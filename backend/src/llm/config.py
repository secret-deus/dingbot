"""
LLM配置管理模块
支持通过JSON配置文件管理LLM提供商和模型配置
基于MCP配置模型的成熟架构设计
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from loguru import logger


class LLMProviderConfig(BaseModel):
    """LLM提供商配置"""
    id: str = Field(..., description="提供商唯一标识符")
    name: str = Field(..., description="提供商显示名称")
    enabled: bool = Field(True, description="是否启用此提供商")
    
    # 核心配置
    model: str = Field(..., description="默认模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    
    # Azure OpenAI 特有配置
    deployment_name: Optional[str] = Field(None, description="Azure OpenAI部署名称")
    api_version: Optional[str] = Field(None, description="Azure OpenAI API版本")
    
    # OpenAI 特有配置
    organization: Optional[str] = Field(None, description="OpenAI组织ID")
    
    # 模型参数配置
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="模型温度参数")
    max_tokens: int = Field(2000, gt=0, le=32000, description="最大token数")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="存在惩罚")
    
    # 连接配置
    timeout: int = Field(30, gt=0, le=300, description="请求超时时间(秒)")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    retry_delay: float = Field(1.0, ge=0.0, le=60.0, description="重试延迟(秒)")
    
    # 流式输出配置
    stream: bool = Field(False, description="是否启用流式输出")
    stream_timeout: int = Field(60, gt=0, le=600, description="流式输出超时时间(秒)")
    
    # 高级配置
    custom_headers: Optional[Dict[str, str]] = Field(None, description="自定义HTTP头")
    proxy_url: Optional[str] = Field(None, description="代理URL")
    verify_ssl: bool = Field(True, description="是否验证SSL证书")
    
    # 功能支持配置
    supports_functions: bool = Field(True, description="是否支持函数调用")
    supports_vision: bool = Field(False, description="是否支持视觉功能")
    supports_streaming: bool = Field(True, description="是否支持流式输出")
    
    # 成本和限制配置
    cost_per_token: Optional[float] = Field(None, ge=0.0, description="每token成本")
    rate_limit_rpm: Optional[int] = Field(None, gt=0, description="每分钟请求限制")
    rate_limit_tpm: Optional[int] = Field(None, gt=0, description="每分钟token限制")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """验证提供商ID格式"""
        if not v or not v.strip():
            raise ValueError("Provider ID cannot be empty")
        # 确保ID只包含字母、数字、下划线和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Provider ID can only contain letters, numbers, underscores and hyphens")
        return v.strip().lower()
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        """验证模型名称"""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """验证基础URL格式"""
        if v is not None:
            v = v.strip()
            if v and not v.startswith(('http://', 'https://')):
                raise ValueError("Base URL must start with http:// or https://")
        return v


class LLMConfiguration(BaseModel):
    """LLM完整配置"""
    version: str = Field("1.0", description="配置版本")
    name: str = Field("LLM配置", description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    
    # 全局启用状态
    enabled: bool = Field(True, description="是否启用LLM功能")
    
    # 提供商配置
    providers: List[LLMProviderConfig] = Field(default_factory=list, description="LLM提供商列表")
    default_provider: str = Field("openai", description="默认提供商ID")
    
    # 全局默认配置
    global_defaults: Dict[str, Any] = Field(
        default_factory=lambda: {
            "temperature": 0.7,
            "max_tokens": 2000,
            "timeout": 30,
            "max_retries": 3,
            "stream": False
        },
        description="全局默认配置"
    )
    
    # 安全配置
    security: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "enable_data_masking": True,
            "mask_sensitive_data": True,
            "allowed_hosts": [],
            "blocked_patterns": []
        },
        description="安全配置"
    )
    
    # 日志配置
    logging: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "enable_request_logging": True,
            "enable_response_logging": False,
            "log_sensitive_data": False
        },
        description="日志配置"
    )
    
    # 缓存配置
    cache: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "enabled": False,
            "ttl": 3600,
            "max_size": 1000
        },
        description="缓存配置"
    )
    
    # 监控配置
    monitoring: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "enabled": True,
            "collect_metrics": True,
            "alert_on_errors": True,
            "performance_threshold": 5.0
        },
        description="监控配置"
    )
    
    @field_validator('default_provider')
    @classmethod
    def validate_default_provider(cls, v, info):
        """验证默认提供商是否存在"""
        if not v or not v.strip():
            raise ValueError("Default provider cannot be empty")
        return v.strip().lower()
    
    def get_provider(self, provider_id: str) -> Optional[LLMProviderConfig]:
        """根据ID获取提供商配置"""
        for provider in self.providers:
            if provider.id == provider_id:
                return provider
        return None
    
    def get_enabled_providers(self) -> List[LLMProviderConfig]:
        """获取所有启用的提供商"""
        return [provider for provider in self.providers if provider.enabled]
    
    def get_default_provider_config(self) -> Optional[LLMProviderConfig]:
        """获取默认提供商配置"""
        return self.get_provider(self.default_provider)
    
    def add_provider(self, provider: LLMProviderConfig) -> bool:
        """添加提供商配置"""
        # 检查ID是否已存在
        if any(p.id == provider.id for p in self.providers):
            return False
        self.providers.append(provider)
        return True
    
    def remove_provider(self, provider_id: str) -> bool:
        """删除提供商配置"""
        original_count = len(self.providers)
        self.providers = [p for p in self.providers if p.id != provider_id]
        return len(self.providers) < original_count
    
    def update_provider(self, provider_id: str, provider: LLMProviderConfig) -> bool:
        """更新提供商配置"""
        for i, p in enumerate(self.providers):
            if p.id == provider_id:
                self.providers[i] = provider
                return True
        return False


# 预定义的提供商模板
DEFAULT_PROVIDER_TEMPLATES = {
    "openai": LLMProviderConfig(
        id="openai",
        name="OpenAI",
        model="gpt-3.5-turbo",
        base_url="https://api.openai.com/v1",
        supports_functions=True,
        supports_vision=False,
        supports_streaming=True
    ),
    "azure": LLMProviderConfig(
        id="azure",
        name="Azure OpenAI",
        model="gpt-35-turbo",
        supports_functions=True,
        supports_vision=False,
        supports_streaming=True
    ),
    "ollama": LLMProviderConfig(
        id="ollama",
        name="Ollama",
        model="llama3.1:8b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama使用固定的API key
        supports_functions=True,
        supports_vision=False,
        supports_streaming=True
    ),
    "zhipu": LLMProviderConfig(
        id="zhipu",
        name="智谱AI",
        model="glm-4",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        supports_functions=True,
        supports_vision=False,
        supports_streaming=True
    ),
    "qwen": LLMProviderConfig(
        id="qwen",
        name="通义千问",
        model="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        supports_functions=True,
        supports_vision=False,
        supports_streaming=True
    )
}


def create_default_configuration() -> LLMConfiguration:
    """创建默认配置"""
    config = LLMConfiguration(
        name="默认LLM配置",
        description="系统默认的LLM配置，包含常用提供商",
        providers=[DEFAULT_PROVIDER_TEMPLATES["openai"]],
        default_provider="openai"
    )
    return config


def load_configuration_from_file(file_path: str) -> LLMConfiguration:
    """从文件加载配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return LLMConfiguration(**config_data)
    except Exception as e:
        logger.error(f"Failed to load LLM configuration from {file_path}: {e}")
        raise


def save_configuration_to_file(config: LLMConfiguration, file_path: str) -> None:
    """保存配置到文件"""
    try:
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                config.model_dump(),
                f,
                ensure_ascii=False,
                indent=2
            )
        logger.info(f"LLM configuration saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save LLM configuration to {file_path}: {e}")
        raise 