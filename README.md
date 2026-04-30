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
# Python 需使用 3.11-3.13；如果 Poetry 误用了 3.14，请先切回 3.13
poetry env use $(which python3.13)

# Python依赖 (使用Poetry)
poetry install

# 前端依赖 (仅开发时需要；推荐 Node 20/22 LTS，见 .nvmrc)
cd frontend-v2 && npm install
```

### 2. 配置

```bash
cp backend/config.env.example backend/config.env
# 编辑 config.env 配置 LLM API Key 等

# JSON 运行时配置只保留本地文件，不提交真实密钥
cp config/llm_config.example.json config/llm_config.json
cp config/mcp_config.example.json config/mcp_config.json
cp config/skills.example.json config/skills.json
cp config/scheduled_tasks.example.json config/scheduled_tasks.json
```

### 3. 启动

```bash
# K8s / ECS 工具已并入主应用进程（backend/src/k8s_mcp、backend/src/ecs_mcp），
# 默认通过 config/mcp_config.json 的 type=local/provider=k8s|ecs 运行，
# 无需再单独启动 k8s-mcp / ecs-mcp。

# 一键启动（仅后端 + 可选其他子进程；见 scripts/start_all.py）
poetry run start-all

# 或仅主服务（含构建后的前端静态资源）
poetry run serve
```

独立 MCP 工程已归档至 `archived/`，见 `archived/README.md`。

### 4. 访问

- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📁 项目结构

```
ding-robot/
├── backend/
│   └── src/
│       ├── k8s_mcp/   # 进程内 K8s 工具（原独立 k8s-mcp）
│       └── ecs_mcp/   # 进程内 ECS 工具（原独立 ecs-mcp）
├── frontend-v2/       # Vue.js 3 前端
├── config/            # 统一配置目录
├── archived/          # 历史独立 MCP Server 工程归档
└── project_document/  # 项目文档
```

## ⚡ 常用命令

| 命令 | 功能 |
|------|------|
| `poetry run start-all` | 一键启动（后端等；K8s/ECS 已在主进程内） |
| `poetry run serve` | 仅启动后端服务 |
| `poetry run dev` | 启动开发环境（后端热重载 + `frontend-v2`） |
| `poetry run build` | 构建前端 |

## 📚 文档

- **[项目状态与计划](./project_document/PROJECT_STATUS.md)** - 完整项目概述
- **[技术架构与配置](./project_document/技术架构与配置指南.md)** - 系统架构详解
- **[重构基线](./project_document/refactor-baseline.md)** - 当前重构目标架构与阶段计划
- **[Chat Stream Contract](./project_document/chat-stream-contract.md)** - 前后端聊天流式协议契约
- **[归档说明](./archived/README.md)** - 原独立 k8s-mcp / ecs-mcp

## 📄 许可证

MIT License
