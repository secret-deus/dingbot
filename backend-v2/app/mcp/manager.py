"""MCP 连接管理器 - 管理多服务器连接、工具聚合与路由"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.core.config import get_settings
from app.mcp.builtin import BuiltinToolRegistry
from app.mcp.policy import ToolCatalogPolicy


class MCPServerConnection:
    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.config = config
        self.session: Any = None
        self._transport_context: Any = None
        self._session_context: Any = None
        self.tools: list[dict] = []
        self.connected = False

    async def connect(self) -> bool:
        transport = self.config.get("type", "sse")
        try:
            if transport == "sse":
                return await self._connect_sse()
            elif transport == "stdio":
                return await self._connect_stdio()
            else:
                logger.warning("不支持的传输类型: {}", transport)
                return False
        except Exception as e:
            logger.error("MCP 服务器 {} 连接失败: {}", self.name, e)
            self.connected = False
            return False

    async def _connect_sse(self) -> bool:
        try:
            from mcp.client.sse import sse_client
            from mcp import ClientSession

            host = self.config.get("host", "localhost")
            port = self.config.get("port", 8766)
            path = self.config.get("path", "/events")
            url = f"http://{host}:{port}{path}"

            self._transport_context = sse_client(url)
            read_stream, write_stream = await self._transport_context.__aenter__()
            self.session = ClientSession(read_stream, write_stream)
            self._session_context = self.session
            await self._session_context.__aenter__()
            await self.session.initialize()
            self.connected = True
            await self._load_tools()
            return True
        except Exception as e:
            logger.error("SSE 连接失败 {}: {}", self.name, e)
            self.connected = False
            return False

    async def _connect_stdio(self) -> bool:
        try:
            from mcp.client.stdio import StdioServerParameters, stdio_client
            from mcp import ClientSession

            command = self.config.get("command", "")
            args = self.config.get("args", [])
            cwd = self._resolve_optional_path(self.config.get("cwd"))
            env = self.config.get("env")
            server_params = StdioServerParameters(
                command=command,
                args=args,
                cwd=str(cwd) if cwd else None,
                env=env,
            )

            self._transport_context = stdio_client(server_params)
            read_stream, write_stream = await self._transport_context.__aenter__()
            self.session = ClientSession(read_stream, write_stream)
            self._session_context = self.session
            await self._session_context.__aenter__()
            await self.session.initialize()
            self.connected = True
            await self._load_tools()
            return True
        except Exception as e:
            logger.error("stdio 连接失败 {}: {}", self.name, e)
            self.connected = False
            return False

    async def _load_tools(self) -> None:
        if not self.session:
            return
        try:
            result = await self.session.list_tools()
            self.tools = [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "inputSchema": t.inputSchema or {},
                    "server": self.name,
                }
                for t in result.tools
            ]
            logger.info("MCP 服务器 {} 提供 {} 个工具", self.name, len(self.tools))
        except Exception as e:
            logger.error("加载工具列表失败 {}: {}", self.name, e)

    async def call_tool(self, name: str, arguments: dict) -> dict:
        if not self.session or not self.connected:
            return {"error": f"服务器 {self.name} 未连接"}
        try:
            result = await self.session.call_tool(name, arguments)
            if result.content:
                text_parts = [c.text for c in result.content if hasattr(c, "text")]
                return {"result": "\n".join(text_parts)}
            return {"result": str(result)}
        except Exception as e:
            logger.error("工具调用失败 {}/{}: {}", self.name, name, e)
            return {"error": str(e)}

    async def disconnect(self) -> None:
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception:
                pass
        if self._transport_context:
            try:
                await self._transport_context.__aexit__(None, None, None)
            except Exception:
                pass
        self.session = None
        self._session_context = None
        self._transport_context = None
        self.connected = False
        self.tools = []

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _resolve_optional_path(cls, value: Optional[str]) -> Optional[Path]:
        if not value:
            return None
        path = Path(value)
        if path.is_absolute():
            return path
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            return cwd_path
        return cls._repo_root() / path


class MCPManager:
    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConnection] = {}
        self._builtin = BuiltinToolRegistry()
        self._policy = ToolCatalogPolicy()
        self._tools_cache: list[dict] = []
        self._tool_server_map: dict[str, str] = {}

    async def connect_all(self, config_path: Optional[str] = None) -> None:
        settings = get_settings()
        path = config_path or settings.mcp_config_path
        servers_config = self._load_config(path)

        for srv in servers_config.get("servers", []):
            if not srv.get("enabled", False):
                continue
            if srv.get("implementation") == "builtin":
                logger.info("跳过内置 MCP 配置 {}，该工具组由进程内注册表加载", srv.get("name"))
                continue
            conn = MCPServerConnection(srv["name"], srv)
            ok = await conn.connect()
            if ok:
                self._servers[srv["name"]] = conn

        self._rebuild_cache()
        logger.info(
            "MCP 连接就绪: {} 个远程服务器, {} 个内置工具",
            len(self._servers),
            len(self._builtin.list_tools()),
        )

    async def disconnect_all(self) -> None:
        for conn in self._servers.values():
            await conn.disconnect()
        self._servers.clear()
        self._tools_cache.clear()
        self._tool_server_map.clear()

    async def list_tools(self, skill_id: Optional[str] = None) -> list[dict]:
        if skill_id:
            return self._filter_by_skill(skill_id)
        return self._tools_cache

    async def call_tool(
        self,
        name: str,
        arguments: dict,
        user: Optional[dict] = None,
    ) -> dict:
        decision = self._policy.authorize(name, user, arguments)
        if not decision.allowed:
            return {
                "error": "tool_execution_denied",
                "reason": decision.reason,
                "requires_confirmation": decision.requires_confirmation,
                "tool": name,
            }

        server_name = self._tool_server_map.get(name)
        if server_name == "builtin":
            return await self._builtin.call(name, arguments)
        if server_name and server_name in self._servers:
            return await self._servers[server_name].call_tool(name, arguments)
        if decision.metadata is not None:
            return {
                "error": "tool_unavailable",
                "reason": "tool_not_loaded",
                "message": f"工具 {name} 已在 catalog 中标记为可执行，但当前运行时未加载对应处理器",
                "tool": name,
            }
        return {"error": f"工具 {name} 未找到"}

    def authorize_tool_call(
        self,
        name: str,
        user: Optional[dict],
        arguments: Optional[dict[str, Any]] = None,
    ):
        return self._policy.authorize(name, user, arguments)

    async def health_check(self) -> dict:
        result = {}
        for name, conn in self._servers.items():
            health = {"connected": conn.connected, "tools": len(conn.tools)}
            if name == "toolsearch" and conn.connected:
                catalog_stats = await self._toolsearch_catalog_stats(conn)
                if catalog_stats:
                    health.update(catalog_stats)
            result[name] = health
        builtin_tools = self._builtin.list_tools()
        result["builtin"] = {
            "connected": True,
            "tools": len(builtin_tools),
            "available_tools": sum(1 for tool in builtin_tools if tool.get("available", True)),
            "unavailable_tools": sum(
                1 for tool in builtin_tools if not tool.get("available", True)
            ),
        }
        return result

    def reload_builtin(self) -> None:
        self._builtin = BuiltinToolRegistry()
        self._rebuild_cache()

    async def _toolsearch_catalog_stats(self, conn: MCPServerConnection) -> dict:
        response = await conn.call_tool("tool_categories", {})
        if "error" in response:
            return {}
        try:
            payload = json.loads(response.get("result", "{}"))
        except json.JSONDecodeError:
            return {}
        return {
            "catalog_total": payload.get("total", 0),
            "catalog_categories": payload.get("categories", []),
            "execution_policies": payload.get("executionPolicies", []),
        }

    def _load_config(self, path: str) -> dict:
        config_file = self._resolve_config_path(path)
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                return json.load(f)
        logger.warning("MCP 配置文件不存在: {}", path)
        return {"servers": []}

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _resolve_config_path(cls, path: str) -> Path:
        config_file = Path(path)
        if config_file.is_absolute():
            return config_file
        candidates = [
            Path.cwd() / config_file,
            cls._repo_root() / config_file,
            cls._repo_root() / "backend-v2" / config_file,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _rebuild_cache(self) -> None:
        self._tools_cache = []
        self._tool_server_map = {}

        for tool in self._builtin.list_tools():
            self._tools_cache.append(tool)
            self._tool_server_map[tool["name"]] = "builtin"

        for conn in self._servers.values():
            for tool in conn.tools:
                self._tools_cache.append(tool)
                self._tool_server_map[tool["name"]] = conn.name

    def _filter_by_skill(self, skill_id: str) -> list[dict]:
        skills_path = Path(get_settings().skills_config_path)
        if not skills_path.exists():
            return self._tools_cache
        with open(skills_path, encoding="utf-8") as f:
            skills = json.load(f)
        for skill in skills.get("skills", []):
            if skill.get("id") == skill_id:
                prefixes = skill.get("allowed_prefixes", [])
                if not prefixes:
                    return self._tools_cache
                return [
                    t for t in self._tools_cache if any(t["name"].startswith(p) for p in prefixes)
                ]
        return self._tools_cache
