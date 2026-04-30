"""
统一错误处理系统
提供错误分类、格式化和解决建议功能
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from enum import Enum


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    MCP_ERROR = "mcp_error"
    STREAM_ERROR = "stream_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """根据异常类型和消息分类错误"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 网络相关错误
        if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        
        # HTTP状态码相关错误
        if '401' in error_str or 'unauthorized' in error_str:
            return ErrorType.AUTHENTICATION_ERROR
        elif '403' in error_str or 'forbidden' in error_str:
            return ErrorType.AUTHORIZATION_ERROR
        elif '429' in error_str or 'rate limit' in error_str:
            return ErrorType.RATE_LIMIT_ERROR
        elif any(code in error_str for code in ['500', '502', '503', '504']):
            return ErrorType.SERVER_ERROR
        elif any(code in error_str for code in ['400', '404', '422']):
            return ErrorType.CLIENT_ERROR
        
        # MCP相关错误
        if 'mcp' in error_str or 'tool' in error_str:
            return ErrorType.MCP_ERROR
        
        # 流式处理错误
        if 'stream' in error_str or 'sse' in error_str:
            return ErrorType.STREAM_ERROR
        
        # 配置相关错误
        if any(keyword in error_str for keyword in ['config', 'api_key', 'credential']):
            return ErrorType.CONFIGURATION_ERROR
        
        # API相关错误
        if any(keyword in error_type for keyword in ['http', 'api', 'request']):
            return ErrorType.API_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def get_error_suggestions(error_type: ErrorType, error: Exception) -> List[str]:
        """根据错误类型提供解决建议"""
        suggestions = []
        
        if error_type == ErrorType.NETWORK_ERROR:
            suggestions.extend([
                "检查网络连接是否正常",
                "确认服务器地址是否正确",
                "尝试刷新页面重试",
                "检查防火墙设置"
            ])
        
        elif error_type == ErrorType.AUTHENTICATION_ERROR:
            suggestions.extend([
                "检查API密钥是否正确配置",
                "确认API密钥是否已过期",
                "重新生成API密钥",
                "检查认证方式是否正确"
            ])
        
        elif error_type == ErrorType.AUTHORIZATION_ERROR:
            suggestions.extend([
                "确认账户权限是否足够",
                "检查API密钥的权限范围",
                "联系管理员获取相应权限",
                "确认访问的资源是否存在"
            ])
        
        elif error_type == ErrorType.RATE_LIMIT_ERROR:
            suggestions.extend([
                "请求过于频繁，请稍后重试",
                "考虑增加请求间隔",
                "升级API套餐以获得更高限额",
                "检查是否有其他程序在并发请求"
            ])
        
        elif error_type == ErrorType.SERVER_ERROR:
            suggestions.extend([
                "服务器暂时不可用，请稍后重试",
                "检查服务器状态",
                "联系技术支持",
                "尝试使用备用服务器"
            ])
        
        elif error_type == ErrorType.CLIENT_ERROR:
            suggestions.extend([
                "检查请求参数是否正确",
                "确认请求格式是否符合要求",
                "查看API文档确认用法",
                "检查数据格式和类型"
            ])
        
        elif error_type == ErrorType.MCP_ERROR:
            suggestions.extend([
                "检查MCP服务器是否正常运行",
                "确认工具配置是否正确",
                "重启MCP服务器",
                "检查工具权限设置"
            ])
        
        elif error_type == ErrorType.STREAM_ERROR:
            suggestions.extend([
                "检查网络连接稳定性",
                "尝试刷新页面重新连接",
                "确认服务器支持流式传输",
                "检查浏览器兼容性"
            ])
        
        elif error_type == ErrorType.CONFIGURATION_ERROR:
            suggestions.extend([
                "检查配置文件格式是否正确",
                "确认所有必需参数已配置",
                "验证配置值的有效性",
                "参考配置文档示例"
            ])
        
        else:  # UNKNOWN_ERROR or API_ERROR
            suggestions.extend([
                "请稍后重试",
                "检查网络连接",
                "联系技术支持",
                "查看详细错误日志"
            ])
        
        return suggestions
    
    @staticmethod
    def format_error_response(
        error: Exception, 
        context: Optional[str] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """格式化错误响应"""
        error_type = ErrorHandler.classify_error(error)
        suggestions = ErrorHandler.get_error_suggestions(error_type, error)
        
        # 生成用户友好的错误消息
        user_message = ErrorHandler._get_user_friendly_message(error_type, error)
        
        response = {
            "type": "error",
            "error_type": error_type.value,
            "message": user_message,
            "original_error": str(error),
            "suggestions": suggestions,
            "timestamp": time.time(),
            "context": context
        }
        
        # 在开发环境中包含详细的错误信息
        if include_traceback:
            import traceback
            response["traceback"] = traceback.format_exc()
        
        return response
    
    @staticmethod
    def _get_user_friendly_message(error_type: ErrorType, error: Exception) -> str:
        """生成用户友好的错误消息"""
        error_messages = {
            ErrorType.NETWORK_ERROR: "网络连接失败，请检查网络状态",
            ErrorType.AUTHENTICATION_ERROR: "身份验证失败，请检查API密钥",
            ErrorType.AUTHORIZATION_ERROR: "权限不足，请联系管理员",
            ErrorType.RATE_LIMIT_ERROR: "请求过于频繁，请稍后重试",
            ErrorType.SERVER_ERROR: "服务器暂时不可用，请稍后重试",
            ErrorType.CLIENT_ERROR: "请求参数错误，请检查输入",
            ErrorType.MCP_ERROR: "工具调用失败，请检查MCP服务状态",
            ErrorType.STREAM_ERROR: "流式传输中断，请重新连接",
            ErrorType.CONFIGURATION_ERROR: "配置错误，请检查设置",
            ErrorType.API_ERROR: "API调用失败，请稍后重试",
            ErrorType.UNKNOWN_ERROR: "发生未知错误，请联系技术支持"
        }
        
        base_message = error_messages.get(error_type, "发生错误")
        
        # 如果原始错误消息比较简洁且有用，可以附加
        original_msg = str(error)
        if len(original_msg) < 100 and not any(
            keyword in original_msg.lower() 
            for keyword in ['traceback', 'exception', 'error:', 'failed:']
        ):
            return f"{base_message}: {original_msg}"
        
        return base_message
    
    @staticmethod
    def log_error(
        error: Exception, 
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """记录错误日志"""
        error_type = ErrorHandler.classify_error(error)
        
        log_data = {
            "error_type": error_type.value,
            "error_message": str(error),
            "context": context,
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": time.time()
        }
        
        # 根据错误严重程度选择日志级别
        if error_type in [ErrorType.SERVER_ERROR, ErrorType.UNKNOWN_ERROR]:
            logger.error(f"严重错误: {error}", extra=log_data, exc_info=True)
        elif error_type in [ErrorType.AUTHENTICATION_ERROR, ErrorType.AUTHORIZATION_ERROR]:
            logger.warning(f"认证/授权错误: {error}", extra=log_data)
        elif error_type in [ErrorType.RATE_LIMIT_ERROR, ErrorType.CLIENT_ERROR]:
            logger.info(f"客户端错误: {error}", extra=log_data)
        else:
            logger.warning(f"其他错误: {error}", extra=log_data)


class StreamErrorHandler:
    """流式响应专用错误处理器"""
    
    @staticmethod
    def format_stream_error(error: Exception, context: Optional[str] = None) -> str:
        """格式化流式响应中的错误"""
        error_response = ErrorHandler.format_error_response(error, context)
        
        # 返回JSON格式的错误数据，用于SSE传输
        import json
        return json.dumps(error_response, ensure_ascii=False)
    
    @staticmethod
    def create_error_chunk(message: str, error_type: str = "stream_error") -> str:
        """创建错误数据块"""
        error_data = {
            "type": "error",
            "error_type": error_type,
            "message": message,
            "timestamp": time.time()
        }
        
        import json
        return json.dumps(error_data, ensure_ascii=False)


# 简化的错误处理装饰器
def handle_api_errors(context: str = None):
    """API错误处理装饰器"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    ErrorHandler.log_error(e, context=context or func.__name__)
                    error_response = ErrorHandler.format_error_response(e, context)
                    
                    # 根据错误类型返回适当的HTTP状态码
                    from fastapi import HTTPException
                    error_type = ErrorHandler.classify_error(e)
                    
                    status_codes = {
                        ErrorType.AUTHENTICATION_ERROR: 401,
                        ErrorType.AUTHORIZATION_ERROR: 403,
                        ErrorType.CLIENT_ERROR: 400,
                        ErrorType.RATE_LIMIT_ERROR: 429,
                        ErrorType.SERVER_ERROR: 500,
                        ErrorType.CONFIGURATION_ERROR: 500,
                        ErrorType.MCP_ERROR: 503,
                        ErrorType.STREAM_ERROR: 500,
                        ErrorType.NETWORK_ERROR: 503,
                        ErrorType.API_ERROR: 500,
                        ErrorType.UNKNOWN_ERROR: 500
                    }
                    
                    status_code = status_codes.get(error_type, 500)
                    raise HTTPException(status_code=status_code, detail=error_response)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ErrorHandler.log_error(e, context=context or func.__name__)
                    error_response = ErrorHandler.format_error_response(e, context)
                    
                    from fastapi import HTTPException
                    error_type = ErrorHandler.classify_error(e)
                    
                    status_codes = {
                        ErrorType.AUTHENTICATION_ERROR: 401,
                        ErrorType.AUTHORIZATION_ERROR: 403,
                        ErrorType.CLIENT_ERROR: 400,
                        ErrorType.RATE_LIMIT_ERROR: 429,
                        ErrorType.SERVER_ERROR: 500,
                        ErrorType.CONFIGURATION_ERROR: 500,
                        ErrorType.MCP_ERROR: 503,
                        ErrorType.STREAM_ERROR: 500,
                        ErrorType.NETWORK_ERROR: 503,
                        ErrorType.API_ERROR: 500,
                        ErrorType.UNKNOWN_ERROR: 500
                    }
                    
                    status_code = status_codes.get(error_type, 500)
                    raise HTTPException(status_code=status_code, detail=error_response)
            return sync_wrapper
    return decorator