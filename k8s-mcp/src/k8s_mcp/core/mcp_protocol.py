"""
MCP (Model Context Protocol) 协议实现

基于MCP标准实现的协议层，用于K8s MCP服务器与客户端的通信
"""

import json
import uuid
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class MCPErrorCode(Enum):
    """MCP错误代码"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # 自定义错误代码
    TOOL_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002
    AUTHENTICATION_ERROR = -32003
    AUTHORIZATION_ERROR = -32004
    RESOURCE_NOT_FOUND = -32005
    VALIDATION_ERROR = -32006


class MCPMethod(Enum):
    """MCP方法枚举"""
    INITIALIZE = "initialize"
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    PING = "ping"
    NOTIFICATIONS = "notifications"


class MCPToolSchema(BaseModel):
    """MCP工具Schema定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Dict[str, Any] = Field(..., description="输入参数schema")


class MCPRequest(BaseModel):
    """MCP请求"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")
    method: str = Field(..., description="方法名")
    params: Optional[Dict[str, Any]] = Field(None, description="参数")
    id: Optional[Union[str, int]] = Field(None, description="请求ID")
    
    @classmethod
    def from_json(cls, data: str) -> "MCPRequest":
        """从JSON字符串创建请求"""
        try:
            return cls.model_validate_json(data)
        except Exception as e:
            logger.error(f"解析MCP请求失败: {e}")
            raise


class MCPResponse(BaseModel):
    """MCP响应"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC版本")
    result: Optional[Any] = Field(None, description="响应结果")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")
    id: Optional[Union[str, int]] = Field(None, description="请求ID")
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json(exclude_none=True)


class MCPServerInfo(BaseModel):
    """MCP服务器信息"""
    name: str = Field(..., description="服务器名称")
    version: str = Field(..., description="服务器版本")
    description: Optional[str] = Field(None, description="服务器描述")
    author: Optional[str] = Field(None, description="作者")
    homepage: Optional[str] = Field(None, description="主页")


class MCPServerCapabilities(BaseModel):
    """MCP服务器能力"""
    tools: bool = Field(default=True, description="支持工具调用")
    notifications: bool = Field(default=True, description="支持通知")
    logging: bool = Field(default=True, description="支持日志")
    resources: bool = Field(default=False, description="支持资源")
    prompts: bool = Field(default=False, description="支持提示")


class MCPInitializeRequest(BaseModel):
    """MCP初始化请求"""
    protocol_version: str = Field(..., description="协议版本")
    client_info: Dict[str, Any] = Field(..., description="客户端信息")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="客户端能力")


class MCPInitializeResult(BaseModel):
    """MCP初始化结果"""
    protocol_version: str = Field(..., description="协议版本")
    server_info: MCPServerInfo = Field(..., description="服务器信息")
    capabilities: MCPServerCapabilities = Field(..., description="服务器能力")


class MCPListToolsResult(BaseModel):
    """MCP工具列表结果"""
    tools: List[MCPToolSchema] = Field(..., description="工具列表")


