#!/bin/bash

# TikTok创作者评分系统 - 一键启动服务脚本
# 作者: TikTok Creator Score System
# 版本: 1.0

set -e  # 遇到错误立即退出

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

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用root权限运行此脚本"
        echo "使用方法: sudo bash start.sh [command]"
        exit 1
    fi
}

# 检查服务状态
check_service_status() {
    if systemctl is-active --quiet tiktok-creator-score; then
        return 0  # 服务正在运行
    else
        return 1  # 服务未运行
    fi
}

# 检查Nginx状态
check_nginx_status() {
    if systemctl is-active --quiet nginx; then
        return 0  # Nginx正在运行
    else
        return 1  # Nginx未运行
    fi
}

# 启动服务
start_service() {
    print_info "启动TikTok创作者评分系统..."
    
    # 启动应用服务
    if check_service_status; then
        print_warning "应用服务已在运行中"
    else
        systemctl start tiktok-creator-score
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
    
    print_success "所有服务启动完成！"
    show_status
}

# 停止服务
stop_service() {
    print_info "停止TikTok创作者评分系统..."
    
    systemctl stop tiktok-creator-score
    systemctl stop nginx
    
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启TikTok创作者评分系统..."
    
    systemctl restart tiktok-creator-score
    systemctl restart nginx
    
    sleep 3
    
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
    print_info "=== 服务状态 ==="
    
    # 应用服务状态
    if check_service_status; then
        print_success "应用服务: 运行中"
    else
        print_error "应用服务: 已停止"
    fi
    
    # Nginx状态
    if check_nginx_status; then
        print_success "Nginx: 运行中"
    else
        print_error "Nginx: 已停止"
    fi
    
    # 端口监听状态
    if netstat -tlnp | grep -q ":80 "; then
        print_success "端口80: 正在监听"
    else
        print_warning "端口80: 未监听"
    fi
    
    if netstat -tlnp | grep -q ":8080 "; then
        print_success "端口8080: 正在监听"
    else
        print_warning "端口8080: 未监听"
    fi
    
    echo ""
    print_info "=== 访问信息 ==="
    echo "🌐 Web访问地址: http://$(hostname -I | awk '{print $1}')"
    echo "🌐 本地访问地址: http://localhost"
    echo ""
}

# 显示日志
show_logs() {
    print_info "显示应用服务日志 (按Ctrl+C退出)..."
    journalctl -u tiktok-creator-score -f
}

# 显示帮助信息
show_help() {
    echo "TikTok创作者评分系统 - 服务管理脚本"
    echo ""
    echo "使用方法: sudo bash start.sh [command]"
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
    echo "  sudo bash start.sh          # 启动服务"
    echo "  sudo bash start.sh status   # 查看状态"
    echo "  sudo bash start.sh logs     # 查看日志"
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
            check_root
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