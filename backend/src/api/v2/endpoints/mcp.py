"""
MCP配置管理API端点
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from src.mcp.config import get_config_manager
from src.mcp.config_manager import MCPConfigManager
from src.mcp.enhanced_client import EnhancedMCPClient


router = APIRouter(prefix="/mcp", tags=["MCP配置"])


class MCPConfigResponse(BaseModel):
    """MCP配置响应"""
    version: str
    name: str
    description: Optional[str]
    servers: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    tool_routing: Optional[Dict[str, str]]
    security: Optional[Dict[str, Any]]


class MCPServerStatusResponse(BaseModel):
    """MCP服务器状态响应"""
    overall_status: str
    total_tools: int
    servers: Dict[str, Dict[str, Any]]
    stats: Dict[str, Any]


class MCPToolResponse(BaseModel):
    """MCP工具响应"""
    name: str
    description: str
    category: Optional[str]
    enabled: bool
    input_schema: Dict[str, Any]
    server: Optional[str]


class MCPConfigUpdateRequest(BaseModel):
    """MCP配置更新请求"""
    config: Dict[str, Any]


def get_config_manager_dep() -> MCPConfigManager:
    """获取配置管理器依赖"""
    return get_config_manager()


@router.get("/config", response_model=MCPConfigResponse)
async def get_mcp_config(
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取MCP配置"""
    try:
        config = config_manager.get_config()
        
        return MCPConfigResponse(
            version=config.version,
            name=config.name,
            description=config.description,
            servers=[server.dict() for server in config.servers],
            tools=[tool.dict() for tool in config.tools],
            tool_routing=config.tool_routing,
            security=config.security
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP配置失败: {str(e)}")


@router.post("/config")
async def update_mcp_config(
    request: MCPConfigUpdateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """更新MCP配置"""
    try:
        # 验证配置
        from ...mcp.config import MCPConfiguration
        updated_config = MCPConfiguration(**request.config)
        
        # 保存配置
        config_manager.config = updated_config
        config_manager.save_config()
        
        return {"message": "MCP配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新MCP配置失败: {str(e)}")


@router.post("/config/reload")
async def reload_mcp_config(
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """重新加载MCP配置"""
    try:
        config_manager.reload_config()
        return {"message": "MCP配置重新加载成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载MCP配置失败: {str(e)}")


@router.get("/config/validate")
async def validate_mcp_config(
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """验证MCP配置"""
    try:
        errors = config_manager.validate_config()
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        else:
            return {
                "valid": True,
                "message": "MCP配置验证通过"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证MCP配置失败: {str(e)}")


@router.get("/servers", response_model=List[Dict[str, Any]])
async def get_mcp_servers(
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取MCP服务器列表"""
    try:
        servers = config_manager.get_enabled_servers()
        return [server.dict() for server in servers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP服务器失败: {str(e)}")


@router.get("/servers/{server_name}")
async def get_mcp_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取指定MCP服务器配置"""
    try:
        server = config_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
        
        return server.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP服务器失败: {str(e)}")


@router.get("/tools", response_model=List[MCPToolResponse])
async def get_mcp_tools(
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取MCP工具列表"""
    try:
        tools = config_manager.get_config().tools
        
        # 过滤工具
        if category:
            tools = [tool for tool in tools if tool.category == category]
        
        if enabled is not None:
            tools = [tool for tool in tools if tool.enabled == enabled]
        
        # 转换为响应格式
        tool_responses = []
        for tool in tools:
            server = config_manager.get_server_for_tool(tool.name)
            tool_responses.append(MCPToolResponse(
                name=tool.name,
                description=tool.description,
                category=tool.category,
                enabled=tool.enabled,
                input_schema=tool.input_schema,
                server=server.name if server else None
            ))
        
        return tool_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP工具失败: {str(e)}")


@router.get("/tools/{tool_name}")
async def get_mcp_tool(
    tool_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取指定MCP工具配置"""
    try:
        tool = config_manager.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        server = config_manager.get_server_for_tool(tool_name)
        
        return MCPToolResponse(
            name=tool.name,
            description=tool.description,
            category=tool.category,
            enabled=tool.enabled,
            input_schema=tool.input_schema,
            server=server.name if server else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP工具失败: {str(e)}")


@router.get("/status", response_model=MCPServerStatusResponse)
async def get_mcp_status():
    """获取MCP客户端状态"""
    try:
        # 获取全局MCP客户端实例
        from ....main import mcp_client
        
        if hasattr(mcp_client, 'health_check'):
            # 增强客户端
            health_info = await mcp_client.health_check()
            return MCPServerStatusResponse(**health_info)
        else:
            # 默认客户端
            stats = mcp_client.get_stats()
            tools = await mcp_client.list_tools()
            
            return MCPServerStatusResponse(
                overall_status=mcp_client.status.value,
                total_tools=len(tools),
                servers={},
                stats=stats.dict()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取MCP状态失败: {str(e)}")


@router.post("/tools/{tool_name}/enable")
async def enable_mcp_tool(
    tool_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """启用MCP工具"""
    try:
        tool = config_manager.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        tool.enabled = True
        config_manager.save_config()
        
        return {"message": f"工具 {tool_name} 已启用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用工具失败: {str(e)}")


@router.post("/tools/{tool_name}/disable")
async def disable_mcp_tool(
    tool_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """禁用MCP工具"""
    try:
        tool = config_manager.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        
        tool.enabled = False
        config_manager.save_config()
        
        return {"message": f"工具 {tool_name} 已禁用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用工具失败: {str(e)}")


@router.post("/servers/{server_name}/enable")
async def enable_mcp_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """启用MCP服务器"""
    try:
        server = config_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
        
        server.enabled = True
        config_manager.save_config()
        
        return {"message": f"服务器 {server_name} 已启用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用服务器失败: {str(e)}")


@router.post("/servers/{server_name}/disable")
async def disable_mcp_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """禁用MCP服务器"""
    try:
        server = config_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
        
        server.enabled = False
        config_manager.save_config()
        
        return {"message": f"服务器 {server_name} 已禁用"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用服务器失败: {str(e)}")


@router.get("/categories")
async def get_tool_categories(
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """获取工具分类列表"""
    try:
        tools = config_manager.get_config().tools
        categories = list(set(tool.category for tool in tools if tool.category))
        
        category_info = {}
        for category in categories:
            category_tools = [tool for tool in tools if tool.category == category]
            category_info[category] = {
                "total": len(category_tools),
                "enabled": len([tool for tool in category_tools if tool.enabled])
            }
        
        return category_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具分类失败: {str(e)}")

# 导出路由器
mcp_router = router 