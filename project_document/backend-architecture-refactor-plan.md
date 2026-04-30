# 后端架构重构方案

生成时间：2026-04-29

## 当前判断

这个项目的核心方向是对的：前端提供 Web 运维工作台，后端把 DingTalk、LLM、MCP 工具、K8s/ECS 能力和定时巡检串起来。但现在后端架构仍然偏“原型期”：启动入口、API 路由、LLM 编排、MCP 执行和配置热更新彼此缠在一起，导致继续扩展前端体验或接入更多工具时会越来越难维护。

已完成的基线清理里，独立 `k8s-mcp` / `ecs-mcp` 已迁到主进程内工具能力，流式聊天协议也已经有结构化事件层。下一步不建议继续在现有大文件上补功能，应该先把运行时边界拆出来。

## 主要问题

### 1. 应用入口承担过多职责

`backend/main.py` 同时负责日志、环境变量、配置迁移、MCP 连接、LLM 初始化、DingTalk 初始化、巡检任务、调度器、静态文件挂载和 SPA fallback。它还暴露全局变量给 API 端点导入。

风险：

- API 层通过 `from main import ...` 获取运行时实例，测试和热重载容易受导入顺序影响。
- 任意配置管理器初始化都可能创建目录、迁移文件或启动 watcher，副作用过早。
- 静态文件 `backend/static/spa/index.html` 不存在时，根路径仍会返回 `FileResponse`，部署缺失前端产物时会变成运行时错误。

### 2. API v2 汇总路由已经变成兼容层堆叠

`backend/src/api/v2/router.py` 约 898 行，既有核心聊天接口，也有工具接口、LLM/MCP 兼容接口、debug 接口、provider stub、路由注册和对 `main` 的运行时访问。

风险：

- 路由职责不清，前端不知道哪些接口是正式契约、哪些只是历史兼容。
- `/api/v2/chat/stream` 内部同时判断 CrewAI、stream fallback、工具校验、SSE header、错误格式，难以单测。
- 多个配置接口表达相同概念，例如 `/config/llm`、`/llm/config/*`、`/config/llm/providers*`，会让前端状态同步变复杂。

### 3. LLM 编排器是最大单体

`backend/src/llm/processor.py` 约 2140 行。它同时做供应商客户端初始化、工具选择、工具参数修复、工具结果摘要、上下文裁剪、脱敏、流式输出、兼容统计和 fallback 文案。

风险：

- 工具执行策略、模型调用、响应事件和结果摘要耦合在一个类里，后续换模型或加 Agent 编排成本很高。
- 当前有敏感配置日志风险，例如初始化时打印完整 `self.config`。
- 工具参数和工具结果被多处直接写日志，可能泄露 kubeconfig 路径、实例 ID、sessionWebhook 或业务数据。

### 4. MCP 客户端同时做连接、工具执行和配置回写

`backend/src/mcp/enhanced_client.py` 约 1406 行。它同时负责 SSE/stdio 连接、工具发现、工具过滤、SSE 队列等待、内置工具合并、配置文件自动同步和权限推断。

风险：

- 连接层和配置写入层耦合，工具发现事件可能直接改 `config/mcp_config.json`。
- SSE 工具结果等待使用单队列重新放回消息，多个并发调用下容易造成结果饥饿或顺序问题。
- builtin 和 remote 工具的边界还不够清晰，未来增加 Prometheus、日志、CMDB、工单类工具时会继续膨胀。

### 5. 配置层路径和副作用不收敛

`MCPConfigManager`、`LLMConfigManager`、`ConfigManager` 都会查找环境变量、创建目录、迁移历史配置、写备份或启动文件 watcher。它们目前默认依赖进程 cwd。

风险：

- 从不同工作目录启动会影响 `config/*.json` 解析。
- 测试导入配置管理器时容易生成真实目录或备份。
- 配置 reload、runtime rebuild 和前端保存 API 没有统一事务语义。

### 6. 安全边界不足

前端登录目前主要依赖 localStorage 状态；后端 CORS 使用 `allow_origins=["*"]` 且 `allow_credentials=True`。工具调用默认只做 Skill 过滤，没有统一的“只读/高危/需确认/审计”执行策略。

风险：

- Web UI 适合内网自用，但一旦暴露到更大网络，认证和 CORS 都不够。
- LLM 可调用工具时缺少明确的操作等级和审批钩子。
- DingTalk webhook、sessionWebhook、LLM API key、MCP auth token 的日志脱敏需要统一落地。

## 目标架构

目标不是“拆得很碎”，而是建立几个稳定边界：

```text
backend/src/app/
  settings.py          # 唯一配置入口，解析 env + json，输出不可变 settings
  container.py         # 运行时依赖容器，持有 llm、tool_runtime、dingtalk、scheduler
  lifespan.py          # FastAPI 生命周期，只负责编排启动/关闭

backend/src/api/v2/
  chat.py              # /chat 和 /chat/stream
  tools.py             # 工具列表、工具执行状态
  config_llm.py        # LLM 配置正式接口
  config_mcp.py        # MCP/工具配置正式接口
  scheduler.py         # 调度任务
  inspection.py        # 巡检
  compatibility.py     # 历史接口集中放这里，并标记 sunset

backend/src/chat/
  use_case.py          # 聊天业务用例
  events.py            # 后端内部事件模型 + SSE 编码
  tool_loop.py         # 工具决策和多轮执行
  summarizer.py        # 工具结果摘要

backend/src/llm/
  gateway.py           # OpenAI-compatible client 封装
  models.py            # LLM 请求/响应模型

backend/src/tool_runtime/
  registry.py          # 统一工具注册表
  executor.py          # 并发、超时、重试、审计
  permissions.py       # read/write/dangerous 分类和确认策略
  adapters/
    k8s.py
    ecs.py
    remote_mcp.py

backend/src/security/
  redaction.py         # 日志、配置、工具参数统一脱敏
  audit.py             # 工具调用审计事件
```

