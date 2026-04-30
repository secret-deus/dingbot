# 09 排错与 FAQ

[← Wiki 首页](./README.md)

## 1. 阿里云相关

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `未配置阿里云AK/SK` | 环境变量未注入 | 检查 `backend/config.env` 或进程环境，`ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET`。 |
| `403` / RAM 拒绝 | 缺 Action 或 Resource 过窄 | 在 RAM 控制台搜索报错中的 Action，补 [04](./04-aliyun-ram-network-security.md) 策略。 |
| 监控无数据、地域不对 | 实例不在默认地域 | 传 `region_id` 或设置 `ALIBABA_CLOUD_REGION_CANDIDATES`。 |
| 连接超时 | 出站被防火墙拦截 | 放行 `ecs.aliyuncs.com`、`metrics.*.aliyuncs.com`。 |
| CMS Action 名不一致 | 产品与文档版本差异 | **以 RAM 控制台检索到的 Action 为准** 替换策略示例。 |

## 2. Kubernetes 相关

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `Kubeconfig文件不存在` | 路径错误 | 设置 `KUBECONFIG_PATH` 或 `KUBECONFIG`，或放 `~/.kube/config`。 |
| `Forbidden` / `Unauthorized` | RBAC 不足 | 按 [05](./05-kubernetes-rbac-and-kubeconfig.md) 补 ClusterRole 或缩小 `namespace` 不用 `all`。 |
| `list_pod_for_all_namespaces` 失败 | 只有 Namespace 权限 | 不要用 `namespace=all`，或改为集群角色。 |
| `pods/log` 403 | 缺子资源权限 | RBAC 增加 `pods/log` **get**。 |

## 3. Prometheus 相关

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| `未配置Prometheus URL` | `PROMETHEUS_URL` 空 | 配置可访问的 Prometheus 根 URL。 |
| 查询结果为空 | PromQL 与集群标签不一致 | 检查 `k8s_prometheus_app_metrics.py` 内 Pod 命名正则与 `namespace`。 |
| 401 | 认证失败 | 设置 `PROMETHEUS_AUTH_TYPE` 与 basic/bearer 凭据。 |

## 4. Builtin 未注册

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 工具列表无 K8s/ECS | `BUILTIN_K8S_ECS_TOOLS=false` | 设为 `true` 或删除变量。 |
| 远程与 builtin 重复 | 配置问题 | 使用 `MCP_SKIP_REMOTE_SERVER_NAMES` 或 builtin 实现标记。 |

## 5. FAQ

**Q1：进程内工具和远程 MCP 会重复吗？**
A：若配置不当可能重复；用跳过列表与 `implementation=builtin` 对齐（见 [02](./02-architecture-and-data-flow.md)）。

**Q2：能否用 STS 替代长期 AK？**
A：当前 RPC 未传 `SecurityToken`；需改造或走 SDK 统一凭证（见 [04](./04-aliyun-ram-network-security.md)）。

**Q3：`k8s_client` 里有写操作，是否安全？**
A：当前 **SAFE_QUERY_TOOLS 未暴露写工具**；评审以注册表为准；若合并写工具需单独 RBAC。

**Q4：Wiki 与代码不一致听谁的？**
A：以 **源码** 为准；请提 PR 更新 Wiki。

---

[返回 Wiki 首页](./README.md)
