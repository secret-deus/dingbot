from __future__ import annotations

import json

import pytest

from app.mcp.builtin import BuiltinToolRegistry
from app.mcp.config_store import apply_mcp_updates, public_mcp_config, read_mcp_document, write_mcp_document


@pytest.mark.asyncio
async def test_builtin_config_can_disable_k8s_and_expose_unconfigured_ecs(monkeypatch, tmp_path):
    config_path = tmp_path / "mcp_config.json"
    config_path.write_text(
        json.dumps(
            {
                "builtin": {
                    "k8s": {"enabled": False},
                    "ecs": {"enabled": True, "region_id": "cn-hangzhou"},
                },
                "servers": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("KUBECONFIG_PATH", raising=False)
    monkeypatch.delenv("K8S_NAMESPACE", raising=False)
    monkeypatch.delenv("K8S_IN_CLUSTER", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", raising=False)

    registry = BuiltinToolRegistry()
    tools = {tool["name"]: tool for tool in registry.list_tools()}

    assert "k8s-get-pods" not in tools
    assert tools["ecs-list-instances"]["available"] is False
    result = await registry.call("ecs-list-instances", {})
    assert result["error"] == "tool_unavailable"
    assert result["reason"] == "ecs_credentials_not_configured"


def test_mcp_public_config_redacts_ecs_secret_and_writes_builtin_config(monkeypatch, tmp_path):
    config_path = tmp_path / "mcp_config.json"
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("KUBECONFIG_PATH", raising=False)
    monkeypatch.delenv("K8S_NAMESPACE", raising=False)
    monkeypatch.delenv("K8S_IN_CLUSTER", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", raising=False)

    document, _source = read_mcp_document(config_path)
    updated = apply_mcp_updates(
        document,
        {
            "k8s": {"enabled": True, "kubeconfig_path": "/tmp/kubeconfig", "namespace": "prod"},
            "ecs": {
                "enabled": True,
                "access_key_id": "local-access-key-id",
                "access_key_secret": "local-access-key-secret",
                "region_id": "cn-shanghai",
            },
        },
    )
    write_mcp_document(updated, config_path)

    public = public_mcp_config(*read_mcp_document(config_path))
    serialized = json.dumps(public)
    assert public["k8s"]["kubeconfig_path"] == "/tmp/kubeconfig"
    assert public["k8s"]["namespace"] == "prod"
    assert public["ecs"]["access_key_id_configured"] is True
    assert public["ecs"]["access_key_secret_configured"] is True
    assert public["ecs"]["region_id"] == "cn-shanghai"
    assert "local-access-key-secret" not in serialized
