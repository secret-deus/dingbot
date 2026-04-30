"""
进程内 K8s / ECS 工具（原独立 k8s-mcp、ecs-mcp 合并进主应用）。

环境变量 BUILTIN_K8S_ECS_TOOLS=true（默认）时注册并走本模块，不再依赖远程 SSE MCP。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Set

from loguru import logger

from src.mcp.runtime import LocalMCPRuntime
from src.mcp.types import MCPTool

_LOCAL_RUNTIME: Optional[LocalMCPRuntime] = None

# 与 config/mcp_config.json 中 name 对齐（无 implementation 字段时的回退）
DEFAULT_SKIP_REMOTE_SERVER_NAMES: frozenset[str] = frozenset(
    {"k8s-mcp", "ecs-sse-server"}
)


def builtin_k8s_ecs_tools_enabled() -> bool:
    return os.getenv("BUILTIN_K8S_ECS_TOOLS", "true").lower() == "true"


def skip_remote_server_names() -> Set[str]:
    raw = os.getenv("MCP_SKIP_REMOTE_SERVER_NAMES", "")
    if raw.strip():
        return {x.strip() for x in raw.split(",") if x.strip()}
    return set(DEFAULT_SKIP_REMOTE_SERVER_NAMES)


def resolved_skip_remote_server_names(config_manager: Any = None) -> Set[str]:
    """
    合并环境变量跳过集合 + mcp_config 中本地实现的服务器名。
    """
    names = set(skip_remote_server_names())
    cfg = getattr(config_manager, "current_config", None) if config_manager is not None else None
    if cfg and getattr(cfg, "servers", None):
        for s in cfg.servers:
            if getattr(s, "implementation", None) == "builtin" or getattr(s, "type", None) == "local":
                names.add(s.name)
    return names


def register_builtin_tools_once() -> None:
    if not builtin_k8s_ecs_tools_enabled():
        return
    try:
        _get_local_runtime().connect()
        logger.info("进程内 K8s/ECS 工具已注册（原独立 MCP Server 逻辑）")
    except Exception as e:
        logger.error(f"注册进程内 K8s/ECS 工具失败: {e}")
        raise


def _get_local_runtime() -> LocalMCPRuntime:
    global _LOCAL_RUNTIME
    if _LOCAL_RUNTIME is None:
        _LOCAL_RUNTIME = LocalMCPRuntime(enabled=builtin_k8s_ecs_tools_enabled())
    return _LOCAL_RUNTIME


def tool_is_builtin(name: str) -> bool:
    """当前工具是否由进程内 K8s/ECS registry 提供。"""
    if not builtin_k8s_ecs_tools_enabled():
        return False
    runtime = _get_local_runtime()
    runtime.connect()
    return runtime.has_tool(name)


def merge_builtin_mcptools() -> Dict[str, MCPTool]:
    """合并 K8s + ECS 工具为 MCPTool 映射（供 EnhancedMCPClient.tools）。"""
    out: Dict[str, MCPTool] = {}
    if not builtin_k8s_ecs_tools_enabled():
        return out
    try:
        return _get_local_runtime().connect()
    except Exception as e:
        logger.error(f"枚举进程内 K8s/ECS 工具失败: {e}")
        return out


async def execute_builtin_tool(name: str, parameters: Dict[str, Any]) -> Any:
    runtime = _get_local_runtime()
    runtime.connect()
    return await runtime.call_tool(name, parameters)
