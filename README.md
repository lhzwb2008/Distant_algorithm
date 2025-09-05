# TikTok Creator Score System

基于TiKhub API的TikTok创作者评分系统，通过分析账户质量和内容互动数据来计算创作者的综合评分。

## 项目概述

本项目实现了一个完整的TikTok创作者评分系统，包含两个主要评分维度：

### 1. 账户质量评分（35%权重）- 作为加权指标
- **粉丝数量**（40%权重）
- **总点赞数**（40%权重） 
- **发布频率**（20%权重）

### 2. 内容互动数据评分（65%权重）
- **视频播放量**（10%权重）
- **点赞率**（15%权重）
- **评论率**（30%权重）
- **分享率**（30%权重）
- **保存率**（15%权重）

### 主评分公式

```
TikTok Creator Score = (内容互动数据 × 65% + 内容质量固定分 × 35%) × 账户质量加权
```

其中：内容质量固定分 = 60分

### 账户质量加权系数

- 0-10分：加权系数 = 1.0
- 10-30分：加权系数 = 1.2
- 31-60分：加权系数 = 1.5
- 61-80分：加权系数 = 2.0
- 81-100分：加权系数 = 3.0

## 详细评分规则

### 账户质量评分（基于最近三个月数据）

#### 1. 粉丝数量评分（40%权重）
**评分公式**: `min(log10(followers) * 10, 100)`

**阈值参考**:
- 1K-10K粉丝：20-30分
- 10K-100K粉丝：30-40分
- 100K-1M粉丝：40-50分
- 1M-10M粉丝：50-60分
- 10M+粉丝：60-100分（满分）

#### 2. 总点赞数评分（40%权重）
**评分公式**: `min(log10(total_likes) * 12.5, 100)`

**阈值参考**:
- 0-1K点赞：0-37.5分（新手区间）
- 1K-10K点赞：37.5-50分（成长区间）
- 10K-100K点赞：50-62.5分（活跃区间）
- 100K-1M点赞：62.5-75分（优质区间）
- 1M-10M点赞：75-87.5分（头部区间）
- 10M+点赞：87.5-100分（顶级区间）

**示例计算**:
- 500点赞：log10(500) × 12.5 = 2.7 × 12.5 = 33.8分
- 5K点赞：log10(5000) × 12.5 = 3.7 × 12.5 = 46.3分
- 50K点赞：log10(50000) × 12.5 = 4.7 × 12.5 = 58.8分
- 500K点赞：log10(500000) × 12.5 = 5.7 × 12.5 = 71.3分

#### 3. 发布频率评分（20%权重）
**评分公式**: `max(0, 100 - abs(weekly_frequency - 21) * 3)`
- 理想频次：21次/周（平均每天3个视频）
- 惩罚系数：3（偏离理想频次1个，扣3分）
- 数据源：最近三个月的视频数据

**示例计算**:
- 每周1个视频：max(0, 100 - 20*3) = 40分
- 每周7个视频：max(0, 100 - 14*3) = 58分
- 每周15个视频：max(0, 100 - 6*3) = 82分
- 每周21个视频：max(0, 100 - 0*3) = 100分（满分）
- 每周27个视频：max(0, 100 - 6*3) = 82分

### 内容互动数据评分（基于最近100条视频）

#### 1. 视频播放量评分（10%权重）
**评分公式**: `min((views / (followers * 基准系数)) * 100, 100)`

**基准系数分层**:
- 0-1千粉丝：基准 = 1.5倍粉丝量
- 1千-1万粉丝：基准 = 1.0倍粉丝量
- 1万-10万粉丝：基准 = 0.8倍粉丝量
- 10万-100万粉丝：基准 = 0.6倍粉丝量
- 100万+粉丝：基准 = 0.4倍粉丝量

**无粉丝数据时**: `min((views / 2000) * 100, 100)`

#### 2. 点赞率评分（15%权重）
**评分公式**: `min((likes / total_views) * 2500, 100)`

**基准逻辑**:
- 4.0%点赞率 = 100分（行业优秀标准）
- 2.0%点赞率 = 50分（行业平均）
- 系数 = 100 / 4.0 * 100 = 2500

#### 3. 评论率评分（30%权重）
**评分公式**: `min((comments / total_views) * 12500, 100)`

**基准逻辑**:
- 评论率通常为点赞率的1/5
- 0.8%评论率 = 100分（优秀标准）
- 系数 = 100 / 0.8 * 100 = 12500

