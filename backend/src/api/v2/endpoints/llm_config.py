"""
LLM配置管理API端点
提供基于文件的LLM配置管理功能
复用MCP配置API的成熟设计模式
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from loguru import logger
import tempfile
import os
import json

from src.llm.config_manager import (
    LLMConfigManager,
    get_llm_config_manager
)
from src.llm.config import LLMProviderConfig, LLMConfiguration

router = APIRouter(prefix="/llm/config", tags=["LLM配置"])

# 请求模型
class LLMConfigUpdateRequest(BaseModel):
    """LLM配置更新请求"""
    config: Dict[str, Any] = Field(..., description="LLM配置数据")

class ProviderCreateRequest(BaseModel):
    """创建提供商请求"""
    id: str = Field(..., description="提供商唯一标识符")
    name: str = Field(..., description="提供商显示名称")
    enabled: bool = Field(True, description="是否启用")
    model: str = Field(..., description="默认模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    deployment_name: Optional[str] = Field(None, description="Azure OpenAI部署名称")
    api_version: Optional[str] = Field(None, description="Azure OpenAI API版本")
    organization: Optional[str] = Field(None, description="OpenAI组织ID")
    temperature: float = Field(0.7, description="模型温度参数")
    max_tokens: int = Field(2000, description="最大token数")
    timeout: int = Field(30, description="请求超时时间")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")

class ConfigImportRequest(BaseModel):
    """配置导入请求"""
    config_data: Dict[str, Any] = Field(..., description="配置数据")

# 响应模型
class ProviderResponse(BaseModel):
    """提供商响应"""
    id: str
    name: str
    enabled: bool
    model: str
    base_url: Optional[str] = None
    status: Optional[str] = None
    
class BackupResponse(BaseModel):
    """备份响应"""
    name: str
    size: int
    created: str
    modified: str

# 依赖注入
def get_config_manager() -> LLMConfigManager:
    """获取LLM配置管理器"""
    return get_llm_config_manager()

# 当前配置
@router.get("/current")
async def get_current_llm_config(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """获取当前LLM配置"""
    try:
        config = config_manager.get_config()
        return {
            "version": config.version,
            "name": config.name,
            "description": config.description,
            "enabled": config.enabled,
            "providers": [provider.model_dump() for provider in config.providers],
            "default_provider": config.default_provider,
            "global_defaults": config.global_defaults,
            "security": config.security,
            "logging": config.logging,
            "cache": config.cache
        }
    except Exception as e:
        logger.error(f"获取当前LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

# 配置更新
@router.post("/update")
async def update_llm_config(
    request: LLMConfigUpdateRequest,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """更新LLM配置"""
    try:
        # 验证并创建配置对象
        config_data = request.config
        config = LLMConfiguration.model_validate(config_data)
        
        # 更新配置（会自动创建备份）
        success = config_manager.update_config(config)
        
        if success:
            return {"message": "LLM配置更新成功"}
        else:
            raise HTTPException(status_code=400, detail="配置更新失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"配置验证失败: {str(e)}")
    except Exception as e:
        logger.error(f"更新LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

# 配置概览
@router.get("/overview")
async def get_llm_config_overview(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """获取LLM配置概览"""
    try:
        config = config_manager.get_config()
        
        # 统计信息
        total_providers = len(config.providers)
        enabled_providers = sum(1 for p in config.providers if p.enabled)
        
        # 按类型分组提供商
        providers_by_type = {}
        for provider in config.providers:
            provider_type = provider.id.split('_')[0] if '_' in provider.id else provider.id
            if provider_type not in providers_by_type:
                providers_by_type[provider_type] = []
            providers_by_type[provider_type].append(provider.name)
        
        return {
            "config_name": config.name,
            "config_description": config.description,
            "statistics": {
                "total_providers": total_providers,
                "enabled_providers": enabled_providers,
                "default_provider": config.default_provider,
                "providers_by_type": providers_by_type
            },
            "global_defaults": config.global_defaults,
            "last_updated": None  # 可以添加配置文件的修改时间
        }
    except Exception as e:
        logger.error(f"获取LLM配置概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置概览失败: {str(e)}")

# 提供商管理
@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """获取提供商列表"""
    try:
        config = config_manager.get_config()
        providers = []
        
        for provider in config.providers:
            providers.append(ProviderResponse(
                id=provider.id,
                name=provider.name,
                enabled=provider.enabled,
                model=provider.model,
                base_url=provider.base_url,
                status="configured"  # 可以添加实际状态检查
            ))
        
        return providers
    except Exception as e:
        logger.error(f"获取提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")

@router.post("/providers")
async def create_provider(
    request: ProviderCreateRequest,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """创建提供商"""
    try:
        # 构建提供商配置
        provider_config = LLMProviderConfig(
            id=request.id,
            name=request.name,
            enabled=request.enabled,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url,
            deployment_name=request.deployment_name,
            api_version=request.api_version,
            organization=request.organization,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout
        )
        
        # 合并自定义配置
        if request.custom_config:
            for key, value in request.custom_config.items():
                if hasattr(provider_config, key):
                    setattr(provider_config, key, value)
        
        success = config_manager.add_provider(provider_config)
        if success:
            return {"message": f"提供商 {request.name} 创建成功"}
        else:
            raise HTTPException(status_code=400, detail="提供商创建失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建提供商失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建提供商失败: {str(e)}")

@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    request: ProviderCreateRequest,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """更新提供商"""
    try:
        provider_config = LLMProviderConfig(
            id=request.id,
            name=request.name,
            enabled=request.enabled,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url,
            deployment_name=request.deployment_name,
            api_version=request.api_version,
            organization=request.organization,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout
        )
        
        success = config_manager.update_provider(provider_id, provider_config)
        if success:
            return {"message": f"提供商 {provider_id} 更新成功"}
        else:
            raise HTTPException(status_code=404, detail="提供商不存在")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新提供商失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新提供商失败: {str(e)}")

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """删除提供商"""
    try:
        success = config_manager.remove_provider(provider_id)
        if success:
            return {"message": f"提供商 {provider_id} 删除成功"}
        else:
            raise HTTPException(status_code=404, detail="提供商不存在")
    except Exception as e:
        logger.error(f"删除提供商失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除提供商失败: {str(e)}")

# 备份管理
@router.get("/backups", response_model=List[BackupResponse])
async def get_llm_config_backups(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """获取备份列表"""
    try:
        backups = config_manager.get_backups()
        return [
            BackupResponse(
                name=backup["name"],
                size=backup["size"],
                created=backup["created"],
                modified=backup["modified"]
            )
            for backup in backups
        ]
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.post("/restore/{backup_name}")
async def restore_llm_config_backup(
    backup_name: str,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """恢复指定备份"""
    try:
        success = config_manager.restore_backup(backup_name)
        if success:
            return {"message": f"备份 {backup_name} 恢复成功"}
        else:
            raise HTTPException(status_code=404, detail="备份不存在")
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")

# 配置验证
@router.post("/validate")
async def validate_llm_config(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """验证LLM配置"""
    try:
        config = config_manager.get_config()
        
        # 基本验证
        errors = []
        warnings = []
        
        # 验证是否有提供商
        if not config.providers:
            errors.append("配置中没有任何提供商")
        
        # 验证默认提供商
        if config.default_provider:
            default_exists = any(p.id == config.default_provider for p in config.providers)
            if not default_exists:
                errors.append(f"默认提供商 '{config.default_provider}' 不存在")
        
        # 验证提供商配置
        for provider in config.providers:
            if not provider.api_key and not provider.base_url:
                warnings.append(f"提供商 '{provider.name}' 缺少API密钥和基础URL")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "provider_count": len(config.providers),
            "enabled_provider_count": sum(1 for p in config.providers if p.enabled)
        }
    except Exception as e:
        logger.error(f"验证LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")

# 配置导入导出
@router.get("/export")
async def export_llm_config(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """导出LLM配置"""
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        success = config_manager.export_config(temp_file)
        if success:
            return FileResponse(
                temp_file,
                media_type='application/json',
                filename='llm_config.json'
            )
        else:
            raise HTTPException(status_code=500, detail="配置导出失败")
            
    except Exception as e:
        logger.error(f"导出LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@router.post("/import")
async def import_llm_config(
    file: UploadFile = File(...),
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """导入LLM配置"""
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
            return {"message": "LLM配置导入成功"}
        else:
            raise HTTPException(status_code=400, detail="配置导入失败")
            
    except Exception as e:
        logger.error(f"导入LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")


@router.get("/file-watcher/status")
async def get_file_watcher_status(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """获取文件监控状态"""
    try:
        status = config_manager.get_file_watcher_status()
        return {
            "status": "success",
            "file_watcher": status
        }
    except Exception as e:
        logger.error(f"获取文件监控状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/file-watcher/toggle")
async def toggle_file_watcher(
    enabled: bool,
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """启用/禁用文件监控"""
    try:
        config_manager.set_file_watcher_enabled(enabled)
        status = config_manager.get_file_watcher_status()
        
        return {
            "message": f"文件监控已{'启用' if enabled else '禁用'}",
            "enabled": enabled,
            "status": status
        }
    except Exception as e:
        logger.error(f"切换文件监控状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.post("/file-watcher/restart")
async def restart_file_watcher(
    config_manager: LLMConfigManager = Depends(get_config_manager)
):
    """重启文件监控"""
    try:
        success = config_manager.restart_file_watcher()
        status = config_manager.get_file_watcher_status()
        
        if success:
            return {
                "message": "文件监控重启成功",
                "status": status
            }
        else:
            return {
                "message": "文件监控重启失败",
                "status": status
            }
    except Exception as e:
        logger.error(f"重启文件监控失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启失败: {str(e)}") 