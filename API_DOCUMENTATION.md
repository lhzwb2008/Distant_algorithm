# TikTok创作者评分系统 API 接入文档

## 概述

TikTok创作者评分系统提供了完整的REST API，支持同步和异步两种调用方式。系统可以分析TikTok创作者的内容质量、互动数据和账户质量，生成综合评分。

**服务地址**: `http://43.134.78.93:8080`

## API端点列表

### 1. 异步任务提交 (推荐)

**POST** `/submit_task`

提交一个异步评分计算任务，适用于需要长时间处理的场景。

#### 请求参数

```json
{
    "username": "string",    // TikTok用户名（必填）
    "keyword": "string"      // 关键词筛选（可选）
}
```

#### 响应示例

```json
{
    "success": true,
    "task_id": "4845f5c5-be3f-4bf4-868a-d6824fdc44a3",
    "status": "pending",
    "message": "任务已提交，请使用task_id查询结果"
}
```

#### curl 示例

```bash
curl -X POST http://43.134.78.93:8080/submit_task \
  -H "Content-Type: application/json" \
  -d '{"username":"etherstories","keyword":"Amph"}'
```

---

### 2. 任务状态查询

**GET** `/task_status/<task_id>`

查询异步任务的处理状态和结果。

#### 路径参数

- `task_id`: 任务ID（从submit_task接口获得）

#### 响应状态

- `pending`: 任务等待处理
- `processing`: 任务处理中
- `completed`: 任务完成
- `failed`: 任务失败

#### 处理中响应示例

```json
{
    "success": true,
    "task_id": "4845f5c5-be3f-4bf4-868a-d6824fdc44a3",
    "status": "processing",
    "username": "etherstories",
    "keyword": "Amph",
    "created_at": "2025-09-05T18:00:49.959882",
    "progress": "正在分析视频内容..."
}
```

#### 完成响应示例

```json
{
    "success": true,
    "task_id": "4845f5c5-be3f-4bf4-868a-d6824fdc44a3",
    "status": "completed",
    "username": "etherstories",
    "keyword": "Amph",
    "created_at": "2025-09-05T18:00:49.959882",
    "completed_at": "2025-09-05T18:05:30.123456",
    "result": {
        "success": true,
        "username": "etherstories",
        "keyword": "Amph",
        "score": 100.98,
        "sec_uid": "MS4wLjABAAAA-VpxSxRgX5cmrshTJIazUPluZzhOMoxOF9rlAmcA_r6c1e_YemY32IyDJ5lqdW94",
        "breakdown": {
            "最终评分详细计算": {...},
            "AI视频质量评分": {...},
            "内容互动评分": {...},
            "账户质量评分": {...}
        }
    }
}
```

#### curl 示例

```bash
curl http://43.134.78.93:8080/task_status/4845f5c5-be3f-4bf4-868a-d6824fdc44a3
```

---

### 3. 任务列表查询

**GET** `/tasks`

获取所有任务的列表，按创建时间倒序排列。

#### 响应示例

```json
{
    "success": true,
    "total": 5,
    "tasks": [
        {
            "task_id": "4845f5c5-be3f-4bf4-868a-d6824fdc44a3",
            "status": "completed",
            "username": "etherstories",
            "keyword": "Amph",
            "created_at": "2025-09-05T18:00:49.959882",
            "completed_at": "2025-09-05T18:05:30.123456",
            "score": 100.98
        },
        {
            "task_id": "abc123-def456-ghi789",
            "status": "processing",
            "username": "another_user",
            "keyword": "无",
            "created_at": "2025-09-05T17:55:20.123456",
            "progress": "正在分析视频内容..."
        }
    ]
}
```

#### curl 示例

```bash
curl http://43.134.78.93:8080/tasks
```

---

### 4. 同步评分计算 (兼容接口)

**POST** `/calculate_score`

同步计算评分，保持向后兼容。⚠️ **注意**: 此接口可能因为处理时间过长导致超时，建议使用异步接口。

#### 请求参数

```json
{
    "username": "string",    // TikTok用户名（必填）
    "keyword": "string"      // 关键词筛选（可选）
}
```

#### 响应示例

