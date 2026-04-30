"""
进程内 Builtin 工具提供者抽象：K8s / ECS 各一实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from loguru import logger

from src.mcp.types import MCPException, MCPTool


def _schema_to_mcptool(schema: Any, provider: str) -> MCPTool:
    return MCPTool(
        name=schema.name,
        description=schema.description,
        input_schema=schema.input_schema,
        timeout=getattr(schema, "timeout", None),
        category=getattr(schema, "category", None),
        provider=provider,
    )


def _call_result_to_payload(result: Any) -> Any:
    """Convert legacy K8s/ECS MCPCallToolResult into the app-level payload."""
    parts = []
    for block in getattr(result, "content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    text = "\n".join(parts)
    if getattr(result, "is_error", False):
        try:
            import json

            payload = json.loads(text)
        except Exception:
            payload = {"message": text}
        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("error") or text
        else:
            message = text
        raise MCPException("LOCAL_TOOL_FAILED", str(message), details=payload)
    try:
        import json

        return json.loads(text)
    except Exception:
        return text


class BuiltinToolProvider(ABC):
    """单类进程内工具（如 K8s、ECS）的注册与枚举。"""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        ...

    @abstractmethod
    def register(self) -> None:
        ...

    @abstractmethod
    def list_mcptools(self) -> Dict[str, MCPTool]:
        ...

    @abstractmethod
    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        ...


class K8sBuiltinProvider(BuiltinToolProvider):
    @property
    def provider_id(self) -> str:
        return "builtin-k8s"

    def register(self) -> None:
        from src.k8s_mcp.tools import register_all_tools

        register_all_tools()

    def list_mcptools(self) -> Dict[str, MCPTool]:
        out: Dict[str, MCPTool] = {}
        from src.k8s_mcp.core.tool_registry import tool_registry as k8s_tr

        for t in k8s_tr.list_tools():
            try:
                sch = t.get_schema()
                out[t.name] = _schema_to_mcptool(sch, self.provider_id)
            except Exception as e:
                logger.warning(f"跳过 K8s 工具 schema: {t.name} — {e}")
        return out

    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        from src.k8s_mcp.core.tool_registry import tool_registry as k8s_tr

        tool = k8s_tr.get_tool(name)
        if not tool:
            raise KeyError(name)
        self._reset_disconnected_clients(tool)
        result = await k8s_tr.execute_tool(name, parameters)
        return _call_result_to_payload(result)

    def _reset_disconnected_clients(self, tool: Any, seen: set[int] | None = None) -> None:
        """Drop stale K8s clients so recovered clusters can reconnect."""
        seen = seen or set()
        marker = id(tool)
        if marker in seen:
            return
        seen.add(marker)

        k8s_client = getattr(tool, "k8s_client", None)
        if k8s_client is not None and not getattr(k8s_client, "connected", False):
            logger.info(f"重置未连接的 K8s 工具客户端: {tool.name}")
            setattr(tool, "k8s_client", None)

        for value in vars(tool).values():
            if value is None or isinstance(value, (str, bytes, int, float, bool, dict, list, tuple, set)):
                continue
            if hasattr(value, "k8s_client") or hasattr(value, "execute"):
                self._reset_disconnected_clients(value, seen)


class EcsBuiltinProvider(BuiltinToolProvider):
    @property
    def provider_id(self) -> str:
        return "builtin-ecs"

    def register(self) -> None:
        from src.ecs_mcp.tools import register_all_tools

        register_all_tools()

    def list_mcptools(self) -> Dict[str, MCPTool]:
        out: Dict[str, MCPTool] = {}
        from src.ecs_mcp.core.tool_registry import tool_registry as ecs_tr

        for t in ecs_tr.list_tools():
            try:
                sch = t.get_schema()
                out[t.name] = _schema_to_mcptool(sch, self.provider_id)
            except Exception as e:
                logger.warning(f"跳过 ECS 工具 schema: {t.name} — {e}")
        return out

    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        from src.ecs_mcp.core.tool_registry import tool_registry as ecs_tr

        if not ecs_tr.get_tool(name):
            raise KeyError(name)
        result = await ecs_tr.execute_tool(name, parameters)
        return _call_result_to_payload(result)


def default_builtin_providers() -> List[BuiltinToolProvider]:
    return [K8sBuiltinProvider(), EcsBuiltinProvider()]


def collect_builtin_mcptools(providers: List[BuiltinToolProvider] | None = None) -> Dict[str, MCPTool]:
    """合并多提供者工具映射；同名后者覆盖（ECS 在列表中靠后则覆盖 K8s，一般不会同名）。"""
    out: Dict[str, MCPTool] = {}
    for p in providers or default_builtin_providers():
        merged = p.list_mcptools()
        for k, v in merged.items():
            if k in out and out[k].provider != v.provider:
                logger.warning(f"进程内工具名冲突: {k} ({out[k].provider} <- {v.provider})")
            out[k] = v
    return out
