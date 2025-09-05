# 🔒 安全指南

## ⚠️ 重要提醒

**永远不要将包含API密钥的`.env`文件提交到Git！**

## 🚨 如果API密钥被意外提交到GitHub

### 立即行动清单

1. **🔑 立即更换API密钥**
   - TiKhub: https://tikhub.io
   - OpenRouter: https://openrouter.ai
   - OpenAI: https://platform.openai.com/api-keys
   
2. **🗑️ 从Git中移除敏感文件**
   ```bash
   git rm --cached .env
   git commit -m "Remove .env file from tracking"
   git push origin main
   ```

3. **🧹 清理Git历史（可选但推荐）**
   ```bash
   # 警告：这会重写Git历史，需要强制推送
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch .env' \
   --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

## 🛡️ 预防措施

### 1. 正确的文件结构

```
✅ 正确做法:
.env                    # 本地配置，包含真实API密钥（不提交）
.env.example           # 配置模板（可以提交）
.gitignore             # 确保包含 .env

❌ 错误做法:
.env 被提交到Git      # 会暴露API密钥
```

### 2. 检查.gitignore

确保`.gitignore`文件包含：
```
# Environment variables
.env
.env.local
.env.*.local

# API Keys
*.key
secrets/
```

### 3. 提交前检查

每次提交前运行：
```bash
# 检查将要提交的文件
git status

# 确保.env不在其中
git diff --cached --name-only | grep -E "\.(env|key)$"
```

### 4. 使用Git钩子

创建`.git/hooks/pre-commit`文件：
```bash
#!/bin/bash
if git diff --cached --name-only | grep -E "\.(env|key)$"; then
    echo "❌ 错误：检测到敏感文件！"
    echo "请检查是否意外添加了.env或密钥文件"
    exit 1
fi
```

## 🔍 安全检查工具

### 检查当前状态
```bash
# 运行配置检查工具
python3 check_config.py

# 检查Git状态
git status

# 检查是否有敏感文件被跟踪
git ls-files | grep -E "\.(env|key)$"
```

### 检查GitHub历史
1. 访问你的GitHub仓库
2. 点击"Commits"
3. 检查最近的提交是否包含敏感文件

## 📋 最佳实践

### ✅ 正确的工作流程

1. **初始设置**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入真实API密钥
   nano .env
   ```

2. **确认.gitignore**
   ```bash
   echo ".env" >> .gitignore
   git add .gitignore
   git commit -m "Update .gitignore"
   ```

3. **每次提交前**
   ```bash
   git status  # 确认没有.env文件
   git add .   # 添加文件
   git commit -m "Your commit message"
   git push origin main
   ```

### ❌ 避免的错误

- `git add .` 时没有检查文件列表
- 直接 `git add .env`
- 忘记配置 `.gitignore`
- 使用 `git add -A` 或 `git add --all` 而不检查

## 🆘 紧急响应

如果发现API密钥泄露：

1. **立即更换所有API密钥**
2. **检查API使用日志是否有异常**
3. **从Git历史中彻底移除敏感信息**
4. **通知团队成员更新本地配置**

## 📞 联系方式

如有安全问题，请立即：
1. 停止使用泄露的API密钥
2. 联系API提供商报告安全事件
3. 更新所有相关系统的密钥

---

🔐 **记住：安全是每个人的责任！**