#### 4. 分享率评分（30%权重）
**评分公式**: `min((shares / total_views) * 25000, 100)`

**基准逻辑**:
- 分享率通常为点赞率的1/10
- 0.4%分享率 = 100分（优秀标准）
- 系数 = 100 / 0.4 * 100 = 25000

#### 5. 保存率评分（15%权重）
**评分公式**: `min((saves / total_views) * 10000, 100)`

**基准逻辑**:
- 保存率介于评论率和分享率之间
- 1.0%保存率 = 100分（优秀标准）
- 系数 = 100 / 1.0 * 100 = 10000

## 数据源说明

### 账户质量分数据源
- **时间范围**: 最近三个月的视频数据
- **用途**: 计算发布频率，评估近期活跃度
- **获取方式**: 通过TikHub API分页获取，自动过滤三个月外的视频

### 内容互动分数据源  
- **数据量**: 最近100条视频
- **用途**: 计算播放量、点赞率、评论率、分享率、保存率
- **获取方式**: 通过TikHub API获取用户最新视频列表
- **关键词筛选**: 支持根据关键词筛选特定主题的视频进行评分

## 项目结构

```
tiktok_creator_score/
├── __init__.py                     # 项目初始化
├── config.py                       # 配置文件
├── models.py                       # 数据模型定义
├── api_client.py                   # TiKhub API客户端
├── account_quality_calculator.py   # 账户质量评分计算器
├── content_interaction_calculator.py # 内容互动评分计算器
├── creator_score_calculator.py     # 主评分计算器
├── example.py                      # 使用示例
├── requirements.txt                # 项目依赖
├── .env.example                    # 环境变量模板
├── .env                           # 环境变量配置
├── tests/                         # 单元测试
│   ├── __init__.py
│   ├── test_account_quality_calculator.py
│   ├── test_content_interaction_calculator.py
│   ├── test_creator_score_calculator.py
│   ├── test_api_client.py
│   └── test_score_calculator.py
└── README.md                      # 项目文档
```

## 安装和配置

### 1. 环境要求

- Python 3.7+
- pip

### 2. 安装依赖

```bash
cd tiktok_creator_score
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置您的TiKhub API密钥：

```env
# TiKhub API配置
TIKHUB_API_KEY=your_api_key_here
TIKHUB_BASE_URL=https://api.tikhub.dev

# OpenRouter API配置（用于AI视频质量评分）
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 字幕提取开关（默认关闭）
# 设置为 true 启用字幕提取和AI评分
# 设置为 false 跳过字幕提取（需要自定义视频内容提取方法）
ENABLE_SUBTITLE_EXTRACTION=false

# 数据获取范围配置
ACCOUNT_QUALITY_DAYS=90
CONTENT_INTERACTION_MAX_VIDEOS=100

# 评分权重配置
CONTENT_QUALITY_WEIGHT=0.35
CONTENT_INTERACTION_WEIGHT=0.65
```

## 使用方法

### 快速开始

```python
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient

# 初始化计算器和API客户端
calculator = CreatorScoreCalculator()
api_client = TiKhubAPIClient()

# 计算单个创作者评分
username = "example_user"
score_result = calculator.calculate_creator_score(username, api_client)

print(f"创作者 {username} 的总评分: {score_result['total_score']:.2f}")
print(f"账户质量评分: {score_result['account_quality_score']:.2f}")
print(f"内容互动评分: {score_result['content_interaction_score']:.2f}")
print(f"账户质量加权: {score_result['account_quality_weight']}")
```

### 批量计算评分

```python
# 批量计算多个创作者评分
usernames = ["user1", "user2", "user3"]
batch_results = calculator.calculate_batch_scores(usernames, api_client)

for username, result in batch_results.items():
    if result['success']:
        print(f"{username}: {result['score']['total_score']:.2f}分")
    else:
        print(f"{username}: 计算失败 - {result['error']}")
```

### 手动数据计算

```python
from models import UserProfile, VideoDetail

# 创建用户档案
user_profile = UserProfile(
    username="test_user",
    follower_count=50000,
    total_likes=1000000,
    video_count=100
)

# 创建视频详情列表
video_details = [
    VideoDetail(
        video_id="video1",
        view_count=100000,
        like_count=5000,
        comment_count=500,
        share_count=200
    ),
    # 更多视频...
]

