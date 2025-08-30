"""TikTok创作者评分系统使用示例"""

import json
import logging
from typing import List

from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient
from models import CreatorScore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def username_to_secuid_example():
    """用户名转换secUid示例"""
    print("\n=== 用户名转换secUid示例 ===")
    
    # 初始化API客户端
    api_client = TiKhubAPIClient()
    
    # 示例用户名（请替换为实际的TikTok用户名）
    username = "taylorswift"
    
    try:
        # 通过用户名获取secUid
        print(f"正在获取用户 {username} 的secUid...")
        sec_uid = api_client.get_secuid_from_username(username)
        
        if sec_uid:
            print(f"✅ 成功获取secUid: {sec_uid}")
            print(f"现在可以使用这个secUid进行评分计算")
        else:
            print(f"❌ 无法获取用户 {username} 的secUid")
            print("可能的原因: 用户名不存在、网络问题或API限制")
        
    except Exception as e:
        print(f"获取secUid时发生错误: {e}")
        logger.error(f"用户名转换示例失败: {e}")

def single_creator_example():
    """单个创作者评分示例"""
    print("\n=== 单个创作者评分示例 ===")
    
    # 初始化评分计算器
    calculator = CreatorScoreCalculator()
    
    # 示例secUid（请替换为实际的TikTok secUid）
    sec_uid = "MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM"
    
    try:
        # 计算创作者评分
        print(f"正在计算secUid {sec_uid} 的评分...")
        creator_score = calculator.calculate_creator_score_by_user_id(
            user_id=sec_uid,
            video_count=5  # 分析最新5个视频
        )
        
        # 显示评分结果
        print(f"\n用户的评分结果：")
        print(f"最终评分: {creator_score.final_score:.2f}")
        print(f"账户质量分: {creator_score.account_quality.total_score:.2f}")
        print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}")
        print(f"质量加权系数: {creator_score.account_quality.multiplier}")
        print(f"分析视频数量: {creator_score.video_count}")
        
        # 获取详细分解
        breakdown = calculator.get_score_breakdown(creator_score)
        print("\n详细评分分解:")
        print(json.dumps(breakdown, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"计算评分时发生错误: {e}")
        logger.error(f"单个创作者评分示例失败: {e}")

def batch_creators_example():
    """批量创作者评分示例"""
    print("\n=== 批量创作者评分示例 ===")
    
    # 初始化评分计算器
    calculator = CreatorScoreCalculator()
    
    # 示例secUid列表（请替换为实际的TikTok secUid）
    sec_uids = [
        "MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM",
        "MS4wLjABAAAA_example_secuid_2", 
        "MS4wLjABAAAA_example_secuid_3"
    ]
    
    try:
        # 批量计算评分
        print(f"正在批量计算 {len(sec_uids)} 个创作者的评分...")
        creator_scores = []
        
        for i, sec_uid in enumerate(sec_uids, 1):
            try:
                print(f"正在计算第 {i} 个创作者...")
                score = calculator.calculate_creator_score_by_user_id(
                    user_id=sec_uid,
                    video_count=5  # 每个用户分析5个视频
                )
                creator_scores.append(score)
            except Exception as e:
                print(f"计算第 {i} 个创作者失败: {e}")
                continue
        
        if creator_scores:
            # 比较创作者
            comparison = calculator.compare_creators(creator_scores)
            
            print("\n创作者评分排名:")
            for creator in comparison:
                print(f"{creator['排名']}. {creator['用户名']} - {creator['最终评分']}分")
                
            print("\n详细比较结果:")
            print(json.dumps(comparison, ensure_ascii=False, indent=2))
        else:
            print("没有成功计算出任何创作者的评分")
            
    except Exception as e:
        print(f"批量计算评分时发生错误: {e}")
        logger.error(f"批量创作者评分示例失败: {e}")

def api_client_example():
    """API客户端使用示例"""
    print("\n=== API客户端使用示例 ===")
    
    # 初始化API客户端
    api_client = TiKhubAPIClient()
    
    sec_uid = "MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM"
    
    try:
        # 获取用户档案
        print(f"正在获取secUid {sec_uid} 的档案信息...")
        user_profile = api_client.fetch_user_profile(sec_uid)
        
        print(f"\n用户档案信息:")
        print(f"用户名: {user_profile.username}")
        print(f"粉丝数: {user_profile.follower_count:,}")
        print(f"总点赞数: {user_profile.total_likes:,}")
        print(f"视频数量: {user_profile.video_count}")
        
        # 获取用户视频列表
        print(f"\n正在获取用户视频列表...")
        video_list = api_client.fetch_user_videos(sec_uid, count=5)
        print(f"获取到 {len(video_list)} 个视频ID")
        
        # 获取第一个视频的详情
        if video_list:
            video_id = video_list[0]
            print(f"\n正在获取视频 {video_id} 的详情...")
            video_detail = api_client.fetch_video_detail(video_id)
            
            print(f"视频详情:")
            print(f"视频ID: {video_detail.video_id}")
            print(f"播放量: {video_detail.view_count:,}")
            print(f"点赞数: {video_detail.like_count:,}")
            print(f"评论数: {video_detail.comment_count:,}")
            print(f"分享数: {video_detail.share_count:,}")
            
    except Exception as e:
        print(f"API调用时发生错误: {e}")
        logger.error(f"API客户端示例失败: {e}")

def manual_calculation_example():
    """手动数据计算示例"""
    print("\n=== 手动数据计算示例 ===")
    
    from models import UserProfile, VideoDetail
    from account_quality_calculator import AccountQualityCalculator
    from content_interaction_calculator import ContentInteractionCalculator
    
    # 创建示例数据
    user_profile = UserProfile(
        username="example_user",
        follower_count=50000,
        total_likes=1000000,
        video_count=100
    )
    
    video_details = [
        VideoDetail(
            video_id="video1",
            view_count=100000,
            like_count=5000,
            comment_count=500,
            share_count=200
        ),
        VideoDetail(
            video_id="video2",
            view_count=80000,
            like_count=4000,
            comment_count=400,
            share_count=150
        ),
        VideoDetail(
            video_id="video3",
            view_count=120000,
            like_count=6000,
            comment_count=600,
            share_count=250
        )
    ]
    
    # 计算账户质量评分
    account_calculator = AccountQualityCalculator()
    account_quality = account_calculator.calculate_account_quality(
        user_profile, video_details
    )
    
    print(f"账户质量评分:")
    print(f"粉丝数量得分: {account_quality.follower_score:.2f}")
    print(f"总点赞得分: {account_quality.likes_score:.2f}")
    print(f"发布频率得分: {account_quality.posting_score:.2f}")
    print(f"账户质量总分: {account_quality.total_score:.2f}")
    print(f"质量加权系数: {account_quality.multiplier}")
    
    # 计算内容互动评分
    content_calculator = ContentInteractionCalculator()
    content_interaction = content_calculator.calculate_weighted_content_score(
        video_details, user_profile.follower_count
    )
    
    print(f"\n内容互动评分:")
    print(f"播放量得分: {content_interaction.view_score:.2f}")
    print(f"点赞得分: {content_interaction.like_score:.2f}")
    print(f"评论得分: {content_interaction.comment_score:.2f}")
    print(f"分享得分: {content_interaction.share_score:.2f}")
    print(f"内容互动总分: {content_interaction.total_score:.2f}")
    
    # 使用评分计算器计算最终评分
    calculator = CreatorScoreCalculator()
    creator_score = calculator.calculate_creator_score_from_data(
        user_profile, video_details
    )
    
    print(f"\n最终评分: {creator_score.final_score:.2f}")

def user_id_example():
    """通过用户ID计算评分示例"""
    print("\n=== 通过secUid计算评分示例 ===")
    
    # 初始化评分计算器
    calculator = CreatorScoreCalculator()
    
    # 示例secUid（请替换为实际的TikTok secUid）
    user_id = "MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM"
    
    try:
        # 通过secUid计算创作者评分
        print(f"正在通过secUid {user_id} 计算评分...")
        creator_score = calculator.calculate_creator_score_by_user_id(
            user_id=user_id,
            video_count=5  # 分析最新5个视频
        )
        
        # 显示评分结果
        print(f"\n用户的评分结果：")
        print(f"最终评分: {creator_score.final_score:.2f}")
        print(f"账户质量分: {creator_score.account_quality.total_score:.2f}")
        print(f"内容互动分: {creator_score.content_interaction.total_score:.2f}")
        print(f"质量加权系数: {creator_score.account_quality.multiplier}")
        print(f"分析视频数量: {creator_score.video_count}")
        
        # 获取详细分解
        breakdown = calculator.get_score_breakdown(creator_score)
        print("\n详细评分分解:")
        print(json.dumps(breakdown, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"通过secUid计算评分时发生错误: {e}")
        logger.error(f"secUid评分示例失败: {e}")

def main():
    """主函数 - 运行所有示例"""
    print("TikTok创作者评分系统使用示例")
    print("=" * 50)
    
    # 注意：在实际使用前，请确保：
    # 1. 已正确配置API密钥
    # 2. 替换示例中的secUid为真实的TikTok数据
    # 3. 确保网络连接正常
    
    try:
        # 运行手动计算示例（不需要API调用）
        manual_calculation_example()
        
        # 运行用户名转换示例
        print("\n注意：以下示例需要网络连接")
        username_to_secuid_example()
        
        # 运行API相关示例（需要有效的API密钥和网络连接）
        print("\n注意：以下示例需要有效的API密钥和网络连接")
        print("如果没有配置API密钥，这些示例将会失败")
        
        # 取消注释以下行来运行API示例
        # api_client_example()
        # single_creator_example()
        # user_id_example()  # secUid评分示例
        # batch_creators_example()
        
        print("\n所有示例运行完成！")
        
    except Exception as e:
        print(f"运行示例时发生错误: {e}")
        logger.error(f"主函数执行失败: {e}")

if __name__ == "__main__":
    # 运行示例
    main()