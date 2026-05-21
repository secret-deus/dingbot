from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.mcp.manager import MCPManager


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
        assert health["toolsearch"]["catalog_total"] == 55
    finally:
        await manager.disconnect_all()


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
