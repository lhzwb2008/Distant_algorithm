#!/usr/bin/env python3
"""
配置验证工具
检查API密钥和配置是否正确设置
"""

import os
from config import Config

def check_env_file():
    """检查.env文件是否存在"""
    env_file = '.env'
    if os.path.exists(env_file):
        print("✅ .env 文件存在")
        return True
    else:
        print("❌ .env 文件不存在")
        print("💡 请复制 .env.example 为 .env 并配置API密钥:")
        print("   cp .env.example .env")
        print("   然后编辑 .env 文件填入真实的API密钥")
        return False

def check_api_keys():
    """检查API密钥配置"""
    print("\n🔍 API密钥配置检查:")
    
    issues = []
    
    # 检查TiKhub API密钥
    if Config.TIKHUB_API_KEY:
        print(f"✅ TiKhub API Key: {Config.TIKHUB_API_KEY[:20]}...{Config.TIKHUB_API_KEY[-10:]}")
    else:
        print("❌ TiKhub API Key: 未配置")
        issues.append("TiKhub API密钥未在.env文件中配置")
    
    # 检查OpenRouter API密钥
    if Config.OPENROUTER_API_KEY:
        print(f"✅ OpenRouter API Key: {Config.OPENROUTER_API_KEY[:20]}...{Config.OPENROUTER_API_KEY[-10:]}")
    else:
        print("❌ OpenRouter API Key: 未配置")
        issues.append("OpenRouter API密钥未在.env文件中配置")
    
    return issues

def check_api_endpoints():
    """检查API端点配置"""
    print("\n🌐 API端点配置:")
    print(f"✅ TiKhub Base URL: {Config.TIKHUB_BASE_URL}")
    print(f"✅ OpenRouter Base URL: {Config.OPENROUTER_BASE_URL}")
    print(f"✅ OpenRouter Model: {Config.OPENROUTER_MODEL}")

def check_other_configs():
    """检查其他配置"""
    print("\n⚙️  其他配置:")
    print(f"✅ 账户质量数据范围: {Config.ACCOUNT_QUALITY_DAYS} 天")
    print(f"✅ 内容互动最大视频数: {Config.CONTENT_INTERACTION_MAX_VIDEOS}")
    print(f"✅ TiKhub 请求超时: {Config.TIKHUB_REQUEST_TIMEOUT}s")
    print(f"✅ TiKhub 最大重试: {Config.TIKHUB_MAX_RETRIES}")
    print(f"✅ OpenRouter 请求超时: {Config.OPENROUTER_REQUEST_TIMEOUT}s")

def main():
    """主函数"""
    print("🚀 Distant Algorithm 配置验证工具")
    print("=" * 50)
    
    # 1. 检查.env文件
    env_exists = check_env_file()
    
    if not env_exists:
        return False
    
    # 2. 检查API密钥
    issues = check_api_keys()
    
    # 3. 检查API端点
    check_api_endpoints()
    
    # 4. 检查其他配置
    check_other_configs()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 配置检查结果:")
    
    if not issues:
        print("🎉 所有配置都正确设置！")
        print("\n💡 现在您可以:")
        print("   • 运行字幕提取工具: python3 quick_subtitle_test.py <video_url>")
        print("   • 启动Web应用: python3 web_app.py")
        print("   • 运行评分系统: python3 example.py")
        return True
    else:
        print("⚠️  发现以下配置问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 解决步骤:")
        print("   1. 确保 .env 文件存在")
        print("   2. 在 .env 文件中添加缺失的API密钥:")
        print("      TIKHUB_API_KEY=your_actual_api_key")
        print("      OPENROUTER_API_KEY=your_actual_api_key")
        print("   3. 重新运行此脚本验证配置")
        
        return False

if __name__ == "__main__":
    main()
