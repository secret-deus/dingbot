# K8s MCP Poetry使用指南

本指南详细介绍如何使用Poetry管理和运行K8s MCP项目。

## 🎯 快速开始

### 1. 安装Poetry

```bash
# 使用官方脚本安装
curl -sSL https://install.python-poetry.org | python3 -

# 或者使用pip安装
pip install poetry
```

### 2. 进入项目目录

```bash
cd k8s-mcp
```

### 3. 配置环境

创建`.env`文件：
```bash
cp config.env.example .env
# 编辑.env文件，设置你的kubeconfig路径和默认命名空间
```

### 4. 安装依赖

```bash
poetry install
```

### 5. 启动服务器

```bash
# 方式1: 使用Poetry命令
poetry run python start_k8s_mcp_server.py

# 方式2: 使用简化脚本
./run.py
# 或者
python run.py

# 方式3: 使用启动脚本
./scripts/start.sh

# 方式4: 激活虚拟环境后运行
poetry shell
python start_k8s_mcp_server.py
```

## 📋 配置说明

### 基本配置

只需要配置两个核心字段：

```env
# Kubernetes配置文件路径
KUBECONFIG_PATH=/Users/a123/.kube/config

# 默认命名空间
K8S_NAMESPACE=default

# 可选：服务器配置
K8S_MCP_HOST=localhost
K8S_MCP_PORT=8766
K8S_MCP_DEBUG=false
```

### 配置优先级

1. 显式指定的kubeconfig文件路径 (`KUBECONFIG_PATH`)
2. `KUBECONFIG` 环境变量
3. 默认的 `~/.kube/config` 