#!/usr/bin/env python3
"""
调试Gemini API响应解析问题
"""

import logging
import sys
import os

# 添加当前目录到Python路径
sys.path.append('.')

from google_gemini_client import GoogleGeminiClient
from video_content_analyzer import VideoContentAnalyzer
from api_client import TiKhubAPIClient
from models import VideoDetail

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_video_analysis():
    """调试视频分析过程"""
    
    # 测试视频ID（从日志中获取）
    test_video_id = "7535704364065770774"
    
    logger.info(f"开始调试视频 {test_video_id}")
    
    # 初始化客户端
    analyzer = VideoContentAnalyzer()
    api_client = TiKhubAPIClient()
    
    # 获取视频信息
    try:
        response = api_client._make_request(
            endpoint="/api/v1/tiktok/app/v3/fetch_one_video",
            params={"aweme_id": test_video_id}
        )
        
        if not response or 'aweme_detail' not in response:
            logger.error("无法获取视频信息")
            return
            
        aweme_detail = response['aweme_detail']
        
        # 创建VideoDetail对象
        from datetime import datetime
        video = VideoDetail(
            video_id=test_video_id,
            desc=aweme_detail.get('desc', ''),
            create_time=datetime.fromtimestamp(aweme_detail.get('create_time', 0)),
            author_id=aweme_detail.get('author', {}).get('unique_id', ''),
            view_count=aweme_detail.get('statistics', {}).get('play_count', 0),
            like_count=aweme_detail.get('statistics', {}).get('digg_count', 0),
            comment_count=aweme_detail.get('statistics', {}).get('comment_count', 0),
            share_count=aweme_detail.get('statistics', {}).get('share_count', 0),
            download_count=aweme_detail.get('statistics', {}).get('download_count', 0),
            collect_count=aweme_detail.get('statistics', {}).get('collect_count', 0),
            duration=aweme_detail.get('duration', 0)
        )
        
        logger.info(f"视频信息: {video.desc[:100]}...")
        
        # 分析视频
        result = analyzer._analyze_single_video_with_gemini(video, keyword="test", project_name="test")
        
        if result:
            logger.info(f"分析结果:")
            logger.info(f"  - keyword_score: {result.keyword_score}")
            logger.info(f"  - originality_score: {result.originality_score}")
            logger.info(f"  - clarity_score: {result.clarity_score}")
            logger.info(f"  - spam_score: {result.spam_score}")
            logger.info(f"  - promotion_score: {result.promotion_score}")
            logger.info(f"  - total_score: {result.total_score} (类型: {type(result.total_score)})")
            logger.info(f"  - reasoning: {result.reasoning}")
            
            # 检查total_score的值
            if isinstance(result.total_score, str):
                logger.error(f"❌ total_score是字符串而不是数字: '{result.total_score}'")
            elif "📹" in str(result.total_score):
                logger.error(f"❌ total_score包含异常字符: '{result.total_score}'")
        else:
            logger.error("分析失败")
            
    except Exception as e:
        logger.error(f"调试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_video_analysis()