# 计算评分
score_result = calculator.calculate_total_score(user_profile, video_details)
```

## API文档

### CreatorScoreCalculator

主要的评分计算器类。

#### 方法

- `calculate_creator_score(username, api_client, video_limit=10)`: 计算创作者总评分
- `calculate_total_score(user_profile, video_details)`: 基于已有数据计算评分
- `calculate_batch_scores(usernames, api_client, video_limit=10)`: 批量计算评分
- `get_score_breakdown(score_result)`: 获取评分详细分解
- `compare_creators(score_results)`: 比较多个创作者评分

### AccountQualityCalculator

账户质量评分计算器。

#### 方法

- `calculate_account_quality_score(user_profile)`: 计算账户质量总分
- `_calculate_follower_score(followers)`: 计算粉丝数量得分
- `_calculate_total_likes_score(total_likes)`: 计算总点赞数得分
- `_calculate_posting_frequency_score(weekly_frequency)`: 计算发布频率得分

### ContentInteractionCalculator

内容互动评分计算器。

#### 方法

- `calculate_content_interaction_score(video_detail, follower_count)`: 计算单个视频评分
- `calculate_average_content_score(video_details, follower_count)`: 计算平均内容评分
- `calculate_weighted_content_score(video_details, follower_count)`: 计算加权内容评分

### TiKhubAPIClient

TiKhub API客户端。

#### 方法

- `get_user_profile(username)`: 获取用户档案信息
- `get_video_metrics(video_id)`: 获取视频指标数据
- `get_video_detail(video_id)`: 获取视频详情
- `get_user_videos(username, limit=10)`: 获取用户视频列表
- `get_trend_data(username, days=14)`: 获取趋势数据

## 评分算法详解

### 账户质量评分算法

#### 1. 粉丝数量评分（40%权重）

```python
score = min(log10(followers) * 10, 100)
```

- 1K-10K粉丝：20-40分
- 10K-100K粉丝：40-50分
- 100K+粉丝：50-60分
- 上限100分

#### 2. 总点赞数评分（40%权重）

```python
score = min(log10(total_likes) * 12.5, 100)
```

- 500点赞：33.8分
- 5K点赞：46.3分
- 50K点赞：58.8分
- 500K点赞：71.3分
- 5M点赞：83.8分

#### 3. 发布频率评分（20%权重）

```python
score = max(0, 100 - abs(weekly_frequency - 5) * 15)
```

- 理想频次：每周5个视频（满分100）
- 最优范围：3-7次/周

### 内容互动评分算法

#### 1. 视频播放量评分（10%权重）

```python
score = min((views / followers) * 100, 100)
```

- 1.0倍播放量 = 100分（满分）
- 0.5倍播放量 = 50分（及格）

#### 2. 点赞数评分（25%权重）

```python
score = min((likes / views) * 2500, 100)
```

- 4.0%点赞率 = 100分（优秀）
- 2.0%点赞率 = 50分（平均）

#### 3. 评论数评分（30%权重）

```python
score = min((comments / views) * 12500, 100)
```

- 0.8%评论率 = 100分（优秀）
- 基于点赞率的1/5经验数据

#### 4. 分享数评分（35%权重）

```python
score = min((shares / views) * 25000, 100)
```

- 0.4%分享率 = 100分（优秀）
- 基于点赞率的1/10经验数据

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_creator_score_calculator.py

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=.
```

## 示例输出

```json
{
  "total_score": 156.75,
  "account_quality_score": 65.2,
  "content_interaction_score": 78.5,
  "account_quality_weight": 2.0,
  "video_scores": [
    {
      "video_id": "video1",
      "score": 82.3,
      "view_score": 100.0,
      "like_score": 87.5,
      "comment_score": 75.0,
      "share_score": 68.2
    }
  ],
  "score_breakdown": {
    "follower_score": 47.0,
    "total_likes_score": 75.0,
    "posting_frequency_score": 85.0,
    "weighted_account_score": 65.2,
    "weighted_content_score": 78.5
  }
}
```

## 注意事项

1. **API限制**: TiKhub API有请求频率限制，建议合理控制请求频率
2. **数据准确性**: 评分结果基于API返回的数据，请确保数据的时效性
3. **评分范围**: 总评分理论上可以超过100分（由于加权系数的存在）
4. **错误处理**: 系统包含完善的错误处理机制，但仍需注意网络异常情况

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。