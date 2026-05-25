import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = resolve(import.meta.dirname, "../../..");
const sourcePath = resolve(repoRoot, "config/mcp_config.json");
const fallbackPath = resolve(repoRoot, "config/mcp_config.example.json");
const outputPath = resolve(repoRoot, "config/tool_catalog.json");

const executableBuiltins = new Set([
  "k8s-get-pods",
  "k8s-get-services",
  "k8s-describe-service",
  "k8s-get-endpoints",
  "k8s-get-deployments",
  "k8s-get-replicasets",
  "k8s-get-ingresses",
  "k8s-describe-ingress",
  "k8s-get-nodes",
  "k8s-get-logs",
  "k8s-describe-pod",
  "k8s-get-events",
  "k8s-get-deployment-history",
  "k8s-rollout-status",
  "k8s-get-statefulsets",
  "k8s-get-daemonsets",
  "k8s-get-jobs",
  "k8s-get-cronjobs",
  "k8s-get-hpas",
  "k8s-get-networkpolicies",
  "k8s-get-namespaces",
  "k8s-get-configmaps",
  "k8s-describe-configmap",
  "k8s-get-secrets",
  "k8s-describe-secret",
  "k8s-get-serviceaccounts",
  "k8s-get-pvcs",
  "k8s-get-pvs",
  "k8s-get-storageclasses",
  "k8s-get-resourcequotas",
  "k8s-get-limitranges",
  "k8s-get-roles",
  "k8s-get-rolebindings",
  "k8s-get-clusterroles",
  "k8s-get-clusterrolebindings",
  "k8s-get-pod-disruption-budgets",
  "k8s-get-cluster-metrics",
  "k8s-prometheus-app-metrics",
  "k8s-cluster-summary",
  "k8s-sync-knowledge-graph",
  "k8s-relation-query",
  "k8s-resource-metrics-query",
  "k8s-update-knowledge-graph-metrics",
  "k8s-resource-monitor",
  "k8s-metrics-coverage-report",
  "k8s-resource-analysis-report",
  "k8s-scale-deployment",
  "k8s-restart-deployment",
  "k8s-edit-resource",
  "k8s-patch-resource",
  "k8s-delete-resource",
  "k8s-exec-pod",
  "ecs-list-instances",
  "ecs-describe-instance-monitor-data",
  "ecs-inspect",
  "aliyun-ecs-list-instances",
  "aliyun-ecs-describe-instance",
  "aliyun-ecs-list-security-groups",
  "aliyun-ecs-describe-security-group-rules",
  "aliyun-cms-get-ecs-metrics",
  "aliyun-cms-get-alerts",
  "aliyun-cms-get-event-history",
  "aliyun-sls-list-logstores",
  "aliyun-sls-query-logs",
  "aliyun-sls-query-error-summary",
  "aliyun-lb-list-instances",
  "aliyun-lb-describe-health",
  "aliyun-swas-list-instances",
]);

const dangerLevels = new Map([
  ["k8s-scale-deployment", "write"],
  ["k8s-restart-deployment", "write"],
  ["k8s-edit-resource", "write"],
  ["k8s-patch-resource", "write"],
  ["k8s-delete-resource", "dangerous"],
  ["k8s-exec-pod", "dangerous"],
]);

