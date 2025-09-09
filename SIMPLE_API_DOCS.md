# TikTok创作者评分API文档

## 概述

这是一个简化的TikTok创作者评分API，提供基于`secUid`的评分计算功能。API会返回完整的评分数据，包括总分、各项评分详情和AI质量评分理由。

## API接口

### 1. 计算创作者评分

#### 方法调用

```python
from simple_score_api import SimpleScoreAPI

api = SimpleScoreAPI()

# 基础调用（无关键词筛选）
result = api.calculate_score_by_secuid(sec_uid="MS4wLjABAAAA...")

# 带关键词筛选的调用
result = api.calculate_score_by_secuid(
    sec_uid="MS4wLjABAAAA...", 
    keyword="crypto"
)

# 获取JSON格式结果
json_result = api.get_score_json(
    sec_uid="MS4wLjABAAAA...", 
    keyword="crypto"
)
```

#### 命令行调用

```bash
# 基础调用
python simple_score_api.py "MS4wLjABAAAA..."

# 带关键词筛选
python simple_score_api.py "MS4wLjABAAAA..." "crypto"
```

## 输入参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| `sec_uid` | string | 是 | TikTok用户的secUid（格式如：MS4wLjABAAAA...） |
| `keyword` | string | 否 | 关键词筛选，用于筛选包含特定关键词的视频进行评分 |

## 输出格式

### 成功响应

```json
{
  "success": true,
  "timestamp": "2025-01-09T15:30:45.123456",
  "sec_uid": "MS4wLjABAAAA...",
  "keyword": "crypto",
  "scores": {
    "total_score": 85.67,
    "account_quality": {
      "score": 82.15,
      "follower_score": 79.59,
      "likes_score": 100.0,
      "posting_score": 51.58,
      "multiplier": 3.0
    },
    "content_interaction": {
      "score": 21.37,
      "view_score": 100.0,
      "like_score": 24.86,
      "comment_score": 12.84,
      "share_score": 9.39,
      "save_score": 6.48
    },
    "performance_metrics": {
      "peak_performance": 95.2,
      "recent_performance": 88.1,
      "overall_performance": 85.67
    }
  },
  "user_info": {
    "username": "example_user",
    "video_count": 25,
    "calculated_at": "2025-01-09T15:30:45.123456"
  },
  "ai_quality_scores": {
    "video_id_1": {
      "total_score": 82.5,
      "keyword_score": 85.0,
      "originality_score": 80.0,
      "clarity_score": 85.0,
      "spam_score": 95.0,
      "promotion_score": 70.0,
      "reasoning": "该视频在关键词相关性方面表现良好，内容原创性较高，表达清晰。检测到轻微的推广内容，但整体质量较高。"
    },
    "video_id_2": {
      "total_score": 78.2,
      "keyword_score": 75.0,
      "originality_score": 82.0,
      "clarity_score": 80.0,
      "spam_score": 90.0,
      "promotion_score": 65.0,
      "reasoning": "视频内容与关键词相关度中等，原创性较好，表达较为清晰。存在一定的推广元素。"
    }
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "无法获取用户信息: API请求失败",
  "timestamp": "2025-01-09T15:30:45.123456",
  "sec_uid": "MS4wLjABAAAA...",
  "keyword": "crypto"
}
```

## 响应字段说明

### 评分相关字段

| 字段路径 | 类型 | 描述 |
|----------|------|------|
| `scores.total_score` | number | 最终总评分（0-100分） |
| `scores.account_quality.score` | number | 账户质量总分 |
| `scores.account_quality.follower_score` | number | 粉丝质量评分 |
| `scores.account_quality.activity_score` | number | 活跃度评分 |
| `scores.account_quality.content_score` | number | 内容质量评分 |
| `scores.account_quality.engagement_score` | number | 互动质量评分 |
| `scores.content_interaction.score` | number | 内容互动总分 |
| `scores.content_interaction.avg_views` | number | 平均播放量 |
| `scores.content_interaction.avg_likes` | number | 平均点赞数 |
| `scores.content_interaction.avg_comments` | number | 平均评论数 |
| `scores.content_interaction.avg_shares` | number | 平均分享数 |
| `scores.content_interaction.engagement_rate` | number | 平均互动率（%） |

### 性能指标字段

| 字段路径 | 类型 | 描述 |
|----------|------|------|
| `scores.performance_metrics.peak_performance` | number | 峰值表现评分 |
| `scores.performance_metrics.recent_performance` | number | 近期表现评分 |
| `scores.performance_metrics.overall_performance` | number | 整体表现评分 |

### AI质量评分字段

| 字段路径 | 类型 | 描述 |
|----------|------|------|
| `ai_quality_scores.{video_id}.total_score` | number | AI评分总分（0-100分） |
| `ai_quality_scores.{video_id}.keyword_score` | number | 关键词相关性评分 |
| `ai_quality_scores.{video_id}.originality_score` | number | 内容原创性评分 |
| `ai_quality_scores.{video_id}.clarity_score` | number | 表达清晰度评分 |
| `ai_quality_scores.{video_id}.spam_score` | number | 垃圾信息识别评分（越高越好） |
| `ai_quality_scores.{video_id}.promotion_score` | number | 推广内容识别评分（越高表示非推广） |
| `ai_quality_scores.{video_id}.reasoning` | string | AI评分的详细理由说明 |

## 评分算法说明

### 总评分计算公式

```
TikTok Creator Score = (内容互动数据 × 65% + 内容质量 × 35%) × 账户质量加权
```

### 各项评分说明

1. **账户质量评分**：基于粉丝数量、账户活跃度、内容发布频率等因素
2. **内容互动评分**：基于视频的播放量、点赞数、评论数、分享数等互动数据
3. **AI质量评分**：使用AI模型对视频内容进行质量评估，包括原创性、清晰度等维度

## 使用示例

### Python集成示例

```python
from simple_score_api import SimpleScoreAPI

def analyze_creator(sec_uid, keyword=None):
    api = SimpleScoreAPI()
    result = api.calculate_score_by_secuid(sec_uid, keyword)
    
    if result['success']:
        print(f"用户: {result['user_info']['username']}")
        print(f"总评分: {result['scores']['total_score']}")
        print(f"账户质量: {result['scores']['account_quality']['score']}")
        print(f"内容互动: {result['scores']['content_interaction']['score']}")
        
        # 显示AI质量评分
        for video_id, quality in result['ai_quality_scores'].items():
            print(f"视频 {video_id}: {quality['total_score']} - {quality['reasoning']}")
    else:
        print(f"评分失败: {result['error']}")

# 使用示例
analyze_creator("MS4wLjABAAAA...", "crypto")
```

### 命令行使用示例

```bash
# 基础评分
python simple_score_api.py "MS4wLjABAAAA..."

# 带关键词筛选的评分
python simple_score_api.py "MS4wLjABAAAA..." "crypto"
```

## 注意事项

1. **secUid格式**：必须是有效的TikTok secUid格式（通常以"MS4wLjABAAAA"开头）
2. **关键词筛选**：当提供关键词时，只会对包含该关键词的视频进行AI质量评分
3. **API限制**：评分计算依赖于TikTok API，可能受到API限制影响
4. **计算时间**：完整的评分计算可能需要30-60秒，请耐心等待
5. **兼容性**：此API不会影响现有的任何功能，可以安全集成

## 错误处理

API会返回详细的错误信息，常见错误类型：

- `无效的secUid格式`
- `无法获取用户信息`
- `API请求失败`
- `视频数据获取失败`

建议在集成时添加适当的错误处理逻辑。
