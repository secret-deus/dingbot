"""Local MCP runtime.

This module is the app-owned MCP execution boundary. It keeps K8s/ECS tools
in-process by default while preserving MCP-like tool schemas and call semantics.
Remote transports remain adapters behind EnhancedMCPClient instead of being the
primary runtime path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger

from src.mcp.builtin.providers import BuiltinToolProvider, default_builtin_providers
from src.mcp.types import MCPConnectionStatus, MCPException, MCPTool


@dataclass
class LocalMCPRuntimeSnapshot:
    """Serializable status for API surfaces and diagnostics."""

    enabled: bool
    status: str
    providers: List[Dict[str, Any]] = field(default_factory=list)
    tool_count: int = 0
    transport: str = "local"


class LocalMCPRuntime:
    """Register, list, and execute in-process MCP providers."""

    def __init__(
        self,
        providers: Optional[Iterable[BuiltinToolProvider]] = None,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self.providers: List[BuiltinToolProvider] = list(providers or default_builtin_providers())
        self.status = MCPConnectionStatus.DISCONNECTED
        self.tools: Dict[str, MCPTool] = {}
        self._tool_providers: Dict[str, BuiltinToolProvider] = {}
        self._registered = False

    def connect(self) -> Dict[str, MCPTool]:
        """Register local providers and refresh the tool map."""
        if not self.enabled:
            self.status = MCPConnectionStatus.DISCONNECTED
            self.tools.clear()
            self._tool_providers.clear()
            return {}

        try:
            self._register_once()
            self._refresh_tools()
            self.status = MCPConnectionStatus.CONNECTED if self.tools else MCPConnectionStatus.ERROR
            return dict(self.tools)
        except Exception as exc:
            self.status = MCPConnectionStatus.ERROR
            logger.error(f"Local MCP runtime 初始化失败: {exc}")
            raise MCPException("LOCAL_MCP_INIT_FAILED", str(exc)) from exc

    def _register_once(self) -> None:
        if self._registered:
            return
        for provider in self.providers:
            provider.register()
        self._registered = True
        logger.info("Local MCP providers registered: {}", [p.provider_id for p in self.providers])

    def _refresh_tools(self) -> None:
        self.tools.clear()
        self._tool_providers.clear()
        for provider in self.providers:
            provider_tools = provider.list_mcptools()
            for name, tool in provider_tools.items():
                if name in self.tools and self.tools[name].provider != tool.provider:
                    logger.warning(
                        "Local MCP tool conflict: {} ({} <- {})",
                        name,
                        self.tools[name].provider,
                        tool.provider,
                    )
                self.tools[name] = tool
                self._tool_providers[name] = provider

    def list_tools(self) -> List[MCPTool]:
        return list(self.tools.values())

    def has_tool(self, name: str) -> bool:
        return name in self.tools

    async def call_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        provider = self._tool_providers.get(name)
        if provider is None:
            raise MCPException("LOCAL_TOOL_NOT_FOUND", f"本地 MCP 工具不存在: {name}", tool_name=name)
        return await provider.execute_tool(name, parameters)

    def snapshot(self) -> LocalMCPRuntimeSnapshot:
        provider_rows = []
        for provider in self.providers:
            count = sum(1 for p in self._tool_providers.values() if p is provider)
            provider_rows.append(
                {
                    "id": provider.provider_id,
                    "transport": "local",
                    "tool_count": count,
                    "enabled": self.enabled,
                }
            )
        return LocalMCPRuntimeSnapshot(
            enabled=self.enabled,
            status=self.status.value,
            providers=provider_rows,
            tool_count=len(self.tools),
            transport="local",
        )
