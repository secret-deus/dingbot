"""系统配置 & MCP 工具状态 API"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, is_placeholder_secret, resolve_repo_path
from app.core.deps import get_current_user, require_admin
from app.db.repositories.audit_repo import AuditRepository
from app.db.session import get_db
from app.llm.config_store import (
    delete_provider,
    load_llm_runtime,
    normalize_provider_id,
    read_llm_document,
    upsert_provider,
    write_llm_document,
)
from app.mcp.config_store import (
    apply_mcp_updates,
    public_mcp_config,
    read_mcp_document,
    write_mcp_document,
)
from app.mcp.tools.knowledge_graph import FileKnowledgeGraphStore

router = APIRouter(prefix="/config", tags=["配置"])


@router.get("/status")
async def get_status():
    return {"status": "ok", "version": "3.0.0"}


@router.get("/health")
async def health_check():
    from app.core.deps import _get_app_state

    state = _get_app_state()
    llm_runtime = load_llm_runtime()
    mcp_manager = state.get("mcp_manager")
    mcp_health = await mcp_manager.health_check() if mcp_manager else {}
    scheduler_runner = state.get("scheduler_runner")
    return {
        "status": "healthy",
        "llm_enabled": llm_runtime.active,
        "llm_configured": llm_runtime.configured,
        "mcp_servers": mcp_health,
        "scheduler": scheduler_runner.status()
        if scheduler_runner
        else {"enabled": False, "running": False, "jobs": 0},
    }


@router.get("/dashboard")
async def dashboard_summary(_user: dict = Depends(get_current_user)):
    from app.core.deps import _get_app_state

    settings = get_settings()
    state = _get_app_state()
    llm_runtime = load_llm_runtime()
    mcp_manager = state.get("mcp_manager")
    mcp_health = await mcp_manager.health_check() if mcp_manager else {}
    tools = await mcp_manager.list_tools() if mcp_manager else []
    scheduler_runner = state.get("scheduler_runner")
    scheduler = (
        scheduler_runner.status()
        if scheduler_runner
        else {"enabled": False, "running": False, "jobs": 0}
    )

    config_path = resolve_repo_path(settings.mcp_config_path)
    mcp_config = public_mcp_config(*read_mcp_document(config_path))
    k8s_config = mcp_config["k8s"]

    store = FileKnowledgeGraphStore(settings.k8s_knowledge_graph_path)
    graph = store.load()
    graph_summary = store.summarize(graph)
    coverage = _metrics_coverage(graph)

    total_tools = sum(server.get("tools", 0) for server in mcp_health.values()) or len(tools)
    available_tools = sum(
        server.get("available_tools", 0) for server in mcp_health.values()
    ) or len([tool for tool in tools if tool.get("available", True)])
    unavailable_tools = max(total_tools - available_tools, 0)
    k8s_tools = len([tool for tool in tools if tool.get("name", "").startswith("k8s-")])

    cluster_available = bool(k8s_config.get("available"))
    cluster_name = "minikube" if cluster_available else "Kubernetes 未连接"
    namespace = k8s_config.get("namespace") or settings.k8s_namespace

    return {
        "theme": _dashboard_theme(),
        "icon_pack": _dashboard_icon_pack(),
        "cluster": {
            "name": cluster_name,
            "namespace": namespace,
            "available": cluster_available,
            "configured": bool(k8s_config.get("configured")),
            "mode": "in-cluster" if k8s_config.get("in_cluster") else "kubeconfig",
            "unavailable_reason": k8s_config.get("unavailable_reason") or "",
        },
        "tools": {
            "total": total_tools,
            "available": available_tools,
            "unavailable": unavailable_tools,
            "kubernetes": k8s_tools,
        },
        "knowledge_graph": {
            "updated_at": graph.get("updated_at"),
            "summary": graph_summary,
            "coverage": coverage,
        },
        "scheduler": scheduler,
        "llm": {
            "enabled": llm_runtime.active,
            "configured": llm_runtime.configured,
        },
        "insights": _dashboard_insights(
            cluster_available=cluster_available,
            namespace=namespace,
            k8s_tools=k8s_tools,
            total_tools=total_tools,
            available_tools=available_tools,
            unavailable_tools=unavailable_tools,
            graph_summary=graph_summary,
            coverage=coverage,
            scheduler=scheduler,
        ),
        "resource_map": _dashboard_resource_map(graph_summary, cluster_available),
        "execution_timeline": _dashboard_timeline(
            namespace=namespace,
            cluster_available=cluster_available,
            graph_summary=graph_summary,
            llm_enabled=llm_runtime.active,
        ),
        "next_actions": [
            {
                "id": "inspect",
                "title": "查看相关资源",
                "route": "Chat",
                "tone": "blue",
                "icon": "bot-core",
            },
            {
                "id": "repair",
                "title": "生成修复建议",
                "route": "Chat",
                "tone": "green",
                "icon": "execution-flow",
            },
            {
                "id": "audit",
                "title": "导出审计记录",
                "route": "MCPConfig",
                "tone": "slate",
                "icon": "mcp-toolchain",
            },
        ],
    }


@router.get("/tools")
async def list_tools(_user: dict = Depends(get_current_user)):
    from app.core.deps import _get_app_state

    state = _get_app_state()
    mcp_manager = state.get("mcp_manager")
    if not mcp_manager:
        return {"tools": []}
    tools = await mcp_manager.list_tools()
    return {"tools": tools}


@router.get("/llm")
async def get_llm_config(_user: dict = Depends(get_current_user)):
    runtime = load_llm_runtime()
    selected = runtime.provider
    return {
        "enabled": runtime.enabled,
        "active": runtime.active,
        "api_key_configured": bool(selected and selected.api_key_configured),
        "api_key_placeholder": bool(selected and is_placeholder_secret(selected.api_key)),
        "model": selected.model if selected else "",
        "base_url": selected.base_url if selected else None,
        "temperature": selected.temperature if selected else 0.3,
        "max_tokens": selected.max_tokens if selected else 2000,
        "timeout": selected.timeout if selected else 60,
        "masking_enabled": runtime.masking_enabled,
        "config_path": str(runtime.config_path),
        "source": runtime.source,
        "default_provider": runtime.default_provider,
        "selected_provider_id": runtime.selected_provider_id,
        "providers": runtime.providers,
        "restart_required": False,
    }


class LLMProviderRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stream: Optional[bool] = None


class UpdateLLMConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    default_provider: Optional[str] = None
    provider_id: Optional[str] = None
    provider: Optional[LLMProviderRequest] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    masking_enabled: Optional[bool] = None


class K8sMCPConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    kubeconfig_path: Optional[str] = None
    namespace: Optional[str] = None
    in_cluster: Optional[bool] = None


class ECSMCPConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    region_id: Optional[str] = None


class AliyunSLSConfigRequest(BaseModel):
    mappings: Optional[list[dict[str, Any]]] = None


class AliyunMCPConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    access_key_id: Optional[str] = None
    access_key_secret: Optional[str] = None
    default_region_id: Optional[str] = None
    allowed_regions: Optional[list[str]] = None
    required_tags: Optional[dict[str, list[str]]] = None
    allowed_instance_ids: Optional[list[str]] = None
    sls: Optional[AliyunSLSConfigRequest] = None


class UpdateMCPConfigRequest(BaseModel):
    k8s: Optional[K8sMCPConfigRequest] = None
    ecs: Optional[ECSMCPConfigRequest] = None
    aliyun: Optional[AliyunMCPConfigRequest] = None


class K8sKnowledgeGraphSyncRequest(BaseModel):
    namespace: Optional[str] = None
    all_namespaces: bool = False


@router.patch("/llm")
async def update_llm_config(
    req: UpdateLLMConfigRequest,
    _user: dict = Depends(require_admin),
):
    settings = get_settings()
    config_path = resolve_repo_path(settings.llm_config_path)
    document, _source = read_llm_document(config_path)
    security = document.setdefault("security", {})
    updates = req.model_dump(exclude_none=True)

    if "enabled" in updates:
        document["enabled"] = updates["enabled"]
    if "default_provider" in updates:
        document["default_provider"] = normalize_provider_id(updates["default_provider"])
    if "masking_enabled" in updates:
        security["enable_data_masking"] = updates["masking_enabled"]
        security["mask_sensitive_data"] = updates["masking_enabled"]

    provider_updates: dict[str, Any] = {}
    if req.provider:
        provider_updates.update(req.provider.model_dump(exclude_none=True))
    flat_provider_fields = ["model", "base_url", "api_key", "temperature", "max_tokens", "timeout"]
    for field in flat_provider_fields:
        if field in updates:
            provider_updates[field] = updates[field]
    if "provider_id" in updates:
        provider_updates.setdefault("id", updates["provider_id"])

    if provider_updates:
        if not provider_updates.get("id"):
            provider_updates["id"] = updates.get("provider_id") or document.get("default_provider")
        provider = upsert_provider(document, provider_updates)
        if updates.get("default_provider") == provider_updates.get("id"):
            document["default_provider"] = provider["id"]
        elif not document.get("default_provider"):
            document["default_provider"] = provider["id"]

    write_llm_document(document, config_path)
    runtime = load_llm_runtime(document.get("default_provider"))
    return {
        "updated": list(updates.keys()),
        "restart_required": False,
        "active": runtime.active,
    }


@router.get("/mcp")
async def get_mcp_config(_user: dict = Depends(get_current_user)):
    settings = get_settings()
    config_path = resolve_repo_path(settings.mcp_config_path)
    document, source = read_mcp_document(config_path)
    return public_mcp_config(document, source)


@router.patch("/mcp")
async def update_mcp_config(
    req: UpdateMCPConfigRequest,
    _user: dict = Depends(require_admin),
):
    from app.core.deps import _get_app_state

    settings = get_settings()
    config_path = resolve_repo_path(settings.mcp_config_path)
    document, _source = read_mcp_document(config_path)
    updates = req.model_dump(exclude_unset=True)
    document = apply_mcp_updates(document, updates)
    write_mcp_document(document, config_path)

    state = _get_app_state()
    mcp_manager = state.get("mcp_manager")
    if mcp_manager:
        mcp_manager.reload_builtin()

    return public_mcp_config(document, "json")


@router.get("/k8s/knowledge-graph")
async def get_k8s_knowledge_graph(
    namespace: Optional[str] = Query(default=None),
    all_namespaces: bool = Query(default=False),
    auto_sync: bool = Query(default=False),
    user: dict = Depends(get_current_user),
):
    settings = get_settings()
    namespace = namespace or settings.k8s_namespace
    store = FileKnowledgeGraphStore(settings.k8s_knowledge_graph_path)
    graph = store.load()

    if auto_sync and _knowledge_graph_needs_sync(graph, namespace, all_namespaces):
        result = await _sync_k8s_knowledge_graph(
            namespace=namespace, all_namespaces=all_namespaces, user=user
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        graph = store.load()

    visible_graph = graph if all_namespaces else _filter_knowledge_graph(graph, namespace)
    return {
        "path": str(store.path),
        "updated_at": graph.get("updated_at"),
        "metadata": graph.get("metadata", {}),
        "namespace": namespace,
        "all_namespaces": all_namespaces,
        "summary": store.summarize(visible_graph),
        "coverage": _metrics_coverage(visible_graph),
        "nodes": visible_graph["nodes"],
        "edges": visible_graph["edges"],
    }


@router.post("/k8s/knowledge-graph/sync")
async def sync_k8s_knowledge_graph(
    req: K8sKnowledgeGraphSyncRequest,
    user: dict = Depends(get_current_user),
):
    settings = get_settings()
    namespace = req.namespace or settings.k8s_namespace
    result = await _sync_k8s_knowledge_graph(
        namespace=namespace,
        all_namespaces=req.all_namespaces,
        user=user,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    store = FileKnowledgeGraphStore(settings.k8s_knowledge_graph_path)
    graph = store.load()
    visible_graph = graph if req.all_namespaces else _filter_knowledge_graph(graph, namespace)
    return {
        **result,
        "namespace": namespace,
        "all_namespaces": req.all_namespaces,
        "graph": {
            "path": str(store.path),
            "updated_at": graph.get("updated_at"),
            "metadata": graph.get("metadata", {}),
            "summary": store.summarize(visible_graph),
            "coverage": _metrics_coverage(visible_graph),
            "nodes": visible_graph["nodes"],
            "edges": visible_graph["edges"],
        },
    }


@router.delete("/llm/providers/{provider_id}", status_code=204)
async def delete_llm_provider(
    provider_id: str,
    _user: dict = Depends(require_admin),
):
    settings = get_settings()
    config_path = resolve_repo_path(settings.llm_config_path)
    document, _source = read_llm_document(config_path)
    if not delete_provider(document, provider_id):
        raise HTTPException(404, "模型配置不存在")
    write_llm_document(document, config_path)


@router.get("/audit")
async def get_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    repo = AuditRepository(db)
    logs = await repo.query(
        actor=actor,
        action=action,
        resource=resource,
        resource_id=resource_id,
        result=result,
        limit=limit,
        offset=offset,
    )
    await db.commit()
    return [
        {
            "id": log.id,
            "actor": log.actor,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "result": log.result,
            "ip": log.ip,
            "details": log.details,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]


async def _sync_k8s_knowledge_graph(
    namespace: str,
    all_namespaces: bool,
    user: dict,
) -> dict[str, Any]:
    from app.core.deps import _get_app_state

    state = _get_app_state()
    mcp_manager = state.get("mcp_manager")
    if not mcp_manager:
        return {"error": "mcp_manager_not_initialized"}
    result = await mcp_manager.call_tool(
        "k8s-sync-knowledge-graph",
        {"namespace": namespace, "all_namespaces": all_namespaces},
        user=user,
    )
    return result.get("result", result) if isinstance(result, dict) else {"error": str(result)}


def _knowledge_graph_needs_sync(
    graph: dict[str, Any], namespace: str, all_namespaces: bool = False
) -> bool:
    if not graph.get("nodes"):
        return True
    metadata = graph.get("metadata", {})
    if all_namespaces:
        return not bool(metadata.get("all_namespaces"))
    if metadata.get("all_namespaces"):
        return False
    return bool(namespace and metadata.get("namespace") != namespace)


def _filter_knowledge_graph(graph: dict[str, Any], namespace: Optional[str]) -> dict[str, Any]:
    if not namespace:
        return {
            "nodes": graph.get("nodes", []),
            "edges": graph.get("edges", []),
        }

    nodes = [node for node in graph.get("nodes", []) if node.get("namespace") in (namespace, None)]
    node_ids = {node.get("id") for node in nodes}
    edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("source") in node_ids and edge.get("target") in node_ids
    ]
    return {"nodes": nodes, "edges": edges}


def _metrics_coverage(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    total = len(nodes)
    nodes_with_metrics = [node for node in nodes if node.get("metrics")]
    return {
        "total_nodes": total,
        "nodes_with_metrics": len(nodes_with_metrics),
        "coverage": round(len(nodes_with_metrics) / total, 4) if total else 0,
    }


def _dashboard_theme() -> dict[str, str]:
    return {
        "background": "#070a0f",
        "shell": "#0d1420",
        "surface": "#111827",
        "surface_alt": "#172235",
        "surface_light": "#f8fafc",
        "border": "#2a3648",
        "text": "#f8fafc",
        "muted": "#9aa8bd",
        "primary": "#22c55e",
        "accent": "#38bdf8",
        "warning": "#f59e0b",
        "danger": "#ef4444",
    }


def _dashboard_icon_pack() -> dict[str, str]:
    return {
        "bot": "bot-core",
        "kubernetes": "kubernetes-cluster",
        "mcp": "mcp-toolchain",
        "graph": "knowledge-map",
        "timeline": "execution-flow",
    }


def _dashboard_insights(
    *,
    cluster_available: bool,
    namespace: str,
    k8s_tools: int,
    total_tools: int,
    available_tools: int,
    unavailable_tools: int,
    graph_summary: dict[str, Any],
    coverage: dict[str, Any],
    scheduler: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "id": "kubernetes",
            "label": "Kubernetes",
            "title": "集群上下文已就绪" if cluster_available else "等待连接集群",
            "detail": f"{namespace} / {k8s_tools} 个 K8s 工具",
            "tone": "green" if cluster_available else "amber",
            "icon": "kubernetes-cluster",
        },
        {
            "id": "mcp-tools",
            "label": "MCP Tools",
            "title": f"{available_tools}/{total_tools} 可执行",
            "detail": f"{unavailable_tools} 个工具不可用"
            if unavailable_tools
            else "工具链全量可用",
            "tone": "amber" if unavailable_tools else "green",
            "icon": "mcp-toolchain",
        },
        {
            "id": "knowledge-graph",
            "label": "Knowledge Graph",
            "title": f"{graph_summary.get('nodes', 0)} 节点 / {graph_summary.get('edges', 0)} 关系",
            "detail": f"指标覆盖 {round(float(coverage.get('coverage', 0)) * 100)}%",
            "tone": "blue" if graph_summary.get("nodes") else "slate",
            "icon": "knowledge-map",
        },
        {
            "id": "scheduler",
            "label": "Scheduler",
            "title": f"{scheduler.get('jobs', 0)} 个活跃任务",
            "detail": "调度器运行中" if scheduler.get("running") else "调度器未运行或未启用",
            "tone": "green" if scheduler.get("running") else "slate",
            "icon": "execution-flow",
        },
    ]


def _dashboard_resource_map(
    graph_summary: dict[str, Any], cluster_available: bool
) -> list[dict[str, Any]]:
    node_types = graph_summary.get("node_types", {})
    return [
        {
            "kind": "Deployment",
            "count": node_types.get("deployment", 0),
            "tone": "blue",
            "icon": "knowledge-map",
        },
        {
            "kind": "ReplicaSet",
            "count": node_types.get("replicaset", 0),
            "tone": "blue",
            "icon": "execution-flow",
        },
        {
            "kind": "Pod",
            "count": node_types.get("pod", 0),
            "tone": "green" if cluster_available else "slate",
            "icon": "kubernetes-cluster",
        },
        {
            "kind": "Event",
            "count": graph_summary.get("edges", 0),
            "tone": "amber",
            "icon": "mcp-toolchain",
        },
    ]


def _dashboard_timeline(
    *,
    namespace: str,
    cluster_available: bool,
    graph_summary: dict[str, Any],
    llm_enabled: bool,
) -> list[dict[str, Any]]:
    return [
        {
            "id": "question",
            "title": "用户提问",
            "detail": f"查看 {namespace} namespace 当前状态",
            "tone": "blue",
            "icon": "bot-core",
        },
        {
            "id": "pods",
            "title": "调用 k8s-get-pods",
            "detail": "Kubernetes 工具可执行" if cluster_available else "等待 K8s 配置",
            "tone": "green" if cluster_available else "amber",
            "icon": "kubernetes-cluster",
        },
        {
            "id": "events",
            "title": "调用 k8s-get-events",
            "detail": f"图谱已有 {graph_summary.get('nodes', 0)} 个节点"
            if graph_summary.get("nodes")
            else "可在知识图谱页同步资源",
            "tone": "green" if graph_summary.get("nodes") else "slate",
            "icon": "knowledge-map",
        },
        {
            "id": "answer",
            "title": "生成结论",
            "detail": "LLM 已启用，可生成自然语言结论"
            if llm_enabled
            else "LLM 未启用，展示结构化证据",
            "tone": "green" if llm_enabled else "amber",
            "icon": "execution-flow",
        },
    ]
