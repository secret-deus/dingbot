"""内置工具注册 - K8s & ECS 进程内工具（无需单独 MCP 服务器）"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.config import get_settings
from app.mcp.tools.k8s import K8sClient
from app.mcp.tools.ecs import ECSClient


class BuiltinToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Any] = {}
        self._tool_defs: list[dict] = []
        self._k8s: K8sClient | None = None
        self._ecs: ECSClient | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        settings = get_settings()

        if settings.k8s_mcp_enabled:
            self._k8s = K8sClient(
                kubeconfig_path=settings.kubeconfig_path,
                in_cluster=settings.k8s_in_cluster,
                default_namespace=settings.k8s_namespace,
            )
            self._register_k8s_tools()

        ecs_enabled = bool(settings.ecs_mcp_enabled or settings.alibaba_access_key_id)
        if ecs_enabled:
            self._ecs = ECSClient(
                access_key_id=settings.alibaba_access_key_id or "",
                access_key_secret=settings.alibaba_access_key_secret or "",
                region_id=settings.alibaba_region_id,
            )
            self._register_ecs_tools(
                available=bool(
                    settings.alibaba_access_key_id and settings.alibaba_access_key_secret
                ),
                unavailable_reason="未配置 ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET",
            )

    def _register_k8s_tools(self) -> None:
        available = bool(self._k8s and self._k8s.is_configured())
        unavailable_reason = (
            ""
            if available
            else (self._k8s.unavailable_reason() if self._k8s else "K8s 客户端未初始化")
        )
        k8s_tools = [
            {
                "name": "k8s-get-pods",
                "description": "获取 Pod 列表，namespace=all 或 all_namespaces=true 查询全部命名空间",
                "schema": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间；传 all 查询全部命名空间",
                    },
                    "all_namespaces": {"type": "boolean", "description": "是否查询全部命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-services",
                "description": "获取 Service 列表或单个 Service",
                "schema": {
                    "service_name": {"type": "string", "description": "Service 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-describe-service",
                "description": "描述 Service 详情",
                "schema": {
                    "service_name": {"type": "string", "description": "Service 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["service_name"],
            },
            {
                "name": "k8s-get-endpoints",
                "description": "获取 Service 端点",
                "schema": {
                    "service_name": {"type": "string", "description": "Service 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-deployments",
                "description": "获取 Deployment 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-replicasets",
                "description": "获取 ReplicaSet 列表",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-ingresses",
                "description": "获取 Ingress 列表或单个 Ingress",
                "schema": {
                    "ingress_name": {"type": "string", "description": "Ingress 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-describe-ingress",
                "description": "描述 Ingress 详情",
                "schema": {
                    "ingress_name": {"type": "string", "description": "Ingress 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["ingress_name"],
            },
            {
                "name": "k8s-get-nodes",
                "description": "获取 Node 列表",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-get-logs",
                "description": "获取 Pod 日志",
                "schema": {
                    "pod_name": {"type": "string", "description": "Pod名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "tail_lines": {"type": "integer", "description": "行数"},
                },
                "required": ["pod_name"],
            },
            {
                "name": "k8s-describe-pod",
                "description": "描述 Pod 详情",
                "schema": {
                    "pod_name": {"type": "string", "description": "Pod名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["pod_name"],
            },
            {
                "name": "k8s-get-events",
                "description": "获取事件列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-deployment-history",
                "description": "获取 Deployment 版本历史",
                "schema": {
                    "deployment_name": {"type": "string", "description": "Deployment 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["deployment_name"],
            },
            {
                "name": "k8s-rollout-status",
                "description": "查看 Deployment/StatefulSet/DaemonSet 发布状态",
                "schema": {
                    "workload_type": {
                        "type": "string",
                        "description": "资源类型: deployment/statefulset/daemonset",
                    },
                    "name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["name"],
            },
            {
                "name": "k8s-get-statefulsets",
                "description": "获取 StatefulSet 列表",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-daemonsets",
                "description": "获取 DaemonSet 列表",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-jobs",
                "description": "获取 Job 列表",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-cronjobs",
                "description": "获取 CronJob 列表",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "label_selector": {"type": "string", "description": "标签选择器"},
                },
                "required": [],
            },
            {
                "name": "k8s-get-hpas",
                "description": "获取 HPA 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-networkpolicies",
                "description": "获取 NetworkPolicy 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-namespaces",
                "description": "获取 Namespace 列表",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-get-configmaps",
                "description": "获取 ConfigMap 列表或单个 ConfigMap",
                "schema": {
                    "configmap_name": {"type": "string", "description": "ConfigMap 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "include_data": {"type": "boolean", "description": "是否返回 data 内容"},
                },
                "required": [],
            },
            {
                "name": "k8s-describe-configmap",
                "description": "描述 ConfigMap 详情",
                "schema": {
                    "configmap_name": {"type": "string", "description": "ConfigMap 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "include_data": {"type": "boolean", "description": "是否返回 data 内容"},
                },
                "required": ["configmap_name"],
            },
            {
                "name": "k8s-get-secrets",
                "description": "获取 Secret 列表或单个 Secret 元数据(值脱敏)",
                "schema": {
                    "secret_name": {"type": "string", "description": "Secret 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-describe-secret",
                "description": "描述 Secret 元数据和值键名(值脱敏)",
                "schema": {
                    "secret_name": {"type": "string", "description": "Secret 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["secret_name"],
            },
            {
                "name": "k8s-get-serviceaccounts",
                "description": "获取 ServiceAccount 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-pvcs",
                "description": "获取 PVC 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {"name": "k8s-get-pvs", "description": "获取 PV 列表", "schema": {}, "required": []},
            {
                "name": "k8s-get-storageclasses",
                "description": "获取 StorageClass 列表",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-get-resourcequotas",
                "description": "获取 ResourceQuota 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-limitranges",
                "description": "获取 LimitRange 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-roles",
                "description": "获取 Role 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-rolebindings",
                "description": "获取 RoleBinding 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-clusterroles",
                "description": "获取 ClusterRole 列表",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-get-clusterrolebindings",
                "description": "获取 ClusterRoleBinding 列表",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-get-pod-disruption-budgets",
                "description": "获取 PodDisruptionBudget 列表",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-get-cluster-metrics",
                "description": "获取 metrics.k8s.io 集群指标",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-prometheus-app-metrics",
                "description": "查询 Prometheus 应用指标",
                "schema": {
                    "app_name": {"type": "string", "description": "应用名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["app_name"],
            },
            {
                "name": "k8s-cluster-summary",
                "description": "集群概览",
                "schema": {},
                "required": [],
            },
            {
                "name": "k8s-sync-knowledge-graph",
                "description": "同步 K8s 拓扑到本地知识图谱",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "all_namespaces": {"type": "boolean", "description": "是否同步全部命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-relation-query",
                "description": "查询资源关系图谱",
                "schema": {
                    "resource_type": {"type": "string", "description": "资源类型"},
                    "resource_name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "depth": {"type": "integer", "description": "关系深度"},
                },
                "required": ["resource_type", "resource_name"],
            },
            {
                "name": "k8s-resource-metrics-query",
                "description": "查询图谱中的资源指标",
                "schema": {
                    "resource_type": {"type": "string", "description": "资源类型"},
                    "resource_name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["resource_name"],
            },
            {
                "name": "k8s-update-knowledge-graph-metrics",
                "description": "更新本地知识图谱拓扑和指标占位",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "all_namespaces": {"type": "boolean", "description": "是否同步全部命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-resource-monitor",
                "description": "基于知识图谱执行资源健康检查",
                "schema": {
                    "app_name": {"type": "string", "description": "应用名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": [],
            },
            {
                "name": "k8s-metrics-coverage-report",
                "description": "生成知识图谱指标覆盖报告",
                "schema": {"namespace": {"type": "string", "description": "命名空间"}},
                "required": [],
            },
            {
                "name": "k8s-resource-analysis-report",
                "description": "基于知识图谱生成资源分析报告",
                "schema": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "notify_dingtalk": {"type": "boolean", "description": "是否通知钉钉"},
                },
                "required": [],
            },
            {
                "name": "k8s-scale-deployment",
                "description": "调整 Deployment 副本数",
                "schema": {
                    "deployment_name": {"type": "string", "description": "Deployment 名称"},
                    "replicas": {"type": "integer", "description": "目标副本数"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["deployment_name", "replicas"],
                "dangerLevel": "write",
            },
            {
                "name": "k8s-restart-deployment",
                "description": "滚动重启 Deployment",
                "schema": {
                    "deployment_name": {"type": "string", "description": "Deployment 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["deployment_name"],
                "dangerLevel": "write",
            },
            {
                "name": "k8s-edit-resource",
                "description": "编辑资源(JSON patch/merge patch)",
                "schema": {
                    "resource_type": {
                        "type": "string",
                        "description": "资源类型: pod/service/deployment/replicaset/ingress/configmap/secret/statefulset/daemonset/job/cronjob/hpa/pvc/networkpolicy/pdb",
                    },
                    "name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "patch": {"type": "object", "description": "Patch JSON 对象"},
                },
                "required": ["resource_type", "name", "patch"],
                "dangerLevel": "write",
            },
            {
                "name": "k8s-patch-resource",
                "description": "Patch 资源(JSON patch/merge patch)",
                "schema": {
                    "resource_type": {
                        "type": "string",
                        "description": "资源类型: pod/service/deployment/replicaset/ingress/configmap/secret/statefulset/daemonset/job/cronjob/hpa/pvc/networkpolicy/pdb",
                    },
                    "name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "patch": {"type": "object", "description": "Patch JSON 对象"},
                },
                "required": ["resource_type", "name", "patch"],
                "dangerLevel": "write",
            },
            {
                "name": "k8s-delete-resource",
                "description": "删除资源",
                "schema": {
                    "resource_type": {
                        "type": "string",
                        "description": "资源类型: pod/service/deployment/replicaset/ingress/configmap/secret/statefulset/daemonset/job/cronjob/hpa/pvc/networkpolicy/pdb",
                    },
                    "name": {"type": "string", "description": "资源名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                },
                "required": ["resource_type", "name"],
                "dangerLevel": "dangerous",
            },
            {
                "name": "k8s-exec-pod",
                "description": "在 Pod 容器内执行命令",
                "schema": {
                    "pod_name": {"type": "string", "description": "Pod 名称"},
                    "namespace": {"type": "string", "description": "命名空间"},
                    "container": {"type": "string", "description": "容器名称"},
                    "command": {"type": "string", "description": "要执行的命令"},
                    "timeout_seconds": {"type": "integer", "description": "超时时间"},
                },
                "required": ["pod_name", "command"],
                "dangerLevel": "dangerous",
            },
        ]
        for tool in k8s_tools:
            name = tool["name"]
            schema = tool["schema"]
            tool_def = {
                "name": name,
                "description": tool["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": schema,
                    "required": tool["required"],
                },
                "server": "builtin",
                "available": available,
                "dangerLevel": tool.get("dangerLevel", "read"),
            }
            if not available:
                tool_def["unavailableReason"] = unavailable_reason
            self._tool_defs.append(tool_def)
            self._handlers[name] = self._k8s

    def _register_ecs_tools(self, available: bool, unavailable_reason: str = "") -> None:
        ecs_tools = [
            (
                "ecs-list-instances",
                "获取 ECS 实例列表",
                {"page_size": {"type": "integer", "description": "每页数量"}},
            ),
            (
                "ecs-describe-instance",
                "查询实例详情",
                {"instance_id": {"type": "string", "description": "实例ID"}},
            ),
            (
                "ecs-describe-instance-monitor-data",
                "查询 ECS 实例监控",
                {
                    "instance_id": {"type": "string", "description": "ECS 实例 ID"},
                    "region_id": {
                        "type": "string",
                        "description": "地域 ID，默认使用内置 ECS 配置",
                    },
                    "start_time": {"type": "string", "description": "ISO8601 UTC 开始时间"},
                    "end_time": {
                        "type": "string",
                        "description": "ISO8601 UTC 结束时间，默认当前 UTC",
                    },
                    "relative_range": {
                        "type": "string",
                        "description": "相对时间范围: 1h/6h/24h/7d/30d",
                    },
                    "period": {"type": "integer", "description": "采样周期，支持 60/600/3600 秒"},
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要返回的指标字段",
                    },
                    "max_points": {"type": "integer", "description": "最大采样点数，默认 400"},
                },
            ),
            (
                "ecs-inspect",
                "ECS 巡检",
                {"instance_ids": {"type": "string", "description": "实例ID列表(逗号分隔)"}},
            ),
        ]
        for name, desc, schema in ecs_tools:
            required = [k for k in schema if k == "instance_id"]
            tool_def = {
                "name": name,
                "description": desc,
                "inputSchema": {"type": "object", "properties": schema, "required": required},
                "server": "builtin",
                "available": available,
            }
            if not available:
                tool_def["unavailableReason"] = unavailable_reason
            self._tool_defs.append(tool_def)
            self._handlers[name] = self._ecs

    def list_tools(self) -> list[dict]:
        self._ensure_initialized()
        return list(self._tool_defs)

    async def call(self, name: str, arguments: dict) -> dict:
        self._ensure_initialized()
        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"内置工具 {name} 不存在"}

        tool_def = next((tool for tool in self._tool_defs if tool.get("name") == name), None)
        if tool_def and not tool_def.get("available", True):
            return {
                "error": "tool_unavailable",
                "reason": self._unavailable_reason_code(name),
                "message": tool_def.get("unavailableReason") or f"工具 {name} 当前不可用",
                "tool": name,
            }

        try:
            method_name = name.replace("-", "_")
            method = getattr(handler, method_name, None)
            if method is None:
                return {"error": f"工具方法 {method_name} 未实现"}
            result = await method(**arguments)
            return {"result": result}
        except Exception as e:
            logger.error("内置工具 {} 执行失败: {}", name, e)
            return {"error": str(e)}

    @staticmethod
    def _unavailable_reason_code(name: str) -> str:
        if name.startswith("k8s-"):
            return "kubeconfig_not_configured"
        if name.startswith("ecs-"):
            return "ecs_credentials_not_configured"
        return "tool_not_configured"
