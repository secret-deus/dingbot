from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.mcp.builtin import BuiltinToolRegistry
from app.api.config import _filter_knowledge_graph, _knowledge_graph_needs_sync, _metrics_coverage
from app.mcp.tools.k8s import K8sClient


@pytest.mark.asyncio
async def test_k8s_get_endpoints_formats_service_subsets():
    api = _FakeCoreV1()
    client = K8sClient(default_namespace="default")
    client._v1 = api

    result = await client.k8s_get_endpoints(service_name="web", namespace="prod")

    assert api.read_args == {"name": "web", "namespace": "prod"}
    assert result == {
        "count": 1,
        "items": [
            {
                "name": "web",
                "namespace": "prod",
                "subsets": [
                    {
                        "addresses": [
                            {
                                "ip": "10.0.0.10",
                                "hostname": None,
                                "node": "node-a",
                                "target_kind": "Pod",
                                "target_name": "web-abc",
                            }
                        ],
                        "not_ready_addresses": [
                            {
                                "ip": "10.0.0.11",
                                "hostname": None,
                                "node": "node-b",
                                "target_kind": "Pod",
                                "target_name": "web-def",
                            }
                        ],
                        "ports": [{"name": "http", "port": 8080, "protocol": "TCP"}],
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_k8s_get_endpoints_lists_by_label_selector():
    api = _FakeCoreV1()
    client = K8sClient(default_namespace="default")
    client._v1 = api

    result = await client.k8s_get_endpoints(label_selector="app=web")

    assert api.list_args == {
        "namespace": "default",
        "label_selector": "app=web",
        "limit": 100,
    }
    assert result["count"] == 1
    assert result["items"][0]["name"] == "web"


@pytest.mark.asyncio
async def test_k8s_get_pods_supports_all_namespaces():
    api = _FakeCoreV1()
    client = K8sClient(default_namespace="default")
    client._v1 = api

    result = await client.k8s_get_pods(namespace="all", label_selector="app=web")

    assert api.pod_all_args == {"label_selector": "app=web", "limit": 500}
    assert result["count"] == 1
    assert result["items"][0]["namespace"] == "prod"


@pytest.mark.asyncio
async def test_k8s_get_events_handles_sparse_event_fields():
    api = _FakeCoreV1()
    client = K8sClient(default_namespace="default")
    client._v1 = api

    result = await client.k8s_get_events(namespace="prod")

    assert api.event_args == {"namespace": "prod", "limit": 50}
    assert result == {
        "count": 2,
        "items": [
            {
                "type": "Unknown",
                "reason": "",
                "message": "",
                "object": None,
                "object_kind": None,
                "namespace": None,
                "count": 1,
                "time": None,
            },
            {
                "type": "Warning",
                "reason": "BackOff",
                "message": "Back-off restarting failed container",
                "object": "web-abc",
                "object_kind": "Pod",
                "namespace": "prod",
                "count": 3,
                "time": "2026-05-06 10:00:00",
            },
        ],
    }


def test_builtin_registry_exposes_k8s_get_endpoints_schema():
    registry = BuiltinToolRegistry()
    tools = {tool["name"]: tool for tool in registry.list_tools()}

    assert "k8s-get-endpoints" in tools
    assert "k8s-get-statefulsets" in tools
    assert "k8s-get-cluster-metrics" in tools
    assert tools["k8s-get-deployment-history"]["inputSchema"]["required"] == ["deployment_name"]
    assert tools["k8s-describe-secret"]["inputSchema"]["required"] == ["secret_name"]
    schema = tools["k8s-get-endpoints"]["inputSchema"]
    assert schema["required"] == []
    assert "label_selector" in schema["properties"]
    assert tools["k8s-delete-resource"]["dangerLevel"] == "dangerous"
    assert tools["k8s-exec-pod"]["inputSchema"]["required"] == ["pod_name", "command"]
    assert tools["k8s-scale-deployment"]["dangerLevel"] == "write"


def test_k8s_unavailable_reason_is_empty_after_config_loaded():
    client = K8sClient(default_namespace="default")
    client._config_loaded = True

    assert client.unavailable_reason() == ""


def test_knowledge_graph_api_helpers_filter_namespace_and_coverage():
    graph = {
        "metadata": {"namespace": "prod", "all_namespaces": False},
        "nodes": [
            {
                "id": "node:_cluster:minikube",
                "kind": "node",
                "name": "minikube",
                "namespace": None,
                "metrics": {},
            },
            {
                "id": "deployment:prod:web",
                "kind": "deployment",
                "name": "web",
                "namespace": "prod",
                "metrics": {"cpu": 1},
            },
            {
                "id": "pod:prod:web-1",
                "kind": "pod",
                "name": "web-1",
                "namespace": "prod",
                "metrics": {},
            },
            {
                "id": "deployment:test:web",
                "kind": "deployment",
                "name": "web",
                "namespace": "test",
                "metrics": {},
            },
        ],
        "edges": [
            {"source": "deployment:prod:web", "target": "pod:prod:web-1", "type": "owns"},
            {
                "source": "pod:prod:web-1",
                "target": "node:_cluster:minikube",
                "type": "scheduled_on",
            },
            {
                "source": "deployment:test:web",
                "target": "node:_cluster:minikube",
                "type": "scheduled_on",
            },
        ],
    }

    visible = _filter_knowledge_graph(graph, "prod")
    coverage = _metrics_coverage(visible)

    assert {node["id"] for node in visible["nodes"]} == {
        "node:_cluster:minikube",
        "deployment:prod:web",
        "pod:prod:web-1",
    }
    assert len(visible["edges"]) == 2
    assert coverage == {"total_nodes": 3, "nodes_with_metrics": 1, "coverage": 0.3333}
    assert _knowledge_graph_needs_sync(graph, "prod") is False
    assert _knowledge_graph_needs_sync(graph, "test") is True
    assert _knowledge_graph_needs_sync(graph, "prod", all_namespaces=True) is True


@pytest.mark.asyncio
async def test_k8s_get_service_ingress_and_replicasets_format_resources():
    core = _FakeCoreV1()
    apps = _FakeAppsV1()
    networking = _FakeNetworkingV1()
    client = K8sClient(default_namespace="default")
    client._v1 = core
    client._apps_v1 = apps
    client._networking_v1 = networking

    service = await client.k8s_describe_service(service_name="web", namespace="prod")
    ingresses = await client.k8s_get_ingresses(namespace="prod")
    replica_sets = await client.k8s_get_replicasets(namespace="prod", label_selector="app=web")
    missing_service = await client.k8s_describe_service(namespace="prod")
    missing_ingress = await client.k8s_describe_ingress(namespace="prod")

    assert core.service_read_args == {"name": "web", "namespace": "prod"}
    assert missing_service == {"error": "service_name 参数必填"}
    assert missing_ingress == {"error": "ingress_name 参数必填"}
    assert service["selector"] == {"app": "web"}
    assert service["ports"][0] == {
        "name": "http",
        "port": 80,
        "target_port": 8080,
        "node_port": None,
        "protocol": "TCP",
    }
    assert networking.ingress_list_args == {"namespace": "prod", "limit": 100}
    assert ingresses["items"][0]["rules"][0] == {
        "host": "example.com",
        "paths": [{"path": "/", "path_type": "Prefix", "service": "web", "service_port": 80}],
    }
    assert apps.rs_list_args == {
        "namespace": "prod",
        "label_selector": "app=web",
        "limit": 100,
    }
    assert replica_sets["items"][0]["owners"] == [
        {"kind": "Deployment", "name": "web", "controller": True}
    ]


@pytest.mark.asyncio
async def test_k8s_write_and_exec_tools_call_expected_handlers(monkeypatch):
    core = _FakeCoreV1()
    apps = _FakeAppsV1()
    networking = _FakeNetworkingV1()
    client = K8sClient(default_namespace="default")
    client._v1 = core
    client._apps_v1 = apps
    client._networking_v1 = networking

    monkeypatch.setattr(
        K8sClient,
        "_stream_pod_exec",
        staticmethod(lambda *_args: "ok\n"),
    )

    scaled = await client.k8s_scale_deployment(
        deployment_name="web",
        replicas=3,
        namespace="prod",
    )
    restarted = await client.k8s_restart_deployment(deployment_name="web", namespace="prod")
    patched = await client.k8s_patch_resource(
        resource_type="ingress",
        name="web",
        namespace="prod",
        patch='{"metadata":{"annotations":{"owner":"ops"}}}',
    )
    deleted = await client.k8s_delete_resource(
        resource_type="service", name="web", namespace="prod"
    )
    executed = await client.k8s_exec_pod(
        pod_name="web-abc",
        namespace="prod",
        container="app",
        command="ls /tmp",
    )

    assert scaled["scaled"] is True
    assert apps.scale_patch_args == {
        "name": "web",
        "namespace": "prod",
        "body": {"spec": {"replicas": 3}},
    }
    assert restarted["restarted"] is True
    assert apps.deployment_patch_args["name"] == "web"
    assert networking.ingress_patch_args == {
        "name": "web",
        "namespace": "prod",
        "body": {"metadata": {"annotations": {"owner": "ops"}}},
    }
    assert patched == {
        "resource_type": "ingress",
        "name": "web",
        "namespace": "prod",
        "patched": True,
    }
    assert core.service_delete_args == {"name": "web", "namespace": "prod"}
    assert deleted["deleted"] is True
    assert executed["command"] == ["ls", "/tmp"]
    assert executed["output"] == "ok\n"


@pytest.mark.asyncio
async def test_k8s_deployment_history_rollout_and_workloads():
    apps = _FakeAppsV1()
    batch = _FakeBatchV1()
    autoscaling = _FakeAutoscalingV2()
    client = K8sClient(default_namespace="default")
    client._apps_v1 = apps
    client._batch_v1 = batch
    client._autoscaling_v2 = autoscaling

    history = await client.k8s_get_deployment_history(deployment_name="web", namespace="prod")
    rollout = await client.k8s_rollout_status(name="web", namespace="prod")
    statefulsets = await client.k8s_get_statefulsets(namespace="prod", label_selector="app=db")
    daemonsets = await client.k8s_get_daemonsets(namespace="prod")
    jobs = await client.k8s_get_jobs(namespace="prod")
    cronjobs = await client.k8s_get_cronjobs(namespace="prod")
    hpas = await client.k8s_get_hpas(namespace="prod")

    assert apps.deployment_read_args == {"name": "web", "namespace": "prod"}
    assert apps.rs_list_args["label_selector"] == "app=web"
    assert history["count"] == 1
    assert history["items"][0]["revision"] == 3
    assert history["items"][0]["images"] == ["nginx:1.27"]
    assert rollout["complete"] is False
    assert statefulsets["items"][0]["service_name"] == "db-headless"
    assert daemonsets["items"][0]["desired"] == 2
    assert jobs["items"][0]["succeeded"] == 1
    assert cronjobs["items"][0]["schedule"] == "*/5 * * * *"
    assert hpas["items"][0]["target"] == {
        "kind": "Deployment",
        "name": "web",
        "api_version": "apps/v1",
    }


@pytest.mark.asyncio
async def test_k8s_common_inventory_tools_redact_and_format_resources():
    core = _FakeCoreV1()
    networking = _FakeNetworkingV1()
    rbac = _FakeRbacV1()
    storage = _FakeStorageV1()
    policy = _FakePolicyV1()
    client = K8sClient(default_namespace="default")
    client._v1 = core
    client._networking_v1 = networking
    client._rbac_v1 = rbac
    client._storage_v1 = storage
    client._policy_v1 = policy

    namespaces = await client.k8s_get_namespaces()
    configmaps = await client.k8s_get_configmaps(namespace="prod")
    configmap = await client.k8s_describe_configmap(
        configmap_name="web-config", namespace="prod", include_data=True
    )
    secrets = await client.k8s_get_secrets(namespace="prod")
    serviceaccounts = await client.k8s_get_serviceaccounts(namespace="prod")
    pvcs = await client.k8s_get_pvcs(namespace="prod")
    pvs = await client.k8s_get_pvs()
    quotas = await client.k8s_get_resourcequotas(namespace="prod")
    limits = await client.k8s_get_limitranges(namespace="prod")
    storageclasses = await client.k8s_get_storageclasses()
    roles = await client.k8s_get_roles(namespace="prod")
    rolebindings = await client.k8s_get_rolebindings(namespace="prod")
    clusterroles = await client.k8s_get_clusterroles()
    clusterrolebindings = await client.k8s_get_clusterrolebindings()
    networkpolicies = await client.k8s_get_networkpolicies(namespace="prod")
    pdbs = await client.k8s_get_pod_disruption_budgets(namespace="prod")

    assert namespaces["items"][0]["name"] == "prod"
    assert configmaps["items"][0]["keys"] == ["APP_MODE"]
    assert "data" not in configmaps["items"][0]
    assert configmap["data"] == {"APP_MODE": "prod"}
    assert secrets["items"][0]["values"] == "redacted"
    assert secrets["items"][0]["keys"] == ["password"]
    assert serviceaccounts["items"][0]["image_pull_secrets"] == ["pull-secret"]
    assert pvcs["items"][0]["requested_storage"] == "1Gi"
    assert pvs["items"][0]["claim"] == {"namespace": "prod", "name": "data-web-0"}
    assert quotas["items"][0]["hard"]["pods"] == "10"
    assert limits["items"][0]["limits"][0]["type"] == "Container"
    assert storageclasses["items"][0]["provisioner"] == "k8s.io/minikube-hostpath"
    assert roles["items"][0]["rules"][0]["verbs"] == ["get", "list"]
    assert rolebindings["items"][0]["subjects"][0]["kind"] == "ServiceAccount"
    assert clusterroles["items"][0]["name"] == "view"
    assert clusterrolebindings["items"][0]["role_ref"]["name"] == "view"
    assert networkpolicies["items"][0]["policy_types"] == ["Ingress"]
    assert pdbs["items"][0]["disruptions_allowed"] == 1


@pytest.mark.asyncio
async def test_k8s_cluster_metrics_uses_real_metrics_api_shape():
    client = K8sClient(default_namespace="default")
    client._custom_objects = _FakeCustomObjects()

    result = await client.k8s_get_cluster_metrics()

    assert result["source"] == "metrics.k8s.io"
    assert result["total_cpu_mcores"] == 250
    assert result["total_memory_mib"] == 512
    assert result["top_pods_by_cpu"][0]["name"] == "web-abc"
    assert result["top_pods_by_memory"][0]["memory_mib"] == 128


@pytest.mark.asyncio
async def test_k8s_knowledge_graph_tools_sync_and_query(monkeypatch, tmp_path):
    monkeypatch.setenv("K8S_KNOWLEDGE_GRAPH_PATH", str(tmp_path / "kg.json"))
    core = _FakeCoreV1()
    apps = _FakeAppsV1()
    networking = _FakeNetworkingV1()
    client = K8sClient(default_namespace="default")
    client._v1 = core
    client._apps_v1 = apps
    client._networking_v1 = networking

    synced = await client.k8s_sync_knowledge_graph(namespace="prod", all_namespaces="false")
    relation = await client.k8s_relation_query(
        resource_type="deployment",
        resource_name="web",
        namespace="prod",
        depth="2",
    )
    metrics = await client.k8s_resource_metrics_query(
        resource_type="deployment",
        resource_name="web",
        namespace="prod",
    )
    coverage = await client.k8s_metrics_coverage_report(namespace="prod")
    report = await client.k8s_resource_analysis_report(namespace="prod", notify_dingtalk="false")
    saved_graph = json.loads((tmp_path / "kg.json").read_text())

    assert synced["summary"]["node_types"]["deployment"] == 1
    assert saved_graph["metadata"]["all_namespaces"] is False
    assert saved_graph["metadata"]["namespace"] == "prod"
    assert synced["summary"]["edge_types"]["owns"] == 2
    assert relation["found"] is True
    assert {node["kind"] for node in relation["nodes"]} >= {"deployment", "replicaset", "pod"}
    assert metrics["found"] is True
    assert "暂无指标数据" in metrics["message"]
    assert coverage["total_nodes"] > 0
    assert coverage["coverage"] == 0
    assert report["issue_count"] == 1
    assert report["notify_dingtalk"] is False
    assert report["issues"][0]["reason"] == "deployment_available_replicas_low"


@pytest.mark.asyncio
async def test_builtin_registry_marks_k8s_tools_unavailable_without_kubeconfig(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.delenv("KUBECONFIG_PATH", raising=False)

    registry = BuiltinToolRegistry()
    tools = {tool["name"]: tool for tool in registry.list_tools()}

    assert tools["k8s-cluster-summary"]["available"] is False
    result = await registry.call("k8s-cluster-summary", {})
    assert result["error"] == "tool_unavailable"
    assert result["reason"] == "kubeconfig_not_configured"


class _FakeCoreV1:
    def __init__(self) -> None:
        self.read_args = None
        self.list_args = None
        self.event_args = None
        self.service_read_args = None
        self.service_delete_args = None
        self.pod_all_args = None

    def list_node(self, limit: int):
        return SimpleNamespace(items=[_node(name="minikube")])

    def list_namespaced_pod(self, namespace: str, limit: int, label_selector: str = ""):
        return SimpleNamespace(items=[_pod(name="web-pod", namespace=namespace)])

    def list_pod_for_all_namespaces(self, label_selector: str = "", limit: int = 500):
        self.pod_all_args = {"label_selector": label_selector, "limit": limit}
        return SimpleNamespace(items=[_pod(name="web-pod", namespace="prod")])

    def read_namespaced_endpoints(self, name: str, namespace: str):
        self.read_args = {"name": name, "namespace": namespace}
        return _endpoint(name=name, namespace=namespace)

    def list_namespaced_endpoints(self, namespace: str, label_selector: str, limit: int):
        self.list_args = {
            "namespace": namespace,
            "label_selector": label_selector,
            "limit": limit,
        }
        return SimpleNamespace(items=[_endpoint(name="web", namespace=namespace)])

    def list_namespaced_event(self, namespace: str, limit: int):
        self.event_args = {"namespace": namespace, "limit": limit}
        return SimpleNamespace(
            items=[
                SimpleNamespace(
                    type=None,
                    reason=None,
                    message=None,
                    involved_object=None,
                    count=None,
                    event_time=None,
                    last_timestamp=None,
                    first_timestamp=None,
                ),
                SimpleNamespace(
                    type="Warning",
                    reason="BackOff",
                    message="Back-off restarting failed container",
                    involved_object=SimpleNamespace(name="web-abc", kind="Pod", namespace="prod"),
                    count=3,
                    event_time=None,
                    last_timestamp="2026-05-06 10:00:00",
                    first_timestamp=None,
                ),
            ]
        )

    def read_namespaced_service(self, name: str, namespace: str):
        self.service_read_args = {"name": name, "namespace": namespace}
        return _service(name=name, namespace=namespace)

    def list_namespaced_service(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_service(name="web", namespace=namespace)])

    def delete_namespaced_service(self, name: str, namespace: str):
        self.service_delete_args = {"name": name, "namespace": namespace}

    def list_namespace(self, limit: int):
        return SimpleNamespace(items=[_namespace(name="prod")])

    def list_namespaced_config_map(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_configmap(name="web-config", namespace=namespace)])

    def read_namespaced_config_map(self, name: str, namespace: str):
        return _configmap(name=name, namespace=namespace)

    def list_namespaced_secret(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_secret(name="web-secret", namespace=namespace)])

    def read_namespaced_secret(self, name: str, namespace: str):
        return _secret(name=name, namespace=namespace)

    def list_namespaced_service_account(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_service_account(name="web", namespace=namespace)])

    def list_namespaced_persistent_volume_claim(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_pvc(name="data-web-0", namespace=namespace)])

    def list_persistent_volume(self, limit: int):
        return SimpleNamespace(items=[_pv(name="pv-data-web-0")])

    def list_namespaced_resource_quota(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_resource_quota(name="quota", namespace=namespace)])

    def list_namespaced_limit_range(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_limit_range(name="limits", namespace=namespace)])


