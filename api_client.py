"""TiKhub API客户端"""

import requests
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import Config
from models import UserProfile, VideoMetrics, VideoDetail

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
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{Config.TIKHUB_MAX_RETRIES}): {e}")
                if attempt == Config.TIKHUB_MAX_RETRIES - 1:
                    raise
                time.sleep(Config.ERROR_HANDLING['retry_delay'] * (attempt + 1))
                
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
            duration=aweme_detail.get('duration', 0) / 1000.0  # 转换为秒
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
            # 当有关键词时，获取更多视频以便筛选
            api_count = 50  # 获取更多视频用于筛选
        else:
            logger.info(f"开始获取用户 {user_id} 的前 {count} 个作品")
            api_count = count
        
        # 直接调用API获取用户视频列表
        params = {
            'secUid': user_id,
            'count': api_count
        }
        
        try:
            # 使用配置中的API端点获取用户视频列表
            data = self._make_request(Config.USER_VIDEOS_ENDPOINT, params)
            
            # 检查API响应状态
            if data.get('statusCode', 1) != 0:
                logger.warning(f"API返回错误状态: {data.get('statusMsg', 'Unknown error')}")
                return []
            
            # 获取视频列表 - 使用与fetch_user_videos相同的逻辑
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
            
            # 从视频列表构建VideoDetail对象，并获取额外的指标数据
            video_details = []
            
            # 如果有关键词，先筛选匹配的视频
            if keyword:
                filtered_videos = []
                logger.info(f"🔍 开始筛选包含关键词 '{keyword}' 的视频...")
                for i, video in enumerate(videos, 1):
                    desc = video.get('desc', '')
                    video_id = video.get('id', 'unknown')
                    if keyword.lower() in desc.lower():
                        filtered_videos.append(video)
                        logger.info(f"✅ 第{i}个视频匹配关键词 '{keyword}':")
                        logger.info(f"   📹 视频ID: {video_id}")
                        logger.info(f"   📝 完整描述: {desc}")
                    else:
                        logger.info(f"❌ 第{i}个视频不匹配关键词 '{keyword}':")
                        logger.info(f"   📹 视频ID: {video_id}")
                        logger.info(f"   📝 完整描述: {desc}")
                videos_to_process = filtered_videos
                logger.info(f"🎯 关键词 '{keyword}' 筛选结果: {len(filtered_videos)}/{len(videos)} 个视频匹配")
            else:
                videos_to_process = videos[:count]
            
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
                        duration=video.get('video', {}).get('duration', 0)
                    )
                    video_details.append(video_detail)
                    # 记录详细的视频数据
                    logger.info(f"成功解析视频 {video_detail.video_id}")
                    logger.info(f"  📺 播放: {view_count:,}, 👍 点赞: {like_count:,}, 💬 评论: {comment_count:,}, 🔄 分享: {share_count:,}")
                    logger.info(f"  📝 完整描述: {video_detail.desc}")
                    if collect_count > 0:
                        logger.info(f"  ⭐ 收藏: {collect_count:,}")
                except Exception as e:
                    logger.error(f"解析视频数据失败: {e}")
                    continue
                    
            logger.info(f"成功获取用户 {user_id} 的 {len(video_details)} 个作品详情")
            return video_details
            
        except Exception as e:
            logger.error(f"获取用户视频列表失败: {e}")
            return []
    
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
        
        # 计算三个月前的时间
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)  # 约3个月
        logger.info(f"时间范围: {three_months_ago.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}")
        
        all_videos = []
        cursor = 0
        page = 1
        videos_per_page = 20  # 每页获取20个视频
        
        while page <= max_pages:
            logger.info(f"正在获取第 {page} 页数据 (cursor: {cursor})...")
            
            # 设置分页参数（与工作的API调用保持一致）
            params = {
                'secUid': user_id,
                'count': videos_per_page
            }
            
            # 只有在非第一页时才添加cursor参数
            if cursor > 0:
                params['cursor'] = cursor
            
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
                        
                        # 检查视频是否在三个月范围内
                        if create_time < three_months_ago:
                            videos_outside_range += 1
                            logger.info(f"视频 {video_id} 创建时间 {create_time.strftime('%Y-%m-%d')} 超出三个月范围，跳过")
                            continue
                        
                        # 关键词筛选（如果提供了关键词）
                        if keyword:
                            desc = video.get('desc', '')
                            if keyword.lower() not in desc.lower():
                                logger.info(f"❌ 视频 {video_id} 不匹配关键词 '{keyword}':")
                                logger.info(f"   📝 完整描述: {desc}")
                                continue
                            else:
                                logger.info(f"✅ 视频 {video_id} 匹配关键词 '{keyword}':")
                                logger.info(f"   📝 完整描述: {desc}")
                        
                        # 从基础API响应获取数据（与现有代码保持一致）
                        base_stats = video.get('stats', {})
                        
                        view_count = base_stats.get('playCount', 0)
                        like_count = base_stats.get('diggCount', 0)
                        comment_count = base_stats.get('commentCount', 0)
                        share_count = base_stats.get('shareCount', 0)
                        collect_count = base_stats.get('collectCount', 0)
                        
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
                            duration=video.get('video', {}).get('duration', 0)
                        )
                        page_videos.append(video_detail)
                        
                        logger.info(f"成功解析视频 {video_detail.video_id} (创建时间: {create_time.strftime('%Y-%m-%d')})")
                        
                    except Exception as e:
                        logger.error(f"解析视频数据失败: {e}")
                        continue
                
                all_videos.extend(page_videos)
                logger.info(f"第 {page} 页: 解析成功 {len(page_videos)} 个视频，跳过 {videos_outside_range} 个超出范围的视频")
                
                # 如果当前页有很多视频超出时间范围，可能后续页面都超出范围了
                if videos_outside_range > len(page_videos):
                    logger.info("当前页超出时间范围的视频较多，可能已到达三个月边界，停止分页")
                    break
                
                # 更新分页参数（与现有API保持兼容）
                has_more = data.get('hasMore', False)
                if not has_more:
                    logger.info("API返回 hasMore=false，没有更多数据")
                    break
                
                # 更新cursor用于下一页
                new_cursor = data.get('cursor', cursor + videos_per_page)
                # 确保cursor是整数类型
                cursor = int(new_cursor) if new_cursor is not None else cursor + videos_per_page
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