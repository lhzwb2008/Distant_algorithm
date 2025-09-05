#!/usr/bin/env python3
"""
OpenAI Whisper API客户端 - 用于视频音频转文本
"""

import os
import io
import logging
import tempfile
import subprocess
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class AudioTranscription:
    """音频转文本结果"""
    video_id: str
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    source: str = "whisper_api"
    raw_response: Optional[Dict[str, Any]] = None

class OpenAIWhisperClient:
    """OpenAI Whisper API客户端"""
    
    def __init__(self, api_key: str):
        """初始化Whisper客户端
        
        Args:
            api_key: OpenAI API密钥
        """
        self.client = OpenAI(api_key=api_key)
        self.max_file_size = 25 * 1024 * 1024  # 25MB限制
        logger.info("OpenAI Whisper客户端初始化完成")
    
    def transcribe_video_from_url(self, video_id: str, video_url: str) -> Optional[AudioTranscription]:
        """从视频URL提取音频并转录为文本
        
        Args:
            video_id: 视频ID
            video_url: 视频下载URL
            
        Returns:
            音频转录结果，失败时返回None
        """
        try:
            logger.info(f"开始为视频 {video_id} 提取音频并转录")
            
            # 1. 从URL流式提取音频
            audio_data = self._extract_audio_from_url(video_url)
            if not audio_data:
                logger.warning(f"视频 {video_id} 音频提取失败")
                return None
            
            # 2. 检查文件大小
            if len(audio_data) > self.max_file_size:
                logger.warning(f"视频 {video_id} 音频文件过大 ({len(audio_data)/1024/1024:.1f}MB > 25MB)")
                # 尝试压缩音频
                audio_data = self._compress_audio(audio_data)
                if not audio_data or len(audio_data) > self.max_file_size:
                    logger.error(f"视频 {video_id} 音频压缩后仍然过大，跳过")
                    return None
            
            # 3. 调用OpenAI Whisper API
            transcription = self._transcribe_audio(video_id, audio_data)
            
            if transcription:
                logger.info(f"视频 {video_id} 转录成功，文本长度: {len(transcription.text)} 字符")
                return transcription
            else:
                logger.warning(f"视频 {video_id} 转录失败")
                return None
                
        except Exception as e:
            logger.error(f"视频 {video_id} 音频转录过程中发生错误: {e}")
            return None
    
    def _extract_audio_from_url(self, video_url: str) -> Optional[bytes]:
        """从视频URL流式提取音频
        
        Args:
            video_url: 视频URL
            
        Returns:
            音频数据（bytes），失败时返回None
        """
        try:
            # 使用ffmpeg从URL直接提取音频到内存
            cmd = [
                'ffmpeg',
                '-i', video_url,           # 输入视频URL
                '-vn',                     # 不处理视频流
                '-acodec', 'libmp3lame',   # 使用MP3编码
                '-ar', '16000',            # 采样率16kHz（Whisper推荐）
                '-ac', '1',                # 单声道
                '-ab', '64k',              # 比特率64kbps（压缩音频）
                '-f', 'mp3',               # 输出格式MP3
                'pipe:1'                   # 输出到stdout
            ]
            
            logger.debug(f"执行ffmpeg命令: {' '.join(cmd)}")
            
            # 执行ffmpeg命令
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,  # 60秒超时
                check=False
            )
            
            if process.returncode == 0:
                audio_data = process.stdout
                logger.debug(f"音频提取成功，大小: {len(audio_data)/1024:.1f}KB")
                return audio_data
            else:
                error_msg = process.stderr.decode('utf-8', errors='ignore')
                logger.error(f"ffmpeg音频提取失败: {error_msg}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg音频提取超时")
            return None
        except FileNotFoundError:
            logger.error("ffmpeg未安装，无法提取音频")
            return None
        except Exception as e:
            logger.error(f"音频提取过程中发生错误: {e}")
            return None
    
    def _compress_audio(self, audio_data: bytes) -> Optional[bytes]:
        """压缩音频数据
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            压缩后的音频数据，失败时返回None
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3') as temp_input:
                with tempfile.NamedTemporaryFile(suffix='.mp3') as temp_output:
                    # 写入原始音频数据
                    temp_input.write(audio_data)
                    temp_input.flush()
                    
                    # 使用ffmpeg进一步压缩
                    cmd = [
                        'ffmpeg',
                        '-i', temp_input.name,
                        '-acodec', 'libmp3lame',
                        '-ar', '8000',      # 降低采样率到8kHz
                        '-ac', '1',         # 单声道
                        '-ab', '32k',       # 降低比特率到32kbps
                        '-f', 'mp3',
                        temp_output.name,
                        '-y'                # 覆盖输出文件
                    ]
                    
                    process = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=30,
                        check=False
                    )
                    
                    if process.returncode == 0:
                        # 读取压缩后的数据
                        temp_output.seek(0)
                        compressed_data = temp_output.read()
                        logger.debug(f"音频压缩成功: {len(audio_data)/1024:.1f}KB -> {len(compressed_data)/1024:.1f}KB")
                        return compressed_data
                    else:
                        logger.error(f"音频压缩失败: {process.stderr.decode('utf-8', errors='ignore')}")
                        return None
                        
        except Exception as e:
            logger.error(f"音频压缩过程中发生错误: {e}")
            return None
    
    def _transcribe_audio(self, video_id: str, audio_data: bytes) -> Optional[AudioTranscription]:
        """使用OpenAI Whisper API转录音频
        
        Args:
            video_id: 视频ID
            audio_data: 音频数据
            
        Returns:
            转录结果，失败时返回None
        """
        try:
            # 创建内存中的音频文件
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"{video_id}.mp3"  # 设置文件名，API需要
            
            logger.debug(f"调用OpenAI Whisper API转录音频，大小: {len(audio_data)/1024:.1f}KB")
            
            # 调用OpenAI Whisper API
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",  # 获取详细信息
                language=None  # 自动检测语言
            )
            
            # 解析响应
            if response and response.text:
                transcription = AudioTranscription(
                    video_id=video_id,
                    text=response.text.strip(),
                    language=getattr(response, 'language', None),
                    duration=getattr(response, 'duration', None),
                    source="whisper_api",
                    raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
                )
                
                logger.info(f"Whisper转录成功: {len(transcription.text)} 字符, 语言: {transcription.language}")
                return transcription
            else:
                logger.warning("Whisper API返回空结果")
                return None
                
        except Exception as e:
            logger.error(f"Whisper API调用失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """检查服务是否可用
        
        Returns:
            True如果服务可用，False否则
        """
        try:
            # 检查ffmpeg是否可用
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            
            # 简单测试OpenAI API连接
            # 这里可以添加更多检查逻辑
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg不可用，音频转录功能将无法使用")
            return False
        except Exception as e:
            logger.error(f"服务可用性检查失败: {e}")
            return False

def test_whisper_client():
    """测试Whisper客户端功能"""
    # 这里可以添加测试代码
    pass

if __name__ == "__main__":
    # 测试代码
    test_whisper_client()