class _FakeAppsV1:
    def __init__(self) -> None:
        self.rs_list_args = None
        self.scale_patch_args = None
        self.deployment_patch_args = None
        self.deployment_read_args = None

    def list_namespaced_deployment(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_deployment(name="web", namespace=namespace)])

    def read_namespaced_deployment(self, name: str, namespace: str):
        self.deployment_read_args = {"name": name, "namespace": namespace}
        return _deployment(name=name, namespace=namespace)

    def list_namespaced_replica_set(
        self, namespace: str, label_selector: str = "", limit: int = 100
    ):
        self.rs_list_args = {
            "namespace": namespace,
            "label_selector": label_selector,
            "limit": limit,
        }
        return SimpleNamespace(items=[_replica_set(name="web-6d8f", namespace=namespace)])

    def list_namespaced_stateful_set(
        self, namespace: str, label_selector: str = "", limit: int = 100
    ):
        self.statefulset_list_args = {
            "namespace": namespace,
            "label_selector": label_selector,
            "limit": limit,
        }
        return SimpleNamespace(items=[_statefulset(name="db", namespace=namespace)])

    def read_namespaced_stateful_set(self, name: str, namespace: str):
        return _statefulset(name=name, namespace=namespace)

    def list_namespaced_daemon_set(
        self, namespace: str, label_selector: str = "", limit: int = 100
    ):
        self.daemonset_list_args = {
            "namespace": namespace,
            "label_selector": label_selector,
            "limit": limit,
        }
        return SimpleNamespace(items=[_daemonset(name="node-agent", namespace=namespace)])

    def read_namespaced_daemon_set(self, name: str, namespace: str):
        return _daemonset(name=name, namespace=namespace)

    def patch_namespaced_deployment_scale(self, name: str, namespace: str, body: dict):
        self.scale_patch_args = {"name": name, "namespace": namespace, "body": body}

    def patch_namespaced_deployment(self, name: str, namespace: str, body: dict):
        self.deployment_patch_args = {"name": name, "namespace": namespace, "body": body}