```json
{
    "success": true,
    "username": "etherstories",
    "keyword": "Amph",
    "score": 100.98,
    "sec_uid": "MS4wLjABAAAA-VpxSxRgX5cmrshTJIazUPluZzhOMoxOF9rlAmcA_r6c1e_YemY32IyDJ5lqdW94",
    "breakdown": {
        "最终评分详细计算": {
            "算法说明": "40%峰值表现 + 40%近期状态 + 20%整体水平",
            "视频总数": "2 个",
            "基础分数": "50.49分",
            "账户质量加权": "基础分数 × 2.000 = 100.98",
            "最终评分": "100.98分"
        },
        "AI视频质量评分": {
            "平均AI质量分": "80.5/100",
            "最高AI质量分": "84.0/100",
            "最低AI质量分": "77.0/100",
            "评分视频数": 2,
            "说明": "AI智能评分系统"
        }
    }
}
```

#### curl 示例

```bash
curl -X POST http://43.134.78.93:8080/calculate_score \
  -H "Content-Type: application/json" \
  -d '{"username":"etherstories","keyword":"Amph"}'
```

---

### 5. 主页面

**GET** `/`

返回Web界面主页，提供用户友好的评分界面。

---

## 推荐使用流程

### 异步处理流程 (推荐)

1. **提交任务**: 调用 `POST /submit_task` 获得 `task_id`
2. **轮询状态**: 每5秒调用 `GET /task_status/<task_id>` 检查状态
3. **获取结果**: 当状态为 `completed` 时，从响应中获取评分结果

### JavaScript 示例

```javascript
async function calculateScore(username, keyword) {
    // 1. 提交任务
    const submitResponse = await fetch('/submit_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, keyword })
    });
    
    const submitData = await submitResponse.json();
    if (!submitData.success) {
        throw new Error(submitData.error);
    }
    
    const taskId = submitData.task_id;
    
    // 2. 轮询状态
    return new Promise((resolve, reject) => {
        const checkStatus = async () => {
            try {
                const statusResponse = await fetch(`/task_status/${taskId}`);
                const statusData = await statusResponse.json();
                
                if (statusData.status === 'completed') {
                    resolve(statusData.result);
                } else if (statusData.status === 'failed') {
                    reject(new Error(statusData.error));
                } else {
                    // 继续轮询
                    setTimeout(checkStatus, 5000);
                }
            } catch (error) {
                reject(error);
            }
        };
        
        checkStatus();
    });
}

// 使用示例
calculateScore('etherstories', 'Amph')
    .then(result => console.log('评分结果:', result))
    .catch(error => console.error('错误:', error));
```

### Python 示例

```python
import requests
import time
import json

def calculate_score_async(username, keyword=None):
    base_url = "http://43.134.78.93:8080"
    
    # 1. 提交任务
    submit_data = {"username": username}
    if keyword:
        submit_data["keyword"] = keyword
        
    response = requests.post(f"{base_url}/submit_task", json=submit_data)
    result = response.json()
    
    if not result["success"]:
        raise Exception(result["error"])
    
    task_id = result["task_id"]
    print(f"任务已提交，ID: {task_id}")
    
    # 2. 轮询状态
    while True:
        response = requests.get(f"{base_url}/task_status/{task_id}")
        status_data = response.json()
        
        print(f"状态: {status_data['status']}, 进度: {status_data.get('progress', '')}")
        
        if status_data["status"] == "completed":
            return status_data["result"]
        elif status_data["status"] == "failed":
            raise Exception(status_data["error"])
        
        time.sleep(5)  # 等待5秒后再次检查

# 使用示例
try:
    result = calculate_score_async("etherstories", "Amph")
    print(f"最终评分: {result['score']}")
    print(f"详细结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"错误: {e}")
```

## 错误处理

### 常见错误码

- `400`: 请求参数错误（如用户名为空）
- `404`: 资源不存在（如用户名不存在或任务ID不存在）
- `500`: 服务器内部错误

### 错误响应格式

```json
{
    "success": false,
    "error": "错误描述信息"
}
```

## 性能说明

- **处理时间**: 通常2-6分钟，取决于视频数量和文件大小
- **并发限制**: 系统限制了API调用频率以保证稳定性
- **文件大小**: 支持大文件视频分析（使用Google Gemini AI）
- **超时设置**: 异步接口无超时限制，同步接口5分钟超时

## 系统特性

- ✅ **AI智能分析**: 使用Google Gemini 2.5 Flash进行视频内容分析
- ✅ **多维度评分**: 内容质量、互动数据、账户质量综合评估
- ✅ **关键词筛选**: 支持基于关键词的视频筛选分析
- ✅ **详细报告**: 提供完整的评分计算过程和理由
- ✅ **异步处理**: 避免长时间等待和超时问题
- ✅ **实时进度**: 任务处理进度实时更新

## 技术支持

如有问题请联系系统管理员或查看服务日志获取详细错误信息。

---

**最后更新**: 2025-09-05  
**API版本**: v1.0  
**文档版本**: 1.0
