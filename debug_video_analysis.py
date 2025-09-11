#!/usr/bin/env python3
"""
视频分析诊断脚本
专门用于排查特定视频ID的Gemini API调用问题
"""

import os
import sys
import time
import logging
import requests
import base64
from typing import Optional

# 添加项目根目录到Python路径
sys.path.append('/root/Distant_algorithm')

from config import Config
from api_client import TiKhubAPIClient

# 设置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/root/Distant_algorithm/debug_video.log')
    ]
)
logger = logging.getLogger(__name__)

class VideoDebugger:
    """视频分析调试器"""
    
    def __init__(self):
        self.api_client = TiKhubAPIClient()
        self.api_key = Config.GOOGLE_API_KEY
        self.model = Config.GOOGLE_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = Config.GOOGLE_REQUEST_TIMEOUT
        
    def debug_video(self, video_id: str):
        """调试特定视频ID的完整流程"""
        logger.info(f"🔍 开始调试视频 {video_id}")
        
        # 步骤1: 检查API配置
        if not self._check_api_config():
            return False
            
        # 步骤2: 获取视频信息
        video_info = self._get_video_info(video_id)
        if not video_info:
            return False
            
        # 步骤3: 获取视频下载URL
        video_url = self._get_video_url(video_id)
        if not video_url:
            return False
            
        # 步骤4: 下载视频文件
        video_path = self._download_video(video_url, video_id)
        if not video_path:
            return False
            
        # 步骤5: 分析视频文件
        self._analyze_video_file(video_path, video_id)
        
        # 步骤6: 尝试Gemini API调用
        self._test_gemini_api(video_path, video_id)
        
        # 清理临时文件
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"🗑️ 清理临时文件: {video_path}")
            
        return True
    
    def _check_api_config(self) -> bool:
        """检查API配置"""
        logger.info("📋 检查API配置...")
        
        if not self.api_key:
            logger.error("❌ Google API Key未配置")
            return False
        logger.info(f"✅ Google API Key: {self.api_key[:10]}...")
        
        if not Config.TIKHUB_API_KEY:
            logger.error("❌ TikHub API Key未配置")
            return False
        logger.info(f"✅ TikHub API Key: {Config.TIKHUB_API_KEY[:10]}...")
        
        logger.info(f"✅ Gemini Model: {self.model}")
        logger.info(f"✅ API Timeout: {self.timeout}s")
        
        return True
    
    def _get_video_info(self, video_id: str) -> Optional[dict]:
        """获取视频基本信息"""
        logger.info(f"📺 获取视频 {video_id} 基本信息...")
        
        try:
            # 调用TikHub API获取视频信息
            response = self.api_client._make_request(
                endpoint="/api/v1/tiktok/app/v3/fetch_one_video",
                params={"aweme_id": video_id}
            )
            
            logger.info(f"📊 API响应: {response}")
            
            # 检查是否被过滤
            if response and 'filter_detail' in response:
                filter_info = response['filter_detail']
                if filter_info.get('filter_reason'):
                    logger.error(f"❌ 视频被过滤: {filter_info.get('filter_reason')}")
                    logger.error(f"❌ 过滤详情: {filter_info.get('detail_msg', 'N/A')}")
                    logger.error("❌ 这个视频ID可能已被删除、私有化或不可访问")
                    return None
            
            if response and 'aweme_detail' in response and response['aweme_detail']:
                video_detail = response['aweme_detail']
                logger.info(f"✅ 视频标题: {video_detail.get('desc', 'N/A')}")
                logger.info(f"✅ 视频时长: {video_detail.get('duration', 'N/A')}ms")
                logger.info(f"✅ 视频作者: {video_detail.get('author', {}).get('nickname', 'N/A')}")
                
                # 检查视频URL
                video_play_addr = video_detail.get('video', {}).get('play_addr', {})
                url_list = video_play_addr.get('url_list', [])
                logger.info(f"✅ 可用下载URL数量: {len(url_list)}")
                
                return video_detail
            else:
                logger.error("❌ 无法获取视频详情 - aweme_detail为空")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取视频信息失败: {e}")
            return None
    
    def _get_video_url(self, video_id: str) -> Optional[str]:
        """获取视频下载URL"""
        logger.info(f"🔗 获取视频 {video_id} 下载URL...")
        
        try:
            response = self.api_client._make_request(
                endpoint="/api/v1/tiktok/app/v3/fetch_one_video",
                params={"aweme_id": video_id}
            )
            
            logger.info(f"📊 URL API响应: {response}")
            
            if response and 'aweme_detail' in response:
                video_detail = response['aweme_detail']
                video_play_addr = video_detail.get('video', {}).get('play_addr', {})
                url_list = video_play_addr.get('url_list', [])
                
                if url_list:
                    video_url = url_list[0]
                    logger.info(f"✅ 视频下载URL: {video_url[:100]}...")
                    return video_url
                else:
                    logger.error("❌ 未找到视频下载URL")
                    return None
            else:
                logger.error("❌ API响应中无视频详情")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取视频URL失败: {e}")
            return None
    
    def _download_video(self, video_url: str, video_id: str) -> Optional[str]:
        """下载视频文件"""
        logger.info(f"⬇️ 下载视频 {video_id}...")
        
        temp_path = f"/tmp/debug_video_{video_id}.mp4"
        
        try:
            response = requests.get(video_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(temp_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"✅ 视频下载完成: {temp_path}")
            logger.info(f"✅ 文件大小: {file_size_mb:.2f}MB")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ 视频下载失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None
    
    def _analyze_video_file(self, video_path: str, video_id: str):
        """分析视频文件属性"""
        logger.info(f"🔍 分析视频文件 {video_id}...")
        
        try:
            # 基本文件信息
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"📊 文件大小: {file_size_mb:.2f}MB ({file_size} bytes)")
            
            # MIME类型检测
            import mimetypes
            mime_type, _ = mimetypes.guess_type(video_path)
            logger.info(f"📊 MIME类型: {mime_type}")
            
            # 检查是否超过20MB限制
            if file_size > 20 * 1024 * 1024:
                logger.warning(f"⚠️ 文件大小超过20MB限制，需要使用Files API")
            else:
                logger.info(f"✅ 文件大小符合内联数据要求")
            
            # 尝试读取文件头
            with open(video_path, 'rb') as f:
                header = f.read(16)
                logger.info(f"📊 文件头(hex): {header.hex()}")
                
                # 检查是否为有效的MP4文件
                if header[4:8] == b'ftyp':
                    logger.info("✅ 检测到有效的MP4文件头")
                else:
                    logger.warning("⚠️ 文件头不符合标准MP4格式")
            
        except Exception as e:
            logger.error(f"❌ 分析视频文件失败: {e}")
    
    def _test_gemini_api(self, video_path: str, video_id: str):
        """测试Gemini API调用"""
        logger.info(f"🤖 测试Gemini API调用 {video_id}...")
        
        try:
            # 读取视频数据
            logger.info("📖 读取视频数据...")
            with open(video_path, 'rb') as f:
                video_data = f.read()
            logger.info(f"✅ 读取完成，数据长度: {len(video_data)} bytes")
            
            # Base64编码
            logger.info("🔄 Base64编码...")
            start_time = time.time()
            video_b64 = base64.b64encode(video_data).decode('utf-8')
            encode_time = time.time() - start_time
            logger.info(f"✅ Base64编码完成，耗时: {encode_time:.2f}s，编码后长度: {len(video_b64)} 字符")
            
            # 构建请求
            logger.info("🔧 构建API请求...")
            generate_url = f"{self.base_url}/models/{self.model.replace('models/', '')}:generateContent"
            logger.info(f"🔗 API URL: {generate_url}")
            
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
                                "text": """请分析这个视频的内容，并根据以下标准进行评分：

视频描述：无

评分标准：
1. 关键词相关性 (0-60分)：评估视频内容与描述的匹配度和主题一致性
2. 内容原创性 (0-20分)：评估内容的原创程度和独特性
3. 表达清晰度 (0-10分)：评估视频的表达是否清晰、逻辑是否合理
4. 垃圾信息识别 (0-5分)：检测是否存在垃圾信息、重复内容或低质量内容
5. 推广内容识别 (0-5分)：检测是否为纯推广内容或包含过多营销信息

请以JSON格式返回评分结果：
{
    "content_summary": "视频内容的简要总结",
    "keyword_relevance": 分数,
    "originality_score": 分数,
    "clarity_score": 分数,
    "spam_score": 分数,
    "promotion_score": 分数,
    "total_score": 总分,
    "reasoning": {
        "keyword_reasoning": "关键词相关性评分理由",
        "originality_reasoning": "原创性评分理由",
        "clarity_reasoning": "清晰度评分理由",
        "spam_reasoning": "垃圾信息评分理由",
        "promotion_reasoning": "推广内容评分理由"
    }
}

请确保返回有效的JSON格式。"""
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
            logger.info(f"📊 请求体大小: {len(str(payload))} 字符")
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                generate_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            request_time = time.time() - start_time
            
            logger.info(f"📥 收到响应，状态码: {response.status_code}，耗时: {request_time:.2f}s")
            logger.info(f"📊 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ API调用成功!")
                logger.info(f"📊 响应内容: {str(result)[:500]}...")
                
                if 'candidates' in result and result['candidates']:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    logger.info(f"🎯 分析结果: {content[:200]}...")
                else:
                    logger.warning("⚠️ 响应格式异常，未找到分析结果")
            else:
                logger.error(f"❌ API调用失败: {response.status_code}")
                logger.error(f"❌ 错误响应: {response.text}")
                
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_info = error_data['error']
                        logger.error(f"❌ 错误代码: {error_info.get('code', 'N/A')}")
                        logger.error(f"❌ 错误消息: {error_info.get('message', 'N/A')}")
                        logger.error(f"❌ 错误状态: {error_info.get('status', 'N/A')}")
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Gemini API测试失败: {e}")
            import traceback
            logger.error(f"❌ 详细错误: {traceback.format_exc()}")

def main():
    """主函数"""
    problem_video_id = "7506300694433942790"  # 问题视频ID
    
    print(f"🚀 开始诊断视频 {problem_video_id}")
    print("=" * 60)
    
    debugger = VideoDebugger()
    success = debugger.debug_video(problem_video_id)
    
    print("=" * 60)
    if not success:
        print("❌ 问题视频ID已确认不可用")
        print("🔄 尝试使用一个可用的视频ID来测试Gemini API...")
        
        # 从日志中找一个成功的视频ID进行测试
        test_video_ids = [
            "7289558230940781830",  # 从日志中看到的成功案例
            "7509530540693884165",
            "7504189407235280134"
        ]
        
        for test_id in test_video_ids:
            print(f"🧪 测试视频ID: {test_id}")
            if debugger.debug_video(test_id):
                print(f"✅ 找到可用视频ID: {test_id}")
                break
            else:
                print(f"❌ 视频ID {test_id} 也不可用")
    else:
        print("✅ 诊断完成，请查看日志文件 debug_video.log")
    
    print(f"📄 详细日志文件: /root/Distant_algorithm/debug_video.log")

if __name__ == "__main__":
    main()