class _FakeBatchV1:
    def list_namespaced_job(self, namespace: str, label_selector: str = "", limit: int = 100):
        return SimpleNamespace(items=[_job(name="backup", namespace=namespace)])

    def list_namespaced_cron_job(self, namespace: str, label_selector: str = "", limit: int = 100):
        return SimpleNamespace(items=[_cronjob(name="backup-cron", namespace=namespace)])


class _FakeAutoscalingV2:
    def list_namespaced_horizontal_pod_autoscaler(self, namespace: str, limit: int = 100):
        return SimpleNamespace(items=[_hpa(name="web-hpa", namespace=namespace)])


class _FakeNetworkingV1:
    def __init__(self) -> None:
        self.ingress_list_args = None
        self.ingress_patch_args = None

    def list_namespaced_ingress(self, namespace: str, limit: int):
        self.ingress_list_args = {"namespace": namespace, "limit": limit}
        return SimpleNamespace(items=[_ingress(name="web", namespace=namespace)])

    def read_namespaced_ingress(self, name: str, namespace: str):
        return _ingress(name=name, namespace=namespace)

    def patch_namespaced_ingress(self, name: str, namespace: str, body: dict):
        self.ingress_patch_args = {"name": name, "namespace": namespace, "body": body}

    def list_namespaced_network_policy(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_network_policy(name="default-deny", namespace=namespace)])


