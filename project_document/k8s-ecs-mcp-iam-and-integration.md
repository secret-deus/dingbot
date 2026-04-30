# K8s / ECS MCP：权限、网络与跨项目集成说明

> **更完整的研发 Wiki（多章节、工具手册、排错）**：[wiki/k8s-ecs-mcp/README.md](./wiki/k8s-ecs-mcp/README.md)。

本文档面向**在其他项目中复用或对接**本仓库内进程内 K8s/ECS MCP 能力的开发与运维人员，说明：

- 阿里云侧 **RAM 权限（Action 粒度）**、开放域名与凭证形态；
- Kubernetes 侧 **RBAC / kubeconfig** 与代码实际调用的 API；
- Prometheus、后端 HTTP 等**非阿里云**依赖；
- 安全与排错要点。

**关联文档**：[k8s-ecs-mcp-tools-agent-guide.md](./k8s-ecs-mcp-tools-agent-guide.md)（工具名、源码与调用契约）。

---

## 1. 阿里云 ECS + 云监控（CloudMonitor）

### 1.1 代码实际调用的 OpenAPI / RPC

实现位置：`backend/src/ecs_mcp/`。当前实现**不依赖**阿里云 SDK 完成全部监控查询（部分路径为自签名 RPC + HTTP），但 RAM 授权需与 **OpenAPI 文档中的 Action 名称**一致（控制台 → RAM → 权限策略 → 脚本配置中可检索 `ecs:`、`cms:`）。

| 工具名（MCP） | 主要行为 | 调用方式 | 对应 API Action（RAM 侧） |
|---------------|----------|----------|---------------------------|
| `ecs-list-instances` | 列举/筛选实例 | `ecs_rpc.rpc_get` → `ecs.aliyuncs.com` | `DescribeInstances` → **`ecs:DescribeInstances`** |
| `ecs-inspect` | 巡检 + 拉监控摘要 | 同上 + 复用监控工具逻辑 | **`ecs:DescribeInstances`** + 下表 CMS |
| `ecs-describe-instance-monitor-data` | 实例监控时间序列 | ① `DescribeInstances` 解析地域；② **CMS** `metrics.*.aliyuncs.com` 上 `DescribeMetricList` / `QueryMetricList` | **`ecs:DescribeInstances`** + **`cms:DescribeMetricList`**、**`cms:QueryMetricList`** |

补充说明：

- **地域解析**：`ecs-describe-instance-monitor-data` 会按 `region_id` 参数、`ALIBABA_CLOUD_ECS_REGION_ID` 以及 `ALIBABA_CLOUD_REGION_CANDIDATES` 等多地域尝试 `DescribeInstances`，直到命中实例所在地域。RAM 需允许在**这些地域**查询实例（见 1.4 资源范围）。
- **云监控端点**：代码依次尝试 `https://metrics.{RegionId}.aliyuncs.com` 与 `https://metrics.aliyuncs.com`（见 `cms_rpc.py` 与 `ecs_monitor_data.py`）。
- **SDK 备用路径**：`backend/src/ecs_mcp/clients/ecs_client.py` 中存在 `ECSSDKClient.describe_instance_monitor_data`（对应 **`ecs:DescribeInstanceMonitorData`**），当前主流程以 **CMS RPC** 为主；若你后续启用 SDK 或合并分支后改为 SDK，**需额外授权** `ecs:DescribeInstanceMonitorData`。

### 1.2 网络与域名

运行 MCP 的服务器**必须能访问**（HTTPS 出站）：

| 用途 | 域名示例 |
|------|----------|
| ECS OpenAPI | `https://ecs.aliyuncs.com` |
| 云监控（区域） | `https://metrics.{region}.aliyuncs.com` |
| 云监控（公共） | `https://metrics.aliyuncs.com` |

若使用 VPC 内网 Endpoint、固定出口 IP 或代理，需在安全组与防火墙中放行上述目标；**无阿里云控制台权限**时，仅能通过「能访问上述 API」验证。

### 1.3 环境变量（与 `backend/src/ecs_mcp/config.py` 对齐）

| 变量 | 含义 |
|------|------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | RAM 用户 AccessKey ID |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | RAM 用户 AccessKey Secret |
| `ALIBABA_CLOUD_SECURITY_TOKEN` | 可选；**STS 临时凭证**的 Token（当前 **RPC 路径未使用 STS**，仅 `ECSSDKClient` 构造时支持；若全链路走 RPC，需改用支持 STS 的调用方式或长期 AK） |
| `ALIBABA_CLOUD_ECS_REGION_ID` | 默认地域，如 `cn-hangzhou` |
| `ALIBABA_CLOUD_REGION_CANDIDATES` | 可选，逗号分隔；监控工具在**未指定地域**时用于多地域探测实例 |
| `ECS_CALL_TIMEOUT` / `ECS_RETRY_ATTEMPTS` / `ECS_MAX_CONCURRENCY` | 调用超时、重试与并发（默认 30s 等） |

### 1.4 RAM 策略最小集（示例）

以下 JSON 为**最小只读**思路，用于「能跑通当前 ECS 三工具」；实际生产请按账号模型收紧 `Resource` 与 `Condition`（见 1.5）。

