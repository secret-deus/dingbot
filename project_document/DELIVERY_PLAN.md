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

1. RC1 发布候选收口：本地验证、Compose smoke、浏览器 smoke 和自测报告已完成，
   详见 `project_document/specs/release-candidate-hardening/self-test-report-rc1.md`。
2. AccessKey 轮换：本轮手工测试使用过粘贴到对话里的 AK/SK，进入共享或长期环境前
   必须轮换。
3. Real Aliyun resource smoke：在具备 ECS/LB/SLS 具体资源 ID 或映射后，验证 detail、
   metrics、load-balancer health 和 SLS log tools。
4. 产品化治理：在 RC1 后再推进真实权限管理 API、审计筛选、DingTalk 实发验收和
   危险操作确认流设计。

## 工作规则

- 每个功能必须有 `requirements.md`、`design.md`、`tasks.md`。
- `tasks.md` 的任务必须能映射到验证命令。
- 真实配置、密钥、数据库、日志、kubeconfig 不进入版本控制。
- 修改前后端行为时至少跑 `backend-v2` 测试和 `frontend-v3` 构建。
- 涉及 UI 的变更需要补浏览器冒烟截图或报告。

## 风险台账

| 风险 | 影响 | 处理 |
| --- | --- | --- |
| Tool inventory 从旧版 21 个缩到当前 8 个 K8s 工具 | 运维能力倒退 | 已用 ToolSearch catalog 恢复并扩展到 55 个可执行工具 |
| Scheduler 只有 CRUD 没有 runner | UI 显示可配置但不会执行 | 已在 S4 接入 runner、手动运行和执行历史 |
| DingTalk 仅有配置字段 | 通知开关误导用户 | 已在 S4 接入 webhook service 和 mock-backed 测试 |
| Docker 后端镜像缺少 ToolSearch runtime | Compose 下启用 ToolSearch 会启动失败 | 已在 S5 改为根构建上下文并把 Node 22/ToolSearch dist 打入后端镜像 |
| 本地 MCP 配置包含宿主机绝对路径 | Compose 内 ToolSearch stdio 启动失败 | RC1 已在 MCP manager 中按运行时 repo root 规范化 Node/cwd/env 路径 |
| 后端测试覆盖不足 | 重构容易回归 | 从公共端点测试扩展到 auth/session/MCP |
| 前端 bundle 偏大 | 首屏加载慢 | S3/S5 做 manualChunks 和路由级拆包 |
| 本地验证依赖错误 Node.js | `scripts/verify.sh` 在部分 shell 下可能找不到 `tsc` 或触发 Homebrew Node 动态库错误 | RC1 先固定验证入口，再决定文档化或脚本化 Node 选择 |