class _FakeRbacV1:
    def list_namespaced_role(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_role(name="pod-reader", namespace=namespace)])

    def list_namespaced_role_binding(self, namespace: str, limit: int):
        return SimpleNamespace(
            items=[_role_binding(name="pod-reader-binding", namespace=namespace)]
        )

    def list_cluster_role(self, limit: int):
        return SimpleNamespace(items=[_role(name="view", namespace=None)])

    def list_cluster_role_binding(self, limit: int):
        return SimpleNamespace(items=[_role_binding(name="view-binding", namespace=None)])


class _FakeStorageV1:
    def list_storage_class(self, limit: int):
        return SimpleNamespace(items=[_storage_class(name="standard")])


class _FakePolicyV1:
    def list_namespaced_pod_disruption_budget(self, namespace: str, limit: int):
        return SimpleNamespace(items=[_pdb(name="web-pdb", namespace=namespace)])


class _FakeCustomObjects:
    def list_cluster_custom_object(self, group: str, version: str, plural: str):
        assert group == "metrics.k8s.io"
        assert version == "v1beta1"
        if plural == "nodes":
            return {
                "items": [
                    {
                        "metadata": {"name": "minikube"},
                        "timestamp": "2026-05-06T10:00:00Z",
                        "window": "30s",
                        "usage": {"cpu": "250m", "memory": "512Mi"},
                    }
                ]
            }
        if plural == "pods":
            return {
                "items": [
                    {
                        "metadata": {"name": "web-abc", "namespace": "prod"},
                        "timestamp": "2026-05-06T10:00:00Z",
                        "window": "30s",
                        "containers": [
                            {"name": "app", "usage": {"cpu": "125m", "memory": "128Mi"}}
                        ],
                    }
                ]
            }
        return {"items": []}


