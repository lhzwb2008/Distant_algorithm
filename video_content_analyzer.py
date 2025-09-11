#!/usr/bin/env python3
"""
视频内容分析器
支持字幕提取和Google Gemini视频分析两种模式
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
from config import Config
from models import VideoDetail
from openrouter_client import OpenRouterClient, QualityScore
from google_gemini_client import GoogleGeminiClient, VideoAnalysisResult
from api_client import TiKhubAPIClient

logger = logging.getLogger(__name__)

class VideoContentAnalyzer:
    """视频内容分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 根据配置决定初始化哪些客户端
        if Config.ENABLE_SUBTITLE_EXTRACTION:
            self.openrouter_client = OpenRouterClient()
            self.google_client = None
        else:
            self.openrouter_client = None
            self.google_client = GoogleGeminiClient()
        
        self.api_client = TiKhubAPIClient()
        
    def analyze_videos_batch(self, videos: List[VideoDetail], keyword: str = None, project_name: str = None) -> Dict[str, QualityScore]:
        """
        批量分析视频内容（支持字幕和视频分析两种模式）
        
        Args:
            videos: 视频详情列表
            keyword: 关键词，用于AI评分时的匹配检查
            project_name: 项目方名称，用于AI评分时的匹配检查
            
        Returns:
            视频ID到QualityScore的映射字典
        """
        if not videos:
            return {}
            
        total_videos = len(videos)
        
        if Config.ENABLE_SUBTITLE_EXTRACTION:
            # 模式1：使用字幕提取 + OpenRouter
            return self._analyze_with_subtitles(videos)
        else:
            # 模式2：使用Google Gemini视频分析
            return self._analyze_with_gemini(videos, keyword, project_name)
    
    def _analyze_with_subtitles(self, videos: List[VideoDetail]) -> Dict[str, QualityScore]:
        """使用字幕提取模式分析视频"""
        if not self.openrouter_client:
            logger.error("OpenRouter客户端未初始化，无法使用字幕提取模式")
            return {}
            
        total_videos = len(videos)
        concurrent_requests = min(Config.OPENROUTER_CONCURRENT_REQUESTS, total_videos)
        
        logger.info(f"🎬 使用字幕提取模式分析，共 {total_videos} 个视频，并发数: {concurrent_requests}")
        
        results = {}
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            future_to_video = {
                executor.submit(self._analyze_single_video_with_subtitle, video): video 
                for video in videos
            }
            
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                completed_count += 1
                
                try:
                    quality_score = future.result()
                    if quality_score:
                        results[video.video_id] = quality_score
                        logger.info(f"✅ 视频 {video.video_id} 字幕分析完成 ({completed_count}/{total_videos}) - 总分: {quality_score.total_score:.1f}")
                    else:
                        logger.warning(f"❌ 视频 {video.video_id} 字幕分析失败 ({completed_count}/{total_videos})")
                        
                except Exception as e:
                    logger.error(f"💥 视频 {video.video_id} 字幕分析异常 ({completed_count}/{total_videos}): {e}")
        
        success_rate = len(results) / total_videos * 100 if total_videos > 0 else 0
        logger.info(f"🎯 字幕分析完成！成功: {len(results)}/{total_videos} ({success_rate:.1f}%)")
        
        return results
    
    def _analyze_with_gemini(self, videos: List[VideoDetail], keyword: str = None, project_name: str = None) -> Dict[str, QualityScore]:
        """使用Google Gemini视频分析模式"""
        if not self.google_client:
            logger.error("Google Gemini客户端未初始化，无法使用视频分析模式")
            return {}
            
        total_videos = len(videos)
        # 使用 Google API 并发限制，避免500错误
        concurrent_requests = min(Config.GOOGLE_CONCURRENT_REQUESTS, total_videos)
        
        logger.info(f"🤖 使用Google Gemini视频分析模式，共 {total_videos} 个视频，并发数: {concurrent_requests} (限制Gemini API并发)")
        
        results = {}
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            future_to_video = {
                executor.submit(self._analyze_single_video_with_gemini, video, keyword, project_name): video 
                for video in videos
            }
            
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                completed_count += 1
                
                try:
                    quality_score = future.result()
                    if quality_score:
                        results[video.video_id] = quality_score
                        logger.info(f"✅ 视频 {video.video_id} Gemini分析完成 ({completed_count}/{total_videos}) - 总分: {quality_score.total_score:.1f}")
                    else:
                        logger.warning(f"❌ 视频 {video.video_id} Gemini分析失败 ({completed_count}/{total_videos})")
                        
                except Exception as e:
                    logger.error(f"💥 视频 {video.video_id} Gemini分析异常 ({completed_count}/{total_videos}): {e}")
        
        success_rate = len(results) / total_videos * 100 if total_videos > 0 else 0
        logger.info(f"🎯 Gemini分析完成！成功: {len(results)}/{total_videos} ({success_rate:.1f}%)")
        
        return results
    
    def _analyze_single_video_with_subtitle(self, video: VideoDetail) -> Optional[QualityScore]:
        """使用字幕分析单个视频"""
        if not video.subtitle or not video.subtitle.full_text:
            logger.warning(f"视频 {video.video_id} 没有字幕，无法进行质量评分")
            return None
        
        try:
            quality_score = self.openrouter_client.evaluate_video_quality(
                subtitle_text=video.subtitle.full_text,
                video_description=video.desc
            )
            return quality_score
            
        except Exception as e:
            logger.error(f"视频 {video.video_id} 字幕质量评分失败: {e}")
            return None
    
    def _analyze_single_video_with_gemini(self, video: VideoDetail, keyword: str = None, project_name: str = None) -> Optional[QualityScore]:
        """使用Google Gemini分析单个视频"""
        try:
            # 添加延迟以避免Gemini API并发压力 (降低到2次/秒 = 0.5秒间隔)
            time.sleep(0.5)
            
            # 获取视频下载URL
            video_url = self._get_video_download_url(video.video_id)
            if not video_url:
                logger.error(f"无法获取视频 {video.video_id} 的下载URL")
                return None
            
            # 使用Gemini分析视频（不传入desc字段，完全基于视频内容）
            analysis_result = self.google_client.analyze_video_from_url(
                video_url=video_url,
                video_id=video.video_id,
                keyword=keyword,
                project_name=project_name
            )
            
            if not analysis_result:
                return None
            
            # 转换为QualityScore格式
            quality_score = self._convert_gemini_result_to_quality_score(analysis_result)
            return quality_score
            
        except Exception as e:
            logger.error(f"视频 {video.video_id} Gemini分析失败: {e}")
            return None
    
    def _get_video_download_url(self, video_id: str) -> Optional[str]:
        """获取视频下载URL，优先选择 lowest_540_1 清晰度"""
        try:
            # 调用fetch_one_video API获取下载URL
            params = {'aweme_id': video_id}
            data = self.api_client._make_request(Config.VIDEO_DETAIL_ENDPOINT, params)
            
            # 添加调试信息
            logger.info(f"🔍 视频 {video_id} API响应键: {list(data.keys()) if data else 'None'}")
            
            if not data:
                logger.error(f"获取视频 {video_id} 详情失败：API响应为空")
                return None
            
            # 检查不同可能的响应格式
            if 'data' in data:
                video_data = data['data']
            elif 'aweme_detail' in data:
                video_data = {'aweme_detail': data['aweme_detail']}
            else:
                logger.error(f"获取视频 {video_id} 详情失败：未找到预期的数据结构，可用键: {list(data.keys())}")
                return None
            
            aweme_detail = video_data.get('aweme_detail', {})
            video_info = aweme_detail.get('video', {})
            
            # 优先尝试从 bit_rate 数组中获取 lowest_540_1 清晰度
            # 直接使用默认play_addr，不再选择特定清晰度
            # 这样可以避免低质量视频导致的Gemini API 500错误
            logger.info(f"📺 视频 {video_id} 使用默认play_addr（不选择特定清晰度）...")
            
            if video_info:
                play_addr_info = video_info.get('play_addr', {})
                url_list = play_addr_info.get('url_list', [])
                if url_list:
                    download_url = url_list[0]
                    logger.info(f"✅ 获取视频 {video_id} 默认play_addr URL成功")
                    return download_url
            
            # 回退到原有逻辑：尝试获取无水印版本
            logger.info(f"⚠️ 视频 {video_id} bit_rate数组不可用，回退到传统方式...")
            download_no_watermark = video_info.get('download_no_watermark_addr', {})
            no_watermark_urls = download_no_watermark.get('url_list', [])
            
            if no_watermark_urls:
                download_url = no_watermark_urls[0]
                logger.info(f"✅ 获取视频 {video_id} 无水印下载URL成功 (传统方式)")
                return download_url
            
            # 如果没有无水印版本，尝试有水印版本
            logger.info(f"⚠️ 视频 {video_id} 无水印版本不可用，尝试有水印版本...")
            download_with_watermark = video_info.get('download_addr', {}) or video_info.get('play_addr', {})
            watermark_urls = download_with_watermark.get('url_list', [])
            
            if watermark_urls:
                download_url = watermark_urls[0]
                logger.info(f"✅ 获取视频 {video_id} 有水印下载URL成功 (传统方式)")
                return download_url
            
            # 都没有找到
            logger.error(f"❌ 视频 {video_id} 没有可用的下载URL")
            logger.info(f"🔍 视频结构调试:")
            logger.info(f"   - aweme_detail存在: {bool(aweme_detail)}")
            logger.info(f"   - video存在: {bool(video_info)}")
            if video_info:
                logger.info(f"   - video对象的键: {list(video_info.keys())}")
                if bit_rate_list:
                    logger.info(f"   - 可用清晰度: {[q.get('gear_name', 'unknown') for q in bit_rate_list if isinstance(q, dict)]}")
            return None
                
        except Exception as e:
            logger.error(f"获取视频 {video_id} 下载URL失败: {e}")
            return None
    
    def _convert_gemini_result_to_quality_score(self, result: VideoAnalysisResult) -> QualityScore:
        """将Gemini分析结果转换为QualityScore格式"""
        return QualityScore(
            keyword_score=result.keyword_relevance,
            originality_score=result.originality_score,
            clarity_score=result.clarity_score,
            spam_score=result.spam_score,
            promotion_score=result.promotion_score,
            total_score=result.total_score,
            reasoning=result.reasoning
        )
    
    def get_analysis_mode_info(self) -> Dict[str, Any]:
        """获取当前分析模式信息"""
        if Config.ENABLE_SUBTITLE_EXTRACTION:
            return {
                'mode': 'subtitle_extraction',
                'description': '字幕提取 + OpenRouter AI评分',
                'api_used': 'OpenRouter',
                'concurrent_requests': Config.OPENROUTER_CONCURRENT_REQUESTS,
                'requires_subtitle': True,
                'requires_video_download': False
            }
        else:
            return {
                'mode': 'video_analysis',
                'description': 'Google Gemini视频内容分析',
                'api_used': 'Google Gemini + TikHub',
                'concurrent_requests': Config.TIKHUB_CONCURRENT_REQUESTS,
                'requires_subtitle': False,
                'requires_video_download': True,
                'note': 'Gemini分析受TikHub API限流影响 (10次/秒)'
            }
