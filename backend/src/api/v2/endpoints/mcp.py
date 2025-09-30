"""
MCP配置管理API端点
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from ....mcp.config_manager import MCPConfigManager
from ....mcp.enhanced_client import EnhancedMCPClient
from ....mcp.config import get_config_manager
from ....mcp.types import MCPConnectionStatus


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


@router.get("/runtime/servers")
async def get_runtime_servers():
    """获取运行时MCP服务器状态（兼容性端点）"""
    try:
        config_manager = get_config_manager()
        servers = config_manager.get_all_servers()
        
        # 获取全局MCP客户端实例
        from main import mcp_client
        
        servers_status = []
        for server in servers:
            # 检查连接状态
            is_connected = False
            tools_count = 0
            
            if hasattr(mcp_client, 'connections'):
                connection = mcp_client.connections.get(server.name)
                is_connected = connection and connection.status == MCPConnectionStatus.CONNECTED
                # 计算该服务器的工具数量
                tools_count = 0
                if connection and hasattr(connection, 'tools'):
                    tools_count = len(connection.tools)
            
            servers_status.append({
                "name": server.name,
                "display_name": server.name,  # 使用name作为显示名称
                "enabled": server.enabled,
                "connected": is_connected,
                "type": server.type,
                "tools_count": tools_count,
                "host": getattr(server, 'host', None),
                "port": getattr(server, 'port', None)
            })
        
        return {
            "servers": servers_status,
            "total_enabled": len([s for s in servers_status if s["enabled"]]),
            "total_connected": len([s for s in servers_status if s["connected"]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运行时服务器状态失败: {str(e)}")


@router.get("/servers/status")
async def get_servers_status():
    """获取所有MCP服务器的详细状态（用于前端开关显示）"""
    try:
        config_manager = get_config_manager()
        servers = config_manager.get_all_servers()
        
        # 获取全局MCP客户端实例
        from main import mcp_client
        
        servers_status = []
        for server in servers:
            # 检查连接状态
            is_connected = False
            tools_count = 0
            
            if hasattr(mcp_client, 'connections'):
                connection = mcp_client.connections.get(server.name)
                is_connected = connection and connection.status == MCPConnectionStatus.CONNECTED
                # 计算该服务器的工具数量
                tools_count = 0
                if connection and hasattr(connection, 'tools'):
                    tools_count = len(connection.tools)
            
            servers_status.append({
                "name": server.name,
                "display_name": server.name,  # 使用name作为显示名称
                "enabled": server.enabled,
                "connected": is_connected,
                "type": server.type,
                "tools_count": tools_count,
                "host": getattr(server, 'host', None),
                "port": getattr(server, 'port', None)
            })
        
        return {
            "servers": servers_status,
            "total_enabled": len([s for s in servers_status if s["enabled"]]),
            "total_connected": len([s for s in servers_status if s["connected"]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务器状态失败: {str(e)}")


@router.post("/servers/batch-toggle")
async def batch_toggle_servers(
    request: dict,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """批量切换服务器状态"""
    try:
        server_states = request.get("servers", {})
        results = []
        
        for server_name, enabled in server_states.items():
            server = config_manager.get_server_by_name(server_name)
            if server:
                server.enabled = enabled
                results.append({
                    "server": server_name,
                    "enabled": enabled,
                    "success": True
                })
            else:
                results.append({
                    "server": server_name,
                    "enabled": enabled,
                    "success": False,
                    "error": "服务器不存在"
                })
        
        config_manager.save_config()
        
        return {
            "message": "批量更新完成",
            "results": results,
            "success_count": len([r for r in results if r["success"]]),
            "total_count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量切换失败: {str(e)}")


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
        from main import mcp_client
        
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


@router.post("/servers/{server_name}/connect")
async def connect_mcp_server(server_name: str):
    """连接MCP服务器"""
    try:
        from main import mcp_client
        
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP客户端未初始化")
        
        # 检查服务器是否存在
        config_manager = get_config_manager()
        server = config_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
        
        # 尝试连接服务器
        success = await mcp_client.connect_server(server_name)
        
        if success:
            return {"message": f"服务器 {server_name} 连接成功", "connected": True}
        else:
            raise HTTPException(status_code=500, detail=f"服务器 {server_name} 连接失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接服务器失败: {str(e)}")


@router.post("/servers/{server_name}/disconnect")
async def disconnect_mcp_server(server_name: str):
    """断开MCP服务器连接"""
    try:
        from main import mcp_client
        
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP客户端未初始化")
        
        # 断开服务器连接
        success = await mcp_client.disconnect_server(server_name)
        
        if success:
            return {"message": f"服务器 {server_name} 已断开连接", "connected": False}
        else:
            return {"message": f"服务器 {server_name} 断开连接失败", "connected": None}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开连接失败: {str(e)}")


@router.post("/servers/{server_name}/reconnect")
async def reconnect_mcp_server(server_name: str):
    """重新连接MCP服务器"""
    try:
        from main import mcp_client
        
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP客户端未初始化")
        
        # 先断开再连接
        await mcp_client.disconnect_server(server_name)
        success = await mcp_client.connect_server(server_name)
        
        if success:
            return {"message": f"服务器 {server_name} 重连成功", "connected": True}
        else:
            raise HTTPException(status_code=500, detail=f"服务器 {server_name} 重连失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重连服务器失败: {str(e)}")


@router.post("/config/servers/{server_name}/toggle")
async def toggle_mcp_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager_dep)
):
    """切换MCP服务器状态（启用/禁用）"""
    try:
        server = config_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"服务器 {server_name} 不存在")
        
        # 切换状态
        old_enabled = server.enabled
        server.enabled = not server.enabled
        config_manager.save_config()
        
        # 自动连接/断开服务器
        try:
            from main import mcp_client
            if mcp_client:
                if server.enabled and not old_enabled:
                    # 服务器被启用，自动连接
                    logger.info(f"服务器 {server_name} 被启用，正在自动连接...")
                    connect_success = await mcp_client.connect_server(server_name)
                    if connect_success:
                        logger.info(f"✅ 服务器 {server_name} 自动连接成功")
                    else:
                        logger.warning(f"⚠️ 服务器 {server_name} 自动连接失败")
                elif not server.enabled and old_enabled:
                    # 服务器被禁用，自动断开
                    logger.info(f"服务器 {server_name} 被禁用，正在自动断开...")
                    disconnect_success = await mcp_client.disconnect_server(server_name)
                    if disconnect_success:
                        logger.info(f"✅ 服务器 {server_name} 自动断开成功")
                    else:
                        logger.warning(f"⚠️ 服务器 {server_name} 自动断开失败")
        except Exception as auto_connect_error:
            logger.warning(f"自动连接/断开服务器时出错: {auto_connect_error}")
        
        status = "启用" if server.enabled else "禁用"
        return {"message": f"服务器 {server_name} 已{status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换服务器状态失败: {str(e)}")


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