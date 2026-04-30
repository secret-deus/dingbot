# ding-robot 重写方案 (v3.0)

> 本文件是 codex 执行重写的唯一权威来源。所有架构决策已在此固化，不再讨论"要不要"，只讨论"如何实现"。

---

## 0. 重写总目标

打造一个**易维护、可测试、可扩展**的 Kubernetes 自然语言运维助手，保留 v2 的全部核心能力，但去掉 v2 的所有维护痛点。

**指导原则（按优先级）**：
1. **单一职责** — 每个模块只做一件事
2. **配置统一** — 一个配置入口，禁止 env/JSON/dotenv 三处分散
3. **协议统一** — 流式只用 SSE，不再混用 WebSocket
4. **状态后端化** — 所有持久化状态在后端 SQLite，前端只做展示
5. **工具自注册** — K8s 工具用装饰器自动发现，禁止手动注册表
6. **测试先行** — 工具层 100% 单测覆盖，API 层有集成测试

---

## 1. 技术栈决策

| 层 | 选型 | 替代了什么 | 理由 |
|---|---|---|---|
| 包管理 | **uv** | poetry | 10x 速度、锁文件兼容性更好 |
| 后端语言 | Python 3.11 | Python 3.9 | structural pattern matching、性能 |
| 后端框架 | **FastAPI** | FastAPI | 保留，生态成熟 |
| ASGI | uvicorn | uvicorn | 保留 |
| 数据库 | **SQLite + SQLModel** | localStorage + 文件 | 后端持久化、类型安全 ORM |
| 配置 | **pydantic-settings + TOML** | env/JSON/dotenv 三套 | 单一配置源 |
| 日志 | **structlog** | loguru | 结构化、JSON 输出、便于聚合 |
| 流式 | **SSE only** (sse-starlette) | SSE+WebSocket+HTTP 混用 | 协议统一 |
| 前端框架 | **Vue 3 + TypeScript** | Vue 3 (JS) | 类型安全 |
| 前端构建 | Vite | Vite | 保留 |
| 状态管理 | Pinia | Pinia | 保留 |
| UI 库 | **Element Plus** | Element UI | Vue 3 原生 |
| 包管理 | pnpm | npm | monorepo 支持 |
| LLM SDK | openai (兼容 Ollama/vLLM) | openai + 多种 | 用 OpenAI 兼容协议统一 |
| K8s 客户端 | kubernetes (官方) | kubernetes | 保留 |
| MCP 协议 | **官方 mcp Python SDK** | 自己实现 SSE 协议 | 别造轮子 |
| 测试框架 | pytest + pytest-asyncio + httpx | 几乎为空 | 全覆盖 |
| 类型检查 | mypy (strict) | 无 | 强制类型 |
| Lint/Format | ruff | 无 | 一站式 |

---

## 2. 目录结构（最终态）

