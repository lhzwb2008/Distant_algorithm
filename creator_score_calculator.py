"""TikTok创作者评分计算器（主评分公式）"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import Config
from models import (
    UserProfile, VideoDetail, VideoMetrics, 
    AccountQualityScore, ContentInteractionScore, CreatorScore
)
from api_client import TiKhubAPIClient
from account_quality_calculator import AccountQualityCalculator
from content_interaction_calculator import ContentInteractionCalculator
from video_quality_scorer import VideoQualityScorer
from improved_api_flow import ImprovedAPIFlow
from openrouter_client import QualityScore

logger = logging.getLogger(__name__)

class CreatorScoreCalculator:
    """TikTok创作者评分计算器
    
    主评分公式：
    TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权
    
    注：内容质量使用AI评分，无AI评分时为0分
    """
    
    def __init__(self, api_client: Optional[TiKhubAPIClient] = None):
        """初始化评分计算器
        
        Args:
            api_client: TiKhub API客户端，如果不提供则创建新实例
        """
        self.api_client = api_client or TiKhubAPIClient()
        self.account_calculator = AccountQualityCalculator()
        self.content_calculator = ContentInteractionCalculator()
        self.quality_scorer = VideoQualityScorer()
        self.improved_flow = ImprovedAPIFlow(self.api_client, self.quality_scorer)
        
        # 权重配置
        self.content_weight = Config.CONTENT_INTERACTION_WEIGHT  # 65%
        self.content_quality_weight = 0.35  # 35% 内容质量权重
        self.content_quality_score = 0.0    # 内容质量默认分数（当没有AI评分时使用0分）
        
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
    
    def calculate_creator_score_by_user_id(self, user_id: str, video_count: int = 100, keyword: str = None, project_name: str = None) -> CreatorScore:
        """通过用户ID计算创作者评分（使用优化的API流程）
        
        Args:
            user_id: TikTok用户ID
            video_count: 获取的视频数量，默认100个用于内容互动分计算
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            project_name: 项目方名称筛选，如果提供则筛选包含该项目方名称的视频
            
        Returns:
            创作者评分对象
        """
        try:
            # 1. 使用传入的user_id作为secUid（因为调用方已经转换过了）
            sec_uid = user_id
            print(f"✅ 使用secUid: {sec_uid[:20]}...")
            
            # 2. 🔄 使用优化的API流程
            print(f"🚀 开始使用优化的API调用流程")
            
            # 阶段1：获取账户质量分数据（最近3个月，不调用大模型）
            print(f"📊 阶段1: 获取账户质量分计算数据")
            account_quality_videos = self.improved_flow.fetch_videos_for_account_quality(sec_uid)
            
            # 阶段2：获取内容互动分数据并对匹配关键词的视频进行AI评分
            print(f"🎯 阶段2: 获取内容互动分计算数据并进行AI质量评分")
            if keyword:
                print(f"   🔍 关键词筛选: '{keyword}'")
            else:
                print(f"   📋 无关键词筛选，获取前{video_count}条视频")
            
            content_interaction_videos, ai_quality_scores = self.improved_flow.fetch_videos_for_content_interaction_with_ai_scoring(
                sec_uid, keyword=keyword, project_name=project_name, max_videos=video_count
            )
            
            # 数据获取结果统计
            print(f"✅ 账户质量分计算: 获取 {len(account_quality_videos)} 个视频数据（最近3个月）")
            print(f"✅ 内容互动分计算: 获取 {len(content_interaction_videos)} 个视频数据（最近{video_count}条）")
            print(f"🤖 AI质量评分: 完成 {len(ai_quality_scores)} 个视频的评分")
            
            # 如果最近三个月没有视频数据，仍然要获取用户档案信息来计算账户质量分
            if not account_quality_videos:
                print(f"⚠️  用户 {user_id} 最近三个月没有视频数据，但仍会计算账户质量分（粉丝数、总点赞数）")
            
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
                    total_likes=sum(video.like_count for video in content_interaction_videos),
                    video_count=len(content_interaction_videos),
                    bio="",
                    avatar_url="",
                    verified=False
                )
            
            # 4. 计算账户质量评分
            print(f"\n🧮 计算账户质量评分")
            print(f"📋 账户质量评分包含三个维度:")
            print(f"   • 粉丝数量评分 (权重40%)")
            print(f"   • 总点赞数评分 (权重40%)")
            print(f"   • 发布频率评分 (权重20%) - 基于最近三个月的所有作品")
            
            account_quality = self.account_calculator.calculate_account_quality(
                user_profile, account_quality_videos  # 使用最近3个月的视频数据
            )
            
            print(f"📊 账户质量评分详情:")
            print(f"   • 粉丝数量: {user_profile.follower_count:,} → 得分: {account_quality.follower_score:.2f}/100")
            print(f"   • 总点赞数: {user_profile.total_likes:,} → 得分: {account_quality.likes_score:.2f}/100")
            print(f"   • 发布频率: 得分: {account_quality.posting_score:.2f}/100")
            print(f"   • 账户质量总分: {account_quality.total_score:.2f}/100")
            print(f"   • 质量加权系数: {account_quality.multiplier:.3f}")
            
            # 5. 计算内容互动评分
            print(f"\n🧮 计算内容互动评分")
            if keyword:
                print(f"📋 内容互动评分包含五个维度（基于最近{video_count}条视频中关键词'{keyword}'匹配的{len(content_interaction_videos)}个作品）:")
            else:
                print(f"📋 内容互动评分包含五个维度（基于最近{video_count}条视频中的{len(content_interaction_videos)}个作品）:")
            print(f"   • 播放量表现 (权重10%)")
            print(f"   • 点赞率表现 (权重15%)")
            print(f"   • 评论率表现 (权重30%)")
            print(f"   • 分享率表现 (权重30%)")
            print(f"   • 保存率表现 (权重15%)")
            
            content_interaction = self.content_calculator.calculate_weighted_content_score(
                content_interaction_videos, user_profile.follower_count  # 使用新的API流程获取的视频数据
            )
            
            print(f"📊 内容互动评分详情:")
            print(f"   • 播放量表现: {content_interaction.view_score:.2f}/100")
            print(f"   • 点赞率表现: {content_interaction.like_score:.2f}/100")
            print(f"   • 评论率表现: {content_interaction.comment_score:.2f}/100")
            print(f"   • 分享率表现: {content_interaction.share_score:.2f}/100")
            print(f"   • 保存率表现: {content_interaction.save_score:.2f}/100")
            print(f"   • 内容互动总分: {content_interaction.total_score:.2f}/100")
            
            # 6. 计算最终评分
            print(f"\n🧮 计算最终评分")
            print(f"📋 新主评分公式:")
            print(f"   TikTok Creator Score = (40%峰值表现 + 40%近期状态 + 20%整体水平) × 账户质量加权")
            print(f"   其中: 每个视频评分 = 内容互动数据 × 65% + 内容质量 × 35%")
            print(f"   内容质量使用AI评分，无AI评分时为0分")
            
            # 6. 🤖 集成AI质量评分到最终计算
            print(f"\n🤖 AI视频质量评分集成")
            if ai_quality_scores:
                avg_ai_score = sum(score.total_score for score in ai_quality_scores.values()) / len(ai_quality_scores)
                print(f"📊 AI质量评分统计:")
                print(f"   • 评分视频数: {len(ai_quality_scores)}")
                print(f"   • 平均AI质量分: {avg_ai_score:.1f}/100 (AI智能评分)")
                print(f"   • 最高AI质量分: {max(score.total_score for score in ai_quality_scores.values()):.1f}/100")
                print(f"   • 最低AI质量分: {min(score.total_score for score in ai_quality_scores.values()):.1f}/100")
                
                # 显示每个视频的AI评分详情
                print(f"📋 各视频AI质量评分详情:")
                for video_id, ai_score in ai_quality_scores.items():
                    print(f"   • 视频 {video_id}: {ai_score.total_score:.1f}/100")
                    print(f"     - 关键词: {ai_score.keyword_score:.1f}/60")
                    print(f"     - 原创性: {ai_score.originality_score:.1f}/20") 
                    print(f"     - 清晰度: {ai_score.clarity_score:.1f}/10")
                    print(f"     - 垃圾识别: {ai_score.spam_score:.1f}/5")
                    print(f"     - 推广识别: {ai_score.promotion_score:.1f}/5")
            else:
                print(f"⚠️  没有AI质量评分数据，内容质量分为: {self.content_quality_score}/100")
                print(f"   • 原因: 没有匹配关键词的视频或字幕提取失败")
            
            final_score = self._calculate_final_score_with_ai(
                account_quality, content_interaction_videos, user_profile.follower_count, ai_quality_scores
            )
            
            # 计算基础分数用于显示（使用新算法）
            if content_interaction_videos:
                all_video_scores = []
                for video in content_interaction_videos:
                    video_score = self._calculate_single_video_score_with_ai(video, user_profile.follower_count, ai_quality_scores)
                    all_video_scores.append(video_score)
                
                # 过滤掉视频链接无效的视频（-1.0标识）
                valid_video_scores = [score for score in all_video_scores if score >= 0.0]
                
                if valid_video_scores:
                    n = len(valid_video_scores)
                    peak_performance = max(valid_video_scores)
                    
                    # 从原始顺序中找到最近的有效视频
                    recent_valid_scores = []
                    for score in all_video_scores:
                        if score >= 0.0:
                            recent_valid_scores.append(score)
                            if len(recent_valid_scores) >= 3:
                                break
                    recent_performance = sum(recent_valid_scores) / len(recent_valid_scores)
                    overall_performance = sum(valid_video_scores) / n
                    
                    base_score = (
                        0.4 * peak_performance +      # 40%看峰值表现
                        0.4 * recent_performance +    # 40%看近期状态
                        0.2 * overall_performance     # 20%看整体水平
                    )
                else:
                    # 所有视频都链接无效，使用默认分数
                    base_score = self.content_quality_score * self.content_quality_weight
                    peak_performance = recent_performance = overall_performance = 0.0
            else:
                base_score = self.content_quality_score * self.content_quality_weight
            
            print(f"📊 最终评分计算详情:")
            if content_interaction_videos:
                if valid_video_scores:
                    invalid_count = len(all_video_scores) - len(valid_video_scores)
                    print(f"   • 视频总数: {len(content_interaction_videos)} 个 (有效: {len(valid_video_scores)} 个, 链接无效: {invalid_count} 个)")
                    print(f"   • 峰值表现: {peak_performance:.2f} × 40% = {peak_performance * 0.4:.2f}")
                    print(f"   • 近期状态: {recent_performance:.2f} × 40% = {recent_performance * 0.4:.2f} (最近{len(recent_valid_scores)}条有效视频)")
                    print(f"   • 整体水平: {overall_performance:.2f} × 20% = {overall_performance * 0.2:.2f} (所有有效视频)")
                    print(f"   • 基础分数: {base_score:.2f}")
                    print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
                    if ai_quality_scores:
                        print(f"   • AI质量评分影响: {len(ai_quality_scores)}个视频使用AI评分AI智能评分")
                    if invalid_count > 0:
                        print(f"   ⚠️ 注意: {invalid_count}个视频因链接无效未参与评分计算")
                else:
                    print(f"   • 视频总数: {len(content_interaction_videos)} 个 (全部链接无效)")
                    print(f"   • 使用默认内容质量分数: {self.content_quality_score:.2f}")
                    print(f"   • 基础分数: {base_score:.2f}")
                    print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
            else:
                print(f"   • 无视频数据，使用默认内容质量分数: {self.content_quality_score:.2f}")
                print(f"   • 基础分数: {base_score:.2f}")
                print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
            print(f"   • 最终评分: {final_score:.2f}")
            
            return CreatorScore(
                user_id=user_profile.user_id,
                username=user_profile.username,
                account_quality=account_quality,
                content_interaction=content_interaction,
                final_score=final_score,
                video_count=len(content_interaction_videos),  # 使用新的视频数据
                calculated_at=datetime.now(),
                # 新算法相关字段
                peak_performance=peak_performance if content_interaction_videos else 0.0,
                recent_performance=recent_performance if content_interaction_videos else 0.0,
                overall_performance=overall_performance if content_interaction_videos else 0.0,
                video_scores=all_video_scores if content_interaction_videos else []
            )
            
        except Exception as e:
            logger.error(f"通过用户ID {user_id} 计算评分时发生错误: {e}")
            raise
            
    def _calculate_single_video_score(self, video: VideoDetail, follower_count: int) -> float:
        """计算单个视频的评分
        
        单视频评分公式：
        Video Score = 内容互动数据 × 65% + 内容质量 × 35%
        其中内容质量使用AI评分，无AI评分时为0分
        
        Args:
            video: 视频详情
            follower_count: 粉丝数量
            
        Returns:
            单个视频评分 (0-100)
        """
        # 计算内容互动各项得分
        view_score = self.content_calculator.calculate_view_score(video.view_count, follower_count)
        like_score = self.content_calculator.calculate_like_score(video.like_count, video.view_count, follower_count)
        comment_score = self.content_calculator.calculate_comment_score(video.comment_count, video.view_count, follower_count)
        share_score = self.content_calculator.calculate_share_score(video.share_count, video.view_count, follower_count)
        save_score = self.content_calculator.calculate_save_score(
            getattr(video, 'collect_count', 0), video.view_count, follower_count
        )
        
        # 计算内容互动总分（按权重）
        content_interaction_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        # 单视频评分 = 内容互动数据 × 65% + 内容质量 × 35%
        video_score = (
            content_interaction_score * self.content_weight +
            self.content_quality_score * self.content_quality_weight
        )
        
        return max(0.0, min(100.0, video_score))
    
    def _calculate_single_video_score_with_ai(self, video: VideoDetail, follower_count: int, ai_quality_scores: Dict[str, QualityScore]) -> float:
        """计算单个视频的评分（集成AI质量评分）
        
        单视频评分公式：
        - 如果AI评分为0分（视频内容与筛选条件不相关），直接返回0分
        - 否则：Video Score = 内容互动数据 × 65% + 内容质量 × 35%
        其中内容质量：有AI评分时使用AI评分，否则使用默认值
        
        Args:
            video: 视频详情
            follower_count: 粉丝数量
            ai_quality_scores: AI质量评分字典
            
        Returns:
            单个视频评分 (0-100)
        """
        # 计算内容互动各项得分
        view_score = self.content_calculator.calculate_view_score(video.view_count, follower_count)
        like_score = self.content_calculator.calculate_like_score(video.like_count, video.view_count, follower_count)
        comment_score = self.content_calculator.calculate_comment_score(video.comment_count, video.view_count, follower_count)
        share_score = self.content_calculator.calculate_share_score(video.share_count, video.view_count, follower_count)
        save_score = self.content_calculator.calculate_save_score(
            getattr(video, 'collect_count', 0), video.view_count, follower_count
        )
        
        # 计算内容互动总分（按权重）
        content_interaction_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        # 获取内容质量分：优先使用AI评分，否则使用默认值
        if video.video_id in ai_quality_scores:
            ai_score = ai_quality_scores[video.video_id]
            content_quality_score = ai_score.total_score
            
            # 重要逻辑：如果AI评分为0分，需要区分两种情况
            if content_quality_score == 0.0:
                # 检查是否是视频链接无效导致的0分
                if ai_score.reasoning and ("视频链接无效" in ai_score.reasoning or 
                                         "无法获取视频内容" in ai_score.reasoning or
                                         "视频没有字幕数据" in ai_score.reasoning or
                                         "字幕质量评分失败" in ai_score.reasoning or
                                         "Gemini视频分析失败" in ai_score.reasoning or
                                         "Gemini视频分析异常" in ai_score.reasoning):
                    # 视频链接无效，返回-1标识，不参与总分计算
                    return -1.0
                else:
                    # 视频内容与筛选条件不相关，返回0分
                    return 0.0
                
        else:
            # 重要逻辑：如果没有AI评分数据，说明视频不符合筛选条件，直接返回0分
            # 这种情况通常发生在关键词筛选时，视频内容不包含目标关键词
            if ai_quality_scores is not None:  # 如果提供了AI评分字典但该视频不在其中
                return 0.0
            content_quality_score = self.content_quality_score
        
        # 单视频评分 = 内容互动数据 × 65% + 内容质量 × 35%
        video_score = (
            content_interaction_score * self.content_weight +
            content_quality_score * self.content_quality_weight
        )
        
        return max(0.0, min(100.0, video_score))
    
    def _calculate_final_score_with_ai(self,
                                     account_quality: AccountQualityScore,
                                     video_details: List[VideoDetail],
                                     follower_count: int,
                                     ai_quality_scores: Dict[str, QualityScore]) -> float:
        """计算最终评分（集成AI质量评分）
        
        使用新的三维评分算法：
        - 40% 峰值表现（最高分视频）
        - 40% 近期状态（最近3个视频平均分）  
        - 20% 整体水平（所有视频平均分）
        然后乘以账户质量加权系数
        
        Args:
            account_quality: 账户质量评分
            video_details: 视频详情列表
            follower_count: 粉丝数量
            ai_quality_scores: AI质量评分字典
            
        Returns:
            最终评分
        """
        if not video_details:
            # 没有视频时，只使用固定的内容质量分数
            base_score = self.content_quality_score * self.content_quality_weight
            return base_score * account_quality.multiplier
        
        # 按发布时间排序（最新的在前）
        sorted_videos = sorted(video_details, key=lambda v: v.create_time if v.create_time else datetime.min, reverse=True)
        
        # 计算每个视频的评分（集成AI质量评分，按时间顺序）
        all_video_scores = []
        for video in sorted_videos:
            video_score = self._calculate_single_video_score_with_ai(video, follower_count, ai_quality_scores)
            all_video_scores.append(video_score)
        
        # 过滤掉视频链接无效的视频（-1.0标识），只保留有效视频进行评分计算
        valid_video_scores = [score for score in all_video_scores if score >= 0.0]
        
        # 如果没有有效视频，使用默认分数
        if not valid_video_scores:
            base_score = self.content_quality_score * self.content_quality_weight
            return base_score * account_quality.multiplier
        
        # 应用新的三维评分算法（只使用有效视频）
        n = len(valid_video_scores)
        
        # 1. 峰值表现：取最高分
        peak_performance = max(valid_video_scores)
        
        # 2. 近期状态：最近3个有效视频的平均分
        # 需要从原始顺序中找到最近的有效视频
        recent_valid_scores = []
        for score in all_video_scores:
            if score >= 0.0:
                recent_valid_scores.append(score)
                if len(recent_valid_scores) >= 3:
                    break
        recent_performance = sum(recent_valid_scores) / len(recent_valid_scores)
        
        # 3. 整体水平：所有有效视频的平均分
        overall_performance = sum(valid_video_scores) / n
        
        # 综合评分：40%峰值 + 40%近期 + 20%整体
        base_score = (
            0.4 * peak_performance +   # 40%看峰值表现
            0.4 * recent_performance + # 40%看近期状态
            0.2 * overall_performance  # 20%看整体水平
        )
        
        # 应用账户质量加权
        final_score = base_score * account_quality.multiplier
        
        return max(0.0, min(300.0, final_score))  # 最高300分（100 * 3.0倍数）
    
    def get_score_breakdown(self, creator_score: CreatorScore, ai_quality_scores: Dict[str, QualityScore] = None, video_details: List[VideoDetail] = None, follower_count: int = 0, user_profile: UserProfile = None) -> Dict[str, Any]:
        """获取详细的评分分解信息，包含每个视频的详细计算过程
        
        Args:
            creator_score: 创作者评分对象
            ai_quality_scores: AI质量评分字典
            video_details: 视频详情列表
            follower_count: 粉丝数量
            user_profile: 用户资料信息（包含原始粉丝数、点赞数等）
            
        Returns:
            详细的评分分解信息
        """
        # 计算账户质量权重后的分数（用于显示详细计算过程）
        follower_weighted = creator_score.account_quality.follower_score * 0.4
        likes_weighted = creator_score.account_quality.likes_score * 0.4
        posting_weighted = creator_score.account_quality.posting_score * 0.2
        
        # 计算每个视频的详细评分
        individual_videos = []
        if video_details and follower_count > 0:
            for video in video_details:
                # 复用实际算分逻辑，确保显示值与计算值一致
                video_total_score = self._calculate_single_video_score_with_ai(video, follower_count, ai_quality_scores)
                
                # 计算单个视频的互动各项得分（仅用于显示详情）
                view_score = self.content_calculator.calculate_view_score(video.view_count, follower_count)
                like_score = self.content_calculator.calculate_like_score(video.like_count, video.view_count, follower_count)
                comment_score = self.content_calculator.calculate_comment_score(video.comment_count, video.view_count, follower_count)
                share_score = self.content_calculator.calculate_share_score(video.share_count, video.view_count, follower_count)
                save_score = self.content_calculator.calculate_save_score(
                    getattr(video, 'collect_count', 0), video.view_count, follower_count
                )
                
                # 计算互动总分（仅用于显示详情）
                interaction_total = (
                    view_score * 0.10 + like_score * 0.15 + comment_score * 0.30 +
                    share_score * 0.30 + save_score * 0.15
                )
                
                # 获取AI质量分（仅用于显示详情）
                ai_score = 0.0
                ai_details = "无AI评分"
                if ai_quality_scores and video.video_id in ai_quality_scores:
                    quality_score = ai_quality_scores[video.video_id]
                    ai_score = quality_score.total_score
                    ai_details = f"关键词:{quality_score.keyword_score:.1f} + 原创性:{quality_score.originality_score:.1f} + 清晰度:{quality_score.clarity_score:.1f} + 垃圾识别:{quality_score.spam_score:.1f} + 推广识别:{quality_score.promotion_score:.1f} = {ai_score:.1f}"
                
                # 构建视频链接
                video_url = f"https://www.tiktok.com/@user/video/{video.video_id}"
                
                individual_videos.append({
                    "video_id": video.video_id,
                    "video_url": video_url,
                    "create_time": video.create_time.strftime("%Y-%m-%d %H:%M") if hasattr(video.create_time, 'strftime') else str(video.create_time),
                    "互动数据": {
                        "播放量": f"{video.view_count:,}",
                        "点赞数": f"{video.like_count:,}",
                        "评论数": f"{video.comment_count:,}",
                        "分享数": f"{video.share_count:,}",
                        "保存数": f"{getattr(video, 'collect_count', 0):,}"
                    },
                    "互动评分": {
                        "播放量得分": f"{view_score:.2f}",
                        "点赞得分": f"{like_score:.2f}",
                        "评论得分": f"{comment_score:.2f}",
                        "分享得分": f"{share_score:.2f}",
                        "保存得分": f"{save_score:.2f}",
                        "互动总分": f"{interaction_total:.2f}",
                        "计算过程": f"{view_score:.2f}×10% + {like_score:.2f}×15% + {comment_score:.2f}×30% + {share_score:.2f}×30% + {save_score:.2f}×15% = {interaction_total:.2f}"
                    },
                    "AI质量评分": {
                        "AI总分": f"{ai_score:.2f}",
                        "详细计算": ai_details,
                        "评分理由": ai_quality_scores[video.video_id].reasoning if ai_quality_scores and video.video_id in ai_quality_scores else "无AI评分"
                    },
                    "视频总分": {
                        "总分": f"{video_total_score:.2f}",
                        "计算公式": self._generate_score_formula_explanation(interaction_total, ai_score, video_total_score)
                    }
                })

        breakdown = {
            "视频数量": creator_score.video_count,
            "账户质量评分": {
                "原始数据": {
                    "粉丝数量": f"{user_profile.follower_count:,}" if user_profile else "N/A",
                    "总点赞数": f"{user_profile.total_likes:,}" if user_profile else "N/A",
                    "发布频率": creator_score.account_quality.posting_details.get("weekly_frequency", creator_score.account_quality.posting_details.get("发布频率", "N/A")) if creator_score.account_quality.posting_details else "N/A"
                },
                "粉丝数量得分": f"{creator_score.account_quality.follower_score:.2f}",
                "总点赞得分": f"{creator_score.account_quality.likes_score:.2f}",
                "发布频率得分": f"{creator_score.account_quality.posting_score:.2f}",
                "账户质量总分": f"{creator_score.account_quality.total_score:.2f}",
                "质量加权系数": f"{creator_score.account_quality.multiplier:.3f}",
                "发布频率详细计算": creator_score.account_quality.posting_details or {},
                "详细计算过程": {
                    "粉丝数量计算": f"{creator_score.account_quality.follower_score:.2f} × 40% = {follower_weighted:.2f}",
                    "总点赞数计算": f"{creator_score.account_quality.likes_score:.2f} × 40% = {likes_weighted:.2f}",
                    "发布频率计算": f"{creator_score.account_quality.posting_score:.2f} × 20% = {posting_weighted:.2f}",
                    "账户质量总分": f"{follower_weighted:.2f} + {likes_weighted:.2f} + {posting_weighted:.2f} = {creator_score.account_quality.total_score:.2f}",
                    "质量加权系数": f"根据账户质量总分计算得出 {creator_score.account_quality.multiplier:.3f}"
                }
            },
            "各视频详细评分": individual_videos,
            "内容互动详细计算过程": creator_score.content_interaction.calculation_details or {},
            "最终评分详细计算": {
                "算法说明": "40%峰值表现 + 40%近期状态 + 20%整体水平",
                "视频总数": f"{creator_score.video_count} 个",
                "峰值表现": f"{getattr(creator_score, 'peak_performance', 0):.2f} × 40% = {getattr(creator_score, 'peak_performance', 0) * 0.4:.2f}",
                "近期状态": f"{getattr(creator_score, 'recent_performance', 0):.2f} × 40% = {getattr(creator_score, 'recent_performance', 0) * 0.4:.2f}",
                "整体水平": f"{getattr(creator_score, 'overall_performance', 0):.2f} × 20% = {getattr(creator_score, 'overall_performance', 0) * 0.2:.2f}",
                "基础分数": f"{(getattr(creator_score, 'peak_performance', 0) * 0.4 + getattr(creator_score, 'recent_performance', 0) * 0.4 + getattr(creator_score, 'overall_performance', 0) * 0.2):.2f}",
                "账户质量加权": f"基础分数 × {creator_score.account_quality.multiplier:.3f} = {creator_score.final_score:.2f}",
                "最终评分": f"{creator_score.final_score:.2f}分",
                "说明": "每个视频分别计算：互动分×65% + AI质量分×35% = 视频分，详情请查看下方各视频评分"
            }
        }
        
        return breakdown
    
    def calculate_creator_score_by_user_id_with_ai_scores(self, user_id: str, video_count: int = 100, keyword: str = None, project_name: str = None) -> tuple[CreatorScore, Dict[str, QualityScore], List[VideoDetail], UserProfile]:
        """通过用户ID计算创作者评分并返回AI质量评分（用于Web界面）
        
        Args:
            user_id: TikTok用户ID
            video_count: 获取的视频数量，默认100个用于内容互动分计算
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            project_name: 项目方名称筛选，如果提供则筛选包含该项目方名称的视频
            
        Returns:
            (创作者评分对象, AI质量评分字典)
        """
        try:
            # 1. 使用传入的user_id作为secUid（因为调用方已经转换过了）
            sec_uid = user_id
            print(f"✅ 使用secUid: {sec_uid[:20]}...")
            
            # 2. 🔄 使用优化的API流程
            print(f"🚀 开始使用优化的API调用流程")
            
            # 阶段1：获取账户质量分数据（最近3个月，不调用大模型）
            print(f"📊 阶段1: 获取账户质量分计算数据")
            account_quality_videos = self.improved_flow.fetch_videos_for_account_quality(sec_uid)
            
            # 阶段2：获取内容互动分数据并对匹配关键词的视频进行AI评分
            print(f"🎯 阶段2: 获取内容互动分计算数据并进行AI质量评分")
            if keyword:
                print(f"   🔍 关键词筛选: '{keyword}'")
            else:
                print(f"   📋 无关键词筛选，获取前{video_count}条视频")
            
            content_interaction_videos, ai_quality_scores = self.improved_flow.fetch_videos_for_content_interaction_with_ai_scoring(
                sec_uid, keyword=keyword, project_name=project_name, max_videos=video_count
            )
            
            # 数据获取结果统计
            print(f"✅ 账户质量分计算: 获取 {len(account_quality_videos)} 个视频数据（最近3个月）")
            print(f"✅ 内容互动分计算: 获取 {len(content_interaction_videos)} 个视频数据（最近{video_count}条）")
            print(f"🤖 AI质量评分: 完成 {len(ai_quality_scores)} 个视频的评分")
            
            # 如果最近三个月没有视频数据，仍然要获取用户档案信息来计算账户质量分
            if not account_quality_videos:
                print(f"⚠️  用户 {user_id} 最近三个月没有视频数据，但仍会计算账户质量分（粉丝数、总点赞数）")
            
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
                    total_likes=sum(video.like_count for video in content_interaction_videos),
                    video_count=len(content_interaction_videos),
                    bio="",
                    avatar_url="",
                    verified=False
                )
            
            # 4. 计算账户质量评分
            print(f"\n🧮 计算账户质量评分")
            print(f"📋 账户质量评分包含三个维度:")
            print(f"   • 粉丝数量评分 (权重40%)")
            print(f"   • 总点赞数评分 (权重40%)")
            print(f"   • 发布频率评分 (权重20%) - 基于最近三个月的所有作品")
            
            account_quality = self.account_calculator.calculate_account_quality(
                user_profile, account_quality_videos  # 使用最近3个月的视频数据
            )
            
            print(f"📊 账户质量评分详情:")
            print(f"   • 粉丝数量: {user_profile.follower_count:,} → 得分: {account_quality.follower_score:.2f}/100")
            print(f"   • 总点赞数: {user_profile.total_likes:,} → 得分: {account_quality.likes_score:.2f}/100")
            print(f"   • 发布频率: 得分: {account_quality.posting_score:.2f}/100")
            print(f"   • 账户质量总分: {account_quality.total_score:.2f}/100")
            print(f"   • 质量加权系数: {account_quality.multiplier:.3f}")
            
            # 5. 计算内容互动评分
            print(f"\n🧮 计算内容互动评分")
            if keyword:
                print(f"📋 内容互动评分包含五个维度（基于最近{video_count}条视频中关键词'{keyword}'匹配的{len(content_interaction_videos)}个作品）:")
            else:
                print(f"📋 内容互动评分包含五个维度（基于最近{video_count}条视频中的{len(content_interaction_videos)}个作品）:")
            print(f"   • 播放量表现 (权重10%)")
            print(f"   • 点赞率表现 (权重15%)")
            print(f"   • 评论率表现 (权重30%)")
            print(f"   • 分享率表现 (权重30%)")
            print(f"   • 保存率表现 (权重15%)")
            
            content_interaction = self.content_calculator.calculate_weighted_content_score(
                content_interaction_videos, user_profile.follower_count  # 使用新的API流程获取的视频数据
            )
            
            print(f"📊 内容互动评分详情:")
            print(f"   • 播放量表现: {content_interaction.view_score:.2f}/100")
            print(f"   • 点赞率表现: {content_interaction.like_score:.2f}/100")
            print(f"   • 评论率表现: {content_interaction.comment_score:.2f}/100")
            print(f"   • 分享率表现: {content_interaction.share_score:.2f}/100")
            print(f"   • 保存率表现: {content_interaction.save_score:.2f}/100")
            print(f"   • 内容互动总分: {content_interaction.total_score:.2f}/100")
            
            # 6. 计算最终评分
            print(f"\n🧮 计算最终评分")
            print(f"📋 新主评分公式:")
            print(f"   TikTok Creator Score = (40%峰值表现 + 40%近期状态 + 20%整体水平) × 账户质量加权")
            print(f"   其中: 每个视频评分 = 内容互动数据 × 65% + 内容质量 × 35%")
            print(f"   内容质量使用AI评分，无AI评分时为0分")
            
            # 6. 🤖 集成AI质量评分到最终计算
            print(f"\n🤖 AI视频质量评分集成")
            if ai_quality_scores:
                avg_ai_score = sum(score.total_score for score in ai_quality_scores.values()) / len(ai_quality_scores)
                print(f"📊 AI质量评分统计:")
                print(f"   • 评分视频数: {len(ai_quality_scores)}")
                print(f"   • 平均AI质量分: {avg_ai_score:.1f}/100 (AI智能评分)")
                print(f"   • 最高AI质量分: {max(score.total_score for score in ai_quality_scores.values()):.1f}/100")
                print(f"   • 最低AI质量分: {min(score.total_score for score in ai_quality_scores.values()):.1f}/100")
                
                # 显示每个视频的AI评分详情
                print(f"📋 各视频AI质量评分详情:")
                for video_id, ai_score in ai_quality_scores.items():
                    print(f"   • 视频 {video_id}: {ai_score.total_score:.1f}/100")
                    print(f"     - 关键词: {ai_score.keyword_score:.1f}/60")
                    print(f"     - 原创性: {ai_score.originality_score:.1f}/20") 
                    print(f"     - 清晰度: {ai_score.clarity_score:.1f}/10")
                    print(f"     - 垃圾识别: {ai_score.spam_score:.1f}/5")
                    print(f"     - 推广识别: {ai_score.promotion_score:.1f}/5")
            else:
                print(f"⚠️  没有AI质量评分数据，内容质量分为: {self.content_quality_score}/100")
                print(f"   • 原因: 没有匹配关键词的视频或字幕提取失败")
            
            final_score = self._calculate_final_score_with_ai(
                account_quality, content_interaction_videos, user_profile.follower_count, ai_quality_scores
            )
            
            # 计算基础分数用于显示（使用新算法）
            if content_interaction_videos:
                all_video_scores = []
                for video in content_interaction_videos:
                    video_score = self._calculate_single_video_score_with_ai(video, user_profile.follower_count, ai_quality_scores)
                    all_video_scores.append(video_score)
                
                # 过滤掉视频链接无效的视频（-1.0标识）
                valid_video_scores = [score for score in all_video_scores if score >= 0.0]
                
                if valid_video_scores:
                    n = len(valid_video_scores)
                    peak_performance = max(valid_video_scores)
                    
                    # 从原始顺序中找到最近的有效视频
                    recent_valid_scores = []
                    for score in all_video_scores:
                        if score >= 0.0:
                            recent_valid_scores.append(score)
                            if len(recent_valid_scores) >= 3:
                                break
                    recent_performance = sum(recent_valid_scores) / len(recent_valid_scores)
                    overall_performance = sum(valid_video_scores) / n
                    
                    base_score = (
                        0.4 * peak_performance +   # 40%看峰值表现
                        0.4 * recent_performance + # 40%看近期状态
                        0.2 * overall_performance     # 20%看整体水平
                    )
                else:
                    # 所有视频都链接无效，使用默认分数
                    base_score = self.content_quality_score * self.content_quality_weight
                    peak_performance = recent_performance = overall_performance = 0.0
                    recent_valid_scores = []  # 无有效视频时设为空列表
            else:
                base_score = self.content_quality_score * self.content_quality_weight
                peak_performance = recent_performance = overall_performance = 0.0
                recent_valid_scores = []  # 无视频数据时设为空列表
            
            print(f"📊 最终评分计算详情:")
            if content_interaction_videos:
                print(f"   • 视频总数: {len(content_interaction_videos)} 个")
                print(f"   • 峰值表现: {peak_performance:.2f} × 40% = {peak_performance * 0.4:.2f}")
                print(f"   • 近期状态: {recent_performance:.2f} × 40% = {recent_performance * 0.4:.2f} (最近{len(recent_valid_scores)}条有效视频)")
                print(f"   • 整体水平: {overall_performance:.2f} × 20% = {overall_performance * 0.2:.2f} (所有视频)")
                print(f"   • 基础分数: {base_score:.2f}")
                print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
                if ai_quality_scores:
                    print(f"   • AI质量评分影响: {len(ai_quality_scores)}个视频使用AI评分AI智能评分")
            else:
                print(f"   • 无视频数据，使用默认内容质量分数: {self.content_quality_score:.2f}")
                print(f"   • 基础分数: {base_score:.2f}")
                print(f"   • 账户质量加权: {base_score:.2f} × {account_quality.multiplier:.3f} = {final_score:.2f}")
            print(f"   • 最终评分: {final_score:.2f}")
            
            creator_score = CreatorScore(
                user_id=user_profile.user_id,
                username=user_profile.username,
                account_quality=account_quality,
                content_interaction=content_interaction,
                final_score=final_score,
                video_count=len(content_interaction_videos),  # 使用新的视频数据
                calculated_at=datetime.now(),
                # 新算法相关字段
                peak_performance=peak_performance if content_interaction_videos else 0.0,
                recent_performance=recent_performance if content_interaction_videos else 0.0,
                overall_performance=overall_performance if content_interaction_videos else 0.0,
                video_scores=video_scores if content_interaction_videos else []
            )
            
            return creator_score, ai_quality_scores, content_interaction_videos, user_profile
            
        except Exception as e:
            logger.error(f"通过用户ID {user_id} 计算评分时发生错误: {e}")
            raise
    
    def _calculate_final_score(self,
                             account_quality: AccountQualityScore,
                             video_details: List[VideoDetail],
                             follower_count: int) -> float:
        """计算最终评分
        
        新主评分公式：
        TikTok Creator Score = (
            0.4 × max(V₁, V₂, ..., Vₙ) +           # 40%看峰值表现
            0.4 × 最近3条视频平均分 +                 # 40%看近期状态  
            0.2 × 近100条视频平均分                  # 20%看整体水平
        ) × 账户质量加权
        
        Args:
            account_quality: 账户质量评分
            video_details: 视频详情列表
            follower_count: 粉丝数量
            
        Returns:
            最终评分
        """
        if not video_details:
            # 如果没有视频数据，返回基础分数
            base_score = self.content_quality_score * self.content_quality_weight
            return base_score * account_quality.multiplier
        
        # 按发布时间排序（最新的在前）
        sorted_videos = sorted(video_details, key=lambda v: v.create_time if v.create_time else datetime.min, reverse=True)
        
        # 计算每个视频的评分（按时间顺序）
        video_scores = []
        for video in sorted_videos:
            video_score = self._calculate_single_video_score(video, follower_count)
            video_scores.append(video_score)
        
        n = len(video_scores)
        
        # 1. 峰值表现：最高分数 (40%权重)
        peak_performance = max(video_scores)
        
        # 2. 近期状态：最近3条视频平均分 (40%权重，现在是按时间最新的3个)
        recent_videos_count = min(3, n)
        recent_scores = video_scores[:recent_videos_count]  # 取前3个（最新的）
        recent_performance = sum(recent_scores) / len(recent_scores)
        
        # 3. 整体水平：所有视频平均分 (20%权重)
        overall_performance = sum(video_scores) / n
        
        # 计算基础分数
        base_score = (
            0.4 * peak_performance +      # 40%看峰值表现
            0.4 * recent_performance +    # 40%看近期状态
            0.2 * overall_performance     # 20%看整体水平
        )
        
        # 应用账户质量加权
        final_score = base_score * account_quality.multiplier
        
        logger.info(
            f"最终评分计算 - 视频数量: {n}, "
            f"峰值表现: {peak_performance:.2f}, "
            f"近期状态: {recent_performance:.2f}, "
            f"整体水平: {overall_performance:.2f}, "
            f"基础分: {base_score:.2f}, "
            f"加权系数: {account_quality.multiplier:.3f}, "
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
    
    def _generate_score_formula_explanation(self, interaction_total: float, ai_score: float, video_total_score: float) -> str:
        """
        生成视频总分计算公式的详细说明，包含特殊逻辑处理
        """
        # 计算理论值（按公式计算的结果）
        theoretical_score = interaction_total * 0.65 + ai_score * 0.35
        
        # 基础公式
        base_formula = f"互动分×65% + AI质量分×35% = {interaction_total:.2f}×0.65 + {ai_score:.2f}×0.35 = {theoretical_score:.2f}"
        
        # 检查是否有特殊逻辑生效
        if ai_score == 0.0 and video_total_score == 0.0 and theoretical_score > 0:
            return f"{base_formula}\n⚠️ 特殊规则：AI质量评分为0时，视频总分强制设为0.00"
        elif video_total_score != theoretical_score:
            return f"{base_formula}\n⚠️ 应用特殊评分逻辑，最终得分：{video_total_score:.2f}"
        else:
            return base_formula
        
