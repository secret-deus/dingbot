# v2 K8s 工具实现参考（重写时对照用）

> 这份文档是 v2 代码删除前提取的"硬知识"——K8s API 调用模式、PromQL 查询、踩过的坑。
> 重写时**不要照搬代码**，但**必须照搬这些 API 调用与 Gotcha**，避免重新踩坑。
> 参见 [REWRITE_PLAN.md](../REWRITE_PLAN.md)。

---

## 0. 工具清单（重写时全部需要保留）

| 工具名 | 类别 | 优先级 |
|---|---|---|
| get_pods | 查询 | P0 |
| get_deployments | 查询 | P0 |
| get_services | 查询 | P0 |
| get_nodes | 查询 | P0 |
| get_logs | 查询 | P0 |
| get_events | 查询 | P0 |
| describe_pod | 查询 | P0 |
| get_endpoints | 查询 | P1 |
| get_deployment_history | 查询 | P1 |
| scale_deployment | 修改 | P0 |
| patch_deployment | 修改 | P0 |
| restart_deployment | 修改 | P1 |
| rollback_deployment | 修改 | P1 |
| create_deployment | 修改 | P2 |
| create_service | 修改 | P2 |
| patch_service | 修改 | P2 |
| update_service | 修改 | P2 |
| generate_deployment_yaml | 工具 | P2 |
| get_cluster_metrics | 监控 | P0 |
| resource_metrics_query | 监控 | P1（依赖知识图谱）|
| prometheus_app_metrics | 监控 | P0 |
| update_knowledge_graph_metrics | 监控 | P2 |
| relation_query | 智能 | P1（依赖知识图谱）|
| cluster_summary | 智能 | P1 |

P0 必须 phase 3 完成，P1 phase 6，P2 phase 7。

---

## 1. K8s API 调用速查表

所有调用基于官方 `kubernetes` Python 客户端的 async 接口。

### 1.1 Pods

```python
# 列出所有命名空间的 Pod
core_v1.list_pod_for_all_namespaces(label_selector=..., limit=100000)

# 列出某 namespace
core_v1.list_namespaced_pod(namespace=ns, label_selector=..., limit=100000)

# 单个 Pod 详情
core_v1.read_namespaced_pod(name=pod_name, namespace=ns)

# Pod 日志
core_v1.read_namespaced_pod_log(name=pod_name, namespace=ns, tail_lines=n, container=...)
```

**Gotcha**:
- `namespace="all"` → 用 `list_pod_for_all_namespaces`，不要传 `namespace="all"` 给 `list_namespaced_pod`（它会当字面值）
- `namespace=""`（空字符串）→ 转 `None`，否则 K8s 客户端报错
- Pod 状态字段：`status.phase`（Running/Pending/Succeeded/Failed/Unknown）
- 容器就绪：遍历 `status.container_statuses[].ready`，做 `ready_count/total`
- 多容器 Pod 取日志默认第一个容器；要指定必须传 `container=` 参数（v2 漏掉了，重写补上）
- 列表超 50 项主动截断，返回 `warning` 字段，提示用户加 label_selector

### 1.2 Deployments

```python
apps_v1.list_namespaced_deployment(namespace=ns, label_selector=...)
apps_v1.read_namespaced_deployment(name=name, namespace=ns)

# 扩缩容（专用 scale 子资源，效率比 patch 整体高）
apps_v1.patch_namespaced_deployment_scale(
    name=name, namespace=ns,
    body={"spec": {"replicas": replicas}}
)

# 通用 patch（修改镜像、env 等）
apps_v1.patch_namespaced_deployment(name=name, namespace=ns, body=patch_data)

# 重启（注意：不存在 restart API，靠改 annotation 触发滚动）
apps_v1.patch_namespaced_deployment(
    name=name, namespace=ns,
    body={"spec": {"template": {"metadata": {"annotations": {
        "kubectl.kubernetes.io/restartedAt": iso8601_now
    }}}}}
)

# 创建
apps_v1.create_namespaced_deployment(namespace=ns, body=deployment_config)

# 历史版本（通过 ReplicaSet）
apps_v1.list_namespaced_replica_set(namespace=ns, label_selector=f"app={dep_name}")
```

