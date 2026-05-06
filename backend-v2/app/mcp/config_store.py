"""UI-managed runtime MCP configuration for builtin tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings, is_placeholder_secret, resolve_repo_path
from app.mcp.tools.k8s import K8sClient


def read_mcp_document(config_path: Optional[Path] = None) -> tuple[dict[str, Any], str]:
    path = config_path or resolve_repo_path(get_settings().mcp_config_path)
    if path.exists():
        try:
            return _normalize_document(json.loads(path.read_text(encoding="utf-8"))), "json"
        except (OSError, json.JSONDecodeError):
            pass

    example_path = resolve_repo_path("config/mcp_config.example.json")
    if example_path.exists():
        try:
            return _normalize_document(json.loads(example_path.read_text(encoding="utf-8"))), "example"
        except (OSError, json.JSONDecodeError):
            pass

    return _normalize_document({}), "default"


def write_mcp_document(document: dict[str, Any], config_path: Optional[Path] = None) -> None:
    path = config_path or resolve_repo_path(get_settings().mcp_config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_document(document), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def public_mcp_config(document: Optional[dict[str, Any]] = None, source: str = "") -> dict[str, Any]:
    settings = get_settings()
    config_path = resolve_repo_path(settings.mcp_config_path)
    if document is None:
        document, source = read_mcp_document(config_path)

    k8s_status = _k8s_status(settings)
    ecs_configured = bool(
        settings.alibaba_access_key_id
        and settings.alibaba_access_key_secret
        and not is_placeholder_secret(settings.alibaba_access_key_secret)
    )
    ecs_enabled = bool(settings.ecs_mcp_enabled or settings.alibaba_access_key_id)

    return {
        "config_path": str(config_path),
        "source": source,
        "restart_required": False,
        "k8s": {
            "enabled": bool(settings.k8s_mcp_enabled),
            "kubeconfig_path": settings.kubeconfig_path or "",
            "namespace": settings.k8s_namespace,
            "in_cluster": bool(settings.k8s_in_cluster),
            "configured": k8s_status["configured"],
            "available": k8s_status["available"],
            "unavailable_reason": k8s_status["unavailable_reason"],
        },
        "ecs": {
            "enabled": ecs_enabled,
            "region_id": settings.alibaba_region_id,
            "access_key_id_configured": bool(settings.alibaba_access_key_id),
            "access_key_secret_configured": bool(settings.alibaba_access_key_secret),
            "configured": ecs_configured,
            "available": bool(ecs_enabled and ecs_configured),
            "unavailable_reason": "" if ecs_configured else "未配置 ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        },
    }


def apply_mcp_updates(document: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_document(document)
    builtin = normalized.setdefault("builtin", {})

    if isinstance(updates.get("k8s"), dict):
        k8s = builtin.setdefault("k8s", {})
        for field in ["enabled", "in_cluster"]:
            if field in updates["k8s"]:
                k8s[field] = bool(updates["k8s"][field])
        if "namespace" in updates["k8s"]:
            k8s["namespace"] = str(updates["k8s"]["namespace"] or "default").strip() or "default"
        if "kubeconfig_path" in updates["k8s"]:
            path = str(updates["k8s"]["kubeconfig_path"] or "").strip()
            k8s["kubeconfig_path"] = path or None

    if isinstance(updates.get("ecs"), dict):
        ecs = builtin.setdefault("ecs", {})
        if "enabled" in updates["ecs"]:
            ecs["enabled"] = bool(updates["ecs"]["enabled"])
        if "region_id" in updates["ecs"]:
            ecs["region_id"] = str(updates["ecs"]["region_id"] or "cn-hangzhou").strip() or "cn-hangzhou"
        if "access_key_id" in updates["ecs"]:
            access_key_id = str(updates["ecs"]["access_key_id"] or "").strip()
            if access_key_id:
                ecs["access_key_id"] = access_key_id
        if "access_key_secret" in updates["ecs"]:
            access_key_secret = str(updates["ecs"]["access_key_secret"] or "").strip()
            if access_key_secret:
                ecs["access_key_secret"] = access_key_secret

    return normalized


def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        document = {}
    document.setdefault("version", "1.0")
    document.setdefault("name", "MCP configuration")
    document.setdefault("description", "ToolSearch plus in-process K8s/ECS tool configuration.")
    document.setdefault("global_config", {})
    document.setdefault("servers", [])
    document.setdefault("tools", [])
    document.setdefault("tool_routing", {})
    document.setdefault("security", {"readonly_default": True, "audit_enabled": True})
    document.setdefault("logging", {"level": "INFO"})
    builtin = document.setdefault("builtin", {})
    if not isinstance(builtin, dict):
        builtin = {}
        document["builtin"] = builtin
    _normalize_k8s_config(builtin.setdefault("k8s", {}))
    _normalize_ecs_config(builtin.setdefault("ecs", {}))
    if not isinstance(document["servers"], list):
        document["servers"] = []
    return document


def _normalize_k8s_config(config: dict[str, Any]) -> None:
    config.setdefault("enabled", True)
    config.setdefault("kubeconfig_path", None)
    config.setdefault("namespace", "default")
    config.setdefault("in_cluster", False)


def _normalize_ecs_config(config: dict[str, Any]) -> None:
    config.setdefault("enabled", False)
    config.setdefault("access_key_id", None)
    config.setdefault("access_key_secret", None)
    config.setdefault("region_id", "cn-hangzhou")


def _k8s_status(settings: Any) -> dict[str, Any]:
    if not settings.k8s_mcp_enabled:
        return {"configured": False, "available": False, "unavailable_reason": "K8s MCP 未启用"}

    client = K8sClient(
        kubeconfig_path=settings.kubeconfig_path,
        in_cluster=settings.k8s_in_cluster,
        default_namespace=settings.k8s_namespace,
    )
    available = client.is_configured()
    return {
        "configured": bool(settings.k8s_in_cluster or settings.kubeconfig_path or available),
        "available": available,
        "unavailable_reason": "" if available else client.unavailable_reason(),
    }
