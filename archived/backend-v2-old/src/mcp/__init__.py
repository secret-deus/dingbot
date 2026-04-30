"""
MCP 包初始化。
惰性加载子模块，避免 `import src.mcp.builtin_k8s_ecs` 等路径时拉全量依赖。
"""

from importlib import import_module as _import_module
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "config_manager":
        return _import_module(".config_manager", __name__)
    if name == "config":
        return _import_module(".config", __name__)
    if name == "enhanced_client":
        return _import_module(".enhanced_client", __name__)
    if name == "types":
        return _import_module(".types", __name__)
    if name == "MCPConfigManager":
        return _import_module(".config_manager", __name__).MCPConfigManager
    if name == "MCPConfiguration":
        return _import_module(".config", __name__).MCPConfiguration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "config_manager",
    "config",
    "enhanced_client",
    "types",
    "MCPConfigManager",
    "MCPConfiguration",
]