**Gotcha**:
- patch body 是 **strategic merge patch**，不是 JSON Patch（不要写 `[{"op":"replace",...}]`）
- 容器数组在 patch 中必须用 `name` 字段对齐，否则 K8s 不知道改哪个容器
- `restart` 没有 K8s API，必须改 `template.metadata.annotations` 触发新 ReplicaSet
- `scale` 用 `patch_namespaced_deployment_scale`，比改整体 spec 高效
- 创建时 `selector` 必须与 `template.metadata.labels` 一致，否则 K8s 拒绝
- `dry_run=true` 通过 query param `dryRun=All` 实现（kubernetes-client 库中是 `dry_run="All"`）
- 已存在时强制替换：先 read 获取 resourceVersion，再 patch；不要直接 create

### 1.3 Services / Endpoints

```python
core_v1.list_namespaced_service(namespace=ns, label_selector=...)
core_v1.read_namespaced_service(name=name, namespace=ns)
core_v1.create_namespaced_service(namespace=ns, body=service_config)
core_v1.patch_namespaced_service(name=name, namespace=ns, body=patch)

# Endpoints（看实际就绪的 Pod IP）
core_v1.list_namespaced_endpoints(namespace=ns, label_selector=...)
core_v1.read_namespaced_endpoints(name=svc_name, namespace=ns)
```

**Gotcha**:
- Endpoints 名字与 Service 名字相同（K8s 自动维护）
- Endpoints 为空 = 没有 Pod 匹配 selector 或 Pod 都没就绪——这是排障的关键信号
- Service `type` 改 ClusterIP↔NodePort 时，老的 NodePort 端口会保留直到下次重建
- selector 修改是即时生效的，但 Endpoints 同步需 1-2 秒

### 1.4 Nodes

```python
core_v1.list_node()
core_v1.read_node(name=node_name)
```

**Gotcha**:
- `status.allocatable` ≠ `status.capacity`：allocatable = capacity - reserved（kube/system reserved）
- 节点资源单位：CPU 是 millicores（"500m" 或 "0.5"，要统一），内存是字节数（要转 Gi）
- 节点条件 `status.conditions[]`：Ready / DiskPressure / MemoryPressure / PIDPressure / NetworkUnavailable

### 1.5 Events

```python
# 命名空间所有事件
core_v1.list_namespaced_event(namespace=ns, limit=...)

# 关联到特定 Pod 的事件（排障神器）
core_v1.list_namespaced_event(
    namespace=ns,
    field_selector=f"involvedObject.name={pod_name}"
)
```

**Gotcha**:
- Event 默认 TTL 1 小时（集群级配置），超时即丢失，不要假定能查到老 Event
- `reason` 字段是排障关键：FailedScheduling / FailedMount / Unhealthy / BackOff / OOMKilled
- `field_selector` 必须用 K8s 的 selector 语法，不是 PromQL 也不是 jq

---

## 2. Prometheus 集成

### 2.1 配置

```bash
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_AUTH_TYPE=none|basic|bearer
PROMETHEUS_ACCESS_KEY=...
PROMETHEUS_SECRET_KEY=...
```

重写时迁到 `AppSettings` 表（参见 [REWRITE_PLAN.md](../REWRITE_PLAN.md) §3）。

### 2.2 核心 PromQL 查询

#### CPU 使用率（vs limit）
```promql
sum(rate(container_cpu_usage_seconds_total{pod=~"<app>.*",namespace="<ns>"}[5m]))
  /
sum(container_spec_cpu_quota{pod=~"<app>.*",namespace="<ns>"} 
    / container_spec_cpu_period{pod=~"<app>.*",namespace="<ns>"})
```

#### 内存使用率（vs limit）
```promql
sum(container_memory_usage_bytes{pod=~"<app>.*",namespace="<ns>"})
  /
sum(container_spec_memory_limit_bytes{pod=~"<app>.*",namespace="<ns>"})
```

#### CPU 绝对值
```promql
sum(rate(container_cpu_usage_seconds_total{pod=~"<app>.*",namespace="<ns>"}[5m]))
```

#### 内存绝对值
```promql
sum(container_memory_usage_bytes{pod=~"<app>.*",namespace="<ns>"})
```

