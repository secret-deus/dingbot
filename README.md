# 钉钉K8s运维机器人

一个基于钉钉的智能Kubernetes运维机器人，支持通过自然语言进行K8s集群管理和运维操作。

## ✨ 核心特性

- 🤖 **智能对话**: 自然语言交互，理解运维意图
- ⚙️ **K8s管理**: Pod、Service、Deployment等资源管理
- 📊 **实时监控**: 集群状态、资源使用情况监控
- 🔧 **MCP协议**: 可扩展的工具系统
- 🌐 **Web界面**: 现代化Vue3聊天界面，流式响应体验
- 💾 **会话持久化**: 对话历史自动保存
- 🔐 **数据安全**: IP/主机名/人名脱敏

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python依赖 (使用Poetry)
poetry install

# 前端依赖 (仅开发时需要)
cd frontend-v2 && npm install
```

### 2. 配置

```bash
cp backend/config.env.example backend/config.env
# 编辑 config.env 配置 LLM API Key 等
```

### 3. 启动

```bash
# 一键启动所有服务（推荐）
# 会自动启动 MCP 服务器和后端，按正确顺序启动
poetry run start-all

# 或者分别启动
# 启动MCP服务器 (可选，如果使用 start-all 则不需要)
cd ecs-mcp && poetry run serve &
cd k8s-mcp && poetry run serve &

# 启动主服务 (包含前端)
poetry run serve
```

### 4. 访问

- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📁 项目结构

```
ding-robot/
├── backend/          # FastAPI后端
├── frontend-v2/      # Vue.js 3 前端
├── config/           # 统一配置目录
├── k8s-mcp/          # Kubernetes MCP服务器
├── ecs-mcp/          # 阿里云ECS MCP服务器
└── project_document/ # 项目文档
```

## ⚡ 常用命令

| 命令 | 功能 |
|------|------|
| `poetry run start-all` | 一键启动所有服务（MCP + 后端） |
| `poetry run serve` | 仅启动后端服务 |
| `poetry run dev` | 启动开发环境 |
| `poetry run build` | 构建前端 |

## 📚 文档

- **[项目状态与计划](./project_document/PROJECT_STATUS.md)** - 完整项目概述
- **[技术架构与配置](./project_document/技术架构与配置指南.md)** - 系统架构详解
- **[K8s MCP文档](./k8s-mcp/README.md)** - K8s工具集
- **[ECS MCP文档](./ecs-mcp/README.md)** - ECS监控工具

## 📄 许可证

MIT License
