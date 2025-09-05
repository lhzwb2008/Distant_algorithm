#!/usr/bin/env python3
"""
Google Gemini API客户端
用于视频内容分析和质量评分
"""

import logging
import tempfile
import os
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class VideoAnalysisResult:
    """视频分析结果"""
    video_id: str
    content_summary: str
    keyword_relevance: float  # 0-60分
    originality_score: float  # 0-20分  
    clarity_score: float      # 0-10分
    spam_score: float         # 0-5分
    promotion_score: float    # 0-5分
    total_score: float        # 总分
    reasoning: Dict[str, str] # 评分理由

class GoogleGeminiClient:
    """Google Gemini API客户端"""
    
    def __init__(self):
        """初始化客户端"""
        self.api_key = Config.GOOGLE_API_KEY
        self.model = Config.GOOGLE_MODEL
        self.timeout = Config.GOOGLE_REQUEST_TIMEOUT
        
        if not self.api_key:
            logger.warning("Google API Key未配置，视频分析功能将不可用")
            
        # 设置API端点
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def download_video(self, video_url: str, video_id: str) -> Optional[str]:
        """
        下载视频文件到临时目录
        
        Args:
            video_url: 视频下载URL
            video_id: 视频ID
            
        Returns:
            临时文件路径，失败返回None
        """
        try:
            logger.info(f"开始下载视频 {video_id}...")
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"video_{video_id}.mp4")
            
            # 下载视频
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # 写入临时文件
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(temp_file_path) / (1024 * 1024)  # MB
            logger.info(f"视频 {video_id} 下载完成，文件大小: {file_size:.2f}MB")
            
            return temp_file_path
            
        except Exception as e:
            logger.error(f"下载视频 {video_id} 失败: {e}")
            return None
    
    def upload_video_to_gemini(self, video_path: str) -> Optional[str]:
        """
        上传视频到Gemini Files API
        
        Args:
            video_path: 本地视频文件路径
            
        Returns:
            文件URI，失败返回None
        """
        try:
            logger.info("上传视频到Gemini Files API...")
            
            # 上传文件
            upload_url = f"{self.base_url}/files"
            
            with open(video_path, 'rb') as video_file:
                files = {
                    'file': ('video.mp4', video_file, 'video/mp4')
                }
                
                headers = {
                    'X-Goog-Api-Key': self.api_key
                }
                
                response = requests.post(
                    upload_url,
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                file_uri = result.get('uri')
                
                if file_uri:
                    logger.info(f"视频上传成功，URI: {file_uri}")
                    return file_uri
                else:
                    logger.error("上传响应中未找到文件URI")
                    return None
                    
        except Exception as e:
            logger.error(f"上传视频到Gemini失败: {e}")
            return None
    
    def analyze_video_content(self, file_uri: str, video_description: str = "") -> Optional[VideoAnalysisResult]:
        """
        使用Gemini分析视频内容并评分
        
        Args:
            file_uri: Gemini文件URI
            video_description: 视频描述（可选）
            
        Returns:
            视频分析结果
        """
        try:
            logger.info("开始使用Gemini分析视频内容...")
            
            # 构建评分提示词
            prompt = self._build_analysis_prompt(video_description)
            
            # 调用Gemini API
            generate_url = f"{self.base_url}/models/{self.model.replace('models/', '')}:generateContent"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "fileData": {
                                    "fileUri": file_uri
                                }
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key
            }
            
            response = requests.post(
                generate_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析响应
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return self._parse_analysis_result(content, "unknown")
            else:
                logger.error("Gemini响应中未找到分析结果")
                return None
                
        except Exception as e:
            logger.error(f"Gemini视频分析失败: {e}")
            return None
    
    def _build_analysis_prompt(self, video_description: str = "") -> str:
        """构建视频分析提示词"""
        prompt = f"""
请分析这个视频的内容，并根据以下标准进行评分：

视频描述：{video_description if video_description else "无"}

评分标准：
1. 关键词相关性 (0-60分)：评估视频内容与描述的匹配度和主题一致性
2. 内容原创性 (0-20分)：评估内容的原创程度和独特性
3. 表达清晰度 (0-10分)：评估视频的表达是否清晰、逻辑是否合理
4. 垃圾信息识别 (0-5分)：检测是否存在垃圾信息、重复内容或低质量内容
5. 推广内容识别 (0-5分)：检测是否为纯推广内容或包含过多营销信息

请以JSON格式返回评分结果：
{{
    "content_summary": "视频内容的简要总结",
    "keyword_relevance": 分数,
    "originality_score": 分数,
    "clarity_score": 分数,
    "spam_score": 分数,
    "promotion_score": 分数,
    "total_score": 总分,
    "reasoning": {{
        "keyword_reasoning": "关键词相关性评分理由",
        "originality_reasoning": "原创性评分理由",
        "clarity_reasoning": "清晰度评分理由",
        "spam_reasoning": "垃圾信息评分理由",
        "promotion_reasoning": "推广内容评分理由"
    }}
}}

请确保返回有效的JSON格式。
"""
        return prompt
    
    def _parse_analysis_result(self, content: str, video_id: str) -> Optional[VideoAnalysisResult]:
        """解析Gemini分析结果"""
        try:
            import json
            import re
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("无法从Gemini响应中提取JSON")
                return None
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            return VideoAnalysisResult(
                video_id=video_id,
                content_summary=data.get('content_summary', ''),
                keyword_relevance=float(data.get('keyword_relevance', 0)),
                originality_score=float(data.get('originality_score', 0)),
                clarity_score=float(data.get('clarity_score', 0)),
                spam_score=float(data.get('spam_score', 0)),
                promotion_score=float(data.get('promotion_score', 0)),
                total_score=float(data.get('total_score', 0)),
                reasoning=data.get('reasoning', {})
            )
            
        except Exception as e:
            logger.error(f"解析Gemini分析结果失败: {e}")
            return None
    
    def cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"已清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def analyze_video_from_url(self, video_url: str, video_id: str, video_description: str = "") -> Optional[VideoAnalysisResult]:
        """
        从视频URL完整分析视频内容
        
        Args:
            video_url: 视频下载URL
            video_id: 视频ID
            video_description: 视频描述
            
        Returns:
            视频分析结果
        """
        temp_file_path = None
        
        try:
            # 1. 下载视频
            temp_file_path = self.download_video(video_url, video_id)
            if not temp_file_path:
                return None
            
            # 2. 检查文件大小（Gemini限制20MB内联数据）
            file_size = os.path.getsize(temp_file_path)
            
            if file_size > 20 * 1024 * 1024:  # 20MB
                # 大文件：使用Files API
                file_uri = self.upload_video_to_gemini(temp_file_path)
                if not file_uri:
                    return None
                result = self.analyze_video_content(file_uri, video_description)
            else:
                # 小文件：直接内联处理
                result = self._analyze_video_inline(temp_file_path, video_id, video_description)
            
            return result
            
        finally:
            # 清理临时文件
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def _analyze_video_inline(self, video_path: str, video_id: str, video_description: str) -> Optional[VideoAnalysisResult]:
        """内联分析小视频文件"""
        try:
            logger.info(f"使用内联方式分析视频 {video_id}...")
            
            # 检查API密钥
            if not self.api_key:
                logger.error("Google API Key未配置，无法进行视频分析")
                return None
            
            # 读取视频数据
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            # Base64编码
            import base64
            video_b64 = base64.b64encode(video_data).decode('utf-8')
            
            prompt = self._build_analysis_prompt(video_description)
            
            generate_url = f"{self.base_url}/models/{self.model.replace('models/', '')}:generateContent"
            logger.info(f"🔗 调用Gemini API: {generate_url}")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "video/mp4",
                                    "data": video_b64
                                }
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key
            }
            
            logger.info(f"📤 发送请求到Gemini API...")
            response = requests.post(
                generate_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"📥 收到响应，状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Gemini API错误: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"✅ Gemini分析完成，响应长度: {len(content)} 字符")
                return self._parse_analysis_result(content, video_id)
            else:
                logger.error(f"Gemini响应格式异常: {result}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Gemini API连接错误: {e}")
            logger.info("💡 可能的解决方案:")
            logger.info("   1. 检查网络连接")
            logger.info("   2. 检查Google API Key是否有效")
            logger.info("   3. 检查是否需要VPN访问Google服务")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Gemini API超时: {e}")
            return None
        except Exception as e:
            logger.error(f"内联视频分析失败: {e}")
            return None