def _endpoint(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace),
        subsets=[
            SimpleNamespace(
                addresses=[
                    SimpleNamespace(
                        ip="10.0.0.10",
                        hostname=None,
                        node_name="node-a",
                        target_ref=SimpleNamespace(kind="Pod", name="web-abc"),
                    )
                ],
                not_ready_addresses=[
                    SimpleNamespace(
                        ip="10.0.0.11",
                        hostname=None,
                        node_name="node-b",
                        target_ref=SimpleNamespace(kind="Pod", name="web-def"),
                    )
                ],
                ports=[SimpleNamespace(name="http", port=8080, protocol="TCP")],
            )
        ],
    )


def _service(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace),
        spec=SimpleNamespace(
            type="ClusterIP",
            cluster_ip="10.96.0.10",
            external_i_ps=[],
            selector={"app": "web"},
            ports=[
                SimpleNamespace(
                    name="http",
                    port=80,
                    target_port=8080,
                    node_port=None,
                    protocol="TCP",
                )
            ],
        ),
    )


def _replica_set(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name,
            namespace=namespace,
            labels={"app": "web"},
            annotations={
                "deployment.kubernetes.io/revision": "3",
                "kubernetes.io/change-cause": "rollout image",
            },
            owner_references=[SimpleNamespace(kind="Deployment", name="web", controller=True)],
            creation_timestamp="2026-05-06T00:00:00Z",
        ),
        spec=SimpleNamespace(
            replicas=2,
            template=SimpleNamespace(
                spec=SimpleNamespace(containers=[SimpleNamespace(image="nginx:1.27")])
            ),
        ),
        status=SimpleNamespace(replicas=2, ready_replicas=2, available_replicas=1),
    )


