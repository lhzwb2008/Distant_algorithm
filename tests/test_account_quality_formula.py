#!/usr/bin/env python3
"""测试账户质量评分公式是否符合要求"""

import math
from account_quality_calculator import AccountQualityCalculator
from models import UserProfile, VideoDetail
from datetime import datetime, timedelta

def test_follower_score_formula():
    """测试粉丝数量评分公式"""
    calculator = AccountQualityCalculator()
    
    print("=== 粉丝数量评分测试 ===")
    print("公式: min(log10(followers) * 10, 100)")
    print("权重: 40%")
    print()
    
    test_cases = [
        (1000, "1K粉丝"),
        (5000, "5K粉丝"),
        (10000, "10K粉丝"),
        (50000, "50K粉丝"),
        (100000, "100K粉丝"),
        (500000, "500K粉丝"),
        (1000000, "1M粉丝")
    ]
    
    for followers, desc in test_cases:
        score = calculator.calculate_follower_score(followers)
        expected = min(math.log10(followers) * 10, 100)
        print(f"{desc}: {score:.2f}分 (期望: {expected:.2f}分) - {'✅' if abs(score - expected) < 0.01 else '❌'}")
    print()

def test_likes_score_formula():
    """测试总点赞数评分公式"""
    calculator = AccountQualityCalculator()
    
    print("=== 总点赞数评分测试 ===")
    print("公式: min(log10(total_likes) * 12.5, 100)")
    print("权重: 40%")
    print()
    
    test_cases = [
        (500, "500点赞"),
        (1000, "1K点赞"),
        (5000, "5K点赞"),
        (10000, "10K点赞"),
        (50000, "50K点赞"),
        (100000, "100K点赞"),
        (500000, "500K点赞"),
        (1000000, "1M点赞"),
        (5000000, "5M点赞"),
        (10000000, "10M点赞")
    ]
    
    for likes, desc in test_cases:
        score = calculator.calculate_likes_score(likes)
        expected = min(math.log10(likes) * 12.5, 100)
        print(f"{desc}: {score:.2f}分 (期望: {expected:.2f}分) - {'✅' if abs(score - expected) < 0.01 else '❌'}")
    print()

def test_posting_score_formula():
    """测试发布频率评分公式"""
    calculator = AccountQualityCalculator()
    
    print("=== 发布频率评分测试 ===")
    print("公式: max(0, 100 - abs(weekly_frequency - 5) * 15)")
    print("权重: 20%")
    print("理想频次: 5次/周")
    print()
    
    # 创建不同发布频率的测试视频
    now = datetime.now()
    
    test_frequencies = [
        (1, "每周1个"),
        (3, "每周3个"),
        (5, "每周5个"),
        (7, "每周7个"),
        (9, "每周9个")
    ]
    
    for weekly_freq, desc in test_frequencies:
        # 创建4周内的视频数据
        videos = []
        total_videos = weekly_freq * 4  # 4周的视频总数
        
        for i in range(total_videos):
            video_time = now - timedelta(days=i * 7 / weekly_freq)  # 均匀分布在4周内
            videos.append(VideoDetail(
                video_id=f"test_{i}",
                desc=f"测试视频{i}",
                create_time=video_time,
                author_id="test_author",
                view_count=1000,
                like_count=50,
                comment_count=10,
                share_count=5,
                download_count=0,
                collect_count=2
            ))
        
        score = calculator.calculate_posting_score(videos)
        expected = max(0, 100 - abs(weekly_freq - 5) * 15)
        print(f"{desc}: {score:.2f}分 (期望: {expected:.2f}分) - {'✅' if abs(score - expected) < 5 else '❌'}")
    print()

def test_weight_distribution():
    """测试权重分配"""
    calculator = AccountQualityCalculator()
    
    print("=== 权重分配测试 ===")
    print("粉丝数量: 40%")
    print("总点赞数: 40%")
    print("发布频率: 20%")
    print()
    
    # 创建测试用户档案
    user_profile = UserProfile(
        user_id="test_user",
        username="test_user",
        display_name="测试用户",
        follower_count=10000,  # 应该得到40分
        following_count=100,
        total_likes=10000,     # 应该得到50分
        video_count=50,
        bio="测试用户",
        avatar_url="",
        verified=False
    )
    
    # 创建理想发布频率的视频（每周5个）
    now = datetime.now()
    videos = []
    for i in range(20):  # 4周，每周5个
        video_time = now - timedelta(days=i * 1.4)  # 每1.4天一个视频
        videos.append(VideoDetail(
            video_id=f"test_{i}",
            desc=f"测试视频{i}",
            create_time=video_time,
            author_id="test_author",
            view_count=1000,
            like_count=50,
            comment_count=10,
            share_count=5,
            download_count=0,
            collect_count=2
        ))
    
    result = calculator.calculate_account_quality(user_profile, videos)
    
    print(f"粉丝得分: {result.follower_score:.2f}分")
    print(f"点赞得分: {result.likes_score:.2f}分")
    print(f"发布得分: {result.posting_score:.2f}分")
    print(f"总分: {result.total_score:.2f}分")
    
    # 验证权重计算
    expected_total = result.follower_score * 0.4 + result.likes_score * 0.4 + result.posting_score * 0.2
    print(f"期望总分: {expected_total:.2f}分")
    print(f"权重计算: {'✅' if abs(result.total_score - expected_total) < 0.01 else '❌'}")
    print()

if __name__ == "__main__":
    print("账户质量评分公式验证")
    print("=" * 50)
    print()
    
    test_follower_score_formula()
    test_likes_score_formula()
    test_posting_score_formula()
    test_weight_distribution()
    
    print("测试完成！")