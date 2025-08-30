#!/usr/bin/env python3
"""测试修复后的API功能"""

import logging
from api_client import TiKhubAPIClient
from creator_score_calculator import CreatorScoreCalculator

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_fix():
    """测试API修复后的功能"""
    print("=== 测试API修复后的功能 ===")
    
    # 初始化客户端
    client = TiKhubAPIClient()
    calculator = CreatorScoreCalculator()
    
    # 测试用户
    username = "auto_trading0"
    
    try:
        # 1. 测试获取secUid
        print(f"\n🔄 步骤1：获取用户 {username} 的secUid...")
        sec_uid = client.get_secuid_from_username(username)
        if sec_uid:
            print(f"✅ 成功获取secUid: {sec_uid}")
        else:
            print(f"❌ 获取secUid失败")
            return
        
        # 2. 测试获取视频列表
        print(f"\n🔄 步骤2：获取用户视频列表...")
        video_ids = client.fetch_user_videos(sec_uid, 5)
        print(f"✅ 成功获取 {len(video_ids)} 个视频ID")
        if video_ids:
            print(f"前3个视频ID: {video_ids[:3]}")
        
        # 3. 测试获取视频详情
        print(f"\n🔄 步骤3：获取视频详情...")
        video_details = client.fetch_user_top_videos(sec_uid, 3)
        print(f"✅ 成功获取 {len(video_details)} 个视频详情")
        
        if video_details:
            for i, video in enumerate(video_details[:2], 1):
                print(f"视频{i}: 播放量={video.view_count:,}, 点赞={video.like_count:,}, 评论={video.comment_count:,}")
        
        # 4. 测试完整评分计算
        print(f"\n🔄 步骤4：计算完整评分...")
        creator_score = calculator.calculate_creator_score_by_user_id(sec_uid, 3)
        
        print(f"\n🎉 评分计算成功！")
        print(f"用户: {creator_score.username}")
        print(f"最终评分: {creator_score.final_score:.2f}")
        print(f"账户质量分: {creator_score.account_quality.total_score:.2f}")
        print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}")
        print(f"分析视频数量: {creator_score.video_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error(f"测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_api_fix()
    if success:
        print("\n🎉 所有测试通过！API修复成功！")
    else:
        print("\n❌ 测试失败，需要进一步调试")