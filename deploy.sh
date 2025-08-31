#!/bin/bash

# TikTok创作者评分系统 - Linux服务器一键部署脚本
# 作者: TikTok Creator Score System
# 版本: 1.0

set -e  # 遇到错误立即退出

echo "🚀 开始部署 TikTok创作者评分系统..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root权限运行此脚本"
    echo "使用方法: sudo bash deploy.sh"
    exit 1
fi

# 检测操作系统类型
if [ -f /etc/redhat-release ]; then
    OS_TYPE="centos"
    echo "🔍 检测到CentOS/RHEL系统"
elif [ -f /etc/debian_version ]; then
    OS_TYPE="debian"
    echo "🔍 检测到Debian/Ubuntu系统"
else
    echo "❌ 不支持的操作系统"
    exit 1
fi

# 更新系统包
echo "📦 更新系统包..."
if [ "$OS_TYPE" = "centos" ]; then
    yum update -y
    # 安装EPEL仓库
    yum install -y epel-release
else
    apt update && apt upgrade -y
fi

# 安装Python3和相关工具
echo "🐍 安装Python3和相关工具..."
if [ "$OS_TYPE" = "centos" ]; then
    yum install -y python3 python3-pip python3-venv git curl nginx net-tools
    # 确保pip3可用
    if ! command -v pip3 &> /dev/null; then
        yum install -y python3-pip
    fi
else
    apt install -y python3 python3-pip python3-venv git curl nginx net-tools
fi

# 检查项目文件
echo "🔍 检查项目文件..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_DIR="$(pwd)"

# 确定项目目录
if [ -f "$SCRIPT_DIR/web_app.py" ] && [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
    echo "✅ 在脚本目录找到项目文件: $PROJECT_DIR"
elif [ -f "$CURRENT_DIR/web_app.py" ] && [ -f "$CURRENT_DIR/requirements.txt" ]; then
    PROJECT_DIR="$CURRENT_DIR"
    echo "✅ 在当前目录找到项目文件: $PROJECT_DIR"
else
    echo "❌ 未找到项目文件 (web_app.py, requirements.txt)"
    echo "   脚本目录: $SCRIPT_DIR"
    echo "   当前目录: $CURRENT_DIR"
    echo "   请确保在项目根目录运行此脚本"
    exit 1
fi

# 切换到项目目录
echo "📁 切换到项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# 创建Python虚拟环境
echo "🔧 创建Python虚拟环境..."
if python3 -m venv venv 2>/dev/null; then
    echo "✅ 使用venv创建虚拟环境成功"
elif python3 -m virtualenv venv 2>/dev/null; then
    echo "✅ 使用virtualenv创建虚拟环境成功"
else
    echo "⚠️  venv模块不可用，安装virtualenv..."
    if [ "$OS_TYPE" = "centos" ]; then
        yum install -y python3-virtualenv || pip3 install virtualenv
    else
        apt install -y python3-virtualenv || pip3 install virtualenv
    fi
    python3 -m virtualenv venv
    echo "✅ 使用virtualenv创建虚拟环境成功"
fi
source venv/bin/activate

# 安装Python依赖
echo "📚 安装Python依赖..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  未找到requirements.txt，安装基础依赖..."
    pip install flask requests python-dotenv
fi

# 设置文件权限
echo "🔐 设置文件权限..."
if [ -f "start.sh" ]; then
    chmod +x start.sh
fi

# 创建systemd服务文件
echo "⚙️  创建systemd服务..."
cat > /etc/systemd/system/tiktok-creator-score.service << EOF
[Unit]
Description=TikTok Creator Score System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python web_app.py --port=8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 配置Nginx反向代理
echo "🌐 配置Nginx反向代理..."

# 检测Nginx配置目录结构
if [ -d "/etc/nginx/sites-available" ]; then
    # Debian/Ubuntu 系统
    NGINX_CONFIG_FILE="/etc/nginx/sites-available/tiktok-creator-score"
    NGINX_ENABLE_CMD="ln -sf /etc/nginx/sites-available/tiktok-creator-score /etc/nginx/sites-enabled/"
else
    # CentOS/RHEL 系统
    NGINX_CONFIG_FILE="/etc/nginx/conf.d/tiktok-creator-score.conf"
    NGINX_ENABLE_CMD=""  # CentOS不需要启用步骤
fi

echo "📝 创建Nginx配置文件: $NGINX_CONFIG_FILE"
sudo tee $NGINX_CONFIG_FILE > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点（仅适用于Debian/Ubuntu）
if [ -n "$NGINX_ENABLE_CMD" ]; then
    echo "🔗 启用Nginx站点配置..."
    sudo bash -c "$NGINX_ENABLE_CMD"
    sudo rm -f /etc/nginx/sites-enabled/default
else
    echo "✅ CentOS系统：配置文件已直接放置在conf.d目录"
fi

# 测试Nginx配置
echo "🧪 测试Nginx配置..."
nginx -t

# 启用并启动服务
echo "🔄 启用并启动服务..."
systemctl daemon-reload
systemctl enable tiktok-creator-score
systemctl enable nginx
systemctl restart nginx

# 配置防火墙
echo "🔥 配置防火墙..."
if [ "$OS_TYPE" = "centos" ]; then
    # CentOS使用firewalld
    if command -v firewall-cmd &> /dev/null; then
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --reload
        echo "✅ firewalld防火墙配置完成"
    else
        echo "⚠️  firewalld未安装，跳过防火墙配置"
    fi
else
    # Debian/Ubuntu使用ufw
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 22/tcp
        echo "y" | ufw enable
        echo "✅ ufw防火墙配置完成"
    else
        echo "⚠️  ufw未安装，跳过防火墙配置"
    fi
fi

echo "✅ 部署完成！"
echo ""
echo "📋 部署信息:"
echo "   项目目录: $PROJECT_DIR"
echo "   服务名称: tiktok-creator-score"
echo "   Web端口: 80 (通过Nginx代理到8080)"
echo ""
echo "🚀 启动服务:"
echo "   sudo systemctl start tiktok-creator-score"
echo ""
echo "📊 查看服务状态:"
echo "   sudo systemctl status tiktok-creator-score"
echo ""
echo "📝 查看服务日志:"
echo "   sudo journalctl -u tiktok-creator-score -f"
echo ""
echo "🌐 访问地址: http://your-server-ip"
echo ""
echo "💡 使用一键启动脚本: sudo bash start.sh"