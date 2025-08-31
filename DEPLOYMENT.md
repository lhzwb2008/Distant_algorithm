# TikTok创作者评分系统 - Linux服务器部署指南

本指南将帮助您在Linux服务器上快速部署TikTok创作者评分系统。

## 📋 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 9+ / CentOS 7+
- **内存**: 最少1GB RAM
- **存储**: 最少2GB可用空间
- **网络**: 需要访问外网（用于安装依赖包）
- **权限**: 需要root权限

## 🚀 快速部署

### 1. 准备部署文件

将项目文件上传到服务器，或使用git克隆：

```bash
# 方法1: 使用git克隆（推荐）
git clone <your-repository-url>
cd <project-directory>

# 方法2: 手动上传文件
# 将所有项目文件上传到服务器的某个目录
```

### 2. 运行一键部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy.sh start.sh

# 运行部署脚本
sudo bash deploy.sh
```

部署脚本将自动完成以下操作：
- ✅ 更新系统包
- ✅ 安装Python3、pip、nginx等依赖
- ✅ 创建应用目录 `/opt/tiktok-creator-score`
- ✅ 设置Python虚拟环境
- ✅ 安装项目依赖
- ✅ 创建系统服务用户
- ✅ 配置systemd服务
- ✅ 配置Nginx反向代理（80端口）
- ✅ 配置防火墙规则

### 3. 启动服务

```bash
# 使用一键启动脚本
sudo bash start.sh

# 或者手动启动
sudo systemctl start tiktok-creator-score
```

## 🎛️ 服务管理

### 使用一键管理脚本

```bash
# 启动服务
sudo bash start.sh start

# 停止服务
sudo bash start.sh stop

# 重启服务
sudo bash start.sh restart

# 查看服务状态
sudo bash start.sh status

# 查看服务日志
sudo bash start.sh logs

# 显示帮助信息
sudo bash start.sh help
```

### 使用systemctl命令

```bash
# 启动服务
sudo systemctl start tiktok-creator-score

# 停止服务
sudo systemctl stop tiktok-creator-score

# 重启服务
sudo systemctl restart tiktok-creator-score

# 查看服务状态
sudo systemctl status tiktok-creator-score

# 开机自启动
sudo systemctl enable tiktok-creator-score

# 禁用开机自启动
sudo systemctl disable tiktok-creator-score
```

## 📊 访问系统

部署完成后，您可以通过以下方式访问系统：

- **Web界面**: `http://your-server-ip`
- **本地访问**: `http://localhost`（在服务器上）

## 📝 日志管理

### 查看应用日志

```bash
# 实时查看日志
sudo journalctl -u tiktok-creator-score -f

# 查看最近的日志
sudo journalctl -u tiktok-creator-score -n 100

# 查看今天的日志
sudo journalctl -u tiktok-creator-score --since today
```

### 查看Nginx日志

```bash
# 查看访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

## 🔧 配置文件位置

- **应用目录**: `/opt/tiktok-creator-score`
- **systemd服务文件**: `/etc/systemd/system/tiktok-creator-score.service`
- **Nginx配置文件**: `/etc/nginx/sites-available/tiktok-creator-score`
- **环境配置**: `/opt/tiktok-creator-score/.env`

## 🔒 安全配置

### 防火墙设置

```bash
# 查看防火墙状态
sudo ufw status

# 允许HTTP访问
sudo ufw allow 80/tcp

# 允许SSH访问
sudo ufw allow 22/tcp

# 启用防火墙
sudo ufw enable
```

### SSL证书配置（可选）

如果需要HTTPS访问，可以使用Let's Encrypt：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🛠️ 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查服务状态
   sudo systemctl status tiktok-creator-score
   
   # 查看详细日志
   sudo journalctl -u tiktok-creator-score -n 50
   ```

2. **端口被占用**
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep :8080
   sudo netstat -tlnp | grep :80
   ```

3. **权限问题**
   ```bash
   # 重新设置权限
   sudo chown -R tiktok-score:tiktok-score /opt/tiktok-creator-score
   ```

4. **依赖安装失败**
   ```bash
   # 手动安装依赖
   cd /opt/tiktok-creator-score
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 重新部署

如果需要重新部署：

```bash
# 停止服务
sudo bash start.sh stop

# 备份配置（可选）
sudo cp /opt/tiktok-creator-score/.env /tmp/backup.env

# 重新运行部署脚本
sudo bash deploy.sh

# 恢复配置（如果有备份）
sudo cp /tmp/backup.env /opt/tiktok-creator-score/.env

# 启动服务
sudo bash start.sh start
```

## 📈 性能优化

### Nginx优化

编辑 `/etc/nginx/sites-available/tiktok-creator-score`：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 增加客户端最大请求大小
    client_max_body_size 100M;
    
    # 启用gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 系统资源监控

```bash
# 查看系统资源使用情况
top
htop

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志和应用日志
3. 确保系统满足最低要求
4. 联系技术支持团队

---

**部署完成后，您的TikTok创作者评分系统就可以正常使用了！** 🎉