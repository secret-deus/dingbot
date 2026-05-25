"""Tool execution policy based on the normalized ToolSearch catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.db.models import Role

DISCOVERY_TOOLS = {"toolsearch", "tool_get", "tool_categories", "tool_reload_catalog"}


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    category: str
    danger_level: str
    execution_policy: str
    server: str


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str
    metadata: Optional[ToolMetadata]
    requires_confirmation: bool = False

    def to_audit_details(self, arguments: dict[str, Any]) -> dict[str, Any]:
        metadata = self.metadata
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "tool": metadata.name if metadata else None,
            "category": metadata.category if metadata else None,
            "dangerLevel": metadata.danger_level if metadata else None,
            "executionPolicy": metadata.execution_policy if metadata else None,
            "server": metadata.server if metadata else None,
            "requiresConfirmation": self.requires_confirmation,
            "argumentKeys": sorted(arguments.keys()),
            "argumentPreview": _safe_argument_preview(arguments),
            **_aliyun_audit_context(metadata.name if metadata else "", arguments),
        }


class ToolCatalogPolicy:
    def __init__(self, catalog_path: Optional[str] = None) -> None:
        self.catalog_path = self._resolve_catalog_path(catalog_path)
        self._tools: dict[str, ToolMetadata] = {}
        self.reload()

    def reload(self) -> None:
        self._tools = {}
        if not self.catalog_path.exists():
            return
        with open(self.catalog_path, encoding="utf-8") as f:
            catalog = json.load(f)
        for tool in catalog.get("tools", []):
            name = tool.get("name")
            if not name:
                continue
            self._tools[name] = ToolMetadata(
                name=name,
                category=tool.get("category", ""),
                danger_level=tool.get("dangerLevel", "read"),
                execution_policy=tool.get("executionPolicy", "catalog_only"),
                server=tool.get("server", ""),
            )

    def authorize(
        self,
        name: str,
        user: Optional[dict],
        arguments: Optional[dict[str, Any]] = None,
    ) -> ToolPolicyDecision:
        args = arguments or {}
        confirmed = bool(args.pop("__confirmed", False))

        if name in DISCOVERY_TOOLS:
            return ToolPolicyDecision(
                allowed=True,
                reason="discovery_tool",
                metadata=ToolMetadata(
                    name=name,
                    category="toolsearch",
                    danger_level="read",
                    execution_policy="executable",
                    server="toolsearch",
                ),
            )

        metadata = self._tools.get(name)
        if not metadata:
            return ToolPolicyDecision(False, "tool_not_in_catalog", None)

        if metadata.execution_policy == "catalog_only":
            return ToolPolicyDecision(False, "catalog_only_tool_cannot_execute", metadata)

        role = Role((user or {}).get("role", Role.VIEWER.value))
        if metadata.danger_level == "read":
            if metadata.name.startswith("aliyun-") and not self._has_role(role, Role.OPERATOR):
                return ToolPolicyDecision(False, "operator_role_required", metadata)
            if not self._has_role(role, Role.VIEWER):
                return ToolPolicyDecision(False, "viewer_role_required", metadata)
            return ToolPolicyDecision(True, "read_allowed", metadata)

        if metadata.danger_level == "write":
            if not self._has_role(role, Role.OPERATOR):
                return ToolPolicyDecision(False, "operator_role_required", metadata)
            if not confirmed:
                return ToolPolicyDecision(False, "confirmation_required", metadata, True)
            return ToolPolicyDecision(True, "write_allowed", metadata)

        if metadata.danger_level == "dangerous":
            if not self._has_role(role, Role.ADMIN):
                return ToolPolicyDecision(False, "admin_role_required", metadata)
            if not confirmed:
                return ToolPolicyDecision(False, "confirmation_required", metadata, True)
            return ToolPolicyDecision(True, "dangerous_allowed", metadata)

        return ToolPolicyDecision(
            False, f"unsupported_danger_level:{metadata.danger_level}", metadata
        )

    def describe(self, name: str) -> Optional[ToolMetadata]:
        if name in DISCOVERY_TOOLS:
            return ToolMetadata(name, "toolsearch", "read", "executable", "toolsearch")
        return self._tools.get(name)

    @staticmethod
    def _has_role(actual: Role, required: Role) -> bool:
        levels = {Role.VIEWER: 1, Role.OPERATOR: 2, Role.ADMIN: 3}
        return levels.get(actual, 0) >= levels.get(required, 0)

    @classmethod
    def _resolve_catalog_path(cls, catalog_path: Optional[str]) -> Path:
        if catalog_path:
            path = Path(catalog_path)
            return path if path.is_absolute() else cls._repo_root() / path
        return cls._repo_root() / "config/tool_catalog.json"

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[3]


def _safe_argument_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    preview = {}
    for key, value in arguments.items():
        normalized = key.lower().replace("-", "_")
        if any(
            secret_word in normalized
            for secret_word in ["secret", "token", "password", "api_key", "access_key"]
        ):
            preview[key] = "<redacted>"
        elif key in {
            "query",
            "category",
            "limit",
            "dangerLevel",
            "name",
            "tool",
            "namespace",
            "deployment_name",
            "pod_name",
            "service_name",
            "ingress_name",
            "resource_name",
            "resource_type",
            "replicas",
            "container",
            "timeout_seconds",
            "depth",
            "all_namespaces",
            "app_name",
            "region_id",
            "instance_id",
            "resource_id",
            "security_group_id",
            "load_balancer_id",
            "service",
            "env",
            "relative_range",
            "project",
            "logstore",
            "state",
            "event_type",
        }:
            preview[key] = value
    return preview


def _aliyun_audit_context(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if not tool_name.startswith("aliyun-"):
        return {}
    resource_ids = [
        str(arguments[key])
        for key in ["instance_id", "resource_id", "security_group_id", "load_balancer_id"]
        if arguments.get(key)
    ]
    context: dict[str, Any] = {
        "region_id": arguments.get("region_id"),
        "resource_ids": resource_ids,
    }
    if arguments.get("service"):
        context["service"] = arguments.get("service")
    if arguments.get("env"):
        context["env"] = arguments.get("env")
    if arguments.get("relative_range"):
        context["time_range"] = arguments.get("relative_range")
    return context
