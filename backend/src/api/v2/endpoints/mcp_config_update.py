"""
MCP配置更新API端点
提供直接更新MCP配置文件的功能
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from loguru import logger
import json
import os
import traceback
import asyncio
from pathlib import Path

router = APIRouter(prefix="/mcp/config", tags=["MCP配置"])

# 请求模型
class MCPConfigUpdateRequest(BaseModel):
    """MCP配置更新请求"""
    config_data: Dict[str, Any] = Field(..., description="完整的MCP配置数据")

# 响应模型
class MCPConfigUpdateResponse(BaseModel):
    """MCP配置更新响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    config_path: str = Field(..., description="配置文件路径")
    backup_path: Optional[str] = Field(None, description="备份文件路径")
    warnings: List[str] = Field(default_factory=list, description="警告信息")

async def reload_mcp_client_async():
    """异步重载MCP客户端"""
    try:
        # 延迟两秒，确保文件写入完成
        await asyncio.sleep(2)
        
        # 尝试获取主模块中的MCP客户端
        import sys
        main_module = sys.modules.get('main')
        if main_module and hasattr(main_module, 'mcp_client'):
            mcp_client = getattr(main_module, 'mcp_client')
            if mcp_client:
                logger.info("🔄 从main模块获取到MCP客户端，准备重载配置")
                if hasattr(mcp_client, 'reload_config_async'):
                    await mcp_client.reload_config_async()
                    logger.info("✅ MCP客户端配置已异步热重载")
                elif hasattr(mcp_client, 'reload_config'):
                    # 如果是同步方法，使用run_in_executor执行
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, mcp_client.reload_config)
                    logger.info("✅ MCP客户端配置已热重载")
                else:
                    logger.warning("⚠️ MCP客户端没有reload_config方法")
        else:
            # 尝试从其他可能的位置获取MCP客户端
            try:
                logger.info("🔍 尝试从backend.src.mcp导入MCP客户端")
                from backend.src.mcp import get_mcp_client
                mcp_client = get_mcp_client()
                if mcp_client and hasattr(mcp_client, 'reload_config'):
                    if asyncio.iscoroutinefunction(mcp_client.reload_config):
                        await mcp_client.reload_config()
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, mcp_client.reload_config)
                    logger.info("✅ 通过导入获取的MCP客户端配置已热重载")
                else:
                    logger.warning("⚠️ 导入的MCP客户端不支持重载配置")
            except ImportError:
                logger.warning("⚠️ 无法从backend.src.mcp导入MCP客户端模块")
                
                # 尝试其他可能的导入路径
                try:
                    logger.info("🔍 尝试从src.mcp导入MCP客户端")
                    from src.mcp import get_mcp_client
                    mcp_client = get_mcp_client()
                    if mcp_client and hasattr(mcp_client, 'reload_config'):
                        if asyncio.iscoroutinefunction(mcp_client.reload_config):
                            await mcp_client.reload_config()
                        else:
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, mcp_client.reload_config)
                        logger.info("✅ 通过src.mcp导入的MCP客户端配置已热重载")
                except ImportError:
                    logger.warning("⚠️ 无法从src.mcp导入MCP客户端模块")
    except ImportError:
        logger.warning("⚠️ 无法导入MCP客户端模块")
    except Exception as e:
        logger.error(f"❌ MCP客户端热重载失败: {e}")
        logger.debug(traceback.format_exc())

def background_reload_mcp_client():
    """后台任务：重载MCP客户端"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 运行异步重载函数
        loop.run_until_complete(reload_mcp_client_async())
        loop.close()
    except Exception as e:
        logger.error(f"❌ 后台重载MCP客户端失败: {e}")

@router.post("/update", response_model=MCPConfigUpdateResponse)
async def update_mcp_config(request: MCPConfigUpdateRequest, background_tasks: BackgroundTasks):
    """更新MCP配置文件"""
    warnings = []
    backup_path = None
    
    try:
        # 确定配置文件路径
        config_paths = [
            "config/mcp_config.json",
            "backend/config/mcp_config.json"
        ]
        
        # 检查哪个配置文件存在并且有内容
        primary_config_path = None
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # 确保文件不是空的
                            primary_config_path = path
                            break
                except Exception as e:
                    warnings.append(f"读取配置文件 {path} 失败: {str(e)}")
                    continue
        
        # 如果没有找到有效的配置文件，使用默认路径
        if not primary_config_path:
            primary_config_path = "config/mcp_config.json"
            warnings.append(f"未找到有效的配置文件，将使用默认路径: {primary_config_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(primary_config_path), exist_ok=True)
        
        logger.info(f"📝 更新MCP配置文件: {primary_config_path}")
        
        # 创建备份
        backup_dir = Path(os.path.dirname(primary_config_path)) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"mcp_config_{timestamp}.json"
        
        # 如果原配置文件存在，创建备份
        if os.path.exists(primary_config_path):
            import shutil
            shutil.copy2(primary_config_path, backup_path)
            logger.info(f"💾 创建配置备份: {backup_path}")
        
        # 验证配置数据
        if not isinstance(request.config_data, dict):
            raise ValueError("配置数据必须是一个JSON对象")
        
        if "servers" not in request.config_data:
            warnings.append("配置中缺少servers字段")
        
        if "tools" not in request.config_data:
            warnings.append("配置中缺少tools字段")
        
        # 写入新配置
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(primary_config_path), exist_ok=True)
            
            # 检查文件权限
            if os.path.exists(primary_config_path):
                # 检查文件是否可写
                if not os.access(primary_config_path, os.W_OK):
                    logger.warning(f"⚠️ 配置文件不可写: {primary_config_path}，尝试修改权限")
                    try:
                        os.chmod(primary_config_path, 0o644)  # 尝试修改权限
                    except Exception as perm_error:
                        logger.warning(f"无法修改文件权限: {perm_error}")
            
            # 写入配置
            with open(primary_config_path, 'w', encoding='utf-8') as f:
                json.dump(request.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 主配置文件已更新: {primary_config_path}")
        except Exception as e:
            logger.error(f"❌ 写入主配置文件失败: {e}")
            logger.debug(traceback.format_exc())
            raise ValueError(f"写入配置文件失败: {str(e)}")
        
        # 同步到另一个配置文件位置
        for path in config_paths:
            if path != primary_config_path:
                try:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    
                    # 检查文件权限
                    if os.path.exists(path):
                        if not os.access(path, os.W_OK):
                            logger.warning(f"⚠️ 配置文件不可写: {path}，尝试修改权限")
                            try:
                                os.chmod(path, 0o644)  # 尝试修改权限
                            except Exception as perm_error:
                                logger.warning(f"无法修改文件权限: {perm_error}")
                    
                    # 复制配置
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(request.config_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"✅ 同步配置到: {path}")
                except Exception as e:
                    warnings.append(f"同步配置到 {path} 失败: {str(e)}")
                    logger.warning(f"⚠️ 同步配置到 {path} 失败: {e}")
                    logger.debug(traceback.format_exc())
        
        # 在后台任务中重载MCP客户端
        background_tasks.add_task(background_reload_mcp_client)
        
        return {
            "success": True,
            "message": "MCP配置更新成功",
            "config_path": primary_config_path,
            "backup_path": str(backup_path),
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"❌ 更新MCP配置失败: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"更新MCP配置失败: {str(e)}")