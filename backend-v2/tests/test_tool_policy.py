from __future__ import annotations

import json

from app.mcp.policy import ToolCatalogPolicy


def test_policy_allows_read_tool_for_viewer(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path)))
    decision = policy.authorize("k8s-get-pods", {"username": "viewer", "role": "viewer"}, {})

    assert decision.allowed is True
    assert decision.reason == "read_allowed"
    assert decision.metadata is not None
    assert decision.metadata.danger_level == "read"


def test_policy_denies_catalog_only_tool(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path)))
    decision = policy.authorize("k8s-get-deployment-history", {"username": "admin", "role": "admin"}, {})

    assert decision.allowed is False
    assert decision.reason == "catalog_only_tool_cannot_execute"


def test_policy_requires_confirmation_for_write_tool(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path, danger_level="write")))
    arguments = {"namespace": "default", "deployment_name": "web", "replicas": 2}

    viewer = policy.authorize("k8s-get-pods", {"username": "viewer", "role": "viewer"}, arguments)
    assert viewer.allowed is False
    assert viewer.reason == "operator_role_required"

    operator_without_confirmation = policy.authorize(
        "k8s-get-pods",
        {"username": "operator", "role": "operator"},
        arguments,
    )
    assert operator_without_confirmation.allowed is False
    assert operator_without_confirmation.reason == "confirmation_required"
    assert operator_without_confirmation.requires_confirmation is True
    assert operator_without_confirmation.confirmation_token

    bool_confirmed = policy.authorize(
        "k8s-get-pods",
        {"username": "operator", "role": "operator"},
        {**arguments, "__confirmed": True},
    )
    assert bool_confirmed.allowed is False
    assert bool_confirmed.reason == "confirmation_required"

    operator_confirmed = policy.authorize(
        "k8s-get-pods",
        {"username": "operator", "role": "operator"},
        {**arguments, "__confirmation_token": operator_without_confirmation.confirmation_token},
    )
    assert operator_confirmed.allowed is True
    assert operator_confirmed.reason == "write_allowed"

    tampered_arguments = {
        **arguments,
        "replicas": 4,
        "__confirmation_token": operator_without_confirmation.confirmation_token,
    }
    tampered = policy.authorize(
        "k8s-get-pods",
        {"username": "operator", "role": "operator"},
        tampered_arguments,
    )
    assert tampered.allowed is False
    assert tampered.reason == "invalid_confirmation_token"


def test_policy_requires_admin_for_dangerous_tool(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path, danger_level="dangerous")))
    arguments = {"namespace": "default", "resource_type": "pod", "resource_name": "web-1"}

    operator = policy.authorize(
        "k8s-get-pods",
        {"username": "operator", "role": "operator"},
        arguments,
    )
    assert operator.allowed is False
    assert operator.reason == "admin_role_required"

    admin_without_confirmation = policy.authorize(
        "k8s-get-pods",
        {"username": "admin", "role": "admin"},
        arguments,
    )
    assert admin_without_confirmation.allowed is False
    assert admin_without_confirmation.reason == "confirmation_required"

    admin = policy.authorize(
        "k8s-get-pods",
        {"username": "admin", "role": "admin"},
        {**arguments, "__confirmation_token": admin_without_confirmation.confirmation_token},
    )
    assert admin.allowed is True
    assert admin.reason == "dangerous_allowed"


def test_policy_allows_toolsearch_discovery_tools_without_catalog_entry(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path)))
    arguments = {"query": "pod 日志", "api_key": "secret-value"}
    decision = policy.authorize("toolsearch", {"username": "viewer", "role": "viewer"}, arguments)

    assert decision.allowed is True
    assert decision.reason == "discovery_tool"
    assert decision.metadata is not None
    assert decision.metadata.category == "toolsearch"
    assert decision.to_audit_details(arguments)["argumentPreview"] == {
        "query": "pod 日志",
        "api_key": "<redacted>",
    }


def _catalog(tmp_path, danger_level: str = "read"):
    path = tmp_path / "tool_catalog.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "tools": [
                    {
                        "name": "k8s-get-pods",
                        "title": "获取 Pod 列表",
                        "category": "kubernetes",
                        "description": "获取 Kubernetes Pod 列表",
                        "tags": ["k8s", "pod"],
                        "dangerLevel": danger_level,
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    },
                    {
                        "name": "k8s-get-deployment-history",
                        "title": "获取 Deployment 版本历史",
                        "category": "kubernetes",
                        "description": "获取 Kubernetes Deployment 的版本历史",
                        "tags": ["k8s", "deployment"],
                        "dangerLevel": "read",
                        "server": "catalog",
                        "executionPolicy": "catalog_only",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
