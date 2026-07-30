# Ops Workbench（智能运维工作台）

面向 Kubernetes、ECS 与阿里云场景的智能运维工作台，统一覆盖 ChatOps 对话、MCP 工具治理、审计与调度，仓库 slug 为 `ops-workbench`。当前仓库已进入 v3 重构线：后端使用 FastAPI，前端使用 Vue 3，工具层通过 MCP 管理；DingTalk 仅作为通知集成，旧实现集中归档在 `archived/`。

## 当前状态

可用主线：

- `backend-v2/`：FastAPI API、登录认证、会话和消息持久化、SSE 聊天、MCP 工具聚合、审计日志、定时任务 CRUD。
- `frontend-v3/`：Vue 3 + Vite + Naive UI，包含登录、仪表盘、聊天、MCP 工具、定时任务、权限/审计页面。
- `config/`：只提交 `*.example.json` 和说明文档，真实运行时配置留在本地。
- `mcp-servers/toolsearch/`：本地 stdio MCP server，用于搜索 68 个当前运维工具目录和可执行工具。
- `project_document/specs/`：spec 驱动开发文档和交付计划。
- `archived/`：v2 后端、旧前端、独立 K8s/ECS MCP 工程和历史测试。

仍在建设中的主线：

- ToolSearch MCP：已恢复旧版 21 个运维工具目录并扩展到 68 个可执行工具；工具发现、执行、权限、确认、审计已拆开。
- 阿里云只读 Adapter：已提供 13 个 `aliyun-*` 只读诊断工具，覆盖 ECS、CloudMonitor、SLS、负载均衡和轻量应用服务器，按 RAM 凭据、地域、标签、资源 ID 和角色权限收口。
- Scheduler runner：已接入持久化任务执行、手动运行、执行历史和前端状态展示。
- DingTalk webhook：已接入 markdown 通知和签名 webhook，调度任务可按任务开关发送通知。
- 回归测试：已覆盖公共端点、MCP stdio、ToolSearch 编排、工具治理、审计、调度和通知 mock；后续继续补浏览器和真实环境冒烟。

## 本地启动

推荐本地运行时：

- Python：使用仓库 `.python-version` 指定的 3.13；Docker 后端镜像使用
  Python 3.12，二者都满足 `backend-v2/pyproject.toml` 的版本范围。
- Node.js：使用 `.nvmrc` 指定的 Node 22；前端和 ToolSearch Docker 构建也使用
  Node 22。

后端：

```bash
cd backend-v2
poetry install
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端开发服务器：

```bash
cd frontend-v3
npm install
# 如果后端不在默认 8000 端口，可设置 VITE_API_TARGET，例如:
# VITE_API_TARGET=http://127.0.0.1:8001 npm run dev
npm run dev
```

访问地址：

- 后端健康检查：http://127.0.0.1:8000/health
- 后端 API 文档：http://127.0.0.1:8000/docs
- 前端开发页：http://127.0.0.1:3000

默认开发登录账号会在后端首次启动且无管理员时创建：

```text
admin / admin
```

该账号仅用于本地开发。部署到共享或生产环境前，请至少设置：

```bash
APP_ENV=production
SECRET_KEY=<32位以上随机密钥>
CORS_ALLOW_ORIGINS=https://your-frontend.example.com
BOOTSTRAP_ADMIN_USERNAME=<初始化管理员用户名>
BOOTSTRAP_ADMIN_PASSWORD=<强密码>
```

生产模式会拒绝占位 `SECRET_KEY`、通配 `CORS_ALLOW_ORIGINS=*` 和默认
`BOOTSTRAP_ADMIN_PASSWORD=admin`。如果已经手工创建管理员，也可以设置
`BOOTSTRAP_ADMIN_ENABLED=false` 禁止自动初始化管理员。

## 构建与验证

后端测试：

```bash
cd backend-v2
poetry run pytest
```

前端类型检查与构建：

```bash
cd frontend-v3
npm run build
```

ToolSearch MCP：

```bash
cd mcp-servers/toolsearch
npm install
npm run catalog:generate
npm test
```

`npm run build` 默认把前端产物输出到 `backend-v2/static/spa`，用于后端集成式部署。Docker 前端镜像会单独构建到容器内的 `/usr/share/nginx/html/spa`。

Docker Compose：

```bash
cp backend-v2/.env.example backend-v2/.env
docker compose --project-name ding-robot up --build
```

Compose 模式下：

- 后端：http://127.0.0.1:8000
- 前端：http://127.0.0.1:3000/spa/

如果本机端口被占用，可以只覆盖宿主机映射端口，容器内部仍使用
backend `8000` 和 frontend `80`：

```bash
BACKEND_PORT=8010 FRONTEND_PORT=3010 docker compose --project-name ding-robot up --build
```

`ding-robot` 是为保留现有 Docker 网络、容器与镜像资源前缀而固定的兼容
Compose project name，不代表当前产品名称或仓库 slug。

后端镜像会在构建阶段编译并携带 `mcp-servers/toolsearch`，所以 Docker 运行时可以直接启动 stdio ToolSearch。启用 ToolSearch 时，将 `config/mcp_config.example.json` 复制为 `config/mcp_config.json`，并把 `toolsearch.enabled` 改为 `true`。

阿里云只读 Adapter 配置在 `config/mcp_config.json` 的 `builtin.aliyun` 下，也可以用环境变量覆盖。`ALIYUN_ALLOWED_REGIONS`、`ALIYUN_REQUIRED_TAGS`、`ALIYUN_ALLOWED_INSTANCE_IDS` 和 `ALIYUN_SLS_MAPPINGS` 在环境变量中需要使用 JSON 格式。

## 本地 CI 等价验证

常规验证：

```bash
scripts/verify.sh
```

如果本机 Docker runtime 可用，同时验证镜像构建：

```bash
VERIFY_DOCKER_BUILD=1 scripts/verify.sh
```

## 配置策略

只提交示例配置：

```bash
cp config/llm_config.example.json config/llm_config.json
cp config/mcp_config.example.json config/mcp_config.json
cp config/skills.example.json config/skills.json
cp config/scheduled_tasks.example.json config/scheduled_tasks.json
```

真实密钥、webhook、云凭证、kubeconfig、本地数据库和日志不得提交。

## 持续交付计划

后续开发按 spec 目录推进：

- [可持续交付计划](./project_document/DELIVERY_PLAN.md)
- [ToolSearch MCP Spec](./project_document/specs/toolsearch-mcp/tasks.md)
- [Aliyun Read-Only MCP Adapter Spec](./project_document/specs/aliyun-readonly-mcp/tasks.md)
- [可持续交付 Spec](./project_document/specs/sustainable-delivery/tasks.md)

每个交付切片都应包含：spec 更新、实现、测试、构建验证、自测记录和明确的提交范围。
