"""
MCP配置管理模块
支持通过JSON配置文件管理MCP服务器和工具
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from .types import MCPClientConfig, MCPTool


class MCPServerConfig(BaseModel):
    """MCP服务器配置"""
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器类型", pattern="^(websocket|http|sse|stream_http|local|subprocess)$")
    enabled: bool = Field(True, description="是否启用")
    
    # WebSocket配置
    host: Optional[str] = Field(None, description="WebSocket主机")
    port: Optional[int] = Field(None, description="WebSocket端口")
    path: Optional[str] = Field(None, description="WebSocket路径")
    
    # HTTP配置
    base_url: Optional[str] = Field(None, description="HTTP基础URL")
    
    # SSE配置
    sse_url: Optional[str] = Field(None, description="SSE端点URL")
    
    # Stream HTTP配置
    stream_url: Optional[str] = Field(None, description="Stream HTTP端点URL")
    
    # 本地/子进程配置
    command: Optional[str] = Field(None, description="启动命令")
    args: Optional[List[str]] = Field(None, description="命令参数")
    cwd: Optional[str] = Field(None, description="工作目录")
    env: Optional[Dict[str, str]] = Field(None, description="环境变量")
    
    # 连接配置
    timeout: int = Field(30, description="连接超时时间(秒)")
    retry_attempts: int = Field(3, description="重试次数")
    retry_delay: int = Field(1, description="重试延迟(秒)")
    
    # 认证配置
    auth_type: Optional[str] = Field(None, description="认证类型")
    auth_token: Optional[str] = Field(None, description="认证令牌")
    auth_headers: Optional[Dict[str, str]] = Field(None, description="认证头")
    
    # 工具过滤
    enabled_tools: Optional[List[str]] = Field(None, description="启用的工具列表")
    disabled_tools: Optional[List[str]] = Field(None, description="禁用的工具列表")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['websocket', 'http', 'sse', 'stream_http', 'local', 'subprocess']
        if v not in valid_types:
            raise ValueError(f"Invalid server type: {v}. Must be one of {valid_types}")
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class MCPToolConfig(BaseModel):
    """MCP工具配置"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: Optional[str] = Field(None, description="工具分类")
    enabled: bool = Field(True, description="是否启用")
    server_name: Optional[str] = Field(None, description="所属服务器名称")
    
    # 参数配置
    input_schema: Dict[str, Any] = Field(..., description="输入参数schema")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    
    # 执行配置
    timeout: Optional[int] = Field(None, description="执行超时时间(秒)")
    cache_enabled: Optional[bool] = Field(None, description="是否启用缓存")
    cache_ttl: Optional[int] = Field(None, description="缓存TTL(秒)")
    
    # 权限配置
    required_permissions: Optional[List[str]] = Field(None, description="所需权限")
    allowed_users: Optional[List[str]] = Field(None, description="允许的用户")
    allowed_roles: Optional[List[str]] = Field(None, description="允许的角色")


class MCPConfiguration(BaseModel):
    """MCP完整配置"""
    version: str = Field("1.0", description="配置版本")
    name: str = Field("Default MCP Configuration", description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    
    # 全局配置
    global_config: MCPClientConfig = Field(default_factory=MCPClientConfig, description="全局客户端配置")
    
    # 服务器配置
    servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP服务器列表")
    
    # 工具配置
    tools: List[MCPToolConfig] = Field(default_factory=list, description="工具配置列表")
    
    # 路由配置
    tool_routing: Optional[Dict[str, str]] = Field(None, description="工具路由配置")
    
    # 安全配置
    security: Optional[Dict[str, Any]] = Field(None, description="安全配置")
    
    # 日志配置
    logging: Optional[Dict[str, Any]] = Field(None, description="日志配置")


# 延迟导入避免循环导入
def get_config_manager():
    """获取全局配置管理器实例 - 延迟导入避免循环依赖"""
    from .config_manager import get_mcp_config_manager
    return get_mcp_config_manager()


def set_config_manager(manager):
    """设置全局配置管理器实例 - 暂不支持"""
    logger.warning("set_config_manager function is deprecated, use get_config_manager() instead") 