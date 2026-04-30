# 05 Kubernetes：kubeconfig 与 RBAC

[← Wiki 首页](./README.md)

## 1. 连接方式（当前实现）

- 代码：`K8sClient._load_k8s_config()` → `kubernetes.config.load_kube_config(config_file=kubeconfig_path)`。
- **未实现**：Pod 内 `load_incluster_config()`；若要在集群内跑，请 **挂载 kubeconfig Secret** 或 **扩展代码** 支持 in-cluster。

环境变量：`KUBECONFIG_PATH` 或 `KUBECONFIG`，否则尝试 `~/.kube/config`。

## 2. 连接自检调用的 API

`connect()` 成功后测试：

- `GET /version`（`VersionApi.get_code()`）
- `list_node(limit=1)`

因此 RBAC 至少需要能 **list nodes**（至少一个）与访问版本信息（见下 nonResourceURLs）。

## 3. 只读工具覆盖的 API 动词

与 `SAFE_QUERY_TOOLS` 中工具通过 `K8sClient` **读路径**一致（不含 scale/patch/delete）：

| Kubernetes 资源 | 典型 verbs |
|-----------------|------------|
| `pods` | get, list |
| `pods/log` | get |
| `services` | get, list |
| `endpoints` | get, list |
| `events` | list（及按 fieldSelector 的 list） |
| `nodes` | list |
| `deployments` | get, list |
| `replicasets` | list |

当 **`namespace=all`** 时，会调用 `list_*_for_all_namespaces`，需要 **集群范围** list 权限。

## 4. ClusterRole 示例（只读 + 日志）

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8s-ecs-mcp-readonly
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

将 `ClusterRoleBinding`/`RoleBinding` 绑定到 kubeconfig 对应的用户或 ServiceAccount。

**说明**：若集群启用了 **OPA/Gatekeeper**、**ValidatingWebhook** 等，可能仍拦截部分请求，与 RBAC 无关。

## 5. 单命名空间部署

若业务只允许查一个 NS：

- 使用 **Role + RoleBinding** 限制 `pods`、`services` 等资源到该 namespace；
- **禁止**在工具参数中传 `namespace=all`，否则客户端会调全集群 list，必然失败。

## 6. 与 `k8s_client.py` 中写操作的说明

`k8s_client.py` 内仍包含 **patch/create/scale** 等方法的实现，用于历史或其它入口；**当前 `SAFE_QUERY_TOOLS` 不注册写操作工具**。安全评审时应以 **实际注册工具** 为准，但若未来开放写工具，需单独评估 RBAC。

下一章：[06 K8s 工具手册](./06-tools-reference-kubernetes.md)
