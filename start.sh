#!/bin/bash

# TikTok创作者评分系统 - 一键启动服务脚本
# 作者: TikTok Creator Score System
# 版本: 1.0

set -e  # 遇到错误立即退出

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="tiktok-creator-score"
PORT=8080

# 检测操作系统
OS_TYPE="$(uname -s)"
case "${OS_TYPE}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS_TYPE}"
esac

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否为root用户（Linux环境需要）
check_root() {
    if [ "$MACHINE" = "Linux" ]; then
        if [ "$EUID" -ne 0 ]; then
            print_error "在Linux环境下请使用root权限运行此脚本"
            echo "使用方法: sudo bash start.sh [command]"
            exit 1
        fi
    else
        print_info "检测到 $MACHINE 环境，跳过root权限检查"
    fi
}

# 检查服务状态
check_service_status() {
    if [ "$MACHINE" = "Linux" ]; then
        if systemctl is-active --quiet $SERVICE_NAME; then
            return 0  # 服务正在运行
        else
            return 1  # 服务未运行
        fi
    else
        # macOS环境下检查端口是否被占用
        if lsof -i :$PORT >/dev/null 2>&1; then
            return 0  # 端口被占用，认为服务在运行
        else
            return 1  # 端口未被占用
        fi
    fi
}

# 检查Nginx状态
check_nginx_status() {
    if [ "$MACHINE" = "Linux" ]; then
        if systemctl is-active --quiet nginx; then
            return 0  # Nginx正在运行
        else
            return 1  # Nginx未运行
        fi
    else
        # macOS环境下不需要Nginx，直接返回成功
        return 0
    fi
}

# 启动服务
start_service() {
    print_info "启动TikTok创作者评分系统..."
    
    # 确保在项目目录
    cd "$SCRIPT_DIR"
    
    if [ "$MACHINE" = "Linux" ]; then
        # Linux环境：使用systemctl启动服务
        # 启动应用服务
        if check_service_status; then
            print_warning "应用服务已在运行中"
        else
            systemctl start $SERVICE_NAME
            sleep 2
            if check_service_status; then
                print_success "应用服务启动成功"
            else
                print_error "应用服务启动失败"
                return 1
            fi
        fi
        
        # 启动Nginx
        if check_nginx_status; then
            print_warning "Nginx已在运行中"
        else
            systemctl start nginx
            sleep 1
            if check_nginx_status; then
                print_success "Nginx启动成功"
            else
                print_error "Nginx启动失败"
                return 1
            fi
        fi
    else
        # macOS环境：直接启动Python应用
        if check_service_status; then
            print_warning "应用服务已在运行中（端口 $PORT 被占用）"
        else
            print_info "在macOS环境下直接启动Python Flask应用..."
            
            # 检查Python是否可用
            if ! command -v python3 &> /dev/null; then
                print_error "Python3 未安装或不在PATH中"
                return 1
            fi
            
            # 检查web_app.py是否存在
            if [ ! -f "web_app.py" ]; then
                print_error "web_app.py 文件不存在"
                return 1
            fi
            
            # 后台启动Flask应用
            print_info "后台启动Flask应用，端口: $PORT"
            nohup python3 web_app.py --port $PORT --host 127.0.0.1 > flask_app.log 2>&1 &
            echo $! > flask_app.pid
            
            # 等待应用启动
            sleep 3
            
            if check_service_status; then
                print_success "Python Flask应用启动成功"
                print_info "应用日志文件: $SCRIPT_DIR/flask_app.log"
                print_info "PID文件: $SCRIPT_DIR/flask_app.pid"
            else
                print_error "Python Flask应用启动失败，请检查日志"
                return 1
            fi
        fi
    fi
    
    print_success "所有服务启动完成！"
    show_status
}

# 停止服务
stop_service() {
    print_info "停止TikTok创作者评分系统..."
    
    if [ "$MACHINE" = "Linux" ]; then
        # Linux环境：使用systemctl停止服务
        systemctl stop $SERVICE_NAME
        systemctl stop nginx
    else
        # macOS环境：停止Python应用
        if [ -f "flask_app.pid" ]; then
            local pid=$(cat flask_app.pid)
            if kill -0 $pid 2>/dev/null; then
                print_info "停止Flask应用 (PID: $pid)..."
                kill $pid
                sleep 2
                if kill -0 $pid 2>/dev/null; then
                    print_warning "正常停止失败，强制终止..."
                    kill -9 $pid
                fi
                print_success "Flask应用已停止"
            else
                print_warning "Flask应用进程已不存在"
            fi
            rm -f flask_app.pid
        else
            print_warning "未找到PID文件，尝试通过端口停止..."
            # 通过端口查找并停止进程
            local pids=$(lsof -ti :$PORT)
            if [ -n "$pids" ]; then
                echo "$pids" | xargs kill
                sleep 1
                print_success "通过端口停止了相关进程"
            else
                print_info "端口 $PORT 未被占用"
            fi
        fi
    fi
    
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启TikTok创作者评分系统..."
    
    # 确保在项目目录
    cd "$SCRIPT_DIR"
    
    if [ "$MACHINE" = "Linux" ]; then
        # Linux环境：使用systemctl重启服务
        systemctl restart $SERVICE_NAME
        systemctl restart nginx
        sleep 3
    else
        # macOS环境：先停止再启动
        stop_service
        sleep 2
        start_service
        return $?
    fi
    
    if check_service_status && check_nginx_status; then
        print_success "服务重启成功！"
        show_status
    else
        print_error "服务重启失败，请检查日志"
        return 1
    fi
}

