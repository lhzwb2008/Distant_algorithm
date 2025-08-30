"""账户质量计算器单元测试"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from account_quality_calculator import AccountQualityCalculator
from models import UserProfile, VideoDetail

class TestAccountQualityCalculator(unittest.TestCase):
    """账户质量计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = AccountQualityCalculator()
        
        # 创建测试用户档案
        self.user_profile = UserProfile(
            username="test_user",
            follower_count=50000,
            total_likes=1000000,
            video_count=100
        )
        
        # 创建测试视频数据
        self.video_details = [
            VideoDetail(
                video_id="video1",
                view_count=100000,
                like_count=5000,
                comment_count=500,
                share_count=200
            ),
            VideoDetail(
                video_id="video2",
                view_count=80000,
                like_count=4000,
                comment_count=400,
                share_count=150
            )
        ]
    
    def test_calculate_follower_score(self):
        """测试粉丝数量得分计算"""
        # 测试不同粉丝数量的得分
        test_cases = [
            (1000, 30.0),      # 1K粉丝
            (10000, 40.0),     # 10K粉丝
            (100000, 50.0),    # 100K粉丝
            (1000000, 60.0),   # 1M粉丝
        ]
        
        for followers, expected_min_score in test_cases:
            score = self.calculator.calculate_follower_score(followers)
            self.assertGreaterEqual(score, expected_min_score - 5)  # 允许5分误差
            self.assertLessEqual(score, 100)  # 不超过100分
    
    def test_calculate_likes_score(self):
        """测试总点赞数得分计算"""
        # 测试不同点赞数的得分
        test_cases = [
            (500, 30),         # 500点赞
            (5000, 45),        # 5K点赞
            (50000, 58),       # 50K点赞
            (500000, 70),      # 500K点赞
            (5000000, 83),     # 5M点赞
        ]
        
        for likes, expected_min_score in test_cases:
            score = self.calculator.calculate_likes_score(likes)
            self.assertGreaterEqual(score, expected_min_score - 5)  # 允许5分误差
            self.assertLessEqual(score, 100)  # 不超过100分
    
    def test_calculate_posting_score(self):
        """测试发布频率得分计算"""
        # 测试不同发布频率的得分
        test_cases = [
            (1, 40),   # 每周1个视频
            (3, 70),   # 每周3个视频
            (5, 100),  # 每周5个视频（最优）
            (7, 70),   # 每周7个视频
            (9, 40),   # 每周9个视频
        ]
        
        for frequency, expected_score in test_cases:
            score = self.calculator.calculate_posting_score(frequency)
            self.assertEqual(score, expected_score)
    
    def test_get_quality_multiplier(self):
        """测试账户质量加权系数"""
        # 测试不同质量分数的加权系数
        test_cases = [
            (5, 1.0),    # 0-10分
            (15, 1.2),   # 10-30分
            (45, 1.5),   # 31-60分
            (70, 2.0),   # 61-80分
            (90, 3.0),   # 81-100分
        ]
        
        for quality_score, expected_multiplier in test_cases:
            multiplier = self.calculator.get_quality_multiplier(quality_score)
            self.assertEqual(multiplier, expected_multiplier)
    
    def test_calculate_account_quality(self):
        """测试账户质量总分计算"""
        account_quality = self.calculator.calculate_account_quality(
            self.user_profile, self.video_details
        )
        
        # 验证返回的数据结构
        self.assertIsNotNone(account_quality.follower_score)
        self.assertIsNotNone(account_quality.likes_score)
        self.assertIsNotNone(account_quality.posting_score)
        self.assertIsNotNone(account_quality.total_score)
        self.assertIsNotNone(account_quality.multiplier)
        
        # 验证分数范围
        self.assertGreaterEqual(account_quality.follower_score, 0)
        self.assertLessEqual(account_quality.follower_score, 100)
        
        self.assertGreaterEqual(account_quality.likes_score, 0)
        self.assertLessEqual(account_quality.likes_score, 100)
        
        self.assertGreaterEqual(account_quality.posting_score, 0)
        self.assertLessEqual(account_quality.posting_score, 100)
        
        self.assertGreaterEqual(account_quality.total_score, 0)
        self.assertLessEqual(account_quality.total_score, 100)
        
        # 验证加权系数
        self.assertIn(account_quality.multiplier, [1.0, 1.2, 1.5, 2.0, 3.0])
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零值
        zero_profile = UserProfile(
            username="zero_user",
            follower_count=0,
            total_likes=0,
            video_count=0
        )
        
        account_quality = self.calculator.calculate_account_quality(
            zero_profile, []
        )
        
        # 零值应该得到最低分
        self.assertEqual(account_quality.follower_score, 0)
        self.assertEqual(account_quality.likes_score, 0)
        self.assertEqual(account_quality.multiplier, 1.0)  # 最低加权
        
        # 测试极大值
        large_profile = UserProfile(
            username="large_user",
            follower_count=10000000,  # 1000万粉丝
            total_likes=100000000,    # 1亿点赞
            video_count=1000
        )
        
        account_quality = self.calculator.calculate_account_quality(
            large_profile, self.video_details
        )
        
        # 极大值应该被限制在100分以内
        self.assertLessEqual(account_quality.follower_score, 100)
        self.assertLessEqual(account_quality.likes_score, 100)
        self.assertEqual(account_quality.multiplier, 3.0)  # 最高加权

if __name__ == '__main__':
    unittest.main()