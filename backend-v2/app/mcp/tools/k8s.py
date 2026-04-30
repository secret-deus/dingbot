"""K8s 客户端 - 封装 kubernetes python client 的核心操作"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from app.core.config import get_settings


class K8sClient:
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        in_cluster: bool = False,
        default_namespace: str = "default",
    ) -> None:
        self.kubeconfig_path = kubeconfig_path
        self.in_cluster = in_cluster
        self.default_namespace = default_namespace
        self._v1: Any = None
        self._apps_v1: Any = None

    def _get_v1(self) -> Any:
        if self._v1 is None:
            from kubernetes import client, config
            if self.in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config(config_file=self.kubeconfig_path)
            self._v1 = client.CoreV1Api()
        return self._v1

    def _get_apps_v1(self) -> Any:
        if self._apps_v1 is None:
            from kubernetes import client
            self._apps_v1 = client.AppsV1Api()
        return self._apps_v1

    def _ns(self, kwargs: dict) -> str:
        return kwargs.get("namespace", self.default_namespace)

    async def k8s_get_pods(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        label_selector = kwargs.get("label_selector", "")
        pods = v1.list_namespaced_pod(namespace=ns, label_selector=label_selector, limit=100)
        items = []
        for p in pods.items:
            items.append({
                "name": p.metadata.name,
                "namespace": p.metadata.namespace,
                "status": p.status.phase,
                "node": p.spec.node_name,
                "restarts": sum(cs.restart_count for cs in (p.status.container_statuses or [])),
                "age": str(p.metadata.creation_timestamp),
            })
        return {"count": len(items), "items": items}

    async def k8s_get_services(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        svcs = v1.list_namespaced_service(namespace=ns, limit=100)
        items = [
            {"name": s.metadata.name, "type": s.spec.type,
             "cluster_ip": s.spec.cluster_ip, "ports": [f"{p.port}/{p.protocol}" for p in (s.spec.ports or [])]}
            for s in svcs.items
        ]
        return {"count": len(items), "items": items}

    async def k8s_get_deployments(self, **kwargs: Any) -> dict:
        apps = self._get_apps_v1()
        ns = self._ns(kwargs)
        deps = apps.list_namespaced_deployment(namespace=ns, limit=100)
        items = [
            {"name": d.metadata.name, "replicas": d.spec.replicas,
             "available": d.status.available_replicas or 0,
             "image": d.spec.template.spec.containers[0].image if d.spec.template.spec.containers else ""}
            for d in deps.items
        ]
        return {"count": len(items), "items": items}

    async def k8s_get_nodes(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        nodes = v1.list_node(limit=100)
        items = [
            {"name": n.metadata.name, "status": n.status.conditions[-1].type if n.status.conditions else "Unknown",
             "roles": [k.replace("node-role.kubernetes.io/", "") for k in (n.metadata.labels or {}) if k.startswith("node-role")],
             "version": n.status.node_info.kubelet_version if n.status.node_info else ""}
            for n in nodes.items
        ]
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

    async def k8s_describe_pod(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        pod_name = kwargs.get("pod_name", "")
        if not pod_name:
            return {"error": "pod_name 参数必填"}
        pod = v1.read_namespaced_pod(name=pod_name, namespace=ns)
        return {
            "name": pod.metadata.name, "namespace": pod.metadata.namespace,
            "status": pod.status.phase, "node": pod.spec.node_name,
            "containers": [{"name": c.name, "image": c.image} for c in pod.spec.containers],
            "events": str(pod.metadata.creation_timestamp),
        }

    async def k8s_get_events(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        ns = self._ns(kwargs)
        events = v1.list_namespaced_event(namespace=ns, limit=50)
        items = [
            {"type": e.type, "reason": e.reason, "message": e.message[:200],
             "object": e.involved_object.name, "count": e.count}
            for e in events.items
        ]
        return {"count": len(items), "items": items}

    async def k8s_cluster_summary(self, **kwargs: Any) -> dict:
        v1 = self._get_v1()
        apps = self._get_apps_v1()
        ns = self.default_namespace
        nodes = v1.list_node()
        pods = v1.list_pod_for_all_namespaces(limit=500)
        deps = apps.list_deployment_for_all_namespaces(limit=200)
        return {
            "nodes": len(nodes.items),
            "pods": len(pods.items),
            "deployments": len(deps.items),
            "pod_phases": {p: sum(1 for pod in pods.items if pod.status.phase == p) for p in {"Running", "Pending", "Failed", "Succeeded"}},
        }
