#!/usr/bin/env python3
"""
TikTok字幕提取测试工具
用法: python3 quick_subtitle_test.py <视频链接或ID>
"""

import sys
import re
from api_client import TiKhubAPIClient

def extract_video_id(url_or_id: str) -> str:
    """提取视频ID"""
    if not url_or_id:
        raise ValueError("链接或ID不能为空")
    
    # 如果是纯数字，直接返回
    if url_or_id.isdigit() and len(url_or_id) >= 15:
        return url_or_id
    
    # 从URL中提取ID
    patterns = [r'/video/(\d+)', r'aweme_id=(\d+)', r'item_id=(\d+)']
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    raise ValueError(f"无法从 '{url_or_id}' 中提取视频ID")

def main():
    if len(sys.argv) != 2:
        print("用法: python3 quick_subtitle_test.py <视频链接或ID>")
        print("\n示例:")
        print("  python3 quick_subtitle_test.py 7123456789012345678")
        print("  python3 quick_subtitle_test.py 'https://www.tiktok.com/@user/video/7123456789012345678'")
        sys.exit(1)
    
    url_or_id = sys.argv[1]
    
    try:
        # 提取视频ID
        video_id = extract_video_id(url_or_id)
        print(f"🎬 视频ID: {video_id}")
        
        # 初始化API客户端
        api_client = TiKhubAPIClient()
        
        # 获取视频详情
        print("📡 正在获取视频详情...")
        video_detail = api_client.fetch_video_detail(video_id)
        
        if not video_detail:
            print("❌ 无法获取视频详情")
            return
            
        print(f"✅ 视频详情获取成功")
        print(f"📹 视频描述: {video_detail.desc[:50]}..." if video_detail.desc else "无描述")
        print(f"📊 播放量: {video_detail.view_count:,}")
        
        # 使用主流程的字幕提取方法
        print("🔍 正在提取字幕...")
        subtitle = api_client.extract_subtitle_text(video_id)
        
        # 检查原始API响应中的字幕数据结构
        print("\n🔍 检查原始API响应中的字幕数据...")
        try:
            # 重新获取视频详情以检查原始数据
            print("   📡 正在获取原始API响应...")
            response = api_client._make_request('/api/v1/tiktok/app/v3/fetch_one_video', {
                'aweme_id': video_id,
                'region': 'US',
                'priority_region': 'US'
            })
            
            print(f"   📊 API响应状态: {bool(response)}")
            if response:
                print(f"   📊 响应顶层键: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            
            if response and 'data' in response and 'aweme_detail' in response['data']:
                aweme_detail = response['data']['aweme_detail']
                print(f"   📊 aweme_detail键: {list(aweme_detail.keys())}")
                
                # 检查所有可能的字幕相关字段
                print("   🔍 检查字幕相关字段:")
                
                # 检查 cla_info
                if 'cla_info' in aweme_detail:
                    cla_info = aweme_detail['cla_info']
                    print(f"      cla_info存在: {bool(cla_info)}")
                    if cla_info:
                        print(f"      cla_info类型: {type(cla_info)}")
                        print(f"      cla_info内容: {cla_info}")
                        
                        if isinstance(cla_info, dict) and 'caption_infos' in cla_info:
                            caption_infos = cla_info['caption_infos']
                            print(f"      caption_infos存在: {bool(caption_infos)}")
                            if caption_infos:
                                print(f"      caption_infos数量: {len(caption_infos)}")
                                for i, caption in enumerate(caption_infos):
                                    print(f"      字幕 {i+1}: {caption}")
                else:
                    print("      ❌ 没有找到 cla_info 字段")
                
                # 检查其他可能的字幕字段
                subtitle_fields = ['subtitle', 'captions', 'text_extra', 'desc']
                for field in subtitle_fields:
                    if field in aweme_detail:
                        value = aweme_detail[field]
                        print(f"      {field}: {str(value)[:100]}...")
                
                # 检查 video 字段下的字幕信息
                if 'video' in aweme_detail:
                    video_info = aweme_detail['video']
                    print(f"      video字段存在: {bool(video_info)}")
                    if isinstance(video_info, dict):
                        print(f"      video键: {list(video_info.keys())}")
                        if 'cla_info' in video_info:
                            print(f"      video.cla_info: {video_info['cla_info']}")
            else:
                print("   ❌ API响应格式不正确或缺少必要字段")
                if response:
                    print(f"   响应结构: {response}")
                
        except Exception as e:
            print(f"   ❌ 检查原始数据时出错: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")
        
        if subtitle and subtitle.full_text:
            print(f"\n✅ 字幕提取成功!")
            print(f"📝 字幕语言: {subtitle.language}")
            print(f"📝 字幕格式: {subtitle.caption_format}")
            print(f"📝 自动生成: {subtitle.is_auto_generated}")
            print(f"📊 字符数: {len(subtitle.full_text)}")
            print(f"📊 单词数: {len(subtitle.full_text.split())}")
            newline_char = '\n'
            print(f"📊 行数: {len(subtitle.full_text.split(newline_char))}")
            
            print(f"\n📝 字幕内容:")
            print("=" * 60)
            print(subtitle.full_text)
            print("=" * 60)
        else:
            print("❌ 此视频没有可用的字幕数据")
            print("💡 可能原因:")
            print("   • 视频作者没有添加字幕")
            print("   • 视频语言不支持自动字幕")
            print("   • 视频太短或音频质量不佳")
            print("   • TikTok没有为此视频生成字幕")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
