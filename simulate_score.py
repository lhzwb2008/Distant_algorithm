#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok创作者评分模拟器

通过输入用户nickname直接计算评分的简化脚本
使用方法: python3 simulate_score.py <username> [video_count]
"""

import sys
import logging
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient
from config import Config

# 配置简化的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python3 simulate_score.py <username> [keyword]")
        print("示例: python3 simulate_score.py auto_trading0")
        print("示例: python3 simulate_score.py auto_trading0 交易")
        sys.exit(1)
    
    username = sys.argv[1]
    keyword = None  # 关键词筛选
    
    if len(sys.argv) >= 3:
        keyword = sys.argv[2]
        print(f"🔍 将筛选包含关键词 '{keyword}' 的视频")
    
    print(f"🎯 TikTok创作者评分分析 - 用户: {username}")
    print("=" * 50)
    
    # 初始化计算器
    try:
        api_client = TiKhubAPIClient()
        calculator = CreatorScoreCalculator(api_client)
        print("✅ 评分系统初始化完成")
    except Exception as e:
        print(f"❌ 评分系统初始化失败: {e}")
        sys.exit(1)
    
    # 计算评分
    calculate_score_by_username(calculator, username, keyword)

def calculate_score_by_username(calculator: CreatorScoreCalculator, username: str, keyword: str = None):
    """通过用户名计算评分"""
    try:
        if keyword:
            print(f"\n🔄 开始分析用户 {username} 包含关键词 '{keyword}' 的视频")
        else:
            print(f"\n🔄 开始分析用户 {username} 的视频")
        
        # 获取secUid
        sec_uid = calculator.api_client.get_secuid_from_username(username)
        if not sec_uid:
            print(f"❌ 无法获取用户 {username} 的secUid")
            return
        
        # 计算评分
        final_score = calculator.calculate_score(sec_uid, keyword=keyword)
        
        print(f"\n🎉 最终评分: {final_score:.2f}分")
        
    except Exception as e:
        print(f"❌ 计算评分时发生错误: {e}")
        logger.error(f"计算评分错误: {e}", exc_info=True)

def calculate_score_by_user_id(calculator: CreatorScoreCalculator):
    """通过用户ID计算评分 (保留兼容性)"""
    try:
        # 获取用户输入
        user_id = input("\n请输入TikTok用户名 (例如: auto_trading0): ").strip()
        if not user_id:
            print("❌ 用户名不能为空")
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
        
        calculate_score_by_username(calculator, user_id, video_count)
        
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



if __name__ == "__main__":
    main()