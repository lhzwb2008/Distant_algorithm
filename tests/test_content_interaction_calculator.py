"""内容互动计算器单元测试"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_interaction_calculator import ContentInteractionCalculator
from models import VideoDetail

class TestContentInteractionCalculator(unittest.TestCase):
    """内容互动计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = ContentInteractionCalculator()
        self.follower_count = 50000
        
        # 创建测试视频数据
        self.video_detail = VideoDetail(
            video_id="test_video",
            view_count=100000,
            like_count=4000,    # 4%点赞率
            comment_count=800,  # 0.8%评论率
            share_count=400     # 0.4%分享率
        )
        
        self.video_list = [
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
                like_count=3200,
                comment_count=640,
                share_count=320
            ),
            VideoDetail(
                video_id="video3",
                view_count=120000,
                like_count=4800,
                comment_count=960,
                share_count=480
            )
        ]
    
    def test_calculate_view_score(self):
        """测试播放量得分计算"""
        # 测试不同播放量与粉丝数比例的得分
        test_cases = [
            (25000, 50000, 50),    # 0.5倍播放量 = 50分
            (50000, 50000, 100),   # 1.0倍播放量 = 100分
            (100000, 50000, 100),  # 2.0倍播放量 = 100分（上限）
        ]
        
        for views, followers, expected_score in test_cases:
            score = self.calculator.calculate_view_score(views, followers)
            self.assertEqual(score, expected_score)
    
    def test_calculate_like_score(self):
        """测试点赞数得分计算"""
        # 测试不同点赞率的得分
        test_cases = [
            (2000, 100000, 50),    # 2%点赞率 = 50分
            (4000, 100000, 100),   # 4%点赞率 = 100分
            (6000, 100000, 100),   # 6%点赞率 = 100分（上限）
        ]
        
        for likes, views, expected_score in test_cases:
            score = self.calculator.calculate_like_score(likes, views)
            self.assertEqual(score, expected_score)
    
    def test_calculate_comment_score(self):
        """测试评论数得分计算"""
        # 测试不同评论率的得分
        test_cases = [
            (400, 100000, 50),     # 0.4%评论率 = 50分
            (800, 100000, 100),    # 0.8%评论率 = 100分
            (1200, 100000, 100),   # 1.2%评论率 = 100分（上限）
        ]
        
        for comments, views, expected_score in test_cases:
            score = self.calculator.calculate_comment_score(comments, views)
            self.assertEqual(score, expected_score)
    
    def test_calculate_share_score(self):
        """测试分享数得分计算"""
        # 测试不同分享率的得分
        test_cases = [
            (200, 100000, 50),     # 0.2%分享率 = 50分
            (400, 100000, 100),    # 0.4%分享率 = 100分
            (600, 100000, 100),    # 0.6%分享率 = 100分（上限）
        ]
        
        for shares, views, expected_score in test_cases:
            score = self.calculator.calculate_share_score(shares, views)
            self.assertEqual(score, expected_score)
    
    def test_calculate_completion_score(self):
        """测试完播率得分计算"""
        # 测试不同完播率的得分
        test_cases = [
            (0.5, 71.5),   # 50%完播率
            (0.7, 100),    # 70%完播率 = 100分
            (0.8, 100),    # 80%完播率 = 100分（上限）
        ]
        
        for completion_rate, expected_score in test_cases:
            score = self.calculator.calculate_completion_score(completion_rate)
            self.assertAlmostEqual(score, expected_score, places=1)
    
    def test_calculate_single_video_score(self):
        """测试单个视频评分计算"""
        content_score = self.calculator.calculate_single_video_score(
            self.video_detail, self.follower_count
        )
        
        # 验证返回的数据结构
        self.assertIsNotNone(content_score.view_score)
        self.assertIsNotNone(content_score.like_score)
        self.assertIsNotNone(content_score.comment_score)
        self.assertIsNotNone(content_score.share_score)
        self.assertIsNotNone(content_score.total_score)
        
        # 验证分数范围
        self.assertGreaterEqual(content_score.view_score, 0)
        self.assertLessEqual(content_score.view_score, 100)
        
        self.assertGreaterEqual(content_score.like_score, 0)
        self.assertLessEqual(content_score.like_score, 100)
        
        self.assertGreaterEqual(content_score.comment_score, 0)
        self.assertLessEqual(content_score.comment_score, 100)
        
        self.assertGreaterEqual(content_score.share_score, 0)
        self.assertLessEqual(content_score.share_score, 100)
        
        self.assertGreaterEqual(content_score.total_score, 0)
        self.assertLessEqual(content_score.total_score, 100)
    
    def test_calculate_average_content_score(self):
        """测试平均内容评分计算"""
        avg_score = self.calculator.calculate_average_content_score(
            self.video_list, self.follower_count
        )
        
        # 验证返回的数据结构
        self.assertIsNotNone(avg_score.view_score)
        self.assertIsNotNone(avg_score.like_score)
        self.assertIsNotNone(avg_score.comment_score)
        self.assertIsNotNone(avg_score.share_score)
        self.assertIsNotNone(avg_score.total_score)
        
        # 验证分数范围
        self.assertGreaterEqual(avg_score.total_score, 0)
        self.assertLessEqual(avg_score.total_score, 100)
    
    def test_calculate_weighted_content_score(self):
        """测试加权内容评分计算"""
        weighted_score = self.calculator.calculate_weighted_content_score(
            self.video_list, self.follower_count
        )
        
        # 验证返回的数据结构
        self.assertIsNotNone(weighted_score.view_score)
        self.assertIsNotNone(weighted_score.like_score)
        self.assertIsNotNone(weighted_score.comment_score)
        self.assertIsNotNone(weighted_score.share_score)
        self.assertIsNotNone(weighted_score.total_score)
        
        # 验证分数范围
        self.assertGreaterEqual(weighted_score.total_score, 0)
        self.assertLessEqual(weighted_score.total_score, 100)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零值
        zero_video = VideoDetail(
            video_id="zero_video",
            view_count=0,
            like_count=0,
            comment_count=0,
            share_count=0
        )
        
        content_score = self.calculator.calculate_single_video_score(
            zero_video, self.follower_count
        )
        
        # 零值应该得到最低分
        self.assertEqual(content_score.view_score, 0)
        self.assertEqual(content_score.like_score, 0)
        self.assertEqual(content_score.comment_score, 0)
        self.assertEqual(content_score.share_score, 0)
        
        # 测试空视频列表
        avg_score = self.calculator.calculate_average_content_score([], self.follower_count)
        self.assertEqual(avg_score.total_score, 0)
        
        # 测试除零情况
        zero_view_video = VideoDetail(
            video_id="zero_view_video",
            view_count=0,
            like_count=100,
            comment_count=50,
            share_count=25
        )
        
        content_score = self.calculator.calculate_single_video_score(
            zero_view_video, self.follower_count
        )
        
        # 零播放量时，互动率应该为0
        self.assertEqual(content_score.like_score, 0)
        self.assertEqual(content_score.comment_score, 0)
        self.assertEqual(content_score.share_score, 0)
    
    def test_weight_calculation(self):
        """测试权重计算"""
        # 验证权重总和为100%
        weights = self.calculator.weights
        total_weight = (
            weights['view_weight'] + 
            weights['like_weight'] + 
            weights['comment_weight'] + 
            weights['share_weight']
        )
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        # 验证各项权重值
        self.assertEqual(weights['view_weight'], 0.10)
        self.assertEqual(weights['like_weight'], 0.25)
        self.assertEqual(weights['comment_weight'], 0.30)
        self.assertEqual(weights['share_weight'], 0.35)

if __name__ == '__main__':
    unittest.main()