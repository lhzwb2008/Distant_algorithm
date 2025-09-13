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
        
    def calculate_posting_score(self, video_details: List[VideoDetail]) -> Tuple[float, dict]:
        """计算发布频率得分
        
        评分公式：max(0, 100 - abs(weekly_frequency - 10) * 6)
        - 10 = 理想频次（每周10个视频）
        - 6 = 惩罚系数（偏离理想频次1个，扣6分）
        - abs() = 取绝对值
        - max(0, ...) = 最低0分
        
        示例计算：
        - 每周1个 → max(0, 100 - 9*6) = 46分
        - 每周3个 → max(0, 100 - 7*6) = 58分  
        - 每周5个 → max(0, 100 - 5*6) = 70分 
        - 每周7个 → max(0, 100 - 3*6) = 82分
        - 每周10个 → max(0, 100 - 0*6) = 100分
        - 每周15个 → max(0, 100 - 5*6) = 70分
        - 每周17个 → max(0, 100 - 7*6) = 58分
        - 每周20个 → max(0, 100 - 10*6) = 40分
        
        注意：基于最近三个月的数据计算发布频率
        
        Args:
            video_details: 视频详情列表（应该是最近三个月的视频）
            
        Returns:
            Tuple[float, dict]: (发布频率得分 (0-100), 详细计算过程)
        """
        if not video_details:
            return 0.0, {"计算类型": "无视频数据", "结果": "0.00次/周, 得分: 0.00"}
            
        # 基于三个月数据计算发布频率
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)  # 约3个月
        
        # 统计有效时间的视频
        valid_videos = []
        invalid_time_videos = []
        
        logger.info(f"📊 发布频率计算开始（基于三个月数据，共{len(video_details)}个视频）")
        logger.info(f"   计算公式: weekly_frequency = 近3个月视频总数 ÷ 12周")
        logger.info(f"   评分公式: max(0, 100 - abs(weekly_frequency - 理想频率) × 惩罚系数)")
        
        for video in video_details:
            if video.create_time:
                # 检查时间是否有效（不是1970年的时间戳）
                if video.create_time.year > 1980:  # 合理的时间范围
                    # 由于传入的video_details已经是三个月内的数据，这里不再过滤时间范围
                    valid_videos.append(video)
                else:
                    invalid_time_videos.append(video)
            else:
                invalid_time_videos.append(video)
        
        # 如果没有有效时间的视频，但有视频数据，则使用简化计算
        if not valid_videos and invalid_time_videos:
            logger.warning(f"检测到 {len(invalid_time_videos)} 个视频的时间戳无效，使用简化发布频率计算")
            # 假设这些视频是最近发布的，按视频数量估算发布频率
            # 假设平均每周发布频率为视频总数除以12周（3个月）
            estimated_weekly_frequency = len(video_details) / 12.0
            
            # 应用评分公式
            ideal_frequency = 10
            penalty_coefficient = 6
            deviation = abs(estimated_weekly_frequency - ideal_frequency)
            penalty = deviation * penalty_coefficient
            score = max(0, 100 - penalty)
            
            details = {
            "计算类型": "简化计算（时间戳无效）",
            "总视频数": len(video_details),
            "假设时间跨度": "12周（3个月）",
            "估算发布频率": f"{len(video_details)} ÷ 12 = {estimated_weekly_frequency:.2f}次/周",
            "weekly_frequency": f"{estimated_weekly_frequency:.2f}次/周",
            "理想频率": f"{ideal_frequency}次/周",
            "偏差": f"|{estimated_weekly_frequency:.2f} - {ideal_frequency}| = {deviation:.2f}",
            "扣分": f"{deviation:.2f} × {penalty_coefficient} = {penalty:.2f}",
            "最终得分": f"max(0, 100 - {penalty:.2f}) = {score:.2f}"
        }
            
            logger.info(f"简化计算：{len(video_details)}个视频，估算频率{estimated_weekly_frequency:.1f}次/周，得分{score:.1f}")
            return score, details
        
        if not valid_videos:
            details = {
                "计算类型": "无有效视频",
                "结果": "0.00次/周 (无有效视频), 得分: 0.00"
            }
            logger.info("发布频率计算结果: 0.00次/周 (无有效视频), 得分: 0.00")
            return 0.0, details
            
        # 使用统一的简化计算方式（基于12周）
        estimated_weekly_frequency = len(valid_videos) / 12.0
        
        # 应用评分公式
        ideal_frequency = 10
        penalty_coefficient = 6
        deviation = abs(estimated_weekly_frequency - ideal_frequency)
        penalty = deviation * penalty_coefficient
        score = max(0, 100 - penalty)
        
        details = {
            "计算类型": "统一计算（基于12周）",
            "有效视频数": len(valid_videos),
            "假设时间跨度": "12周（3个月）",
            "发布频率": f"{len(valid_videos)} ÷ 12 = {estimated_weekly_frequency:.2f}次/周",
            "weekly_frequency": f"{estimated_weekly_frequency:.2f}次/周",
            "理想频率": f"{ideal_frequency}次/周",
            "偏差": f"|{estimated_weekly_frequency:.2f} - {ideal_frequency}| = {deviation:.2f}",
            "扣分": f"{deviation:.2f} × {penalty_coefficient} = {penalty:.2f}",
            "最终得分": f"max(0, 100 - {penalty:.2f}) = {score:.2f}"
        }
        
        logger.info(f"发布频率计算完成：{len(valid_videos)}个视频，频率{estimated_weekly_frequency:.1f}次/周，得分{score:.1f}")
        return score, details
        
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
        posting_score, posting_details = self.calculate_posting_score(video_details or [])
        
        # 权重计算总分
        total_score = (
            follower_score * 0.4 +  # 粉丝数量权重40%
            likes_score * 0.4 +     # 总点赞数权重40%
            posting_score * 0.2     # 发布频率权重20%
        )
        
        # 获取加权系数
        multiplier = self.get_quality_multiplier(total_score)
        
        # 添加详细计算过程到posting_details
        if posting_details is None:
            posting_details = {}
        
        posting_details.update({
            "账户质量详细计算过程": {
                "粉丝数量": f"{user_profile.follower_count:,}",
                "粉丝数量得分": f"{follower_score:.2f}",
                "粉丝数量加权": f"{follower_score:.2f} × 40% = {follower_score * 0.4:.2f}",
                "总点赞数": f"{user_profile.total_likes:,}",
                "总点赞数得分": f"{likes_score:.2f}",
                "总点赞数加权": f"{likes_score:.2f} × 40% = {likes_score * 0.4:.2f}",
                "发布频率得分": f"{posting_score:.2f}",
                "发布频率加权": f"{posting_score:.2f} × 20% = {posting_score * 0.2:.2f}",
                "账户质量总分计算": f"{follower_score * 0.4:.2f} + {likes_score * 0.4:.2f} + {posting_score * 0.2:.2f} = {total_score:.2f}",
                "质量加权系数": f"{multiplier:.3f}"
            }
        })
        
        # 账户质量评分计算完成
        logger.info(f"✅ 账户质量评分计算完成: 总分{total_score:.2f}, 加权系数{multiplier:.3f}")
        
        return AccountQualityScore(
            follower_score=follower_score,
            likes_score=likes_score,
            posting_score=posting_score,
            total_score=total_score,
            multiplier=multiplier,
            posting_details=posting_details
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