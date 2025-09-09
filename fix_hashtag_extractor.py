#!/usr/bin/env python3
"""
修正版本：为每个用户的每个hashtag创建单独行，并添加对应的视频链接
"""

import pandas as pd
import re
import logging
from typing import List, Set, Dict
from api_client import TiKhubAPIClient
from config import Config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_hashtags_from_text(text: str) -> Set[str]:
    """从文本中提取hashtag
    
    Args:
        text: 包含hashtag的文本
        
    Returns:
        hashtag集合
    """
    if not text:
        return set()
    
    # 使用正则表达式匹配hashtag模式
    # 支持中文、英文、数字、下划线等字符
    hashtag_pattern = r'#([a-zA-Z0-9_\u4e00-\u9fff]+)'
    hashtags = re.findall(hashtag_pattern, text)
    
    # 转换为小写并去重
    return {tag.lower() for tag in hashtags}

def build_tiktok_video_url(video_id: str) -> str:
    """构建TikTok视频链接
    
    Args:
        video_id: 视频ID
        
    Returns:
        TikTok视频链接
    """
    return f"https://www.tiktok.com/@user/video/{video_id}"

def main():
    """主函数"""
    try:
        logger.info("开始hashtag提取任务（新格式：每个hashtag一行）...")
        
        # 1. 读取leaderboard表格
        logger.info("读取leaderboard.xlsx...")
        df = pd.read_excel('leaderboard.xlsx')
        
        # 备份原始文件
        df.to_excel('leaderboard_backup.xlsx', index=False)
        logger.info("已创建备份文件: leaderboard_backup.xlsx")
        
        # 2. 确定username列名
        username_column = None
        for col in df.columns:
            if 'username' in str(col).lower():
                username_column = col
                break
        
        if username_column is None:
            logger.error("未找到username列")
            return
        
        logger.info(f"找到username列: {username_column}")
        
        # 3. 获取所有用户名
        usernames = df[username_column].dropna().tolist()
        logger.info(f"提取到{len(usernames)}个用户名")
        
        # 4. 初始化API客户端
        api_client = TiKhubAPIClient()
        
        # 5. 新的数据结构：每个hashtag一行
        result_data = []
        
        # 处理所有用户
        for i, username in enumerate(usernames, 1):
            try:
                logger.info(f"\n[{i}/{len(usernames)}] 处理用户: {username}")
                
                # 获取用户最新100个视频
                logger.info(f"正在获取用户 {username} 的最新100个视频...")
                videos = api_client.fetch_user_videos_by_username(username, count=100)
                
                if not videos:
                    logger.warning(f"用户 {username} 未获取到视频数据")
                    # 为没有视频的用户创建一个空行
                    result_data.append({
                        'username': username,
                        'hashtag': '',
                        'video_links': ''
                    })
                    continue
                
                # 获取用户的原始数据
                user_row = df[df[username_column] == username]
                if len(user_row) == 0:
                    logger.warning(f"在Excel中找不到用户 {username}")
                    continue
                
                user_data = user_row.iloc[0].to_dict()
                
                # 为该用户创建hashtag到视频链接的映射
                hashtag_to_videos: Dict[str, List[str]] = {}
                
                for video in videos:
                    if hasattr(video, 'desc') and hasattr(video, 'video_id'):
                        # VideoDetail对象
                        desc = video.desc or ''
                        video_id = video.video_id
                    elif isinstance(video, dict):
                        # 字典格式
                        desc = video.get('desc', '') or ''
                        video_id = video.get('id', '') or video.get('video_id', '') or video.get('aweme_id', '')
                    else:
                        continue
                    
                    if not video_id:
                        continue
                        
                    # 提取该视频的hashtag
                    hashtags = extract_hashtags_from_text(desc)
                    video_url = build_tiktok_video_url(video_id)
                    
                    # 将视频链接添加到对应的hashtag中
                    for hashtag in hashtags:
                        if hashtag not in hashtag_to_videos:
                            hashtag_to_videos[hashtag] = []
                        hashtag_to_videos[hashtag].append(video_url)
                
                # 为该用户的每个hashtag创建一行数据
                if hashtag_to_videos:
                    for hashtag, video_urls in hashtag_to_videos.items():
                        # 去重并排序视频链接
                        unique_urls = list(set(video_urls))
                        unique_urls.sort()
                        video_links_str = ', '.join(unique_urls)
                        
                        # 复制用户原始数据并添加hashtag信息
                        row_data = user_data.copy()
                        # 移除不需要的hashtags列（如果存在）
                        if 'hashtags' in row_data:
                            del row_data['hashtags']
                        row_data['hashtag'] = hashtag
                        row_data['video_links'] = video_links_str
                        result_data.append(row_data)
                    
                    logger.info(f"用户 {username} 提取到 {len(hashtag_to_videos)} 个唯一hashtag")
                else:
                    # 用户有视频但没有hashtag
                    row_data = user_data.copy()
                    # 移除不需要的hashtags列（如果存在）
                    if 'hashtags' in row_data:
                        del row_data['hashtags']
                    row_data['hashtag'] = ''
                    row_data['video_links'] = ''
                    result_data.append(row_data)
                    logger.info(f"用户 {username} 没有找到hashtag")
                
            except Exception as e:
                logger.error(f"处理用户 {username} 时出错: {e}")
                # 为出错的用户创建一个空行
                user_row = df[df[username_column] == username]
                if len(user_row) > 0:
                    user_data = user_row.iloc[0].to_dict()
                    row_data = user_data.copy()
                    # 移除不需要的hashtags列（如果存在）
                    if 'hashtags' in row_data:
                        del row_data['hashtags']
                    row_data['hashtag'] = ''
                    row_data['video_links'] = ''
                    result_data.append(row_data)
                continue
        
        # 6. 创建新的DataFrame，每个hashtag一行
        if result_data:
            new_df = pd.DataFrame(result_data)
            
            # 7. 保存新的文件格式
            new_df.to_excel('leaderboard_hashtags.xlsx', index=False)
            logger.info("结果已保存到: leaderboard_hashtags.xlsx（每个hashtag一行）")
            
            # 保持原文件不变
            logger.info("原文件 leaderboard.xlsx 保持不变")
        
        # 8. 显示统计信息
        if result_data:
            total_rows = len(result_data)
            unique_users = len(set(row['username'] for row in result_data))
            total_hashtags = len([row for row in result_data if row['hashtag']])
            logger.info(f"任务完成！")
            logger.info(f"- 原始用户数: {len(df)}")
            logger.info(f"- 处理用户数: {unique_users}")
            logger.info(f"- 总行数（每个hashtag一行）: {total_rows}")
            logger.info(f"- 有效hashtag行数: {total_hashtags}")
            
            # 显示前几行结果
            logger.info("\n新格式前几行预览（每个hashtag一行）:")
            new_df = pd.DataFrame(result_data)
            for i, (_, row) in enumerate(new_df[['username', 'hashtag', 'video_links']].head().iterrows(), 1):
                hashtag = str(row['hashtag'])[:30] + '...' if len(str(row['hashtag'])) > 30 else str(row['hashtag'])
                video_links = str(row['video_links'])[:50] + '...' if len(str(row['video_links'])) > 50 else str(row['video_links'])
                logger.info(f"  {i}. {row['username']} | {hashtag} | {video_links}")
        else:
            logger.warning("没有生成任何数据")
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise

if __name__ == "__main__":
    main()