## 分阶段执行

### Phase 1：先建立依赖容器和安全日志

改动范围小，但收益大。

- 新增 `app/settings.py`，集中解析 `config.env`、`config/*.json` 路径，禁止业务模块自行猜 cwd。
- 新增 `app/container.py`，把 `mcp_client`、`llm_processor`、`dingtalk_bot`、scheduler 从 `main.py` 全局变量迁走。
- FastAPI dependency 从 `from main import ...` 改为 `request.app.state.container`。
- 新增 `security/redaction.py`，先处理 API key、token、secret、webhook、headers、工具参数日志。
- 修复 `backend/static` 不存在时的 SPA fallback，后端 API 服务和前端静态部署解耦。

验收：

- `backend/tests` 全过。
- `python -c "from main import app"` 不创建无关配置备份。
- 启动日志不出现完整 API key、webhook、auth token、sessionWebhook。

### Phase 2：拆 API 路由

- `router.py` 只保留 `api_v2_router = APIRouter(prefix="/api/v2")` 和 include。
- 聊天接口迁到 `api/v2/chat.py`。
- config/provider/debug 兼容接口迁到 `api/v2/compatibility.py`，文档标出保留周期。
- 前端 API client 只使用正式接口，移除“暂不支持”的 provider stub 调用。

验收：

- OpenAPI tags 清晰：Chat / Tools / Config / Scheduler / Inspection / Compatibility。
- 每个路由文件不超过 300-400 行。
- 前端能跑通登录、仪表盘、聊天、MCP 配置、定时任务。

### Phase 3：拆 LLM 聊天用例

- `EnhancedLLMProcessor` 降级为 `LLMGateway` 或兼容 facade。
- 把多轮工具循环迁到 `chat/tool_loop.py`。
- 把工具结果摘要迁到 `chat/summarizer.py`。
- 后端内部只流转结构化 `ChatEvent`，SSE 是 API 层编码细节。
- CrewAI 作为独立 orchestrator adapter，不再直接写在 API route 中判断。

验收：

- 单测覆盖：无工具聊天、工具一次调用、多轮工具、工具失败、LLM client 缺失、空消息、CrewAI fallback。
- 前端不再依赖纯文本分隔符 `---` 判断阶段。

### Phase 4：统一工具运行时

- 已开始落地 `backend/src/mcp/runtime.py`，以 `LocalMCPRuntime` 统一本地 K8s/ECS 工具注册、枚举和调用。
- `config/mcp_config.json` 的 K8s/ECS 主路径改为 `type=local`、`provider=k8s|ecs`，不再依赖独立 SSE 服务。
- 后续可新增 `tool_runtime/registry.py` 或将 `LocalMCPRuntime` 平滑迁移到该目录，统一 builtin K8s/ECS 和 remote MCP 工具。
- `EnhancedMCPClient` 拆成 `RemoteMCPConnection`、`RemoteMCPRegistry`、`RemoteMCPExecutor`。
- 禁止工具发现事件直接写主配置；改成返回 discovery diff，由配置 API 或后台任务显式接受。
- 增加工具等级：`read`、`change`、`dangerous`。
- 高危工具统一进入确认流：Web 二次确认、DingTalk 审批或只生成命令不执行。

验收：

- 并发工具调用用 request_id 独立 Future，不共享反复 put-back 的单队列。
- 工具执行审计记录包含 user/session/skill/tool/parameters_redacted/result_status/duration。

### Phase 5：前后端契约和部署收口

- 生成 `openapi.json`，前端基于契约生成/约束 API 类型。
- 后端只提供 API；前端构建产物由部署层决定是否挂载。
- 配置 examples、README、启动脚本保持一致。
- 删除 compatibility 路由里确认为无前端调用的接口。

验收：

- `npm run build`、`poetry run pytest`、浏览器 smoke 测试形成固定回归命令。
- 兼容接口调用量为 0 后，再做源码删除。

## 优先级最高的具体修复

1. 立即修日志脱敏：`processor.py`、`enhanced_client.py`、`dingtalk/bot.py` 中所有完整配置、工具参数、webhook 输出都要走 redaction。
2. 立即拆运行时依赖：API 不再 import `main`。
3. 立即保护静态文件：`backend/static` 不存在时不挂载或返回明确 404/API-only 提示。
4. 先把 `router.py` 分文件，再继续做前端重设计。
5. 工具执行引入权限等级和审计，尤其是未来一旦加入写操作或自动修复。

## 不建议现在直接删除的代码

- `backend/src/api/v2/endpoints/resources.py`：前端 Dashboard 的资源指标更新仍在调用。
- `backend/src/k8s_mcp`、`backend/src/ecs_mcp`：虽然独立服务已归档，但 builtin 工具仍引用这些包内 registry 和 tool 实现。
- `frontend-v2/src/utils/auth.js`：看起来和 Pinia auth store 重叠，但需要先确认所有旧组件引用后再删。
- `createEventSource` 辅助函数：当前主聊天流使用 fetch POST，不代表该函数一定无用，应在前端 API 调用收口时统一清理。
