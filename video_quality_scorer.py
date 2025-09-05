#!/usr/bin/env python3
"""
视频质量评分器
基于字幕内容使用AI模型进行质量评分
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any
from openrouter_client import OpenRouterClient, QualityScore
from models import VideoDetail
from config import Config

logger = logging.getLogger(__name__)

class VideoQualityScorer:
    """视频质量评分器"""
    
    def __init__(self, openrouter_api_key: str = None, model: str = None):
        """
        初始化质量评分器
        
        Args:
            openrouter_api_key: OpenRouter API密钥，如果不提供则从配置文件读取
            model: 使用的模型，如果不提供则从配置文件读取
        """
        # 只有在启用字幕提取时才初始化 OpenRouter 客户端
        if Config.ENABLE_SUBTITLE_EXTRACTION:
            self.openrouter_client = OpenRouterClient(api_key=openrouter_api_key, model=model)
        else:
            self.openrouter_client = None
        
    def score_video_quality(self, video: VideoDetail) -> Optional[QualityScore]:
        """
        为单个视频进行质量评分
        
        Args:
            video: 视频详情对象
            
        Returns:
            QualityScore对象或None（如果评分失败）
        """
        # 检查字幕提取开关是否启用
        if not Config.ENABLE_SUBTITLE_EXTRACTION or not self.openrouter_client:
            logger.info(f"字幕提取开关已关闭，跳过视频 {video.video_id} 的AI质量评分")
            return None
            
        if not video.subtitle or not video.subtitle.full_text:
            logger.warning(f"视频 {video.video_id} 没有字幕，无法进行质量评分")
            return None
        
        try:
            logger.info(f"开始为视频 {video.video_id} 进行质量评分...")
            
            # 使用OpenRouter进行质量评分
            quality_score = self.openrouter_client.evaluate_video_quality(
                subtitle_text=video.subtitle.full_text,
                video_description=video.desc
            )
            
            logger.info(f"视频 {video.video_id} 质量评分完成:")
            logger.info(f"  📊 总分: {quality_score.total_score:.1f}/100")
            logger.info(f"  🎯 关键词: {quality_score.keyword_score:.1f}/60")
            logger.info(f"  ✨ 原创性: {quality_score.originality_score:.1f}/20")
            logger.info(f"  💬 清晰度: {quality_score.clarity_score:.1f}/10")
            logger.info(f"  🚫 垃圾信息: {quality_score.spam_score:.1f}/5")
            logger.info(f"  📢 推广识别: {quality_score.promotion_score:.1f}/5")
            logger.info(f"  💡 评分理由: {quality_score.reasoning}")
            
            return quality_score
            
        except Exception as e:
            logger.error(f"视频 {video.video_id} 质量评分失败: {e}")
            return None
    
    def score_videos_batch(self, videos: list[VideoDetail]) -> Dict[str, QualityScore]:
        """
        批量为视频进行质量评分（并行处理）
        
        Args:
            videos: 视频详情列表
            
        Returns:
            视频ID到QualityScore的映射字典
        """
        if not videos:
            return {}
            
        total_videos = len(videos)
        concurrent_requests = min(Config.OPENROUTER_CONCURRENT_REQUESTS, total_videos)
        
        logger.info(f"🚀 开始并行批量质量评分，共 {total_videos} 个视频，并发数: {concurrent_requests}")
        
        # 使用线程池进行并行处理
        results = {}
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            # 提交所有任务
            future_to_video = {
                executor.submit(self.score_video_quality, video): video 
                for video in videos
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                completed_count += 1
                
                try:
                    quality_score = future.result()
                    if quality_score:
                        results[video.video_id] = quality_score
                        logger.info(f"✅ 视频 {video.video_id} 评分完成 ({completed_count}/{total_videos}) - 总分: {quality_score.total_score:.1f}")
                    else:
                        logger.warning(f"❌ 视频 {video.video_id} 评分失败 ({completed_count}/{total_videos})")
                        
                except Exception as e:
                    logger.error(f"💥 视频 {video.video_id} 评分异常 ({completed_count}/{total_videos}): {e}")
        
        success_rate = len(results) / total_videos * 100 if total_videos > 0 else 0
        logger.info(f"🎯 并行批量质量评分完成！成功: {len(results)}/{total_videos} ({success_rate:.1f}%)")
        
        # 输出评分统计
        if results:
            scores = [score.total_score for score in results.values()]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            logger.info(f"📈 评分统计:")
            logger.info(f"  平均分: {avg_score:.1f}")
            logger.info(f"  最高分: {max_score:.1f}")
            logger.info(f"  最低分: {min_score:.1f}")
        
        return results
    
    def get_quality_summary(self, quality_scores: Dict[str, QualityScore]) -> Dict[str, Any]:
        """
        获取质量评分汇总统计
        
        Args:
            quality_scores: 视频质量评分字典
            
        Returns:
            汇总统计数据
        """
        if not quality_scores:
            return {}
        
        scores = list(quality_scores.values())
        total_scores = [s.total_score for s in scores]
        keyword_scores = [s.keyword_score for s in scores]
        originality_scores = [s.originality_score for s in scores]
        clarity_scores = [s.clarity_score for s in scores]
        spam_scores = [s.spam_score for s in scores]
        promotion_scores = [s.promotion_score for s in scores]
        
        def calc_stats(score_list):
            return {
                'average': sum(score_list) / len(score_list),
                'max': max(score_list),
                'min': min(score_list)
            }
        
        return {
            'total_videos': len(quality_scores),
            'total_score': calc_stats(total_scores),
            'keyword_score': calc_stats(keyword_scores),
            'originality_score': calc_stats(originality_scores),
            'clarity_score': calc_stats(clarity_scores),
            'spam_score': calc_stats(spam_scores),
            'promotion_score': calc_stats(promotion_scores),
            'quality_distribution': {
                'excellent': len([s for s in total_scores if s >= 80]),  # 优秀
                'good': len([s for s in total_scores if 60 <= s < 80]),  # 良好
                'average': len([s for s in total_scores if 40 <= s < 60]),  # 一般
                'poor': len([s for s in total_scores if s < 40])  # 较差
            }
        }
