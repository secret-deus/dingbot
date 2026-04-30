"""工具执行抽象：默认走远程 MCP，可扩展为进程内工具。"""

from .registry import ToolExecutionBackend, MCPToolBackendAdapter, get_default_tool_backend

__all__ = [
    "ToolExecutionBackend",
    "MCPToolBackendAdapter",
    "get_default_tool_backend",
]
