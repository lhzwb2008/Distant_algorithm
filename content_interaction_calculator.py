"""内容互动数据评分计算器（维度2）"""

import logging
from typing import List

from models import VideoDetail, VideoMetrics, UserProfile, ContentInteractionScore

logger = logging.getLogger(__name__)

class ContentInteractionCalculator:
    """内容互动数据评分计算器"""
    
    def __init__(self):
        """初始化计算器"""
        pass
    
    def _get_follower_coefficient(self, follower_count: int) -> float:
        """获取粉丝数量系数（系数1）
        
        根据粉丝数量确定基准系数：
        - 0-100：基准 = 3倍粉丝量
        - 100-1k：基准 = 2倍粉丝量
        - 1k-5k：基准 = 1倍粉丝量
        - 5k-10k：基准 = 0.8倍粉丝量
        - 10k-50k：基准 = 0.7倍粉丝量
        - 50k-100k：基准 = 0.6倍粉丝量
        - 100k-500k：基准 = 0.5倍粉丝量
        - 500k-1M：基准 = 0.4倍粉丝量
        - 1M+：基准 = 0.3倍粉丝量
        """
        if follower_count <= 100:
            return 3.0
        elif follower_count <= 1000:
            return 2.0
        elif follower_count <= 5000:
            return 1.0
        elif follower_count <= 10000:
            return 0.8
        elif follower_count <= 50000:
            return 0.7
        elif follower_count <= 100000:
            return 0.6
        elif follower_count <= 500000:
            return 0.5
        elif follower_count <= 1000000:
            return 0.4
        else:
            return 0.3
    
    def _get_view_coefficient(self, views: int) -> float:
        """获取播放量系数（系数2）
        
        根据播放量确定基准系数：
        - 0-1k：基准 = 2倍
        - 1k-10k：基准 = 1倍
        - 10k-100k：基准 = 0.7倍
        - 100k-500k：基准 = 0.6倍
        - 500k+：基准 = 0.5倍
        """
        if views <= 1000:
            return 2.0
        elif views <= 10000:
            return 1.0
        elif views <= 100000:
            return 0.7
        elif views <= 500000:
            return 0.6
        else:
            return 0.5
        
    def calculate_view_score(self, views: int, follower_count: int) -> float:
        """计算视频播放量得分
        
        评分公式：min((views / (followers * 基准系数)) * 100, 100)
        基准系数根据粉丝数量分层：
        - 0-100：基准 = 3倍粉丝量
        - 100-1k：基准 = 2倍粉丝量
        - 1k-5k：基准 = 1倍粉丝量
        - 5k-10k：基准 = 0.8倍粉丝量
        - 10k-50k：基准 = 0.7倍粉丝量
        - 50k-100k：基准 = 0.6倍粉丝量
        - 100k-500k：基准 = 0.5倍粉丝量
        - 500k-1M：基准 = 0.4倍粉丝量
        - 1M+：基准 = 0.3倍粉丝量
        
        Args:
            views: 视频播放量
            follower_count: 粉丝数量
            
        Returns:
            播放量得分 (0-100)
        """
        if follower_count <= 0:
            # 当没有粉丝数据时，基于播放量绝对值评分
            # 基准：2000播放量 = 100分，1000播放量 = 50分
            score = min((views / 2000) * 100, 100)
            return max(0.0, score)
        
        # 使用系数1
        coefficient1 = self._get_follower_coefficient(follower_count)
            
        expected_views = follower_count * coefficient1
        view_ratio = views / expected_views
        score = min(view_ratio * 100, 100)
        return max(0.0, score)
        
    def calculate_view_score_with_details(self, views: int, follower_count: int) -> tuple:
        """计算视频播放量得分并返回详细计算过程
        
        Returns:
            (score, details_dict)
        """
        if follower_count <= 0:
            score = min((views / 2000) * 100, 100)
            score = max(0.0, score)
            details = {
                "原始数据": f"播放量: {views:,}, 粉丝数: {follower_count}",
                "计算方式": "无粉丝数据时的计算",
                "公式": "min((播放量 / 2000) × 100, 100)",
                "计算过程": f"min(({views:,} / 2000) × 100, 100) = min({views/2000*100:.2f}, 100) = {score:.2f}",
                "最终得分": f"{score:.2f}"
            }
            return score, details
        
        coefficient1 = self._get_follower_coefficient(follower_count)
        expected_views = follower_count * coefficient1
        view_ratio = views / expected_views
        score = min(view_ratio * 100, 100)
        score = max(0.0, score)
        
        # 获取粉丝数量分层说明
        tier_description = self._get_follower_tier_description(follower_count)
        
        details = {
            "原始数据": f"播放量: {views:,}, 粉丝数: {follower_count:,}",
            "系数1选择过程": f"粉丝数{follower_count:,} → {tier_description}",
            "基准系数": f"{coefficient1}",
            "期望播放量": f"{follower_count:,} × {coefficient1} = {expected_views:,}",
            "播放比例": f"{views:,} / {expected_views:,} = {view_ratio:.4f}",
            "公式": "min((播放量 / (粉丝数 × 系数1)) × 100, 100)",
            "计算过程": f"min({view_ratio:.4f} × 100, 100) = min({view_ratio*100:.2f}, 100) = {score:.2f}",
            "最终得分": f"{score:.2f}"
        }
        return score, details
        
    def _get_follower_tier_description(self, follower_count: int) -> str:
        """获取粉丝数量分层描述"""
        if follower_count <= 100:
            return f"0-100粉丝层级 (系数3.0)"
        elif follower_count <= 1000:
            return f"100-1k粉丝层级 (系数2.0)"
        elif follower_count <= 5000:
            return f"1k-5k粉丝层级 (系数1.0)"
        elif follower_count <= 10000:
            return f"5k-10k粉丝层级 (系数0.8)"
        elif follower_count <= 50000:
            return f"10k-50k粉丝层级 (系数0.7)"
        elif follower_count <= 100000:
            return f"50k-100k粉丝层级 (系数0.6)"
        elif follower_count <= 500000:
            return f"100k-500k粉丝层级 (系数0.5)"
        elif follower_count <= 1000000:
            return f"500k-1M粉丝层级 (系数0.4)"
        else:
            return f"1M+粉丝层级 (系数0.3)"
        
    def calculate_like_score(self, likes: int, views: int, follower_count: int = 0) -> float:
        """计算点赞数得分
        
        新公式：min((likes / max(followers*系数1*20%, views*系数2)) * 2500, 100)
        
        Args:
            likes: 点赞数
            views: 播放量
            follower_count: 粉丝数量（可选，为0时使用旧公式）
            
        Returns:
            点赞得分 (0-100)
        """
        if views <= 0:
            return 0.0
        
        # 如果没有粉丝数据，使用旧公式保持向后兼容
        if follower_count <= 0:
            like_rate = likes / views
            score = min(like_rate * 2500, 100)
            return max(0.0, score)
        
        # 新公式：使用系数计算
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2  # 20%
        view_base = views * coefficient2
        
        base_value = max(follower_base, view_base)
        if base_value <= 0:
            return 0.0
            
        score = min((likes / base_value) * 2500, 100)
        return max(0.0, score)
        
    def calculate_like_score_with_details(self, likes: int, views: int, follower_count: int = 0) -> tuple:
        """计算点赞数得分并返回详细计算过程"""
        if views <= 0:
            details = {
                "原始数据": f"点赞数: {likes:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "播放量为0，无法计算点赞得分",
                "最终得分": "0.00"
            }
            return 0.0, details
        
        if follower_count <= 0:
            like_rate = likes / views
            score = min(like_rate * 2500, 100)
            score = max(0.0, score)
            details = {
                "原始数据": f"点赞数: {likes:,}, 播放量: {views:,}, 粉丝数: {follower_count}",
                "计算方式": "无粉丝数据时的计算",
                "点赞率": f"{likes:,} / {views:,} = {like_rate:.6f}",
                "公式": "min(点赞率 × 2500, 100)",
                "计算过程": f"min({like_rate:.6f} × 2500, 100) = min({like_rate*2500:.2f}, 100) = {score:.2f}",
                "最终得分": f"{score:.2f}"
            }
            return score, details
        
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2
        view_base = views * coefficient2
        base_value = max(follower_base, view_base)
        
        if base_value <= 0:
            details = {
                "原始数据": f"点赞数: {likes:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "基准值计算为0，无法计算点赞得分",
                "最终得分": "0.00"
            }
            return 0.0, details
            
        score = min((likes / base_value) * 2500, 100)
        score = max(0.0, score)
        
        # 获取播放量分层说明
        view_tier = self._get_view_tier_description(views)
        
        details = {
            "原始数据": f"点赞数: {likes:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
            "系数1选择过程": f"粉丝数{follower_count:,} → {self._get_follower_tier_description(follower_count)}",
            "系数2选择过程": f"播放量{views:,} → {view_tier}",
            "粉丝基准系数": f"{coefficient1}",
            "播放量基准系数": f"{coefficient2}",
            "粉丝基准值": f"{follower_count:,} × {coefficient1} × 20% = {follower_base:.2f}",
            "播放量基准值": f"{views:,} × {coefficient2} = {view_base:.2f}",
            "最终基准值": f"max({follower_base:.2f}, {view_base:.2f}) = {base_value:.2f}",
            "公式": "min((点赞数 / max(粉丝数×系数1×20%, 播放量×系数2)) × 2500, 100)",
            "计算过程": f"min(({likes:,} / {base_value:.2f}) × 2500, 100) = min({likes/base_value*2500:.2f}, 100) = {score:.2f}",
            "最终得分": f"{score:.2f}"
        }
        return score, details
        
    def _get_view_tier_description(self, views: int) -> str:
        """获取播放量分层描述"""
        if views <= 1000:
            return f"0-1k播放层级 (系数2.0)"
        elif views <= 10000:
            return f"1k-10k播放层级 (系数1.0)"
        elif views <= 100000:
            return f"10k-100k播放层级 (系数0.7)"
        elif views <= 500000:
            return f"100k-500k播放层级 (系数0.6)"
        else:
            return f"500k+播放层级 (系数0.5)"
        
    def calculate_comment_score(self, comments: int, views: int, follower_count: int = 0) -> float:
        """计算评论数得分
        
        新公式：min((comments / max(followers*系数1*20%, views*系数2)) * 12500, 100)
        
        Args:
            comments: 评论数
            views: 播放量
            follower_count: 粉丝数量（可选，为0时使用旧公式）
            
        Returns:
            评论得分 (0-100)
        """
        if views <= 0:
            return 0.0
        
        # 如果没有粉丝数据，使用旧公式保持向后兼容
        if follower_count <= 0:
            comment_rate = comments / views
            score = min(comment_rate * 12500, 100)
            return max(0.0, score)
        
        # 新公式：使用系数计算
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2  # 20%
        view_base = views * coefficient2
        
        base_value = max(follower_base, view_base)
        if base_value <= 0:
            return 0.0
            
        score = min((comments / base_value) * 12500, 100)
        return max(0.0, score)
        
    def calculate_comment_score_with_details(self, comments: int, views: int, follower_count: int = 0) -> tuple:
        """计算评论数得分并返回详细计算过程"""
        if views <= 0:
            details = {
                "原始数据": f"评论数: {comments:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "播放量为0，无法计算评论得分",
                "最终得分": "0.00"
            }
            return 0.0, details
        
        if follower_count <= 0:
            comment_rate = comments / views
            score = min(comment_rate * 12500, 100)
            score = max(0.0, score)
            details = {
                "原始数据": f"评论数: {comments:,}, 播放量: {views:,}, 粉丝数: {follower_count}",
                "计算方式": "无粉丝数据时的计算",
                "评论率": f"{comments:,} / {views:,} = {comment_rate:.6f}",
                "公式": "min(评论率 × 12500, 100)",
                "计算过程": f"min({comment_rate:.6f} × 12500, 100) = min({comment_rate*12500:.2f}, 100) = {score:.2f}",
                "最终得分": f"{score:.2f}"
            }
            return score, details
        
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2
        view_base = views * coefficient2
        base_value = max(follower_base, view_base)
        
        if base_value <= 0:
            details = {
                "原始数据": f"评论数: {comments:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "基准值计算为0，无法计算评论得分",
                "最终得分": "0.00"
            }
            return 0.0, details
            
        score = min((comments / base_value) * 12500, 100)
        score = max(0.0, score)
        
        details = {
            "原始数据": f"评论数: {comments:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
            "系数1选择过程": f"粉丝数{follower_count:,} → {self._get_follower_tier_description(follower_count)}",
            "系数2选择过程": f"播放量{views:,} → {self._get_view_tier_description(views)}",
            "粉丝基准系数": f"{coefficient1}",
            "播放量基准系数": f"{coefficient2}",
            "粉丝基准值": f"{follower_count:,} × {coefficient1} × 20% = {follower_base:.2f}",
            "播放量基准值": f"{views:,} × {coefficient2} = {view_base:.2f}",
            "最终基准值": f"max({follower_base:.2f}, {view_base:.2f}) = {base_value:.2f}",
            "公式": "min((评论数 / max(粉丝数×系数1×20%, 播放量×系数2)) × 12500, 100)",
            "计算过程": f"min(({comments:,} / {base_value:.2f}) × 12500, 100) = min({comments/base_value*12500:.2f}, 100) = {score:.2f}",
            "最终得分": f"{score:.2f}"
        }
        return score, details
        
    def calculate_share_score(self, shares: int, views: int, follower_count: int = 0) -> float:
        """计算分享数得分
        
        新公式：min((shares / max(followers*系数1*20%, views*系数2)) * 25000, 100)
        
        Args:
            shares: 分享数
            views: 播放量
            follower_count: 粉丝数量（可选，为0时使用旧公式）
            
        Returns:
            分享得分 (0-100)
        """
        if views <= 0:
            return 0.0
        
        # 如果没有粉丝数据，使用旧公式保持向后兼容
        if follower_count <= 0:
            share_rate = shares / views
            score = min(share_rate * 25000, 100)
            return max(0.0, score)
        
        # 新公式：使用系数计算
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2  # 20%
        view_base = views * coefficient2
        
        base_value = max(follower_base, view_base)
        if base_value <= 0:
            return 0.0
            
        score = min((shares / base_value) * 25000, 100)
        return max(0.0, score)
        
    def calculate_share_score_with_details(self, shares: int, views: int, follower_count: int = 0) -> tuple:
        """计算分享数得分并返回详细计算过程"""
        if views <= 0:
            details = {
                "原始数据": f"分享数: {shares:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "播放量为0，无法计算分享得分",
                "最终得分": "0.00"
            }
            return 0.0, details
        
        if follower_count <= 0:
            share_rate = shares / views
            score = min(share_rate * 25000, 100)
            score = max(0.0, score)
            details = {
                "原始数据": f"分享数: {shares:,}, 播放量: {views:,}, 粉丝数: {follower_count}",
                "计算方式": "无粉丝数据时的计算",
                "分享率": f"{shares:,} / {views:,} = {share_rate:.6f}",
                "公式": "min(分享率 × 25000, 100)",
                "计算过程": f"min({share_rate:.6f} × 25000, 100) = min({share_rate*25000:.2f}, 100) = {score:.2f}",
                "最终得分": f"{score:.2f}"
            }
            return score, details
        
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2
        view_base = views * coefficient2
        base_value = max(follower_base, view_base)
        
        if base_value <= 0:
            details = {
                "原始数据": f"分享数: {shares:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "基准值计算为0，无法计算分享得分",
                "最终得分": "0.00"
            }
            return 0.0, details
            
        score = min((shares / base_value) * 25000, 100)
        score = max(0.0, score)
        
        details = {
            "原始数据": f"分享数: {shares:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
            "系数1选择过程": f"粉丝数{follower_count:,} → {self._get_follower_tier_description(follower_count)}",
            "系数2选择过程": f"播放量{views:,} → {self._get_view_tier_description(views)}",
            "粉丝基准系数": f"{coefficient1}",
            "播放量基准系数": f"{coefficient2}",
            "粉丝基准值": f"{follower_count:,} × {coefficient1} × 20% = {follower_base:.2f}",
            "播放量基准值": f"{views:,} × {coefficient2} = {view_base:.2f}",
            "最终基准值": f"max({follower_base:.2f}, {view_base:.2f}) = {base_value:.2f}",
            "公式": "min((分享数 / max(粉丝数×系数1×20%, 播放量×系数2)) × 25000, 100)",
            "计算过程": f"min(({shares:,} / {base_value:.2f}) × 25000, 100) = min({shares/base_value*25000:.2f}, 100) = {score:.2f}",
            "最终得分": f"{score:.2f}"
        }
        return score, details
        
    def calculate_save_score(self, saves: int, views: int, follower_count: int = 0) -> float:
        """计算保存数得分
        
        新公式：min((saves / max(followers*系数1*20%, views*系数2)) * 10000, 100)
        
        Args:
            saves: 保存数
            views: 播放量
            follower_count: 粉丝数量（可选，为0时使用旧公式）
            
        Returns:
            保存得分 (0-100)
        """
        if views <= 0:
            return 0.0
        
        # 如果没有粉丝数据，使用旧公式保持向后兼容
        if follower_count <= 0:
            save_rate = saves / views
            score = min(save_rate * 10000, 100)
            return max(0.0, score)
        
        # 新公式：使用系数计算
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2  # 20%
        view_base = views * coefficient2
        
        base_value = max(follower_base, view_base)
        if base_value <= 0:
            return 0.0
            
        score = min((saves / base_value) * 10000, 100)
        return max(0.0, score)
        
    def calculate_save_score_with_details(self, saves: int, views: int, follower_count: int = 0) -> tuple:
        """计算保存数得分并返回详细计算过程"""
        if views <= 0:
            details = {
                "原始数据": f"保存数: {saves:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "播放量为0，无法计算保存得分",
                "最终得分": "0.00"
            }
            return 0.0, details
        
        if follower_count <= 0:
            save_rate = saves / views
            score = min(save_rate * 10000, 100)
            score = max(0.0, score)
            details = {
                "原始数据": f"保存数: {saves:,}, 播放量: {views:,}, 粉丝数: {follower_count}",
                "计算方式": "无粉丝数据时的计算",
                "保存率": f"{saves:,} / {views:,} = {save_rate:.6f}",
                "公式": "min(保存率 × 10000, 100)",
                "计算过程": f"min({save_rate:.6f} × 10000, 100) = min({save_rate*10000:.2f}, 100) = {score:.2f}",
                "最终得分": f"{score:.2f}"
            }
            return score, details
        
        coefficient1 = self._get_follower_coefficient(follower_count)
        coefficient2 = self._get_view_coefficient(views)
        
        follower_base = follower_count * coefficient1 * 0.2
        view_base = views * coefficient2
        base_value = max(follower_base, view_base)
        
        if base_value <= 0:
            details = {
                "原始数据": f"保存数: {saves:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
                "错误": "基准值计算为0，无法计算保存得分",
                "最终得分": "0.00"
            }
            return 0.0, details
            
        score = min((saves / base_value) * 10000, 100)
        score = max(0.0, score)
        
        details = {
            "原始数据": f"保存数: {saves:,}, 播放量: {views:,}, 粉丝数: {follower_count:,}",
            "系数1选择过程": f"粉丝数{follower_count:,} → {self._get_follower_tier_description(follower_count)}",
            "系数2选择过程": f"播放量{views:,} → {self._get_view_tier_description(views)}",
            "粉丝基准系数": f"{coefficient1}",
            "播放量基准系数": f"{coefficient2}",
            "粉丝基准值": f"{follower_count:,} × {coefficient1} × 20% = {follower_base:.2f}",
            "播放量基准值": f"{views:,} × {coefficient2} = {view_base:.2f}",
            "最终基准值": f"max({follower_base:.2f}, {view_base:.2f}) = {base_value:.2f}",
            "公式": "min((保存数 / max(粉丝数×系数1×20%, 播放量×系数2)) × 10000, 100)",
            "计算过程": f"min(({saves:,} / {base_value:.2f}) × 10000, 100) = min({saves/base_value*10000:.2f}, 100) = {score:.2f}",
            "最终得分": f"{score:.2f}"
        }
        return score, details
        
    def calculate_completion_score(self, completion_rate: float) -> float:
        """计算完播率得分
        
        评分公式：min(completion_rate * 100 * 1.43, 100)
        基准逻辑：>70%为优秀, >80%为极佳
        - 基于TikTok算法重要性，70%完播率为满分
        - 系数 = 100 / 70 = 1.43
        
        Args:
            completion_rate: 完播率 (0-1)
            
        Returns:
            完播率得分 (0-100)
        """
        if completion_rate <= 0:
            return 0.0
            
        score = min(completion_rate * 100 * 1.43, 100)
        return max(0.0, score)
        
    def calculate_single_video_score(self, 
                                   video: VideoDetail, 
                                   follower_count: int) -> ContentInteractionScore:
        """计算单个视频的内容互动得分
        
        权重分配：
        - 视频播放量：10%
        - 点赞数：25%
        - 评论数：30%
        - 分享数：35%
        
        Args:
            video: 视频详情
            follower_count: 粉丝数量
            
        Returns:
            内容互动评分对象
        """
        # 计算各项得分
        view_score = self.calculate_view_score(video.view_count, follower_count)
        like_score = self.calculate_like_score(video.like_count, video.view_count, follower_count)
        comment_score = self.calculate_comment_score(video.comment_count, video.view_count, follower_count)
        share_score = self.calculate_share_score(video.share_count, video.view_count, follower_count)
        
        # 权重计算总分
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.25 +      # 点赞权重25%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.35       # 分享权重35%
        )
        
        logger.info(f"视频 {video.video_id} 互动评分 - 播放: {view_score:.2f}, "
                   f"点赞: {like_score:.2f}, 评论: {comment_score:.2f}, "
                   f"分享: {share_score:.2f}, 总分: {total_score:.2f}")
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            total_score=total_score
        )
        
    def calculate_average_content_score(self, 
                                       videos: List[VideoDetail], 
                                       follower_count: int) -> ContentInteractionScore:
        """计算平均内容互动得分
        
        基于多个视频的平均表现计算得分
        
        Args:
            videos: 视频详情列表
            follower_count: 粉丝数量
            
        Returns:
            平均内容互动评分对象
        """
        if not videos:
            return ContentInteractionScore(
                view_score=0.0,
                like_score=0.0,
                comment_score=0.0,
                share_score=0.0,
                save_score=0.0,
                total_score=0.0
            )
            
        # 计算总数据
        total_views = sum(video.view_count for video in videos)
        total_likes = sum(video.like_count for video in videos)
        total_comments = sum(video.comment_count for video in videos)
        total_shares = sum(video.share_count for video in videos)
        
        # 计算平均值
        avg_views = total_views / len(videos)
        avg_likes = total_likes / len(videos)
        avg_comments = total_comments / len(videos)
        avg_shares = total_shares / len(videos)
        
        # 计算总数据（添加保存数）
        total_saves = sum(getattr(video, 'collect_count', 0) or 0 for video in videos)  # 使用collect_count作为保存数
        avg_saves = total_saves / len(videos)
        
        # 计算各项得分
        view_score = self.calculate_view_score(int(avg_views), follower_count)
        like_score = self.calculate_like_score(int(avg_likes), int(avg_views))
        comment_score = self.calculate_comment_score(int(avg_comments), int(avg_views))
        share_score = self.calculate_share_score(int(avg_shares), int(avg_views))
        save_score = self.calculate_save_score(int(avg_saves), int(avg_views))
        
        # 权重计算总分（新权重配置）
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        # 详细计算过程日志
        logger.info(f"📊 内容互动评分计算详情（基于累计值）:")
        logger.info(f"   • 累计播放量: {total_views:,} → 得分: {view_score:.2f} × 10% = {view_score * 0.10:.2f}")
        logger.info(f"   • 累计点赞数: {total_likes:,} → 得分: {like_score:.2f} × 15% = {like_score * 0.15:.2f}")
        logger.info(f"   • 累计评论数: {total_comments:,} → 得分: {comment_score:.2f} × 30% = {comment_score * 0.30:.2f}")
        logger.info(f"   • 累计分享数: {total_shares:,} → 得分: {share_score:.2f} × 30% = {share_score * 0.30:.2f}")
        logger.info(f"   • 累计保存数: {total_saves:,} → 得分: {save_score:.2f} × 15% = {save_score * 0.15:.2f}")
        logger.info(f"   • 内容互动总分: {total_score:.2f}")
        
        # 构建详细计算过程
        calculation_details = {
            "累计播放量": f"{total_views:,}",
            "累计点赞数": f"{total_likes:,}",
            "累计评论数": f"{total_comments:,}",
            "累计分享数": f"{total_shares:,}",
            "累计保存数": f"{total_saves:,}",
            "播放量得分计算": f"{view_score:.2f} × 10% = {view_score * 0.10:.2f}",
            "点赞得分计算": f"{like_score:.2f} × 15% = {like_score * 0.15:.2f}",
            "评论得分计算": f"{comment_score:.2f} × 30% = {comment_score * 0.30:.2f}",
            "分享得分计算": f"{share_score:.2f} × 30% = {share_score * 0.30:.2f}",
            "保存得分计算": f"{save_score:.2f} × 15% = {save_score * 0.15:.2f}",
            "内容互动总分": f"{total_score:.2f}"
        }
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            save_score=save_score,
            total_score=total_score,
            calculation_details=calculation_details
        )
        
    def calculate_weighted_content_score(self, 
                                        videos: List[VideoDetail], 
                                        follower_count: int,
                                        recent_weight: float = 0.7) -> ContentInteractionScore:
        """计算加权内容互动得分
        
        给最近的视频更高的权重
        
        Args:
            videos: 视频详情列表（按时间排序，最新的在前）
            follower_count: 粉丝数量
            recent_weight: 最近视频的权重
            
        Returns:
            加权内容互动评分对象
        """
        if not videos:
            return ContentInteractionScore(
                view_score=0.0,
                like_score=0.0,
                comment_score=0.0,
                share_score=0.0,
                save_score=0.0,
                total_score=0.0
            )
            
        # 按时间排序（最新的在前）
        sorted_videos = sorted(videos, key=lambda x: x.create_time, reverse=True)
        
        total_weight = 0.0
        weighted_views = 0.0
        weighted_likes = 0.0
        weighted_comments = 0.0
        weighted_shares = 0.0
        weighted_saves = 0.0
        
        for i, video in enumerate(sorted_videos):
            # 计算权重：最新的视频权重最高
            weight = recent_weight ** i
            total_weight += weight
            
            weighted_views += video.view_count * weight
            weighted_likes += video.like_count * weight
            weighted_comments += video.comment_count * weight
            weighted_shares += video.share_count * weight
            weighted_saves += (getattr(video, 'collect_count', 0) or 0) * weight
            
        # 计算累计值（按文档要求使用累计值而非平均值）
        total_views = sum(video.view_count for video in sorted_videos)
        total_likes = sum(video.like_count for video in sorted_videos)
        total_comments = sum(video.comment_count for video in sorted_videos)
        total_shares = sum(video.share_count for video in sorted_videos)
        total_saves = sum(getattr(video, 'collect_count', 0) or 0 for video in sorted_videos)
        
        # 计算各项得分（基于累计值）
        view_score = self.calculate_view_score(total_views, follower_count)
        like_score = self.calculate_like_score(total_likes, total_views)
        comment_score = self.calculate_comment_score(total_comments, total_views)
        share_score = self.calculate_share_score(total_shares, total_views)
        save_score = self.calculate_save_score(total_saves, total_views)
        
        # 权重计算总分（新权重配置）
        total_score = (
            view_score * 0.10 +      # 播放量权重10%
            like_score * 0.15 +      # 点赞权重15%
            comment_score * 0.30 +   # 评论权重30%
            share_score * 0.30 +     # 分享权重30%
            save_score * 0.15        # 保存权重15%
        )
        
        # 详细计算过程日志
        logger.info(f"📊 内容互动评分计算详情（基于累计值）:")
        logger.info(f"   • 累计播放量: {total_views:,} → 得分: {view_score:.2f} × 10% = {view_score * 0.10:.2f}")
        logger.info(f"   • 累计点赞数: {total_likes:,} → 得分: {like_score:.2f} × 15% = {like_score * 0.15:.2f}")
        logger.info(f"   • 累计评论数: {total_comments:,} → 得分: {comment_score:.2f} × 30% = {comment_score * 0.30:.2f}")
        logger.info(f"   • 累计分享数: {total_shares:,} → 得分: {share_score:.2f} × 30% = {share_score * 0.30:.2f}")
        logger.info(f"   • 累计保存数: {total_saves:,} → 得分: {save_score:.2f} × 15% = {save_score * 0.15:.2f}")
        logger.info(f"   • 内容互动总分: {total_score:.2f}")
        
        return ContentInteractionScore(
            view_score=view_score,
            like_score=like_score,
            comment_score=comment_score,
            share_score=share_score,
            save_score=save_score,
            total_score=total_score
        )