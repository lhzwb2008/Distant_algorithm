#!/usr/bin/env python3
"""
优化的API调用流程 - 修复版
使用原有工作的方法来确保可靠性
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from api_client import TiKhubAPIClient
from video_quality_scorer import VideoQualityScorer
from video_content_analyzer import VideoContentAnalyzer
from models import VideoDetail
from openrouter_client import QualityScore
from config import Config

logger = logging.getLogger(__name__)

class ImprovedAPIFlow:
    """改进的API调用流程"""
    
    def __init__(self, api_client: TiKhubAPIClient = None, quality_scorer: VideoQualityScorer = None):
        """
        初始化改进的API流程
        
        Args:
            api_client: TikHub API客户端
            quality_scorer: 视频质量评分器
        """
        self.api_client = api_client or TiKhubAPIClient()
        self.quality_scorer = quality_scorer or VideoQualityScorer()
        self.content_analyzer = VideoContentAnalyzer()
    
    def fetch_videos_for_account_quality(self, user_id: str) -> List[VideoDetail]:
        """
        获取用于账户质量分计算的视频（最近3个月，不调用大模型）
        
        Args:
            user_id: 用户ID
            
        Returns:
            视频详情列表
        """
        logger.info("📊 第一阶段：获取账户质量分计算所需的视频数据")
        logger.info("   - 数据范围：最近3个月的所有视频")
        logger.info("   - 用途：计算发布频率评分")
        logger.info("   - 大模型调用：❌ 不调用")
        
        try:
            # 使用原有的工作方法获取最近3个月的视频
            videos = self.api_client.fetch_user_videos_last_3_months(user_id)
            logger.info(f"✅ 账户质量分数据获取完成：{len(videos)} 个视频")
            return videos
        except Exception as e:
            logger.error(f"获取账户质量分视频数据失败: {e}")
            return []
    
    def fetch_videos_for_content_interaction_with_ai_scoring(
        self, 
        user_id: str, 
        keyword: str = None, 
        project_name: str = None,
        max_videos: int = 100
    ) -> tuple[List[VideoDetail], Dict[str, QualityScore], int]:
        """获取用于内容互动分计算的视频，并对匹配关键词的视频进行AI评分
        
        Args:
            user_id: 用户ID
            keyword: 关键词筛选
            project_name: 项目方名称筛选
            max_videos: 最大视频数量
            
        Returns:
            (视频详情列表, AI质量评分字典, 筛选前的总视频数量)
        """
        logger.info("🎯 第二阶段：获取内容互动分计算所需的视频数据")
        logger.info(f"   - 数据范围：最近{max_videos}条视频")
        logger.info(f"   - 关键词筛选：{keyword or '无'}")
        
        # 获取分析模式信息
        analysis_info = self.content_analyzer.get_analysis_mode_info()
        logger.info(f"   - 分析模式：{analysis_info['description']}")
        logger.info(f"   - 使用API：{analysis_info['api_used']}")
        logger.info(f"   - 并发数：{analysis_info['concurrent_requests']}")
        logger.info(f"   - 需要下载视频：{'✅ 是' if analysis_info['requires_video_download'] else '❌ 否'}")
        
        # 使用原有的工作方法获取视频
        videos = []
        quality_scores = {}
        total_fetched_videos = 0
        
        try:
            if keyword or project_name:
                # 如果有关键词或项目方名称，使用筛选条件
                filter_terms = []
                if keyword:
                    filter_terms.append(f"关键词 '{keyword}'")
                if project_name:
                    filter_terms.append(f"项目方 '{project_name}'")
                logger.info(f"📡 使用筛选条件 {' | '.join(filter_terms)} 获取匹配视频...")
                
                # 传递关键词和项目方名称到API客户端
                videos, total_fetched_videos = self.api_client.fetch_user_top_videos(user_id, max_videos, keyword, project_name)
                logger.info(f"✅ 获取到 {len(videos)} 个匹配筛选条件的视频（从 {total_fetched_videos} 个视频中筛选）")
                
            else:
                # 没有筛选条件，获取最近的视频但不进行AI评分
                logger.info(f"📡 获取最近 {max_videos} 条视频（无筛选条件）...")
                videos, total_fetched_videos = self.api_client.fetch_user_top_videos(user_id, max_videos)
                logger.info(f"✅ 获取到 {len(videos)} 个视频")
                
        except Exception as e:
            logger.error(f"获取视频数据失败: {e}")
            videos = []
            total_fetched_videos = 0
        
        # 单独处理内容分析，避免分析失败影响视频数据
        if videos and (keyword or project_name):
            try:
                logger.info(f"🤖 开始对 {len(videos)} 个匹配视频进行内容分析...")
                # 传递关键词和项目方名称到内容分析器
                quality_scores = self.content_analyzer.analyze_videos_batch(videos, keyword, project_name)
                logger.info(f"✅ 内容分析完成: {len(quality_scores)} 个视频")
            except Exception as e:
                logger.error(f"内容分析失败: {e}")
                logger.info("⚠️  内容分析失败，但视频基础数据仍可用于内容互动评分")
                quality_scores = {}
        
        # 统计信息
        logger.info(f"✅ 内容互动分数据获取完成：")
        logger.info(f"   - 总视频数：{len(videos)}")
        logger.info(f"   - AI评分视频数：{len(quality_scores)}")
        if quality_scores:
            avg_score = sum(score.total_score for score in quality_scores.values()) / len(quality_scores)
            logger.info(f"   - 平均AI评分：{avg_score:.1f}")
        else:
            logger.info(f"   - 平均AI评分：无")
        
        return videos, quality_scores, total_fetched_videos
