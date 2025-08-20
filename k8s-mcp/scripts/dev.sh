#!/bin/bash

# K8s MCP开发环境脚本
# 提供开发过程中常用的命令

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 进入项目目录
cd "${PROJECT_DIR}"

# 显示帮助信息
show_help() {
    echo "K8s MCP开发环境脚本"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  install     安装依赖"
    echo "  dev         安装开发依赖"
    echo "  test        运行测试"
    echo "  format      格式化代码"
    echo "  lint        代码检查"
    echo "  type        类型检查"
    echo "  clean       清理环境"
    echo "  shell       进入Poetry shell"
    echo "  info        显示环境信息"
    echo "  start       启动服务器"
    echo "  help        显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 install"
    echo "  $0 test"
    echo "  $0 format"
    echo "  $0 start"
}

# 安装依赖
install_deps() {
    log_info "安装项目依赖..."
    poetry install
    log_success "依赖安装完成"
}

# 安装开发依赖
install_dev_deps() {
    log_info "安装开发依赖..."
    poetry install --with dev
    log_success "开发依赖安装完成"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    poetry run pytest tests/ -v
    log_success "测试完成"
}

# 格式化代码
format_code() {
    log_info "格式化代码..."
    poetry run black src/ tests/
    poetry run isort src/ tests/
    log_success "代码格式化完成"
}

# 代码检查
lint_code() {
    log_info "运行代码检查..."
    poetry run black --check src/ tests/
    poetry run isort --check-only src/ tests/
    log_success "代码检查通过"
}

# 类型检查
type_check() {
    log_info "运行类型检查..."
    poetry run mypy src/
    log_success "类型检查通过"
}

# 清理环境
clean_env() {
    log_info "清理环境..."
    
    # 清理缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理测试缓存
    rm -rf .pytest_cache 2>/dev/null || true
    rm -rf .coverage 2>/dev/null || true
    rm -rf htmlcov 2>/dev/null || true
    
    # 清理Poetry缓存
    poetry cache clear pypi --all -n 2>/dev/null || true
    
    log_success "环境清理完成"
}

# 进入Poetry shell
enter_shell() {
    log_info "进入Poetry shell..."
    poetry shell
}

# 显示环境信息
show_info() {
    log_info "环境信息:"
    echo
    echo "项目目录: ${PROJECT_DIR}"
    echo "Python版本: $(python --version 2>/dev/null || echo '未检测到')"
    echo "Poetry版本: $(poetry --version 2>/dev/null || echo '未安装')"
    echo
    
    if poetry env info &> /dev/null; then
        echo "虚拟环境信息:"
        poetry env info
    else
        echo "虚拟环境: 未创建"
    fi
    
    echo
    echo "依赖信息:"
    poetry show --tree 2>/dev/null || echo "依赖未安装"
}

# 启动服务器
start_server() {
    log_info "启动K8s MCP服务器..."
    poetry run python start_k8s_mcp_server.py
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_deps
            ;;
        dev)
            install_dev_deps
            ;;
        test)
            run_tests
            ;;
        format)
            format_code
            ;;
        lint)
            lint_code
            ;;
        type)
            type_check
            ;;
        clean)
            clean_env
            ;;
        shell)
            enter_shell
            ;;
        info)
            show_info
            ;;
        start)
            start_server
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 