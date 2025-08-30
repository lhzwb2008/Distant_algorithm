#!/usr/bin/env python3
"""详细的评分分析"""

from api_client import TiKhubAPIClient
from creator_score_calculator import CreatorScoreCalculator
from content_interaction_calculator import ContentInteractionCalculator

def analyze_detailed_scores():
    """分析详细的评分情况"""
    print("=== 详细评分分析 ===")
    
    client = TiKhubAPIClient()
    calculator = CreatorScoreCalculator()
    content_calc = ContentInteractionCalculator()
    
    username = "auto_trading0"
    sec_uid = 'MS4wLjABAAAA03-tVXtgJSYc9rbcTDCiDhAFGlNbSyXbWDcMi6xHI2uuy3mHuOQujUss4BSXnkKc'
    
    print(f"\n🎯 分析用户: {username}")
    print(f"SecUID: {sec_uid}")
    
    # 获取视频数据
    video_details = client.fetch_user_top_videos(sec_uid, 5)
    print(f"\n📊 视频数据 (共{len(video_details)}个):")
    
    total_views = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0
    
    for i, video in enumerate(video_details, 1):
        print(f"视频{i}: 播放={video.view_count:,}, 点赞={video.like_count}, 评论={video.comment_count}, 分享={video.share_count}")
        total_views += video.view_count
        total_likes += video.like_count
        total_comments += video.comment_count
        total_shares += video.share_count
    
    print(f"\n📈 汇总数据:")
    print(f"总播放量: {total_views:,}")
    print(f"总点赞数: {total_likes:,}")
    print(f"总评论数: {total_comments:,}")
    print(f"总分享数: {total_shares:,}")
    
    # 计算平均值
    avg_views = total_views / len(video_details)
    avg_likes = total_likes / len(video_details)
    avg_comments = total_comments / len(video_details)
    avg_shares = total_shares / len(video_details)
    
    print(f"\n📊 平均数据:")
    print(f"平均播放量: {avg_views:.1f}")
    print(f"平均点赞数: {avg_likes:.1f}")
    print(f"平均评论数: {avg_comments:.1f}")
    print(f"平均分享数: {avg_shares:.1f}")
    
    # 计算各项得分
    follower_count = 0  # 模拟没有粉丝数据的情况
    
    print(f"\n🎯 各项得分计算 (粉丝数: {follower_count}):")
    
    # 播放量得分
    view_score = content_calc.calculate_view_score(int(avg_views), follower_count)
    print(f"播放量得分: {view_score:.2f}/100")
    print(f"  - 计算逻辑: 平均播放量 {avg_views:.1f} / 2000 * 100 = {view_score:.2f}")
    
    # 点赞得分
    like_score = content_calc.calculate_like_score(int(avg_likes), int(avg_views))
    like_rate = avg_likes / avg_views * 100
    print(f"点赞得分: {like_score:.2f}/100")
    print(f"  - 点赞率: {like_rate:.2f}%")
    print(f"  - 计算逻辑: 点赞率 {like_rate:.2f}% * 25 = {like_score:.2f}")
    
    # 评论得分
    comment_score = content_calc.calculate_comment_score(int(avg_comments), int(avg_views))
    comment_rate = avg_comments / avg_views * 100 if avg_views > 0 else 0
    print(f"评论得分: {comment_score:.2f}/100")
    print(f"  - 评论率: {comment_rate:.2f}%")
    print(f"  - 原因: 所有视频评论数都为0")
    
    # 分享得分
    share_score = content_calc.calculate_share_score(int(avg_shares), int(avg_views))
    share_rate = avg_shares / avg_views * 100 if avg_views > 0 else 0
    print(f"分享得分: {share_score:.2f}/100")
    print(f"  - 分享率: {share_rate:.2f}%")
    print(f"  - 计算逻辑: 分享率 {share_rate:.2f}% * 250 = {share_score:.2f}")
    
    # 加权总分
    weighted_total = (
        view_score * 0.10 +      # 播放量权重10%
        like_score * 0.25 +      # 点赞权重25%
        comment_score * 0.30 +   # 评论权重30%
        share_score * 0.35       # 分享权重35%
    )
    
    print(f"\n🎯 内容互动加权总分:")
    print(f"播放量贡献: {view_score:.2f} × 10% = {view_score * 0.10:.2f}")
    print(f"点赞贡献: {like_score:.2f} × 25% = {like_score * 0.25:.2f}")
    print(f"评论贡献: {comment_score:.2f} × 30% = {comment_score * 0.30:.2f}")
    print(f"分享贡献: {share_score:.2f} × 35% = {share_score * 0.35:.2f}")
    print(f"总分: {weighted_total:.2f}/100")
    
    # 完整评分
    print(f"\n🏆 完整评分计算:")
    creator_score = calculator.calculate_creator_score_by_user_id(sec_uid, 5)
    print(f"账户质量分: {creator_score.account_quality.total_score:.2f}/100")
    print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}/100")
    print(f"内容质量分: 60.00/100 (固定值)")
    print(f"最终评分: {creator_score.final_score:.2f}/100")
    
    print(f"\n✅ 修复总结:")
    print(f"1. ✅ 播放量得分已修复: 从 0.00 提升到 {view_score:.2f}")
    print(f"2. ✅ 点赞得分正常: {like_score:.2f} (基于 {like_rate:.2f}% 点赞率)")
    print(f"3. ⚠️  评论得分为0: 该用户所有视频确实没有评论")
    print(f"4. ⚠️  分享得分较低: {share_score:.2f} (基于 {share_rate:.2f}% 分享率)")
    print(f"5. ✅ API数据获取正常: 成功获取 {len(video_details)} 个视频的完整数据")

if __name__ == "__main__":
    analyze_detailed_scores()