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
        max_videos: int = 100
    ) -> tuple[List[VideoDetail], Dict[str, QualityScore]]:
        """
        获取用于内容互动分计算的视频，并对匹配关键词的视频进行AI评分
        
        Args:
            user_id: 用户ID
            keyword: 关键词筛选
            max_videos: 最大视频数量
            
        Returns:
            (视频详情列表, AI质量评分字典)
        """
        logger.info("🎯 第二阶段：获取内容互动分计算所需的视频数据")
        logger.info(f"   - 数据范围：最近{max_videos}条视频")
        logger.info(f"   - 关键词筛选：{keyword or '无'}")
        subtitle_status = "✅ 启用" if Config.ENABLE_SUBTITLE_EXTRACTION else "❌ 关闭"
        logger.info(f"   - 字幕提取：{subtitle_status}")
        ai_status = "✅ 仅对匹配关键词的视频调用" if Config.ENABLE_SUBTITLE_EXTRACTION else "❌ 已禁用（需要自定义内容提取方法）"
        logger.info(f"   - 大模型调用：{ai_status}")
        
        # 使用原有的工作方法获取视频
        videos = []
        quality_scores = {}
        
        try:
            if keyword:
                # 如果有关键词，使用关键词筛选
                logger.info(f"📡 使用关键词 '{keyword}' 获取匹配视频...")
                videos = self.api_client.fetch_user_top_videos(user_id, max_videos, keyword)
                logger.info(f"✅ 获取到 {len(videos)} 个匹配关键词的视频")
                
            else:
                # 没有关键词，获取最近的视频但不进行AI评分
                logger.info(f"📡 获取最近 {max_videos} 条视频（无关键词筛选）...")
                videos = self.api_client.fetch_user_top_videos(user_id, max_videos)
                logger.info(f"✅ 获取到 {len(videos)} 个视频")
                
        except Exception as e:
            logger.error(f"获取视频数据失败: {e}")
            videos = []
        
        # 单独处理AI评分，避免AI评分失败影响视频数据
        if videos and keyword:
            try:
                logger.info(f"🤖 开始对 {len(videos)} 个匹配视频进行AI评分...")
                quality_scores = self.quality_scorer.score_videos_batch(videos)
                logger.info(f"✅ AI评分完成: {len(quality_scores)} 个视频")
            except Exception as e:
                logger.error(f"AI评分失败: {e}")
                logger.info("⚠️  AI评分失败，但视频基础数据仍可用于内容互动评分")
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
        
        return videos, quality_scores