const optionalProperties = new Map([
  ["k8s-get-pods", new Set(["namespace", "all_namespaces", "label_selector"])],
  ["k8s-get-services", new Set(["service_name", "namespace"])],
  ["k8s-get-endpoints", new Set(["service_name", "namespace", "label_selector"])],
  ["k8s-get-ingresses", new Set(["ingress_name", "namespace"])],
  ["k8s-get-configmaps", new Set(["configmap_name", "namespace", "include_data"])],
  ["k8s-describe-configmap", new Set(["namespace", "include_data"])],
  ["k8s-get-secrets", new Set(["secret_name", "namespace"])],
  ["k8s-rollout-status", new Set(["workload_type", "namespace"])],
  ["k8s-sync-knowledge-graph", new Set(["namespace", "all_namespaces"])],
  ["k8s-resource-metrics-query", new Set(["namespace", "resource_type"])],
  ["k8s-update-knowledge-graph-metrics", new Set(["namespace", "all_namespaces"])],
  ["k8s-resource-monitor", new Set(["app_name", "namespace"])],
  ["aliyun-ecs-list-instances", new Set(["region_id", "status", "name", "tag_filters", "page_size"])],
  ["aliyun-ecs-describe-instance", new Set(["region_id"])],
  ["aliyun-ecs-list-security-groups", new Set(["region_id", "vpc_id", "instance_id"])],
  ["aliyun-ecs-describe-security-group-rules", new Set(["region_id", "direction"])],
  ["aliyun-cms-get-ecs-metrics", new Set(["region_id", "metrics", "relative_range", "period"])],
  ["aliyun-cms-get-alerts", new Set(["region_id", "resource_id", "state", "relative_range"])],
  ["aliyun-cms-get-event-history", new Set(["region_id", "resource_id", "relative_range", "event_type"])],
  ["aliyun-sls-list-logstores", new Set(["service", "env", "region_id"])],
  ["aliyun-sls-query-logs", new Set(["service", "env", "query", "relative_range", "limit"])],
  ["aliyun-sls-query-error-summary", new Set(["env", "relative_range"])],
  ["aliyun-lb-list-instances", new Set(["region_id", "type", "name", "tag_filters"])],
  ["aliyun-lb-describe-health", new Set(["region_id", "type"])],
  ["aliyun-swas-list-instances", new Set(["region_id", "status", "name", "tag_filters", "page_size"])],
]);

