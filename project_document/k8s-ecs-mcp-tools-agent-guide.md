# K8s / ECS MCP 工具逻辑说明（Agent 开发用）

> **给研发的完整 Wiki（权限、配置、工具手册、排错）** 见：[project_document/wiki/k8s-ecs-mcp/README.md](./wiki/k8s-ecs-mcp/README.md)。

本文档概括主进程内 **Kubernetes** 与 **阿里云 ECS** 两套 MCP 工具的实现位置、注册方式、调用契约与逐工具语义，供开发 Agent（含 CrewAI / 自研编排）时对齐行为。

**源码根路径**：`backend/src/k8s_mcp/`、`backend/src/ecs_mcp/`
**进程内入口**：`backend/src/mcp/builtin_k8s_ecs.py`（`register_builtin_tools_once` → `execute_builtin_tool`）

---

## 1. 架构与数据流

### 1.1 工具基类与协议

- 基类：`backend/src/k8s_mcp/core/tool_registry.py` 中的 `MCPToolBase`
- 每个工具需实现：
  - `get_schema() -> MCPToolSchema`（`backend/src/k8s_mcp/core/mcp_protocol.py`）
  - `async execute(arguments: dict) -> MCPCallToolResult`
- `MCPToolSchema` 字段：`name`、`description`、`input_schema`（JSON Schema 对象）、可选 `timeout`、`category`

### 1.2 注册表

- K8s：`tool_registry.register(instance, "kubernetes")`
- ECS：`tool_registry.register(instance, "ecs")`
- 注册实现：`k8s_mcp/tools/__init__.py` 的 `register_all_tools()`、`ecs_mcp/tools/__init__.py` 的 `register_all_tools()`

### 1.3 主应用如何暴露给 LLM / Agent

1. `builtin_k8s_ecs.register_builtin_tools_once()` 调用上述 `register_all_tools`
2. `merge_builtin_mcptools()` 将各工具的 `get_schema()` 转为后端统一类型 `MCPTool`（见 `backend/src/mcp/types.py`）
3. `EnhancedMCPClient.call_tool(name, parameters)` 若 `name` 为进程内工具，则 `execute_builtin_tool` → 对应 `tool_registry.execute_tool`

### 1.4 返回契约（Agent 解析结果）

- `MCPCallToolResult` 含 `content: List[dict]`，通常为 `{"type":"text","text": "<JSON 字符串>"}`
- `builtin_k8s_ecs.mcp_call_result_to_payload` 会把该文本 **反序列化为 dict** 再交给上层；失败时可能是纯字符串或 `{"error": true, "message": "..."}`

---

## 2. 配置与环境依赖

**跨项目对接（阿里云 RAM、K8s RBAC、网络、检查清单）** 优先阅读 Wiki：[wiki/k8s-ecs-mcp/README.md](./wiki/k8s-ecs-mcp/README.md)；摘要版：[k8s-ecs-mcp-iam-and-integration.md](./k8s-ecs-mcp-iam-and-integration.md)。

### 2.1 Kubernetes

- 配置：`backend/src/k8s_mcp/config.py`（`get_config()`），通常来自 `KUBECONFIG` / `KUBECONFIG_PATH` 及 `backend/config.env` 等；**当前实现以 kubeconfig 文件为主**，Pod 内 in-cluster 需自行扩展 `K8sClient._load_k8s_config`
- 客户端：`backend/src/k8s_mcp/k8s_client.py` 的 `K8sClient`

### 2.2 Prometheus（部分 K8s 工具）

- 环境变量示例：`PROMETHEUS_URL`、`PROMETHEUS_ACCESS_KEY`、`PROMETHEUS_SECRET_KEY`、`PROMETHEUS_AUTH_TYPE`
- 用于：`k8s-prometheus-app-metrics`、`k8s-update-knowledge-graph-metrics`（间接）等

### 2.3 知识图谱（部分 K8s 工具）

- `k8s_mcp/core/k8s_graph.py`：`get_shared_knowledge_graph()`
- 开关与行为受 `get_config().enable_knowledge_graph` 等影响；未启用时部分工具降级或报错

### 2.4 阿里云 ECS

- `backend/src/ecs_mcp/config.py`：`ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET`、地域等
- RPC：`ecs_mcp/clients/ecs_rpc.py`、`cms_rpc.py`（DescribeInstances、监控查询等）

---

## 3. Kubernetes 工具一览

当前 `k8s_mcp/tools/__init__.py` 中 **AVAILABLE_TOOLS = SAFE_QUERY_TOOLS**，均为**读/分析向**能力（写操作类已从说明中移除）。

