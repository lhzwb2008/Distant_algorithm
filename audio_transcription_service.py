#!/usr/bin/env python3
"""
音频转文本服务 - 集成OpenAI Whisper API和TikHub API
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import Config
from api_client import TiKhubAPIClient
from openai_whisper_client import OpenAIWhisperClient, AudioTranscription
from models import VideoSubtitle

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """转录结果"""
    video_id: str
    success: bool
    subtitle: Optional[VideoSubtitle] = None
    error_message: Optional[str] = None
    source: str = "unknown"  # "original_subtitle", "whisper_api", "failed"

class AudioTranscriptionService:
    """音频转文本服务"""
    
    def __init__(self, api_client: TiKhubAPIClient, openai_api_key: Optional[str] = None):
        """初始化音频转文本服务
        
        Args:
            api_client: TikHub API客户端
            openai_api_key: OpenAI API密钥，如果不提供则从配置中获取
        """
        self.api_client = api_client
        
        # 初始化OpenAI Whisper客户端
        api_key = openai_api_key or Config.OPENAI_API_KEY
        if api_key:
            try:
                self.whisper_client = OpenAIWhisperClient(api_key)
                self.whisper_available = self.whisper_client.is_available()
                if self.whisper_available:
                    logger.info("OpenAI Whisper服务初始化成功")
                else:
                    logger.warning("OpenAI Whisper服务不可用（缺少ffmpeg）")
            except Exception as e:
                logger.error(f"OpenAI Whisper服务初始化失败: {e}")
                self.whisper_client = None
                self.whisper_available = False
        else:
            logger.warning("未配置OpenAI API密钥，Whisper功能不可用")
            self.whisper_client = None
            self.whisper_available = False
    
    def extract_subtitle_with_fallback(self, video_id: str) -> TranscriptionResult:
        """提取视频字幕，支持原生字幕和音频转文本双重回退
        
        Args:
            video_id: 视频ID
            
        Returns:
            转录结果
        """
        try:
            # 步骤1: 尝试获取原生字幕
            logger.info(f"为视频 {video_id} 尝试提取原生字幕")
            original_subtitle = self.api_client.extract_subtitle_text(video_id)
            
            if original_subtitle and original_subtitle.full_text:
                logger.info(f"视频 {video_id} 原生字幕提取成功")
                return TranscriptionResult(
                    video_id=video_id,
                    success=True,
                    subtitle=original_subtitle,
                    source="original_subtitle"
                )
            
            # 步骤2: 如果原生字幕失败，尝试音频转文本
            if self.whisper_available and self.whisper_client:
                logger.info(f"视频 {video_id} 原生字幕不可用，尝试音频转文本")
                return self._transcribe_audio_fallback(video_id)
            else:
                logger.warning(f"视频 {video_id} 原生字幕不可用，且音频转文本服务不可用")
                return TranscriptionResult(
                    video_id=video_id,
                    success=False,
                    error_message="原生字幕不可用，且音频转文本服务不可用",
                    source="failed"
                )
                
        except Exception as e:
            logger.error(f"视频 {video_id} 字幕提取过程中发生错误: {e}")
            return TranscriptionResult(
                video_id=video_id,
                success=False,
                error_message=str(e),
                source="failed"
            )
    
    def _transcribe_audio_fallback(self, video_id: str) -> TranscriptionResult:
        """音频转文本回退方案
        
        Args:
            video_id: 视频ID
            
        Returns:
            转录结果
        """
        try:
            # 获取视频下载链接
            download_url = self.api_client.get_video_download_url(video_id)
            if not download_url:
                return TranscriptionResult(
                    video_id=video_id,
                    success=False,
                    error_message="无法获取视频下载链接",
                    source="failed"
                )
            
            # 使用Whisper进行音频转文本
            transcription = self.whisper_client.transcribe_video_from_url(video_id, download_url)
            
            if transcription and transcription.text:
                # 将AudioTranscription转换为VideoSubtitle格式
                subtitle = VideoSubtitle(
                    video_id=video_id,
                    caption_format="whisper_transcription",
                    caption_length=len(transcription.text),
                    language=transcription.language or "unknown",
                    language_code=transcription.language or "unknown", 
                    is_auto_generated=True,
                    subtitle_urls=[],  # 音频转文本没有URL
                    full_text=transcription.text,
                    subtitle_count=1,
                    raw_caption_info=transcription.raw_response
                )
                
                logger.info(f"视频 {video_id} 音频转文本成功，文本长度: {len(transcription.text)} 字符")
                return TranscriptionResult(
                    video_id=video_id,
                    success=True,
                    subtitle=subtitle,
                    source="whisper_api"
                )
            else:
                return TranscriptionResult(
                    video_id=video_id,
                    success=False,
                    error_message="音频转文本失败",
                    source="failed"
                )
                
        except Exception as e:
            logger.error(f"视频 {video_id} 音频转文本回退过程中发生错误: {e}")
            return TranscriptionResult(
                video_id=video_id,
                success=False,
                error_message=str(e),
                source="failed"
            )
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态
        
        Returns:
            服务状态信息
        """
        return {
            "original_subtitle_available": True,  # 原生字幕总是可用的
            "whisper_api_available": self.whisper_available,
            "openai_api_key_configured": bool(Config.OPENAI_API_KEY),
            "ffmpeg_available": self.whisper_client.is_available() if self.whisper_client else False
        }

def test_transcription_service():
    """测试转录服务"""
    from api_client import TiKhubAPIClient
    
    # 创建服务实例
    api_client = TiKhubAPIClient()
    service = AudioTranscriptionService(api_client)
    
    # 显示服务状态
    status = service.get_service_status()
    print("🔧 音频转文本服务状态:")
    for key, value in status.items():
        print(f"   {key}: {'✅' if value else '❌'} {value}")
    
    # 这里可以添加更多测试代码

if __name__ == "__main__":
    test_transcription_service()
