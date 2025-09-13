#!/usr/bin/env python3
"""
OpenRouter API客户端
用于调用大模型进行视频质量评分
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """视频质量评分结果"""
    keyword_score: float  # 关键词评分 (0-100)
    originality_score: float  # 内容原创性 (0-100)
    clarity_score: float  # 表达清晰度 (0-100)
    spam_score: float  # 垃圾信息识别 (0-100, 100表示无垃圾信息)
    promotion_score: float  # 推广内容识别 (0-100, 100表示非推广内容)
    total_score: float  # 总分 (0-100)
    reasoning: str  # 评分逻辑说明
    zero_score_reason: str = ""  # 0分原因标记（当total_score为0时的具体原因）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'keyword_score': self.keyword_score,
            'originality_score': self.originality_score,
            'clarity_score': self.clarity_score,
            'spam_score': self.spam_score,
            'promotion_score': self.promotion_score,
            'total_score': self.total_score,
            'reasoning': self.reasoning,
            'zero_score_reason': self.zero_score_reason
        }

class OpenRouterClient:
    """OpenRouter API客户端"""
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        """
        初始化OpenRouter客户端
        
        Args:
            api_key: OpenRouter API密钥，如果不提供则从配置文件读取
            model: 使用的模型，如果不提供则从配置文件读取
            base_url: API基础URL，如果不提供则从配置文件读取
        """
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.base_url = base_url or Config.OPENROUTER_BASE_URL
        self.model = model or Config.OPENROUTER_MODEL
        self.timeout = Config.OPENROUTER_REQUEST_TIMEOUT
        self.temperature = Config.OPENROUTER_TEMPERATURE
        self.max_tokens = Config.OPENROUTER_MAX_TOKENS
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Please set OPENROUTER_API_KEY in config or pass it directly.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://distant-algorithm.com",  # 可选：你的网站
            "X-Title": "Distant Algorithm Video Quality Scorer"  # 可选：应用名称
        }
        
        logger.info(f"OpenRouter客户端初始化完成，使用模型: {self.model}")
    
    def _make_request(self, messages: list, temperature: float = None) -> Dict[str, Any]:
        """
        发送API请求到OpenRouter
        
        Args:
            messages: 对话消息列表
            temperature: 生成温度 (0-1)，如果不提供则使用配置文件中的值
            
        Returns:
            API响应数据
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API请求失败: {e}")
            raise
    
    def evaluate_video_quality(self, subtitle_text: str, video_description: str = "") -> QualityScore:
        """
        基于字幕内容评估视频质量
        
        Args:
            subtitle_text: 视频字幕文本
            video_description: 视频描述 (可选)
            
        Returns:
            QualityScore对象包含各维度评分
        """
        # 构建评分提示词
        system_prompt = """你是一个专业的视频内容质量评估专家。请基于提供的视频字幕内容，按照以下标准进行评分：

评分标准（总分100分）：
1. 关键词评分 (60分)：
   - 评估内容是否包含明确的主题关键词
   - 一次提到相关关键词：20-30分
   - 多次提到相关关键词：40-50分
   - 包含完整项目/主题介绍：50-60分

2. 内容原创性 (20分)：
   - 评估内容的独特性和原创性
   - 高度原创、独特观点：16-20分
   - 中等原创性：10-15分
   - 低原创性或常见内容：0-9分

3. 表达清晰度 (10分)：
   - 评估语言表达的清晰性和逻辑性
   - 表达清晰、逻辑性强：8-10分
   - 表达一般：5-7分
   - 表达混乱：0-4分

4. 垃圾信息识别 (5分)：
   - 识别是否包含无意义、重复或低质量内容
   - 无垃圾信息：5分
   - 轻微垃圾信息：3-4分
   - 严重垃圾信息：0-2分

5. 推广内容识别 (5分)：
   - 识别是否为推广内容或包含无关标签
   - 非推广内容：5分
   - 轻微推广：3-4分
   - 明显推广：0-2分

请严格按照以下JSON格式返回评分结果：
{
  "keyword_score": 数字,
  "originality_score": 数字,
  "clarity_score": 数字,
  "spam_score": 数字,
  "promotion_score": 数字,
  "total_score": 数字,
  "reasoning": {
    "keyword_reasoning": "关键词评分的详细理由",
    "originality_reasoning": "原创性评分的详细理由",
    "clarity_reasoning": "清晰度评分的详细理由",
    "spam_reasoning": "垃圾信息评分的详细理由",
    "promotion_reasoning": "推广识别评分的详细理由",
    "total_reasoning": "总分计算说明"
  }
}

注意：请直接返回JSON，不要包含任何其他文字或格式标记。"""

        user_prompt = f"""请评估以下视频内容的质量：

视频描述：{video_description if video_description else "无描述"}

字幕内容：
{subtitle_text[:3000]}{"..." if len(subtitle_text) > 3000 else ""}

请按照评分标准给出详细评分。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            logger.info("正在调用OpenRouter进行视频质量评分...")
            response = self._make_request(messages)
            
            # 提取AI回复
            ai_response = response['choices'][0]['message']['content']
            logger.debug(f"AI评分回复: {ai_response}")
            
            # 尝试解析JSON回复
            try:
                # 提取JSON部分
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    score_data = json.loads(json_str)
                else:
                    raise ValueError("未找到JSON格式的评分结果")
                
                # 创建QualityScore对象
                reasoning_data = score_data.get('reasoning', '无评分说明')
                # 如果reasoning是字典，转换为JSON字符串
                if isinstance(reasoning_data, dict):
                    reasoning_str = json.dumps(reasoning_data, ensure_ascii=False, indent=2)
                else:
                    reasoning_str = str(reasoning_data)
                
                quality_score = QualityScore(
                    keyword_score=float(score_data.get('keyword_score', 0)),
                    originality_score=float(score_data.get('originality_score', 0)),
                    clarity_score=float(score_data.get('clarity_score', 0)),
                    spam_score=float(score_data.get('spam_score', 0)),
                    promotion_score=float(score_data.get('promotion_score', 0)),
                    total_score=float(score_data.get('total_score', 0)),
                    reasoning=reasoning_str,
                    zero_score_reason=""
                )
                
                logger.info(f"视频质量评分完成，总分: {quality_score.total_score}")
                return quality_score
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"解析AI评分结果失败: {e}")
                logger.error(f"AI原始回复: {ai_response}")
                
                # 返回默认评分
                return QualityScore(
                    keyword_score=0,
                    originality_score=0,
                    clarity_score=0,
                    spam_score=0,
                    promotion_score=0,
                    total_score=0,
                    reasoning=f"评分解析失败: {str(e)}",
                    zero_score_reason="评分解析失败"
                )
                
        except Exception as e:
            logger.error(f"视频质量评分失败: {e}")
            return QualityScore(
                keyword_score=0,
                originality_score=0,
                clarity_score=0,
                spam_score=0,
                promotion_score=0,
                total_score=0,
                reasoning=f"评分失败: {str(e)}",
                zero_score_reason="评分失败"
            )
