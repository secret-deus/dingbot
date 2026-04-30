# 06 Kubernetes 工具手册（SAFE_QUERY_TOOLS）

[← Wiki 首页](./README.md)

本章面向研发：**工具名、源码、主要参数、依赖的 K8s API、特殊注意点**。
完整 JSON Schema 以各文件 `get_schema()` 为准。

**通用约定**

- 多数工具支持 `namespace: "all"` 表示全命名空间（以 schema 为准）。
- 首次调用前会 `K8sClient.connect()`；失败时返回错误信息。
- 返回体：`MCPCallToolResult` → 文本 JSON，见 [02](./02-architecture-and-data-flow.md)。

---

## 1. 基础查询

| 工具名 | 源码 | 主要参数 | K8sClient 方法 / API 含义 |
|--------|------|----------|---------------------------|
| `k8s-get-pods` | `k8s_get_pods.py` | `namespace`, `label_selector` | `get_pods` → `list_namespaced_pod` / `list_pod_for_all_namespaces` |
| `k8s-get-services` | `k8s_get_services.py` | `namespace`, `label_selector`, `name` | `get_services` → list/read Service |
| `k8s-get-deployments` | `k8s_get_deployments.py` | `namespace`, `label_selector`, `name` | `get_deployments` → list/read Deployment |
| `k8s-get-nodes` | `k8s_get_nodes.py` | `label_selector` | `get_nodes` → `list_node` |
| `k8s-get-logs` | `k8s_get_logs.py` | `pod_name`, `namespace`, `lines`, `since` | `get_pod_logs` → `read_namespaced_pod_log` |
| `k8s-describe-pod` | `k8s_describe_pod.py` | `pod_name`, `namespace` | `describe_pod` → `read_namespaced_pod` + `list_namespaced_event` |
| `k8s-get-events` | `k8s_get_events.py` | `namespace`, `limit` | `get_events` → `list_event_for_all_namespaces` 或 `list_namespaced_event` |
| `k8s-get-deployment-history` | `k8s_get_deployment_history.py` | `name`, `namespace` | `get_deployment_history` → read Deployment + list ReplicaSet |
| `k8s-get-endpoints` | `k8s_get_endpoints.py` | `namespace`, `name`, `label_selector` | `get_endpoints` → read/list Endpoints |

**注意**

- `k8s-get-pods` 等对列表有 **limit**（如 100000），超大集群可能耗时/占内存，需关注超时。
- 日志 `read_namespaced_pod_log` 需 RBAC 对 `pods/log` 的 **get**。

---

## 2. 智能与聚合

| 工具名 | 源码 | 依赖 | 说明 |
|--------|------|------|------|
| `k8s-relation-query` | `k8s_relation_query.py` | `KnowledgeGraph`（`ENABLE_KNOWLEDGE_GRAPH=true` 时）、`RelationQueryHandler` | `query_type`：`related_resources`、`impact_analysis`、`dependency_trace`、`failure_propagation`、`cluster_topology`、`anomaly_correlation`。未启用图谱时走基础模式（见日志）。 |
| `k8s-cluster-summary` | `k8s_cluster_summary.py` | K8sClient + 配置 | 集群摘要聚合。 |
| `k8s-get-cluster-metrics` | `k8s_get_cluster_metrics.py` | `get_nodes` + `get_pods(namespace=all)` | 集群级指标入口。 |

---

## 3. 指标与 Prometheus

| 工具名 | 源码 | 环境变量 | 说明 |
|--------|------|----------|------|
| `k8s-resource-metrics-query` | `k8s_resource_metrics_query.py` | 见 `get_config` 与 metrics 后端 | 资源指标查询管道。 |
| `k8s-prometheus-app-metrics` | `k8s_prometheus_app_metrics.py` | `PROMETHEUS_URL` 必填；`PROMETHEUS_AUTH_*` | `POST .../api/v1/query_range`；PromQL 依赖集群内 kube-state-metrics / cAdvisor 等。 |
| `k8s-update-knowledge-graph-metrics` | `k8s_update_knowledge_graph_metrics.py` | 图谱 + Prometheus | 批量用 Prometheus 更新知识图谱内应用指标。 |
| `k8s-metrics-coverage-report` | `k8s_metrics_coverage_report.py` | 指标与配置 | 指标覆盖报告。 |

---

## 4. 监控、告警与报告

| 工具名 | 源码 | 说明 |
|--------|------|------|
| `k8s-resource-monitor` | `k8s_resource_monitor.py` | 可选联动 `ResourceAlertService`、`MetricsAggregator`、KG。 |
| `k8s-resource-analysis-report` | `k8s_resource_analysis_report_tool.py`（逻辑在 `k8s_resource_analysis_report.py`） | 异常资源报告；可选 **HTTP 调后端** 发钉钉（需 `BACKEND_API_URL` 等）。 |

**编排提示**：分析报告类可能 **长时间运行** + 大 JSON 输出；建议 **提高 LLM/工具超时** 或分页/摘要。

---

## 5. 研发调试

1. 单工具：`tool_registry.get_tool("k8s-get-pods")` 后 `execute({...})`（需在测试环境注入 `K8sClient` 连接）。
2. 确认 `get_schema()` 与 Agent 传的参数键一致（蛇形命名）。
3. `namespace=all` 时确认 RBAC 为 [05](./05-kubernetes-rbac-and-kubeconfig.md) 的 ClusterRole 级。

下一章：[07 ECS 工具手册](./07-tools-reference-ecs.md)
