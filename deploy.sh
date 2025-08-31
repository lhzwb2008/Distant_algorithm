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

# 创建应用目录
APP_DIR="/opt/tiktok-creator-score"
echo "📁 创建应用目录: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# 如果当前目录有项目文件，复制到部署目录
if [ -f "$(dirname "$0")/web_app.py" ]; then
    echo "📋 复制项目文件..."
    cp -r $(dirname "$0")/* $APP_DIR/
else
    echo "❌ 未找到项目文件，请确保在项目根目录运行此脚本"
    exit 1
fi

# 创建Python虚拟环境
echo "🔧 创建Python虚拟环境..."
python3 -m venv venv
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

# 创建系统服务用户
echo "👤 创建系统服务用户..."
if ! id "tiktok-score" &>/dev/null; then
    useradd --system --shell /bin/false --home $APP_DIR tiktok-score
fi

# 设置文件权限
echo "🔐 设置文件权限..."
chown -R tiktok-score:tiktok-score $APP_DIR
chmod +x $APP_DIR/start.sh

# 创建systemd服务文件
echo "⚙️  创建systemd服务..."
cat > /etc/systemd/system/tiktok-creator-score.service << EOF
[Unit]
Description=TikTok Creator Score System
After=network.target

[Service]
Type=simple
User=tiktok-score
Group=tiktok-score
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python web_app.py --port=8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 配置Nginx反向代理
echo "🌐 配置Nginx反向代理..."
cat > /etc/nginx/sites-available/tiktok-creator-score << EOF
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
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用Nginx站点
ln -sf /etc/nginx/sites-available/tiktok-creator-score /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

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
echo "   应用目录: $APP_DIR"
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