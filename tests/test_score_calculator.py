"""TikTok创作者评分计算器单元测试"""

import unittest
import sys
import os
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from score_calculator import TikTokCreatorScoreCalculator
from models import UserProfile, VideoDetail

class TestTikTokCreatorScoreCalculator(unittest.TestCase):
    """TikTok创作者评分计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = TikTokCreatorScoreCalculator()
        
        # 创建测试用户档案
        self.test_user_profile = UserProfile(
            username="test_user",
            follower_count=50000,
            total_likes=1000000,
            video_count=100
        )
        
        # 创建测试视频详情列表
        self.test_video_details = [
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
                share_count=160
            ),
            VideoDetail(
                video_id="video3",
                view_count=120000,
                like_count=6000,
                comment_count=600,
                share_count=240
            )
        ]
    
    def test_calculate_follower_score(self):
        """测试粉丝数量评分计算"""
        # 测试不同粉丝数量的评分
        test_cases = [
            (1000, 30.0),      # log10(1000) * 10 = 30
            (10000, 40.0),     # log10(10000) * 10 = 40
            (100000, 50.0),    # log10(100000) * 10 = 50
            (1000000, 60.0),   # log10(1000000) * 10 = 60
            (10000000, 70.0),  # log10(10000000) * 10 = 70
            (100000000, 80.0), # log10(100000000) * 10 = 80
            (1000000000, 90.0), # log10(1000000000) * 10 = 90
            (10000000000, 100.0) # 超过100分，应该被限制为100
        ]
        
        for followers, expected_score in test_cases:
            with self.subTest(followers=followers):
                score = self.calculator._calculate_follower_score(followers)
                self.assertAlmostEqual(score, expected_score, places=1)
    
    def test_calculate_total_likes_score(self):
        """测试总点赞数评分计算"""
        # 测试不同总点赞数的评分
        test_cases = [
            (500, 33.8),       # log10(500) * 12.5 ≈ 33.8
            (5000, 46.3),      # log10(5000) * 12.5 ≈ 46.3
            (50000, 58.8),     # log10(50000) * 12.5 ≈ 58.8
            (500000, 71.3),    # log10(500000) * 12.5 ≈ 71.3
            (5000000, 83.8),   # log10(5000000) * 12.5 ≈ 83.8
            (50000000, 96.3),  # log10(50000000) * 12.5 ≈ 96.3
            (100000000, 100.0) # 超过100分，应该被限制为100
        ]
        
        for total_likes, expected_score in test_cases:
            with self.subTest(total_likes=total_likes):
                score = self.calculator._calculate_total_likes_score(total_likes)
                self.assertAlmostEqual(score, expected_score, places=1)
    
    def test_calculate_posting_frequency_score(self):
        """测试发布频率评分计算"""
        # 测试不同发布频率的评分
        test_cases = [
            (1, 40.0),   # max(0, 100 - abs(1-5) * 15) = 40
            (3, 70.0),   # max(0, 100 - abs(3-5) * 15) = 70
            (5, 100.0),  # max(0, 100 - abs(5-5) * 15) = 100
            (7, 70.0),   # max(0, 100 - abs(7-5) * 15) = 70
            (9, 40.0),   # max(0, 100 - abs(9-5) * 15) = 40
            (12, 0.0),   # max(0, 100 - abs(12-5) * 15) = 0
        ]
        
        for frequency, expected_score in test_cases:
            with self.subTest(frequency=frequency):
                score = self.calculator._calculate_posting_frequency_score(frequency)
                self.assertEqual(score, expected_score)
    
    def test_calculate_account_quality_score(self):
        """测试账户质量评分计算"""
        # 使用测试用户档案
        score = self.calculator.calculate_account_quality_score(self.test_user_profile)
        
        # 验证评分在合理范围内
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # 验证具体计算
        # 粉丝数评分：log10(50000) * 10 ≈ 47.0
        # 总点赞评分：log10(1000000) * 12.5 = 75.0
        # 发布频率评分：假设每周发布频率为 100/52 ≈ 1.9，评分约为 53.5
        # 加权平均：47.0 * 0.4 + 75.0 * 0.4 + 53.5 * 0.2 ≈ 59.5
        expected_score = 47.0 * 0.4 + 75.0 * 0.4 + 53.5 * 0.2
        self.assertAlmostEqual(score, expected_score, places=0)
    
    def test_calculate_engagement_rate(self):
        """测试互动率计算"""
        # 测试点赞率计算
        like_rate = self.calculator._calculate_engagement_rate(5000, 100000, 2500)
        self.assertAlmostEqual(like_rate, 125.0, places=1)  # (5000/100000) * 2500 = 125
        
        # 测试评论率计算
        comment_rate = self.calculator._calculate_engagement_rate(500, 100000, 12500)
        self.assertAlmostEqual(comment_rate, 62.5, places=1)  # (500/100000) * 12500 = 62.5
        
        # 测试分享率计算
        share_rate = self.calculator._calculate_engagement_rate(200, 100000, 25000)
        self.assertAlmostEqual(share_rate, 50.0, places=1)  # (200/100000) * 25000 = 50
        
        # 测试超过100分的情况
        high_rate = self.calculator._calculate_engagement_rate(10000, 100000, 2500)
        self.assertEqual(high_rate, 100.0)  # 应该被限制为100
    
    def test_calculate_view_ratio_score(self):
        """测试播放量比率评分计算"""
        # 测试不同播放量比率的评分
        test_cases = [
            (50000, 100000, 50.0),   # 0.5倍播放量 = 50分
            (100000, 100000, 100.0), # 1.0倍播放量 = 100分
            (150000, 100000, 100.0), # 1.5倍播放量 = 100分（限制为100）
            (200000, 100000, 100.0), # 2.0倍播放量 = 100分（限制为100）
        ]
        
        for views, followers, expected_score in test_cases:
            with self.subTest(views=views, followers=followers):
                score = self.calculator._calculate_view_ratio_score(views, followers)
                self.assertEqual(score, expected_score)
    
    def test_calculate_content_interaction_score(self):
        """测试内容互动数据评分计算"""
        # 使用第一个测试视频
        video = self.test_video_details[0]
        score = self.calculator.calculate_content_interaction_score(
            video, self.test_user_profile.follower_count
        )
        
        # 验证评分在合理范围内
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # 验证具体计算
        # 播放量评分：(100000/50000) * 100 = 200，限制为100，权重10% = 10
        # 点赞率评分：(5000/100000) * 2500 = 125，限制为100，权重25% = 25
        # 评论率评分：(500/100000) * 12500 = 62.5，权重30% = 18.75
        # 分享率评分：(200/100000) * 25000 = 50，权重35% = 17.5
        # 总分：10 + 25 + 18.75 + 17.5 = 71.25
        expected_score = 10 + 25 + 18.75 + 17.5
        self.assertAlmostEqual(score, expected_score, places=1)
    
    def test_get_account_quality_weight(self):
        """测试账户质量加权系数获取"""
        # 测试不同评分范围的加权系数
        test_cases = [
            (5, 1.0),    # 0-10分
            (15, 1.2),   # 10-30分
            (45, 1.5),   # 31-60分
            (70, 2.0),   # 61-80分
            (90, 3.0),   # 81-100分
        ]
        
        for score, expected_weight in test_cases:
            with self.subTest(score=score):
                weight = self.calculator._get_account_quality_weight(score)
                self.assertEqual(weight, expected_weight)
    
    def test_calculate_total_score(self):
        """测试总评分计算"""
        score_result = self.calculator.calculate_total_score(
            self.test_user_profile, 
            self.test_video_details
        )
        
        # 验证返回结果结构
        self.assertIn('total_score', score_result)
        self.assertIn('account_quality_score', score_result)
        self.assertIn('content_interaction_score', score_result)
        self.assertIn('account_quality_weight', score_result)
        self.assertIn('video_scores', score_result)
        
        # 验证评分范围
        self.assertGreaterEqual(score_result['total_score'], 0)
        self.assertLessEqual(score_result['total_score'], 300)  # 最大可能分数
        
        self.assertGreaterEqual(score_result['account_quality_score'], 0)
        self.assertLessEqual(score_result['account_quality_score'], 100)
        
        self.assertGreaterEqual(score_result['content_interaction_score'], 0)
        self.assertLessEqual(score_result['content_interaction_score'], 100)
        
        # 验证加权系数
        self.assertIn(score_result['account_quality_weight'], [1.0, 1.2, 1.5, 2.0, 3.0])
        
        # 验证视频评分数量
        self.assertEqual(len(score_result['video_scores']), len(self.test_video_details))
    
    def test_calculate_total_score_empty_videos(self):
        """测试空视频列表的总评分计算"""
        score_result = self.calculator.calculate_total_score(
            self.test_user_profile, 
            []
        )
        
        # 验证内容互动评分为0
        self.assertEqual(score_result['content_interaction_score'], 0)
        
        # 验证总评分只包含账户质量评分
        expected_total = score_result['account_quality_score'] * score_result['account_quality_weight']
        self.assertAlmostEqual(score_result['total_score'], expected_total, places=2)
    
    def test_calculate_total_score_single_video(self):
        """测试单个视频的总评分计算"""
        single_video = [self.test_video_details[0]]
        score_result = self.calculator.calculate_total_score(
            self.test_user_profile, 
            single_video
        )
        
        # 验证视频评分数量
        self.assertEqual(len(score_result['video_scores']), 1)
        
        # 验证内容互动评分等于单个视频的评分
        expected_content_score = self.calculator.calculate_content_interaction_score(
            single_video[0], 
            self.test_user_profile.follower_count
        )
        self.assertAlmostEqual(
            score_result['content_interaction_score'], 
            expected_content_score, 
            places=2
        )
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零粉丝数
        zero_follower_profile = UserProfile(
            username="zero_user",
            follower_count=0,
            total_likes=0,
            video_count=0
        )
        
        # 应该不会抛出异常
        score = self.calculator.calculate_account_quality_score(zero_follower_profile)
        self.assertGreaterEqual(score, 0)
        
        # 测试零播放量视频
        zero_view_video = VideoDetail(
            video_id="zero_video",
            view_count=0,
            like_count=0,
            comment_count=0,
            share_count=0
        )
        
        # 应该不会抛出异常
        score = self.calculator.calculate_content_interaction_score(
            zero_view_video, 
            1000
        )
        self.assertGreaterEqual(score, 0)
    
    def test_score_consistency(self):
        """测试评分一致性"""
        # 多次计算同样的数据，结果应该一致
        score1 = self.calculator.calculate_total_score(
            self.test_user_profile, 
            self.test_video_details
        )
        
        score2 = self.calculator.calculate_total_score(
            self.test_user_profile, 
            self.test_video_details
        )
        
        self.assertEqual(score1['total_score'], score2['total_score'])
        self.assertEqual(score1['account_quality_score'], score2['account_quality_score'])
        self.assertEqual(score1['content_interaction_score'], score2['content_interaction_score'])
    
    def test_score_monotonicity(self):
        """测试评分单调性"""
        # 更好的数据应该得到更高的评分
        better_profile = UserProfile(
            username="better_user",
            follower_count=100000,  # 更多粉丝
            total_likes=2000000,    # 更多点赞
            video_count=100
        )
        
        better_videos = [
            VideoDetail(
                video_id="better_video",
                view_count=200000,  # 更多播放
                like_count=10000,   # 更多点赞
                comment_count=1000, # 更多评论
                share_count=400     # 更多分享
            )
        ]
        
        original_score = self.calculator.calculate_total_score(
            self.test_user_profile, 
            [self.test_video_details[0]]
        )
        
        better_score = self.calculator.calculate_total_score(
            better_profile, 
            better_videos
        )
        
        # 更好的数据应该得到更高的评分
        self.assertGreater(
            better_score['account_quality_score'], 
            original_score['account_quality_score']
        )
        self.assertGreater(
            better_score['total_score'], 
            original_score['total_score']
        )

if __name__ == '__main__':
    unittest.main()