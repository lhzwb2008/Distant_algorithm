# -*- coding: utf-8 -*-
"""
TikTok Creator Score System Configuration

配置文件，包含API设置、评分权重和系统参数
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # TiKhub API配置
    # 注意：TIKHUB_API_KEY 必须在 .env 文件中配置，不提供默认值以确保安全
    TIKHUB_API_KEY = os.getenv('TIKHUB_API_KEY')
    TIKHUB_BASE_URL = os.getenv('TIKHUB_BASE_URL', 'https://api.tikhub.dev')  # 使用正确的API URL
    TIKHUB_REQUEST_TIMEOUT = int(os.getenv('TIKHUB_REQUEST_TIMEOUT', '30'))
    TIKHUB_MAX_RETRIES = int(os.getenv('TIKHUB_MAX_RETRIES', '25'))  # 增加到25次，确保覆盖限流恢复时间
    
    # OpenRouter API配置 - 用于视频质量评分
    # 注意：OPENROUTER_API_KEY 必须在 .env 文件中配置，不提供默认值以确保安全
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
    OPENROUTER_REQUEST_TIMEOUT = int(os.getenv('OPENROUTER_REQUEST_TIMEOUT', '60'))
    OPENROUTER_TEMPERATURE = float(os.getenv('OPENROUTER_TEMPERATURE', '0.3'))
    OPENROUTER_MAX_TOKENS = int(os.getenv('OPENROUTER_MAX_TOKENS', '2000'))
    OPENROUTER_CONCURRENT_REQUESTS = int(os.getenv('OPENROUTER_CONCURRENT_REQUESTS', '20'))  # 并发请求数
    
    # Google Gemini API配置 - 用于视频内容分析（当字幕提取关闭时使用）
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_MODEL = os.getenv('GOOGLE_MODEL', 'models/gemini-2.5-flash')
    GOOGLE_REQUEST_TIMEOUT = int(os.getenv('GOOGLE_REQUEST_TIMEOUT', '120'))  # 视频处理需要更长时间
    GOOGLE_CONCURRENT_REQUESTS = int(os.getenv('GOOGLE_CONCURRENT_REQUESTS', '5'))  # Google API并发数，建议较低
    
    # 数据获取范围配置
    ACCOUNT_QUALITY_DAYS = int(os.getenv('ACCOUNT_QUALITY_DAYS', '90'))  # 维度一：账户质量分数据范围（天数）
    CONTENT_INTERACTION_MAX_VIDEOS = int(os.getenv('CONTENT_INTERACTION_MAX_VIDEOS', '100'))  # 维度二：内容互动分最大检查视频数
    
    # API端点配置
    API_ENDPOINTS = {
        'user_profile': '/api/v1/tiktok/web/fetch_user_profile',
        'video_metrics': '/api/v1/tiktok/analytics/fetch_video_metrics',
        'video_detail': '/api/v1/tiktok/app/v3/fetch_one_video',
        'user_videos': '/api/v1/tiktok/web/fetch_user_post'
    }
    
    # API端点快捷访问
    USER_PROFILE_ENDPOINT = API_ENDPOINTS['user_profile']
    VIDEO_METRICS_ENDPOINT = API_ENDPOINTS['video_metrics']
    VIDEO_DETAIL_ENDPOINT = API_ENDPOINTS['video_detail']
    USER_VIDEOS_ENDPOINT = API_ENDPOINTS['user_videos']
    
    # 字幕提取开关配置
    ENABLE_SUBTITLE_EXTRACTION = os.getenv('ENABLE_SUBTITLE_EXTRACTION', 'false').lower() == 'true'
    
    # 主评分权重配置
    CONTENT_QUALITY_WEIGHT = float(os.getenv('CONTENT_QUALITY_WEIGHT', '0.35'))
    CONTENT_INTERACTION_WEIGHT = float(os.getenv('CONTENT_INTERACTION_WEIGHT', '0.65'))
    
    # 账户质量评分权重
    ACCOUNT_QUALITY_WEIGHTS = {
        'follower_count': 0.40,  # 粉丝数量权重
        'total_likes': 0.40,     # 总点赞数权重
        'posting_frequency': 0.20 # 发布频率权重
    }
    
    # 内容互动评分权重
    CONTENT_INTERACTION_WEIGHTS = {
        'views': 0.10,      # 播放量权重
        'likes': 0.25,      # 点赞数权重
        'comments': 0.30,   # 评论数权重
        'shares': 0.35      # 分享数权重
    }
    
    # 账户质量加权系数
    ACCOUNT_QUALITY_MULTIPLIERS = {
        (0, 10): 1.0,
        (10, 30): 1.2,
        (31, 60): 1.5,
        (61, 80): 2.0,
        (81, 100): 3.0
    }
    
    # 评分算法参数
    SCORING_PARAMETERS = {
        # 粉丝数量评分参数
        'follower_score': {
            'log_multiplier': 10,
            'max_score': 100
        },
        
        # 总点赞数评分参数
        'total_likes_score': {
            'log_multiplier': 12.5,
            'max_score': 100
        },
        
        # 发布频率评分参数
        'posting_frequency_score': {
            'ideal_frequency': 5,  # 理想的每周发布次数
            'penalty_coefficient': 15,  # 偏离理想频次的惩罚系数
            'max_score': 100
        },
        
        # 播放量评分参数
        'view_score': {
            'multiplier': 100,  # 播放量/粉丝数的倍数
            'max_score': 100
        },
        
        # 点赞率评分参数
        'like_rate_score': {
            'multiplier': 2500,  # 点赞率系数
            'max_score': 100,
            'excellent_rate': 0.04  # 优秀点赞率标准（4%）
        },
        
        # 评论率评分参数
        'comment_rate_score': {
            'multiplier': 12500,  # 评论率系数
            'max_score': 100,
            'excellent_rate': 0.008  # 优秀评论率标准（0.8%）
        },
        
        # 分享率评分参数
        'share_rate_score': {
            'multiplier': 25000,  # 分享率系数
            'max_score': 100,
            'excellent_rate': 0.004  # 优秀分享率标准（0.4%）
        }
    }
    
    # 行业基准数据
    INDUSTRY_BENCHMARKS = {
        'average_engagement_rate': 0.025,  # 平均互动率2.5%
        'excellent_engagement_rate': 0.0396,  # 优秀互动率3.96%
        'small_account_engagement': 0.042,  # 小账户互动率4.2%
        'large_account_threshold': 100000,  # 大账户粉丝阈值
        
        # 不同粉丝数量级的基准
        'follower_benchmarks': {
            '1k_10k': {'score_range': (20, 40), 'engagement_rate': 0.042},
            '10k_100k': {'score_range': (40, 50), 'engagement_rate': 0.035},
            '100k_plus': {'score_range': (50, 60), 'engagement_rate': 0.025}
        }
    }
    
    # 数据验证规则
    VALIDATION_RULES = {
        'min_follower_count': 0,
        'max_follower_count': 1000000000,  # 10亿粉丝上限
        'min_video_count': 1,
        'max_video_count': 1000,  # 单次分析最多1000个视频
        'min_engagement_rate': 0,
        'max_engagement_rate': 1.0,  # 100%互动率上限
        'min_score': 0,
        'max_base_score': 100,  # 基础评分上限
        'max_weighted_score': 300  # 加权后评分上限
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'enable_cache': True,
        'cache_ttl': 3600,  # 缓存时间1小时
        'max_cache_size': 1000  # 最大缓存条目数
    }
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 错误处理配置
    ERROR_HANDLING = {
        'max_retries': 3,
        'retry_delay': 3,  # 基础重试延迟（秒），配合指数退避
        'timeout_threshold': 30,  # 超时阈值（秒）
        'rate_limit_delay': 60,  # 限流延迟（秒）
        'exponential_backoff': True,  # 启用指数退避
        'backoff_factor': 1.5,  # 退避因子
        'max_delay': 30  # 最大延迟时间（秒）
    }
    
    @classmethod
    def get_account_quality_multiplier(cls, score: float) -> float:
        """根据账户质量分数获取加权系数
        
        Args:
            score: 账户质量分数
            
        Returns:
            float: 加权系数
        """
        for (min_score, max_score), multiplier in cls.ACCOUNT_QUALITY_MULTIPLIERS.items():
            if min_score <= score <= max_score:
                return multiplier
        
        # 如果分数超出范围，返回最高倍数
        return 3.0
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置的有效性
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查API密钥
        if not cls.TIKHUB_API_KEY:
            validation_result['valid'] = False
            validation_result['errors'].append('TIKHUB_API_KEY is required')
        
        if not cls.OPENROUTER_API_KEY:
            validation_result['warnings'].append('OPENROUTER_API_KEY is not set, video quality scoring will be disabled')
        
        # 检查权重总和
        account_weight_sum = sum(cls.ACCOUNT_QUALITY_WEIGHTS.values())
        if abs(account_weight_sum - 1.0) > 0.001:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f'Account quality weights sum to {account_weight_sum}, should be 1.0'
            )
        
        content_weight_sum = sum(cls.CONTENT_INTERACTION_WEIGHTS.values())
        if abs(content_weight_sum - 1.0) > 0.001:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f'Content interaction weights sum to {content_weight_sum}, should be 1.0'
            )
        
        main_weight_sum = cls.CONTENT_QUALITY_WEIGHT + cls.CONTENT_INTERACTION_WEIGHT
        if abs(main_weight_sum - 1.0) > 0.001:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f'Main weights sum to {main_weight_sum}, should be 1.0'
            )
        
        # 检查参数合理性
        if cls.TIKHUB_REQUEST_TIMEOUT <= 0:
            validation_result['warnings'].append('Request timeout should be positive')
        
        if cls.TIKHUB_MAX_RETRIES < 0:
            validation_result['warnings'].append('Max retries should be non-negative')
        
        return validation_result
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        return {
            'tikhub_api_configured': bool(cls.TIKHUB_API_KEY),
            'openrouter_api_configured': bool(cls.OPENROUTER_API_KEY),
            'google_api_configured': bool(cls.GOOGLE_API_KEY),
            'tikhub_base_url': cls.TIKHUB_BASE_URL,
            'openrouter_base_url': cls.OPENROUTER_BASE_URL,
            'openrouter_model': cls.OPENROUTER_MODEL,
            'openrouter_concurrent_requests': cls.OPENROUTER_CONCURRENT_REQUESTS,
            'google_model': cls.GOOGLE_MODEL,
            'google_concurrent_requests': cls.GOOGLE_CONCURRENT_REQUESTS,
            'subtitle_extraction_enabled': cls.ENABLE_SUBTITLE_EXTRACTION,
            'data_range': {
                'account_quality_days': cls.ACCOUNT_QUALITY_DAYS,
                'content_interaction_max_videos': cls.CONTENT_INTERACTION_MAX_VIDEOS
            },
            'main_weights': {
                'content_quality': cls.CONTENT_QUALITY_WEIGHT,
                'content_interaction': cls.CONTENT_INTERACTION_WEIGHT
            },
            'account_quality_weights': cls.ACCOUNT_QUALITY_WEIGHTS,
            'content_interaction_weights': cls.CONTENT_INTERACTION_WEIGHTS,
            'cache_enabled': cls.CACHE_CONFIG['enable_cache'],
            'log_level': cls.LOG_LEVEL
        }


# 创建全局配置实例
config = Config()

# 验证配置
validation_result = config.validate_config()
if not validation_result['valid']:
    raise ValueError(f"Configuration validation failed: {validation_result['errors']}")

if validation_result['warnings']:
    import warnings
    for warning in validation_result['warnings']:
        warnings.warn(f"Configuration warning: {warning}")