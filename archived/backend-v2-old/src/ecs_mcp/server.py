"""
ECS MCP服务器 - 基于 FastAPI 的独立 HTTP 进程入口。

主应用默认在进程内注册 ECS 工具；无需启动本文件。保留用于调试或旧部署；
历史工程见 ``archived/ecs-mcp-standalone/``。
"""

import asyncio
import json
import sys
import time
import os
from typing import Dict, Any, Optional, Set
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from .config import get_config, ECSConfig
from .core.tool_registry import tool_registry
from .tools import register_all_tools


class ToolCallRequest(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    status: str
    message: str


class SSEEvent(BaseModel):
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


class ECSMCPServer:
    def __init__(self, config: Optional[ECSConfig] = None):
        self.config = config or get_config()
        self.app = FastAPI(title="ECS MCP Server", version="0.1.0")
        self.clients: Set[str] = set()
        self.event_queues: Dict[str, asyncio.Queue] = {}
        self.is_running = False
        self._setup_logging()
        self._setup_routes()
        logger.info("ECS MCP服务器初始化完成")

    def _setup_logging(self):
        logger.remove()
        logger.add(
            sys.stdout,
            level="DEBUG" if self.config.debug else "INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            colorize=True,
        )
        logger.add(
            "logs/ecs-mcp.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8",
        )

    def _serialize_result(self, result: Any) -> Any:
        try:
            if result is None:
                return None
            if isinstance(result, (str, int, float, bool)):
                return result
            if isinstance(result, (list, tuple)):
                return [self._serialize_result(x) for x in result]
            if isinstance(result, dict):
                return {k: self._serialize_result(v) for k, v in result.items()}
            if hasattr(result, "model_dump"):
                return result.model_dump()
            if hasattr(result, "dict"):
                return result.dict()
            return str(result)
        except Exception as e:
            logger.warning(f"序列化失败: {e}")
            return str(result)

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {
                "name": "ECS MCP Server",
                "version": "0.1.0",
                "protocol": "SSE",
                "status": "running" if self.is_running else "stopped",
            }

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "clients": len(self.clients),
            }

        @self.app.get("/tools")
        async def list_tools():
            try:
                tools = tool_registry.list_tools("ecs", enabled_only=True)
                return {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "category": getattr(tool, "category", "ecs"),
                            "input_schema": tool.get_schema().input_schema
                            if hasattr(tool, "get_schema")
                            else {},
                        }
                        for tool in tools
                    ],
                    "total_count": len(tools),
                    "last_updated": time.time(),
                }
            except Exception as e:
                logger.error(f"获取工具列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            start_time = time.time()
            try:
                logger.info(f"📥 收到工具调用请求: {request.name}")
                logger.debug(f"🔧 工具参数: {request.arguments}")
                asyncio.create_task(self._execute_tool_async(request, start_time))
                return ToolCallResponse(status="accepted", message="工具调用已接受，正在异步执行")
            except Exception as e:
                logger.error(f"工具调用处理失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tools/refresh")
        async def refresh_tools():
            """刷新工具列表（与 k8s-mcp 风格一致）"""
            try:
                logger.info("🔄 开始刷新ECS工具列表...")
                tool_registry.clear_category("ecs")
                count = register_all_tools()
                tools = tool_registry.list_tools("ecs", enabled_only=True)
                result = {
                    "success": True,
                    "message": f"成功刷新工具列表，注册了 {count} 个工具",
                    "tools_count": len(tools),
                    "tools": [
                        {"name": t.name, "description": t.description, "category": getattr(t, "category", "ecs")}
                        for t in tools
                    ],
                    "refreshed_at": time.time(),
                }
                # 广播工具列表更新事件
                await self._broadcast_event("tools_updated", result)
                return result
            except Exception as e:
                logger.error(f"刷新ECS工具列表失败: {e}")
                return {"success": False, "error": str(e), "refreshed_at": time.time()}

        @self.app.get("/events")
        async def sse_events(request: Request):
            return StreamingResponse(
                self._event_stream(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control",
                },
            )

    def _format_sse_event(self, event: str, data: Dict[str, Any]) -> str:
        try:
            json_data = json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError):
            serialized_data = self._serialize_result(data)
            json_data = json.dumps(serialized_data, ensure_ascii=False)
        return f"event: {event}\ndata: {json_data}\n\n"

    async def _broadcast_event(self, event: str, data: Dict[str, Any]):
        if not self.clients:
            return
        serialized_data = self._serialize_result(data)
        event_data = {"event": event, "data": serialized_data}
        for client_id in list(self.clients):
            try:
                if client_id in self.event_queues:
                    await self.event_queues[client_id].put(event_data)
            except Exception as e:
                logger.error(f"向客户端 {client_id} 发送事件失败: {e}")

    async def _event_stream(self, request: Request):
        client_id = str(time.time())
        self.clients.add(client_id)
        self.event_queues[client_id] = asyncio.Queue()
        logger.info(f"新的SSE客户端连接: {client_id}")
        try:
            yield self._format_sse_event("connected", {"client_id": client_id, "timestamp": time.time(), "server": "ECS MCP Server"})
            tools = tool_registry.list_tools("ecs", enabled_only=True)
            yield self._format_sse_event("tools_list", {"tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": getattr(t, "category", "ecs"),
                    "timeout": getattr(t, "timeout", None),
                    "input_schema": t.get_schema().input_schema if hasattr(t, "get_schema") else {}
                }
                for t in tools
            ]})
            while True:
                try:
                    event = await asyncio.wait_for(self.event_queues[client_id].get(), timeout=30.0)
                    yield self._format_sse_event(event["event"], event["data"])
                except asyncio.TimeoutError:
                    yield self._format_sse_event("heartbeat", {"timestamp": time.time()})
        except asyncio.CancelledError:
            logger.info(f"SSE客户端连接取消: {client_id}")
        except Exception as e:
            logger.error(f"SSE事件流错误: {e}")
        finally:
            self.clients.discard(client_id)
            self.event_queues.pop(client_id, None)
            logger.info(f"SSE客户端断开连接: {client_id}")

    async def _execute_tool_async(self, request: ToolCallRequest, start_time: float):
        try:
            result = await tool_registry.execute_tool(request.name, request.arguments)
            execution_time = time.time() - start_time
            if getattr(result, "is_error", False):
                await self._broadcast_event("tool_error", {"id": request.id, "tool": request.name, "error": str(result.content), "success": False, "execution_time": execution_time, "timestamp": time.time()})
                return
            result_data = self._serialize_result(result)
            await self._broadcast_event("tool_complete", {"id": request.id, "tool": request.name, "result": result_data, "success": True, "execution_time": execution_time, "timestamp": time.time()})
        except Exception as e:
            execution_time = time.time() - start_time
            await self._broadcast_event("tool_error", {"id": request.id, "tool": request.name, "error": str(e), "success": False, "execution_time": execution_time, "timestamp": time.time()})


def build_app() -> FastAPI:
    server = ECSMCPServer()
    try:
        count = register_all_tools()
        logger.info(f"已注册ECS工具数量: {count}")
    except Exception as e:
        logger.error(f"注册ECS工具失败: {e}")
    return server.app


# 供uvicorn --reload 导入
app = build_app()


def run():
    import uvicorn
    cfg = get_config()
    # 默认开启热重载；设置 ECS_MCP_RELOAD=false 可显式关闭
    reload_enabled = (os.getenv("ECS_MCP_RELOAD", "true").lower() == "true")
    logger.info(f"启动方式: {'reload' if reload_enabled else 'normal'}")
    uvicorn.run(
        "ecs_mcp.server:app",
        factory=False,
        host=cfg.host,
        port=cfg.port,
        reload=reload_enabled,
        log_level="info",
    )


if __name__ == "__main__":
    asyncio.run(main())
