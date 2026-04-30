#!/bin/bash

# K8s MCP服务器Poetry启动脚本
# 自动检测和设置Poetry环境

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

# 检查Poetry是否安装
check_poetry() {
    log_info "检查Poetry安装状态..."

    if command -v poetry &> /dev/null; then
        POETRY_VERSION=$(poetry --version 2>/dev/null || echo "unknown")
        log_success "Poetry已安装: ${POETRY_VERSION}"
        return 0
    else
        log_error "Poetry未安装"
        echo
        echo "请使用以下命令安装Poetry:"
        echo "  curl -sSL https://install.python-poetry.org | python3 -"
        echo "  或者: pip install poetry"
        echo
        exit 1
    fi
}

# 进入项目目录
cd "${PROJECT_DIR}"

# 检查Poetry配置文件
check_project() {
    log_info "检查项目配置..."

    if [[ ! -f "pyproject.toml" ]]; then
        log_error "pyproject.toml文件不存在"
        exit 1
    fi

    if [[ ! -f "poetry.lock" ]]; then
        log_warning "poetry.lock文件不存在，将重新生成"
    fi

    log_success "项目配置检查通过"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."

    # 检查虚拟环境是否存在
    if poetry env info &> /dev/null; then
        log_success "虚拟环境已存在"
    else
        log_info "创建虚拟环境..."
        poetry env use python3
    fi

    # 安装依赖
    log_info "安装项目依赖..."
    poetry install

    log_success "依赖安装完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."

    LOCAL_CONFIG=".env"

    if [[ -f "${LOCAL_CONFIG}" ]]; then
        log_success "找到本地配置文件: ${LOCAL_CONFIG}"
    else
        log_info "本地配置文件不存在，将使用默认配置"
    fi

    # 检查Kubernetes配置
    if [[ -f "config/k8s_config.yaml" ]]; then
        log_success "找到Kubernetes配置文件: config/k8s_config.yaml"
    else
        log_warning "Kubernetes配置文件不存在，将使用默认配置"
    fi
}

# 启动服务器
start_server() {
    log_info "启动K8s MCP服务器..."

    # 设置环境变量
    export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH}"

    # 启动服务器
    poetry run python start_k8s_mcp_server.py
}

# 主函数
main() {
    echo "=========================================="
    echo "🚀 K8s MCP服务器Poetry启动脚本"
    echo "=========================================="
    echo

    # 检查Poetry
    check_poetry

    # 检查项目
    check_project

    # 安装依赖
    install_dependencies

    # 检查配置
    check_config

    echo
    echo "=========================================="
    echo "✅ 环境准备完成，正在启动服务器..."
    echo "=========================================="
    echo

    # 启动服务器
    start_server
}

# 处理信号
trap 'log_info "接收到中断信号，正在停止服务器..."; exit 0' SIGINT SIGTERM

# 运行主函数
main "$@"