```
ding-robot/
├── README.md
├── REWRITE_PLAN.md              # 本文件
├── pyproject.toml               # 单一 Python 工程定义（uv workspace）
├── uv.lock
├── .env.example                 # 仅含敏感凭证占位符
├── config.toml                  # 默认配置（非敏感）
├── docker-compose.yml           # 一键启动 backend + mcp_server
├── Dockerfile.backend
├── Dockerfile.mcp
│
├── apps/
│   ├── backend/                 # FastAPI 应用
│   │   ├── pyproject.toml       # workspace member
│   │   └── src/backend/
│   │       ├── __init__.py
│   │       ├── main.py          # FastAPI app factory，<50 行
│   │       ├── config.py        # pydantic Settings，所有配置
│   │       ├── db.py            # SQLModel engine + session
│   │       ├── deps.py          # FastAPI dependencies
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── chat.py      # POST /api/chat (SSE)
│   │       │   ├── sessions.py  # CRUD 会话
│   │       │   ├── tasks.py     # CRUD 定时任务
│   │       │   ├── settings.py  # LLM/MCP 配置 CRUD
│   │       │   └── health.py
│   │       ├── models/          # SQLModel 表定义
│   │       │   ├── session.py   # ChatSession, ChatMessage
│   │       │   ├── task.py      # ScheduledTask
│   │       │   └── settings.py  # AppSettings
│   │       ├── services/        # 业务逻辑层（无 HTTP 依赖）
│   │       │   ├── chat.py      # 编排 LLM + MCP，返回 async iterator
│   │       │   ├── llm.py       # LLM 调用，支持 OpenAI 兼容协议
│   │       │   ├── mcp_client.py # 调用 mcp_server，工具列表缓存
│   │       │   ├── scheduler.py # APScheduler 包装
│   │       │   ├── notify.py    # DingTalk webhook
│   │       │   └── redact.py    # 数据脱敏（独立纯函数）
│   │       └── tests/
│   │           ├── conftest.py
│   │           ├── test_chat.py
│   │           ├── test_redact.py
│   │           └── test_scheduler.py
│   │
│   ├── mcp_server/              # K8s MCP 服务（独立部署）
│   │   ├── pyproject.toml
│   │   └── src/mcp_server/
│   │       ├── __init__.py
│   │       ├── main.py          # 用官方 mcp SDK，<30 行
│   │       ├── config.py
│   │       ├── k8s.py           # K8s client 包装（单例）
│   │       ├── prom.py          # Prometheus client
│   │       ├── registry.py      # @tool 装饰器 + 自动发现
│   │       ├── tools/           # 每文件一个工具，import 即注册
│   │       │   ├── __init__.py  # 自动 import 整个目录
│   │       │   ├── pods.py      # get_pods, get_pod_logs, delete_pod
│   │       │   ├── deployments.py  # get/scale/patch
│   │       │   ├── services.py
│   │       │   ├── nodes.py
│   │       │   ├── events.py
│   │       │   ├── metrics.py   # resource metrics
│   │       │   ├── prometheus.py # prom 查询、应用指标
│   │       │   └── relations.py # 关系推理
│   │       └── tests/
│   │           ├── conftest.py  # fake k8s client
│   │           ├── test_pods.py
│   │           ├── test_deployments.py
│   │           └── ...          # 每个工具一个测试文件
│   │
│   └── frontend/                # Vue 3 + TS
│       ├── package.json
│       ├── tsconfig.json
│       ├── vite.config.ts
│       ├── index.html
│       └── src/
│           ├── main.ts
│           ├── App.vue
│           ├── router.ts
│           ├── api/
│           │   ├── client.ts    # axios 封装
│           │   ├── sse.ts       # SSE 客户端（EventSource 包装）
│           │   ├── chat.ts
│           │   ├── sessions.ts
│           │   ├── tasks.ts
│           │   └── settings.ts
│           ├── stores/
│           │   ├── chat.ts      # 当前会话状态（不持久化，只缓存）
│           │   └── settings.ts
│           ├── views/
│           │   ├── ChatView.vue
│           │   ├── SessionsView.vue
│           │   ├── TasksView.vue
│           │   └── SettingsView.vue
│           ├── components/
│           │   ├── chat/
│           │   │   ├── MessageList.vue
│           │   │   ├── MessageItem.vue
│           │   │   ├── MessageInput.vue
│           │   │   └── ToolCallCard.vue   # 工具调用展示
│           │   ├── markdown/
│           │   │   └── MarkdownView.vue   # markdown-it + katex + shiki
│           │   ├── tasks/
│           │   │   ├── TaskForm.vue
│           │   │   └── CronEditor.vue
│           │   └── common/
│           │       ├── AppLayout.vue
│           │       └── ConfirmDialog.vue
│           └── types/
│               └── api.ts       # 与后端 schema 对齐的 TS 类型
│
├── scripts/
│   ├── dev.sh                   # 一键启动 backend + mcp + frontend
│   ├── seed.py                  # 注入示例配置
│   └── migrate.py               # alembic 包装
│
└── docs/
    ├── architecture.md          # 架构图 + 数据流
    ├── adding-a-tool.md         # 如何加新 K8s 工具
    └── deployment.md
```

**约束**：
- 所有 Python 模块文件 ≤ 250 行；超出必须拆分
- 所有 Vue 单文件组件 ≤ 200 行
- 禁止出现 `utils.py` 或 `helpers.py` 这种名字；必须按职责命名

