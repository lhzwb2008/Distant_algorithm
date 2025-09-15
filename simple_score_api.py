#!/usr/bin/env python3
"""
简化的TikTok创作者评分API
提供基于secUid的评分计算接口，返回完整的评分数据和AI质量评分理由
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleScoreAPI:
    """简化的评分API类"""
    
    def __init__(self):
        """初始化API"""
        self.calculator = CreatorScoreCalculator()
        logger.info("SimpleScoreAPI initialized")
    
    def calculate_score_by_secuid(self, sec_uid: str, keyword: str = None) -> Dict[str, Any]:
        """
        根据secUid计算创作者评分
        
        Args:
            sec_uid: TikTok用户的secUid
            keyword: 可选的关键词筛选
            
        Returns:
            包含完整评分数据的字典
        """
        try:
            logger.info(f"开始计算secUid {sec_uid[:20]}... 的评分")
            
            # 使用现有的评分计算方法
            try:
                result = self.calculator.calculate_creator_score_by_user_id_with_ai_scores(
                    sec_uid, keyword=keyword
                )
                logger.info(f"方法返回结果类型: {type(result)}, 长度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                logger.info(f"返回结果内容: {result}")
                
                # 检查返回结果的结构
                if not isinstance(result, (tuple, list)):
                    logger.error(f"返回结果不是元组或列表: {type(result)}")
                    raise ValueError(f"期望返回元组，但得到: {type(result)}")
                
                if len(result) != 5:
                    logger.error(f"返回结果长度错误: 期望5个值，实际得到{len(result)}个值")
                    logger.error(f"返回结果详情: {[type(item) for item in result]}")
                    raise ValueError(f"期望5个返回值，但得到{len(result)}个值")
                
                creator_score, ai_quality_scores, video_details, user_profile, total_fetched_videos = result
            except ValueError as ve:
                logger.error(f"解包返回值时出错: {ve}")
                raise
            except Exception as e:
                logger.error(f"调用calculate_creator_score_by_user_id_with_ai_scores时出错: {e}")
                raise
            
            # 构建响应数据
            response_data = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "sec_uid": sec_uid,
                "keyword": keyword or "无关键词筛选",
                "scores": {
                    "total_score": round(creator_score.final_score, 2),
                    "account_quality": {
                        "score": round(creator_score.account_quality.total_score, 2),
                        "follower_score": round(creator_score.account_quality.follower_score, 2),
                        "likes_score": round(creator_score.account_quality.likes_score, 2),
                        "posting_score": round(creator_score.account_quality.posting_score, 2),
                        "multiplier": round(creator_score.account_quality.multiplier, 2)
                    },
                    "content_interaction": {
                        "score": round(creator_score.content_interaction.total_score, 2),
                        "view_score": round(creator_score.content_interaction.view_score, 2),
                        "like_score": round(creator_score.content_interaction.like_score, 2),
                        "comment_score": round(creator_score.content_interaction.comment_score, 2),
                        "share_score": round(creator_score.content_interaction.share_score, 2),
                        "save_score": round(creator_score.content_interaction.save_score, 2)
                    },
                    "performance_metrics": {
                        "peak_performance": round(creator_score.peak_performance, 2),
                        "recent_performance": round(creator_score.recent_performance, 2),
                        "overall_performance": round(creator_score.overall_performance, 2)
                    }
                },
                "user_info": {
                    "username": creator_score.username,
                    "video_count": creator_score.video_count,
                    "total_fetched_videos": total_fetched_videos,
                    "calculated_at": creator_score.calculated_at.isoformat()
                },
                "ai_quality_scores": {}
            }
            
            # 添加AI质量评分和理由
            if ai_quality_scores:
                for video_id, quality_score in ai_quality_scores.items():
                    response_data["ai_quality_scores"][video_id] = {
                        "total_score": round(quality_score.total_score, 2),
                        "keyword_score": round(quality_score.keyword_score, 2),
                        "originality_score": round(quality_score.originality_score, 2),
                        "clarity_score": round(quality_score.clarity_score, 2),
                        "spam_score": round(quality_score.spam_score, 2),
                        "promotion_score": round(quality_score.promotion_score, 2),
                        "reasoning": quality_score.reasoning
                    }
            
            logger.info(f"成功计算评分: {response_data['scores']['total_score']}")
            return response_data
            
        except Exception as e:
            logger.error(f"计算评分时发生错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "sec_uid": sec_uid,
                "keyword": keyword or "无关键词筛选"
            }
    
    def get_score_json(self, sec_uid: str, keyword: str = None) -> str:
        """
        获取JSON格式的评分结果
        
        Args:
            sec_uid: TikTok用户的secUid
            keyword: 可选的关键词筛选
            
        Returns:
            JSON字符串格式的评分结果
        """
        result = self.calculate_score_by_secuid(sec_uid, keyword)
        return json.dumps(result, ensure_ascii=False, indent=2)

def main():
    """命令行测试接口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python simple_score_api.py <sec_uid> [keyword]")
        print("示例: python simple_score_api.py MS4wLjABAAAA... crypto")
        sys.exit(1)
    
    sec_uid = sys.argv[1]
    keyword = sys.argv[2] if len(sys.argv) > 2 else None
    
    api = SimpleScoreAPI()
    result = api.get_score_json(sec_uid, keyword)
    print(result)

if __name__ == "__main__":
    main()