def _ingress(name: str, namespace: str):
    service = SimpleNamespace(name="web", port=SimpleNamespace(number=80, name=None))
    path = SimpleNamespace(path="/", path_type="Prefix", backend=SimpleNamespace(service=service))
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace),
        spec=SimpleNamespace(
            ingress_class_name="nginx",
            rules=[SimpleNamespace(host="example.com", http=SimpleNamespace(paths=[path]))],
            tls=[SimpleNamespace(hosts=["example.com"])],
        ),
    )


def _node(name: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, labels={"node-role.kubernetes.io/control-plane": ""}),
        status=SimpleNamespace(
            conditions=[SimpleNamespace(type="Ready", status="True")],
            node_info=SimpleNamespace(kubelet_version="v1.29.0"),
        ),
    )


def _deployment(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name,
            namespace=namespace,
            labels={"app": "web"},
            annotations={"deployment.kubernetes.io/revision": "3"},
            generation=4,
        ),
        spec=SimpleNamespace(
            replicas=2,
            selector=SimpleNamespace(match_labels={"app": "web"}),
            template=SimpleNamespace(spec=SimpleNamespace(containers=[])),
        ),
        status=SimpleNamespace(
            available_replicas=1,
            ready_replicas=1,
            updated_replicas=1,
            observed_generation=4,
            conditions=[
                SimpleNamespace(
                    type="Available",
                    status="False",
                    reason="MinimumReplicasUnavailable",
                    message="",
                )
            ],
        ),
    )


