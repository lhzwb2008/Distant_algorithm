#!/usr/bin/env python3
"""
Google Gemini API客户端
用于视频内容分析和质量评分
"""

import logging
import tempfile
import os
import time
import requests
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from config import Config

# 尝试导入Google AI SDK
try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False
    logging.warning("Google AI SDK未安装，将使用REST API方式")

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
        
        # 初始化SDK客户端（如果可用）
        self.genai_client = None
        if HAS_GENAI_SDK and self.api_key:
            try:
                self.genai_client = genai.Client(api_key=self.api_key)
                logger.info(f"✅ Google Gemini SDK客户端初始化完成 - 模型: {self.model}")
            except Exception as e:
                logger.warning(f"SDK初始化失败，将使用REST API: {e}")
                self.genai_client = None
        else:
            logger.info(f"✅ Google Gemini REST客户端初始化完成 - 模型: {self.model}")
        
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
            start_time = time.time()
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            logger.info(f"上传视频到Gemini Files API... (文件大小: {file_size_mb:.2f}MB)")
            
            # 根据文件大小选择上传方式
            # ≤20MB: 内联方式（base64编码）
            # >20MB: Files API（避免请求体过大）
            if file_size_mb > 20:
                return self._upload_large_video(video_path, file_size_mb, start_time)
            else:
                return self._upload_small_video(video_path, file_size_mb, start_time)
                    
        except Exception as e:
            upload_time = time.time() - start_time
            logger.error(f"❌ 上传视频到Gemini失败 (耗时: {upload_time:.2f}秒): {e}")
            return None
    
    def _upload_large_video(self, video_path: str, file_size_mb: float, start_time: float) -> Optional[str]:
        """上传大文件（>20MB）使用Files API - 优先使用SDK方式"""
        logger.info("📤 使用Files API上传大文件...")
        
        # 优先尝试SDK方式
        if self.genai_client:
            try:
                logger.info("📤 使用Google AI SDK上传文件...")
                myfile = self.genai_client.files.upload(file=video_path)
                upload_time = time.time() - start_time
                logger.info(f"✅ SDK上传成功，URI: {myfile.uri}, 总耗时: {upload_time:.2f}秒")
                
                # 等待文件处理完成
                logger.info("⏳ 等待文件处理完成...")
                self._wait_for_file_active(myfile.name)
                
                return myfile.uri
            except Exception as e:
                logger.warning(f"SDK上传失败: {e}，尝试REST API方式")
        
        # 回退到REST API方式
        try:
            # 尝试多种上传方式
            upload_attempts = [
                # 方式1: 使用官方推荐的/upload/files端点
                {
                    'url': f"{self.base_url}/upload/files",
                    'method': 'multipart_with_metadata',
                    'description': '官方/upload/files端点'
                },
                # 方式2: 使用基础/files端点
                {
                    'url': f"{self.base_url}/files",
                    'method': 'multipart_simple',
                    'description': '基础/files端点'
                }
            ]
            
            for attempt in upload_attempts:
                logger.info(f"📤 尝试上传方式: {attempt['description']}")
                
                headers = {
                    'X-Goog-Api-Key': self.api_key,
                }
                
                with open(video_path, 'rb') as video_file:
                    if attempt['method'] == 'multipart_with_metadata':
                        files = {
                            'file': (os.path.basename(video_path), video_file, 'video/mp4')
                        }
                        data = {
                            'displayName': os.path.basename(video_path)
                        }
                        upload_response = requests.post(
                            attempt['url'],
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=self.timeout
                        )
                    else:  # multipart_simple
                        files = {
                            'file': (os.path.basename(video_path), video_file, 'video/mp4')
                        }
                        upload_response = requests.post(
                            attempt['url'],
                            files=files,
                            headers=headers,
                            timeout=self.timeout
                        )
                
                    upload_time = time.time() - start_time
                    logger.info(f"📤 上传请求完成，耗时: {upload_time:.2f}秒")
                    logger.info(f"📋 上传响应状态: {upload_response.status_code}")
                    logger.info(f"📋 上传响应头: {dict(upload_response.headers)}")
                    logger.info(f"📋 上传响应内容: {upload_response.text}")
                    
                    if upload_response.status_code in [200, 201]:
                        # 解析响应获取文件URI
                        try:
                            result = upload_response.json()
                            logger.info(f"📋 完整上传响应: {result}")
                            
                            # 检查多种可能的URI字段
                            file_uri = (result.get('file', {}).get('uri') or 
                                       result.get('uri') or 
                                       result.get('name'))
                            
                            if file_uri:
                                # 如果只是文件名，构建完整URI
                                if not file_uri.startswith('http'):
                                    file_uri = f"https://generativelanguage.googleapis.com/v1beta/files/{file_uri}"
                                
                                logger.info(f"✅ 大文件上传成功，URI: {file_uri}, 总耗时: {upload_time:.2f}秒")
                                return file_uri
                            else:
                                logger.warning(f"❌ {attempt['description']} 响应中未找到文件URI，尝试下一种方式")
                                continue  # 尝试下一种上传方式
                                
                        except json.JSONDecodeError:
                            logger.warning(f"❌ {attempt['description']} 响应不是有效的JSON格式，尝试下一种方式")
                            continue  # 尝试下一种上传方式
                    else:
                        logger.warning(f"❌ {attempt['description']} 上传失败，状态码: {upload_response.status_code}，尝试下一种方式")
                        continue  # 尝试下一种上传方式
            
            # 所有上传方式都失败了
            logger.error("❌ 所有Files API上传方式都失败")
            return self._fallback_to_inline(video_path, file_size_mb, start_time)
                
        except Exception as e:
            upload_time = time.time() - start_time
            logger.error(f"❌ 上传大文件失败 (耗时: {upload_time:.2f}秒): {e}")
            # 降级到内联方式
            return self._fallback_to_inline(video_path, file_size_mb, start_time)
    
    def _fallback_to_inline(self, video_path: str, file_size_mb: float, start_time: float) -> Optional[str]:
        """降级方案：根据文件大小选择合适的处理方式"""
        if file_size_mb > 20:
            # 大文件无法使用内联方式，跳过此视频
            logger.error(f"❌ 文件太大 ({file_size_mb:.2f}MB)，超过内联方式限制(20MB)，且Files API不可用")
            logger.error("📋 建议：检查Google Gemini Files API配置或网络连接")
            upload_time = time.time() - start_time
            logger.error(f"❌ 大文件处理失败 (耗时: {upload_time:.2f}秒)")
            return None
        else:
            # 小文件可以降级到内联方式
            logger.info(f"📤 降级处理：对 {file_size_mb:.2f}MB 文件使用内联方式...")
            try:
                upload_time = time.time() - start_time
                logger.info(f"✅ 降级到内联方式，耗时: {upload_time:.2f}秒")
                return f"inline:{video_path}"
            except Exception as e:
                upload_time = time.time() - start_time
                logger.error(f"❌ 降级方案也失败 (耗时: {upload_time:.2f}秒): {e}")
                return None
    
    def _wait_for_file_active(self, file_name: str, max_wait_time: int = 60) -> bool:
        """等待文件变为ACTIVE状态"""
        if not self.genai_client:
            return False
            
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                file_info = self.genai_client.files.get(name=file_name)
                if file_info.state.name == 'ACTIVE':
                    wait_time = time.time() - start_time
                    logger.info(f"✅ 文件已激活，等待时间: {wait_time:.2f}秒")
                    return True
                elif file_info.state.name == 'FAILED':
                    logger.error(f"❌ 文件处理失败: {file_info.state}")
                    return False
                else:
                    logger.info(f"📋 文件状态: {file_info.state.name}，继续等待...")
                    time.sleep(2)  # 等待2秒后重试
            except Exception as e:
                logger.warning(f"检查文件状态失败: {e}")
                time.sleep(2)
        
        logger.error(f"❌ 文件激活超时（{max_wait_time}秒）")
        return False
    
    def _upload_small_video(self, video_path: str, file_size_mb: float, start_time: float) -> Optional[str]:
        """上传小文件（≤20MB）使用内联方式"""
        logger.info("📤 使用内联方式上传小文件...")
        
        # 小文件直接返回路径，在analyze_video_content中处理
        upload_time = time.time() - start_time
        logger.info(f"✅ 小文件准备完成，将使用内联方式，耗时: {upload_time:.2f}秒")
        return f"inline:{video_path}"
    
    def analyze_video_content(self, file_uri: str, video_id: str = "", keyword: str = None, project_name: str = None) -> Optional[VideoAnalysisResult]:
        """
        使用Gemini分析视频内容并评分
        
        Args:
            file_uri: Gemini文件URI 或 内联文件路径（以"inline:"开头）
            video_id: 视频ID（用于标识和日志）
            keyword: 关键词，用于匹配检查
            project_name: 项目方名称，用于匹配检查
            
        Returns:
            视频分析结果
        """
        try:
            start_time = time.time()
            logger.info("🤖 开始使用Gemini分析视频内容...")
            
            # 判断是大文件（Files API）还是小文件（内联）
            if file_uri.startswith("inline:"):
                return self._analyze_video_inline(file_uri[7:], video_id, keyword, project_name)
            else:
                return self._analyze_video_with_file_api(file_uri, video_id, keyword, project_name)
                
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"❌ Gemini视频分析失败 (耗时: {analysis_time:.2f}秒): {e}")
            return None
    
    def _analyze_video_with_file_api(self, file_uri: str, video_id: str = "", keyword: str = None, project_name: str = None) -> Optional[VideoAnalysisResult]:
        """使用Files API方式分析视频 - 优先使用SDK"""
        start_time = time.time()
        logger.info("📤 使用Files API方式分析大文件...")
        
        # 构建评分提示词（不使用video_description，完全基于视频内容）
        prompt = self._build_analysis_prompt(keyword=keyword, project_name=project_name)
        
        # 优先尝试SDK方式
        if self.genai_client:
            try:
                logger.info("📤 使用Google AI SDK分析文件...")
                
                # 从URI获取文件对象
                file_name = file_uri.split('/')[-1]
                myfile = self.genai_client.files.get(name=f"files/{file_name}")
                
                response = self.genai_client.models.generate_content(
                    model=self.model, 
                    contents=[myfile, prompt]
                )
                
                analysis_time = time.time() - start_time
                logger.info(f"✅ SDK分析完成，响应长度: {len(response.text)} 字符，总耗时: {analysis_time:.2f}秒")
                
                # 使用传入的video_id或从文件URI提取文件名作为标识
                identifier = video_id if video_id else file_uri.split('/')[-1]
                return self._parse_analysis_result(response.text, identifier)
                
            except Exception as e:
                logger.warning(f"SDK分析失败: {e}，尝试REST API方式")
        
        # 回退到REST API方式
        logger.info("📤 使用REST API分析文件...")
        
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
            analysis_time = time.time() - start_time
            logger.info(f"✅ Gemini视频分析完成，总耗时: {analysis_time:.2f}秒")
            return self._parse_analysis_result(content, "unknown")
        else:
            analysis_time = time.time() - start_time
            logger.error(f"❌ Gemini响应中未找到分析结果，耗时: {analysis_time:.2f}秒")
            return None
    
    def _analyze_video_inline(self, video_path: str, video_description: str, start_time: float) -> Optional[VideoAnalysisResult]:
        """使用内联方式分析小文件（<20MB）"""
        logger.info("📤 使用内联方式分析小文件...")
        
        # 构建评分提示词
        prompt = self._build_analysis_prompt(video_description)
        
        # 读取视频文件
        with open(video_path, 'rb') as video_file:
            video_bytes = video_file.read()
        
        # 使用base64编码
        import base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        # 调用Gemini API
        generate_url = f"{self.base_url}/models/{self.model.replace('models/', '')}:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "video/mp4",
                                "data": video_base64
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
            analysis_time = time.time() - start_time
            logger.info(f"✅ Gemini内联视频分析完成，总耗时: {analysis_time:.2f}秒")
            return self._parse_analysis_result(content, "unknown")
        else:
            analysis_time = time.time() - start_time
            logger.error(f"❌ Gemini内联视频分析失败 (耗时: {analysis_time:.2f}秒): 未找到有效响应")
            return None
    
    def _build_analysis_prompt(self, keyword: str = None, project_name: str = None) -> str:
        """构建视频分析提示词"""
        
        # 构建筛选条件说明
        filter_info = "无特定筛选条件"
        if keyword or project_name:
            filter_terms = []
            if keyword:
                filter_terms.append(f"关键词: {keyword}")
            if project_name:
                filter_terms.append(f"项目方: {project_name}")
            filter_info = " 或 ".join(filter_terms)
        
        prompt = f"""
请分析这个视频的内容，并根据以下标准进行评分：

筛选条件：{filter_info}

**重要限制：如果视频中没有出现上述筛选条件中的任何内容，请直接给出零分评价，无需考虑其他评分标准。**

评分标准：
1. 关键词相关性 (0-60分)：评估视频内容与筛选条件的匹配度和主题一致性
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
            
            # 记录原始响应用于调试
            logger.debug(f"原始Gemini响应: {content[:500]}...")
            
            # 多种方式尝试提取JSON
            json_str = None
            
            # 方法1: 提取```json代码块
            json_block_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL | re.IGNORECASE)
            if json_block_match:
                json_str = json_block_match.group(1)
                logger.debug("使用json代码块提取")
            
            # 方法2: 提取第一个完整的JSON对象
            if not json_str:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    logger.debug("使用正则表达式提取")
            
            # 方法3: 查找最大的大括号内容
            if not json_str:
                brace_matches = re.findall(r'\{.*?\}', content, re.DOTALL)
                if brace_matches:
                    json_str = max(brace_matches, key=len)
                    logger.debug("使用最大括号内容提取")
            
            if not json_str:
                logger.error("无法从Gemini响应中提取JSON")
                return None
            
            # 清理JSON字符串
            json_str = json_str.strip()
            
            # 尝试修复常见的JSON格式问题
            json_str = self._fix_json_format(json_str)
            
            logger.debug(f"提取的JSON: {json_str[:200]}...")
            
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
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"问题JSON内容: {json_str if 'json_str' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"解析Gemini分析结果失败: {e}")
            return None
    
    def _fix_json_format(self, json_str: str) -> str:
        """修复常见的JSON格式问题"""
        try:
            import re
            
            # 移除可能的markdown标记
            json_str = re.sub(r'^```json\s*', '', json_str, flags=re.IGNORECASE)
            json_str = re.sub(r'\s*```$', '', json_str)
            
            # 移除注释
            json_str = re.sub(r'//.*?\n', '\n', json_str)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            # 修复尾随逗号
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            # 修复单引号为双引号
            json_str = re.sub(r"(?<!\\)'([^']*?)(?<!\\)'", r'"\1"', json_str)
            
            # 修复未引用的键名
            json_str = re.sub(r'(\w+)\s*:', r'"\1":', json_str)
            
            return json_str
        except Exception as e:
            logger.warning(f"JSON格式修复失败: {e}")
            return json_str
    
    def cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"已清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def analyze_video_from_url(self, video_url: str, video_id: str, keyword: str = None, project_name: str = None) -> Optional[VideoAnalysisResult]:
        """
        从视频URL完整分析视频内容
        
        Args:
            video_url: 视频下载URL
            video_id: 视频ID
            keyword: 关键词，用于匹配检查
            project_name: 项目方名称，用于匹配检查
            
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
                result = self.analyze_video_content(file_uri, video_id, keyword, project_name)
            else:
                # 小文件：直接内联处理
                result = self._analyze_video_inline(temp_file_path, video_id, keyword, project_name)
            
            return result
            
        finally:
            # 清理临时文件
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def _analyze_video_inline(self, video_path: str, video_id: str, keyword: str = None, project_name: str = None) -> Optional[VideoAnalysisResult]:
        """内联分析小视频文件，支持智能重试机制"""
        start_time = time.time()
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"🤖 使用内联方式分析视频 {video_id}... (文件大小: {file_size_mb:.2f}MB)")
        
        # 检查API密钥
        if not self.api_key:
            logger.error("Google API Key未配置，无法进行视频分析")
            return None
        
        # 读取视频数据（只读取一次）
        try:
            with open(video_path, 'rb') as f:
                video_data = f.read()
        except Exception as e:
            logger.error(f"❌ 读取视频文件失败 {video_id}: {e}")
            return None
        
        # Base64编码（只编码一次）
        import base64
        video_b64 = base64.b64encode(video_data).decode('utf-8')
        
        prompt = self._build_analysis_prompt(keyword=keyword, project_name=project_name)
        generate_url = f"{self.base_url}/models/{self.model.replace('models/', '')}:generateContent"
        
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
        
        # 开始重试循环
        max_retries = Config.GOOGLE_MAX_RETRIES
        retry_delay = Config.GOOGLE_RETRY_DELAY
        backoff_factor = Config.GOOGLE_RETRY_BACKOFF
        
        for attempt in range(max_retries + 1):  # +1 因为第一次不算重试
            try:
                if attempt > 0:
                    logger.info(f"🔄 视频 {video_id} 第 {attempt} 次重试，延迟 {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                    retry_delay *= backoff_factor  # 指数退避
                
                logger.info(f"🔗 调用Gemini API: {generate_url} (尝试 {attempt + 1}/{max_retries + 1})")
                logger.info(f"📤 发送请求到Gemini API...")
                
                response = requests.post(
                    generate_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                logger.info(f"📥 收到响应，状态码: {response.status_code}")
                
                # 成功响应
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'candidates' in result and result['candidates']:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        analysis_time = time.time() - start_time
                        retry_info = f" (重试 {attempt} 次)" if attempt > 0 else ""
                        logger.info(f"✅ Gemini分析完成，响应长度: {len(content)} 字符，总耗时: {analysis_time:.2f}秒{retry_info}")
                        return self._parse_analysis_result(content, video_id)
                    else:
                        analysis_time = time.time() - start_time
                        logger.error(f"❌ Gemini响应格式异常 (耗时: {analysis_time:.2f}秒): {result}")
                        return None
                
                # 检查是否为可重试的错误
                elif self._is_retryable_error(response.status_code):
                    if attempt < max_retries:
                        error_msg = self._get_error_message(response)
                        logger.warning(f"⚠️ 视频 {video_id} Gemini API可重试错误 {response.status_code}: {error_msg}")
                        continue  # 继续重试
                    else:
                        error_msg = self._get_error_message(response)
                        logger.error(f"❌ 视频 {video_id} Gemini API错误，已达最大重试次数 {response.status_code}: {error_msg}")
                        return None
                
                # 不可重试的错误
                else:
                    error_msg = self._get_error_message(response)
                    logger.error(f"❌ 视频 {video_id} Gemini API不可重试错误 {response.status_code}: {error_msg}")
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ 视频 {video_id} Gemini API连接错误，将重试: {e}")
                    continue
                else:
                    analysis_time = time.time() - start_time
                    logger.error(f"❌ 视频 {video_id} Gemini API连接错误 (耗时: {analysis_time:.2f}秒): {e}")
                    logger.info("💡 可能的解决方案:")
                    logger.info("   1. 检查网络连接")
                    logger.info("   2. 检查Google API Key是否有效")
                    logger.info("   3. 检查是否需要VPN访问Google服务")
                    return None
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ 视频 {video_id} Gemini API超时，将重试: {e}")
                    continue
                else:
                    analysis_time = time.time() - start_time
                    logger.error(f"❌ 视频 {video_id} Gemini API超时 (耗时: {analysis_time:.2f}秒): {e}")
                    return None
                    
            except Exception as e:
                analysis_time = time.time() - start_time
                logger.error(f"❌ 视频 {video_id} 内联视频分析失败 (耗时: {analysis_time:.2f}秒): {e}")
                return None
        
        # 如果所有重试都失败了
        analysis_time = time.time() - start_time
        logger.error(f"❌ 视频 {video_id} Gemini分析最终失败，已重试 {max_retries} 次 (总耗时: {analysis_time:.2f}秒)")
        return None
    
    def _is_retryable_error(self, status_code: int) -> bool:
        """判断HTTP状态码是否为可重试的错误"""
        retryable_codes = {
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable (模型超载)
            504,  # Gateway Timeout
            429,  # Too Many Requests (速率限制)
        }
        return status_code in retryable_codes
    
    def _get_error_message(self, response) -> str:
        """从响应中提取错误消息"""
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_info = error_data['error']
                message = error_info.get('message', '未知错误')
                status = error_info.get('status', '')
                if status:
                    return f"{message} ({status})"
                return message
            return response.text
        except:
            return response.text
    
