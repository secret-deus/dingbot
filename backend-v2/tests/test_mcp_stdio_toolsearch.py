from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.mcp import manager as manager_module
from app.mcp.manager import MCPManager, MCPServerConnection


@pytest.mark.asyncio
async def test_mcp_manager_loads_toolsearch_stdio(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    toolsearch_entry = repo_root / "mcp-servers/toolsearch/dist/src/index.js"
    if not toolsearch_entry.exists():
        pytest.skip(
            "ToolSearch build output is missing; run `cd mcp-servers/toolsearch && npm test` first"
        )
    node_path = _working_node()
    if node_path is None:
        pytest.skip("Node.js is required for ToolSearch stdio smoke test")
    catalog_payload = json.loads(
        (repo_root / "config/tool_catalog.json").read_text(encoding="utf-8")
    )
    expected_catalog_total = len(catalog_payload["tools"])

    config_path = tmp_path / "mcp_config.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "toolsearch",
                        "type": "stdio",
                        "enabled": True,
                        "command": node_path,
                        "args": ["mcp-servers/toolsearch/dist/src/index.js"],
                        "cwd": str(repo_root),
                        "env": {"TOOL_CATALOG_PATH": str(repo_root / "config/tool_catalog.json")},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    manager = MCPManager()
    try:
        await manager.connect_all(str(config_path))
        tools = await manager.list_tools()
        tool_names = {tool["name"] for tool in tools}
        assert "toolsearch" in tool_names
        assert "tool_get" in tool_names

        result = await manager.call_tool("toolsearch", {"query": "查看 pod 日志", "limit": 1})
        payload = json.loads(result["result"])
        assert payload["results"][0]["name"] == "k8s-get-logs"

        unavailable = await manager.call_tool(
            "ecs-describe-instance-monitor-data",
            {"instance_id": "i-local"},
            user={"username": "admin", "role": "admin"},
        )
        assert unavailable["error"] == "tool_unavailable"
        assert unavailable["reason"] == "tool_not_loaded"
        assert unavailable["tool"] == "ecs-describe-instance-monitor-data"

        health = await manager.health_check()
        assert health["toolsearch"]["catalog_total"] == expected_catalog_total
    finally:
        await manager.disconnect_all()


@pytest.mark.asyncio
async def test_mcp_manager_normalizes_host_absolute_paths_for_toolsearch(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    toolsearch_entry = repo_root / "mcp-servers/toolsearch/dist/src/index.js"
    if not toolsearch_entry.exists():
        pytest.skip(
            "ToolSearch build output is missing; run `cd mcp-servers/toolsearch && npm test` first"
        )
    if _working_node() is None:
        pytest.skip("Node.js is required for ToolSearch stdio smoke test")

    missing_host_root = tmp_path / "host" / repo_root.name
    missing_node = tmp_path / "missing-nvm" / "bin" / "node"
    config_path = tmp_path / "mcp_config.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "toolsearch",
                        "type": "stdio",
                        "enabled": True,
                        "command": str(missing_node),
                        "args": ["mcp-servers/toolsearch/dist/src/index.js"],
                        "cwd": str(missing_host_root),
                        "env": {
                            "TOOL_CATALOG_PATH": str(
                                missing_host_root / "config/tool_catalog.json"
                            )
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    manager = MCPManager()
    try:
        await manager.connect_all(str(config_path))
        tools = await manager.list_tools()
        tool_names = {tool["name"] for tool in tools}
        assert "toolsearch" in tool_names
        assert "tool_get" in tool_names
    finally:
        await manager.disconnect_all()


def test_mcp_server_connection_repo_root_handles_container_layout(tmp_path, monkeypatch):
    runtime_root = tmp_path / "app"
    manager_file = runtime_root / "app/mcp/manager.py"
    manager_file.parent.mkdir(parents=True)
    manager_file.write_text("", encoding="utf-8")
    (runtime_root / "config").mkdir()
    (runtime_root / "mcp-servers").mkdir()

    monkeypatch.setattr(manager_module, "__file__", str(manager_file))

    assert MCPServerConnection._repo_root() == runtime_root


def test_mcp_server_connection_translates_host_paths_in_container_layout(tmp_path, monkeypatch):
    runtime_root = tmp_path / "app"
    manager_file = runtime_root / "app/mcp/manager.py"
    manager_file.parent.mkdir(parents=True)
    manager_file.write_text("", encoding="utf-8")
    (runtime_root / "config").mkdir()
    (runtime_root / "mcp-servers").mkdir()
    catalog_path = runtime_root / "config/tool_catalog.json"
    catalog_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(manager_module, "__file__", str(manager_file))

    missing_host_root = tmp_path / "missing-host" / "ding-robot"
    assert (
        MCPServerConnection._resolve_optional_path(str(missing_host_root))
        == runtime_root
    )
    assert (
        MCPServerConnection._translate_missing_repo_path(
            missing_host_root / "config/tool_catalog.json"
        )
        == catalog_path
    )


def _working_node() -> str | None:
    candidates = []
    path_node = shutil.which("node")
    if path_node:
        candidates.append(Path(path_node))
    candidates.extend(Path.home().glob(".nvm/versions/node/*/bin/node"))

    seen = set()
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        seen.add(candidate_str)
        try:
            subprocess.run([candidate_str, "--version"], check=True, capture_output=True, text=True)
        except Exception:
            continue
        return candidate_str
    return None