### 2.3 HTTP 端点

```
GET <PROMETHEUS_URL>/api/v1/query_range
    ?query=<promql>
    &start=<unix_ts>
    &end=<unix_ts>
    &step=1h         # 14 天用 1h，1 天用 1m
```

响应 JSON：
```json
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {...labels...},
        "values": [[ts, "value"], ...]
      }
    ]
  }
}
```

### 2.4 Gotcha

- **Pod 名正则匹配**：K8s Deployment 生成的 Pod 名是 `<deployment>-<rs-hash>-<pod-hash>`，所以用 `pod=~"<app>.*"` 匹配。如果 app 名带特殊字符（如 `.`），要 PromQL 转义
- **采集延迟**：kubelet → Prometheus 至少 30 秒延迟，不要查最近 1 分钟的数据
- **step 选择**：14 天数据用 step=1h（337 个点），1 天用 1m（1440 点）。step 太小会超时
- **空数据**：应用未跑过/已删除时，Prometheus 返回 `result: []`，不要当作错误，按 0 处理
- **认证**：basic 用 `Authorization: Basic base64(user:pass)`，bearer 用 `Authorization: Bearer <token>`，none 不传
- **PromQL 时间窗口**：`rate()` 至少要 4 倍于 scrape interval（默认 30s），所以最小 `[2m]`，推荐 `[5m]`
- **跨命名空间应用**：如果一个 deployment 跨多个 namespace（罕见），需要用 `namespace=~"ns1|ns2"` 替代单值匹配

---

## 3. 知识图谱 / 关系推理

### 3.1 数据结构

- 用 `networkx.DiGraph`（有向图）
- 节点 ID 格式：
  - 集群级：`<kind>/<name>`（如 `node/node-1`）
  - 命名空间级：`<kind>/<namespace>/<name>`（如 `pod/default/nginx-abc`）

### 3.2 关系类型

| 关系 | 来源 | 目标 | 提取方式 |
|---|---|---|---|
| ownership | Pod | ReplicaSet | `pod.metadata.ownerReferences` |
| ownership | ReplicaSet | Deployment | `rs.metadata.ownerReferences` |
| networking | Service | Pod | label selector 匹配 |
| hosting | Node | Pod | `pod.spec.nodeName` |
| dependency | App A | App B | env 引用 / configmap 引用 / service DNS |

### 3.3 同步策略

v2 用 `cluster_sync_engine` 定期全量拉取并重建图。重写时：
- **建议改为增量**：用 K8s watch API（`core_v1.list_namespaced_pod(watch=True)`）订阅事件，按 ADD/MODIFY/DELETE 增量更新
- 全量同步只在启动和定期校验（如每小时）时做

### 3.4 查询算法

| 查询类型 | 算法 |
|---|---|
| related_resources | BFS，max_depth 限制 |
| impact_analysis | 反向 BFS（沿入边） |
| dependency_trace | 正向 BFS（沿出边） |
| failure_propagation | 双向 BFS |
| cluster_topology | 子图导出 |

**必须用 visited set**，否则环依赖会死循环（v2 在 dependency 关系下出现过）。

### 3.5 Gotcha

- 资源未在图中 ≠ 不存在；可能是 sync 还没跑到。查询前最好检查 last_sync_at
- Service → Pod 关系不是 K8s 直接给的，要自己用 selector 在所有 Pod 上匹配（O(n)），高频查询要缓存
- ownerReferences 可能为空（手工创建的 Pod），不要假定一定有 owner
- TTL 清理：长时间未更新的节点要删掉，否则图无限增长

---

## 4. 数据脱敏（services/redact.py）

v2 在 LLM 处理器里散乱地脱敏。重写时抽成纯函数，输入 str 输出 str。

要脱敏的模式：
- IPv4：`\d{1,3}(\.\d{1,3}){3}` → `<IP>`
- IPv6：标准格式 → `<IPv6>`
- 端口（敏感上下文）：URL 中的 `:port`，独立的 `port=<n>` → `<PORT>`
- API key / token：`(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+` → `<REDACTED>`
- Bearer token：`Bearer\s+\S+` → `Bearer <REDACTED>`
- 中国手机号：`1[3-9]\d{9}` → `<PHONE>`
- 邮箱：`\S+@\S+\.\S+` → `<EMAIL>`

