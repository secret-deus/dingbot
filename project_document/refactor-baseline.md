# 重构基线与执行计划

更新时间：2026-04-29

## 当前判断

项目已经完成 K8s/ECS 工具并入主进程的迁移方向，但当前工作树仍处在半迁移状态：

- Git 曾处于 detached HEAD，已切到 `codex/refactor-baseline` 承接当前改动。
- 原独立 `k8s-mcp`、`ecs-mcp` 目录被删除，新实现位于 `backend/src/k8s_mcp`、`backend/src/ecs_mcp`。
- 后端主链路集中在 `backend/main.py`、`backend/src/api/v2/router.py`、`backend/src/llm/processor.py`、`backend/src/mcp/enhanced_client.py`。
- 前端聊天体验集中在 `frontend-v2/src/components/StreamChat.vue` 和 `frontend-v2/src/stores/chat.js`，组件、状态、流式协议和持久化高度耦合。

## 重构目标架构

```text
backend/
  app/bootstrap        应用启动、依赖注入、生命周期
  api                  HTTP/SSE 协议层，只做参数校验和响应编码
  use_cases            chat、inspection、scheduler 等业务用例
  llm_gateway          LLM provider、prompt、tool-call 适配
  tool_runtime         MCP/builtin tool、权限、审计、执行结果标准化
  adapters             k8s、ecs、dingtalk、prometheus 等外部系统适配
  config_security      配置加载、密钥、技能集、运行时策略

frontend-v2/src/
  app                  路由、应用壳、全局 provider
  features/chat        消息列表、输入区、工具调用面板、会话历史
  features/tools       MCP 工具浏览与配置
  features/scheduler   定时任务
  features/dashboard   系统状态和巡检入口
  shared/api           HTTP 客户端和错误归一
  shared/stream        后端流式事件解析
  shared/ui            基础组件
  shared/theme         设计变量和主题
```

## 分阶段执行

### Phase 0：基线收口

- 固定开发环境：Python 使用 `>=3.11,<3.14`，Node 使用 20/22 LTS。
- 修正开发脚本指向 `frontend-v2`，后端使用当前 Poetry Python 启动。
- 保留真实配置忽略策略，只提交 `config/*.example.json`。
- 增加聊天主链路的最低限度回归测试。

### Phase 1：聊天主链路拆分

- 从 `EnhancedLLMProcessor.stream_chat` 中抽出：
  - `ChatUseCase`
  - `ToolCallOrchestrator`
  - `StreamEventEncoder`
  - `LLMGateway`
- 后端统一输出结构化流式事件，禁止前端依赖临时字符串协议。
- API 层只负责把事件编码为 HTTP 流。

### Phase 2：前端 Chat 重做

- 拆分 `StreamChat.vue`：消息渲染、输入区、工具事件、错误态、空态、历史记录各自组件化。
- 拆分 `stores/chat.js`：会话状态、流式状态、持久化、用户偏好分离。
- 建立 `shared/stream`，只在一个地方解析后端事件。
- 以运维工具体验为基准：更紧凑的信息密度、更清晰的工具调用过程、更少装饰卡片。

### Phase 3：配置、权限、审计

- 配置中心只保留一套 API，不再散落在多个兼容路由中。
- Skill 从 UI 到后端执行链路保持一致。
- 运维工具默认只读，危险操作必须显式授权并产生审计记录。

### Phase 4：验证闭环

- 后端：核心 use case、tool runtime、配置加载、流式事件编码单测。
- 前端：stream parser 单测，Chat 页面浏览器回归。
- 集成：无真实云凭证时用 mock builtin tool，真实环境只做手动/受控测试。

## 第一刀范围

当前切片只做 Phase 0 和聊天链路最小防线：

- 不重写业务逻辑。
- 不删除用户已有迁移文件。
- 不引入新框架。
- 不触碰真实密钥配置。
- 只修正阻塞重构的入口、配置模板和已确认 bug。
