# 可持续交付计划

本计划把项目从“重构骨架可跑”推进到“可持续交付”。执行方式采用 spec 驱动：每个可交付切片先更新 `project_document/specs/`，再进入实现、测试、审查和交付。

## 交付节奏

| 阶段 | 目标 | 可交付物 | 验证门禁 |
| --- | --- | --- | --- |
| S0 仓库基线 | 新 clone 可安装、构建、测试 | README、Dockerfile、Git ignore 规则、最小测试 | `poetry run pytest`、`npm run build` |
| S1 ToolSearch MVP | 工具发现可本地运行 | tool catalog、ToolSearch MCP server、后端 stdio 接入 | ToolSearch 单测、后端 MCP 冒烟 |
| S2 工具执行治理 | 工具发现和执行分离 | IAM、risk level、确认、审计记录 | API 测试、审计断言 |
| S3 运维闭环 | 用户能完成真实只读诊断 | chat candidate cards、K8s/ECS 只读工具恢复 | 浏览器冒烟、minikube/模拟环境 |
| S4 调度与通知 | 定时任务能执行并通知 | Scheduler runner、DingTalk webhook | 调度集成测试、通知 mock |
| S5 发布流水线 | 交付过程可重复 | CI 命令、发布 checklist、自测报告模板、Docker ToolSearch runtime | 全量验证命令通过 |

## 当前优先级

1. Tool execution recovery：逐步把 `catalog_only` 工具恢复为可执行实现。
2. Full Compose smoke：按需启动 `docker compose up --build` 验证前后端联动。
3. 发布自测：按 `project_document/specs/sustainable-delivery/release-checklist.md` 和 `self-test-report-template.md` 固化每个切片结果。

## 工作规则

- 每个功能必须有 `requirements.md`、`design.md`、`tasks.md`。
- `tasks.md` 的任务必须能映射到验证命令。
- 真实配置、密钥、数据库、日志、kubeconfig 不进入版本控制。
- 修改前后端行为时至少跑 `backend-v2` 测试和 `frontend-v3` 构建。
- 涉及 UI 的变更需要补浏览器冒烟截图或报告。

## 风险台账

| 风险 | 影响 | 处理 |
| --- | --- | --- |
| Tool inventory 从旧版 21 个缩到当前 8 个 K8s 工具 | 运维能力倒退 | 用 ToolSearch catalog 先恢复可发现性，再逐步恢复执行 |
| Scheduler 只有 CRUD 没有 runner | UI 显示可配置但不会执行 | 已在 S4 接入 runner、手动运行和执行历史 |
| DingTalk 仅有配置字段 | 通知开关误导用户 | 已在 S4 接入 webhook service 和 mock-backed 测试 |
| Docker 后端镜像缺少 ToolSearch runtime | Compose 下启用 ToolSearch 会启动失败 | 已在 S5 改为根构建上下文并把 Node 22/ToolSearch dist 打入后端镜像 |
| 后端测试覆盖不足 | 重构容易回归 | 从公共端点测试扩展到 auth/session/MCP |
| 前端 bundle 偏大 | 首屏加载慢 | S3/S5 做 manualChunks 和路由级拆包 |