const blueprint = [
  ["k8s-get-pods", "获取 Pod 列表", "获取 Kubernetes Pod 列表，支持命名空间、全部命名空间和标签过滤", ["k8s", "kubernetes", "pod", "pods", "列表", "工作负载", "label", "all namespaces"], { namespace: "命名空间，传 all 查询全部命名空间", all_namespaces: "是否查询全部命名空间", label_selector: "标签选择器" }, ["查看 default 命名空间下的 Pod", "查看全部命名空间的 Pod", "按 app=nginx 标签筛选 Pod"]],
  ["k8s-get-services", "获取 Service 列表", "获取 Kubernetes Service 列表或单个 Service 详细信息", ["k8s", "service", "svc", "服务", "端口", "访问"], { service_name: "Service 名称", namespace: "命名空间" }, ["查看 default 命名空间下的 Service"]],
  ["k8s-describe-service", "描述 Service 详情", "获取 Kubernetes Service 详细信息，包括 selector、端口和访问类型", ["k8s", "service", "svc", "服务", "describe", "详情", "端口"], { service_name: "Service 名称", namespace: "命名空间" }, ["描述 nginx Service 的访问配置"]],
  ["k8s-get-deployments", "获取 Deployment 列表", "获取 Kubernetes Deployment 列表或单个 Deployment 详细信息", ["k8s", "deployment", "deploy", "工作负载", "副本", "镜像"], { namespace: "命名空间" }, ["查看生产命名空间的 Deployment 副本状态"]],
  ["k8s-get-replicasets", "获取 ReplicaSet 列表", "获取 Kubernetes ReplicaSet 列表，支持命名空间和标签过滤", ["k8s", "replicaset", "rs", "副本集", "deployment", "工作负载"], { namespace: "命名空间", label_selector: "标签选择器" }, ["查看 default 命名空间下的 ReplicaSet"]],
  ["k8s-get-ingresses", "获取 Ingress 列表", "获取 Kubernetes Ingress 列表或单个 Ingress 详情", ["k8s", "ingress", "ing", "入口", "域名", "路由"], { ingress_name: "Ingress 名称", namespace: "命名空间" }, ["查看 default 命名空间下的 Ingress"]],
  ["k8s-describe-ingress", "描述 Ingress 详情", "获取 Kubernetes Ingress 路由、TLS 和后端 Service 详情", ["k8s", "ingress", "describe", "域名", "路由", "tls"], { ingress_name: "Ingress 名称", namespace: "命名空间" }, ["描述 web Ingress 的路由规则"]],
  ["k8s-get-nodes", "获取 Node 列表", "获取 Kubernetes Node 列表", ["k8s", "node", "nodes", "节点", "集群", "版本"], {}, ["查看集群节点列表"]],
  ["k8s-get-logs", "获取 Pod 日志", "获取 Kubernetes Pod 日志", ["k8s", "pod", "logs", "log", "日志", "故障排查"], { pod_name: "Pod 名称", namespace: "命名空间", tail_lines: "返回日志行数" }, ["查看 nginx Pod 最近 100 行日志"]],
  ["k8s-describe-pod", "描述 Pod 详情", "获取 Kubernetes Pod 详细信息", ["k8s", "pod", "describe", "详情", "事件", "容器"], { pod_name: "Pod 名称", namespace: "命名空间" }, ["描述异常 Pod 的容器和调度状态"]],
  ["k8s-get-events", "获取事件列表", "获取 Kubernetes 事件列表", ["k8s", "event", "events", "事件", "告警", "调度"], { namespace: "命名空间" }, ["查看 default 命名空间近期事件"]],
  ["k8s-get-deployment-history", "获取 Deployment 版本历史", "获取 Kubernetes Deployment 的版本历史和变更记录", ["k8s", "deployment", "history", "rollout", "版本", "发布", "回滚"], { deployment_name: "Deployment 名称", namespace: "命名空间" }, ["查看 nginx Deployment 发布历史"]],
  ["k8s-rollout-status", "查看发布状态", "查看 Deployment、StatefulSet 或 DaemonSet 的 rollout 发布状态", ["k8s", "rollout", "status", "deployment", "statefulset", "daemonset", "发布"], { workload_type: "资源类型", name: "资源名称", namespace: "命名空间" }, ["查看 nginx Deployment 发布是否完成"]],
  ["k8s-get-statefulsets", "获取 StatefulSet 列表", "获取 Kubernetes StatefulSet 列表，支持命名空间和标签过滤", ["k8s", "statefulset", "sts", "有状态", "工作负载"], { namespace: "命名空间", label_selector: "标签选择器" }, ["查看 default 命名空间下的 StatefulSet"]],
  ["k8s-get-daemonsets", "获取 DaemonSet 列表", "获取 Kubernetes DaemonSet 列表，支持命名空间和标签过滤", ["k8s", "daemonset", "ds", "节点守护", "工作负载"], { namespace: "命名空间", label_selector: "标签选择器" }, ["查看集群节点守护进程状态"]],
  ["k8s-get-jobs", "获取 Job 列表", "获取 Kubernetes Job 列表，支持命名空间和标签过滤", ["k8s", "job", "jobs", "批处理", "任务"], { namespace: "命名空间", label_selector: "标签选择器" }, ["查看批处理 Job 执行结果"]],
  ["k8s-get-cronjobs", "获取 CronJob 列表", "获取 Kubernetes CronJob 列表，支持命名空间和标签过滤", ["k8s", "cronjob", "cron", "定时任务", "批处理"], { namespace: "命名空间", label_selector: "标签选择器" }, ["查看定时任务最近调度状态"]],
  ["k8s-get-hpas", "获取 HPA 列表", "获取 HorizontalPodAutoscaler 列表和副本伸缩状态", ["k8s", "hpa", "autoscaling", "自动扩缩容", "副本"], { namespace: "命名空间" }, ["查看应用自动扩缩容状态"]],
  ["k8s-get-networkpolicies", "获取 NetworkPolicy 列表", "获取 Kubernetes NetworkPolicy 列表和规则数量", ["k8s", "networkpolicy", "netpol", "网络策略", "安全"], { namespace: "命名空间" }, ["查看命名空间网络策略"]],
  ["k8s-get-namespaces", "获取 Namespace 列表", "获取 Kubernetes Namespace 列表和状态", ["k8s", "namespace", "namespaces", "命名空间"], {}, ["查看集群命名空间"]],
  ["k8s-get-configmaps", "获取 ConfigMap 列表", "获取 ConfigMap 列表或单个 ConfigMap，默认只返回键名和大小", ["k8s", "configmap", "cm", "配置", "键值"], { configmap_name: "ConfigMap 名称", namespace: "命名空间", include_data: "是否返回 data 内容" }, ["查看应用配置键名"]],
  ["k8s-describe-configmap", "描述 ConfigMap 详情", "描述单个 ConfigMap，默认不返回 data 内容", ["k8s", "configmap", "describe", "配置", "详情"], { configmap_name: "ConfigMap 名称", namespace: "命名空间", include_data: "是否返回 data 内容" }, ["描述 nginx ConfigMap"]],
  ["k8s-get-secrets", "获取 Secret 列表", "获取 Secret 列表或单个 Secret 元数据，值默认脱敏", ["k8s", "secret", "secrets", "密钥", "脱敏"], { secret_name: "Secret 名称", namespace: "命名空间" }, ["查看 Secret 键名但不暴露值"]],
  ["k8s-describe-secret", "描述 Secret 元数据", "描述单个 Secret 的类型和键名，值始终脱敏", ["k8s", "secret", "describe", "密钥", "脱敏"], { secret_name: "Secret 名称", namespace: "命名空间" }, ["描述镜像拉取 Secret 元数据"]],
  ["k8s-get-serviceaccounts", "获取 ServiceAccount 列表", "获取 ServiceAccount 列表和关联 Secret", ["k8s", "serviceaccount", "sa", "账号", "rbac"], { namespace: "命名空间" }, ["查看 ServiceAccount"]],
  ["k8s-get-pvcs", "获取 PVC 列表", "获取 PersistentVolumeClaim 列表和绑定状态", ["k8s", "pvc", "storage", "存储", "卷"], { namespace: "命名空间" }, ["查看命名空间 PVC 绑定情况"]],
  ["k8s-get-pvs", "获取 PV 列表", "获取 PersistentVolume 列表和绑定状态", ["k8s", "pv", "storage", "存储", "卷"], {}, ["查看集群 PV 绑定情况"]],
  ["k8s-get-storageclasses", "获取 StorageClass 列表", "获取 StorageClass 列表和 provisioner 配置", ["k8s", "storageclass", "sc", "存储类", "provisioner"], {}, ["查看集群存储类"]],
  ["k8s-get-resourcequotas", "获取 ResourceQuota 列表", "获取命名空间 ResourceQuota 的 hard/used 用量", ["k8s", "resourcequota", "quota", "配额", "资源"], { namespace: "命名空间" }, ["查看命名空间资源配额"]],
  ["k8s-get-limitranges", "获取 LimitRange 列表", "获取命名空间 LimitRange 限制策略", ["k8s", "limitrange", "limit", "资源限制", "配额"], { namespace: "命名空间" }, ["查看默认资源限制"]],
  ["k8s-get-roles", "获取 Role 列表", "获取命名空间 Role 和权限规则摘要", ["k8s", "role", "rbac", "权限"], { namespace: "命名空间" }, ["查看命名空间权限角色"]],
  ["k8s-get-rolebindings", "获取 RoleBinding 列表", "获取命名空间 RoleBinding 和主体绑定关系", ["k8s", "rolebinding", "rbac", "权限", "绑定"], { namespace: "命名空间" }, ["查看用户或服务账号绑定的角色"]],
  ["k8s-get-clusterroles", "获取 ClusterRole 列表", "获取集群级 ClusterRole 和权限规则摘要", ["k8s", "clusterrole", "rbac", "集群权限"], {}, ["查看集群角色"]],
  ["k8s-get-clusterrolebindings", "获取 ClusterRoleBinding 列表", "获取集群级 ClusterRoleBinding 和主体绑定关系", ["k8s", "clusterrolebinding", "rbac", "集群权限", "绑定"], {}, ["查看集群角色绑定"]],
  ["k8s-get-pod-disruption-budgets", "获取 PDB 列表", "获取 PodDisruptionBudget 列表和可中断状态", ["k8s", "pdb", "poddisruptionbudget", "可用性", "中断预算"], { namespace: "命名空间" }, ["查看应用维护窗口中断预算"]],
  ["k8s-get-endpoints", "获取 Service 端点", "获取 Kubernetes Service 端点信息，显示实际的 Pod IP 和端口", ["k8s", "service", "endpoint", "endpoints", "pod ip", "端点", "服务发现"], { service_name: "Service 名称", namespace: "命名空间", label_selector: "标签选择器" }, ["查看 Service 后端 Pod IP"]],
  ["k8s-relation-query", "查询资源关系", "查询 Kubernetes 资源之间的关联关系，支持影响分析、依赖追踪和故障传播分析", ["k8s", "relation", "topology", "依赖", "关系", "影响分析", "链路"], { resource_name: "资源名称", namespace: "命名空间", resource_type: "资源类型" }, ["分析某个 Deployment 影响哪些 Service"]],
  ["k8s-cluster-summary", "生成集群摘要", "生成 K8s 集群的智能摘要报告，包含集群健康状态、资源统计、异常检测等信息", ["k8s", "cluster", "summary", "health", "集群", "摘要", "健康"], {}, ["生成当前集群健康摘要"]],
  ["k8s-sync-knowledge-graph", "同步知识图谱", "同步当前 Kubernetes 拓扑到本地知识图谱，生成资源节点和关系边", ["k8s", "knowledge graph", "topology", "知识图谱", "同步", "拓扑"], { namespace: "命名空间", all_namespaces: "是否同步全部命名空间" }, ["同步 default 命名空间资源拓扑到知识图谱"]],
  ["k8s-scale-deployment", "调整 Deployment 副本数", "调整 Kubernetes Deployment 的 replicas 副本数，需要 operator 权限和确认", ["k8s", "deployment", "scale", "replicas", "扩缩容", "副本"], { deployment_name: "Deployment 名称", replicas: "目标副本数", namespace: "命名空间" }, ["将 nginx Deployment 扩容到 3 个副本"]],
  ["k8s-restart-deployment", "滚动重启 Deployment", "通过更新 pod template annotation 触发 Deployment 滚动重启，需要 operator 权限和确认", ["k8s", "deployment", "restart", "rollout", "重启", "发布"], { deployment_name: "Deployment 名称", namespace: "命名空间" }, ["滚动重启 nginx Deployment"]],
  ["k8s-edit-resource", "编辑资源", "通过 JSON Patch/merge patch 编辑指定 K8s 资源，需要 operator 权限和确认", ["k8s", "edit", "patch", "修改", "更新", "资源"], { resource_type: "资源类型", name: "资源名称", namespace: "命名空间", patch: "Patch JSON 对象" }, ["给 Service 添加 annotation"]],
  ["k8s-patch-resource", "Patch 资源", "通过 JSON Patch/merge patch 修改指定 K8s 资源，需要 operator 权限和确认", ["k8s", "patch", "edit", "修改", "资源"], { resource_type: "资源类型", name: "资源名称", namespace: "命名空间", patch: "Patch JSON 对象" }, ["Patch Deployment 环境变量"]],
  ["k8s-delete-resource", "删除资源", "删除 Pod/Service/Deployment/ReplicaSet/Ingress/ConfigMap 等资源，需要 admin 权限和确认", ["k8s", "delete", "删除", "清理", "危险"], { resource_type: "资源类型", name: "资源名称", namespace: "命名空间" }, ["删除指定 Pod"]],
  ["k8s-exec-pod", "Pod Exec", "在 Pod 容器内执行命令，需要 admin 权限和确认", ["k8s", "exec", "pod", "container", "命令", "终端"], { pod_name: "Pod 名称", command: "命令", namespace: "命名空间", container: "容器名称", timeout_seconds: "超时时间" }, ["在 nginx Pod 中执行 ls /tmp"]],
  ["k8s-get-cluster-metrics", "获取集群指标", "获取 K8s 集群的 CPU 和内存使用情况，包括节点级别和集群整体的资源监控数据", ["k8s", "metrics", "cpu", "memory", "指标", "资源", "监控"], {}, ["查看集群 CPU 和内存使用率"]],
  ["k8s-resource-metrics-query", "查询资源指标", "从知识图谱查询 K8s 资源的指标字段，提供资源优化分析入口", ["k8s", "metrics", "resource", "cpu", "memory", "利用率", "优化", "知识图谱"], { resource_name: "资源名称", namespace: "命名空间", resource_type: "资源类型" }, ["查询某应用图谱指标字段"]],
  ["k8s-prometheus-app-metrics", "查询应用实时指标", "直接从 Prometheus 查询指定应用的实时 CPU 和内存利用率数据，提供准确的 14 天平均使用率/请求比例分析", ["k8s", "prometheus", "metrics", "app", "cpu", "memory", "实时指标"], { app_name: "应用名称", namespace: "命名空间" }, ["从 Prometheus 查询应用资源利用率"]],
  ["k8s-update-knowledge-graph-metrics", "更新知识图谱指标", "同步本地知识图谱拓扑，并为后续 Prometheus 指标接入保留指标占位", ["k8s", "knowledge graph", "metrics", "知识图谱", "更新", "批量"], { namespace: "命名空间", all_namespaces: "是否同步全部命名空间" }, ["更新知识图谱中的拓扑和指标占位"]],
  ["k8s-resource-monitor", "触发资源监控", "基于知识图谱触发 K8s 应用资源健康检查，返回缺口和风险项", ["k8s", "monitor", "alert", "resource", "告警", "监控", "资源", "知识图谱"], { app_name: "应用名称", namespace: "命名空间" }, ["触发应用资源健康检查"]],
  ["k8s-metrics-coverage-report", "生成指标覆盖报告", "生成知识图谱资源指标覆盖情况报告", ["k8s", "metrics", "coverage", "report", "指标覆盖", "报告", "知识图谱"], { namespace: "命名空间" }, ["生成图谱指标覆盖报告"]],
  ["k8s-resource-analysis-report", "生成资源分析报告", "分析知识图谱中的 K8s 资源数据，生成异常资源报告和优化建议，支持钉钉通知", ["k8s", "analysis", "report", "resource", "异常", "优化", "钉钉"], { namespace: "命名空间", notify_dingtalk: "是否通知钉钉" }, ["生成资源异常分析报告"]],
  ["ecs-describe-instance-monitor-data", "查询 ECS 实例监控", "查询 ECS 实例监控数据，自动 Period/分片聚合，返回 summary 与采样数据", ["ecs", "aliyun", "instance", "monitor", "cpu", "memory", "监控"], { instance_id: "ECS 实例 ID", metric_name: "指标名称", start_time: "开始时间", end_time: "结束时间" }, ["查询 ECS 实例 CPU 监控数据"]],
  ["ecs-list-instances", "列出 ECS 实例", "列出 ECS 实例，返回实例 ID 清单与少量元数据", ["ecs", "aliyun", "instance", "instances", "列表", "主机"], { page_size: "每页数量" }, ["列出当前地域 ECS 实例"]],
  ["ecs-inspect", "批量巡检 ECS 实例", "批量巡检 ECS 实例，生成风险摘要与报告", ["ecs", "aliyun", "inspect", "巡检", "风险", "报告"], { instance_ids: "逗号分隔的 ECS 实例 ID 列表" }, ["巡检指定 ECS 实例并生成风险摘要"]],
  ["aliyun-ecs-list-instances", "查询 ECS 实例列表", "按地域、状态、名称和标签查询 ECS 实例列表", ["aliyun", "ecs", "instance", "instances", "云服务器", "主机", "实例"], { region_id: "地域 ID", status: "实例状态", name: "实例名称关键词", tag_filters: "额外标签过滤", page_size: "最大返回数量" }, ["查询生产环境 ECS 实例列表"]],
  ["aliyun-ecs-describe-instance", "查询 ECS 实例详情", "查询单台 ECS 实例详情", ["aliyun", "ecs", "instance", "describe", "详情", "云服务器"], { instance_id: "ECS 实例 ID", region_id: "地域 ID" }, ["查询 i-xxx 实例详情"]],
  ["aliyun-ecs-list-security-groups", "查询 ECS 安全组", "查询 ECS 安全组列表", ["aliyun", "ecs", "security group", "安全组", "网络", "权限"], { region_id: "地域 ID", vpc_id: "VPC ID", instance_id: "ECS 实例 ID" }, ["查询实例关联安全组"]],
  ["aliyun-ecs-describe-security-group-rules", "查询 ECS 安全组规则", "查询安全组入方向或出方向规则", ["aliyun", "ecs", "security group", "rule", "安全组规则", "端口"], { security_group_id: "安全组 ID", region_id: "地域 ID", direction: "ingress 或 egress" }, ["查看安全组入方向规则"]],
  ["aliyun-cms-get-ecs-metrics", "查询 ECS 监控指标", "查询 ECS CPU、内存、磁盘、网络等监控指标", ["aliyun", "cms", "cloudmonitor", "metrics", "监控", "指标", "cpu", "内存"], { instance_id: "ECS 实例 ID", region_id: "地域 ID", metrics: "指标名列表", relative_range: "相对时间范围", period: "采样周期" }, ["查询 ECS 最近 1 小时 CPU 指标"]],
  ["aliyun-cms-get-alerts", "查询 CloudMonitor 告警", "查询 CloudMonitor 告警状态", ["aliyun", "cms", "cloudmonitor", "alert", "告警", "报警"], { region_id: "地域 ID", resource_id: "资源 ID", state: "告警状态", relative_range: "相对时间范围" }, ["查询 ECS 相关告警"]],
  ["aliyun-cms-get-event-history", "查询 CloudMonitor 事件", "查询 CloudMonitor 事件历史", ["aliyun", "cms", "cloudmonitor", "event", "事件", "云监控"], { region_id: "地域 ID", resource_id: "资源 ID", relative_range: "相对时间范围", event_type: "事件类型" }, ["查询最近云监控事件"]],
  ["aliyun-sls-list-logstores", "查询 SLS Logstore 映射", "列出已配置服务对应的 SLS project/logstore", ["aliyun", "sls", "logstore", "日志", "服务日志"], { service: "服务名", env: "环境", region_id: "地域 ID" }, ["列出 ding-robot 日志映射"]],
  ["aliyun-sls-query-logs", "查询 SLS 日志", "按服务映射查询 SLS 日志", ["aliyun", "sls", "logs", "日志", "错误日志", "exception", "error"], { service: "服务名", env: "环境", query: "查询语句", relative_range: "相对时间范围", limit: "最大行数" }, ["查询 ding-robot 最近 30 分钟错误日志"]],
  ["aliyun-sls-query-error-summary", "汇总 SLS 错误日志", "按服务映射查询并汇总错误日志", ["aliyun", "sls", "error", "summary", "错误", "异常", "日志摘要"], { service: "服务名", env: "环境", relative_range: "相对时间范围" }, ["汇总生产服务错误日志"]],
  ["aliyun-lb-list-instances", "查询负载均衡实例", "查询 SLB/ALB/NLB 实例列表", ["aliyun", "slb", "alb", "nlb", "load balancer", "负载均衡"], { region_id: "地域 ID", type: "slb/alb/nlb", name: "名称关键词", tag_filters: "额外标签过滤" }, ["查询负载均衡实例"]],
  ["aliyun-lb-describe-health", "查询负载均衡后端健康", "查询 SLB/ALB/NLB 监听和后端健康状态", ["aliyun", "slb", "alb", "nlb", "health", "健康检查", "后端"], { load_balancer_id: "负载均衡实例 ID", region_id: "地域 ID", type: "slb/alb/nlb" }, ["查询负载均衡后端健康状态"]],
  ["aliyun-swas-list-instances", "查询轻量应用服务器实例", "按地域、状态、名称和标签查询轻量应用服务器实例列表", ["aliyun", "swas", "simple application server", "轻量应用服务器", "轻量服务器"], { region_id: "地域 ID", status: "实例状态", name: "实例名称关键词", tag_filters: "额外标签过滤", page_size: "最大返回数量" }, ["查询轻量应用服务器实例"]],
];

