#!/bin/bash
"""
项目清理脚本
提供各种清理功能的便捷入口
"""

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
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

# 清理MCP备份文件
cleanup_mcp_backups() {
    print_info "清理MCP配置备份文件..."
    
    # 先清理错误格式的备份文件（如果存在）
    if python3 scripts/emergency_cleanup_backups.py 2>/dev/null | grep -q "错误格式备份: [1-9]"; then
        print_warning "发现错误格式的备份文件，正在清理..."
        python3 scripts/emergency_cleanup_backups.py --execute
    fi
    
    # 然后清理正常的备份文件，保留5个
    python3 scripts/cleanup_mcp_backups.py --execute --keep 5
    print_success "MCP备份清理完成"
}

# 清理Python缓存
cleanup_python_cache() {
    print_info "清理Python缓存文件..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    print_success "Python缓存清理完成"
}

# 清理日志文件
cleanup_logs() {
    print_info "清理旧日志文件..."
    # 保留最近7天的日志
    find logs/ -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    print_success "日志文件清理完成"
}

# 清理临时文件
cleanup_temp_files() {
    print_info "清理临时文件..."
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    find . -name "*.temp" -type f -delete 2>/dev/null || true
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true
    print_success "临时文件清理完成"
}

# 显示帮助信息
show_help() {
    echo "🧹 项目清理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  mcp           只清理MCP备份文件"
    echo "  python        只清理Python缓存"
    echo "  logs          只清理旧日志文件"
    echo "  temp          只清理临时文件"
    echo "  all           清理所有内容 (默认)"
    echo "  -h, --help    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0            # 清理所有内容"
    echo "  $0 mcp        # 只清理MCP备份"
    echo "  $0 python     # 只清理Python缓存"
}

# 主函数
main() {
    local command=${1:-all}
    
    case $command in
        mcp)
            cleanup_mcp_backups
            ;;
        python)
            cleanup_python_cache
            ;;
        logs)
            cleanup_logs
            ;;
        temp)
            cleanup_temp_files
            ;;
        all)
            print_info "开始全面清理..."
            cleanup_mcp_backups
            cleanup_python_cache
            cleanup_logs
            cleanup_temp_files
            print_success "全面清理完成！"
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 确保在项目根目录运行
if [[ ! -f "pyproject.toml" ]]; then
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

# 运行主函数
main "$@" 