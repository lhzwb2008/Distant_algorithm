"""创作者评分计算器单元测试"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from creator_score_calculator import CreatorScoreCalculator
from models import UserProfile, VideoDetail, AccountQualityScore, ContentInteractionScore

class TestCreatorScoreCalculator(unittest.TestCase):
    """创作者评分计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = CreatorScoreCalculator()
        
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
            ),
            VideoDetail(
                video_id="video3",
                view_count=120000,
                like_count=4800,
                comment_count=600,
                share_count=240
            )
        ]
        
        # 创建测试评分数据
        self.account_quality = AccountQualityScore(
            follower_score=50.0,
            likes_score=75.0,
            posting_score=100.0,
            total_score=70.0,
            multiplier=2.0
        )
        
        self.content_interaction = ContentInteractionScore(
            view_score=80.0,
            like_score=85.0,
            comment_score=75.0,
            share_score=70.0,
            total_score=78.0
        )
    
    def test_calculate_creator_score(self):
        """测试创作者总评分计算"""
        creator_score = self.calculator.calculate_creator_score(
            self.user_profile, self.video_details
        )
        
        # 验证返回的数据结构
        self.assertIsNotNone(creator_score.account_quality)
        self.assertIsNotNone(creator_score.content_interaction)
        self.assertIsNotNone(creator_score.final_score)
        self.assertIsNotNone(creator_score.username)
        self.assertIsNotNone(creator_score.calculation_date)
        
        # 验证用户名
        self.assertEqual(creator_score.username, "test_user")
        
        # 验证分数范围
        self.assertGreaterEqual(creator_score.final_score, 0)
        self.assertLessEqual(creator_score.final_score, 300)  # 考虑到最高3倍加权
        
        # 验证账户质量和内容互动评分
        self.assertGreaterEqual(creator_score.account_quality.total_score, 0)
        self.assertLessEqual(creator_score.account_quality.total_score, 100)
        
        self.assertGreaterEqual(creator_score.content_interaction.total_score, 0)
        self.assertLessEqual(creator_score.content_interaction.total_score, 100)
    
    def test_calculate_from_scores(self):
        """测试基于已有评分数据计算总分"""
        creator_score = self.calculator.calculate_from_scores(
            "test_user", self.account_quality, self.content_interaction
        )
        
        # 验证返回的数据结构
        self.assertEqual(creator_score.username, "test_user")
        self.assertEqual(creator_score.account_quality, self.account_quality)
        self.assertEqual(creator_score.content_interaction, self.content_interaction)
        
        # 验证最终分数计算
        # 公式: (内容互动 × 65% + 账户质量 × 35%) × 账户质量加权
        expected_base_score = (
            self.content_interaction.total_score * 0.65 + 
            self.account_quality.total_score * 0.35
        )
        expected_final_score = expected_base_score * self.account_quality.multiplier
        
        self.assertAlmostEqual(creator_score.final_score, expected_final_score, places=2)
    
    def test_calculate_batch_scores(self):
        """测试批量计算评分"""
        users_data = [
            ("user1", self.user_profile, self.video_details),
            ("user2", self.user_profile, self.video_details[:2]),  # 较少视频
        ]
        
        batch_scores = self.calculator.calculate_batch_scores(users_data)
        
        # 验证返回结果
        self.assertEqual(len(batch_scores), 2)
        
        for score in batch_scores:
            self.assertIsNotNone(score.username)
            self.assertIsNotNone(score.final_score)
            self.assertGreaterEqual(score.final_score, 0)
    
    def test_get_score_breakdown(self):
        """测试评分详细分解"""
        creator_score = self.calculator.calculate_creator_score(
            self.user_profile, self.video_details
        )
        
        breakdown = self.calculator.get_score_breakdown(creator_score)
        
        # 验证分解信息包含所有必要字段
        required_fields = [
            'username', 'final_score', 'account_quality_score', 
            'content_interaction_score', 'quality_multiplier',
            'follower_score', 'likes_score', 'posting_score',
            'view_score', 'like_score', 'comment_score', 'share_score'
        ]
        
        for field in required_fields:
            self.assertIn(field, breakdown)
        
        # 验证数值类型
        numeric_fields = [
            'final_score', 'account_quality_score', 'content_interaction_score',
            'quality_multiplier', 'follower_score', 'likes_score', 'posting_score',
            'view_score', 'like_score', 'comment_score', 'share_score'
        ]
        
        for field in numeric_fields:
            self.assertIsInstance(breakdown[field], (int, float))
    
    def test_compare_creators(self):
        """测试创作者评分比较"""
        # 创建两个不同的用户档案
        user1 = UserProfile(
            username="user1",
            follower_count=100000,
            total_likes=2000000,
            video_count=150
        )
        
        user2 = UserProfile(
            username="user2",
            follower_count=30000,
            total_likes=500000,
            video_count=80
        )
        
        score1 = self.calculator.calculate_creator_score(user1, self.video_details)
        score2 = self.calculator.calculate_creator_score(user2, self.video_details)
        
        comparison = self.calculator.compare_creators([score1, score2])
        
        # 验证比较结果结构
        self.assertIn('rankings', comparison)
        self.assertIn('score_differences', comparison)
        self.assertIn('category_leaders', comparison)
        
        # 验证排名
        rankings = comparison['rankings']
        self.assertEqual(len(rankings), 2)
        
        # 验证排名顺序（按最终分数降序）
        self.assertGreaterEqual(rankings[0]['final_score'], rankings[1]['final_score'])
        
        # 验证分类领先者
        category_leaders = comparison['category_leaders']
        required_categories = [
            'account_quality', 'content_interaction', 'follower_score',
            'likes_score', 'view_score', 'like_score', 'comment_score', 'share_score'
        ]
        
        for category in required_categories:
            self.assertIn(category, category_leaders)
    
    def test_formula_calculation(self):
        """测试评分公式计算的准确性"""
        # 使用已知数据验证公式计算
        account_quality = AccountQualityScore(
            follower_score=60.0,
            likes_score=80.0,
            posting_score=100.0,
            total_score=75.0,  # (60*0.4 + 80*0.4 + 100*0.2) = 76
            multiplier=2.0
        )
        
        content_interaction = ContentInteractionScore(
            view_score=90.0,
            like_score=85.0,
            comment_score=80.0,
            share_score=75.0,
            total_score=81.0  # (90*0.1 + 85*0.25 + 80*0.3 + 75*0.35) = 80.75
        )
        
        creator_score = self.calculator.calculate_from_scores(
            "formula_test", account_quality, content_interaction
        )
        
        # 验证最终分数计算
        # 公式: (内容互动 × 65% + 账户质量 × 35%) × 账户质量加权
        expected_base = 81.0 * 0.65 + 75.0 * 0.35  # 52.65 + 26.25 = 78.9
        expected_final = expected_base * 2.0  # 78.9 * 2.0 = 157.8
        
        self.assertAlmostEqual(creator_score.final_score, expected_final, places=1)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零粉丝用户
        zero_user = UserProfile(
            username="zero_user",
            follower_count=0,
            total_likes=0,
            video_count=0
        )
        
        creator_score = self.calculator.calculate_creator_score(zero_user, [])
        
        # 零数据应该得到最低分
        self.assertGreaterEqual(creator_score.final_score, 0)
        self.assertEqual(creator_score.account_quality.multiplier, 1.0)  # 最低加权
        
        # 测试空视频列表
        creator_score = self.calculator.calculate_creator_score(
            self.user_profile, []
        )
        
        # 应该能正常处理空视频列表
        self.assertIsNotNone(creator_score.final_score)
        self.assertEqual(creator_score.content_interaction.total_score, 0)
    
    def test_weight_configuration(self):
        """测试权重配置"""
        # 验证主评分公式权重
        self.assertEqual(self.calculator.account_quality_weight, 0.35)
        self.assertEqual(self.calculator.content_interaction_weight, 0.65)
        
        # 验证权重总和为1
        total_weight = (
            self.calculator.account_quality_weight + 
            self.calculator.content_interaction_weight
        )
        self.assertAlmostEqual(total_weight, 1.0, places=2)

if __name__ == '__main__':
    unittest.main()