function readSourceTools() {
  for (const path of [sourcePath, fallbackPath]) {
    try {
      const parsed = JSON.parse(readFileSync(path, "utf8"));
      if (Array.isArray(parsed.tools) && parsed.tools.length > 0) {
        return new Map(parsed.tools.map((tool) => [tool.name, tool]));
      }
    } catch {
      // Keep generation deterministic even when local runtime config is absent.
    }
  }
  return new Map();
}

function schemaFromProperties(name, properties) {
  const optional = optionalProperties.get(name) ?? new Set(["namespace", "label_selector", "tail_lines", "page_size", "notify_dingtalk", "container", "timeout_seconds", "all_namespaces"]);
  const required = Object.keys(properties).filter((key) => !optional.has(key));
  return {
    type: "object",
    properties: Object.fromEntries(
      Object.entries(properties).map(([name, description]) => [
        name,
        { type: name === "tail_lines" || name === "page_size" || name === "replicas" || name === "timeout_seconds" || name === "depth" ? "integer" : name === "notify_dingtalk" || name === "all_namespaces" || name === "include_data" ? "boolean" : name === "patch" || name === "tag_filters" ? "object" : "string", description },
      ]),
    ),
    required,
  };
}

function mergeInputSchema(sourceSchema, blueprintSchema) {
  if (!sourceSchema) {
    return blueprintSchema;
  }
  return {
    ...blueprintSchema,
    ...sourceSchema,
    properties: {
      ...(blueprintSchema.properties ?? {}),
      ...(sourceSchema.properties ?? {}),
    },
    required: sourceSchema.required ?? blueprintSchema.required,
  };
}

