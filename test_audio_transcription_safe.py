#!/usr/bin/env python3
"""
安全的音频转文本功能测试脚本
"""

import os
import sys
from api_client import TiKhubAPIClient
from audio_transcription_service import AudioTranscriptionService

def test_audio_transcription():
    """测试音频转文本功能"""
    
    print("🧪 测试音频转文本功能")
    print("=" * 50)
    
    # 从环境变量获取OpenAI API密钥
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ 错误：请在.env文件中配置OPENAI_API_KEY")
        print("   示例：OPENAI_API_KEY=your_openai_api_key_here")
        print()
        print("📋 配置步骤:")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 编辑 .env 文件，填入真实的API密钥")
        print("   3. 重新运行此测试")
        return
    
    # 创建API客户端和转录服务
    api_client = TiKhubAPIClient()
    service = AudioTranscriptionService(api_client, openai_api_key)
    
    # 检查服务状态
    print("🔧 服务状态检查:")
    status = service.get_service_status()
    for key, value in status.items():
        status_icon = "✅" if value else "❌"
        print(f"   {key}: {status_icon}")
    
    print()
    
    # 测试视频ID（之前没有字幕的视频）
    test_video_ids = [
        "7545258736957328648",  # 第一个无字幕视频
        "7544909258668657928"   # 第二个无字幕视频
    ]
    
    for video_id in test_video_ids:
        print(f"🎬 测试视频: {video_id}")
        print("-" * 30)
        
        # 测试字幕提取（带回退）
        result = service.extract_subtitle_with_fallback(video_id)
        
        print(f"   结果: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   来源: {result.source}")
        
        if result.success and result.subtitle:
            print(f"   语言: {result.subtitle.language}")
            print(f"   文本长度: {len(result.subtitle.full_text)} 字符")
            print(f"   文本预览: {result.subtitle.full_text[:100]}...")
        elif result.error_message:
            print(f"   错误: {result.error_message}")
        
        print()

if __name__ == "__main__":
    test_audio_transcription()
