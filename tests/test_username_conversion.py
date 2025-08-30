#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户名转换和评分功能
"""

import logging
from api_client import TiKhubAPIClient
from creator_score_calculator import CreatorScoreCalculator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_username_to_secuid():
    """测试用户名转换为secUid"""
    print("\n=== 测试用户名转换为secUid ===")
    
    client = TiKhubAPIClient()
    test_usernames = ['auto_trading0', 'taylorswift', 'charlidamelio']
    
    for username in test_usernames:
        print(f"\n🔄 正在获取用户 {username} 的secUid...")
        sec_uid = client.get_secuid_from_username(username)
        
        if sec_uid:
            print(f"✅ 成功获取 {username} 的secUid: {sec_uid}")
        else:
            print(f"❌ 无法获取 {username} 的secUid")

def test_score_calculation():
    """测试评分计算功能"""
    print("\n=== 测试评分计算功能 ===")
    
    calculator = CreatorScoreCalculator()
    
    # 使用已知的secUid进行测试
    test_sec_uid = "MS4wLjABAAAA03-tVXtgJSYc9rbcTDCiDhAFGlNbSyXbWDcMi6xHI2uuy3mHuOQujUss4BSXnkKc"
    
    try:
        print(f"\n🔄 正在计算secUid {test_sec_uid} 的评分...")
        
        # 计算评分
        creator_score = calculator.calculate_creator_score_by_user_id(
            user_id=test_sec_uid,
            video_count=5
        )
        
        print(f"\n✅ 评分计算成功！")
        print(f"最终评分: {creator_score.final_score:.2f}")
        print(f"账户质量分: {creator_score.account_quality.total_score:.2f}")
        print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}")
        print(f"质量加权系数: {creator_score.account_quality.multiplier}")
        print(f"分析视频数量: {creator_score.video_count}")
        
    except Exception as e:
        print(f"❌ 评分计算失败: {e}")
        logger.error(f"评分计算失败: {e}")

def test_end_to_end():
    """端到端测试：从用户名到评分"""
    print("\n=== 端到端测试：从用户名到评分 ===")
    
    client = TiKhubAPIClient()
    calculator = CreatorScoreCalculator()
    
    username = 'auto_trading0'
    
    try:
        # 步骤1：获取secUid
        print(f"\n🔄 步骤1：获取用户 {username} 的secUid...")
        sec_uid = client.get_secuid_from_username(username)
        
        if not sec_uid:
            print(f"❌ 无法获取用户 {username} 的secUid，测试终止")
            return
            
        print(f"✅ 成功获取secUid: {sec_uid}")
        
        # 步骤2：计算评分
        print(f"\n🔄 步骤2：计算用户评分...")
        creator_score = calculator.calculate_creator_score_by_user_id(
            user_id=sec_uid,
            video_count=3
        )
        
        print(f"\n🎉 端到端测试成功完成！")
        print(f"用户: {username}")
        print(f"secUid: {sec_uid}")
        print(f"最终评分: {creator_score.final_score:.2f}")
        print(f"账户质量分: {creator_score.account_quality.total_score:.2f}")
        print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}")
        
    except Exception as e:
        print(f"❌ 端到端测试失败: {e}")
        logger.error(f"端到端测试失败: {e}")

def main():
    """主测试函数"""
    print("TikTok创作者评分系统 - 功能测试")
    print("=" * 50)
    
    # 运行各项测试
    test_username_to_secuid()
    test_score_calculation()
    test_end_to_end()
    
    print("\n=" * 50)
    print("所有测试完成！")

if __name__ == "__main__":
    main()