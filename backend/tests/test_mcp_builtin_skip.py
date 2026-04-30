"""进程内 builtin 与远程跳过逻辑测试。"""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.mcp.enhanced_client import EnhancedMCPClient
from src.mcp.builtin_k8s_ecs import resolved_skip_remote_server_names
from src.mcp.config_manager import MCPConfigManager
from src.mcp.types import MCPConnectionStatus
from src.mcp.types import MCPException, MCPTool


def test_resolved_skip_includes_implementation_builtin():
    mock = MagicMock()
    s1 = MagicMock()
    s1.name = "k8s-mcp"
    s1.implementation = "builtin"
    s2 = MagicMock()
    s2.name = "ssh-x"
    s2.implementation = None
    mock.current_config.servers = [s1, s2]
    names = resolved_skip_remote_server_names(mock)
    assert "k8s-mcp" in names
    assert "ssh-x" not in names


class FakeConfigManager:
    def __init__(self, tool_configs=None, server_configs=None):
        self.tool_configs = tool_configs or {}
        self.server_configs = server_configs or {}
        self.current_config = MagicMock()
        self.current_config.servers = list(self.server_configs.values())

    def get_enabled_servers(self):
        return []

    def get_tool_by_name(self, name):
        return self.tool_configs.get(name)

    def get_server_by_name(self, name):
        return self.server_configs.get(name)

    def get_server_for_tool(self, name):
        return None


class FakeLocalRuntime:
    def __init__(self, tools=None, error=None):
        self.tools = tools or {}
        self.error = error

    def connect(self):
        return dict(self.tools)

    def has_tool(self, name):
        return name in self.tools

    async def call_tool(self, name, parameters):
        if self.error:
            raise self.error
        return {"ok": True, "name": name, "parameters": parameters}

    def snapshot(self):
        return SimpleNamespace(
            enabled=True,
            status="connected",
            providers=[],
            tool_count=len(self.tools),
            transport="local",
        )


def _tool(name):
    return MCPTool(name=name, description=f"{name} tool", input_schema={}, provider="builtin-k8s")


def test_local_tool_merge_updates_stats_and_respects_tool_enabled():
    disabled_tool_config = MagicMock()
    disabled_tool_config.enabled = False
    disabled_tool_config.server_name = "k8s-mcp"

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(tool_configs={"disabled": disabled_tool_config})
    )
    client.local_runtime = FakeLocalRuntime(
        tools={
            "enabled": _tool("enabled"),
            "disabled": _tool("disabled"),
        }
    )

    client._merge_builtin_tools()

    assert "enabled" in client.tools
    assert "disabled" not in client.tools
    assert client.builtin_tool_names == {"enabled"}
    assert client.stats.active_tools == 1


def test_local_tool_merge_applies_server_allow_and_deny_without_tool_config():
    server_config = MagicMock()
    server_config.enabled_tools = ["allowed"]
    server_config.disabled_tools = ["blocked"]

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"k8s-mcp": server_config})
    )
    client.local_runtime = FakeLocalRuntime(
        tools={
            "allowed": _tool("allowed"),
            "blocked": _tool("blocked"),
            "not-listed": _tool("not-listed"),
        }
    )

    client._merge_builtin_tools()

    assert set(client.tools) == {"allowed"}
    assert client.builtin_tool_names == {"allowed"}


def test_local_tool_merge_applies_custom_local_provider_server_allowlist():
    server_config = MagicMock()
    server_config.name = "prod-k8s-local"
    server_config.type = "local"
    server_config.provider = "k8s"
    server_config.implementation = None
    server_config.enabled_tools = ["allowed"]
    server_config.disabled_tools = None

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"prod-k8s-local": server_config})
    )
    client.local_runtime = FakeLocalRuntime(
        tools={
            "allowed": _tool("allowed"),
            "other": _tool("other"),
        }
    )

    client._merge_builtin_tools()

    assert set(client.tools) == {"allowed"}


def test_disabled_local_provider_server_hides_its_tools():
    server_config = MagicMock()
    server_config.name = "k8s-mcp"
    server_config.type = "local"
    server_config.provider = "k8s"
    server_config.implementation = "builtin"
    server_config.enabled = False
    server_config.enabled_tools = None
    server_config.disabled_tools = None

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"k8s-mcp": server_config})
    )
    client.local_runtime = FakeLocalRuntime(
        tools={
            "k8s-get-pods": _tool("k8s-get-pods"),
            "k8s-get-services": _tool("k8s-get-services"),
        }
    )

    client._merge_builtin_tools()

    assert client.tools == {}
    assert client.builtin_tool_names == set()


def test_refresh_tools_preserves_local_tools_after_remote_recollect():
    client = EnhancedMCPClient(config_manager=FakeConfigManager())
    client.local_runtime = FakeLocalRuntime(tools={"local-tool": _tool("local-tool")})
    client.tools["stale"] = _tool("stale")

    client._refresh_tools(warn_if_empty=False)

    assert "stale" not in client.tools
    assert "local-tool" in client.tools
    assert client.stats.active_tools == 1


