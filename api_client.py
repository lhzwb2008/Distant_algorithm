"""TiKhub API客户端"""

import requests
import time
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import Config
from models import UserProfile, VideoMetrics, VideoDetail, VideoSubtitle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TiKhubAPIClient:
    """TiKhub API客户端类"""
    
    def __init__(self, api_key: str = None):
        """初始化API客户端
        
        Args:
            api_key: API密钥，如果不提供则使用配置文件中的默认值
        """
        self.api_key = api_key or Config.TIKHUB_API_KEY
        self.base_url = Config.TIKHUB_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'TikTok-Creator-Score/1.0.0'
        })
        
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            API响应数据
            
        Raises:
            requests.RequestException: 请求失败时抛出异常
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(Config.TIKHUB_MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=Config.TIKHUB_REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"API响应: {data}")
                
                # TikHub API通常返回code=200表示成功
                if data.get('code') == 200:  # 成功响应
                    return data.get('data', {})
                elif data.get('code') == 0:  # 也可能是0表示成功
                    return data.get('data', {})
                else:
                    error_msg = data.get('message', '未知错误')
                    logger.error(f"API返回错误 (code: {data.get('code')}): {error_msg}")
                    raise requests.RequestException(f"API错误: {error_msg}")
                    
            except requests.RequestException as e:
                # 生成curl命令供调试
                curl_command = self._generate_curl_command(url, params)
                
                # 对于分页请求的400错误，可能是cursor无效，不需要重试太多次
                if "400 Client Error" in str(e) and "cursor=" in str(params):
                    logger.warning(f"分页请求失败 (尝试 {attempt + 1}/{Config.TIKHUB_MAX_RETRIES}): {e}")
                    logger.warning(f"🐛 调试用curl命令:\n{curl_command}")
                    # 对于分页400错误，只重试3次就放弃
                    if attempt >= 2:
                        logger.warning(f"分页请求连续失败，可能已到达数据边界或cursor无效")
                        raise e
                else:
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{Config.TIKHUB_MAX_RETRIES}): {e}")
                    logger.warning(f"🐛 调试用curl命令:\n{curl_command}")
                    if attempt == Config.TIKHUB_MAX_RETRIES - 1:
                        logger.error(f"API请求失败，已重试{Config.TIKHUB_MAX_RETRIES}次，抛出异常")
                        raise e
                # 实现智能重试延迟
                if Config.ERROR_HANDLING.get('exponential_backoff', False):
                    # 指数退避策略，适应分钟级限流
                    base_delay = Config.ERROR_HANDLING['retry_delay']
                    backoff_factor = Config.ERROR_HANDLING.get('backoff_factor', 1.5)
                    max_delay = Config.ERROR_HANDLING.get('max_delay', 30)
                    
                    # 计算延迟时间：基础延迟 * (退避因子 ^ 尝试次数)
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    # 对于400错误（通常是限流），使用更长的延迟
                    if "400 Client Error" in str(e):
                        delay = max(delay, 5)  # 至少5秒
                        if attempt >= 10:  # 第10次重试后，使用更长延迟
                            delay = max(delay, 15)  # 至少15秒
                        if attempt >= 15:  # 第15次重试后，使用最长延迟
                            delay = max(delay, 25)  # 至少25秒
                    
                    logger.info(f"等待 {delay:.1f} 秒后进行第 {attempt + 2} 次重试...")
                    time.sleep(delay)
                else:
                    # 原有的线性延迟
                    time.sleep(Config.ERROR_HANDLING['retry_delay'] * (attempt + 1))
    
    def _generate_curl_command(self, url: str, params: Dict[str, Any] = None) -> str:
        """生成curl命令供调试使用"""
        import urllib.parse
        
        # 构建完整URL
        if params:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url
        
        # 构建curl命令 - 单行格式便于复制
        headers = []
        for key, value in self.session.headers.items():
            headers.append(f'-H "{key}: {value}"')
        
        # 添加常用的curl选项
        curl_command = f'curl -X GET "{full_url}" {" ".join(headers)} --compressed | jq .'
        
        return curl_command
                
    def fetch_user_profile(self, username_or_secuid: str) -> UserProfile:
        """获取用户档案信息
        
        Args:
            username_or_secuid: TikTok用户名或secUid
            
        Returns:
            用户档案数据
        """
        # 尝试使用secUid参数
        if username_or_secuid.startswith('MS4wLjABAAAA'):
            # 这是secUid格式
            params = {'secUid': username_or_secuid}
        else:
            # 这是用户名格式
            params = {'username': username_or_secuid}
        
        data = self._make_request(Config.USER_PROFILE_ENDPOINT, params)
        
        # 解析API响应数据结构
        user_info = data.get('userInfo', {}) if isinstance(data, dict) else {}
        user_data = user_info.get('user', {}) if isinstance(user_info, dict) else {}
        stats_data = user_info.get('stats', {}) if isinstance(user_info, dict) else {}
        
        # 确保user_data和stats_data是字典类型
        if not isinstance(user_data, dict):
            user_data = {}
        if not isinstance(stats_data, dict):
            stats_data = {}
        
        # 安全获取avatar_url
        avatar_url = ''
        if isinstance(user_data.get('avatarThumb'), dict):
            url_list = user_data['avatarThumb'].get('urlList', [])
            if isinstance(url_list, list) and len(url_list) > 0:
                avatar_url = url_list[0]
        
        return UserProfile(
            user_id=user_data.get('id', ''),
            username=user_data.get('uniqueId', ''),
            display_name=user_data.get('nickname', ''),
            follower_count=stats_data.get('followerCount', 0),
            following_count=stats_data.get('followingCount', 0),
            total_likes=stats_data.get('heartCount', 0),  # 使用heartCount作为总点赞数
            video_count=stats_data.get('videoCount', 0),
            bio=user_data.get('signature', ''),
            avatar_url=avatar_url,
            verified=user_data.get('verified', False)
        )
        
    def fetch_video_metrics(self, video_id: str) -> VideoMetrics:
        """获取视频指标数据
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频指标数据
        """
        params = {'video_id': video_id}
        data = self._make_request(Config.VIDEO_METRICS_ENDPOINT, params)
        
        return VideoMetrics(
            video_id=video_id,
            view_count=data.get('play_count', 0),
            like_count=data.get('digg_count', 0),
            comment_count=data.get('comment_count', 0),
            share_count=data.get('share_count', 0),
            collect_count=data.get('collect_count', 0)
        )
        
    def fetch_video_detail(self, video_id: str) -> VideoDetail:
        """获取视频详情
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频详情数据
        """
        params = {'aweme_id': video_id}
        data = self._make_request(Config.VIDEO_DETAIL_ENDPOINT, params)
        
        aweme_detail = data.get('aweme_detail', {})
        statistics = aweme_detail.get('statistics', {})
        
        # 从已有的API响应中提取字幕信息（避免重复API调用）
        subtitle = self._extract_subtitle_from_response(video_id, aweme_detail)
        
        return VideoDetail(
            video_id=video_id,
            desc=aweme_detail.get('desc', ''),
            create_time=datetime.fromtimestamp(aweme_detail.get('create_time', 0)),
            author_id=aweme_detail.get('author', {}).get('uid', ''),
            view_count=statistics.get('play_count', 0),
            like_count=statistics.get('digg_count', 0),
            comment_count=statistics.get('comment_count', 0),
            share_count=statistics.get('share_count', 0),
            download_count=statistics.get('download_count', 0),
            collect_count=statistics.get('collect_count', 0),
            duration=aweme_detail.get('duration', 0) / 1000.0,  # 转换为秒
            subtitle=subtitle
        )
        
    def fetch_user_videos(self, user_id: str, count: int = 10) -> List[str]:
        """获取用户视频列表
        
        Args:
            user_id: 用户ID (实际使用secUid)
            count: 获取视频数量
            
        Returns:
            视频ID列表
        """
        params = {
            'secUid': user_id,  # API使用secUid参数
            'count': count
        }
        
        try:
            data = self._make_request(Config.USER_VIDEOS_ENDPOINT, params)
            logger.info(f"API响应数据结构键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            logger.debug(f"API响应数据结构: {data}")
            
            # 尝试多种可能的数据结构
            videos = []
            
            # 尝试格式1: data.itemList (最常见的格式)
            if 'itemList' in data:
                videos = data['itemList']
                logger.debug(f"使用格式1获取到 {len(videos)} 个视频")
            # 尝试格式2: data.data.itemList
            elif 'data' in data and 'itemList' in data['data']:
                videos = data['data']['itemList']
                logger.debug(f"使用格式2获取到 {len(videos)} 个视频")
            # 尝试格式3: data.aweme_list
            elif 'aweme_list' in data:
                videos = data['aweme_list']
                logger.debug(f"使用格式3获取到 {len(videos)} 个视频")
            # 尝试格式4: data.data.aweme_list
            elif 'data' in data and 'aweme_list' in data['data']:
                videos = data['data']['aweme_list']
                logger.debug(f"使用格式4获取到 {len(videos)} 个视频")
            else:
                logger.warning(f"未知的API响应格式，可用的键: {list(data.keys())}")
                return []
            
            # 提取视频ID
            video_ids = []
            for video in videos:
                # 尝试多种可能的ID字段
                video_id = video.get('aweme_id') or video.get('id') or video.get('video_id')
                if video_id:
                    video_ids.append(video_id)
                    
            logger.info(f"成功提取到 {len(video_ids)} 个视频ID")
            return video_ids
            
        except Exception as e:
            logger.error(f"获取用户视频列表失败: {e}")
            return []
            
    def fetch_user_top_videos(self, user_id: str, count: int = 5, keyword: str = None) -> List[VideoDetail]:
        """获取用户作品的详细信息
        
        Args:
            user_id: 用户ID (secUid)
            count: 获取作品数量，默认5个（当没有关键词时使用）
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            视频详情列表
        """
        if keyword:
            logger.info(f"开始获取用户 {user_id} 包含关键词 '{keyword}' 的作品")
            # 当有关键词时，需要获取更多视频进行筛选
            max_videos_to_check = Config.CONTENT_INTERACTION_MAX_VIDEOS
            max_pages = max_videos_to_check // 20 + 1  # 计算需要的页数
        else:
            logger.info(f"开始获取用户 {user_id} 的前 {count} 个作品")
            max_pages = 1  # 无关键词时只需要一页
        
        all_videos = []
        cursor = 0
        page = 1
        
        # 分页获取视频
        while page <= max_pages:
            # 直接调用API获取用户视频列表（根据API文档完整配置）
            params = {
                'secUid': user_id,
                'cursor': cursor,
                'count': 20,  # API固定每页20个
                'coverFormat': 2,
                'post_item_list_request_type': 0
            }
            
            try:
                logger.info(f"正在获取第 {page} 页数据 (cursor: {cursor})...")
                # 使用配置中的API端点获取用户视频列表
                data = self._make_request(Config.USER_VIDEOS_ENDPOINT, params)
                
                # 检查API响应状态 - 兼容多种响应格式
                # 添加调试信息
                logger.debug(f"第{page}页API响应状态检查: code={data.get('code')}, statusCode={data.get('statusCode')}")
                
                # 先检查是否成功
                is_success = False
                if data.get('code') == 200:  # 标准格式
                    is_success = True
                elif data.get('statusCode') == 0:  # 旧格式
                    is_success = True
                elif 'data' in data and data.get('statusCode') is None and data.get('code') is None:  # 可能没有状态码但有数据
                    is_success = True
                
                if not is_success:
                    error_msg = data.get('message', data.get('statusMsg', 'Unknown error'))
                    logger.warning(f"第{page}页API返回错误状态: {error_msg}")
                    logger.debug(f"完整响应数据: {data}")
                    break
                
                # 调试：记录API响应结构
                logger.debug(f"第{page}页API响应主要键: {list(data.keys())}")
                if 'data' in data and isinstance(data['data'], dict):
                    logger.debug(f"第{page}页data子级键: {list(data['data'].keys())}")
                
                # 获取视频列表 - 使用与fetch_user_videos相同的逻辑
                videos = []
                
                # 尝试格式1: data.itemList (最常见的格式)
                if 'itemList' in data:
                    videos = data['itemList']
                    logger.debug(f"第{page}页使用格式1获取到 {len(videos)} 个视频")
                # 尝试格式2: data.data.itemList
                elif 'data' in data and 'itemList' in data['data']:
                    videos = data['data']['itemList']
                    logger.debug(f"第{page}页使用格式2获取到 {len(videos)} 个视频")
                # 尝试格式3: data.aweme_list
                elif 'aweme_list' in data:
                    videos = data['aweme_list']
                    logger.debug(f"第{page}页使用格式3获取到 {len(videos)} 个视频")
                # 尝试格式4: data.data.aweme_list
                elif 'data' in data and 'aweme_list' in data['data']:
                    videos = data['data']['aweme_list']
                    logger.debug(f"第{page}页使用格式4获取到 {len(videos)} 个视频")
                else:
                    logger.warning(f"第{page}页未知的API响应格式，可用的键: {list(data.keys())}")
                    break
                
                if not videos:
                    logger.info(f"第{page}页没有更多视频，停止分页")
                    break
                
                all_videos.extend(videos)
                logger.info(f"第{page}页获取到 {len(videos)} 个视频，累计 {len(all_videos)} 个")
                
                # 如果有关键词筛选，检查是否已达到最大视频数量
                if keyword and len(all_videos) >= max_videos_to_check:
                    logger.info(f"已获取 {len(all_videos)} 个视频，达到最大限制 {max_videos_to_check} 个，停止获取更多页面")
                    break
                
                # 更新cursor和页数 - 尝试多种可能的cursor位置
                new_cursor = None
                
                # 根据TikTok API文档优化cursor提取逻辑
                # 优先检查data对象内的cursor相关字段
                if 'data' in data and isinstance(data['data'], dict):
                    data_obj = data['data']
                    if 'cursor' in data_obj:
                        new_cursor = data_obj['cursor']
                        logger.debug(f"找到cursor在data.cursor: {new_cursor}")
                    elif 'max_cursor' in data_obj:
                        new_cursor = data_obj['max_cursor']
                        logger.debug(f"找到max_cursor在data.max_cursor: {new_cursor}")
                    elif 'next_cursor' in data_obj:
                        new_cursor = data_obj['next_cursor']
                        logger.debug(f"找到next_cursor在data.next_cursor: {new_cursor}")
                    else:
                        logger.warning(f"data对象中未找到cursor字段，可用键: {list(data_obj.keys())}")
                # 备用：检查根级别的cursor
                elif 'cursor' in data:
                    new_cursor = data['cursor']
                    logger.debug(f"找到cursor在根级别: {new_cursor}")
                elif 'max_cursor' in data:
                    new_cursor = data['max_cursor']
                    logger.debug(f"找到max_cursor在根级别: {new_cursor}")
                else:
                    logger.warning(f"未找到cursor，API响应的主要键: {list(data.keys())}")
                    if 'data' in data and isinstance(data['data'], dict):
                        logger.warning(f"data子级的键: {list(data['data'].keys())}")
                
                # 确保cursor是整数
                if new_cursor is not None:
                    if isinstance(new_cursor, str):
                        try:
                            new_cursor = int(new_cursor)
                        except ValueError:
                            logger.warning(f"Cursor不是有效数字: {new_cursor}")
                            new_cursor = None
                
                # 如果没有找到有效的cursor，检查是否还有更多数据
                if new_cursor is None:
                    has_more = False
                    # 优先检查data对象内的has_more字段
                    if 'data' in data and isinstance(data['data'], dict) and 'has_more' in data['data']:
                        has_more = data['data']['has_more']
                    elif 'has_more' in data:
                        has_more = data['has_more']
                    elif 'data' in data and isinstance(data['data'], dict) and 'hasMore' in data['data']:
                        has_more = data['data']['hasMore']
                    elif 'hasMore' in data:
                        has_more = data['hasMore']
                    
                    if has_more:
                        logger.warning(f"第{page}页：API表示还有更多数据，但未找到有效cursor，停止分页")
                    else:
                        logger.info(f"第{page}页：API表示没有更多数据")
                    break
                
                # 检查cursor是否有效更新
                # 注意：TikTok API的cursor可能是时间戳，按时间倒序排列时会递减
                if new_cursor == cursor:
                    logger.warning(f"Cursor没有变化 (old: {cursor}, new: {new_cursor})，可能已到达数据末尾")
                    break
                else:
                    logger.debug(f"Cursor更新: {cursor} → {new_cursor}")
                
                cursor = new_cursor
                page += 1
                
                # 如果这页视频少于20个，说明已经到最后一页
                if len(videos) < 20:
                    logger.info(f"第{page-1}页视频数量少于20个，已到达最后一页")
                    break
                
                # 添加请求间隔，避免过于频繁的API调用
                if page <= max_pages:
                    time.sleep(0.5)  # 500ms间隔
                    
            except Exception as e:
                if "400 Client Error" in str(e) and page > 1:
                    logger.info(f"第{page}页获取失败，可能已到达数据边界: {e}")
                    logger.info(f"已成功获取前 {page-1} 页数据，停止继续分页")
                    break
                else:
                    logger.error(f"第{page}页获取失败: {e}")
                    break
        
        logger.info(f"分页获取完成，总共获取 {len(all_videos)} 个视频")
        
        # 如果有关键词筛选，确保只处理前100个视频
        if keyword and len(all_videos) > max_videos_to_check:
            all_videos = all_videos[:max_videos_to_check]
            logger.info(f"截取前 {max_videos_to_check} 个视频进行处理，实际处理 {len(all_videos)} 个视频")
        
        # 从视频列表构建VideoDetail对象，并获取额外的指标数据
        video_details = []
        
        # 如果有关键词，先筛选匹配的视频
        if keyword:
            filtered_videos = []
            logger.info(f"🔍 开始筛选包含关键词 '{keyword}' 的视频...")
            for i, video in enumerate(all_videos, 1):
                desc = video.get('desc', '')
                video_id = video.get('id', 'unknown')
                if keyword.lower() in desc.lower():
                    filtered_videos.append(video)
                    # logger.info(f"✅ 第{i}个视频匹配关键词 '{keyword}':")
                    # logger.info(f"   📹 视频ID: {video_id}")
                    # logger.info(f"   📝 完整描述: {desc}")
                else:
                    pass
                    # logger.info(f"❌ 第{i}个视频不匹配关键词 '{keyword}':")
                    # logger.info(f"   📹 视频ID: {video_id}")
                    # logger.info(f"   📝 完整描述: {desc}")
            
            logger.info(f"🎯 关键词 '{keyword}' 筛选结果: {len(filtered_videos)}/{len(all_videos)} 个视频匹配")
            
            # 对筛选后的视频进行去重（基于video_id）
            seen_ids = set()
            unique_videos = []
            for video in filtered_videos:
                video_id = video.get('id', '')
                if video_id and video_id not in seen_ids:
                    seen_ids.add(video_id)
                    unique_videos.append(video)
            
            if len(unique_videos) != len(filtered_videos):
                logger.info(f"🔄 视频去重: {len(filtered_videos)} → {len(unique_videos)} 个唯一视频")
            
            videos_to_process = unique_videos
        else:
            # 如果没有关键词，按count截取
            videos_to_process = all_videos[:count]
            
        for video in videos_to_process:
            try:
                video_id = video.get('id', '')
                
                # 从基础API响应获取数据
                base_stats = video.get('stats', {})
                
                # 直接使用基础API数据（video_metrics API暂时不可用）
                view_count = base_stats.get('playCount', 0)
                like_count = base_stats.get('diggCount', 0)
                comment_count = base_stats.get('commentCount', 0)
                share_count = base_stats.get('shareCount', 0)
                collect_count = base_stats.get('collectCount', 0)
                
                # 维度二（内容互动分）需要对匹配关键词的视频提取字幕（如果开关启用）
                if keyword and Config.ENABLE_SUBTITLE_EXTRACTION:
                    # 对匹配关键词的视频进行字幕提取
                    subtitle = self.extract_subtitle_text(video_id)
                else:
                    subtitle = None
                
                video_detail = VideoDetail(
                    video_id=video_id,
                    desc=video.get('desc', ''),
                    create_time=datetime.fromtimestamp(video.get('createTime', 0)),
                    author_id=video.get('author', {}).get('uniqueId', ''),
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                    share_count=share_count,
                    download_count=base_stats.get('downloadCount', 0),  # 下载数只在基础API中有
                    collect_count=collect_count,
                    duration=video.get('video', {}).get('duration', 0),
                    subtitle=subtitle
                )
                video_details.append(video_detail)
                # 记录详细的视频数据
                logger.info(f"成功解析视频 {video_detail.video_id}")
                logger.info(f"  📺 播放: {view_count:,}, 👍 点赞: {like_count:,}, 💬 评论: {comment_count:,}, 🔄 分享: {share_count:,}")
                # logger.info(f"  📝 完整描述: {video_detail.desc}")
                if collect_count > 0:
                    logger.info(f"  ⭐ 收藏: {collect_count:,}")
                
                # 显示字幕信息（如果启用了字幕提取）
                if Config.ENABLE_SUBTITLE_EXTRACTION:
                    if subtitle:
                        logger.info(f"  🎬 字幕: {subtitle.language_code}, {len(subtitle.full_text)}字符 (已获取)")
                    else:
                        logger.info(f"  🎬 字幕: 无字幕或提取失败")
                else:
                    logger.info(f"  🎬 字幕: 已禁用字幕提取 (使用Gemini视频分析)")
                    
            except Exception as e:
                logger.error(f"解析视频数据失败: {e}")
                continue
                    
        logger.info(f"成功获取用户 {user_id} 的 {len(video_details)} 个作品详情")
        return video_details
    
    def get_video_download_url(self, video_id: str) -> Optional[str]:
        """获取视频下载链接（无水印版本）
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频下载URL，失败时返回None
        """
        try:
            logger.info(f"获取视频 {video_id} 的下载链接")
            
            # 调用fetch_one_video API
            params = {
                'aweme_id': video_id,
                'region': 'US',
                'priority_region': 'US'
            }
            
            response = self._make_request('/api/v1/tiktok/app/v3/fetch_one_video', params)
            
            if response and 'aweme_detail' in response:
                aweme_detail = response['aweme_detail']
                
                # 获取视频下载链接
                video_info = aweme_detail.get('video', {})
                download_info = video_info.get('download_no_watermark_addr', {})
                url_list = download_info.get('url_list', [])
                
                if url_list and len(url_list) > 0:
                    download_url = url_list[0]  # 取第一个链接
                    logger.info(f"视频 {video_id} 下载链接获取成功")
                    return download_url
                else:
                    logger.warning(f"视频 {video_id} 没有可用的下载链接")
                    return None
            else:
                logger.warning(f"视频 {video_id} 详情获取失败")
                return None
                
        except Exception as e:
            logger.error(f"获取视频 {video_id} 下载链接失败: {e}")
            return None
    
    def fetch_user_videos_last_3_months(self, user_id: str, max_pages: int = 20, keyword: str = None) -> List[VideoDetail]:
        """获取用户最近三个月的所有视频（支持分页）
        
        Args:
            user_id: 用户ID (secUid)
            max_pages: 最大分页数，防止无限循环
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            最近三个月的视频详情列表
        """
        from datetime import datetime, timedelta
        
        if keyword:
            logger.info(f"开始获取用户 {user_id} 最近三个月包含关键词 '{keyword}' 的所有作品（支持分页）")
        else:
            logger.info(f"开始获取用户 {user_id} 最近三个月的所有作品（支持分页）")
        
        # 计算指定天数前的时间
        now = datetime.now()
        days_ago = now - timedelta(days=Config.ACCOUNT_QUALITY_DAYS)
        logger.info(f"时间范围: {days_ago.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}")
        
        all_videos = []
        cursor = 0
        page = 1
        videos_per_page = 20  # 每页获取20个视频
        
        while page <= max_pages:
            logger.info(f"正在获取第 {page} 页数据 (cursor: {cursor})...")
            
            # 设置分页参数（根据API文档完整配置）
            params = {
                'secUid': user_id,
                'cursor': cursor,
                'count': videos_per_page,
                'coverFormat': 2,
                'post_item_list_request_type': 0
            }
            
            try:
                # 调用API获取当前页数据
                data = self._make_request(Config.USER_VIDEOS_ENDPOINT, params)
                
                # 检查API响应状态（与现有API调用保持一致）
                if not data or data.get('statusCode', 1) != 0:
                    logger.warning(f"第 {page} 页API响应异常: {data.get('statusMsg', 'Unknown error') if data else 'No data'}")
                    break
                
                # 获取视频列表 - 使用与现有代码相同的逻辑
                videos = []
                
                # 尝试格式1: data.itemList (最常见的格式)
                if 'itemList' in data:
                    videos = data['itemList']
                    logger.debug(f"第 {page} 页使用格式1获取到 {len(videos)} 个视频")
                # 尝试格式2: data.data.itemList
                elif 'data' in data and 'itemList' in data['data']:
                    videos = data['data']['itemList']
                    logger.debug(f"第 {page} 页使用格式2获取到 {len(videos)} 个视频")
                # 尝试格式3: data.aweme_list
                elif 'aweme_list' in data:
                    videos = data['aweme_list']
                    logger.debug(f"第 {page} 页使用格式3获取到 {len(videos)} 个视频")
                else:
                    logger.warning(f"第 {page} 页未找到视频数据，尝试的字段: itemList, data.itemList, aweme_list")
                    logger.debug(f"第 {page} 页API响应键: {list(data.keys()) if data else 'None'}")
                
                if not videos:
                    logger.info(f"第 {page} 页没有更多视频，停止分页")
                    break
                
                logger.info(f"第 {page} 页获取到 {len(videos)} 个视频")
                
                # 处理当前页的视频
                page_videos = []
                videos_outside_range = 0
                
                for video in videos:
                    try:
                        # 使用与现有代码相同的字段提取逻辑
                        video_id = video.get('id', '')
                        create_time = datetime.fromtimestamp(video.get('createTime', 0))
                        
                        # 检查视频是否在指定时间范围内
                        if create_time < days_ago:
                            videos_outside_range += 1
                            logger.info(f"视频 {video_id} 创建时间 {create_time.strftime('%Y-%m-%d')} 超出{Config.ACCOUNT_QUALITY_DAYS}天范围，跳过")
                            continue
                        
                        # 关键词筛选（如果提供了关键词）
                        if keyword:
                            desc = video.get('desc', '')
                            if keyword.lower() not in desc.lower():
                                # logger.info(f"❌ 视频 {video_id} 不匹配关键词 '{keyword}':")
                                # logger.info(f"   📝 完整描述: {desc}")
                                continue
                            else:
                                pass
                                # logger.info(f"✅ 视频 {video_id} 匹配关键词 '{keyword}':")
                                # logger.info(f"   📝 完整描述: {desc}")
                        
                        # 从基础API响应获取数据（与现有代码保持一致）
                        base_stats = video.get('stats', {})
                        
                        view_count = base_stats.get('playCount', 0)
                        like_count = base_stats.get('diggCount', 0)
                        comment_count = base_stats.get('commentCount', 0)
                        share_count = base_stats.get('shareCount', 0)
                        collect_count = base_stats.get('collectCount', 0)
                        
                        # 维度一（账户质量分）不需要字幕，设为None
                        subtitle = None
                        
                        video_detail = VideoDetail(
                            video_id=video_id,
                            desc=video.get('desc', ''),
                            create_time=create_time,
                            author_id=video.get('author', {}).get('uniqueId', ''),  # 与现有代码保持一致
                            view_count=view_count,
                            like_count=like_count,
                            comment_count=comment_count,
                            share_count=share_count,
                            download_count=base_stats.get('downloadCount', 0),  # 与现有代码保持一致
                            collect_count=collect_count,
                            duration=video.get('video', {}).get('duration', 0),
                            subtitle=subtitle
                        )
                        page_videos.append(video_detail)
                        
                        logger.info(f"成功解析视频 {video_detail.video_id} (创建时间: {create_time.strftime('%Y-%m-%d')})")
                        
                        # 账户质量分计算不需要字幕信息
                        
                    except Exception as e:
                        logger.error(f"解析视频数据失败: {e}")
                        continue
                
                all_videos.extend(page_videos)
                logger.info(f"第 {page} 页: 解析成功 {len(page_videos)} 个视频，跳过 {videos_outside_range} 个超出范围的视频")
                
                # 如果当前页所有视频都超出时间范围，后续页面也会超出范围
                if len(page_videos) == 0 and videos_outside_range > 0:
                    logger.info(f"第{page}页所有视频都超出90天时间范围，后续页面也会超出范围，停止获取")
                    break
                # 如果当前页大部分视频都超出时间范围，也可能已到达边界
                elif videos_outside_range > len(page_videos) * 0.8 and len(page_videos) > 0:
                    logger.info(f"第{page}页大部分视频超出90天时间范围，可能已接近时间边界，停止获取")
                    break
                
                # 更新分页参数（与现有API保持兼容）
                has_more = data.get('hasMore', False)
                if not has_more:
                    logger.info("API返回 hasMore=false，没有更多数据")
                    break
                
                # 更新cursor用于下一页 - 尝试多种可能的cursor位置
                new_cursor = None
                
                # 尝试不同的cursor位置
                if 'cursor' in data:
                    new_cursor = data['cursor']
                elif 'data' in data and isinstance(data['data'], dict) and 'cursor' in data['data']:
                    new_cursor = data['data']['cursor']
                elif 'max_cursor' in data:
                    new_cursor = data['max_cursor']
                elif 'data' in data and isinstance(data['data'], dict) and 'max_cursor' in data['data']:
                    new_cursor = data['data']['max_cursor']
                
                # 确保cursor是整数类型
                if new_cursor is not None:
                    try:
                        cursor = int(new_cursor)
                    except (ValueError, TypeError):
                        logger.warning(f"无法解析cursor为整数: {new_cursor}，停止分页")
                        break
                else:
                    logger.warning("未找到有效的cursor，停止分页")
                    break
                page += 1
                
                # 短暂延迟避免请求过快
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"获取第 {page} 页数据失败: {e}")
                break
        
        logger.info(f"分页获取完成: 共获取 {len(all_videos)} 个最近三个月的视频（共 {page-1} 页）")
        return all_videos
        
    def get_secuid_from_username(self, username: str) -> Optional[str]:
        """通过用户名获取secUid
        
        Args:
            username: TikTok用户名
            
        Returns:
            secUid字符串，如果获取失败返回None
        """
        try:
            # 使用TikHub搜索用户API
            params = {
                'keyword': username,
                'cursor': 0,
                'search_id': ''
            }
            
            data = self._make_request('/api/v1/tiktok/web/fetch_search_user', params)
            
            if data:
                user_list = data.get('user_list', [])
                
                # 查找完全匹配的用户名
                for user_info in user_list:
                    user = user_info.get('user_info', {})
                    unique_id = user.get('unique_id', '').lower()
                    
                    if unique_id == username.lower():
                        sec_uid = user.get('sec_uid')
                        if sec_uid:
                            logger.info(f"成功获取用户 {username} 的secUid: {sec_uid}")
                            return sec_uid
                
                # 如果没有完全匹配，尝试第一个结果
                if user_list:
                    first_user = user_list[0].get('user_info', {})
                    sec_uid = first_user.get('sec_uid')
                    found_username = first_user.get('unique_id', '')
                    
                    if sec_uid:
                        logger.warning(f"未找到完全匹配的用户名，使用最相似的结果: {found_username}")
                        return sec_uid
                        
                logger.error(f"搜索结果中未找到用户 {username}")
            else:
                logger.error(f"搜索用户API返回空数据")
                
        except Exception as e:
            logger.error(f"通过用户名 {username} 获取secUid失败: {e}")
            # 回退到原来的方法
            return self._fallback_get_secuid(username)
            
        return None
        
    def _fallback_get_secuid(self, username: str) -> Optional[str]:
        """备用方法：通过TikTok公开API获取secUid
        
        Args:
            username: TikTok用户名
            
        Returns:
            secUid字符串，如果获取失败返回None
        """
        try:
            logger.info(f"使用备用方法获取用户 {username} 的secUid")
            
            # 使用TikTok的公开API获取用户信息
            url = "https://t.tiktok.com/api/user/detail/"
            params = {
                'uniqueId': username,
                'aid': '1988'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.tiktok.com/',
                'Origin': 'https://www.tiktok.com'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('statusCode') == 0 and 'userInfo' in data:
                    sec_uid = data['userInfo']['user'].get('secUid')
                    if sec_uid:
                        logger.info(f"备用方法成功获取用户 {username} 的secUid: {sec_uid}")
                        return sec_uid
                    else:
                        logger.error(f"备用方法：响应中未找到secUid字段")
                else:
                    logger.error(f"备用方法：API返回错误状态: {data.get('statusCode')}")
            else:
                logger.error(f"备用方法：HTTP请求失败，状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            logger.error(f"备用方法：网络连接失败，无法访问TikTok API")
        except requests.exceptions.Timeout:
            logger.error(f"备用方法：请求超时，TikTok API响应过慢")
        except Exception as e:
            logger.error(f"备用方法：通过用户名 {username} 获取secUid失败: {e}")
            
        return None
    
    def _extract_subtitle_from_response(self, video_id: str, aweme_detail: Dict[str, Any]) -> Optional[VideoSubtitle]:
        """从已有的API响应中提取字幕信息（避免重复API调用）
        
        Args:
            video_id: 视频ID
            aweme_detail: 已获取的aweme_detail数据
            
        Returns:
            VideoSubtitle对象，包含字幕文本，如果没有字幕则返回None
        """
        try:
            if 'video' not in aweme_detail:
                logger.debug(f"视频 {video_id} 没有video字段")
                return None
            
            video_info = aweme_detail['video']
            
            # 检查字幕信息 - 字幕在video.cla_info.caption_infos中
            if 'cla_info' not in video_info:
                logger.debug(f"视频 {video_id} 没有cla_info字段")
                return None
            
            cla_info = video_info['cla_info']
            
            if not isinstance(cla_info, dict) or 'caption_infos' not in cla_info:
                logger.debug(f"视频 {video_id} 没有caption_infos字段")
                return None
            
            caption_infos = cla_info['caption_infos']
            if not caption_infos:
                logger.debug(f"视频 {video_id} 字幕信息为空")
                return None
            
            # 获取第一个字幕信息（通常是主要语言）
            caption_info = caption_infos[0]
            
            # 获取字幕URL
            subtitle_urls = caption_info.get('url_list', [])
            if not subtitle_urls:
                logger.debug(f"视频 {video_id} 没有字幕下载链接")
                return None
            
            # 下载字幕内容
            full_text = self._download_subtitle_content(subtitle_urls)
            if not full_text:
                logger.debug(f"视频 {video_id} 字幕下载失败")
                return None
            
            subtitle = VideoSubtitle(
                video_id=video_id,
                caption_format=caption_info.get('caption_format', 'unknown'),
                caption_length=caption_info.get('caption_length', 0),
                language=caption_info.get('lang', 'unknown'),
                language_code=caption_info.get('language_code', 'unknown'),
                is_auto_generated=caption_info.get('is_auto_generated', False),
                subtitle_urls=subtitle_urls,
                full_text=full_text,
                subtitle_count=full_text.count('.') + full_text.count('!') + full_text.count('?'),  # 估算句子数
                raw_caption_info=caption_info
            )
            
            logger.info(f"📝 视频 {video_id} 字幕提取成功: {subtitle.language_code}, {len(full_text)}字符")
            
            return subtitle
            
        except Exception as e:
            logger.error(f"提取视频 {video_id} 字幕失败: {e}")
            return None
    
    def extract_subtitle_text(self, video_id: str) -> Optional[VideoSubtitle]:
        """提取视频字幕文本
        
        Args:
            video_id: 视频ID
            
        Returns:
            VideoSubtitle对象，包含字幕文本，如果没有字幕则返回None
        """
        try:
            # 获取视频详情
            params = {'aweme_id': video_id}
            raw_data = self._make_request(Config.VIDEO_DETAIL_ENDPOINT, params)
            
            if 'aweme_detail' not in raw_data:
                logger.debug(f"视频 {video_id} 没有详情数据")
                return None
            
            aweme_detail = raw_data['aweme_detail']
            
            if 'video' not in aweme_detail:
                logger.debug(f"视频 {video_id} 没有video字段")
                return None
            
            video_info = aweme_detail['video']
            
            # 检查字幕信息 - 字幕在video.cla_info.caption_infos中
            if 'cla_info' not in video_info:
                logger.debug(f"视频 {video_id} 没有cla_info字段")
                return None
            
            cla_info = video_info['cla_info']
            
            if not isinstance(cla_info, dict) or 'caption_infos' not in cla_info:
                logger.debug(f"视频 {video_id} 没有caption_infos字段")
                return None
            
            caption_infos = cla_info['caption_infos']
            if not caption_infos:
                logger.debug(f"视频 {video_id} 字幕信息为空")
                return None
            
            # 获取第一个字幕信息（通常是主要语言）
            caption_info = caption_infos[0]
            
            # 获取字幕URL
            subtitle_urls = caption_info.get('url_list', [])
            if not subtitle_urls:
                logger.debug(f"视频 {video_id} 没有字幕下载链接")
                return None
            
            # 下载字幕内容
            full_text = self._download_subtitle_content(subtitle_urls)
            if not full_text:
                logger.debug(f"视频 {video_id} 字幕下载失败")
                return None
            
            subtitle = VideoSubtitle(
                video_id=video_id,
                caption_format=caption_info.get('caption_format', 'unknown'),
                caption_length=caption_info.get('caption_length', 0),
                language=caption_info.get('lang', 'unknown'),
                language_code=caption_info.get('language_code', 'unknown'),
                is_auto_generated=caption_info.get('is_auto_generated', False),
                subtitle_urls=subtitle_urls,
                full_text=full_text,
                subtitle_count=full_text.count('.') + full_text.count('!') + full_text.count('?'),  # 估算句子数
                raw_caption_info=caption_info
            )
            
            logger.info(f"📝 视频 {video_id} 字幕提取成功: {subtitle.language_code}, {len(full_text)}字符")
            
            return subtitle
            
        except Exception as e:
            logger.error(f"提取视频 {video_id} 字幕失败: {e}")
            return None
    
    def _download_subtitle_content(self, subtitle_urls: List[str]) -> Optional[str]:
        """下载并解析字幕内容，返回纯文本
        
        Args:
            subtitle_urls: 字幕下载链接列表
            
        Returns:
            纯文本内容，如果下载失败则返回None
        """
        for i, url in enumerate(subtitle_urls, 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.tiktok.com/',
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # 解析WebVTT格式，提取纯文本
                    if content.startswith('WEBVTT'):
                        full_text = self._parse_webvtt_to_text(content)
                        if full_text:
                            return full_text
                    else:
                        # 如果不是WebVTT格式，直接返回内容
                        return content
                        
            except Exception as e:
                logger.debug(f"字幕链接 {i} 下载失败: {e}")
                continue
        
        return None
    
    def _parse_webvtt_to_text(self, webvtt_content: str) -> str:
        """解析WebVTT内容，提取纯文本
        
        Args:
            webvtt_content: WebVTT格式的字幕内容
            
        Returns:
            纯文本内容
        """
        if not webvtt_content or not webvtt_content.startswith('WEBVTT'):
            return ""
        
        lines = webvtt_content.strip().split('\n')
        text_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找时间戳行 (格式: 00:00:00.000 --> 00:00:02.000)
            if '-->' in line:
                # 收集字幕文本（可能跨多行）
                i += 1
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_content = lines[i].strip()
                    if text_content:
                        text_lines.append(text_content)
                    i += 1
                continue
            
            i += 1
        
        # 合并所有文本，去重复
        full_text = ' '.join(text_lines)
        
        # 清理文本
        full_text = re.sub(r'\s+', ' ', full_text)  # 合并多个空格
        full_text = full_text.strip()
        
        return full_text
            
    def fetch_user_videos_by_username(self, username: str, count: int = 5, keyword: str = None) -> List[VideoDetail]:
        """通过用户名获取用户作品详情
        
        Args:
            username: TikTok用户名
            count: 获取作品数量，默认5个（当没有关键词时使用）
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            视频详情列表
        """
        try:
            # 先获取secUid
            sec_uid = self.get_secuid_from_username(username)
            if not sec_uid:
                logger.error(f"无法获取用户 {username} 的secUid")
                return []
                
            # 使用secUid获取用户作品详情
            return self.fetch_user_top_videos(sec_uid, count, keyword)
            
        except Exception as e:
            logger.error(f"通过用户名 {username} 获取作品失败: {e}")
            return []
    
    def fetch_user_videos_recent_100(self, user_id: str, keyword: str = None) -> List[VideoDetail]:
        """获取用户最近100条视频（用于内容互动分计算）
        
        暂时回退到使用现有的工作方法，获取更多视频用于内容互动分计算
        
        Args:
            user_id: 用户ID (secUid)
            keyword: 关键词筛选，如果提供则筛选包含该关键词的视频
            
        Returns:
            视频详情列表
        """        
        if keyword:
            logger.info(f"开始获取用户 {user_id} 包含关键词 '{keyword}' 的作品（用于内容互动分计算）")
            # 使用现有的工作方法，获取更多视频
            return self.fetch_user_top_videos(user_id, 100, keyword)
        else:
            logger.info(f"开始获取用户 {user_id} 的作品（用于内容互动分计算）")
            # 使用现有的工作方法，获取更多视频
            return self.fetch_user_top_videos(user_id, 100)