---

## 3. 数据模型（SQLModel）

```python
# session.py
class ChatSession(SQLModel, table=True):
    id: str = Field(primary_key=True)        # uuid
    title: str
    created_at: datetime
    updated_at: datetime

class ChatMessage(SQLModel, table=True):
    id: str = Field(primary_key=True)
    session_id: str = Field(foreign_key="chatsession.id", index=True)
    role: str                                 # user / assistant / tool
    content: str                              # JSON-serialized parts
    created_at: datetime

# task.py
class ScheduledTask(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    cron: str
    prompt: str                               # 给 LLM 的指令
    enabled: bool = True
    notify_webhook: str | None = None         # DingTalk webhook
    last_run_at: datetime | None = None
    last_status: str | None = None

# settings.py — 单行表，存全局配置
class AppSettings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    llm_base_url: str
    llm_model: str
    llm_api_key: str                          # 加密存储
    mcp_server_url: str
    system_prompt: str
```

迁移工具：alembic（autogenerate）。

---

## 4. 核心数据流（重写后）

```
1. 用户在前端发送消息
   POST /api/chat  body: { session_id, content }
   响应: text/event-stream

2. backend/services/chat.py 编排：
   a. 从 DB 加载会话历史
   b. 调用 services/llm.py 流式调用 LLM
   c. LLM 返回 tool_call → services/mcp_client.py 调 mcp_server
   d. mcp_server 执行 K8s 操作，返回结果
   e. 结果脱敏（services/redact.py）后塞回 LLM 上下文
   f. 整个过程通过 async generator 以 SSE 帧推给前端
      事件类型: token / tool_call / tool_result / done / error

3. 前端 components/chat/MessageList.vue 订阅 SSE，逐帧渲染

4. 会话结束时后端事务性写入 DB（不依赖前端 localStorage）

5. 定时任务由 APScheduler 触发，复用 services/chat.py 的同一编排逻辑
   结果通过 services/notify.py 推送到 DingTalk
```

**关键改动 vs v2**：
- v2 是前端管历史 → v3 后端管历史
- v2 多协议混用 → v3 只 SSE
- v2 工具调用是后端→mcp_server 自定义 SSE → v3 用官方 mcp SDK
- v2 LLM 处理器 300+ 行 → v3 services/llm.py 控制在 100 行内（脱敏抽出，分页抽出）

---

## 5. 工具自动注册（关键设计）

```python
# apps/mcp_server/src/mcp_server/registry.py
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("k8s-mcp")

# apps/mcp_server/src/mcp_server/tools/pods.py
from ..registry import mcp
from ..k8s import core_v1

@mcp.tool()
async def get_pods(namespace: str = "default") -> list[dict]:
    """List pods in a namespace."""
    pods = await core_v1.list_namespaced_pod(namespace)
    return [{"name": p.metadata.name, "status": p.status.phase} for p in pods.items]

# apps/mcp_server/src/mcp_server/tools/__init__.py
# 自动 import 同目录所有 .py 模块，触发 @mcp.tool() 注册
import importlib, pkgutil
for m in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{m.name}")
```

**新增工具流程**：在 `tools/` 下加文件 → 写 `@mcp.tool()` 函数 → 加单测 → 完成。**无需改注册表**。

---

## 6. 必须保留的能力清单（验收标准）

| # | 能力 | 验收方式 |
|---|---|---|
| 1 | 自然语言 → K8s 操作 | E2E：用 prompt "缩容 deployment X 到 0 副本" 验证 |
| 2 | Pod 查询/日志/删除 | 单测 + E2E |
| 3 | Deployment 查询/扩缩容/patch | 单测 + E2E |
| 4 | Service / Node / Event 查询 | 单测 |
| 5 | Prometheus 指标查询 | 单测（mock prom） + 集成测试 |
| 6 | 资源关系推理（如 Pod→Deployment→Service） | 单测 |
| 7 | SSE 流式响应 | 集成测试：断言 SSE 帧序列 |
| 8 | 多会话历史持久化 | API 测试 + 重启后数据仍在 |
| 9 | 数据脱敏（IP/密码/token） | 单测，纯函数 |
| 10 | DingTalk webhook 推送 | 单测（mock httpx） |
| 11 | Cron 定时任务 | 集成测试：APScheduler + DB |
| 12 | 多 LLM 供应商（OpenAI 兼容） | 单测：切换 base_url 仍工作 |