# 显示服务状态
show_status() {
    echo ""
    print_info "=== 服务状态 (${MACHINE}环境) ==="
    
    # 应用服务状态
    if check_service_status; then
        if [ "$MACHINE" = "Mac" ]; then
            print_success "Flask应用: 运行中"
        else
            print_success "应用服务: 运行中"
        fi
    else
        if [ "$MACHINE" = "Mac" ]; then
            print_error "Flask应用: 已停止"
        else
            print_error "应用服务: 已停止"
        fi
    fi
    
    # Nginx状态（仅Linux环境显示）
    if [ "$MACHINE" = "Linux" ]; then
        if check_nginx_status; then
            print_success "Nginx: 运行中"
        else
            print_error "Nginx: 已停止"
        fi
    else
        print_info "Nginx: macOS环境下不需要"
    fi
    
    # 端口监听状态
    if [ "$MACHINE" = "Mac" ]; then
        # macOS环境：使用lsof检查端口
        if lsof -i :$PORT >/dev/null 2>&1; then
            print_success "端口$PORT: 正在监听"
        else
            print_warning "端口$PORT: 未监听"
        fi
    else
        # Linux环境：使用netstat或ss
        if command -v netstat &> /dev/null; then
            if netstat -tlnp | grep -q ":80 "; then
                print_success "端口80: 正在监听"
            else
                print_warning "端口80: 未监听"
            fi
            
            if netstat -tlnp | grep -q ":$PORT "; then
                print_success "端口$PORT: 正在监听"
            else
                print_warning "端口$PORT: 未监听"
            fi
        elif command -v ss &> /dev/null; then
            if ss -tlnp | grep -q ":80 "; then
                print_success "端口80: 正在监听"
            else
                print_warning "端口80: 未监听"
            fi
            
            if ss -tlnp | grep -q ":$PORT "; then
                print_success "端口$PORT: 正在监听"
            else
                print_warning "端口$PORT: 未监听"
            fi
        else
            print_warning "无法检查端口状态 (netstat/ss命令不可用)"
        fi
    fi
    
    echo ""
    print_info "=== 应用信息 ==="
    echo "📁 项目目录: $SCRIPT_DIR"
    echo "🔧 服务名称: $SERVICE_NAME"
    echo "🔌 应用端口: $PORT"
    echo ""
    print_info "=== 访问信息 ==="
    if [ "$MACHINE" = "Mac" ]; then
        echo "🌐 本地访问地址: http://localhost:$PORT"
        echo "🌐 本机IP访问: http://$(ipconfig getifaddr en0 2>/dev/null || echo "获取IP失败"):$PORT"
    else
        echo "🌐 Web访问地址: http://$(hostname -I | awk '{print $1}')"
        echo "🌐 本地访问地址: http://localhost"
    fi
    echo ""
}

# 显示日志
show_logs() {
    if [ "$MACHINE" = "Linux" ]; then
        print_info "显示应用服务日志 (按Ctrl+C退出)..."
        journalctl -u $SERVICE_NAME -f
    else
        print_info "显示Flask应用日志 (按Ctrl+C退出)..."
        if [ -f "flask_app.log" ]; then
            tail -f flask_app.log
        else
            print_error "日志文件不存在: flask_app.log"
            print_info "请先启动应用服务"
            return 1
        fi
    fi
}

# 显示帮助信息
show_help() {
    echo "TikTok创作者评分系统 - 服务管理脚本 (支持Linux/macOS)"
    echo ""
    if [ "$MACHINE" = "Linux" ]; then
        echo "使用方法: sudo bash start.sh [command]"
    else
        echo "使用方法: bash start.sh [command] 或 ./start.sh [command]"
    fi
    echo ""
    echo "可用命令:"
    echo "  start     启动服务 (默认)"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    显示服务状态"
    echo "  logs      显示服务日志"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    if [ "$MACHINE" = "Linux" ]; then
        echo "  sudo bash start.sh          # 启动服务"
        echo "  sudo bash start.sh status   # 查看状态"
        echo "  sudo bash start.sh logs     # 查看日志"
    else
        echo "  ./start.sh                   # 启动服务"
        echo "  ./start.sh status            # 查看状态"
        echo "  ./start.sh logs              # 查看日志"
    fi
    echo ""
    echo "环境说明:"
    echo "  Linux: 使用systemctl管理服务，需要root权限"
    echo "  macOS: 直接启动Python Flask应用，无需root权限"
    echo ""
}

# 主函数
main() {
    local command=${1:-start}
    
    case $command in
        "start")
            check_root
            start_service
            ;;
        "stop")
            check_root
            stop_service
            ;;
        "restart")
            check_root
            restart_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
echo "🚀 TikTok创作者评分系统 - 服务管理"
echo "================================================"
main "$@"