**Gotcha**：
- 不要脱敏 K8s 资源名（虽然有时长得像 token）
- 不要脱敏 PromQL/SQL 字符串里的字面量
- LLM tool_call 的 arguments 要脱敏后再写日志，但传给 mcp_server 时**不脱敏**（mcp_server 需要真值执行）
- 单元测试覆盖每种模式 + 无误伤的负样例

---

## 5. MCP 协议（重写时换官方 SDK）

v2 自己实现了 SSE 协议（`POST /tools/call` + `GET /events`），不兼容标准 MCP。

**重写时直接用官方 [`mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk)**：

```python
# mcp_server 端
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("k8s-mcp")

@mcp.tool()
async def get_pods(namespace: str = "default") -> list[dict]:
    """获取 namespace 下的 Pod 列表"""
    ...

# 启动 stdio 或 SSE
mcp.run(transport="sse")  # 或 "stdio"
```

```python
# backend 端
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://mcp_server:8000/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("get_pods", {"namespace": "default"})
```

好处：
- 不用维护协议代码
- 与 Claude Desktop / 其他 MCP 客户端互通
- 自动处理重连、超时、错误格式

---

## 6. 通用 Gotcha 清单（v2 踩过的坑）

1. **K8s 客户端是有状态的**：单例模式，启动时用 `config.load_kube_config()` 或 `config.load_incluster_config()` 一次。多次加载会造成连接泄漏
2. **资源单位转换**：CPU `500m` = 0.5 core，`2` = 2 cores；内存 `Gi`/`Mi`/`Ki` 都是 1024 进制，`G`/`M`/`K` 是 1000 进制——**别搞混**
3. **时间字段**：K8s 返回的 `creation_timestamp` 是带时区的 datetime，不是字符串。前端展示前要 isoformat
4. **空 namespace 默认值**：v2 在 10 个工具里各自 fallback 到 `config.namespace`——重写时统一在 `K8sClient` 包装层处理
5. **list 操作的 limit**：传 100000 实质是"无上限"，但 K8s 默认分页返回 500，多于 500 时返回 `continue` token，要自己拼
6. **patch 时 resourceVersion 冲突**：高并发改同一资源时会 409，要重试（指数退避）
7. **Pod 删除是异步的**：`delete_namespaced_pod` 返回成功不代表 Pod 没了，`status.phase` 还会是 `Terminating` 几秒到几分钟
8. **kubectl 等价物对照**：
   - `kubectl get pods` → `list_namespaced_pod`
   - `kubectl describe pod X` → `read_namespaced_pod` + `list_namespaced_event(field_selector=...)`
   - `kubectl logs X` → `read_namespaced_pod_log`
   - `kubectl scale deployment X --replicas=N` → `patch_namespaced_deployment_scale`
   - `kubectl rollout restart deployment X` → `patch_namespaced_deployment` + 改 annotation
   - `kubectl rollout undo deployment X` → 找上一个 ReplicaSet 的 podTemplate，patch 回去

---

## 7. 重写时 phase 3 推荐迁移顺序

按"**先简单查询、后复杂操作；先单资源、后跨资源**"：

1. `pods.py`：get_pods、get_pod、describe_pod、get_pod_logs、delete_pod
2. `deployments.py`：get_deployments、get_deployment、scale_deployment、patch_deployment、restart_deployment
3. `services.py`：get_services、get_service、create_service、patch_service
4. `nodes.py`：get_nodes、get_node
5. `events.py`：get_events、get_pod_events
6. `metrics.py`：get_cluster_metrics（只用 K8s API，不依赖 Prometheus）
7. `prometheus.py`：query_app_cpu、query_app_memory、query_app_metrics（含历史聚合）
8. `relations.py`：依赖知识图谱构建完成后再做

每个工具完成必须：
- 写 `@mcp.tool()` 装饰器
- 用 fake k8s client 写至少 3 个单测（正常 / 空结果 / API 错误）
- 在 docstring 写清楚参数和返回值（mcp SDK 自动用作 tool description）