def test_local_tool_error_updates_failure_stats():
    client = EnhancedMCPClient(config_manager=FakeConfigManager())
    client.local_runtime = FakeLocalRuntime(
        tools={"bad-tool": _tool("bad-tool")},
        error=MCPException("LOCAL_TOOL_FAILED", "bad input"),
    )
    client._merge_builtin_tools()

    with pytest.raises(MCPException):
        asyncio.run(client.call_tool("bad-tool", {}))

    assert client.stats.total_calls == 1
    assert client.stats.successful_calls == 0
    assert client.stats.failed_calls == 1


def test_local_tool_call_applies_default_parameters():
    tool_config = MagicMock()
    tool_config.enabled = True
    tool_config.server_name = "k8s-mcp"
    tool_config.default_parameters = {"namespace": "default", "lines": 20}
    tool_config.timeout = None

    server_config = MagicMock()
    server_config.enabled_tools = ["local-tool"]
    server_config.disabled_tools = None

    local_runtime = FakeLocalRuntime(tools={"local-tool": _tool("local-tool")})
    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(
            tool_configs={"local-tool": tool_config},
            server_configs={"k8s-mcp": server_config},
        )
    )
    client.local_runtime = local_runtime
    client._merge_builtin_tools()

    result = asyncio.run(client.call_tool("local-tool", {"lines": 50}))

    assert result["parameters"] == {"namespace": "default", "lines": 50}


def test_builtin_connect_server_refreshes_local_runtime_without_remote_connect():
    server_config = MagicMock()
    server_config.enabled = True
    server_config.enabled_tools = ["k8s-get-pods"]
    server_config.disabled_tools = None
    server_config.implementation = "builtin"

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"k8s-mcp": server_config})
    )
    client.local_runtime = FakeLocalRuntime(tools={"k8s-get-pods": _tool("k8s-get-pods")})

    result = asyncio.run(client.connect_server("k8s-mcp"))

    assert result is True
    assert "k8s-mcp" not in client.connections
    assert set(client.tools) == {"k8s-get-pods"}


def test_refresh_tools_skips_stale_remote_connection_for_builtin_server():
    server_config = MagicMock()
    server_config.enabled = True
    server_config.enabled_tools = ["k8s-get-pods"]
    server_config.disabled_tools = None
    server_config.implementation = "builtin"

    connection = MagicMock()
    connection.config.name = "k8s-mcp"
    connection.status = MCPConnectionStatus.CONNECTED
    connection.tools = {"remote-only": _tool("remote-only")}

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"k8s-mcp": server_config})
    )
    client.connections["k8s-mcp"] = connection
    client.local_runtime = FakeLocalRuntime(tools={"k8s-get-pods": _tool("k8s-get-pods")})

    client._refresh_tools()

    assert "remote-only" not in client.tools
    assert set(client.tools) == {"k8s-get-pods"}


def test_health_check_omits_stale_skipped_remote_connection():
    server_config = MagicMock()
    server_config.enabled = True
    server_config.enabled_tools = ["k8s-get-pods"]
    server_config.disabled_tools = None
    server_config.implementation = "builtin"
    server_config.type = "local"
    server_config.provider = "k8s"

    connection = MagicMock()
    connection.config.name = "k8s-mcp"
    connection.status = MCPConnectionStatus.CONNECTED
    connection.tools = {"remote-only": _tool("remote-only")}

    client = EnhancedMCPClient(
        config_manager=FakeConfigManager(server_configs={"k8s-mcp": server_config})
    )
    client.connections["k8s-mcp"] = connection
    client.local_runtime = FakeLocalRuntime(tools={"k8s-get-pods": _tool("k8s-get-pods")})
    client._refresh_tools()

    health = asyncio.run(client.health_check())

    assert health["servers"] == {}
    assert health["local_runtime"]["tool_count"] == 1


def _write_mcp_config(path, servers):
    path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "name": "test",
                "description": "test",
                "global_config": {},
                "servers": servers,
                "tools": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_validate_config_accepts_local_k8s_and_ecs(tmp_path):
    config_path = tmp_path / "mcp_config.json"
    _write_mcp_config(
        config_path,
        [
            {"name": "local-k8s", "type": "local", "provider": "k8s", "enabled": True},
            {"name": "local-ecs", "type": "local", "provider": "ecs", "enabled": True},
        ],
    )
    manager = MCPConfigManager(str(config_path))

    result = asyncio.run(manager.validate_config())

    assert result.valid is True
    assert result.errors == []
    assert result.server_status == {"local-k8s": "connected", "local-ecs": "connected"}


def test_validate_config_rejects_local_server_without_provider(tmp_path):
    config_path = tmp_path / "mcp_config.json"
    _write_mcp_config(
        config_path,
        [{"name": "broken-local", "type": "local", "enabled": True}],
    )
    manager = MCPConfigManager(str(config_path))

    result = asyncio.run(manager.validate_config())

    assert result.valid is False
    assert "本地MCP服务器 broken-local 缺少provider配置" in result.errors
