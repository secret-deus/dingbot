"""
MCP (Model Context Protocol) 类型定义 - Python版本
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MCPConnectionStatus(str, Enum):
    """MCP连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MCPTool(BaseModel):
    """MCP工具定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Dict[str, Any] = Field(..., description="输入参数schema")
    category: Optional[str] = Field(None, description="工具分类")
    version: Optional[str] = Field(None, description="工具版本")
    provider: Optional[str] = Field(None, description="工具提供者")


class MCPToolCall(BaseModel):
    """MCP工具调用请求"""
    id: str = Field(..., description="调用ID")
    name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    context: Optional[Dict[str, Any]] = Field(None, description="调用上下文")


class MCPError(BaseModel):
    """MCP错误信息"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(None, description="错误详情")


class MCPToolResult(BaseModel):
    """MCP工具调用结果"""
    id: str = Field(..., description="调用ID")
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="是否成功")
    result: Optional[Any] = Field(None, description="调用结果")
    error: Optional[MCPError] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间(ms)")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间戳")


class MCPClientConfig(BaseModel):
    """MCP客户端配置"""
    timeout: int = Field(default=30000, description="超时时间(ms)")
    retry_attempts: int = Field(default=3, description="重试次数")
    retry_delay: int = Field(default=1000, description="重试延迟(ms)")
    max_concurrent_calls: int = Field(default=5, description="最大并发调用数")
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    cache_timeout: int = Field(default=300000, description="缓存超时时间(ms)")


class MCPStats(BaseModel):
    """MCP统计信息"""
    total_calls: int = Field(default=0, description="总调用次数")
    successful_calls: int = Field(default=0, description="成功调用次数")
    failed_calls: int = Field(default=0, description="失败调用次数")
    average_execution_time: float = Field(default=0, description="平均执行时间")
    cache_hit_rate: float = Field(default=0, description="缓存命中率")
    active_tools: int = Field(default=0, description="活跃工具数")


class FunctionCall(BaseModel):
    """LLM函数调用"""
    name: str = Field(..., description="函数名称")
    arguments: str = Field(..., description="函数参数(JSON字符串)")


class FunctionCallResult(BaseModel):
    """LLM函数调用结果"""
    function_call: FunctionCall = Field(..., description="函数调用信息")
    result: Optional[Any] = Field(None, description="调用结果")
    error: Optional[str] = Field(None, description="错误信息")


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")
    function_call: Optional[FunctionCall] = Field(None, description="函数调用")


class ProcessResult(BaseModel):
    """LLM处理结果"""
    content: str = Field(..., description="响应内容")
    function_calls: Optional[List[FunctionCallResult]] = Field(None, description="函数调用结果")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    usage: Optional[Dict[str, int]] = Field(None, description="Token使用情况")


class LLMProviderConfig(BaseModel):
    """单个LLM供应商配置"""
    name: str = Field(..., description="供应商显示名称")
    provider: Literal["openai", "azure", "anthropic", "zhipu", "qwen", "deepseek", "moonshot", "ollama", "custom"] = Field(..., description="供应商类型")
    enabled: bool = Field(default=True, description="是否启用此供应商")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    organization: Optional[str] = Field(None, description="组织ID (适用于OpenAI)")
    api_version: Optional[str] = Field(None, description="API版本 (适用于Azure)")
    deployment_name: Optional[str] = Field(None, description="部署名称 (适用于Azure)")
    timeout: Optional[int] = Field(default=30, description="请求超时时间(秒)")
    max_retries: Optional[int] = Field(default=3, description="最大重试次数")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大Token数")
    proxy_url: Optional[str] = Field(None, description="代理URL")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="自定义请求头")
    stream: bool = Field(default=False, description="是否使用流式输出")
    
    # 供应商特定配置
    icon: Optional[str] = Field(None, description="供应商图标")
    description: Optional[str] = Field(None, description="供应商描述")
    support_functions: bool = Field(default=True, description="是否支持函数调用")
    support_vision: bool = Field(default=False, description="是否支持视觉功能")


class LLMConfig(BaseModel):
    """LLM多供应商配置"""
    providers: Dict[str, LLMProviderConfig] = Field(default_factory=dict, description="供应商配置字典")
    default_provider: str = Field(default="openai", description="默认供应商")
    enabled: bool = Field(default=True, description="是否启用LLM功能")
    
    def get_provider(self, provider_id: str) -> Optional[LLMProviderConfig]:
        """获取指定供应商配置"""
        return self.providers.get(provider_id)
    
    def get_enabled_providers(self) -> Dict[str, LLMProviderConfig]:
        """获取所有启用的供应商"""
        return {k: v for k, v in self.providers.items() if v.enabled}
    
    def add_provider(self, provider_id: str, config: LLMProviderConfig):
        """添加供应商"""
        self.providers[provider_id] = config
    
    def remove_provider(self, provider_id: str):
        """移除供应商"""
        if provider_id in self.providers:
            del self.providers[provider_id]
            # 如果删除的是默认供应商，自动选择第一个可用的
            if self.default_provider == provider_id and self.providers:
                self.default_provider = next(iter(self.providers.keys()))


# 保留单个供应商配置类，用于向后兼容
class LegacyLLMConfig(BaseModel):
    """单个LLM供应商配置（向后兼容）"""
    enabled: bool = Field(default=True, description="是否启用LLM功能")
    provider: Literal["openai", "azure", "anthropic", "zhipu", "qwen", "deepseek", "moonshot", "ollama", "custom"] = Field(..., description="LLM提供商")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    organization: Optional[str] = Field(None, description="组织ID (适用于OpenAI)")
    api_version: Optional[str] = Field(None, description="API版本 (适用于Azure)")
    deployment_name: Optional[str] = Field(None, description="部署名称 (适用于Azure)")
    timeout: Optional[int] = Field(default=30, description="请求超时时间(秒)")
    max_retries: Optional[int] = Field(default=3, description="最大重试次数")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大Token数")
    proxy_url: Optional[str] = Field(None, description="代理URL")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="自定义请求头")
    stream: bool = Field(default=False, description="是否使用流式输出")


class MCPException(Exception):
    """MCP异常类"""
    
    def __init__(self, code: str, message: str, details: Any = None, tool_name: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details
        self.tool_name = tool_name
        super().__init__(f"{code}: {message}") 