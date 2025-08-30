#!/usr/bin/env python3
"""测试API返回的数据字段"""

from api_client import TiKhubAPIClient
import json

def test_api_fields():
    """测试API返回的各个字段"""
    print("=== 测试API字段获取情况 ===")
    
    client = TiKhubAPIClient()
    sec_uid = 'MS4wLjABAAAA03-tVXtgJSYc9rbcTDCiDhAFGlNbSyXbWDcMi6xHI2uuy3mHuOQujUss4BSXnkKc'
    
    # 1. 获取视频ID列表
    print("\n🔄 步骤1：获取视频ID列表...")
    video_ids = client.fetch_user_videos(sec_uid, 3)
    print(f"获取到的视频ID: {video_ids[:3]}")
    
    if not video_ids:
        print("❌ 没有获取到视频ID")
        return
    
    # 2. 测试单个视频详情
    print("\n🔄 步骤2：获取单个视频详情...")
    video_id = video_ids[0]
    print(f"测试视频ID: {video_id}")
    
    try:
        video_detail = client.fetch_video_detail(video_id)
        print(f"\n📊 视频详情数据:")
        print(f"视频ID: {video_detail.video_id}")
        print(f"播放量: {video_detail.view_count:,}")
        print(f"点赞数: {video_detail.like_count:,}")
        print(f"评论数: {video_detail.comment_count:,}")
        print(f"分享数: {video_detail.share_count:,}")
        print(f"收藏数: {video_detail.collect_count:,}")
        
        # 检查哪些字段为0
        zero_fields = []
        if video_detail.view_count == 0:
            zero_fields.append("播放量")
        if video_detail.like_count == 0:
            zero_fields.append("点赞数")
        if video_detail.comment_count == 0:
            zero_fields.append("评论数")
        if video_detail.share_count == 0:
            zero_fields.append("分享数")
        if video_detail.collect_count == 0:
            zero_fields.append("收藏数")
            
        if zero_fields:
            print(f"\n⚠️  为0的字段: {', '.join(zero_fields)}")
        else:
            print(f"\n✅ 所有字段都有数据")
            
    except Exception as e:
        print(f"❌ 获取视频详情失败: {e}")
        return
    
    # 3. 测试多个视频
    print("\n🔄 步骤3：测试多个视频的数据...")
    for i, vid in enumerate(video_ids[:3], 1):
        try:
            detail = client.fetch_video_detail(vid)
            print(f"视频{i}: 播放={detail.view_count:,}, 点赞={detail.like_count:,}, 评论={detail.comment_count:,}, 分享={detail.share_count:,}")
        except Exception as e:
            print(f"视频{i} 获取失败: {e}")
    
    # 4. 测试批量获取
    print("\n🔄 步骤4：测试批量获取视频详情...")
    try:
        video_details = client.fetch_user_top_videos(sec_uid, 3)
        print(f"批量获取到 {len(video_details)} 个视频详情")
        
        total_views = sum(v.view_count for v in video_details)
        total_likes = sum(v.like_count for v in video_details)
        total_comments = sum(v.comment_count for v in video_details)
        total_shares = sum(v.share_count for v in video_details)
        
        print(f"\n📈 汇总数据:")
        print(f"总播放量: {total_views:,}")
        print(f"总点赞数: {total_likes:,}")
        print(f"总评论数: {total_comments:,}")
        print(f"总分享数: {total_shares:,}")
        
        # 分析为什么某些指标为0
        if total_views == 0:
            print("\n🔍 播放量为0的可能原因:")
            print("- API返回的数据中没有播放量字段")
            print("- 播放量字段名称不匹配")
            print("- 该用户的视频确实没有播放量")
            
        if total_comments == 0:
            print("\n🔍 评论数为0的可能原因:")
            print("- API返回的数据中没有评论数字段")
            print("- 评论数字段名称不匹配")
            print("- 该用户的视频确实没有评论")
            
        if total_shares == 0:
            print("\n🔍 分享数为0的可能原因:")
            print("- API返回的数据中没有分享数字段")
            print("- 分享数字段名称不匹配")
            print("- 该用户的视频确实没有分享")
            
    except Exception as e:
        print(f"❌ 批量获取失败: {e}")

if __name__ == "__main__":
    test_api_fields()