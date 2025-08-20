"""
MCP配置管理API端点
提供类似Cursor的MCP配置管理功能
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from loguru import logger
import tempfile
import os
import json

from src.mcp.config_manager import (
    MCPConfigManager, 
    MCPConfigTemplate, 
    MCPConfigValidationResult,
    get_mcp_config_manager
)
from src.mcp.config import MCPServerConfig, MCPToolConfig, MCPConfiguration

router = APIRouter(prefix="/mcp/config", tags=["MCP配置"])

# 请求模型
class ServerCreateRequest(BaseModel):
    """创建服务器请求"""
    name: str = Field(..., description="服务器名称")
    type: str = Field(..., description="服务器类型")
    enabled: bool = Field(True, description="是否启用")
    host: Optional[str] = Field(None, description="主机地址")
    port: Optional[int] = Field(None, description="端口")
    path: Optional[str] = Field("/", description="路径")
    base_url: Optional[str] = Field(None, description="基础URL")
    timeout: int = Field(30, description="超时时间")
    retry_attempts: int = Field(3, description="重试次数")
    enabled_tools: Optional[List[str]] = Field(None, description="启用的工具")
    auth_token: Optional[str] = Field(None, description="认证令牌")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

class ToolCreateRequest(BaseModel):
    """创建工具请求"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: Optional[str] = Field(None, description="工具分类")
    enabled: bool = Field(True, description="是否启用")
    input_schema: Dict[str, Any] = Field(..., description="输入schema")
    timeout: Optional[int] = Field(None, description="超时时间")
    cache_enabled: Optional[bool] = Field(None, description="是否启用缓存")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数")

class TemplateCreateRequest(BaseModel):
    """从模板创建请求"""
    template_name: str = Field(..., description="模板名称")
    server_name: str = Field(..., description="服务器名称")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

class ConfigImportRequest(BaseModel):
    """配置导入请求"""
    config_data: Dict[str, Any] = Field(..., description="配置数据")

# 响应模型
class ServerResponse(BaseModel):
    """服务器响应"""
    name: str
    type: str
    enabled: bool
    status: Optional[str] = None
    tools_count: int = 0
    last_connected: Optional[str] = None

class ToolResponse(BaseModel):
    """工具响应"""
    name: str
    description: str
    category: Optional[str] = None
    enabled: bool
    server: Optional[str] = None
    status: Optional[str] = None

class TemplateResponse(BaseModel):
    """模板响应"""
    name: str
    description: str
    category: str
    icon: Optional[str] = None
    tags: List[str] = []
    author: Optional[str] = None
    version: str = "1.0.0"

# 依赖注入
def get_config_manager() -> MCPConfigManager:
    """获取配置管理器"""
    return get_mcp_config_manager()

# 配置概览
@router.get("/file")
async def get_config_file(path: str = "config/mcp_config.json"):
    """获取配置文件内容"""
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return config_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="配置文件不是有效的JSON格式")
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取配置文件失败: {str(e)}")

@router.get("/overview")
async def get_config_overview(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """获取配置概览"""
    try:
        config = config_manager.get_config()
        
        # 统计信息
        total_servers = len(config.servers)
        enabled_servers = sum(1 for s in config.servers if s.enabled)
        total_tools = len(config.tools)
        enabled_tools = sum(1 for t in config.tools if t.enabled)
        
        # 按类别分组工具
        tools_by_category = {}
        for tool in config.tools:
            category = tool.category or "其他"
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool.name)
        
        # 服务器状态
        server_status = {}
        for server in config.servers:
            if server.enabled:
                # 这里可以添加实际的连接状态检查
                server_status[server.name] = "unknown"
        
        return {
            "config_name": config.name,
            "config_description": config.description,
            "statistics": {
                "total_servers": total_servers,
                "enabled_servers": enabled_servers,
                "total_tools": total_tools,
                "enabled_tools": enabled_tools,
                "tools_by_category": tools_by_category
            },
            "server_status": server_status,
            "last_updated": None  # 可以添加配置文件的修改时间
        }
    except Exception as e:
        logger.error(f"获取配置概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置概览失败: {str(e)}")

