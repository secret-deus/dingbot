# K8s / ECS 进程内 MCP — 研发 Wiki

> **定位**：说明本仓库内 **内置（builtin）Kubernetes 与阿里云 ECS MCP 工具** 的架构、配置、权限、工具契约与排错，供**其他项目/团队**的研发、联调与安全评审使用。

**阅读顺序**

1. 先读 [01-introduction-and-glossary.md](./01-introduction-and-glossary.md)（背景、术语、与「远程 MCP」的区别）。
2. 再读 [02-architecture-and-data-flow.md](./02-architecture-and-data-flow.md)（进程内注册、调用链、与 LLM/Agent 的关系）。
3. 按角色选读：
   - **后端/Agent 开发**：[08-integration-for-developers.md](./08-integration-for-developers.md)、[06-tools-reference-kubernetes.md](./06-tools-reference-kubernetes.md)、[07-tools-reference-ecs.md](./07-tools-reference-ecs.md)。
   - **配置与联调**：[03-configuration.md](./03-configuration.md)。
   - **安全/云账号**：[04-aliyun-ram-network-security.md](./04-aliyun-ram-network-security.md)、[05-kubernetes-rbac-and-kubeconfig.md](./05-kubernetes-rbac-and-kubeconfig.md)。
   - **排错**：[09-troubleshooting-and-faq.md](./09-troubleshooting-and-faq.md)。

**Wiki 文档索引**

| 章节 | 说明 |
|------|------|
| [01 引言与术语](./01-introduction-and-glossary.md) | 文档范围、名词表、源码根路径 |
| [02 架构与数据流](./02-architecture-and-data-flow.md) | 分层图、builtin 开关、注册与执行路径 |
| [03 配置全表](./03-configuration.md) | ECS / K8s / Prometheus / 后端等环境变量 |
| [04 阿里云 RAM 与网络](./04-aliyun-ram-network-security.md) | Action 粒度、策略示例、域名、STS、审计 |
| [05 Kubernetes RBAC](./05-kubernetes-rbac-and-kubeconfig.md) | kubeconfig、ClusterRole、namespace=all |
| [06 K8s 工具手册](./06-tools-reference-kubernetes.md) | 每个工具：参数、依赖、K8s API、注意点 |
| [07 ECS 工具手册](./07-tools-reference-ecs.md) | 每个工具：参数、阿里云 API、RAM、副作用 |
| [08 研发对接指南](./08-integration-for-developers.md) | Skill、call_tool、扩展点、自检清单 |
| [09 排错与 FAQ](./09-troubleshooting-and-faq.md) | 常见错误码与处理 |

**仓库内旧文档（仍保留，本 Wiki 为增强版）**

- [project_document/k8s-ecs-mcp-tools-agent-guide.md](../../k8s-ecs-mcp-tools-agent-guide.md) — 工具清单速查；
- [project_document/k8s-ecs-mcp-iam-and-integration.md](../../k8s-ecs-mcp-iam-and-integration.md) — 权限与集成摘要（本 Wiki 第 04、05 章展开）。

**源码锚点（便于全局搜索）**

- 进程内入口：`backend/src/mcp/builtin_k8s_ecs.py`
- K8s 工具注册：`backend/src/k8s_mcp/tools/__init__.py`（`SAFE_QUERY_TOOLS`）
- ECS 工具注册：`backend/src/ecs_mcp/tools/__init__.py`

---

*若本 Wiki 与源码 `get_schema()` 或环境变量默认值不一致，以源码为准；欢迎提交 PR 修正文档。*
