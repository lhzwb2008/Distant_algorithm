"""数据模型定义"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class UserProfile:
    """用户档案数据模型"""
    user_id: str
    username: str
    display_name: str
    follower_count: int
    following_count: int
    total_likes: int
    video_count: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    verified: bool = False
    
@dataclass
class VideoMetrics:
    """视频指标数据模型"""
    video_id: str
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    download_count: Optional[int] = None
    collect_count: Optional[int] = None
    create_time: Optional[datetime] = None
    
@dataclass
class VideoSubtitle:
    """视频字幕数据模型"""
    video_id: str
    caption_format: str  # webvtt, srt等
    caption_length: int  # 字幕长度
    language: str        # 语言代码 如eng-US
    language_code: str   # 简短语言代码 如en
    is_auto_generated: bool  # 是否自动生成
    subtitle_urls: List[str]  # 字幕下载链接列表
    full_text: Optional[str] = None  # 完整文本内容
    subtitle_count: int = 0  # 字幕条数
    raw_caption_info: Optional[Dict[str, Any]] = None  # 原始字幕信息

@dataclass
class VideoDetail:
    """视频详情数据模型"""
    video_id: str
    desc: str
    create_time: datetime
    author_id: str
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    download_count: int
    collect_count: int
    duration: Optional[float] = None
    subtitle: Optional[VideoSubtitle] = None  # 字幕信息
    
@dataclass
class AccountQualityScore:
    """账户质量评分"""
    follower_score: float  # 粉丝数量得分
    likes_score: float     # 总点赞数得分
    posting_score: float   # 发布频率得分
    total_score: float     # 总分
    multiplier: float      # 加权系数
    posting_details: dict = None  # 发布频率详细计算过程
    
@dataclass
class ContentInteractionScore:
    """内容互动评分"""
    view_score: float      # 播放量得分
    like_score: float      # 点赞得分
    comment_score: float   # 评论得分
    share_score: float     # 分享得分
    save_score: float      # 保存得分
    total_score: float     # 总分
    calculation_details: dict = None  # 详细计算过程
    
@dataclass
class CreatorScore:
    """创作者总评分"""
    user_id: str
    username: str
    account_quality: AccountQualityScore
    content_interaction: ContentInteractionScore
    final_score: float
    calculated_at: datetime
    video_count: int = 0  # 分析的视频数量
    # 新算法相关字段
    peak_performance: float = 0.0  # 峰值表现
    recent_performance: float = 0.0  # 近期状态
    overall_performance: float = 0.0  # 整体水平
    video_scores: List[float] = None  # 每个视频的评分
    
@dataclass
class TrendData:
    """趋势数据"""
    date: str
    views: int
    likes: int
    comments: int
    shares: int