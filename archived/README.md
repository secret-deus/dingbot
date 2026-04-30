# 已归档：独立 MCP Server 工程

`k8s-mcp-standalone/` 与 `ecs-mcp-standalone/` 为历史上 **单独进程 + FastAPI + SSE** 的 MCP 服务实现。

自本仓库合并改造后：

- **K8s / ECS 工具逻辑**已迁入主应用：`backend/src/k8s_mcp/`、`backend/src/ecs_mcp/`
- 运行时由 **`BUILTIN_K8S_ECS_TOOLS`（默认 `true`）** 在进程内注册并执行，无需再启动这两个子服务
- `scripts/start_all.py` 不再拉起上述独立 MCP 进程

若需回顾旧版完整 HTTP 服务、独立 Poetry 环境与启动方式，可查看本目录下代码与各自 `README.md`（自原 `k8s-mcp/`、`ecs-mcp/` 移动并改名）。
