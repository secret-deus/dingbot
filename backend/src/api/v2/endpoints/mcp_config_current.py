"""
MCP配置获取API端点
提供获取当前MCP配置的功能
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger
import json
import os
import traceback
from pathlib import Path

router = APIRouter(prefix="/mcp/config", tags=["MCP配置"])

# 响应模型
class MCPConfigResponse(BaseModel):
    """MCP配置响应"""
    version: str = Field(..., description="配置版本")
    name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    servers: List[Dict[str, Any]] = Field(default_factory=list, description="服务器配置")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="工具配置")
    global_config: Optional[Dict[str, Any]] = Field(None, description="全局配置")
    security: Optional[Dict[str, Any]] = Field(None, description="安全配置")
    logging: Optional[Dict[str, Any]] = Field(None, description="日志配置")
    source_file: str = Field(..., description="配置文件路径")

@router.get("/current", response_model=MCPConfigResponse)
async def get_current_mcp_config():
    """获取当前MCP配置"""
    try:
        # 确定配置文件路径
        config_paths = [
            "config/mcp_config.json",
            "backend/config/mcp_config.json"
        ]
        
        # 检查哪个配置文件存在并且有内容
        config_data = None
        config_path = None
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # 确保文件不是空的
                            config_data = json.loads(content)
                            config_path = path
                            logger.info(f"✅ 从 {path} 加载配置成功")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ 读取配置文件 {path} 失败: {str(e)}")
                    continue
        
        # 如果没有找到有效的配置文件，返回默认配置
        if not config_data:
            logger.warning("⚠️ 未找到有效的配置文件，返回默认配置")
            config_data = {
                "version": "1.0",
                "name": "默认MCP配置",
                "description": "未找到有效配置文件，返回默认配置",
                "servers": [],
                "tools": [],
                "global_config": {
                    "timeout": 30000,
                    "retry_attempts": 3,
                    "retry_delay": 1000,
                    "max_concurrent_calls": 5,
                    "enable_cache": True,
                    "cache_timeout": 300000
                },
                "security": {
                    "enable_audit": True,
                    "audit_log_path": "logs/mcp_audit.log",
                    "rate_limit": {
                        "enabled": True,
                        "requests_per_minute": 100
                    }
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
            config_path = "config/mcp_config.json"
        
        # 确保配置数据包含所有必需字段
        if "version" not in config_data:
            config_data["version"] = "1.0"
        
        if "name" not in config_data:
            config_data["name"] = "MCP配置"
        
        if "servers" not in config_data:
            config_data["servers"] = []
        
        if "tools" not in config_data:
            config_data["tools"] = []
        
        # 添加源文件路径
        config_data["source_file"] = config_path
        
        return config_data
    except Exception as e:
        logger.error(f"❌ 获取MCP配置失败: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取MCP配置失败: {str(e)}")

@router.get("/file")
async def get_mcp_config_file(path: str):
    """从指定路径获取MCP配置文件"""
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise HTTPException(status_code=400, detail=f"配置文件为空: {path}")
            
            config_data = json.loads(content)
            return config_data
    except json.JSONDecodeError as e:
        logger.error(f"❌ 解析配置文件失败: {e}")
        raise HTTPException(status_code=400, detail=f"配置文件格式错误: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 读取配置文件失败: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"读取配置文件失败: {str(e)}")