不保留：v2 的 localStorage 持久化、v2 自定义的 MCP SSE 协议（换官方 SDK）、v2 的 12 份散乱文档（合并为 3 份）。

---

## 7. 执行顺序（codex 按此 phase 推进）

### Phase 1: 骨架（无业务逻辑可跑通）
1. 创建 `pyproject.toml`（uv workspace）、`config.toml`、`.env.example`
2. 创建 `apps/backend` 骨架，FastAPI 起一个 `/health` 端点
3. 创建 `apps/mcp_server` 骨架，注册一个 dummy 工具
4. 创建 `apps/frontend` 骨架，Vue 3 + TS + Element Plus，能展示 hello world
5. `scripts/dev.sh` 能一键启动三个服务
6. **验收**：三服务都健康，前端能访问后端 `/health`

### Phase 2: 数据层
1. SQLModel 三张表 + alembic 初始迁移
2. `apps/backend/services/` 各文件骨架（空实现 + 类型签名）
3. CRUD API：sessions / tasks / settings
4. **验收**：API 测试全过

### Phase 3: K8s 工具迁移
按以下顺序逐个迁移 v2 工具到 `mcp_server/tools/`，每个工具完成时必须带单测：
1. `pods.py`（get / logs / delete）
2. `deployments.py`（get / scale / patch）
3. `services.py`
4. `nodes.py`
5. `events.py`
6. `metrics.py`（resource metrics）
7. `prometheus.py`
8. `relations.py`
**验收**：每个工具单测通过，pytest 覆盖率 > 90%

### Phase 4: LLM + MCP 编排
1. `services/llm.py`：流式调用 OpenAI 兼容 API
2. `services/mcp_client.py`：用官方 mcp SDK 连 mcp_server
3. `services/redact.py`：脱敏纯函数
4. `services/chat.py`：组装上述三者，返回 async generator
5. `api/chat.py`：SSE 端点
6. **验收**：集成测试，发一个 prompt 能得到完整 SSE 流

### Phase 5: 前端
1. SSE 客户端 + ChatView 主聊天界面
2. SessionsView / TasksView / SettingsView
3. ToolCallCard 组件展示工具调用过程
4. **验收**：手工跑一遍主流程

### Phase 6: 调度 & 通知
1. `services/scheduler.py` (APScheduler)
2. `services/notify.py` (DingTalk)
3. **验收**：建一个每分钟跑一次的任务，能收到钉钉推送

### Phase 7: 收尾
1. Dockerfile + docker-compose
2. `docs/architecture.md` / `adding-a-tool.md` / `deployment.md`
3. README 更新
4. **验收**：docker-compose up 即可全栈启动

---

## 8. 给 codex 的执行指令

**你（codex）的工作约束**：
- 严格按 Phase 1→7 顺序，不允许跨 phase 工作
- 每个 Phase 结束必须运行其验收命令并通过
- 每完成一个 Phase 提交一次 git commit，commit message 格式：`phase{N}: {简述}`
- 任何与本方案冲突的设计偏离，**先在 commit message 注明并暂停**，等用户确认
- 禁止引入本方案技术栈表以外的依赖（如确需，先提出）
- 所有代码注释、文档用中文；标识符用英文
- 测试用例命名：`test_<被测函数>_<场景>_<期望>`

**禁止行为**：
- 不要把 v2 的代码"复制粘贴"过来；必须按新结构重写
- 不要保留 v2 的环境变量名/配置文件名；新方案配置一律走 `config.toml` + `AppSettings` 表
- 不要恢复 localStorage 持久化
- 不要混用流式协议
- 不要在工具层写业务逻辑（如 LLM prompt 拼接），那是 backend/services 的事
