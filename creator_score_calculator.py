"""TikTok创作者评分计算器（主评分公式）"""

import logging
from typing import List, Optional
from datetime import datetime

from config import Config
from models import (
    UserProfile, VideoDetail, VideoMetrics, 
    AccountQualityScore, ContentInteractionScore, CreatorScore
)
from api_client import TiKhubAPIClient
from account_quality_calculator import AccountQualityCalculator
from content_interaction_calculator import ContentInteractionCalculator

logger = logging.getLogger(__name__)

class CreatorScoreCalculator:
    """TikTok创作者评分计算器
    
    主评分公式：
    TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权
    
    注：内容质量（维度3）固定为60分
    """
    
    def __init__(self, api_client: Optional[TiKhubAPIClient] = None):
        """初始化评分计算器
        
        Args:
            api_client: TiKhub API客户端，如果不提供则创建新实例
        """
        self.api_client = api_client or TiKhubAPIClient()
        self.account_calculator = AccountQualityCalculator()
        self.content_calculator = ContentInteractionCalculator()
        
        # 权重配置
        self.content_weight = Config.CONTENT_INTERACTION_WEIGHT  # 65%
        self.content_quality_weight = 0.35  # 35% 内容质量权重
        self.content_quality_score = 60.0   # 内容质量固定分数
        
    async def calculate_creator_score(self, 
                                    username: str,
                                    video_count: int = 20) -> CreatorScore:
        """计算创作者总评分
        
        Args:
            username: TikTok用户名
            video_count: 分析的视频数量（默认20个最新视频）
            
        Returns:
            创作者评分对象
        """
        try:
            # 1. 获取用户档案
            logger.info(f"开始计算用户 {username} 的创作者评分")
            user_profile = await self.api_client.get_user_profile(username)
            
            # 2. 获取用户视频列表
            video_list = await self.api_client.get_user_videos(username, count=video_count)
            
            # 3. 获取视频详情
            video_details = []
            for video_id in video_list[:video_count]:  # 限制数量
                try:
                    video_detail = await self.api_client.get_video_detail(video_id)
                    video_details.append(video_detail)
                except Exception as e:
                    logger.warning(f"获取视频 {video_id} 详情失败: {e}")
                    continue
                    
            if not video_details:
                raise ValueError(f"无法获取用户 {username} 的视频数据")
                
            # 4. 计算账户质量评分
            account_quality = self.account_calculator.calculate_account_quality(
                user_profile, video_details
            )
            
            # 5. 计算内容互动评分
            content_interaction = self.content_calculator.calculate_weighted_content_score(
                video_details, user_profile.follower_count
            )
            
            # 6. 计算最终评分
            final_score = self._calculate_final_score(
                account_quality, content_interaction
            )
            
            logger.info(f"用户 {username} 评分计算完成，最终得分: {final_score:.2f}")
            
            return CreatorScore(
                user_id=user_profile.user_id,
                username=username,
                account_quality=account_quality,
                content_interaction=content_interaction,
                final_score=final_score,
                video_count=len(video_details),
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"计算用户 {username} 评分时发生错误: {e}")
            raise
            
    def calculate_creator_score_from_data(self,
                                        user_profile: UserProfile,
                                        video_details: List[VideoDetail]) -> CreatorScore:
        """基于已有数据计算创作者评分
        
        Args:
            user_profile: 用户档案
            video_details: 视频详情列表
            
        Returns:
            创作者评分对象
        """
        try:
            logger.info(f"开始计算用户 {user_profile.username} 的创作者评分（基于已有数据）")
            
            # 1. 计算账户质量评分
            account_quality = self.account_calculator.calculate_account_quality(
                user_profile, video_details
            )
            
            # 2. 计算内容互动评分
            content_interaction = self.content_calculator.calculate_weighted_content_score(
                video_details, user_profile.follower_count
            )
            
            # 3. 计算最终评分
            final_score = self._calculate_final_score(
                account_quality, content_interaction
            )
            
            logger.info(f"用户 {user_profile.username} 评分计算完成，最终得分: {final_score:.2f}")
            
            return CreatorScore(
                user_id=user_profile.user_id,
                username=user_profile.username,
                account_quality=account_quality,
                content_interaction=content_interaction,
                final_score=final_score,
                video_count=len(video_details),
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"计算用户 {user_profile.username} 评分时发生错误: {e}")
            raise
            
    def calculate_score(self, sec_uid: str, keyword: str = None) -> float:
        """计算创作者评分（简化接口）
        
        Args:
            sec_uid: 用户secUid
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            最终评分
        """
        creator_score = self.calculate_creator_score_by_user_id(sec_uid, keyword=keyword)
        return creator_score.final_score
    
    def calculate_creator_score_by_user_id(self, user_id: str, video_count: int = 5, keyword: str = None) -> CreatorScore:
        """通过用户ID计算创作者评分（模拟分数计算）
        
        Args:
            user_id: TikTok用户ID
            video_count: 获取的视频数量，默认5个（当没有关键词时使用）
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            创作者评分对象
        """
        try:
            # 1. 使用传入的user_id作为secUid（因为调用方已经转换过了）
            sec_uid = user_id
            print(f"✅ 使用secUid: {sec_uid[:20]}...")
            
            # 2. 获取用户作品
            if keyword:
                print(f"📡 API调用: 获取用户包含关键词 '{keyword}' 的视频")
                video_details = self.api_client.fetch_user_top_videos(sec_uid, keyword=keyword)
            else:
                print(f"📡 API调用: 获取用户视频列表 (前{video_count}个)")
                video_details = self.api_client.fetch_user_top_videos(sec_uid, video_count)
            
            if not video_details:
                print(f"❌ 用户 {user_id} 没有找到任何视频数据")
                return CreatorScore(
                    user_id=user_id,
                    username=f"user_{user_id}",
                    account_quality=AccountQualityScore(0, 0, 0, 0, 1.0),
                    content_interaction=ContentInteractionScore(0, 0, 0, 0, 0),
                    final_score=0.0,
                    video_count=0,
                    calculated_at=datetime.now()
                )
            
            print(f"✅ 成功获取 {len(video_details)} 个视频数据")
            
            # 3. 获取用户档案信息
            print(f"📡 API调用: 获取用户档案信息")
            try:
                user_profile = self.api_client.fetch_user_profile(sec_uid)
                print(f"✅ 成功获取用户档案: {user_profile.username}")
                print(f"📊 用户数据: 粉丝数 {user_profile.follower_count}, 总点赞 {user_profile.total_likes}")
            except Exception as e:
                print(f"⚠️ 无法获取详细用户档案，使用基本信息: {str(e)}")
                # 创建基本用户档案
                user_profile = UserProfile(
                    user_id=user_id,
                    username=f"user_{user_id}",
                    display_name=f"user_{user_id}",
                    follower_count=0,
                    following_count=0,
                    total_likes=sum(video.like_count for video in video_details),
                    video_count=len(video_details),
                    bio="",
                    avatar_url="",
                    verified=False
                )
            
            # 4. 计算账户质量评分
            print(f"\n🧮 计算账户质量评分")
            print(f"📋 账户质量评分包含三个维度:")
            print(f"   • 粉丝数量评分 (权重40%)")
            print(f"   • 总点赞数评分 (权重40%)")
            print(f"   • 发布频率评分 (权重20%)")
            
            account_quality = self.account_calculator.calculate_account_quality(
                user_profile, video_details
            )
            
            print(f"📊 账户质量评分详情:")
            print(f"   • 粉丝数量: {user_profile.follower_count:,} → 得分: {account_quality.follower_score:.2f}/100")
            print(f"   • 总点赞数: {user_profile.total_likes:,} → 得分: {account_quality.likes_score:.2f}/100")
            print(f"   • 发布频率: 得分: {account_quality.posting_score:.2f}/100")
            print(f"   • 账户质量总分: {account_quality.total_score:.2f}/100")
            print(f"   • 质量加权系数: {account_quality.multiplier:.3f}")
            
            # 5. 计算内容互动评分
            print(f"\n🧮 计算内容互动评分")
            print(f"📋 内容互动评分包含四个维度:")
            print(f"   • 播放量表现 (权重10%)")
            print(f"   • 点赞率表现 (权重25%)")
            print(f"   • 评论率表现 (权重30%)")
            print(f"   • 分享率表现 (权重35%)")
            
            content_interaction = self.content_calculator.calculate_weighted_content_score(
                video_details, user_profile.follower_count
            )
            
            print(f"📊 内容互动评分详情:")
            print(f"   • 播放量表现: {content_interaction.view_score:.2f}/100")
            print(f"   • 点赞率表现: {content_interaction.like_score:.2f}/100")
            print(f"   • 评论率表现: {content_interaction.comment_score:.2f}/100")
            print(f"   • 分享率表现: {content_interaction.share_score:.2f}/100")
            print(f"   • 内容互动总分: {content_interaction.total_score:.2f}/100")
            
            # 6. 计算最终评分
            print(f"\n🧮 计算最终评分")
            print(f"📋 主评分公式:")
            print(f"   TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权")
            print(f"   其中: 内容质量固定为60分")
            
            final_score = self._calculate_final_score(
                account_quality, content_interaction
            )
            
            # 计算基础分数用于显示
            base_score = (
                content_interaction.total_score * self.content_weight +
                self.content_quality_score * self.content_quality_weight
            )
            
            print(f"📊 最终评分计算详情:")
            print(f"   • 内容互动分数: {content_interaction.total_score:.2f} × 65% = {content_interaction.total_score * 0.65:.2f}")
            print(f"   • 内容质量分数: {self.content_quality_score:.2f} × 35% = {self.content_quality_score * 0.35:.2f}")
            print(f"   • 基础分数: {base_score:.2f}")
            print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
            print(f"   • 最终评分: {final_score:.2f}")
            
            return CreatorScore(
                user_id=user_profile.user_id,
                username=user_profile.username,
                account_quality=account_quality,
                content_interaction=content_interaction,
                final_score=final_score,
                video_count=len(video_details),
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"通过用户ID {user_id} 计算评分时发生错误: {e}")
            raise
            
    def _calculate_final_score(self,
                             account_quality: AccountQualityScore,
                             content_interaction: ContentInteractionScore) -> float:
        """计算最终评分
        
        主评分公式：
        TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权
        
        Args:
            account_quality: 账户质量评分
            content_interaction: 内容互动评分
            
        Returns:
            最终评分
        """
        # 基础分数计算：内容互动数据 × 65% + 内容质量 × 35%
        base_score = (
            content_interaction.total_score * self.content_weight +
            self.content_quality_score * self.content_quality_weight
        )
        
        # 应用账户质量加权
        final_score = base_score * account_quality.multiplier
        
        logger.info(
            f"最终评分计算 - 内容互动分: {content_interaction.total_score:.2f}, "
            f"内容质量分: {self.content_quality_score:.2f}, "
            f"基础分: {base_score:.2f}, "
            f"加权系数: {account_quality.multiplier}, "
            f"最终分: {final_score:.2f}"
        )
        
        return min(final_score, 1000.0)  # 设置上限为1000分
        
    async def batch_calculate_scores(self,
                                   usernames: List[str],
                                   video_count: int = 20) -> List[CreatorScore]:
        """批量计算多个创作者的评分
        
        Args:
            usernames: 用户名列表
            video_count: 每个用户分析的视频数量
            
        Returns:
            创作者评分列表
        """
        results = []
        
        for username in usernames:
            try:
                score = await self.calculate_creator_score(username, video_count)
                results.append(score)
                logger.info(f"用户 {username} 评分计算成功")
            except Exception as e:
                logger.error(f"用户 {username} 评分计算失败: {e}")
                continue
                
        return results
        
    def get_score_breakdown(self, creator_score: CreatorScore) -> dict:
        """获取评分详细分解
        
        Args:
            creator_score: 创作者评分对象
            
        Returns:
            评分分解字典
        """
        account_quality = creator_score.account_quality
        content_interaction = creator_score.content_interaction
        
        return {
            "用户名": creator_score.username,
            "最终评分": round(creator_score.final_score, 2),
            "视频数量": creator_score.video_count,
            "账户质量评分": {
                "粉丝数量得分": round(account_quality.follower_score, 2),
                "总点赞得分": round(account_quality.likes_score, 2),
                "发布频率得分": round(account_quality.posting_score, 2),
                "账户质量总分": round(account_quality.total_score, 2),
                "质量加权系数": account_quality.multiplier
            },
            "内容互动评分": {
                "播放量得分": round(content_interaction.view_score, 2),
                "点赞得分": round(content_interaction.like_score, 2),
                "评论得分": round(content_interaction.comment_score, 2),
                "分享得分": round(content_interaction.share_score, 2),
                "内容互动总分": round(content_interaction.total_score, 2)
            },
            "权重配置": {
                "内容互动权重": f"{self.content_weight * 100}%",
                "内容质量权重": f"{self.content_quality_weight * 100}%",
                "内容质量固定分数": self.content_quality_score
            }
        }
        
    def compare_creators(self, creator_scores: List[CreatorScore]) -> List[dict]:
        """比较多个创作者的评分
        
        Args:
            creator_scores: 创作者评分列表
            
        Returns:
            排序后的创作者比较列表
        """
        # 按最终评分排序
        sorted_scores = sorted(
            creator_scores, 
            key=lambda x: x.final_score, 
            reverse=True
        )
        
        comparison = []
        for i, score in enumerate(sorted_scores, 1):
            comparison.append({
                "排名": i,
                "用户名": score.username,
                "最终评分": round(score.final_score, 2),
                "账户质量分": round(score.account_quality.total_score, 2),
                "内容互动分": round(score.content_interaction.total_score, 2),
                "质量加权系数": score.account_quality.multiplier,
                "视频数量": score.video_count
            })
            
        return comparison