def _pod(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name,
            namespace=namespace,
            labels={"app": "web"},
            owner_references=[SimpleNamespace(kind="ReplicaSet", name="web-6d8f", controller=True)],
            creation_timestamp="2026-05-06T00:00:00Z",
        ),
        spec=SimpleNamespace(
            node_name="minikube", containers=[SimpleNamespace(name="app", image="nginx")]
        ),
        status=SimpleNamespace(
            phase="Running", container_statuses=[SimpleNamespace(restart_count=0)]
        ),
    )


def _namespace(name: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name, labels={"env": "prod"}, creation_timestamp="2026-05-06T00:00:00Z"
        ),
        status=SimpleNamespace(phase="Active"),
    )


def _configmap(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "web"}),
        data={"APP_MODE": "prod"},
        binary_data={},
    )


def _secret(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "web"}),
        type="Opaque",
        data={"password": "c2VjcmV0"},
        string_data=None,
    )


def _service_account(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "web"}),
        secrets=[SimpleNamespace(name="web-token")],
        image_pull_secrets=[SimpleNamespace(name="pull-secret")],
        automount_service_account_token=True,
    )


def _pvc(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "web"}),
        spec=SimpleNamespace(
            volume_name="pv-data-web-0",
            storage_class_name="standard",
            access_modes=["ReadWriteOnce"],
            resources=SimpleNamespace(requests={"storage": "1Gi"}),
        ),
        status=SimpleNamespace(phase="Bound", capacity={"storage": "1Gi"}),
    )


