"""账户质量评分计算器（维度1）"""

import math
import logging
from typing import List, Tuple
from datetime import datetime, timedelta

from config import Config
from models import UserProfile, VideoDetail, AccountQualityScore

logger = logging.getLogger(__name__)

class AccountQualityCalculator:
    """账户质量评分计算器"""
    
    def __init__(self):
        """初始化计算器"""
        self.quality_multipliers = Config.ACCOUNT_QUALITY_MULTIPLIERS
        
    def calculate_follower_score(self, follower_count: int) -> float:
        """计算粉丝数量得分
        
        评分公式：min(log10(followers) * 10, 100)
        阈值参考：
        - 1K-10K: 20分
        - 10K-100K: 40分  
        - 100K+: 60分
        - 上限100分
        
        Args:
            follower_count: 粉丝数量
            
        Returns:
            粉丝数量得分 (0-100)
        """
        if follower_count <= 0:
            return 0.0
            
        score = min(math.log10(follower_count) * 10, 100)
        return max(0.0, score)
        
    def calculate_likes_score(self, total_likes: int) -> float:
        """计算总点赞数得分
        
        评分公式：min(log10(total_likes) * 12.5, 100)
        阈值参考：
        - 0-1K点赞：0-37.5分（新手区间）
        - 1K-10K点赞：37.5-50分（成长区间）
        - 10K-100K点赞：50-62.5分（活跃区间）
        - 100K-1M点赞：62.5-75分（优质区间）
        - 1M-10M点赞：75-87.5分（头部区间）
        - 10M+点赞：87.5-100分（顶级区间）
        
        Args:
            total_likes: 总点赞数
            
        Returns:
            总点赞数得分 (0-100)
        """
        if total_likes <= 0:
            return 0.0
            
        score = min(math.log10(total_likes) * 12.5, 100)
        return max(0.0, score)
        
    def calculate_posting_score(self, video_details: List[VideoDetail]) -> float:
        """计算发布频率得分
        
        评分公式：max(0, 100 - abs(weekly_frequency - 5) * 15)
        - 5 = 理想频次（每周5个视频最完美）
        - 15 = 惩罚系数（偏离理想频次1个，扣15分）
        - 最优频次：3-7次/周 (满分100)
        
        Args:
            video_details: 视频详情列表
            
        Returns:
            发布频率得分 (0-100)
        """
        if not video_details:
            return 0.0
            
        # 计算最近4周的发布频率
        now = datetime.now()
        four_weeks_ago = now - timedelta(weeks=4)
        
        # 过滤最近4周的视频
        recent_videos = [
            video for video in video_details 
            if video.create_time and video.create_time >= four_weeks_ago
        ]
        
        if not recent_videos:
            return 0.0
            
        # 计算周平均发布频率
        weeks_count = min(4, (now - min(video.create_time for video in recent_videos)).days / 7)
        if weeks_count <= 0:
            weeks_count = 1
            
        weekly_frequency = len(recent_videos) / weeks_count
        
        # 应用评分公式
        ideal_frequency = 5
        penalty_coefficient = 15
        
        score = max(0, 100 - abs(weekly_frequency - ideal_frequency) * penalty_coefficient)
        
        logger.info(f"发布频率: {weekly_frequency:.2f}次/周, 得分: {score:.2f}")
        return score
        
    def get_quality_multiplier(self, total_score: float) -> float:
        """获取账户质量加权系数
        
        Args:
            total_score: 账户质量总分
            
        Returns:
            加权系数
        """
        for (min_score, max_score), multiplier in self.quality_multipliers.items():
            if min_score <= total_score <= max_score:
                return multiplier
                
        # 如果超出范围，返回最高系数
        return 3.0
        
    def calculate_account_quality(self, 
                                user_profile: UserProfile, 
                                video_details: List[VideoDetail] = None) -> AccountQualityScore:
        """计算账户质量总分
        
        权重分配：
        - 粉丝数量：40%
        - 总点赞数：40%
        - 发布频率：20%
        
        Args:
            user_profile: 用户档案
            video_details: 视频详情列表（用于计算发布频率）
            
        Returns:
            账户质量评分对象
        """
        # 计算各项得分
        follower_score = self.calculate_follower_score(user_profile.follower_count)
        likes_score = self.calculate_likes_score(user_profile.total_likes)
        posting_score = self.calculate_posting_score(video_details or [])
        
        # 权重计算总分
        total_score = (
            follower_score * 0.4 +  # 粉丝数量权重40%
            likes_score * 0.4 +     # 总点赞数权重40%
            posting_score * 0.2     # 发布频率权重20%
        )
        
        # 获取加权系数
        multiplier = self.get_quality_multiplier(total_score)
        
        logger.info(f"账户质量评分 - 粉丝: {follower_score:.2f}, 点赞: {likes_score:.2f}, "
                   f"发布: {posting_score:.2f}, 总分: {total_score:.2f}, 系数: {multiplier}")
        
        return AccountQualityScore(
            follower_score=follower_score,
            likes_score=likes_score,
            posting_score=posting_score,
            total_score=total_score,
            multiplier=multiplier
        )
        
    def calculate_avg_views_per_follower(self, 
                                       total_views: int, 
                                       follower_count: int) -> float:
        """计算平均播放量（每粉丝）
        
        Args:
            total_views: 总播放量
            follower_count: 粉丝数量
            
        Returns:
            平均播放量比率
        """
        if follower_count <= 0:
            return 0.0
        return total_views / follower_count
        
    def calculate_engagement_rates(self, 
                                 total_views: int,
                                 total_likes: int, 
                                 total_comments: int,
                                 total_shares: int) -> Tuple[float, float, float]:
        """计算各种互动率
        
        Args:
            total_views: 总播放量
            total_likes: 总点赞数
            total_comments: 总评论数
            total_shares: 总分享数
            
        Returns:
            (点赞率, 评论率, 分享率)
        """
        if total_views <= 0:
            return 0.0, 0.0, 0.0
            
        like_rate = total_likes / total_views
        comment_rate = total_comments / total_views
        share_rate = total_shares / total_views
        
        return like_rate, comment_rate, share_rate