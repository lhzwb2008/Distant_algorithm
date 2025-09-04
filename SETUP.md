# 🚀 Distant Algorithm 设置指南

## 📋 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd Distant_algorithm

# 安装依赖
pip install -r requirements.txt
```

### 2. API密钥配置

**重要：API密钥通过 `.env` 文件配置，确保安全性**

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入真实的API密钥
nano .env  # 或使用你喜欢的编辑器
```

在 `.env` 文件中配置以下必需的API密钥：

```bash
# TiKhub API密钥（必填）
TIKHUB_API_KEY=your_actual_tikhub_api_key_here

# OpenRouter API密钥（必填 - 用于AI视频质量评分）
OPENROUTER_API_KEY=your_actual_openrouter_api_key_here
```

### 3. 获取API密钥

#### TiKhub API密钥
1. 访问 [TiKhub官网](https://tikhub.io)
2. 注册账户并登录
3. 获取API密钥
4. 将密钥填入 `.env` 文件的 `TIKHUB_API_KEY`

#### OpenRouter API密钥
1. 访问 [OpenRouter官网](https://openrouter.ai)
2. 注册账户并登录
3. 在API Keys页面创建新的API密钥
4. 将密钥填入 `.env` 文件的 `OPENROUTER_API_KEY`

### 4. 验证配置

运行配置验证工具确保设置正确：

```bash
python3 check_config.py
```

如果看到 "🎉 所有配置都正确设置！"，说明配置成功。

## 🎯 功能使用

### 字幕提取工具

```bash
# 测试视频字幕提取
python3 quick_subtitle_test.py "https://www.tiktok.com/@user/video/1234567890"

# 或使用视频ID
python3 quick_subtitle_test.py 1234567890
```

### Web应用

```bash
# 启动Web界面
python3 web_app.py

# 访问 http://localhost:5000
```

### 评分系统

```bash
# 运行示例评分
python3 example.py
```

## 🔒 安全说明

- ✅ `.env` 文件已在 `.gitignore` 中，不会被提交到Git
- ✅ 代码中不包含硬编码的API密钥
- ✅ 所有敏感信息通过环境变量配置

## ⚠️ 注意事项

1. **不要将 `.env` 文件提交到Git**
2. **不要在代码中硬编码API密钥**
3. **定期更换API密钥以确保安全**
4. **确保 `.env` 文件权限设置正确** (`chmod 600 .env`)

## 🛠️ 故障排除

### API密钥相关问题

```bash
# 检查配置
python3 check_config.py

# 常见错误：
# - "User not found" → API密钥无效或过期
# - "401 Unauthorized" → API密钥格式错误
# - "API key is required" → .env文件中未配置密钥
```

### 网络连接问题

```bash
# 测试API连接
curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models
```

## 📞 技术支持

如果遇到问题：

1. 首先运行 `python3 check_config.py` 检查配置
2. 查看错误日志获取详细信息
3. 确认API密钥有效且有足够余额
4. 检查网络连接和防火墙设置

---

🎉 配置完成后，您就可以开始使用 Distant Algorithm 的所有功能了！