# 服务器管理
@router.get("/servers", response_model=List[ServerResponse])
async def list_servers(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """获取服务器列表"""
    try:
        config = config_manager.get_config()
        servers = []
        
        for server in config.servers:
            # 计算工具数量
            tools_count = len(server.enabled_tools) if server.enabled_tools else 0
            
            servers.append(ServerResponse(
                name=server.name,
                type=server.type,
                enabled=server.enabled,
                status="unknown",  # 可以添加实际状态检查
                tools_count=tools_count
            ))
        
        return servers
    except Exception as e:
        logger.error(f"获取服务器列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务器列表失败: {str(e)}")

@router.post("/servers")
async def create_server(
    request: ServerCreateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """创建服务器"""
    try:
        # 构建服务器配置
        server_config = MCPServerConfig(
            name=request.name,
            type=request.type,
            enabled=request.enabled,
            host=request.host,
            port=request.port,
            path=request.path,
            base_url=request.base_url,
            timeout=request.timeout,
            retry_attempts=request.retry_attempts,
            enabled_tools=request.enabled_tools,
            auth_token=request.auth_token
        )
        
        # 合并自定义配置
        if request.custom_config:
            for key, value in request.custom_config.items():
                if hasattr(server_config, key):
                    setattr(server_config, key, value)
        
        success = config_manager.add_server(server_config)
        if success:
            return {"message": f"服务器 {request.name} 创建成功"}
        else:
            raise HTTPException(status_code=400, detail="服务器创建失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建服务器失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建服务器失败: {str(e)}")

@router.put("/servers/{server_name}")
async def update_server(
    server_name: str,
    request: ServerCreateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """更新服务器"""
    try:
        server_config = MCPServerConfig(
            name=request.name,
            type=request.type,
            enabled=request.enabled,
            host=request.host,
            port=request.port,
            path=request.path,
            base_url=request.base_url,
            timeout=request.timeout,
            retry_attempts=request.retry_attempts,
            enabled_tools=request.enabled_tools,
            auth_token=request.auth_token
        )
        
        success = config_manager.update_server(server_name, server_config)
        if success:
            return {"message": f"服务器 {server_name} 更新成功"}
        else:
            raise HTTPException(status_code=404, detail="服务器不存在")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新服务器失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新服务器失败: {str(e)}")

@router.delete("/servers/{server_name}")
async def delete_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """删除服务器"""
    try:
        success = config_manager.remove_server(server_name)
        if success:
            return {"message": f"服务器 {server_name} 删除成功"}
        else:
            raise HTTPException(status_code=404, detail="服务器不存在")
    except Exception as e:
        logger.error(f"删除服务器失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除服务器失败: {str(e)}")

@router.post("/servers/{server_name}/toggle")
async def toggle_server(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """切换服务器启用状态"""
    try:
        success = config_manager.toggle_server(server_name)
        if success:
            return {"message": f"服务器 {server_name} 状态切换成功"}
        else:
            raise HTTPException(status_code=404, detail="服务器不存在")
    except Exception as e:
        logger.error(f"切换服务器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换服务器状态失败: {str(e)}")

# 工具管理
@router.get("/tools", response_model=List[ToolResponse])
async def list_tools(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """获取工具列表"""
    try:
        config = config_manager.get_config()
        tools = []
        
        for tool in config.tools:
            # 查找对应的服务器
            server_name = None
            for server in config.servers:
                if server.enabled_tools and tool.name in server.enabled_tools:
                    server_name = server.name
                    break
            
            tools.append(ToolResponse(
                name=tool.name,
                description=tool.description,
                category=tool.category,
                enabled=tool.enabled,
                server=server_name,
                status="configured" if server_name else "no_server"
            ))
        
        return tools
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")

@router.post("/tools")
async def create_tool(
    request: ToolCreateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """创建工具"""
    try:
        tool_config = MCPToolConfig(
            name=request.name,
            description=request.description,
            category=request.category,
            enabled=request.enabled,
            input_schema=request.input_schema,
            timeout=request.timeout,
            cache_enabled=request.cache_enabled,
            default_parameters=request.default_parameters
        )
        
        success = config_manager.add_tool(tool_config)
        if success:
            return {"message": f"工具 {request.name} 创建成功"}
        else:
            raise HTTPException(status_code=400, detail="工具创建失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建工具失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建工具失败: {str(e)}")

@router.post("/tools/{tool_name}/toggle")
async def toggle_tool(
    tool_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """切换工具启用状态"""
    try:
        success = config_manager.toggle_tool(tool_name)
        if success:
            return {"message": f"工具 {tool_name} 状态切换成功"}
        else:
            raise HTTPException(status_code=404, detail="工具不存在")
    except Exception as e:
        logger.error(f"切换工具状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换工具状态失败: {str(e)}")

# 模板管理
@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """获取模板列表"""
    try:
        templates = config_manager.get_templates()
        return [
            TemplateResponse(
                name=template.name,
                description=template.description,
                category=template.category,
                icon=template.icon,
                tags=template.tags,
                author=template.author,
                version=template.version
            )
            for template in templates.values()
        ]
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.post("/templates/{template_name}/create")
async def create_from_template(
    template_name: str,
    request: TemplateCreateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """从模板创建服务器"""
    try:
        success = config_manager.create_from_template(
            request.template_name,
            request.server_name,
            request.custom_config
        )
        
        if success:
            return {"message": f"从模板 {template_name} 创建服务器 {request.server_name} 成功"}
        else:
            raise HTTPException(status_code=400, detail="从模板创建服务器失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"从模板创建服务器失败: {e}")
        raise HTTPException(status_code=500, detail=f"从模板创建服务器失败: {str(e)}")

# 配置验证
@router.post("/validate", response_model=MCPConfigValidationResult)
async def validate_config(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """验证配置"""
    try:
        result = await config_manager.validate_config()
        return result
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")

# 配置导入导出
@router.get("/export")
async def export_config(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """导出配置"""
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        success = config_manager.export_config(temp_file)
        if success:
            return FileResponse(
                temp_file,
                media_type='application/json',
                filename='mcp_config.json'
            )
        else:
            raise HTTPException(status_code=500, detail="配置导出失败")
            
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@router.post("/import")
async def import_config(
    file: UploadFile = File(...),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """导入配置"""
    try:
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            content = await file.read()
            f.write(content)
            temp_file = f.name
        
        success = config_manager.import_config(temp_file)
        
        # 清理临时文件
        os.unlink(temp_file)
        
        if success:
            return {"message": "配置导入成功"}
        else:
            raise HTTPException(status_code=400, detail="配置导入失败")
            
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

# 备份管理
@router.get("/backups")
async def list_backups(
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """获取备份列表"""
    try:
        backups = config_manager.get_backups()
        return {"backups": backups}
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.post("/backups/{backup_name}/restore")
async def restore_backup(
    backup_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """恢复备份"""
    try:
        success = config_manager.restore_backup(backup_name)
        if success:
            return {"message": f"备份 {backup_name} 恢复成功"}
        else:
            raise HTTPException(status_code=404, detail="备份不存在")
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")

# 连接测试
@router.post("/test/{server_name}")
async def test_server_connection(
    server_name: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """测试服务器连接"""
    try:
        config = config_manager.get_config()
        server = next((s for s in config.servers if s.name == server_name), None)
        
        if not server:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        # 执行连接测试
        status = await config_manager._test_server_connection(server)
        
        return {
            "server_name": server_name,
            "status": status,
            "connected": status == "connected",
            "message": "连接成功" if status == "connected" else "连接失败"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试服务器连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}") 