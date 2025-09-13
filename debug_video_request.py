#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试视频请求失败问题
测试TiKhub API的视频详情接口
"""

import requests
import json
from config import Config

def test_video_request(aweme_id=None):
    """测试视频请求"""
    # 测试多个视频ID
    test_ids = [
        "7538062964197166354",  # 原始失败的ID
        "7409618618934971690",  # 测试一个可能有效的ID
        "7380000000000000000",  # 测试ID格式
    ]
    
    if aweme_id:
        test_ids = [aweme_id]
    
    api_key = Config.TIKHUB_API_KEY
    base_url = Config.TIKHUB_BASE_URL
    
    for i, test_id in enumerate(test_ids):
        print(f"\n{'='*60}")
        print(f"🔧 测试视频请求 #{i+1}")
        print(f"   视频ID: {test_id}")
        print(f"   API Key: {api_key[:20]}...")
        print(f"   Base URL: {base_url}")
        print()
        
        _test_single_video(test_id, api_key, base_url)

def _test_single_video(aweme_id, api_key, base_url):
    """测试单个视频请求"""
    
    # 构建请求URL
    endpoint = "/api/v1/tiktok/app/v3/fetch_one_video"
    url = f"{base_url}{endpoint}"
    
    # 请求参数
    params = {
        "aweme_id": aweme_id
    }
    
    # 请求头
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'TikTok-Creator-Score/1.0.0'
    }
    
    print(f"📤 发送请求到: {url}")
    print(f"📋 请求参数: {params}")
    print(f"📋 请求头: {dict(headers)}")
    print()
    
    try:
        # 发送请求
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print()
        
        # 打印响应内容
        try:
            response_data = response.json()
            print(f"📋 响应内容:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 检查响应结构
            if response_data.get('code') == 200:
                print("\n✅ 请求成功")
                data = response_data.get('data', {})
                if data:
                    print(f"📋 视频数据字段: {list(data.keys())}")
                else:
                    print("⚠️ 响应中没有data字段")
            else:
                error_code = response_data.get('code')
                error_msg = response_data.get('message', '未知错误')
                print(f"\n❌ 请求失败 (code: {error_code}): {error_msg}")
                
        except json.JSONDecodeError:
            print(f"❌ 响应不是有效的JSON格式:")
            print(response.text[:1000])  # 只打印前1000字符
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print("💡 可能的原因:")
        print("   1. 网络连接问题")
        print("   2. API服务器不可达")
        print("   3. 防火墙阻止连接")
        
    except requests.exceptions.Timeout as e:
        print(f"❌ 请求超时: {e}")
        print("💡 可能的原因:")
        print("   1. 网络延迟过高")
        print("   2. API服务器响应慢")
        
    except Exception as e:
        print(f"❌ 其他错误: {e}")
    
    print("\n🔧 对应的curl命令:")
    curl_cmd = f'curl -X GET "{url}?aweme_id={aweme_id}" '
    curl_cmd += f'-H "Authorization: Bearer {api_key}" '
    curl_cmd += f'-H "Content-Type: application/json" '
    curl_cmd += f'-H "User-Agent: TikTok-Creator-Score/1.0.0" '
    curl_cmd += '--compressed | jq .'
    print(curl_cmd)

def test_api_connectivity():
    """测试API连通性"""
    print("\n🔗 测试API连通性...")
    
    try:
        # 测试基础连接
        response = requests.get(Config.TIKHUB_BASE_URL, timeout=10)
        print(f"✅ API服务器可达，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ API服务器不可达: {e}")

def test_api_quota():
    """测试API配额和认证"""
    print("\n💳 测试API配额和认证...")
    
    try:
        # 测试API认证 - 使用一个简单的端点
        headers = {
            'Authorization': f'Bearer {Config.TIKHUB_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'TikTok-Creator-Score/1.0.0'
        }
        
        # 尝试访问用户信息或配额信息端点
        test_url = f"{Config.TIKHUB_BASE_URL}/api/v1/user/info"
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"📊 认证测试状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ API认证成功")
                print(f"📋 用户信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"✅ API认证成功，但响应格式异常")
        elif response.status_code == 401:
            print(f"❌ API Key无效或已过期")
        elif response.status_code == 403:
            print(f"❌ API访问被拒绝，可能是权限不足")
        elif response.status_code == 429:
            print(f"❌ API请求频率限制，需要等待")
        else:
            print(f"⚠️ 未知状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"📋 响应内容: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ API配额测试失败: {e}")

if __name__ == "__main__":
    test_api_connectivity()
    test_api_quota()
    print("\n" + "="*50)
    test_video_request()