| 工具名 | 简述 | 主要依赖 | 源码文件 |
|--------|------|----------|----------|
| `k8s-get-pods` | Pod 列表，支持 namespace、label_selector；大量结果会截断并告警 | K8sClient | `k8s_get_pods.py` |
| `k8s-get-services` | Service 列表/查询 | K8sClient | `k8s_get_services.py` |
| `k8s-get-deployments` | Deployment 列表或单个详情 | K8sClient | `k8s_get_deployments.py` |
| `k8s-get-nodes` | Node 列表 | K8sClient | `k8s_get_nodes.py` |
| `k8s-get-logs` | Pod 日志 | K8sClient | `k8s_get_logs.py` |
| `k8s-describe-pod` | Pod 详情 | K8sClient | `k8s_describe_pod.py` |
| `k8s-get-events` | 事件列表 | K8sClient | `k8s_get_events.py` |
| `k8s-get-deployment-history` | Deployment 历史/回滚信息类查询 | K8sClient | `k8s_get_deployment_history.py` |
| `k8s-get-endpoints` | Endpoints 查询 | K8sClient | `k8s_get_endpoints.py` |
| `k8s-relation-query` | 资源关联、影响分析、依赖、故障传播、拓扑等（依赖知识图谱与 QueryHandler 时功能更全） | K8sClient、KnowledgeGraph、RelationQueryHandler | `k8s_relation_query.py` |
| `k8s-cluster-summary` | 集群摘要 | K8sClient 等 | `k8s_cluster_summary.py` |
| `k8s-get-cluster-metrics` | 集群级指标入口 | K8sClient / 指标管道 | `k8s_get_cluster_metrics.py` |
| `k8s-resource-metrics-query` | 资源指标查询 | 配置与指标后端 | `k8s_resource_metrics_query.py` |
| `k8s-prometheus-app-metrics` | 按 app_name + namespace 查 Prometheus 的 CPU/内存等（14d/1d 等模式） | aiohttp + PROMETHEUS_* | `k8s_prometheus_app_metrics.py` |
| `k8s-update-knowledge-graph-metrics` | 批量用 Prometheus 结果刷新知识图谱内应用指标 | KnowledgeGraph、K8sPrometheusAppMetricsTool | `k8s_update_knowledge_graph_metrics.py` |
| `k8s-resource-monitor` | 手动触发资源监控、告警联动（ResourceAlertService 等可选） | ResourceAlertService、MetricsAggregator、KG | `k8s_resource_monitor.py` |
| `k8s-metrics-coverage-report` | 指标覆盖报告 | 指标与配置 | `k8s_metrics_coverage_report.py` |
| `k8s-resource-analysis-report` | 基于知识图谱生成异常资源报告与建议，可选钉钉通知 | `k8s_resource_analysis_report.py` 核心逻辑 | `k8s_resource_analysis_report_tool.py` |

**Agent 提示**：

- 带 **namespace** 的参数多数支持 `"all"` 表示全命名空间（以各工具 `get_schema` 为准）。
- `k8s-relation-query` 的 `query_type` 枚举见 `k8s_relation_query.py` 内 `get_schema`（如 `related_resources`、`impact_analysis`、`cluster_topology` 等）。
- 长耗时工具在 schema 或类上可能带较大 `timeout`（例如分析报告类），编排时需设足 LLM/工具超时。

---

## 4. ECS 工具一览

| 工具名 | 简述 | 主要依赖 | 源码文件 |
|--------|------|----------|----------|
| `ecs-list-instances` | DescribeInstances 分页列出实例 ID、名称、状态、可用区 | 阿里云 RPC `ecs.aliyuncs.com`、AK/SK | `ecs_list_instances.py` |
| `ecs-describe-instance-monitor-data` | 实例监控时序：时间窗、Period 自动选择、分片、下采样、summary | ECS/CMS RPC、ECSSDKClient | `ecs_monitor_data.py` |
| `ecs-inspect` | 多条件批量选实例 + 拉监控 + 阈值规则 + Markdown 报告落盘 | 复用监控工具、DescribeInstances | `ecs_inspection.py` |

**Agent 提示**：

- 无 AK/SK 时工具会直接返回错误文案（见各 `execute` 首段校验）。
- `ecs-inspect` 默认 `timeout` 较长（类上可设为 120s），且可能写 `project_document/reports/ecs/`（见该文件内 `Path` 逻辑）。

---

## 5. 与 Agent 集成的推荐方式

1. **工具发现**：启动后通过后端已有 MCP 客户端 `list_tools()` 或 OpenAPI `GET /api/v2/skills` + 内部 `SkillRegistry` 做白名单过滤（见 `config/skills.json`、`backend/src/skills/registry.py`）。
2. **调用**：统一走 `EnhancedMCPClient.call_tool(name, dict_params)`，不要绕过 Skill 校验（若已设置 `skill_id`）。
3. **参数**：严格使用各工具 `get_schema().input_schema` 的 JSON Schema；必填项以 schema `required` 为准。
4. **结果**：按「JSON 文本 → dict」解析；错误时检查 `error` / `is_error` 类字段。

---

## 6. 扩展阅读（源码树）

```
backend/src/k8s_mcp/
├── core/
│   ├── tool_registry.py      # 注册表、MCPToolBase
│   ├── mcp_protocol.py       # MCPToolSchema、MCPCallToolResult
│   ├── k8s_graph.py          # 知识图谱
│   └── relation_query_handler.py
├── k8s_client.py
├── tools/                    # 各工具实现
└── config.py

backend/src/ecs_mcp/
├── core/tool_registry.py
├── tools/
├── clients/ecs_rpc.py, cms_rpc.py
└── config.py

backend/src/mcp/builtin_k8s_ecs.py  # 进程内合并与执行入口
```

---

*文档随源码迭代；若与 `get_schema()` 不一致，以源码为准。*