class MCPCallToolRequest(BaseModel):
    """MCP工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")


class MCPCallToolResult(BaseModel):
    """MCP工具调用结果"""
    content: List[Dict[str, Any]] = Field(..., description="结果内容")
    is_error: bool = Field(default=False, description="是否错误")
    
    @classmethod
    def success(cls, content: Union[str, Dict[str, Any]]) -> "MCPCallToolResult":
        """创建成功结果"""
        if isinstance(content, str):
            return cls(content=[{"type": "text", "text": content}])
        else:
            return cls(content=[{"type": "text", "text": json.dumps(content, ensure_ascii=False, indent=2)}])
    
    @classmethod
    def error(cls, message: str, details: Any = None) -> "MCPCallToolResult":
        """创建错误结果"""
        error_content = {"error": message}
        if details:
            error_content["details"] = details
        
        return cls(
            content=[{"type": "text", "text": json.dumps(error_content, ensure_ascii=False, indent=2)}],
            is_error=True
        )


def create_success_response(result: Any, request_id: Optional[Union[str, int]] = None) -> MCPResponse:
    """创建成功响应"""
    return MCPResponse(result=result, id=request_id)


def create_error_response(
    code: MCPErrorCode,
    message: str,
    data: Any = None,
    request_id: Optional[Union[str, int]] = None
) -> MCPResponse:
    """创建错误响应"""
    error = {
        "code": code.value,
        "message": message
    }
    if data is not None:
        error["data"] = data
    
    return MCPResponse(error=error, id=request_id)


def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())


def validate_mcp_request(data: Dict[str, Any]) -> bool:
    """验证MCP请求格式"""
    try:
        # 检查必需字段
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return False
        
        if "method" not in data:
            return False
        
        # 检查ID字段类型
        if "id" in data:
            if not isinstance(data["id"], (str, int)):
                return False
        
        return True
    except Exception:
        return False


def format_tool_execution_result(
    tool_name: str,
    success: bool,
    result: Any = None,
    error: str = None,
    execution_time: float = None
) -> Dict[str, Any]:
    """格式化工具执行结果"""
    formatted_result = {
        "tool_name": tool_name,
        "success": success,
        "timestamp": datetime.now().isoformat(),
    }
    
    if execution_time is not None:
        formatted_result["execution_time"] = execution_time
    
    if success:
        formatted_result["result"] = result
    else:
        formatted_result["error"] = error
    
    return formatted_result


def create_tool_call_result(
    tool_name: str,
    success: bool,
    result: Any = None,
    error: str = None,
    execution_time: float = None
) -> MCPCallToolResult:
    """创建工具调用结果"""
    formatted_result = format_tool_execution_result(
        tool_name=tool_name,
        success=success,
        result=result,
        error=error,
        execution_time=execution_time
    )
    
    if success:
        return MCPCallToolResult.success(formatted_result)
    else:
        return MCPCallToolResult.error(f"工具 {tool_name} 执行失败", formatted_result)


def parse_tool_arguments(arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """解析和验证工具参数"""
    # 这里可以添加更复杂的参数验证逻辑
    # 目前只做基本的类型检查
    
    if not isinstance(arguments, dict):
        raise ValueError("参数必须是字典类型")
    
    # 检查必需参数
    required_params = schema.get("required", [])
    for param in required_params:
        if param not in arguments:
            raise ValueError(f"缺少必需参数: {param}")
    
    # 检查参数类型
    properties = schema.get("properties", {})
    for param, value in arguments.items():
        if param in properties:
            param_schema = properties[param]
            expected_type = param_schema.get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"参数 {param} 必须是字符串类型")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"参数 {param} 必须是数字类型")
            elif expected_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"参数 {param} 必须是布尔类型")
            elif expected_type == "array" and not isinstance(value, list):
                raise ValueError(f"参数 {param} 必须是数组类型")
            elif expected_type == "object" and not isinstance(value, dict):
                raise ValueError(f"参数 {param} 必须是对象类型")
    
    return arguments


class MCPProtocolHandler:
    """MCP协议处理器"""
    
    def __init__(self, server_info: MCPServerInfo, capabilities: MCPServerCapabilities):
        """初始化协议处理器"""
        self.server_info = server_info
        self.capabilities = capabilities
        self.protocol_version = "2024-11-05"
        
        logger.info(f"MCP协议处理器初始化完成: {server_info.name} v{server_info.version}")
    
    def handle_initialize(self, request: MCPInitializeRequest) -> MCPInitializeResult:
        """处理初始化请求"""
        logger.info(f"处理初始化请求: {request.client_info}")
        
        return MCPInitializeResult(
            protocol_version=self.protocol_version,
            server_info=self.server_info,
            capabilities=self.capabilities
        )
    
    def validate_protocol_version(self, version: str) -> bool:
        """验证协议版本兼容性"""
        # 这里可以添加更复杂的版本兼容性检查
        supported_versions = ["2024-11-05", "2024-10-07"]
        return version in supported_versions
    
    def create_notification(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建通知消息"""
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
    
    def log_request(self, request: MCPRequest, response: MCPResponse = None, error: Exception = None):
        """记录请求日志"""
        log_data = {
            "method": request.method,
            "request_id": request.id,
            "timestamp": datetime.now().isoformat()
        }
        
        if response:
            log_data["response_type"] = "success" if response.result else "error"
        
        if error:
            log_data["error"] = str(error)
        
        logger.info(f"MCP请求日志: {log_data}")


def create_k8s_mcp_protocol_handler() -> MCPProtocolHandler:
    """创建K8s MCP协议处理器"""
    server_info = MCPServerInfo(
        name="k8s-mcp",
        version="1.0.0",
        description="Kubernetes MCP服务器 - 提供真实的K8s集群操作支持",
        author="K8s MCP Team",
        homepage="https://github.com/example/k8s-mcp"
    )
    
    capabilities = MCPServerCapabilities(
        tools=True,
        notifications=True,
        logging=True,
        resources=False,
        prompts=False
    )
    
    return MCPProtocolHandler(server_info, capabilities) 