const sourceTools = readSourceTools();
const tools = blueprint.map(([name, title, description, tags, properties, examples]) => {
  const source = sourceTools.get(name) ?? {};
  const category = source.category ?? (name.startsWith("aliyun-") ? "aliyun" : name.startsWith("ecs-") ? "ecs" : "kubernetes");
  const executionPolicy = executableBuiltins.has(name) ? "executable" : "catalog_only";
  const blueprintSchema = schemaFromProperties(name, properties);
  const sourceSchema = source.inputSchema ?? (name === "ecs-describe-instance-monitor-data" ? source.input_schema : undefined);
  return {
    name,
    title,
    category,
    description: source.description ?? description,
    tags,
    dangerLevel: dangerLevels.get(name) ?? "read",
    server: executionPolicy === "executable" ? "builtin" : "catalog",
    executionPolicy,
    inputSchema: mergeInputSchema(sourceSchema, blueprintSchema),
    examples,
    source: {
      catalog: sourceTools.has(name) ? "config/mcp_config.json" : "blueprint",
      builtin: executableBuiltins.has(name),
    },
  };
});

const catalog = {
  version: "1.0.0",
  generatedAt: new Date().toISOString(),
  source: ["config/mcp_config.json", "backend-v2/app/mcp/builtin.py", "mcp-servers/toolsearch/scripts/generate-catalog.mjs"],
  tools,
};

writeFileSync(outputPath, `${JSON.stringify(catalog, null, 2)}\n`, "utf8");
console.error(`Generated ${tools.length} tools at ${outputPath}`);
