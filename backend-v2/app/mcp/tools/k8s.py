"""K8s 客户端 - 封装 kubernetes python client 的核心操作"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings
from app.mcp.tools.knowledge_graph import (
    FileKnowledgeGraphStore,
    graph_node_id,
    normalize_graph_kind,
)


class K8sClient:
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        in_cluster: bool = False,
        default_namespace: str = "default",
    ) -> None:
        self.kubeconfig_path = kubeconfig_path or None
        self.in_cluster = in_cluster
        self.default_namespace = default_namespace
        self._v1: Any = None
        self._apps_v1: Any = None
        self._networking_v1: Any = None
        self._batch_v1: Any = None
        self._autoscaling_v2: Any = None
        self._rbac_v1: Any = None
        self._storage_v1: Any = None
        self._policy_v1: Any = None
        self._custom_objects: Any = None
        self._config_loaded = False
        self._availability_error = ""

    def is_configured(self) -> bool:
        if not self.in_cluster:
            config_path = (
                Path(self.kubeconfig_path).expanduser()
                if self.kubeconfig_path
                else Path.home() / ".kube" / "config"
            )
            if not config_path.exists():
                self._availability_error = f"kubeconfig 文件不存在: {config_path}"
                return False

        try:
            from kubernetes import client, config

            if self.in_cluster:
                config.load_incluster_config()
            elif self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                config.load_kube_config()
            client.CoreV1Api().list_node(limit=1, _request_timeout=2)
            self._config_loaded = True
            self._availability_error = ""
            return True
        except Exception as exc:
            self._availability_error = f"Kubernetes API 不可用: {exc}"
            return False

    def unavailable_reason(self) -> str:
        if self._config_loaded:
            return ""
        if self._availability_error:
            return self._availability_error
        if self.in_cluster:
            return ""
        if self.kubeconfig_path:
            return f"kubeconfig 文件不存在: {self.kubeconfig_path}"
        return "未找到 kubeconfig。请设置 KUBECONFIG_PATH 或创建 ~/.kube/config。"

    def _get_v1(self) -> Any:
        if self._v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._v1 = client.CoreV1Api()
        return self._v1

    def _get_apps_v1(self) -> Any:
        if self._apps_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._apps_v1 = client.AppsV1Api()
        return self._apps_v1

    def _get_networking_v1(self) -> Any:
        if self._networking_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._networking_v1 = client.NetworkingV1Api()
        return self._networking_v1

    def _get_batch_v1(self) -> Any:
        if self._batch_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._batch_v1 = client.BatchV1Api()
        return self._batch_v1

    def _get_autoscaling_v2(self) -> Any:
        if self._autoscaling_v2 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._autoscaling_v2 = client.AutoscalingV2Api()
        return self._autoscaling_v2

    def _get_rbac_v1(self) -> Any:
        if self._rbac_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._rbac_v1 = client.RbacAuthorizationV1Api()
        return self._rbac_v1

    def _get_storage_v1(self) -> Any:
        if self._storage_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._storage_v1 = client.StorageV1Api()
        return self._storage_v1

    def _get_policy_v1(self) -> Any:
        if self._policy_v1 is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._policy_v1 = client.PolicyV1Api()
        return self._policy_v1

    def _get_custom_objects(self) -> Any:
        if self._custom_objects is None:
            from kubernetes import client

            self._ensure_config_loaded()
            self._custom_objects = client.CustomObjectsApi()
        return self._custom_objects

    def _ensure_config_loaded(self) -> None:
        if self._config_loaded:
            return
        from kubernetes import config

        if self.in_cluster:
            config.load_incluster_config()
        elif self.kubeconfig_path:
            config.load_kube_config(config_file=self.kubeconfig_path)
        else:
            config.load_kube_config()
        self._config_loaded = True

    def _ns(self, kwargs: dict) -> str:
        return kwargs.get("namespace", self.default_namespace)

    @staticmethod
    def _all_namespaces(kwargs: dict) -> bool:
        namespace = str(kwargs.get("namespace") or "").strip().lower()
        return K8sClient._as_bool(kwargs.get("all_namespaces"), default=False) or namespace in {
            "all",
            "*",
            "_all",
            "all-namespaces",
            "all_namespaces",
        }

    async def k8s_get_pods(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        label_selector = kwargs.get("label_selector", "")
        if self._all_namespaces(kwargs):
            pods = v1.list_pod_for_all_namespaces(label_selector=label_selector, limit=500)
        else:
            ns = self._ns(kwargs)
            pods = v1.list_namespaced_pod(namespace=ns, label_selector=label_selector, limit=100)
        items = []
        for p in pods.items:
            items.append(
                {
                    "name": p.metadata.name,
                    "namespace": p.metadata.namespace,
                    "status": p.status.phase,
                    "node": p.spec.node_name,
                    "restarts": sum(cs.restart_count for cs in (p.status.container_statuses or [])),
                    "age": str(p.metadata.creation_timestamp),
                }
            )
        return {"count": len(items), "items": items}

    async def k8s_get_services(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        service_name = kwargs.get("service_name") or kwargs.get("name") or ""
        if service_name:
            svcs = [v1.read_namespaced_service(name=service_name, namespace=ns)]
        else:
            svcs = v1.list_namespaced_service(namespace=ns, limit=100).items
        items = [self._format_service(s) for s in svcs]
        return {"count": len(items), "items": items}

    async def k8s_describe_service(self, **kwargs: Any) -> dict:
        service_name = kwargs.get("service_name") or kwargs.get("name") or ""
        if not service_name:
            return {"error": "service_name 参数必填"}
        result = await self.k8s_get_services(**kwargs)
        return result["items"][0]

    async def k8s_get_endpoints(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        service_name = kwargs.get("service_name") or kwargs.get("name") or ""
        label_selector = kwargs.get("label_selector", "")

        if service_name:
            endpoints = [v1.read_namespaced_endpoints(name=service_name, namespace=ns)]
        else:
            endpoints = v1.list_namespaced_endpoints(
                namespace=ns,
                label_selector=label_selector,
                limit=100,
            ).items

        items = []
        for endpoint in endpoints:
            subsets = []
            for subset in endpoint.subsets or []:
                subsets.append(
                    {
                        "addresses": [
                            self._format_endpoint_address(addr) for addr in (subset.addresses or [])
                        ],
                        "not_ready_addresses": [
                            self._format_endpoint_address(addr)
                            for addr in (subset.not_ready_addresses or [])
                        ],
                        "ports": [
                            {"name": port.name, "port": port.port, "protocol": port.protocol}
                            for port in (subset.ports or [])
                        ],
                    }
                )
            items.append(
                {
                    "name": endpoint.metadata.name,
                    "namespace": endpoint.metadata.namespace,
                    "subsets": subsets,
                }
            )
        return {"count": len(items), "items": items}

    async def k8s_get_deployments(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        deps = apps.list_namespaced_deployment(namespace=ns, limit=100)
        items = [
            {
                "name": d.metadata.name,
                "replicas": d.spec.replicas,
                "available": d.status.available_replicas or 0,
                "image": (
                    d.spec.template.spec.containers[0].image
                    if d.spec.template.spec.containers
                    else ""
                ),
            }
            for d in deps.items
        ]
        return {"count": len(items), "items": items}

    async def k8s_get_deployment_history(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        deployment_name = kwargs.get("deployment_name") or kwargs.get("name") or ""
        if not deployment_name:
            return {"error": "deployment_name 参数必填"}

        deployment = apps.read_namespaced_deployment(name=deployment_name, namespace=ns)
        selector = self._label_selector_from_match_labels(
            getattr(
                getattr(getattr(deployment, "spec", None), "selector", None), "match_labels", None
            )
        )
        replica_sets = apps.list_namespaced_replica_set(
            namespace=ns, label_selector=selector, limit=200
        ).items
        items = []
        for replica_set in replica_sets:
            metadata = getattr(replica_set, "metadata", None)
            owners = self._format_owner_refs(getattr(metadata, "owner_references", None) or [])
            if not any(
                owner.get("kind") == "Deployment" and owner.get("name") == deployment_name
                for owner in owners
            ):
                continue
            annotations = getattr(metadata, "annotations", None) or {}
            items.append(
                {
                    "revision": self._as_int(
                        annotations.get("deployment.kubernetes.io/revision"), default=0
                    ),
                    "replicaset": getattr(metadata, "name", None),
                    "namespace": getattr(metadata, "namespace", None),
                    "change_cause": annotations.get("kubernetes.io/change-cause", ""),
                    "desired": getattr(getattr(replica_set, "spec", None), "replicas", None) or 0,
                    "ready": getattr(getattr(replica_set, "status", None), "ready_replicas", None)
                    or 0,
                    "available": getattr(
                        getattr(replica_set, "status", None), "available_replicas", None
                    )
                    or 0,
                    "images": self._pod_template_images(
                        getattr(getattr(replica_set, "spec", None), "template", None)
                    ),
                    "created_at": self._stringify_time(
                        getattr(metadata, "creation_timestamp", None)
                    ),
                }
            )

        items.sort(key=lambda item: item.get("revision") or 0)
        deployment_annotations = (
            getattr(getattr(deployment, "metadata", None), "annotations", None) or {}
        )
        return {
            "deployment": deployment_name,
            "namespace": ns,
            "selector": selector,
            "current_revision": self._as_int(
                deployment_annotations.get("deployment.kubernetes.io/revision"), default=0
            ),
            "count": len(items),
            "items": items,
        }

    async def k8s_rollout_status(self, **kwargs: Any) -> dict:
        workload_type = self._normalize_resource_type(
            kwargs.get("workload_type") or kwargs.get("resource_type") or "deployment"
        )
        name = (
            kwargs.get("name") or kwargs.get("deployment_name") or kwargs.get("workload_name") or ""
        )
        ns = self._ns(kwargs)
        if not name:
            return {"error": "name 参数必填"}
        if workload_type == "deployment":
            obj = self._get_apps_v1().read_namespaced_deployment(name=name, namespace=ns)
            return self._deployment_rollout_status(obj)
        if workload_type == "statefulset":
            obj = self._get_apps_v1().read_namespaced_stateful_set(name=name, namespace=ns)
            return self._statefulset_rollout_status(obj)
        if workload_type == "daemonset":
            obj = self._get_apps_v1().read_namespaced_daemon_set(name=name, namespace=ns)
            return self._daemonset_rollout_status(obj)
        return {"error": f"暂不支持 rollout status 资源类型: {workload_type}"}

    async def k8s_get_statefulsets(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        result = apps.list_namespaced_stateful_set(
            namespace=ns, label_selector=label_selector, limit=100
        )
        items = [self._format_statefulset(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_daemonsets(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        result = apps.list_namespaced_daemon_set(
            namespace=ns, label_selector=label_selector, limit=100
        )
        items = [self._format_daemonset(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_jobs(self, **kwargs: Any) -> dict:
        batch = self._get_batch_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        result = batch.list_namespaced_job(namespace=ns, label_selector=label_selector, limit=100)
        items = [self._format_job(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_cronjobs(self, **kwargs: Any) -> dict:
        batch = self._get_batch_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        result = batch.list_namespaced_cron_job(
            namespace=ns, label_selector=label_selector, limit=100
        )
        items = [self._format_cronjob(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_hpas(self, **kwargs: Any) -> dict:
        autoscaling = self._get_autoscaling_v2()
        ns = self._ns(kwargs)
        result = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace=ns, limit=100)
        items = [self._format_hpa(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_replicasets(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        replica_sets = apps.list_namespaced_replica_set(
            namespace=ns,
            label_selector=label_selector,
            limit=100,
        )
        items = [self._format_replicaset(rs) for rs in replica_sets.items]
        return {"count": len(items), "items": items}

    async def k8s_get_ingresses(self, **kwargs: Any) -> dict:
        networking = self._get_networking_v1()
        ns = self._ns(kwargs)
        ingress_name = kwargs.get("ingress_name") or kwargs.get("name") or ""
        if ingress_name:
            ingresses = [networking.read_namespaced_ingress(name=ingress_name, namespace=ns)]
        else:
            ingresses = networking.list_namespaced_ingress(namespace=ns, limit=100).items
        items = [self._format_ingress(ingress) for ingress in ingresses]
        return {"count": len(items), "items": items}

    async def k8s_describe_ingress(self, **kwargs: Any) -> dict:
        ingress_name = kwargs.get("ingress_name") or kwargs.get("name") or ""
        if not ingress_name:
            return {"error": "ingress_name 参数必填"}
        result = await self.k8s_get_ingresses(**kwargs)
        return result["items"][0]

    async def k8s_get_networkpolicies(self, **kwargs: Any) -> dict:
        networking = self._get_networking_v1()
        ns = self._ns(kwargs)
        result = networking.list_namespaced_network_policy(namespace=ns, limit=100)
        items = [self._format_network_policy(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_nodes(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        nodes = v1.list_node(limit=100)
        items = [
            {
                "name": n.metadata.name,
                "status": n.status.conditions[-1].type if n.status.conditions else "Unknown",
                "roles": [
                    k.replace("node-role.kubernetes.io/", "")
                    for k in (n.metadata.labels or {})
                    if k.startswith("node-role")
                ],
                "version": n.status.node_info.kubelet_version if n.status.node_info else "",
            }
            for n in nodes.items
        ]
        return {"count": len(items), "items": items}

    async def k8s_get_namespaces(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        result = v1.list_namespace(limit=100)
        items = [self._format_namespace(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_configmaps(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        name = kwargs.get("configmap_name") or kwargs.get("name") or ""
        include_data = self._as_bool(kwargs.get("include_data"), default=False)
        if name:
            configmaps = [v1.read_namespaced_config_map(name=name, namespace=ns)]
        else:
            configmaps = v1.list_namespaced_config_map(namespace=ns, limit=100).items
        items = [self._format_configmap(item, include_data=include_data) for item in configmaps]
        return {"count": len(items), "items": items}

    async def k8s_describe_configmap(self, **kwargs: Any) -> dict:
        name = kwargs.get("configmap_name") or kwargs.get("name") or ""
        if not name:
            return {"error": "configmap_name 参数必填"}
        result = await self.k8s_get_configmaps(**kwargs)
        return result["items"][0]

    async def k8s_get_secrets(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        name = kwargs.get("secret_name") or kwargs.get("name") or ""
        if name:
            secrets = [v1.read_namespaced_secret(name=name, namespace=ns)]
        else:
            secrets = v1.list_namespaced_secret(namespace=ns, limit=100).items
        items = [self._format_secret(item) for item in secrets]
        return {"count": len(items), "items": items}

    async def k8s_describe_secret(self, **kwargs: Any) -> dict:
        name = kwargs.get("secret_name") or kwargs.get("name") or ""
        if not name:
            return {"error": "secret_name 参数必填"}
        result = await self.k8s_get_secrets(**kwargs)
        return result["items"][0]

    async def k8s_get_serviceaccounts(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        result = v1.list_namespaced_service_account(namespace=ns, limit=100)
        items = [self._format_service_account(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_pvcs(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        result = v1.list_namespaced_persistent_volume_claim(namespace=ns, limit=100)
        items = [self._format_pvc(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_pvs(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        result = v1.list_persistent_volume(limit=100)
        items = [self._format_pv(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_resourcequotas(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        result = v1.list_namespaced_resource_quota(namespace=ns, limit=100)
        items = [self._format_resource_quota(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_limitranges(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        result = v1.list_namespaced_limit_range(namespace=ns, limit=100)
        items = [self._format_limit_range(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_storageclasses(self, **kwargs: Any) -> dict:
        storage = self._get_storage_v1()
        result = storage.list_storage_class(limit=100)
        items = [self._format_storage_class(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_roles(self, **kwargs: Any) -> dict:
        rbac = self._get_rbac_v1()
        ns = self._ns(kwargs)
        result = rbac.list_namespaced_role(namespace=ns, limit=100)
        items = [self._format_role(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_rolebindings(self, **kwargs: Any) -> dict:
        rbac = self._get_rbac_v1()
        ns = self._ns(kwargs)
        result = rbac.list_namespaced_role_binding(namespace=ns, limit=100)
        items = [self._format_role_binding(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_clusterroles(self, **kwargs: Any) -> dict:
        rbac = self._get_rbac_v1()
        result = rbac.list_cluster_role(limit=100)
        items = [self._format_role(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_clusterrolebindings(self, **kwargs: Any) -> dict:
        rbac = self._get_rbac_v1()
        result = rbac.list_cluster_role_binding(limit=100)
        items = [self._format_role_binding(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_pod_disruption_budgets(self, **kwargs: Any) -> dict:
        policy = self._get_policy_v1()
        ns = self._ns(kwargs)
        result = policy.list_namespaced_pod_disruption_budget(namespace=ns, limit=100)
        items = [self._format_pdb(item) for item in result.items]
        return {"count": len(items), "items": items}

    async def k8s_get_logs(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        pod_name = kwargs.get("pod_name", "")
        tail = kwargs.get("tail_lines", 100)
        if not pod_name:
            return {"error": "pod_name 参数必填"}
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=ns, tail_lines=tail)
        return {"pod": pod_name, "namespace": ns, "logs": logs}

    async def k8s_exec_pod(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        pod_name = kwargs.get("pod_name", "")
        command = self._parse_command(kwargs.get("command"))
        container = kwargs.get("container") or None
        timeout = kwargs.get("timeout_seconds", 30)
        if not pod_name:
            return {"error": "pod_name 参数必填"}
        if not command:
            return {"error": "command 参数必填"}
        output = self._stream_pod_exec(v1, pod_name, ns, command, container, timeout)
        return {
            "pod": pod_name,
            "namespace": ns,
            "container": container,
            "command": command,
            "output": output,
        }

    async def k8s_describe_pod(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        pod_name = kwargs.get("pod_name", "")
        if not pod_name:
            return {"error": "pod_name 参数必填"}
        pod = v1.read_namespaced_pod(name=pod_name, namespace=ns)
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "containers": [{"name": c.name, "image": c.image} for c in pod.spec.containers],
            "events": str(pod.metadata.creation_timestamp),
        }

    async def k8s_get_events(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        events = v1.list_namespaced_event(namespace=ns, limit=50)
        items = [self._format_event(e) for e in events.items]
        return {"count": len(items), "items": items}

    async def k8s_get_cluster_metrics(self, **kwargs: Any) -> dict:
        metrics = self._get_custom_objects()
        try:
            node_metrics = metrics.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
            )
            pod_metrics = metrics.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods",
            )
        except Exception as exc:
            return {
                "error": "metrics_api_unavailable",
                "message": f"metrics.k8s.io API 不可用: {exc}",
                "hint": "请确认 metrics-server 已安装并可通过 kubectl top nodes/pods 查询。",
            }

        nodes = [self._format_node_metric(item) for item in node_metrics.get("items", [])]
        pods = [self._format_pod_metric(item) for item in pod_metrics.get("items", [])]
        total_cpu_mcores = sum(item["cpu_mcores"] for item in nodes)
        total_memory_bytes = sum(item["memory_bytes"] for item in nodes)
        return {
            "source": "metrics.k8s.io",
            "node_count": len(nodes),
            "pod_count": len(pods),
            "total_cpu_mcores": total_cpu_mcores,
            "total_memory_bytes": total_memory_bytes,
            "total_memory_mib": round(total_memory_bytes / 1024 / 1024, 2),
            "nodes": nodes,
            "top_pods_by_cpu": sorted(pods, key=lambda item: item["cpu_mcores"], reverse=True)[:10],
            "top_pods_by_memory": sorted(pods, key=lambda item: item["memory_bytes"], reverse=True)[
                :10
            ],
        }

    async def k8s_prometheus_app_metrics(self, **kwargs: Any) -> dict:
        settings = get_settings()
        prometheus_url = str(getattr(settings, "prometheus_base_url", "") or "").strip().rstrip("/")
        app_name = (
            kwargs.get("app_name") or kwargs.get("deployment_name") or kwargs.get("name") or ""
        )
        namespace = kwargs.get("namespace") or self.default_namespace
        if not app_name:
            return {"error": "app_name 参数必填"}
        if not prometheus_url:
            return {
                "error": "prometheus_not_configured",
                "message": "未配置 PROMETHEUS_BASE_URL，无法直接查询 Prometheus。",
            }

        pod_name_regex = self._promql_string(f"{re.escape(app_name)}.*")
        namespace_value = self._promql_string(namespace)
        queries = {
            "cpu_5m_cores_by_pod": (
                "sum by (pod) (rate(container_cpu_usage_seconds_total{"
                f'namespace="{namespace_value}",pod=~"{pod_name_regex}",container!="",image!=""'
                "}[5m]))"
            ),
            "memory_working_set_bytes_by_pod": (
                "sum by (pod) (container_memory_working_set_bytes{"
                f'namespace="{namespace_value}",pod=~"{pod_name_regex}",container!="",image!=""'
                "})"
            ),
            "restart_increase_1h_by_pod": (
                "sum by (pod) (increase(kube_pod_container_status_restarts_total{"
                f'namespace="{namespace_value}",pod=~"{pod_name_regex}"'
                "}[1h]))"
            ),
        }
        results: dict[str, Any] = {}
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                for key, query in queries.items():
                    response = await client.get(
                        f"{prometheus_url}/api/v1/query", params={"query": query}
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if payload.get("status") != "success":
                        return {
                            "error": "prometheus_query_failed",
                            "metric": key,
                            "response": payload,
                        }
                    results[key] = payload.get("data", {}).get("result", [])
        except Exception as exc:
            return {
                "error": "prometheus_query_failed",
                "message": str(exc),
                "prometheus_url": prometheus_url,
            }

        return {
            "source": "prometheus",
            "prometheus_url": prometheus_url,
            "app_name": app_name,
            "namespace": namespace,
            "queries": queries,
            "results": results,
        }

    async def k8s_sync_knowledge_graph(self, **kwargs: Any) -> dict:
        namespace = kwargs.get("namespace") or self.default_namespace
        all_namespaces = self._as_bool(kwargs.get("all_namespaces"), default=False)
        graph = self._build_knowledge_graph(namespace=namespace, all_namespaces=all_namespaces)
        store = self._knowledge_graph_store()
        saved = store.save(
            graph["nodes"],
            graph["edges"],
            metadata={
                "namespace": None if all_namespaces else namespace,
                "all_namespaces": all_namespaces,
                "source": "kubernetes-api",
            },
        )
        return {
            "path": str(store.path),
            "updated_at": saved["updated_at"],
            "summary": store.summarize(saved),
        }

    async def k8s_update_knowledge_graph_metrics(self, **kwargs: Any) -> dict:
        synced = await self.k8s_sync_knowledge_graph(**kwargs)
        synced["metrics_source"] = "not_configured"
        synced["message"] = "已同步 K8s 拓扑图谱；当前未配置 Prometheus 指标源，指标字段保持为空。"
        return synced

    async def k8s_relation_query(self, **kwargs: Any) -> dict:
        resource_type = kwargs.get("resource_type") or kwargs.get("kind") or ""
        resource_name = kwargs.get("resource_name") or kwargs.get("name") or ""
        namespace = kwargs.get("namespace") or self.default_namespace
        depth = self._as_int(kwargs.get("depth"), default=2, minimum=0)
        if not resource_type:
            return {"error": "resource_type 参数必填"}
        if not resource_name:
            return {"error": "resource_name 参数必填"}
        self._ensure_knowledge_graph(namespace=namespace)
        return self._knowledge_graph_store().query(
            resource_type=resource_type,
            resource_name=resource_name,
            namespace=namespace if normalize_graph_kind(resource_type) != "node" else None,
            depth=depth,
        )

    async def k8s_resource_metrics_query(self, **kwargs: Any) -> dict:
        resource_name = kwargs.get("resource_name") or kwargs.get("name") or ""
        resource_type = kwargs.get("resource_type") or kwargs.get("kind") or "deployment"
        namespace = kwargs.get("namespace") or self.default_namespace
        if not resource_name:
            return {"error": "resource_name 参数必填"}
        self._ensure_knowledge_graph(namespace=namespace)
        relation = self._knowledge_graph_store().query(
            resource_type=resource_type,
            resource_name=resource_name,
            namespace=namespace if normalize_graph_kind(resource_type) != "node" else None,
            depth=0,
        )
        node = relation["nodes"][0] if relation.get("nodes") else None
        return {
            "found": bool(node),
            "resource_type": normalize_graph_kind(resource_type),
            "resource_name": resource_name,
            "namespace": namespace,
            "metrics": node.get("metrics") if node else None,
            "message": (
                "当前图谱中暂无指标数据；需要接入 Prometheus 后填充 metrics 字段。"
                if node and not node.get("metrics")
                else ""
            ),
            "node": node,
        }

    async def k8s_metrics_coverage_report(self, **kwargs: Any) -> dict:
        namespace = kwargs.get("namespace") or self.default_namespace
        self._ensure_knowledge_graph(namespace=namespace)
        coverage = self._knowledge_graph_store().metrics_coverage()
        coverage["message"] = (
            "当前为本地图谱拓扑覆盖率；Prometheus 指标接入后会显示资源指标覆盖率。"
        )
        return coverage

    async def k8s_resource_analysis_report(self, **kwargs: Any) -> dict:
        namespace = kwargs.get("namespace") or self.default_namespace
        self._ensure_knowledge_graph(namespace=namespace)
        store = self._knowledge_graph_store()
        graph = store.load()
        issues = self._analyze_graph_issues(graph, namespace=namespace)
        return {
            "graph_updated_at": graph.get("updated_at"),
            "summary": store.summarize(graph),
            "issues": issues,
            "issue_count": len(issues),
            "notify_dingtalk": self._as_bool(kwargs.get("notify_dingtalk"), default=False),
        }

    async def k8s_resource_monitor(self, **kwargs: Any) -> dict:
        report = await self.k8s_resource_analysis_report(**kwargs)
        app_name = kwargs.get("app_name") or kwargs.get("resource_name")
        if app_name:
            report["app_name"] = app_name
            report["issues"] = [
                issue
                for issue in report["issues"]
                if issue.get("name") == app_name or issue.get("target") == app_name
            ]
            report["issue_count"] = len(report["issues"])
        return report

    async def k8s_scale_deployment(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        deployment_name = kwargs.get("deployment_name") or kwargs.get("name") or ""
        replicas = kwargs.get("replicas")
        if not deployment_name:
            return {"error": "deployment_name 参数必填"}
        if replicas is None:
            return {"error": "replicas 参数必填"}
        replicas = int(replicas)
        body = {"spec": {"replicas": replicas}}
        apps.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=ns,
            body=body,
        )
        return {
            "resource_type": "deployment",
            "name": deployment_name,
            "namespace": ns,
            "replicas": replicas,
            "scaled": True,
        }

    async def k8s_restart_deployment(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        deployment_name = kwargs.get("deployment_name") or kwargs.get("name") or ""
        if not deployment_name:
            return {"error": "deployment_name 参数必填"}
        restarted_at = datetime.now(timezone.utc).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": restarted_at,
                        }
                    }
                }
            }
        }
        apps.patch_namespaced_deployment(
            name=deployment_name,
            namespace=ns,
            body=body,
        )
        return {
            "resource_type": "deployment",
            "name": deployment_name,
            "namespace": ns,
            "restarted_at": restarted_at,
            "restarted": True,
        }

    async def k8s_edit_resource(self, **kwargs: Any) -> dict:
        return await self.k8s_patch_resource(**kwargs)

    async def k8s_patch_resource(self, **kwargs: Any) -> dict:
        resource_type = self._normalize_resource_type(
            kwargs.get("resource_type") or kwargs.get("kind")
        )
        name = kwargs.get("name") or kwargs.get("resource_name") or ""
        ns = self._ns(kwargs)
        patch = self._parse_patch_body(kwargs.get("patch") or kwargs.get("body"))
        if not resource_type:
            return {"error": "resource_type 参数必填"}
        if not name:
            return {"error": "name 参数必填"}
        if patch is None:
            return {"error": "patch 参数必须是 JSON 对象或对象字面量"}

        patcher = self._patch_resource_handler(resource_type)
        if patcher is None:
            return {"error": f"暂不支持 patch 资源类型: {resource_type}"}
        patcher(name=name, namespace=ns, body=patch)
        return {
            "resource_type": resource_type,
            "name": name,
            "namespace": ns,
            "patched": True,
        }

    async def k8s_delete_resource(self, **kwargs: Any) -> dict:
        resource_type = self._normalize_resource_type(
            kwargs.get("resource_type") or kwargs.get("kind")
        )
        name = kwargs.get("name") or kwargs.get("resource_name") or ""
        ns = self._ns(kwargs)
        if not resource_type:
            return {"error": "resource_type 参数必填"}
        if not name:
            return {"error": "name 参数必填"}

        deleter = self._delete_resource_handler(resource_type)
        if deleter is None:
            return {"error": f"暂不支持 delete 资源类型: {resource_type}"}
        deleter(name=name, namespace=ns)
        return {
            "resource_type": resource_type,
            "name": name,
            "namespace": ns,
            "deleted": True,
        }

    async def k8s_cluster_summary(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        apps = self._get_apps_v1()
        nodes = v1.list_node()
        pods = v1.list_pod_for_all_namespaces(limit=500)
        deps = apps.list_deployment_for_all_namespaces(limit=200)
        return {
            "nodes": len(nodes.items),
            "pods": len(pods.items),
            "deployments": len(deps.items),
            "pod_phases": {
                p: sum(1 for pod in pods.items if pod.status.phase == p)
                for p in {"Running", "Pending", "Failed", "Succeeded"}
            },
        }

    def _knowledge_graph_store(self) -> FileKnowledgeGraphStore:
        return FileKnowledgeGraphStore(get_settings().k8s_knowledge_graph_path)

    def _ensure_knowledge_graph(self, namespace: str) -> None:
        store = self._knowledge_graph_store()
        if store.load().get("nodes"):
            return
        graph = self._build_knowledge_graph(namespace=namespace, all_namespaces=False)
        store.save(
            graph["nodes"],
            graph["edges"],
            metadata={"namespace": namespace, "all_namespaces": False, "source": "kubernetes-api"},
        )

    def _build_knowledge_graph(self, namespace: str, all_namespaces: bool = False) -> dict:
        v1 = self._get_v1()
        apps = self._get_apps_v1()
        networking = self._get_networking_v1()

        pods = self._list_resources(v1, "pod", namespace, all_namespaces)
        services = self._list_resources(v1, "service", namespace, all_namespaces)
        nodes = self._safe_items(v1.list_node(limit=100))
        deployments = self._list_resources(apps, "deployment", namespace, all_namespaces)
        replica_sets = self._list_resources(apps, "replica_set", namespace, all_namespaces)
        ingresses = self._list_resources(networking, "ingress", namespace, all_namespaces)

        graph_nodes = []
        edges = []

        for node in nodes:
            graph_node = self._graph_node(
                "node", node, namespace=None, attributes=self._node_attributes(node)
            )
            graph_nodes.append(graph_node)

        for deployment in deployments:
            graph_node = self._graph_node(
                "deployment", deployment, attributes=self._deployment_attributes(deployment)
            )
            graph_nodes.append(graph_node)

        for replica_set in replica_sets:
            graph_node = self._graph_node(
                "replicaset", replica_set, attributes=self._replicaset_attributes(replica_set)
            )
            graph_nodes.append(graph_node)
            edges.extend(self._owner_edges("replicaset", replica_set))

        for pod in pods:
            graph_node = self._graph_node("pod", pod, attributes=self._pod_attributes(pod))
            graph_nodes.append(graph_node)
            edges.extend(self._owner_edges("pod", pod))
            node_name = getattr(getattr(pod, "spec", None), "node_name", None)
            if node_name:
                edges.append(
                    {
                        "source": graph_node["id"],
                        "target": graph_node_id("node", None, node_name),
                        "type": "scheduled_on",
                    }
                )

        pod_nodes = [node for node in graph_nodes if node["kind"] == "pod"]
        for service in services:
            service_node = self._graph_node(
                "service", service, attributes=self._service_attributes(service)
            )
            graph_nodes.append(service_node)
            selector = service_node["attributes"].get("selector") or {}
            if selector:
                for pod_node in pod_nodes:
                    if pod_node.get("namespace") != service_node.get("namespace"):
                        continue
                    if self._labels_match(selector, pod_node.get("labels", {})):
                        edges.append(
                            {
                                "source": service_node["id"],
                                "target": pod_node["id"],
                                "type": "selects",
                            }
                        )

        for ingress in ingresses:
            ingress_node = self._graph_node(
                "ingress", ingress, attributes=self._ingress_attributes(ingress)
            )
            graph_nodes.append(ingress_node)
            for service_name in ingress_node["attributes"].get("backend_services", []):
                edges.append(
                    {
                        "source": ingress_node["id"],
                        "target": graph_node_id(
                            "service", ingress_node.get("namespace"), service_name
                        ),
                        "type": "routes_to",
                    }
                )

        return {
            "nodes": self._dedupe_graph_nodes(graph_nodes),
            "edges": edges,
        }

    @staticmethod
    def _format_endpoint_address(address: Any) -> dict:
        target_ref = getattr(address, "target_ref", None)
        return {
            "ip": getattr(address, "ip", None),
            "hostname": getattr(address, "hostname", None),
            "node": getattr(address, "node_name", None),
            "target_kind": getattr(target_ref, "kind", None) if target_ref else None,
            "target_name": getattr(target_ref, "name", None) if target_ref else None,
        }

    @staticmethod
    def _format_service(service: Any) -> dict:
        spec = getattr(service, "spec", None)
        metadata = getattr(service, "metadata", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "type": getattr(spec, "type", None),
            "cluster_ip": getattr(spec, "cluster_ip", None),
            "external_ips": getattr(spec, "external_i_ps", None)
            or getattr(spec, "external_ips", None)
            or [],
            "selector": getattr(spec, "selector", None) or {},
            "ports": [
                {
                    "name": getattr(port, "name", None),
                    "port": getattr(port, "port", None),
                    "target_port": getattr(port, "target_port", None),
                    "node_port": getattr(port, "node_port", None),
                    "protocol": getattr(port, "protocol", None),
                }
                for port in (getattr(spec, "ports", None) or [])
            ],
        }

    @staticmethod
    def _format_replicaset(replica_set: Any) -> dict:
        metadata = getattr(replica_set, "metadata", None)
        spec = getattr(replica_set, "spec", None)
        status = getattr(replica_set, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "desired": getattr(spec, "replicas", None),
            "ready": getattr(status, "ready_replicas", None) or 0,
            "available": getattr(status, "available_replicas", None) or 0,
            "current": getattr(status, "replicas", None) or 0,
            "owners": K8sClient._format_owner_refs(
                getattr(metadata, "owner_references", None) or []
            ),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_ingress(ingress: Any) -> dict:
        metadata = getattr(ingress, "metadata", None)
        spec = getattr(ingress, "spec", None)
        rules = []
        for rule in getattr(spec, "rules", None) or []:
            paths = []
            http = getattr(rule, "http", None)
            for path in getattr(http, "paths", None) or []:
                backend = getattr(path, "backend", None)
                service = getattr(backend, "service", None) if backend else None
                port = getattr(service, "port", None) if service else None
                paths.append(
                    {
                        "path": getattr(path, "path", None),
                        "path_type": getattr(path, "path_type", None),
                        "service": getattr(service, "name", None) if service else None,
                        "service_port": (
                            (getattr(port, "number", None) or getattr(port, "name", None))
                            if port
                            else None
                        ),
                    }
                )
            rules.append(
                {
                    "host": getattr(rule, "host", None),
                    "paths": paths,
                }
            )

        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "class_name": getattr(spec, "ingress_class_name", None),
            "rules": rules,
            "tls_hosts": [
                host
                for tls in (getattr(spec, "tls", None) or [])
                for host in (getattr(tls, "hosts", None) or [])
            ],
        }

    @staticmethod
    def _format_statefulset(statefulset: Any) -> dict:
        metadata = getattr(statefulset, "metadata", None)
        spec = getattr(statefulset, "spec", None)
        status = getattr(statefulset, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "replicas": getattr(spec, "replicas", None) or 0,
            "ready": getattr(status, "ready_replicas", None) or 0,
            "current": getattr(status, "current_replicas", None) or 0,
            "updated": getattr(status, "updated_replicas", None) or 0,
            "service_name": getattr(spec, "service_name", None),
            "current_revision": getattr(status, "current_revision", None),
            "update_revision": getattr(status, "update_revision", None),
            "images": K8sClient._pod_template_images(getattr(spec, "template", None)),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_daemonset(daemonset: Any) -> dict:
        metadata = getattr(daemonset, "metadata", None)
        spec = getattr(daemonset, "spec", None)
        status = getattr(daemonset, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "desired": getattr(status, "desired_number_scheduled", None) or 0,
            "current": getattr(status, "current_number_scheduled", None) or 0,
            "ready": getattr(status, "number_ready", None) or 0,
            "available": getattr(status, "number_available", None) or 0,
            "updated": getattr(status, "updated_number_scheduled", None) or 0,
            "images": K8sClient._pod_template_images(getattr(spec, "template", None)),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_job(job: Any) -> dict:
        metadata = getattr(job, "metadata", None)
        spec = getattr(job, "spec", None)
        status = getattr(job, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "active": getattr(status, "active", None) or 0,
            "succeeded": getattr(status, "succeeded", None) or 0,
            "failed": getattr(status, "failed", None) or 0,
            "completions": getattr(spec, "completions", None),
            "parallelism": getattr(spec, "parallelism", None),
            "completion_mode": getattr(spec, "completion_mode", None),
            "start_time": K8sClient._stringify_time(getattr(status, "start_time", None)),
            "completion_time": K8sClient._stringify_time(getattr(status, "completion_time", None)),
            "owners": K8sClient._format_owner_refs(
                getattr(metadata, "owner_references", None) or []
            ),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_cronjob(cronjob: Any) -> dict:
        metadata = getattr(cronjob, "metadata", None)
        spec = getattr(cronjob, "spec", None)
        status = getattr(cronjob, "status", None)
        active = getattr(status, "active", None) or []
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "schedule": getattr(spec, "schedule", None),
            "suspend": getattr(spec, "suspend", None) or False,
            "active": [getattr(item, "name", None) for item in active],
            "last_schedule_time": K8sClient._stringify_time(
                getattr(status, "last_schedule_time", None)
            ),
            "last_successful_time": K8sClient._stringify_time(
                getattr(status, "last_successful_time", None)
            ),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_hpa(hpa: Any) -> dict:
        metadata = getattr(hpa, "metadata", None)
        spec = getattr(hpa, "spec", None)
        status = getattr(hpa, "status", None)
        scale_target = getattr(spec, "scale_target_ref", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "target": {
                "kind": getattr(scale_target, "kind", None),
                "name": getattr(scale_target, "name", None),
                "api_version": getattr(scale_target, "api_version", None),
            },
            "min_replicas": getattr(spec, "min_replicas", None),
            "max_replicas": getattr(spec, "max_replicas", None),
            "current_replicas": getattr(status, "current_replicas", None) or 0,
            "desired_replicas": getattr(status, "desired_replicas", None) or 0,
            "current_metrics": K8sClient._serialize_k8s_obj(
                getattr(status, "current_metrics", None) or []
            ),
            "conditions": K8sClient._format_conditions(getattr(status, "conditions", None) or []),
        }

    @staticmethod
    def _format_network_policy(policy: Any) -> dict:
        metadata = getattr(policy, "metadata", None)
        spec = getattr(policy, "spec", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "pod_selector": K8sClient._serialize_k8s_obj(getattr(spec, "pod_selector", None)),
            "policy_types": getattr(spec, "policy_types", None) or [],
            "ingress_rules": len(getattr(spec, "ingress", None) or []),
            "egress_rules": len(getattr(spec, "egress", None) or []),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_namespace(namespace: Any) -> dict:
        metadata = getattr(namespace, "metadata", None)
        status = getattr(namespace, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "status": getattr(status, "phase", None),
            "labels": getattr(metadata, "labels", None) or {},
            "created_at": K8sClient._stringify_time(getattr(metadata, "creation_timestamp", None)),
        }

    @staticmethod
    def _format_configmap(configmap: Any, include_data: bool = False) -> dict:
        metadata = getattr(configmap, "metadata", None)
        data = getattr(configmap, "data", None) or {}
        binary_data = getattr(configmap, "binary_data", None) or {}
        item = {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "keys": sorted(data.keys()),
            "binary_keys": sorted(binary_data.keys()),
            "data_size_bytes": sum(len(str(value).encode("utf-8")) for value in data.values()),
            "labels": getattr(metadata, "labels", None) or {},
        }
        if include_data:
            item["data"] = data
        return item

    @staticmethod
    def _format_secret(secret: Any) -> dict:
        metadata = getattr(secret, "metadata", None)
        data = getattr(secret, "data", None) or {}
        string_data = getattr(secret, "string_data", None) or {}
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "type": getattr(secret, "type", None),
            "keys": sorted(set(data.keys()) | set(string_data.keys())),
            "data_count": len(set(data.keys()) | set(string_data.keys())),
            "values": "redacted",
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_service_account(service_account: Any) -> dict:
        metadata = getattr(service_account, "metadata", None)
        secrets = getattr(service_account, "secrets", None) or []
        image_pull_secrets = getattr(service_account, "image_pull_secrets", None) or []
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "secrets": [getattr(item, "name", None) for item in secrets],
            "image_pull_secrets": [getattr(item, "name", None) for item in image_pull_secrets],
            "automount_service_account_token": getattr(
                service_account, "automount_service_account_token", None
            ),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_pvc(pvc: Any) -> dict:
        metadata = getattr(pvc, "metadata", None)
        spec = getattr(pvc, "spec", None)
        status = getattr(pvc, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "status": getattr(status, "phase", None),
            "volume_name": getattr(spec, "volume_name", None),
            "storage_class": getattr(spec, "storage_class_name", None),
            "access_modes": getattr(spec, "access_modes", None) or [],
            "requested_storage": (
                getattr(spec, "resources", None)
                and getattr(getattr(spec, "resources"), "requests", None)
                or {}
            ).get("storage"),
            "capacity": (getattr(status, "capacity", None) or {}).get("storage"),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_pv(pv: Any) -> dict:
        metadata = getattr(pv, "metadata", None)
        spec = getattr(pv, "spec", None)
        status = getattr(pv, "status", None)
        claim_ref = getattr(spec, "claim_ref", None)
        return {
            "name": getattr(metadata, "name", None),
            "status": getattr(status, "phase", None),
            "storage_class": getattr(spec, "storage_class_name", None),
            "reclaim_policy": getattr(spec, "persistent_volume_reclaim_policy", None),
            "access_modes": getattr(spec, "access_modes", None) or [],
            "capacity": (getattr(spec, "capacity", None) or {}).get("storage"),
            "claim": {
                "namespace": getattr(claim_ref, "namespace", None) if claim_ref else None,
                "name": getattr(claim_ref, "name", None) if claim_ref else None,
            },
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_resource_quota(resource_quota: Any) -> dict:
        metadata = getattr(resource_quota, "metadata", None)
        status = getattr(resource_quota, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "hard": getattr(status, "hard", None) or {},
            "used": getattr(status, "used", None) or {},
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_limit_range(limit_range: Any) -> dict:
        metadata = getattr(limit_range, "metadata", None)
        spec = getattr(limit_range, "spec", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "limits": K8sClient._serialize_k8s_obj(getattr(spec, "limits", None) or []),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_storage_class(storage_class: Any) -> dict:
        metadata = getattr(storage_class, "metadata", None)
        return {
            "name": getattr(metadata, "name", None),
            "provisioner": getattr(storage_class, "provisioner", None),
            "reclaim_policy": getattr(storage_class, "reclaim_policy", None),
            "volume_binding_mode": getattr(storage_class, "volume_binding_mode", None),
            "allow_volume_expansion": getattr(storage_class, "allow_volume_expansion", None),
            "parameters": getattr(storage_class, "parameters", None) or {},
        }

    @staticmethod
    def _format_role(role: Any) -> dict:
        metadata = getattr(role, "metadata", None)
        rules = getattr(role, "rules", None) or []
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "rules": [K8sClient._format_policy_rule(rule) for rule in rules],
            "rule_count": len(rules),
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_role_binding(role_binding: Any) -> dict:
        metadata = getattr(role_binding, "metadata", None)
        role_ref = getattr(role_binding, "role_ref", None)
        subjects = getattr(role_binding, "subjects", None) or []
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "role_ref": {
                "kind": getattr(role_ref, "kind", None),
                "name": getattr(role_ref, "name", None),
                "api_group": getattr(role_ref, "api_group", None),
            },
            "subjects": [
                {
                    "kind": getattr(subject, "kind", None),
                    "name": getattr(subject, "name", None),
                    "namespace": getattr(subject, "namespace", None),
                }
                for subject in subjects
            ],
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_pdb(pdb: Any) -> dict:
        metadata = getattr(pdb, "metadata", None)
        spec = getattr(pdb, "spec", None)
        status = getattr(pdb, "status", None)
        return {
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "min_available": getattr(spec, "min_available", None),
            "max_unavailable": getattr(spec, "max_unavailable", None),
            "current_healthy": getattr(status, "current_healthy", None) or 0,
            "desired_healthy": getattr(status, "desired_healthy", None) or 0,
            "disruptions_allowed": getattr(status, "disruptions_allowed", None) or 0,
            "expected_pods": getattr(status, "expected_pods", None) or 0,
            "labels": getattr(metadata, "labels", None) or {},
        }

    @staticmethod
    def _format_policy_rule(rule: Any) -> dict:
        return {
            "api_groups": getattr(rule, "api_groups", None) or [],
            "resources": getattr(rule, "resources", None) or [],
            "resource_names": getattr(rule, "resource_names", None) or [],
            "verbs": getattr(rule, "verbs", None) or [],
            "non_resource_urls": getattr(rule, "non_resource_urls", None) or [],
        }

    @staticmethod
    def _format_owner_refs(owner_references: list[Any]) -> list[dict]:
        return [
            {
                "kind": getattr(owner, "kind", None),
                "name": getattr(owner, "name", None),
                "controller": getattr(owner, "controller", None),
            }
            for owner in owner_references
        ]

    @staticmethod
    def _format_event(event: Any) -> dict:
        involved_object = getattr(event, "involved_object", None)
        event_time = (
            getattr(event, "event_time", None)
            or getattr(event, "last_timestamp", None)
            or getattr(event, "first_timestamp", None)
        )
        if hasattr(event_time, "isoformat"):
            event_time = event_time.isoformat()
        elif event_time is not None:
            event_time = str(event_time)

        message = getattr(event, "message", "") or ""
        return {
            "type": getattr(event, "type", None) or "Unknown",
            "reason": getattr(event, "reason", None) or "",
            "message": str(message)[:200],
            "object": getattr(involved_object, "name", None) if involved_object else None,
            "object_kind": getattr(involved_object, "kind", None) if involved_object else None,
            "namespace": getattr(involved_object, "namespace", None) if involved_object else None,
            "count": getattr(event, "count", None) or 1,
            "time": event_time,
        }

    @staticmethod
    def _safe_items(value: Any) -> list[Any]:
        return list(getattr(value, "items", None) or [])

    @staticmethod
    def _as_bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", ""}:
                return False
        return default

    @staticmethod
    def _as_int(value: Any, default: int = 0, minimum: int | None = None) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        if minimum is not None:
            return max(parsed, minimum)
        return parsed

    @classmethod
    def _list_resources(
        cls, api: Any, resource: str, namespace: str, all_namespaces: bool
    ) -> list[Any]:
        if all_namespaces:
            method = getattr(api, f"list_{resource}_for_all_namespaces", None)
            if method:
                return cls._safe_items(method(limit=500))
        method = getattr(api, f"list_namespaced_{resource}", None)
        if method:
            return cls._safe_items(method(namespace=namespace, limit=500))
        return []

    @staticmethod
    def _graph_node(
        kind: str,
        obj: Any,
        namespace: Optional[str] = None,
        attributes: Optional[dict] = None,
    ) -> dict:
        metadata = getattr(obj, "metadata", None)
        name = getattr(metadata, "name", None)
        ns = namespace if namespace is not None else getattr(metadata, "namespace", None)
        return {
            "id": graph_node_id(kind, ns, name),
            "kind": normalize_graph_kind(kind),
            "name": name,
            "namespace": ns,
            "labels": getattr(metadata, "labels", None) or {},
            "attributes": attributes or {},
            "metrics": {},
        }

    @staticmethod
    def _node_attributes(node: Any) -> dict:
        status = getattr(node, "status", None)
        metadata = getattr(node, "metadata", None)
        ready_condition = next(
            (
                condition
                for condition in (getattr(status, "conditions", None) or [])
                if getattr(condition, "type", None) == "Ready"
            ),
            None,
        )
        return {
            "ready": getattr(ready_condition, "status", None),
            "roles": [
                key.replace("node-role.kubernetes.io/", "")
                for key in (getattr(metadata, "labels", None) or {})
                if key.startswith("node-role")
            ],
            "version": getattr(getattr(status, "node_info", None), "kubelet_version", None),
        }

    @staticmethod
    def _deployment_attributes(deployment: Any) -> dict:
        spec = getattr(deployment, "spec", None)
        status = getattr(deployment, "status", None)
        return {
            "desired": getattr(spec, "replicas", None) or 0,
            "available": getattr(status, "available_replicas", None) or 0,
            "ready": getattr(status, "ready_replicas", None) or 0,
            "updated": getattr(status, "updated_replicas", None) or 0,
        }

    @staticmethod
    def _replicaset_attributes(replica_set: Any) -> dict:
        spec = getattr(replica_set, "spec", None)
        status = getattr(replica_set, "status", None)
        return {
            "desired": getattr(spec, "replicas", None) or 0,
            "ready": getattr(status, "ready_replicas", None) or 0,
            "available": getattr(status, "available_replicas", None) or 0,
            "current": getattr(status, "replicas", None) or 0,
        }

    @staticmethod
    def _pod_attributes(pod: Any) -> dict:
        spec = getattr(pod, "spec", None)
        status = getattr(pod, "status", None)
        return {
            "phase": getattr(status, "phase", None),
            "node": getattr(spec, "node_name", None),
            "restarts": sum(
                cs.restart_count for cs in (getattr(status, "container_statuses", None) or [])
            ),
        }

    @classmethod
    def _service_attributes(cls, service: Any) -> dict:
        formatted = cls._format_service(service)
        return {
            "type": formatted["type"],
            "cluster_ip": formatted["cluster_ip"],
            "selector": formatted["selector"],
            "ports": formatted["ports"],
        }

    @classmethod
    def _ingress_attributes(cls, ingress: Any) -> dict:
        formatted = cls._format_ingress(ingress)
        backend_services = sorted(
            {
                path["service"]
                for rule in formatted["rules"]
                for path in rule["paths"]
                if path.get("service")
            }
        )
        return {
            "class_name": formatted["class_name"],
            "rules": formatted["rules"],
            "tls_hosts": formatted["tls_hosts"],
            "backend_services": backend_services,
        }

    @staticmethod
    def _owner_edges(child_kind: str, obj: Any) -> list[dict]:
        metadata = getattr(obj, "metadata", None)
        namespace = getattr(metadata, "namespace", None)
        child_name = getattr(metadata, "name", None)
        child_id = graph_node_id(child_kind, namespace, child_name)
        edges = []
        for owner in getattr(metadata, "owner_references", None) or []:
            owner_kind = normalize_graph_kind(getattr(owner, "kind", None))
            owner_name = getattr(owner, "name", None)
            if not owner_kind or not owner_name:
                continue
            edges.append(
                {
                    "source": graph_node_id(owner_kind, namespace, owner_name),
                    "target": child_id,
                    "type": "owns",
                }
            )
        return edges

    @staticmethod
    def _labels_match(selector: dict, labels: dict) -> bool:
        return all(labels.get(key) == value for key, value in selector.items())

    @staticmethod
    def _dedupe_graph_nodes(nodes: list[dict]) -> list[dict]:
        deduped = {}
        for node in nodes:
            if node.get("id"):
                deduped[node["id"]] = node
        return list(deduped.values())

    @staticmethod
    def _pod_template_images(template: Any) -> list[str]:
        spec = getattr(template, "spec", None)
        return [
            getattr(container, "image", "")
            for container in (getattr(spec, "containers", None) or [])
            if getattr(container, "image", "")
        ]

    @staticmethod
    def _label_selector_from_match_labels(match_labels: Any) -> str:
        labels = match_labels or {}
        if not isinstance(labels, dict):
            labels = K8sClient._serialize_k8s_obj(labels) or {}
        return ",".join(f"{key}={value}" for key, value in sorted(labels.items()))

    @staticmethod
    def _stringify_time(value: Any) -> Optional[str]:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _format_conditions(conditions: list[Any]) -> list[dict]:
        return [
            {
                "type": getattr(condition, "type", None),
                "status": getattr(condition, "status", None),
                "reason": getattr(condition, "reason", None),
                "message": getattr(condition, "message", None),
            }
            for condition in conditions
        ]

    @staticmethod
    def _serialize_k8s_obj(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [K8sClient._serialize_k8s_obj(item) for item in value]
        if isinstance(value, tuple):
            return [K8sClient._serialize_k8s_obj(item) for item in value]
        if isinstance(value, dict):
            return {key: K8sClient._serialize_k8s_obj(item) for key, item in value.items()}
        if hasattr(value, "to_dict"):
            return K8sClient._serialize_k8s_obj(value.to_dict())
        if hasattr(value, "__dict__"):
            return {
                key: K8sClient._serialize_k8s_obj(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return str(value)

    @staticmethod
    def _deployment_rollout_status(deployment: Any) -> dict:
        metadata = getattr(deployment, "metadata", None)
        spec = getattr(deployment, "spec", None)
        status = getattr(deployment, "status", None)
        desired = getattr(spec, "replicas", None) or 0
        updated = getattr(status, "updated_replicas", None) or 0
        ready = getattr(status, "ready_replicas", None) or 0
        available = getattr(status, "available_replicas", None) or 0
        observed_generation = getattr(status, "observed_generation", None)
        generation = getattr(metadata, "generation", None)
        complete = (
            observed_generation == generation
            and updated >= desired
            and ready >= desired
            and available >= desired
        )
        return {
            "resource_type": "deployment",
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "complete": complete,
            "desired": desired,
            "updated": updated,
            "ready": ready,
            "available": available,
            "generation": generation,
            "observed_generation": observed_generation,
            "conditions": K8sClient._format_conditions(getattr(status, "conditions", None) or []),
        }

    @staticmethod
    def _statefulset_rollout_status(statefulset: Any) -> dict:
        metadata = getattr(statefulset, "metadata", None)
        spec = getattr(statefulset, "spec", None)
        status = getattr(statefulset, "status", None)
        desired = getattr(spec, "replicas", None) or 0
        ready = getattr(status, "ready_replicas", None) or 0
        updated = getattr(status, "updated_replicas", None) or 0
        current_revision = getattr(status, "current_revision", None)
        update_revision = getattr(status, "update_revision", None)
        complete = ready >= desired and updated >= desired and current_revision == update_revision
        return {
            "resource_type": "statefulset",
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "complete": complete,
            "desired": desired,
            "ready": ready,
            "updated": updated,
            "current_revision": current_revision,
            "update_revision": update_revision,
        }

    @staticmethod
    def _daemonset_rollout_status(daemonset: Any) -> dict:
        metadata = getattr(daemonset, "metadata", None)
        status = getattr(daemonset, "status", None)
        desired = getattr(status, "desired_number_scheduled", None) or 0
        updated = getattr(status, "updated_number_scheduled", None) or 0
        ready = getattr(status, "number_ready", None) or 0
        available = getattr(status, "number_available", None) or 0
        complete = updated >= desired and ready >= desired and available >= desired
        return {
            "resource_type": "daemonset",
            "name": getattr(metadata, "name", None),
            "namespace": getattr(metadata, "namespace", None),
            "complete": complete,
            "desired": desired,
            "updated": updated,
            "ready": ready,
            "available": available,
        }

    @staticmethod
    def _format_node_metric(item: dict) -> dict:
        usage = item.get("usage", {})
        memory_bytes = K8sClient._parse_memory_bytes(usage.get("memory", "0"))
        return {
            "name": item.get("metadata", {}).get("name"),
            "timestamp": item.get("timestamp"),
            "window": item.get("window"),
            "cpu": usage.get("cpu", "0"),
            "memory": usage.get("memory", "0"),
            "cpu_mcores": K8sClient._parse_cpu_mcores(usage.get("cpu", "0")),
            "memory_bytes": memory_bytes,
            "memory_mib": round(memory_bytes / 1024 / 1024, 2),
        }

    @staticmethod
    def _format_pod_metric(item: dict) -> dict:
        containers = []
        total_cpu = 0
        total_memory = 0
        for container in item.get("containers", []):
            usage = container.get("usage", {})
            cpu = K8sClient._parse_cpu_mcores(usage.get("cpu", "0"))
            memory = K8sClient._parse_memory_bytes(usage.get("memory", "0"))
            total_cpu += cpu
            total_memory += memory
            containers.append(
                {
                    "name": container.get("name"),
                    "cpu": usage.get("cpu", "0"),
                    "memory": usage.get("memory", "0"),
                    "cpu_mcores": cpu,
                    "memory_bytes": memory,
                    "memory_mib": round(memory / 1024 / 1024, 2),
                }
            )
        return {
            "name": item.get("metadata", {}).get("name"),
            "namespace": item.get("metadata", {}).get("namespace"),
            "timestamp": item.get("timestamp"),
            "window": item.get("window"),
            "cpu_mcores": total_cpu,
            "memory_bytes": total_memory,
            "memory_mib": round(total_memory / 1024 / 1024, 2),
            "containers": containers,
        }

    @staticmethod
    def _parse_cpu_mcores(value: Any) -> int:
        raw = str(value or "0").strip()
        if raw.endswith("n"):
            return round(float(raw[:-1] or 0) / 1_000_000)
        if raw.endswith("u"):
            return round(float(raw[:-1] or 0) / 1_000)
        if raw.endswith("m"):
            return round(float(raw[:-1] or 0))
        return round(float(raw or 0) * 1000)

    @staticmethod
    def _parse_memory_bytes(value: Any) -> int:
        raw = str(value or "0").strip()
        match = re.fullmatch(r"([0-9.]+)([EPTGMK]i?|[eptgmk]i?)?", raw)
        if not match:
            return 0
        number = float(match.group(1))
        suffix = (match.group(2) or "").lower()
        binary = {
            "ki": 1024,
            "mi": 1024**2,
            "gi": 1024**3,
            "ti": 1024**4,
            "pi": 1024**5,
            "ei": 1024**6,
        }
        decimal = {
            "k": 1000,
            "m": 1000**2,
            "g": 1000**3,
            "t": 1000**4,
            "p": 1000**5,
            "e": 1000**6,
        }
        return int(number * (binary.get(suffix) or decimal.get(suffix) or 1))

    @staticmethod
    def _promql_string(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    @staticmethod
    def _analyze_graph_issues(graph: dict, namespace: str) -> list[dict]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        node_by_id = {node["id"]: node for node in nodes if node.get("id")}
        outgoing: dict[str, list[dict]] = {}
        for edge in edges:
            outgoing.setdefault(edge.get("source", ""), []).append(edge)

        issues = []
        for node in nodes:
            if node.get("namespace") not in (namespace, None):
                continue
            if node.get("kind") == "deployment":
                attrs = node.get("attributes", {})
                desired = attrs.get("desired", 0)
                available = attrs.get("available", 0)
                if desired > available:
                    issues.append(
                        {
                            "severity": "warning",
                            "kind": "deployment",
                            "name": node.get("name"),
                            "namespace": node.get("namespace"),
                            "reason": "deployment_available_replicas_low",
                            "message": f"Deployment 期望 {desired} 副本，可用 {available} 副本。",
                        }
                    )
            elif node.get("kind") == "service":
                selected = [
                    edge for edge in outgoing.get(node["id"], []) if edge.get("type") == "selects"
                ]
                if not selected:
                    issues.append(
                        {
                            "severity": "warning",
                            "kind": "service",
                            "name": node.get("name"),
                            "namespace": node.get("namespace"),
                            "reason": "service_selects_no_pods",
                            "message": "Service selector 当前没有匹配到 Pod。",
                        }
                    )
            elif node.get("kind") == "ingress":
                for edge in [
                    edge for edge in outgoing.get(node["id"], []) if edge.get("type") == "routes_to"
                ]:
                    target = node_by_id.get(edge.get("target"))
                    if not target:
                        issues.append(
                            {
                                "severity": "warning",
                                "kind": "ingress",
                                "name": node.get("name"),
                                "namespace": node.get("namespace"),
                                "target": edge.get("target"),
                                "reason": "ingress_backend_service_missing",
                                "message": "Ingress 指向的 Service 在图谱中不存在。",
                            }
                        )
        return issues

    @staticmethod
    def _parse_command(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        if not isinstance(value, str) or not value.strip():
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item)]
        except json.JSONDecodeError:
            pass
        return shlex.split(value)

    @staticmethod
    def _parse_patch_body(value: Any) -> dict | None:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _normalize_resource_type(value: Any) -> str:
        normalized = str(value or "").strip().lower()
        aliases = {
            "deploy": "deployment",
            "deployments": "deployment",
            "pod": "pod",
            "pods": "pod",
            "svc": "service",
            "services": "service",
            "service": "service",
            "rs": "replicaset",
            "replicasets": "replicaset",
            "replicaset": "replicaset",
            "ing": "ingress",
            "ingresses": "ingress",
            "ingress": "ingress",
            "cm": "configmap",
            "configmaps": "configmap",
            "configmap": "configmap",
            "secret": "secret",
            "secrets": "secret",
            "sa": "serviceaccount",
            "serviceaccounts": "serviceaccount",
            "serviceaccount": "serviceaccount",
            "sts": "statefulset",
            "statefulsets": "statefulset",
            "statefulset": "statefulset",
            "ds": "daemonset",
            "daemonsets": "daemonset",
            "daemonset": "daemonset",
            "job": "job",
            "jobs": "job",
            "cj": "cronjob",
            "cronjobs": "cronjob",
            "cronjob": "cronjob",
            "hpa": "hpa",
            "hpas": "hpa",
            "horizontalpodautoscaler": "hpa",
            "horizontalpodautoscalers": "hpa",
            "pvc": "pvc",
            "pvcs": "pvc",
            "persistentvolumeclaim": "pvc",
            "persistentvolumeclaims": "pvc",
            "netpol": "networkpolicy",
            "networkpolicies": "networkpolicy",
            "networkpolicy": "networkpolicy",
            "pdb": "pdb",
            "poddisruptionbudget": "pdb",
            "poddisruptionbudgets": "pdb",
        }
        return aliases.get(normalized, normalized)

    def _patch_resource_handler(self, resource_type: str):
        if resource_type == "pod":
            return self._get_v1().patch_namespaced_pod
        if resource_type == "service":
            return self._get_v1().patch_namespaced_service
        if resource_type == "configmap":
            return self._get_v1().patch_namespaced_config_map
        if resource_type == "secret":
            return self._get_v1().patch_namespaced_secret
        if resource_type == "serviceaccount":
            return self._get_v1().patch_namespaced_service_account
        if resource_type == "pvc":
            return self._get_v1().patch_namespaced_persistent_volume_claim
        if resource_type == "deployment":
            return self._get_apps_v1().patch_namespaced_deployment
        if resource_type == "replicaset":
            return self._get_apps_v1().patch_namespaced_replica_set
        if resource_type == "statefulset":
            return self._get_apps_v1().patch_namespaced_stateful_set
        if resource_type == "daemonset":
            return self._get_apps_v1().patch_namespaced_daemon_set
        if resource_type == "job":
            return self._get_batch_v1().patch_namespaced_job
        if resource_type == "cronjob":
            return self._get_batch_v1().patch_namespaced_cron_job
        if resource_type == "hpa":
            return self._get_autoscaling_v2().patch_namespaced_horizontal_pod_autoscaler
        if resource_type == "ingress":
            return self._get_networking_v1().patch_namespaced_ingress
        if resource_type == "networkpolicy":
            return self._get_networking_v1().patch_namespaced_network_policy
        if resource_type == "pdb":
            return self._get_policy_v1().patch_namespaced_pod_disruption_budget
        return None

    def _delete_resource_handler(self, resource_type: str):
        if resource_type == "pod":
            return self._get_v1().delete_namespaced_pod
        if resource_type == "service":
            return self._get_v1().delete_namespaced_service
        if resource_type == "configmap":
            return self._get_v1().delete_namespaced_config_map
        if resource_type == "secret":
            return self._get_v1().delete_namespaced_secret
        if resource_type == "serviceaccount":
            return self._get_v1().delete_namespaced_service_account
        if resource_type == "pvc":
            return self._get_v1().delete_namespaced_persistent_volume_claim
        if resource_type == "deployment":
            return self._get_apps_v1().delete_namespaced_deployment
        if resource_type == "replicaset":
            return self._get_apps_v1().delete_namespaced_replica_set
        if resource_type == "statefulset":
            return self._get_apps_v1().delete_namespaced_stateful_set
        if resource_type == "daemonset":
            return self._get_apps_v1().delete_namespaced_daemon_set
        if resource_type == "job":
            return self._get_batch_v1().delete_namespaced_job
        if resource_type == "cronjob":
            return self._get_batch_v1().delete_namespaced_cron_job
        if resource_type == "hpa":
            return self._get_autoscaling_v2().delete_namespaced_horizontal_pod_autoscaler
        if resource_type == "ingress":
            return self._get_networking_v1().delete_namespaced_ingress
        if resource_type == "networkpolicy":
            return self._get_networking_v1().delete_namespaced_network_policy
        if resource_type == "pdb":
            return self._get_policy_v1().delete_namespaced_pod_disruption_budget
        return None

    @staticmethod
    def _stream_pod_exec(
        v1: Any,
        pod_name: str,
        namespace: str,
        command: list[str],
        container: Optional[str],
        timeout: int,
    ) -> str:
        from kubernetes.stream import stream

        return stream(
            v1.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=command,
            container=container,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _request_timeout=timeout,
        )
