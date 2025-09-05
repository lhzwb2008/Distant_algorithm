#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Gemini API 本地测试脚本
用于在境外机器上测试视频分析功能
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

from google_gemini_client import GoogleGeminiClient
from api_client import TiKhubAPIClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_gemini_video_analysis():
    """测试Google Gemini视频分析功能"""
    
    # 检查API密钥
    google_api_key = os.getenv('GOOGLE_API_KEY')
    tikhub_api_key = os.getenv('TIKHUB_API_KEY')
    
    if not google_api_key:
        logger.error("❌ GOOGLE_API_KEY 环境变量未设置")
        return False
        
    if not tikhub_api_key:
        logger.error("❌ TIKHUB_API_KEY 环境变量未设置")
        return False
    
    logger.info("✅ API密钥配置检查通过")
    
    # 初始化客户端
    try:
        gemini_client = GoogleGeminiClient()
        tikhub_client = TiKhubAPIClient()
        logger.info("✅ 客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ 客户端初始化失败: {e}")
        return False
    
    # 测试视频ID（使用之前测试过的视频）
    test_video_id = "7322466309764173057"
    logger.info(f"🎬 测试视频ID: {test_video_id}")
    
    try:
        # 1. 获取视频下载链接
        logger.info("📡 正在获取视频下载链接...")
        video_detail = tikhub_client.fetch_video_detail(test_video_id)
        
        if not video_detail:
            logger.error("❌ 获取视频详情失败")
            return False
            
        logger.info(f"✅ 视频详情获取成功")
        logger.info(f"📹 视频描述: {video_detail.desc[:50]}...")
        logger.info(f"📊 播放量: {video_detail.play_count:,}")
        
        # 2. 获取下载URL
        download_urls = []
        if hasattr(video_detail, 'download_no_watermark_addr') and video_detail.download_no_watermark_addr:
            download_urls.extend(video_detail.download_no_watermark_addr)
            logger.info(f"🎯 找到 {len(video_detail.download_no_watermark_addr)} 个无水印下载链接")
        elif hasattr(video_detail, 'download_addr') and video_detail.download_addr:
            download_urls.extend(video_detail.download_addr)
            logger.info(f"🎯 找到 {len(video_detail.download_addr)} 个带水印下载链接")
        elif hasattr(video_detail, 'play_addr') and video_detail.play_addr:
            download_urls.extend(video_detail.play_addr)
            logger.info(f"🎯 找到 {len(video_detail.play_addr)} 个播放链接")
        
        if not download_urls:
            logger.error("❌ 没有找到可用的视频下载链接")
            return False
            
        best_url = download_urls[0]
        logger.info(f"🔗 使用下载链接: {best_url[:80]}...")
        
        # 3. 使用Google Gemini分析视频
        logger.info("🤖 正在使用Google Gemini分析视频...")
        analysis_result = gemini_client.analyze_video_from_url(best_url, test_video_id)
        
        if analysis_result:
            logger.info("✅ Google Gemini视频分析成功!")
            logger.info(f"📝 分析结果: {analysis_result[:200]}...")
            
            # 解析评分
            try:
                score = gemini_client._parse_analysis_result(analysis_result)
                logger.info(f"⭐ 内容质量评分: {score}/100")
            except Exception as e:
                logger.warning(f"⚠️ 评分解析失败: {e}")
                
            return True
        else:
            logger.error("❌ Google Gemini视频分析失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 Google Gemini API 测试开始")
    print("=" * 50)
    
    success = test_gemini_video_analysis()
    
    print("=" * 50)
    if success:
        print("✅ 测试完成 - 所有功能正常!")
    else:
        print("❌ 测试失败 - 请检查日志信息")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
