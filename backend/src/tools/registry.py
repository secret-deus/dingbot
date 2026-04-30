"""
工具执行后端抽象：当前实现为远程 MCP 客户端适配器，便于后续迁入进程内 ToolRegistry。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from loguru import logger


@runtime_checkable
class ToolExecutionBackend(Protocol):
    async def list_tools(self) -> List[Any]:
        ...

    async def call_tool(
        self,
        name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        ...


class MCPToolBackendAdapter:
    """将 EnhancedMCPClient 适配为统一 ToolExecutionBackend。"""

    def __init__(self, mcp_client: Any):
        self._client = mcp_client

    async def list_tools(self) -> List[Any]:
        if not self._client:
            return []
        return await self._client.list_tools()

    async def call_tool(
        self,
        name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not self._client:
            raise RuntimeError("MCP 客户端未初始化")
        return await self._client.call_tool(name, parameters, context)


def get_default_tool_backend(mcp_client: Any) -> Optional[ToolExecutionBackend]:
    """返回当前进程默认工具后端；无 MCP 时返回 None。"""
    if mcp_client is None:
        logger.debug("无 MCP 客户端，工具后端不可用")
        return None
    return MCPToolBackendAdapter(mcp_client)
