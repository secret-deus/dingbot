"""
钉钉机器人 + LLM + MCP 集成系统
FastAPI v2 API 路由 - 核心业务逻辑
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, ConfigDict

from ...mcp.enhanced_client import EnhancedMCPClient
from ...llm.processor import EnhancedLLMProcessor
from ...config.manager import ConfigManager
from ...mcp.types import MCPStats, MCPException
from ...utils.error_handler import ErrorHandler, StreamErrorHandler, handle_api_errors
from ...utils.monitoring import performance_monitor, debug_collector, request_tracking, debug_log
from .stream_events import (
    encode_done,
    encode_sse_event,
    error_event,
    final_event,
    iter_sse_frames,
    normalize_stream_chunk,
)
from .dependencies import (
    get_mcp_client as resolve_mcp_client,
    get_llm_processor as resolve_llm_processor,
    get_runtime_container,
)
from .endpoints.ops import router as ops_router
from .endpoints.auth import router as auth_router
from .endpoints.users import router as users_router
from .endpoints.audit import router as audit_router
from .standard import success_envelope
from ...app.container import RuntimeContainer
from ...security.auth import CurrentUser, require_permission
from ...security.redaction import redact

# 路由器
api_v2_router = APIRouter(prefix="/api/v2")

# 请求模型
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    stream: bool = Field(default=True, description="是否流式输出")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    tools: Optional[List[str]] = Field(default=None, description="指定使用的工具")
    enable_tools: bool = Field(default=True, description="是否启用MCP工具")
    skill_id: Optional[str] = Field(
        default=None,
        description="项目内 Skill（config/skills.json），用于限制可调用的 MCP 工具",
    )


class MCPToolCallRequest(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict, description="MCP 工具参数")
    context: Optional[Dict[str, Any]] = Field(default=None, description="调用上下文")


READ_ONLY_MCP_TOOLS = {
    "k8s-get-nodes",
    "k8s-get-pods",
    "k8s-get-services",
    "k8s-get-events",
    "k8s-get-deployments",
    "k8s-cluster-summary",
    "k8s-relation-query",
    "ecs-list-instances",
}

# 获取运行时服务实例
def get_mcp_client(request: Request) -> Optional[EnhancedMCPClient]:
    return resolve_mcp_client(request)

def get_llm_processor(request: Request) -> EnhancedLLMProcessor:
    return resolve_llm_processor(request)

@api_v2_router.get("/status")
async def get_v2_status():
    """获取API v2状态信息"""
    try:
        return {
            "version": "2.0",
            "features": ["streaming", "config_management", "real_time_chat"],
            "api_version": "2024-01",
            "compatible_with": "v1",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取v2状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {e}")

@api_v2_router.get(
    "/skills",
    summary="列出项目内 Skill",
    tags=["Chat"],
    dependencies=[Depends(require_permission("chat:read"))],
)
async def list_skills():
    """返回 config/skills.json 中的 Skill 列表（只读）。"""
    try:
        from src.skills.registry import get_skill_registry

        reg = get_skill_registry()
        return {"default_skill_id": reg.default_skill_id, "skills": reg.list_public()}
    except Exception as e:
        logger.error(f"列出 Skill 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_v2_router.get("/health")
async def health_check(container: RuntimeContainer = Depends(get_runtime_container)):
    """健康检查接口"""
    try:
        # 安全地获取组件
        mcp_client = container.mcp_client
        llm_processor = container.llm_processor

        # 检查各组件状态
        tools_count = 0
        if mcp_client:
            try:
                tools = await mcp_client.list_tools()
                tools_count = len(tools)
            except Exception as e:
                logger.warning(f"获取工具列表失败: {e}")

        # 检查钉钉机器人状态（通过环境变量）
        dingtalk_bot_status = False
        try:
            import os
            webhook_url = os.getenv("DINGTALK_WEBHOOK_URL")
            dingtalk_bot_status = webhook_url is not None and webhook_url.strip() != ""
            logger.info(f"钉钉机器人状态: {dingtalk_bot_status}")
        except Exception as e:
            logger.warning(f"获取钉钉机器人状态失败: {e}")

        return {
            "healthy": True,
            "components": {
                "mcp_client": mcp_client is not None and hasattr(mcp_client, 'status') and mcp_client.status.name == "CONNECTED",
                "llm_processor": llm_processor is not None,
                "dingtalk_bot": dingtalk_bot_status,
                "tools_available": tools_count
            },
            "version": "2.0",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")

@api_v2_router.post("/chat", dependencies=[Depends(require_permission("chat:send"))])
async def chat(
    request: ChatRequest,
    llm_processor: EnhancedLLMProcessor = Depends(get_llm_processor)
):
    """普通聊天接口（非流式）"""
    try:
        result = await llm_processor.process_message(request.message)
        return {
            "response": result,
            "message_id": __import__('uuid').uuid4().hex,
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {e}")

@api_v2_router.post(
    "/chat/stream",
    summary="流式对话",
    tags=["Chat"],
    dependencies=[Depends(require_permission("chat:send"))],
)
async def stream_chat(
    request: ChatRequest,
    mcp_client: Optional[EnhancedMCPClient] = Depends(get_mcp_client),
    llm_processor: EnhancedLLMProcessor = Depends(get_llm_processor)
):
    """优化的流式对话接口"""
    try:
        logger.info(f"开始流式对话处理，消息长度: {len(request.message)}")

        # 验证消息不为空
        if not request.message or not request.message.strip():
            empty_message_error = error_event(
                "消息内容不能为空",
                code="EMPTY_MESSAGE",
                recoverable=True,
                suggestions=[
                    "请输入有效的消息内容",
                    "确保消息不只包含空格",
                    "尝试输入一个问题或指令"
                ],
            )

            async def generate_error():
                yield encode_sse_event(empty_message_error)
                yield encode_sse_event(final_event())
                yield encode_done()

            return StreamingResponse(
                generate_error(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "X-Accel-Buffering": "no",
                    "X-Content-Type-Options": "nosniff",
                }
            )

        # 验证工具
        if request.tools and mcp_client:
            available_tools = await mcp_client.list_tools()
            available_tool_names = [tool.name for tool in available_tools]
            invalid_tools = [tool for tool in request.tools if tool not in available_tool_names]
            if invalid_tools:
                raise HTTPException(
                    status_code=400,
                    detail=f"工具不存在: {', '.join(invalid_tools)}"
                )

        # 创建优化的流式响应生成器
        async def generate():
            chunk_count = 0
            tool_call_count = 0
            try:
                logger.info("开始生成流式响应")

                # 使用stream_chat方法进行流式对话
                # 只有在前端启用工具且MCP客户端可用时才启用工具
                enable_tools = request.enable_tools and mcp_client is not None
                logger.info(f"MCP工具支持: {enable_tools} (前端请求: {request.enable_tools}, MCP客户端: {mcp_client is not None})")

                from src.llm.crew_orchestrator import (
                    crewai_importable,
                    run_crew_chat_async,
                    use_crewai_enabled,
                )

                if (
                    use_crewai_enabled()
                    and enable_tools
                    and mcp_client
                    and not crewai_importable()
                ):
                    logger.warning(
                        "USE_CREWAI=true 但 crewai 未安装（常见于 Python 3.14：上游要求 <3.14），已使用 stream_chat"
                    )

                used_crew = False
                try:
                    if (
                        use_crewai_enabled()
                        and enable_tools
                        and mcp_client
                        and crewai_importable()
                    ):
                        text = await run_crew_chat_async(
                            request.message,
                            mcp_client,
                            llm_processor.config,
                            skill_id=request.skill_id,
                        )
                        used_crew = True
                        step = 400
                        for i in range(0, len(text), step):
                            part = text[i : i + step]
                            if part:
                                for frame in iter_sse_frames(normalize_stream_chunk(part)):
                                    yield frame
                except Exception as crew_err:
                    logger.error(f"CrewAI 路径失败，回退 stream_chat: {crew_err}", exc_info=True)
                    used_crew = False

                if used_crew:
                    yield encode_sse_event(final_event(tool_call_count=tool_call_count))
                    yield encode_done()
                    logger.info("流式响应完成（CrewAI）")
                    return

                async for chunk in llm_processor.stream_chat(
                    request.message,
                    enable_tools=enable_tools,
                    skill_id=request.skill_id,
                ):
                    chunk_count += 1

                    events = normalize_stream_chunk(chunk)
                    for event in events:
                        if event.get("type") == "tool_call_start":
                            tool_call_count += 1
                        yield encode_sse_event(event)

                # 明确的结束标识
                yield encode_sse_event(final_event(tool_call_count=tool_call_count))
                yield encode_done()
                logger.info(f"流式响应完成，共输出 {chunk_count} 个块")

            except Exception as e:
                logger.error(f"流式响应生成失败: {e}", exc_info=True)

                # 使用统一错误处理系统
                ErrorHandler.log_error(e, context="stream_chat_generation")
                error_data = ErrorHandler.format_error_response(e, context="流式对话生成")
                yield encode_sse_event(error_event(
                    error_data.get("message") or str(e),
                    code=error_data.get("error_code") or "STREAM_ERROR",
                    recoverable=True,
                    suggestions=error_data.get("suggestions"),
                ))
                yield encode_sse_event(final_event(tool_call_count=tool_call_count))
                yield encode_done()

        # 返回优化的StreamingResponse
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "X-Accel-Buffering": "no",  # 禁用nginx缓冲
                "X-Content-Type-Options": "nosniff",  # 防止MIME类型嗅探
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式对话初始化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话初始化失败: {e}")

@api_v2_router.get(
    "/tools",
    summary="获取MCP工具列表",
    tags=["MCP"],
    dependencies=[Depends(require_permission("mcp:read"))],
)
async def get_v2_tools(mcp_client: Optional[EnhancedMCPClient] = Depends(get_mcp_client)):
    """获取所有可用的MCP工具"""
    try:
        if not mcp_client:
            return {
                "tools": [],
                "total": 0,
                "timestamp": time.time(),
                "message": "MCP客户端未连接"
            }

        tools = await mcp_client.list_tools()
        return {
            "tools": [tool.model_dump() for tool in tools],
            "total": len(tools),
            "timestamp": time.time()
        }
    except MCPException as e:
        logger.error(f"获取工具失败: {e}")
        raise HTTPException(status_code=503, detail=f"获取工具失败: {e.message}")
    except Exception as e:
        logger.error(f"获取工具失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具失败: {e}")

@api_v2_router.post(
    "/tools/refresh",
    summary="刷新MCP工具列表",
    tags=["MCP"],
    dependencies=[Depends(require_permission("mcp:write"))],
)
async def refresh_v2_tools(mcp_client: Optional[EnhancedMCPClient] = Depends(get_mcp_client)):
    """强制刷新MCP工具列表"""
    try:
        if not mcp_client:
            return {
                "success": False,
                "message": "MCP客户端未连接",
                "timestamp": time.time()
            }

        logger.info("🔄 开始刷新MCP工具列表...")

        # 重新连接MCP服务器以刷新工具列表
        await mcp_client.connect()

        # 获取刷新后的工具列表
        tools = await mcp_client.list_tools()

        logger.info(f"✅ MCP工具列表刷新完成，当前有 {len(tools)} 个工具")

        return {
            "success": True,
            "message": f"成功刷新工具列表，当前有 {len(tools)} 个工具",
            "tools": [tool.model_dump() for tool in tools],
            "total": len(tools),
            "timestamp": time.time()
        }
    except MCPException as e:
        logger.error(f"刷新工具失败: {e}")
        return {
            "success": False,
            "error": f"刷新工具失败: {e.message}",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"刷新工具失败: {e}")
        return {
            "success": False,
            "error": f"刷新工具失败: {str(e)}",
            "timestamp": time.time()
        }


@api_v2_router.post(
    "/tools/{tool_name}/call",
    summary="调用 MCP 工具",
    tags=["MCP"],
    dependencies=[Depends(require_permission("mcp:read"))],
)
async def call_v2_tool(
    tool_name: str,
    payload: MCPToolCallRequest,
    request: Request,
    mcp_client: Optional[EnhancedMCPClient] = Depends(get_mcp_client),
    user: CurrentUser = Depends(require_permission("mcp:read")),
):
    """页面级 MCP 工具桥接接口，供拓扑/事故等工作台触发预置工具。"""
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP客户端未连接")

    if tool_name not in READ_ONLY_MCP_TOOLS and not user.can("mcp:write"):
        raise HTTPException(status_code=403, detail=f"工具 {tool_name} 需要 mcp:write 权限")

    try:
        if getattr(mcp_client, "status", None) and mcp_client.status.name != "CONNECTED":
            await mcp_client.connect()

        tools = await mcp_client.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}
        tool = tools_by_name.get(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")

        logger.info(
            "页面触发 MCP 工具: user={} tool={} params={}",
            user.username,
            tool_name,
            redact(payload.parameters),
        )
        start = time.time()
        result = await mcp_client.call_tool(
            tool_name,
            payload.parameters,
            context=payload.context,
        )
        duration_ms = round((time.time() - start) * 1000, 2)

        return success_envelope(
            request,
            {
                "tool": tool.model_dump(),
                "result": jsonable_encoder(result),
            },
            meta={
                "duration_ms": duration_ms,
                "elevated": tool_name not in READ_ONLY_MCP_TOOLS,
            },
        )
    except HTTPException:
        raise
    except MCPException as e:
        logger.error(f"MCP工具调用失败: {tool_name} {e}")
        raise HTTPException(status_code=502, detail=getattr(e, "message", str(e)))
    except Exception as e:
        logger.error(f"MCP工具调用异常: {tool_name} {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"工具调用失败: {e}")

# 配置管理相关的请求模型
class ConfigTestRequest(BaseModel):
    config_type: str  # "llm" or "mcp"
    config_data: Dict[str, Any]


class LegacyLLMConfigPutBody(BaseModel):
    """兼容前端：PUT /config/llm 携带 config_type + config_data。"""
    model_config = ConfigDict(extra="ignore")
    config_type: Optional[str] = None
    config_data: Dict[str, Any] = Field(..., description="完整 LLM 配置 JSON，与 LLMConfiguration 一致")

# 导入配置管理器
from ...config.manager import config_manager, ConfigValidationError

# 导入MCP配置管理端点
from .endpoints.mcp import router as mcp_router
from .endpoints.inspection import router as inspection_router
from .endpoints.mcp_config import router as mcp_config_router
from .endpoints.mcp_config_update import (
    router as mcp_config_update_router,
    update_mcp_config as persist_full_mcp_config,
    MCPConfigUpdateRequest as MCPFullConfigUpdateRequest,
)
from .endpoints.mcp_config_current import router as mcp_config_current_router

# 导入LLM配置管理端点
from .endpoints.llm_config import router as llm_config_router

# 导入任务调度管理端点
from .endpoints.scheduler import router as scheduler_router

# 导入资源告警管理端点
from .endpoints.alerts import router as alerts_router

# 导入资源管理端点
from .endpoints.resources import router as resources_router

# 注册MCP配置路由
api_v2_router.include_router(mcp_config_router)
api_v2_router.include_router(mcp_config_update_router)
api_v2_router.include_router(mcp_config_current_router)

# 注册LLM配置路由
api_v2_router.include_router(llm_config_router)

# 注册巡检路由
api_v2_router.include_router(inspection_router)

# 注册任务调度路由
api_v2_router.include_router(scheduler_router)

# 注册资源告警路由
api_v2_router.include_router(alerts_router)

# 注册资源管理路由
api_v2_router.include_router(resources_router)
api_v2_router.include_router(ops_router)
api_v2_router.include_router(auth_router)
api_v2_router.include_router(users_router)
api_v2_router.include_router(audit_router)

# 多供应商LLM配置管理API - 简化版本
@api_v2_router.get(
    "/config/llm/providers",
    summary="获取LLM配置（简化版）",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_llm_providers_config():
    """获取LLM配置（从环境变量）"""
    try:
        config_data = await config_manager.get_current_llm_config()
        return {
            "success": True,
            "data": redact(config_data)
        }
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@api_v2_router.post(
    "/config/llm/providers",
    summary="LLM配置更新（暂不支持）",
    dependencies=[Depends(require_permission("llm:write"))],
)
async def save_llm_providers_config(config_data: dict):
    """LLM配置更新（暂不支持，返回提示信息）"""
    return {
        "success": False,
        "message": "配置更新功能暂不支持，请直接修改环境变量文件。此功能已列入开发计划。",
        "roadmap_note": "完整的配置管理功能将在v2.0版本中实现"
    }


@api_v2_router.get(
    "/config/llm/providers/templates",
    summary="获取供应商模板（暂不支持）",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_provider_templates():
    """获取供应商模板（暂不支持）"""
    return {
        "success": False,
        "message": "供应商模板功能暂不支持，请参考文档手动配置环境变量。",
        "roadmap_note": "供应商模板功能将在v2.0版本中实现"
    }


@api_v2_router.get(
    "/llm/providers/available",
    summary="获取可用的LLM供应商列表",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_available_providers(container: RuntimeContainer = Depends(get_runtime_container)):
    """获取可用的LLM供应商列表"""
    try:
        llm_processor = container.llm_processor
        if not llm_processor:
            return {
                "success": False,
                "message": "LLM处理器不可用",
                "data": {
                    "providers": {},
                    "current_provider": None
                }
            }

        # 检查处理器是否有必要的方法
        if not hasattr(llm_processor, 'get_available_providers'):
            logger.error("LLM处理器缺少get_available_providers方法")
            return {
                "success": False,
                "message": "LLM处理器版本不兼容",
                "data": {
                    "providers": {},
                    "current_provider": None
                }
            }

        providers = llm_processor.get_available_providers()
        current_provider_id = getattr(llm_processor, 'current_provider_id', None)

        return {
            "success": True,
            "data": {
                "providers": redact(providers),
                "current_provider": current_provider_id
            }
        }
    except Exception as e:
        logger.error(f"获取可用供应商列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"获取供应商列表失败: {str(e)}",
            "data": {
                "providers": {},
                "current_provider": None
            }
        }


@api_v2_router.post(
    "/llm/providers/switch",
    summary="切换LLM供应商（暂不支持）",
    dependencies=[Depends(require_permission("llm:write"))],
)
async def switch_llm_provider(request: dict):
    """切换LLM供应商（暂不支持）"""
    return {
        "success": False,
        "message": "供应商切换功能暂不支持，请修改环境变量 LLM_PROVIDER 后重启服务。",
        "roadmap_note": "动态切换功能将在v2.0版本中实现"
    }


@api_v2_router.get(
    "/llm/providers/stats",
    summary="获取供应商统计信息",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_provider_stats(container: RuntimeContainer = Depends(get_runtime_container)):
    """获取供应商统计信息"""
    try:
        llm_processor = container.llm_processor
        if not llm_processor:
            return {
                "success": False,
                "message": "LLM处理器不可用",
                "data": {}
            }

        return {
            "success": True,
            "data": redact(getattr(llm_processor, 'provider_stats', {}))
        }
    except Exception as e:
        logger.error(f"获取供应商统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 兼容性API：保留原有的单供应商接口，但内部使用简化逻辑
@api_v2_router.get(
    "/config/llm",
    summary="获取LLM配置（兼容性接口）",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_llm_config():
    """获取LLM配置（向后兼容）"""
    try:
        config_data = await config_manager.get_current_llm_config()
        return {
            "success": True,
            "data": redact(config_data)
        }
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@api_v2_router.get(
    "/config/llm/runtime",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_llm_runtime_config(container: RuntimeContainer = Depends(get_runtime_container)):
    """获取运行时实际生效的LLM配置"""
    try:
        # 获取环境变量配置
        saved_config = await config_manager.get_current_llm_config()

        # 尝试从运行时获取配置
        runtime_config = None

        llm_processor = container.llm_processor
        if llm_processor and hasattr(llm_processor, 'config'):
            try:
                config = llm_processor.config
                if isinstance(config, dict):
                    runtime_config = redact({
                        'enabled': config.get('enabled', True),
                        'provider': config.get('provider', 'unknown'),
                        'model': config.get('model', 'unknown'),
                        'api_key': config.get('api_key', ''),
                        'timeout': config.get('timeout', 30),
                        'temperature': config.get('temperature', 0.7),
                        'max_tokens': config.get('max_tokens', 2000),
                    })
                else:
                    runtime_config = redact({
                        'enabled': getattr(config, 'enabled', True),
                        'provider': getattr(config, 'provider', 'unknown'),
                        'model': getattr(config, 'model', 'unknown'),
                        'api_key': getattr(config, 'api_key', ''),
                        'timeout': getattr(config, 'timeout', 30),
                        'temperature': getattr(config, 'temperature', 0.7),
                        'max_tokens': getattr(config, 'max_tokens', 2000),
                    })
            except Exception as config_error:
                logger.error(f"获取运行时配置时出错: {config_error}")
                runtime_config = None

        # 隐藏保存配置中的敏感信息
        saved_config = redact(saved_config)

        # 检查关键配置字段是否同步
        config_synced = False
        if runtime_config and saved_config:
            # 只比较关键字段
            key_fields = ['enabled', 'provider', 'model', 'timeout', 'temperature', 'max_tokens']
            config_synced = all(
                runtime_config.get(field) == saved_config.get(field)
                for field in key_fields
            )

        return {
            "success": True,
            "runtime_config": runtime_config,
            "saved_config": saved_config,
            "config_synced": config_synced,
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        logger.error(f"获取LLM运行时配置失败: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "message": f"获取运行时配置失败: {str(e)}",
            "runtime_config": None,
            "saved_config": None,
            "config_synced": False,
            "timestamp": __import__('time').time()
        }

@api_v2_router.get(
    "/config/mcp",
    dependencies=[Depends(require_permission("mcp:read"))],
)
async def get_mcp_config():
    """获取当前MCP配置"""
    try:
        config = await config_manager.get_current_mcp_config()
        return {
            "success": True,
            "config": config,
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        logger.error(f"获取MCP配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")

@api_v2_router.put(
    "/config/llm",
    dependencies=[Depends(require_permission("llm:write"))],
)
async def update_llm_config_compat(
    body: LegacyLLMConfigPutBody,
    container: RuntimeContainer = Depends(get_runtime_container),
):
    """更新 LLM 配置并重建运行时处理器（与 /api/v2/llm/config/update 行为一致）。"""
    from ...llm.config import LLMConfiguration
    from ...llm.config_manager import get_llm_config_manager

    mgr = get_llm_config_manager()
    config_data = body.config_data
    existing_by_id = {provider.id: provider for provider in mgr.get_config().providers}
    for provider in config_data.get("providers", []):
        existing = existing_by_id.get(provider.get("id"))
        if not existing:
            continue
        incoming_key = provider.get("api_key")
        incoming_base_url = provider.get("base_url")
        if not incoming_key or incoming_key == "***":
            provider["api_key"] = existing.api_key
        if not incoming_base_url or incoming_base_url == "***":
            provider["base_url"] = existing.base_url

    try:
        cfg = LLMConfiguration.model_validate(config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {e}") from e
    if not mgr.update_config(cfg):
        raise HTTPException(status_code=500, detail="保存 LLM 配置失败")
    await container.recreate_llm_processor()
    return {
        "success": True,
        "message": "LLM 配置已保存并应用到运行时",
        "timestamp": time.time(),
    }


@api_v2_router.post(
    "/config/llm/reload",
    dependencies=[Depends(require_permission("llm:write"))],
)
async def reload_llm_config_compat(container: RuntimeContainer = Depends(get_runtime_container)):
    """从磁盘重新加载 LLM 配置并重建处理器。"""
    await container.recreate_llm_processor()
    return {
        "success": True,
        "message": "已从磁盘重新加载 LLM 配置并重建处理器",
        "timestamp": time.time(),
    }


@api_v2_router.put(
    "/config/mcp",
    dependencies=[Depends(require_permission("mcp:write"))],
)
async def update_mcp_config_compat(
    request: MCPFullConfigUpdateRequest,
    background_tasks: BackgroundTasks,
):
    """写入 MCP 配置文件并触发客户端热重载（与 POST /api/v2/mcp/config/update 一致）。"""
    return await persist_full_mcp_config(request, background_tasks)


@api_v2_router.post(
    "/config/test",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def test_config(request: ConfigTestRequest):
    """引导使用专用校验与测试接口，避免重复实现。"""
    return {
        "success": False,
        "message": "请使用专用接口：LLM 校验 POST /api/v2/llm/config/validate；MCP 单服务测试 POST /api/v2/mcp/config/test/{server_name}",
        "config_type": request.config_type,
        "hints": {
            "llm_validate": "/api/v2/llm/config/validate",
            "mcp_test_server": "/api/v2/mcp/config/test/{server_name}",
        },
        "timestamp": time.time(),
    }

@api_v2_router.get(
    "/config/providers",
    dependencies=[Depends(require_permission("llm:read"))],
)
async def get_supported_providers():
    """获取支持的LLM提供商列表"""
    try:
        providers = {
            "llm_providers": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "description": "OpenAI GPT models",
                    "required_fields": ["api_key", "model"],
                    "optional_fields": ["base_url", "organization"],
                    "default_models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
                },
                {
                    "id": "azure",
                    "name": "Azure OpenAI",
                    "description": "Azure OpenAI Service",
                    "required_fields": ["api_key", "base_url", "deployment_name"],
                    "optional_fields": ["api_version"],
                    "default_models": ["gpt-35-turbo", "gpt-4"]
                },
                {
                    "id": "zhipu",
                    "name": "智谱AI",
                    "description": "智谱AI ChatGLM模型",
                    "required_fields": ["api_key"],
                    "optional_fields": ["base_url"],
                    "default_models": ["glm-4", "glm-3-turbo"]
                },
                {
                    "id": "qwen",
                    "name": "通义千问",
                    "description": "阿里云通义千问大模型",
                    "required_fields": ["api_key"],
                    "optional_fields": ["base_url"],
                    "default_models": ["qwen-turbo", "qwen-plus", "qwen-max"]
                },
                {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "description": "DeepSeek AI models",
                    "required_fields": ["api_key"],
                    "optional_fields": ["base_url"],
                    "default_models": ["deepseek-chat", "deepseek-coder"]
                },
                {
                    "id": "moonshot",
                    "name": "Moonshot AI",
                    "description": "月之暗面 Kimi 模型",
                    "required_fields": ["api_key"],
                    "optional_fields": ["base_url"],
                    "default_models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
                },
                {
                    "id": "ollama",
                    "name": "Ollama",
                    "description": "本地ollama服务，支持开源大模型",
                    "required_fields": ["model"],
                    "optional_fields": ["base_url"],
                    "default_models": ["llama2", "codellama", "llama2:13b", "mistral", "phi"]
                },
                {
                    "id": "custom",
                    "name": "自定义API",
                    "description": "兼容OpenAI API格式的自定义服务",
                    "required_fields": ["base_url", "model"],
                    "optional_fields": ["api_key"],
                    "default_models": ["custom-model"]
                }
            ]
        }

        return {
            "success": True,
            "data": providers,
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        logger.error(f"获取提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {e}")

# 调试和监控端点
@api_v2_router.get(
    "/debug/performance",
    summary="获取性能统计",
    tags=["Debug"],
    dependencies=[Depends(require_permission("debug:read"))],
)
async def get_performance_stats():
    """获取系统性能统计信息"""
    try:
        stats = performance_monitor.get_performance_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {e}")

@api_v2_router.get(
    "/debug/requests",
    summary="获取请求历史",
    tags=["Debug"],
    dependencies=[Depends(require_permission("debug:read"))],
)
async def get_request_history(limit: int = 50):
    """获取请求历史记录"""
    try:
        history = performance_monitor.get_request_history(limit)
        return {
            "success": True,
            "data": history,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取请求历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取请求历史失败: {e}")

@api_v2_router.get(
    "/debug/logs",
    summary="获取调试日志",
    tags=["Debug"],
    dependencies=[Depends(require_permission("debug:read"))],
)
async def get_debug_logs(request_id: Optional[str] = None):
    """获取调试日志信息"""
    try:
        debug_info = debug_collector.get_debug_info(request_id)
        return {
            "success": True,
            "data": debug_info,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取调试日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调试日志失败: {e}")

@api_v2_router.post(
    "/debug/test",
    summary="测试端点",
    tags=["Debug"],
    dependencies=[Depends(require_permission("debug:write"))],
)
async def debug_test_endpoint(test_data: Dict[str, Any]):
    """调试测试端点，用于测试各种功能"""
    try:
        # 模拟一些处理时间
        await asyncio.sleep(0.1)

        # 记录调试信息
        debug_collector.add_debug_log(
            level="INFO",
            message="调试测试端点被调用",
            context={"test_data": test_data}
        )

        return {
            "success": True,
            "message": "调试测试完成",
            "received_data": test_data,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"调试测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"调试测试失败: {e}")

# 包含MCP配置管理路由
api_v2_router.include_router(mcp_router)
