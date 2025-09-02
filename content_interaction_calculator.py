"""内容互动数据评分计算器（维度2）"""

import logging
from typing import List

from models import VideoDetail, VideoMetrics, UserProfile, ContentInteractionScore

logger = logging.getLogger(__name__)

class ContentInteractionCalculator:
    """内容互动数据评分计算器"""
    
    def __init__(self):
        """初始化计算器"""
        pass
        
    def calculate_view_score(self, views: int, follower_count: int) -> float:
        """计算视频播放量得分
        
        评分公式：min((views / (followers * 基准系数)) * 100, 100)
        基准系数根据粉丝数量分层：
        - 0-1千：基准 = 1.5倍粉丝量
        - 1千-1万粉丝：基准 = 1.0倍粉丝量
        - 1万-10万粉丝：基准 = 0.8倍粉丝量
        - 10万-100万粉丝：基准 = 0.6倍粉丝量
        - 100万+粉丝：基准 = 0.4倍粉丝量
        
        Args:
            views: 视频播放量
            follower_count: 粉丝数量
            
        Returns:
            播放量得分 (0-100)
        """
        if follower_count <= 0:
            # 当没有粉丝数据时，基于播放量绝对值评分
            # 基准：2000播放量 = 100分，1000播放量 = 50分
            score = min((views / 2000) * 100, 100)
            return max(0.0, score)
        
        # 根据粉丝数量确定基准系数
        if follower_count <= 1000:
            base_coefficient = 1.5
        elif follower_count <= 10000:
            base_coefficient = 1.0
        elif follower_count <= 100000:
            base_coefficient = 0.8
        elif follower_count <= 1000000:
            base_coefficient = 0.6
        else:
            base_coefficient = 0.4
            
        expected_views = follower_count * base_coefficient
        view_ratio = views / expected_views
        score = min(view_ratio * 100, 100)
        return max(0.0, score)
        
    def calculate_like_score(self, likes: int, views: int) -> float:
        """计算点赞数得分
        
        评分公式：min((likes / views) * 2500, 100)
        基准逻辑：
        - 4.0% 点赞率 = 100分 (基于行业优秀标准)
        - 2.0% 点赞率 = 50分 (行业平均)
        - 系数 = 100 / 4.0 * 100 = 2500
        
        Args:
            likes: 点赞数
            views: 播放量
            
        Returns:
            点赞得分 (0-100)
        """
        if views <= 0:
            return 0.0
            
        like_rate = likes / views
        score = min(like_rate * 2500, 100)
        return max(0.0, score)
        
    def calculate_comment_score(self, comments: int, views: int) -> float:
        """计算评论数得分
        
        评分公式：min((comments / views) * 12500, 100)
        基准逻辑：
        - 经验数据：评论率通常为点赞率的1/5
        - 如果点赞率4%为优秀，则评论率0.8%为优秀
        - 系数 = 100 / 0.8 * 100 = 12500
        
        Args:
            comments: 评论数
            views: 播放量
            
        Returns:
            评论得分 (0-100)
        """
        if views <= 0:
            return 0.0
            
        comment_rate = comments / views
        score = min(comment_rate * 12500, 100)
        return max(0.0, score)
        
    def calculate_share_score(self, shares: int, views: int) -> float:
        """计算分享数得分
        
        评分公式：min((shares / views) * 25000, 100)
        基准逻辑：
        - 经验数据：分享率通常为点赞率的1/10
        - 如果点赞率4%为优秀，则分享率0.4%为优秀
        - 系数 = 100 / 0.4 * 100 = 25000
        
        Args:
            shares: 分享数
            views: 播放量
            
        Returns:
            分享得分 (0-100)
        """
        if views <= 0:
            return 0.0
            
        share_rate = shares / views
        score = min(share_rate * 25000, 100)
        return max(0.0, score)
        
    def calculate_save_score(self, saves: int, views: int) -> float:
        """计算保存数得分
        
        评分公式：min((saves / views) * 10000, 100)
        基准逻辑：
        - Save Rate通常介于评论率和分享率之间
        - Save行为比Comment容易（无需思考回复内容）
        - Save行为比Share更私密（不会暴露给关注者）
        - 如果1%保存率为优秀，系数 = 100 / 1 * 100 = 10000
        
        Args:
            saves: 保存数
            views: 播放量
            
        Returns:
            保存得分 (0-100)
        """
        if views <= 0:
            return 0.0
            
        save_rate = saves / views
        score = min(save_rate * 10000, 100)
        return max(0.0, score)
        
    def calculate_completion_score(self, completion_rate: float) -> float:
        """计算完播率得分
        
        评分公式：min(completion_rate * 100 * 1.43, 100)
        基准逻辑：>70%为优秀, >80%为极佳
        - 基于TikTok算法重要性，70%完播率为满分
        - 系数 = 100 / 70 = 1.43
        
        Args:
            completion_rate: 完播率 (0-1)
            
        Returns:
            完播率得分 (0-100)
        """
        if completion_rate <= 0:
            return 0.0
            
        score = min(completion_rate * 100 * 1.43, 100)
        return max(0.0, score)
        
    def calculate_single_video_score(self, 
                                   video: VideoDetail, 
                                   follower_count: int) -> ContentInteractionScore:
        """计算单个视频的内容互动得分
        
        权重分配：
        - 视频播放量：10%
        - 点赞数：25%
        - 评论数：30%
        - 分享数：35%
        
        Args:
            video: 视频详情
            follower_count: 粉丝数量
            
        Returns:
            内容互动评分对象
        """
        # 计算各项得分
        view_score = self.calculate_view_score(video.view_count, follower_count)
        like_score = self.calculate_like_score(video.like_count, video.view_count)
        comment_score = self.calculate_comment_score(video.comment_count, video.view_count)
        share_score = self.calculate_share_score(video.share_count, video.view_count)
        
        # 权重计算总分
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.25 +      # 点赞权重25%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.35       # 分享权重35%
        )
        
        logger.info(f"视频 {video.video_id} 互动评分 - 播放: {view_score:.2f}, "
                   f"点赞: {like_score:.2f}, 评论: {comment_score:.2f}, "
                   f"分享: {share_score:.2f}, 总分: {total_score:.2f}")
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            total_score=total_score
        )
        
    def calculate_average_content_score(self, 
                                       videos: List[VideoDetail], 
                                       follower_count: int) -> ContentInteractionScore:
        """计算平均内容互动得分
        
        基于多个视频的平均表现计算得分
        
        Args:
            videos: 视频详情列表
            follower_count: 粉丝数量
            
        Returns:
            平均内容互动评分对象
        """
        if not videos:
            return ContentInteractionScore(
                view_score=0.0,
                like_score=0.0,
                comment_score=0.0,
                share_score=0.0,
                save_score=0.0,
                total_score=0.0
            )
            
        # 计算总数据
        total_views = sum(video.view_count for video in videos)
        total_likes = sum(video.like_count for video in videos)
        total_comments = sum(video.comment_count for video in videos)
        total_shares = sum(video.share_count for video in videos)
        
        # 计算平均值
        avg_views = total_views / len(videos)
        avg_likes = total_likes / len(videos)
        avg_comments = total_comments / len(videos)
        avg_shares = total_shares / len(videos)
        
        # 计算总数据（添加保存数）
        total_saves = sum(getattr(video, 'collect_count', 0) or 0 for video in videos)  # 使用collect_count作为保存数
        avg_saves = total_saves / len(videos)
        
        # 计算各项得分
        view_score = self.calculate_view_score(int(avg_views), follower_count)
        like_score = self.calculate_like_score(int(avg_likes), int(avg_views))
        comment_score = self.calculate_comment_score(int(avg_comments), int(avg_views))
        share_score = self.calculate_share_score(int(avg_shares), int(avg_views))
        save_score = self.calculate_save_score(int(avg_saves), int(avg_views))
        
        # 权重计算总分（新权重配置）
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        logger.info(f"平均内容互动评分 - 播放: {view_score:.2f}, 点赞: {like_score:.2f}, "
                   f"评论: {comment_score:.2f}, 分享: {share_score:.2f}, 保存: {save_score:.2f}, 总分: {total_score:.2f}")
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            save_score=save_score,
            total_score=total_score
        )
        
    def calculate_weighted_content_score(self, 
                                        videos: List[VideoDetail], 
                                        follower_count: int,
                                        recent_weight: float = 0.7) -> ContentInteractionScore:
        """计算加权内容互动得分
        
        给最近的视频更高的权重
        
        Args:
            videos: 视频详情列表（按时间排序，最新的在前）
            follower_count: 粉丝数量
            recent_weight: 最近视频的权重
            
        Returns:
            加权内容互动评分对象
        """
        if not videos:
            return ContentInteractionScore(
                view_score=0.0,
                like_score=0.0,
                comment_score=0.0,
                share_score=0.0,
                save_score=0.0,
                total_score=0.0
            )
            
        # 按时间排序（最新的在前）
        sorted_videos = sorted(videos, key=lambda x: x.create_time, reverse=True)
        
        total_weight = 0.0
        weighted_views = 0.0
        weighted_likes = 0.0
        weighted_comments = 0.0
        weighted_shares = 0.0
        weighted_saves = 0.0
        
        for i, video in enumerate(sorted_videos):
            # 计算权重：最新的视频权重最高
            weight = recent_weight ** i
            total_weight += weight
            
            weighted_views += video.view_count * weight
            weighted_likes += video.like_count * weight
            weighted_comments += video.comment_count * weight
            weighted_shares += video.share_count * weight
            weighted_saves += (getattr(video, 'collect_count', 0) or 0) * weight
            
        # 计算累计值（按文档要求使用累计值而非平均值）
        total_views = sum(video.view_count for video in sorted_videos)
        total_likes = sum(video.like_count for video in sorted_videos)
        total_comments = sum(video.comment_count for video in sorted_videos)
        total_shares = sum(video.share_count for video in sorted_videos)
        total_saves = sum(getattr(video, 'collect_count', 0) or 0 for video in sorted_videos)
        
        # 计算各项得分（基于累计值）
        view_score = self.calculate_view_score(total_views, follower_count)
        like_score = self.calculate_like_score(total_likes, total_views)
        comment_score = self.calculate_comment_score(total_comments, total_views)
        share_score = self.calculate_share_score(total_shares, total_views)
        save_score = self.calculate_save_score(total_saves, total_views)
        
        # 权重计算总分（新权重配置）
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        # 详细计算过程日志
        logger.info(f"📊 内容互动评分计算详情（基于累计值）:")
        logger.info(f"   • 累计播放量: {total_views:,} → 得分: {view_score:.2f} × 10% = {view_score * 0.10:.2f}")
        logger.info(f"   • 累计点赞数: {total_likes:,} → 得分: {like_score:.2f} × 15% = {like_score * 0.15:.2f}")
        logger.info(f"   • 累计评论数: {total_comments:,} → 得分: {comment_score:.2f} × 30% = {comment_score * 0.30:.2f}")
        logger.info(f"   • 累计分享数: {total_shares:,} → 得分: {share_score:.2f} × 30% = {share_score * 0.30:.2f}")
        logger.info(f"   • 累计保存数: {total_saves:,} → 得分: {save_score:.2f} × 15% = {save_score * 0.15:.2f}")
        logger.info(f"   • 内容互动总分: {total_score:.2f}")
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            save_score=save_score,
            total_score=total_score
        )