def _pv(name: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, labels={"app": "web"}),
        spec=SimpleNamespace(
            storage_class_name="standard",
            persistent_volume_reclaim_policy="Delete",
            access_modes=["ReadWriteOnce"],
            capacity={"storage": "1Gi"},
            claim_ref=SimpleNamespace(namespace="prod", name="data-web-0"),
        ),
        status=SimpleNamespace(phase="Bound"),
    )


def _resource_quota(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        status=SimpleNamespace(hard={"pods": "10"}, used={"pods": "2"}),
    )


def _limit_range(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        spec=SimpleNamespace(limits=[SimpleNamespace(type="Container", default={"cpu": "500m"})]),
    )


def _storage_class(name: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name),
        provisioner="k8s.io/minikube-hostpath",
        reclaim_policy="Delete",
        volume_binding_mode="Immediate",
        allow_volume_expansion=False,
        parameters={},
    )


def _role(name: str, namespace: str | None):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        rules=[
            SimpleNamespace(
                api_groups=[""],
                resources=["pods"],
                resource_names=[],
                verbs=["get", "list"],
                non_resource_urls=[],
            )
        ],
    )


def _role_binding(name: str, namespace: str | None):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        role_ref=SimpleNamespace(
            kind="ClusterRole", name="view", api_group="rbac.authorization.k8s.io"
        ),
        subjects=[SimpleNamespace(kind="ServiceAccount", name="web", namespace="prod")],
    )


def _network_policy(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        spec=SimpleNamespace(
            pod_selector=SimpleNamespace(match_labels={"app": "web"}),
            policy_types=["Ingress"],
            ingress=[SimpleNamespace()],
            egress=[],
        ),
    )


def _pdb(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        spec=SimpleNamespace(min_available=1, max_unavailable=None),
        status=SimpleNamespace(
            current_healthy=2,
            desired_healthy=1,
            disruptions_allowed=1,
            expected_pods=2,
        ),
    )


def _statefulset(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "db"}),
        spec=SimpleNamespace(
            replicas=2,
            service_name="db-headless",
            template=SimpleNamespace(
                spec=SimpleNamespace(containers=[SimpleNamespace(image="postgres:16")])
            ),
        ),
        status=SimpleNamespace(
            ready_replicas=2,
            current_replicas=2,
            updated_replicas=2,
            current_revision="db-1",
            update_revision="db-1",
        ),
    )


def _daemonset(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={"app": "node-agent"}),
        spec=SimpleNamespace(
            template=SimpleNamespace(
                spec=SimpleNamespace(containers=[SimpleNamespace(image="agent:1")])
            )
        ),
        status=SimpleNamespace(
            desired_number_scheduled=2,
            current_number_scheduled=2,
            number_ready=2,
            number_available=2,
            updated_number_scheduled=2,
        ),
    )


def _job(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}, owner_references=[]),
        spec=SimpleNamespace(completions=1, parallelism=1, completion_mode="NonIndexed"),
        status=SimpleNamespace(
            active=0, succeeded=1, failed=0, start_time=None, completion_time="2026-05-06T00:01:00Z"
        ),
    )


def _cronjob(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace, labels={}),
        spec=SimpleNamespace(schedule="*/5 * * * *", suspend=False),
        status=SimpleNamespace(
            active=[],
            last_schedule_time="2026-05-06T00:00:00Z",
            last_successful_time="2026-05-06T00:01:00Z",
        ),
    )


def _hpa(name: str, namespace: str):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace=namespace),
        spec=SimpleNamespace(
            scale_target_ref=SimpleNamespace(kind="Deployment", name="web", api_version="apps/v1"),
            min_replicas=1,
            max_replicas=5,
        ),
        status=SimpleNamespace(
            current_replicas=2,
            desired_replicas=3,
            current_metrics=[],
            conditions=[],
        ),
    )
