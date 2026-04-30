# 03 配置全表

[← Wiki 首页](./README.md)

配置来源以 **环境变量** 为主，部分键在 `backend/config.env` 或 `.env` 中维护；ECS 模块会尝试加载 `backend/config.env`（见 `ecs_mcp/config.py` 的 `_load_envs`）。

---

## 1. 进程内 Builtin 总开关

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BUILTIN_K8S_ECS_TOOLS` | `true` | `false` 时不在进程内注册 K8s/ECS 工具。 |
| `MCP_SKIP_REMOTE_SERVER_NAMES` | （空） | 逗号分隔，跳过与 builtin 重复的远程 MCP 服务名。 |

---

## 2. 阿里云 ECS MCP（`backend/src/ecs_mcp/config.py`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ECS_MCP_HOST` | `0.0.0.0` | 若单独起 ECS MCP HTTP 时使用（主进程 builtin 通常不监听此端口）。 |
| `ECS_MCP_PORT` | `8002` | 同上。 |
| `ECS_MCP_DEBUG` | `false` | 调试。 |
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | — | RAM 用户 AK。 |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | — | RAM 用户 SK。 |
| `ALIBABA_CLOUD_SECURITY_TOKEN` | — | STS Token；**当前 RPC 主路径未传 STS**，见 [04](./04-aliyun-ram-network-security.md)。 |
| `ALIBABA_CLOUD_ECS_REGION_ID` | `cn-hangzhou` | 默认地域。 |
| `ECS_CALL_TIMEOUT` | `30` | 秒。 |
| `ECS_RETRY_ATTEMPTS` | `3` | 重试次数（若上层使用）。 |
| `ECS_MAX_CONCURRENCY` | `3` | 并发上限（若上层使用）。 |

**监控工具地域探测**（非 `ECSConfig` 字段，见 `ecs_monitor_data.py`）：

| 变量 | 说明 |
|------|------|
| `ALIBABA_CLOUD_REGION_CANDIDATES` | 逗号分隔地域列表；未指定实例地域时按序调用 `DescribeInstances` 探测。 |

---

## 3. Kubernetes MCP（`backend/src/k8s_mcp/config.py` → `K8sConfig.from_env()`）

### 3.1 连接与进程

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `KUBECONFIG_PATH` | — | 优先；kubeconfig 路径。 |
| `KUBECONFIG` | — | 次选；与 kubectl 一致。 |
| 未设置时 | `~/.kube/config`（若存在） | 自动回退。 |
| `K8S_NAMESPACE` | `default` | 工具未传 namespace 时的默认。 |
| `K8S_MCP_HOST` | `localhost` | 独立 k8s-mcp 服务时用。 |
| `K8S_MCP_PORT` | `8766` | 同上。 |
| `K8S_MCP_DEBUG` | `false` | 调试。 |

### 3.2 知识图谱（可选）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_KNOWLEDGE_GRAPH` | `false` | `true` 时启用图相关能力。 |
| `SYNC_INTERVAL` | `300` | 同步间隔（秒）。 |
| `GRAPH_MAX_DEPTH` | `3` | 图查询深度。 |
| `GRAPH_TTL` | `3600` | 节点 TTL（秒）。 |
| `GRAPH_MEMORY_LIMIT` | `1024` | MB。 |
| `MAX_SUMMARY_SIZE_KB` | `10` | 摘要大小上限。 |
| `WATCH_TIMEOUT` | `600` | Watch API 超时（秒）。 |
| `MAX_RETRY_COUNT` | `3` | 重试。 |

### 3.3 监控与告警（部分工具）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MONITORING_ENABLED` | `true` | — |
| `METRICS_COLLECTION_INTERVAL` | `30` | 秒。 |
| `METRICS_HISTORY_SIZE` | `1000` | — |
| `HEALTH_CHECK_ENABLED` | `true` | — |
| `HEALTH_CHECK_INTERVAL` | `30` | 秒。 |
| `RESOURCE_ALERT_ENABLED` | `true` | 资源告警。 |
| `MEMORY_ALERT_THRESHOLD` | `0.7` | 0~1。 |
| `CPU_ALERT_THRESHOLD` | `0.8` | 0~1。 |
| `ALERT_COOLDOWN_SECONDS` | `300` | 冷却。 |
| `ENABLE_LLM_ANALYSIS` | `true` | 部分报告是否走 LLM。 |
| `LLM_ANALYSIS_TIMEOUT` | `30` | 秒。 |

### 3.4 后端 API（告警/通知 HTTP）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BACKEND_API_URL` | `http://localhost:8000` | 资源告警等回调本仓库后端。 |
| `ENABLE_BACKEND_NOTIFICATIONS` | `true` | 是否发后端通知。 |
| `API_TIMEOUT` | `30` | 秒。 |
| `API_MAX_RETRIES` | `3` | — |

阈值类（`ALERT_*_MAX`）见源码 `from_env` 完整列表。

---

## 4. Prometheus（`k8s_prometheus_app_metrics.py`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROMETHEUS_URL` | `""` | **必填**；根 URL，无尾部斜杠问题由代码拼接 `/api/v1/query_range`。 |
| `PROMETHEUS_AUTH_TYPE` | `none` | `none` / `basic` / `bearer`。 |
| `PROMETHEUS_ACCESS_KEY` | — | basic 用户名或 bearer token。 |
| `PROMETHEUS_SECRET_KEY` | — | basic 密码。 |

---

## 5. 配置文件路径约定

| 用途 | 常见路径 |
|------|----------|
| 后端环境 | `backend/config.env` |
| MCP 技能白名单 | `config/skills/`（见集成章） |
| ECS 巡检报告输出 | `project_document/reports/ecs/`（`ecs-inspect`） |

下一章：[04 阿里云 RAM 与网络](./04-aliyun-ram-network-security.md)