> **重要**：阿里云 RAM 中 Action 名称以控制台「权限策略编辑器」检索为准；若与 `cms:*` 命名不一致，请用控制台搜索 **DescribeMetricList** / **QueryMetricList** 对应的产品与 Action。

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeInstances"
      ],
      "Resource": [
        "acs:ecs:*:*:instance/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cms:DescribeMetricList",
        "cms:QueryMetricList"
      ],
      "Resource": "*"
    }
  ]
}
```

若启用 **SDK 的 `DescribeInstanceMonitorData`**，再增加：

```json
"ecs:DescribeInstanceMonitorData"
```

### 1.5 资源范围与条件（建议）

- **最小化**：用 RAM 的 **资源组** 或 **标签** 将 ECS 实例纳入范围，在策略中增加 `Condition`（如 `acs:ResourceTag`）限制仅业务实例。
- **多地域**：`DescribeInstances` 按 `RegionId` 调用；若 RAM 仅允许单地域，则多地域探测会失败——需为所有可能地域授权或收窄 `ALIBABA_CLOUD_REGION_CANDIDATES`。
- **审计**：开启 **ActionTrail** 记录 `ecs` / `cms` API 调用，便于跨项目责任界定。

---

## 2. Kubernetes

### 2.1 凭证与连接方式

- 配置：`backend/src/k8s_mcp/config.py`（`K8sConfig.from_env()`）。
- 客户端：`backend/src/k8s_mcp/k8s_client.py` 的 `K8sClient`。
- **当前实现**：通过 **`kubeconfig` 文件**加载（`config.load_kube_config`），**未**在代码中实现 in-cluster `ServiceAccount` 自动加载（若需 Pod 内运行，需自行挂载 kubeconfig 或扩展 `K8sClient._load_k8s_config`）。

环境变量要点：

| 变量 | 含义 |
|------|------|
| `KUBECONFIG_PATH` 或 `KUBECONFIG` | kubeconfig 路径 |
| `K8S_NAMESPACE` | 默认命名空间（工具参数可覆盖 `all` 等） |

连接自检会调用：

- `VersionApi.get_code()`（集群版本）
- `CoreV1Api.list_node(limit=1)`

### 2.2 进程内「只读」工具涉及的 K8s API

以下与 **builtin 注册的安全查询工具**一致（不写 Deployment、不 scale）；对应 `K8sClient` 方法中的 **read/list** 调用：

| 能力 | 资源 API（概念） | verbs |
|------|------------------|-------|
| Pod 列表 | `pods` | get, list |
| Service | `services` | get, list |
| Deployment | `deployments` | get, list |
| ReplicaSet（历史） | `replicasets` | list |
| Node | `nodes` | list |
| Event | `events` | list |
| Pod 详情 | `pods` + `events` | get, list |
| Pod 日志 | `pods/log` 子资源 | get |
| Endpoints | `endpoints` | get, list |

**命名空间**：`namespace=all` 时，会跨命名空间调用 `list_*_for_all_namespaces` 类接口，需 **ClusterRole** 或具备全集群 list 权限的绑定。

### 2.3 ClusterRole 示例（只读 + 日志）

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ding-robot-k8s-mcp-readonly
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "endpoints", "events", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/version", "/version/*"]
    verbs: ["get"]
```

将上述 `ClusterRole` 绑定到承载 kubeconfig 所用的用户/ServiceAccount（若使用证书用户，则对应 CSR 签发的身份）。

若仅允许**单命名空间**，可将 `ClusterRole` 改为 `Role` 并去掉 `namespace=all` 工具路径，或在前端/Agent 侧限制参数。

---

## 3. Prometheus（非阿里云）

工具：`k8s-prometheus-app-metrics`（`backend/src/k8s_mcp/tools/k8s_prometheus_app_metrics.py`）。

| 变量 | 含义 |
|------|------|
| `PROMETHEUS_URL` | Prometheus 根 URL（必填），如 `https://prom.example.com` |
| `PROMETHEUS_AUTH_TYPE` | `none` / `basic` / `bearer` |
| `PROMETHEUS_ACCESS_KEY` | basic 时用户名，或 bearer 时 token |
| `PROMETHEUS_SECRET_KEY` | basic 时密码 |

请求路径：`POST {PROMETHEUS_URL}/api/v1/query_range`（PromQL 依赖集群内 kube-state-metrics / cAdvisor 等典型指标）。

**权限**：不涉及阿里云 RAM；需保证网络可达及 Prometheus 自身鉴权策略允许查询。

---

## 4. 后端 HTTP / 钉钉（可选）

告警与通知相关代码（如 `resource_alert_service_v2`、`k8s_resource_analysis_report`）可能通过 **HTTP** 调用本仓库 `backend` API（`BACKEND_API_URL` / `backend_api_url`），由后端再发钉钉等。**对接方**需准备：

- 可路由的 `http(s)://` 后端地址；
- 若走内网，与 K8s/ECS 工具所在网络打通或同 VPC。

具体路径与鉴权以 `backend` 路由与部署为准，**不在本文展开**。

---

## 5. 跨项目集成检查清单

| 项 | 说明 |
|----|------|
| RAM 用户 | 仅 ECS 只读 + CMS 监控读，禁止 `RunInstances`、`DeleteInstance` 等写操作（除非业务扩展） |
| AK 保管 | 使用 KMS/密钥管理服务或环境注入，禁止写入镜像与 Git |
| 出站 | 放行 ECS、metrics 域名 HTTPS |
| K8s | kubeconfig 最小权限 + 定期轮换证书；区分「只读 Agent」与「运维写操作」集群角色 |
| Prometheus | 独立 URL 与鉴权；与 K8s RBAC 解耦 |
| 观测 | 对 API 失败率、429、RAM 拒绝原因做日志或告警 |

---

## 6. 版本与追溯

- 本文档依据仓库 `backend/src/ecs_mcp/`、`backend/src/k8s_mcp/k8s_client.py` 等实现整理；若升级阿里云 OpenAPI 版本或改用官方 SDK 统一封装，请重新核对 **Action 与 RAM 策略**。
- RAM Action 名称以阿里云控制台 **权限策略编辑器** 检索结果为准；若 `cms:*` 与控制台不一致，以控制台为准替换本文件中的示例。
