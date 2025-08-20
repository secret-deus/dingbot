"""
钉钉机器人 + LLM + MCP 集成系统
FastAPI v2 API 路由 - 核心业务逻辑
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

from ...mcp.enhanced_client import EnhancedMCPClient
from ...llm.processor import EnhancedLLMProcessor
from ...config.manager import ConfigManager
from ...mcp.types import MCPStats, MCPException
from ...utils.error_handler import ErrorHandler, StreamErrorHandler, handle_api_errors
from ...utils.monitoring import performance_monitor, debug_collector, request_tracking, debug_log

# 路由器
api_v2_router = APIRouter(prefix="/api/v2")

# 请求模型
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    stream: bool = Field(default=True, description="是否流式输出")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    tools: Optional[List[str]] = Field(default=None, description="指定使用的工具")
    enable_tools: bool = Field(default=True, description="是否启用MCP工具")
    
class ConfigUpdateRequest(BaseModel):
    config_data: Dict[str, Any] = Field(..., description="配置数据")

# 获取全局服务实例（从main.py导入）
def get_mcp_client() -> Optional[EnhancedMCPClient]:
    from main import mcp_client
    return mcp_client

def get_llm_processor() -> EnhancedLLMProcessor:
    from main import llm_processor
    if not llm_processor:
        raise HTTPException(status_code=503, detail="LLM处理器未初始化")
    return llm_processor

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

@api_v2_router.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 安全地获取组件
        mcp_client = None
        llm_processor = None
        
        try:
            mcp_client = get_mcp_client()
        except Exception as e:
            logger.warning(f"获取MCP客户端失败: {e}")
        
        try:
            llm_processor = get_llm_processor()
        except Exception as e:
            logger.warning(f"获取LLM处理器失败: {e}")
        
        # 检查各组件状态
        tools_count = 0
        if mcp_client:
            try:
                tools = await mcp_client.list_tools()
                tools_count = len(tools)
            except Exception as e:
                logger.warning(f"获取工具列表失败: {e}")
        
        return {
            "healthy": True,
            "components": {
                "mcp_client": mcp_client is not None and hasattr(mcp_client, 'status') and mcp_client.status.name == "CONNECTED",
                "llm_processor": llm_processor is not None,
                "tools_available": tools_count
            },
            "version": "2.0",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")

@api_v2_router.post("/chat")
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

@api_v2_router.post("/chat/stream", summary="流式对话", tags=["Chat"])
async def stream_chat(
    request: ChatRequest,
    mcp_client: Optional[EnhancedMCPClient] = Depends(get_mcp_client),
    llm_processor: EnhancedLLMProcessor = Depends(get_llm_processor)
):
    """优化的流式对话接口"""
    import json
    import time
    
    try:
        logger.info(f"开始流式对话处理，消息长度: {len(request.message)}")
        
        # 验证消息不为空
        if not request.message or not request.message.strip():
            error_data = {
                "type": "error",
                "message": "消息内容不能为空",
                "error_code": "EMPTY_MESSAGE",
                "timestamp": time.time(),
                "suggestions": [
                    "请输入有效的消息内容",
                    "确保消息不只包含空格",
                    "尝试输入一个问题或指令"
                ]
            }
            
            async def generate_error():
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n"
                yield "data: [DONE]\n"
            
            return StreamingResponse(
                generate_error(),
                media_type="text/plain",
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
            try:
                logger.info("开始生成流式响应")
                
                # 使用stream_chat方法进行流式对话
                # 只有在前端启用工具且MCP客户端可用时才启用工具
                enable_tools = request.enable_tools and mcp_client is not None
                logger.info(f"MCP工具支持: {enable_tools} (前端请求: {request.enable_tools}, MCP客户端: {mcp_client is not None})")
                
                async for chunk in llm_processor.stream_chat(
                    request.message,
                    enable_tools=enable_tools
                ):
                    chunk_count += 1
                    
                    # 标准化SSE格式输出
                    if isinstance(chunk, str):
                        # 处理换行符：逐字符处理，将换行符转换为空的data行
                        if '\n' in chunk:
                            # 逐字符处理，构建正确的SSE格式
                            current_line = ""
                            for char in chunk:
                                if char == '\n':
                                    # 发送当前行内容（如果有）
                                    if current_line:
                                        yield f"data: {current_line}\n"
                                        current_line = ""
                                    # 发送空行代表换行符
                                    yield f"data: \n"
                                else:
                                    current_line += char
                            
                            # 发送剩余内容（如果有）
                            if current_line:
                                yield f"data: {current_line}\n"
                            
                            logger.debug(f"输出多行文本块 #{chunk_count}: {chunk.count(chr(10))} 个换行符")
                        elif chunk:  # 单行非空内容
                            yield f"data: {chunk}\n"
                            logger.debug(f"输出文本块 #{chunk_count}: {len(chunk)} 字符")
                        # 注意：空字符串chunk会被忽略，因为它们通常是无意义的
                    elif isinstance(chunk, dict):
                        # 结构化数据转JSON
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n"
                        logger.debug(f"输出结构化数据块 #{chunk_count}: {chunk.get('type', 'unknown')}")
                    else:
                        # 其他类型转字符串
                        chunk_str = str(chunk)
                        if chunk_str.strip():
                            yield f"data: {chunk_str}\n"
                            logger.debug(f"输出其他类型块 #{chunk_count}: {type(chunk)}")
                
                # 明确的结束标识
                yield "data: [DONE]\n"
                logger.info(f"流式响应完成，共输出 {chunk_count} 个块")
                
            except Exception as e:
                logger.error(f"流式响应生成失败: {e}", exc_info=True)
                
                # 使用统一错误处理系统
                ErrorHandler.log_error(e, context="stream_chat_generation")
                error_data = ErrorHandler.format_error_response(e, context="流式对话生成")
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n"
        
        # 返回优化的StreamingResponse
        return StreamingResponse(
            generate(),
            media_type="text/plain",
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

@api_v2_router.get("/tools", summary="获取MCP工具列表", tags=["MCP"])
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

# 配置管理相关的请求模型
class ConfigTestRequest(BaseModel):
    config_type: str  # "llm" or "mcp"
    config_data: Dict[str, Any]

# 导入配置管理器
from ...config.manager import config_manager, ConfigValidationError

# 导入MCP配置管理端点
from .endpoints.mcp import router as mcp_router
from .endpoints.inspection import router as inspection_router
from .endpoints.mcp_config import router as mcp_config_router
from .endpoints.mcp_config_update import router as mcp_config_update_router
from .endpoints.mcp_config_current import router as mcp_config_current_router

# 导入LLM配置管理端点
from .endpoints.llm_config import router as llm_config_router

# 注册MCP配置路由
api_v2_router.include_router(mcp_config_router)
api_v2_router.include_router(mcp_config_update_router)
api_v2_router.include_router(mcp_config_current_router)

# 注册LLM配置路由
api_v2_router.include_router(llm_config_router)

# 注册巡检路由
api_v2_router.include_router(inspection_router)

# 多供应商LLM配置管理API - 简化版本
@api_v2_router.get("/config/llm/providers", summary="获取LLM配置（简化版）")
async def get_llm_providers_config():
    """获取LLM配置（从环境变量）"""
    try:
        config_data = await config_manager.get_current_llm_config()
        return {
            "success": True,
            "data": config_data
        }
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@api_v2_router.post("/config/llm/providers", summary="LLM配置更新（暂不支持）")
async def save_llm_providers_config(config_data: dict):
    """LLM配置更新（暂不支持，返回提示信息）"""
    return {
        "success": False,
        "message": "配置更新功能暂不支持，请直接修改环境变量文件。此功能已列入开发计划。",
        "roadmap_note": "完整的配置管理功能将在v2.0版本中实现"
    }


@api_v2_router.get("/config/llm/providers/templates", summary="获取供应商模板（暂不支持）")
async def get_provider_templates():
    """获取供应商模板（暂不支持）"""
    return {
        "success": False,
        "message": "供应商模板功能暂不支持，请参考文档手动配置环境变量。",
        "roadmap_note": "供应商模板功能将在v2.0版本中实现"
    }


@api_v2_router.get("/llm/providers/available", summary="获取可用的LLM供应商列表")
async def get_available_providers():
    """获取可用的LLM供应商列表"""
    try:
        import sys
        main_module = sys.modules.get('main')
        if not main_module or not hasattr(main_module, 'llm_processor'):
            return {
                "success": False,
                "message": "LLM处理器未初始化",
                "data": {
                    "providers": {},
                    "current_provider": None
                }
            }
        
        llm_processor = getattr(main_module, 'llm_processor')
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
                "providers": providers,
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


@api_v2_router.post("/llm/providers/switch", summary="切换LLM供应商（暂不支持）")
async def switch_llm_provider(request: dict):
    """切换LLM供应商（暂不支持）"""
    return {
        "success": False,
        "message": "供应商切换功能暂不支持，请修改环境变量 LLM_PROVIDER 后重启服务。",
        "roadmap_note": "动态切换功能将在v2.0版本中实现"
    }


@api_v2_router.get("/llm/providers/stats", summary="获取供应商统计信息")
async def get_provider_stats():
    """获取供应商统计信息"""
    try:
        import sys
        main_module = sys.modules.get('main')
        if not main_module or not hasattr(main_module, 'llm_processor'):
            return {
                "success": False,
                "message": "LLM处理器未初始化",
                "data": {}
            }
        
        llm_processor = getattr(main_module, 'llm_processor')
        if not llm_processor:
            return {
                "success": False,
                "message": "LLM处理器不可用",
                "data": {}
            }
        
        return {
            "success": True,
            "data": getattr(llm_processor, 'provider_stats', {})
        }
    except Exception as e:
        logger.error(f"获取供应商统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 兼容性API：保留原有的单供应商接口，但内部使用简化逻辑
@api_v2_router.get("/config/llm", summary="获取LLM配置（兼容性接口）")
async def get_llm_config():
    """获取LLM配置（向后兼容）"""
    try:
        config_data = await config_manager.get_current_llm_config()
        return {
            "success": True,
            "data": config_data
        }
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@api_v2_router.get("/config/llm/runtime")
async def get_llm_runtime_config():
    """获取运行时实际生效的LLM配置"""
    try:
        # 获取环境变量配置
        saved_config = await config_manager.get_current_llm_config()
        
        # 尝试从运行时获取配置
        import sys
        main_module = sys.modules.get('main')
        runtime_config = None
        
        if main_module and hasattr(main_module, 'llm_processor'):
            llm_processor = getattr(main_module, 'llm_processor')
            if llm_processor and hasattr(llm_processor, 'config'):
                try:
                    # 简化版LLM处理器的config是字典类型
                    config = llm_processor.config
                    if isinstance(config, dict):
                        runtime_config = {
                            'enabled': config.get('enabled', True),
                            'provider': config.get('provider', 'unknown'),
                            'model': config.get('model', 'unknown'),
                            'api_key': "***" + config.get('api_key', '')[-4:] if len(config.get('api_key', '')) > 4 else "***",
                            'timeout': config.get('timeout', 30),
                            'temperature': config.get('temperature', 0.7),
                            'max_tokens': config.get('max_tokens', 2000),
                        }
                    else:
                        # 向后兼容：对象类型配置
                        runtime_config = {
                            'enabled': getattr(config, 'enabled', True),
                            'provider': getattr(config, 'provider', 'unknown'),
                            'model': getattr(config, 'model', 'unknown'),
                            'api_key': "***" + getattr(config, 'api_key', '')[-4:] if len(getattr(config, 'api_key', '')) > 4 else "***",
                            'timeout': getattr(config, 'timeout', 30),
                            'temperature': getattr(config, 'temperature', 0.7),
                            'max_tokens': getattr(config, 'max_tokens', 2000),
                        }
                except Exception as config_error:
                    logger.error(f"获取运行时配置时出错: {config_error}")
                    runtime_config = None
        
        # 隐藏保存配置中的敏感信息
        if "api_key" in saved_config and saved_config["api_key"]:
            saved_config["api_key"] = "***" + saved_config["api_key"][-4:] if len(saved_config["api_key"]) > 4 else "***"
        
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

@api_v2_router.get("/config/mcp")
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

@api_v2_router.put("/config/llm")
async def update_llm_config(request: ConfigUpdateRequest):
    """更新LLM配置（暂不支持）"""
    return {
        "success": False,
        "message": "LLM配置更新功能暂不支持，请直接修改环境变量文件后重启服务。",
        "roadmap_note": "完整的配置管理功能将在v2.0版本中实现",
        "timestamp": time.time()
    }

@api_v2_router.post("/config/llm/reload")
async def reload_llm_config():
    """重新加载LLM配置（暂不支持）"""
    return {
        "success": False,
        "message": "配置热重载功能暂不支持，请重启服务以应用新的环境变量配置。",
        "roadmap_note": "配置热重载功能将在v2.0版本中实现",
        "timestamp": time.time()
    }

@api_v2_router.put("/config/mcp")
async def update_mcp_config(request: ConfigUpdateRequest):
    """更新MCP配置（暂不支持）"""
    return {
        "success": False,
        "message": "MCP配置更新功能暂不支持，请直接修改环境变量文件后重启服务。",
        "roadmap_note": "完整的配置管理功能将在v2.0版本中实现",
        "timestamp": time.time()
    }

@api_v2_router.post("/config/test")
async def test_config(request: ConfigTestRequest):
    """测试配置连接性（暂不支持）"""
    return {
        "success": False,
        "message": "配置测试功能暂不支持。",
        "roadmap_note": "配置测试功能将在v2.0版本中实现",
        "timestamp": __import__('time').time()
    }

@api_v2_router.get("/config/providers")
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
@api_v2_router.get("/debug/performance", summary="获取性能统计", tags=["Debug"])
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

@api_v2_router.get("/debug/requests", summary="获取请求历史", tags=["Debug"])
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

@api_v2_router.get("/debug/logs", summary="获取调试日志", tags=["Debug"])
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

@api_v2_router.post("/debug/test", summary="测试端点", tags=["Debug"])
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