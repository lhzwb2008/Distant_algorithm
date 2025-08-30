#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok创作者评分模拟器

通过输入用户ID计算模拟分数的简单脚本
"""

import sys
import logging
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    print("=" * 60)
    print("TikTok创作者评分模拟器")
    print("=" * 60)
    
    # 初始化计算器
    try:
        api_client = TiKhubAPIClient()
        calculator = CreatorScoreCalculator(api_client)
        print("✅ 评分系统初始化成功")
    except Exception as e:
        print(f"❌ 评分系统初始化失败: {e}")
        return
    
    while True:
        print("\n" + "-" * 40)
        print("请选择操作:")
        print("1. 通过用户ID计算评分")
        print("2. 查看评分公式说明")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            calculate_score_by_user_id(calculator)
        elif choice == '2':
            show_scoring_formula()
        elif choice == '3':
            print("\n👋 感谢使用TikTok创作者评分系统！")
            break
        else:
            print("❌ 无效选择，请重新输入")

def calculate_score_by_user_id(calculator: CreatorScoreCalculator):
    """通过用户ID计算评分"""
    try:
        # 获取用户输入
        print("\n请选择输入方式:")
        print("1. 输入TikTok用户名 (例如: taylorswift)")
        print("2. 输入TikTok secUid (例如: MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM)")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            username = input("\n请输入TikTok用户名: ").strip()
            if not username:
                print("❌ 用户名不能为空")
                return
            
            # 通过用户名获取secUid
            print(f"🔄 正在获取用户 {username} 的secUid...")
            api_client = TiKhubAPIClient()
            user_id = api_client.get_secuid_from_username(username)
            
            if not user_id:
                 print(f"❌ 无法获取用户 {username} 的secUid")
                 print("💡 可能的原因:")
                 print("   1. 用户名不存在或拼写错误")
                 print("   2. 网络连接问题")
                 print("   3. TikTok API访问限制")
                 print("\n💡 建议解决方案:")
                 print("   1. 检查用户名是否正确")
                 print("   2. 直接使用secUid (选择选项2)")
                 print("   3. 稍后重试")
                 return
            
            print(f"✅ 成功获取secUid: {user_id}")
            
        elif choice == "2":
            user_id = input("\n请输入TikTok secUid: ").strip()
            if not user_id:
                print("❌ secUid不能为空")
                return
        else:
            print("❌ 无效的选择")
            return
        
        video_count_input = input("请输入要分析的视频数量 (默认5个): ").strip()
        video_count = 5
        if video_count_input:
            try:
                video_count = int(video_count_input)
                if video_count <= 0 or video_count > 20:
                    print("⚠️ 视频数量应在1-20之间，使用默认值5")
                    video_count = 5
            except ValueError:
                print("⚠️ 无效的视频数量，使用默认值5")
                video_count = 5
        
        print(f"\n🔄 正在分析用户 {user_id} 的前 {video_count} 个视频...")
        
        # 计算评分
        score = calculator.calculate_creator_score_by_user_id(user_id, video_count)
        
        # 显示结果
        print("\n" + "=" * 50)
        print("📊 评分结果")
        print("=" * 50)
        print(f"用户名: {score.username}")
        print(f"分析视频数: {video_count}")
        print(f"\n📈 评分详情:")
        print(f"  账户质量评分: {score.account_quality.total_score:.2f}/100")
        print(f"    - 粉丝数量得分: {score.account_quality.follower_score:.2f}")
        print(f"    - 总点赞得分: {score.account_quality.likes_score:.2f}")
        print(f"    - 发布频率得分: {score.account_quality.posting_score:.2f}")
        print(f"    - 质量加权系数: {score.account_quality.multiplier:.2f}")
        
        print(f"\n  内容互动评分: {score.content_interaction.total_score:.2f}/100")
        print(f"    - 播放量得分: {score.content_interaction.view_score:.2f}")
        print(f"    - 点赞数得分: {score.content_interaction.like_score:.2f}")
        print(f"    - 评论数得分: {score.content_interaction.comment_score:.2f}")
        print(f"    - 分享数得分: {score.content_interaction.share_score:.2f}")
        
        print(f"\n🎯 最终评分: {score.final_score:.2f}/100")
        
        # 评分等级
        grade = get_score_grade(score.final_score)
        print(f"📊 评分等级: {grade}")
        
    except Exception as e:
        print(f"❌ 计算评分时发生错误: {e}")
        logger.error(f"计算评分错误: {e}", exc_info=True)

def show_scoring_formula():
    """显示评分公式说明"""
    print("\n" + "=" * 60)
    print("📋 TikTok创作者评分公式说明")
    print("=" * 60)
    
    print("\n🎯 主评分公式:")
    print("TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权")
    print("\n📝 说明:")
    print("• 内容质量(维度3): 固定为60分")
    print("• 内容互动数据(维度2): 基于播放量、点赞、评论、分享计算")
    print("• 账户质量加权: 基于粉丝数、总点赞数、发布频率计算")
    
    print("\n📊 评分维度详情:")
    print("\n1. 账户质量评分 (影响加权系数):")
    print("   • 粉丝数量 (40%): 基于对数函数计算")
    print("   • 总点赞数 (40%): 基于对数函数计算")
    print("   • 发布频率 (20%): 基于理想发布频次计算")
    
    print("\n2. 内容互动评分 (65%权重):")
    print("   • 播放量 (10%): 基于播放量比率计算")
    print("   • 点赞数 (25%): 基于点赞率计算")
    print("   • 评论数 (30%): 基于评论率计算")
    print("   • 分享数 (35%): 基于分享率计算")
    
    print("\n3. 内容质量 (35%权重):")
    print("   • 当前固定为60分")
    
    print("\n🏆 账户质量加权系数:")
    print("   • 0-10分: 1.0倍")
    print("   • 10-30分: 1.2倍")
    print("   • 31-60分: 1.5倍")
    print("   • 61-80分: 2.0倍")
    print("   • 81-100分: 3.0倍")

def get_score_grade(score: float) -> str:
    """根据分数获取等级"""
    if score >= 90:
        return "🏆 S级 (优秀)"
    elif score >= 80:
        return "🥇 A级 (良好)"
    elif score >= 70:
        return "🥈 B级 (中等)"
    elif score >= 60:
        return "🥉 C级 (及格)"
    else:
        return "❌ D级 (需要改进)"

if __name__ == "__main__":
    main()