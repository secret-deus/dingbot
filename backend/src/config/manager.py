"""
配置管理器 - 集成文件配置和环境变量配置
支持配置文件优先、环境变量fallback的混合策略
"""

import os
from typing import Dict, Any, Optional
from loguru import logger
from dotenv import load_dotenv

try:
    from ..llm.config_manager import LLMConfigManager, get_llm_config_manager
    from ..llm.config import LLMConfiguration, LLMProviderConfig
except ImportError:
    # 处理测试环境的导入问题
    try:
        from llm.config_manager import LLMConfigManager, get_llm_config_manager
        from llm.config import LLMConfiguration, LLMProviderConfig
    except ImportError:
        # 如果都导入失败，设置为None（fallback模式）
        LLMConfigManager = None
        get_llm_config_manager = None
        LLMConfiguration = None
        LLMProviderConfig = None


class ConfigValidationError(Exception):
    """配置验证错误"""
    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigManager:
    """增强的配置管理器 - 支持文件配置和环境变量配置的混合策略"""

    def __init__(self):
        self.env_file_path = self._find_env_file()
        # 加载环境变量
        load_dotenv(self.env_file_path, override=True)

        # 初始化LLM配置管理器
        try:
            if get_llm_config_manager is not None:
                self.llm_config_manager = get_llm_config_manager()
                # 检查是否成功从环境变量迁移
                if hasattr(self.llm_config_manager, '_migration_performed'):
                    logger.info("✅ 已从环境变量迁移到LLM配置文件")
            else:
                logger.warning("LLM配置管理器模块未能导入，使用环境变量模式")
                self.llm_config_manager = None
        except Exception as e:
            logger.warning(f"LLM配置管理器初始化失败: {e}")
            self.llm_config_manager = None

    def _find_env_file(self) -> str:
        """查找环境变量文件"""
        possible_paths = [
            "config.env",
            ".env",
            "backend/config.env",
            "backend/.env"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果都不存在，使用config.env作为默认
        return "config.env"

    async def get_current_llm_config(self) -> Dict[str, Any]:
        """
        获取当前LLM配置 - 优先从文件读取，fallback到环境变量
        保持输出格式与现有系统兼容
        """
        try:
            # 优先尝试从文件配置读取
            if self.llm_config_manager:
                config = self.llm_config_manager.get_config()
                provider_config = config.get_default_provider_config()

                if provider_config and config.enabled:
                    # 转换为兼容的字典格式
                    config_dict = self._convert_file_config_to_dict(config, provider_config)
                    logger.info(f"✅ 从配置文件加载LLM配置: {config_dict.get('provider', 'unknown')} - {config_dict.get('model', 'unknown')}")
                    return config_dict
                else:
                    logger.warning("文件配置中没有有效的默认提供商，fallback到环境变量")
        except Exception as e:
            logger.warning(f"文件配置读取失败: {e}，fallback到环境变量")

        # Fallback到环境变量配置
        return await self._get_env_llm_config()

    def _convert_file_config_to_dict(self, config: Any, provider: Any) -> Dict[str, Any]:
        """将文件配置转换为兼容的字典格式"""
        config_dict = {
            "enabled": config.enabled,
            "provider": provider.id,
            "model": provider.model,
            "api_key": provider.api_key,
            "base_url": provider.base_url,
            "organization": provider.organization,
            "api_version": provider.api_version,
            "deployment_name": provider.deployment_name,
            "timeout": provider.timeout,
            "max_retries": provider.max_retries,
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens,
            "stream": provider.stream
        }

        # 移除空值但保留重要字段
        filtered_config = {}
        important_fields = {"enabled", "provider", "model", "timeout", "max_retries", "temperature", "max_tokens", "stream"}

        for key, value in config_dict.items():
            if key in important_fields:
                filtered_config[key] = value
            elif value is not None and value != "":
                filtered_config[key] = value

        return filtered_config

    async def _get_env_llm_config(self) -> Dict[str, Any]:
        """从环境变量获取LLM配置（保持原有逻辑）"""
        try:
            # 重新加载环境变量确保最新
            load_dotenv(self.env_file_path, override=True)

            config_data = {
                "enabled": os.getenv("LLM_ENABLED", "true").lower() == "true",
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                "api_key": os.getenv("LLM_API_KEY", ""),
                "base_url": os.getenv("LLM_BASE_URL"),
                "organization": os.getenv("LLM_ORGANIZATION"),
                "api_version": os.getenv("LLM_API_VERSION"),
                "deployment_name": os.getenv("LLM_DEPLOYMENT_NAME"),
                "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
                "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
                "stream": os.getenv("LLM_STREAM", "false").lower() == "true"
            }

            # 移除空值
            filtered_config = {k: v for k, v in config_data.items() if v is not None and v != ""}
            # 但保留重要字段
            important_fields = {"enabled", "provider", "model", "api_key", "timeout", "max_retries", "temperature", "max_tokens", "stream"}
            for field in important_fields:
                if field not in filtered_config and field in config_data:
                    filtered_config[field] = config_data[field]

            logger.info(f"✅ 从环境变量加载LLM配置: {filtered_config.get('provider', 'unknown')} - {filtered_config.get('model', 'unknown')}")
            return filtered_config

        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}")
            # 返回默认配置
            return {
                "enabled": True,
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": "",
                "timeout": 30,
                "max_retries": 3,
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }

    async def get_current_mcp_config(self) -> Dict[str, Any]:
        """从环境变量获取MCP配置"""
        try:
            load_dotenv(self.env_file_path, override=True)

            config_data = {
                "timeout": int(os.getenv("MCP_TIMEOUT", "30000")),
                "retry_attempts": int(os.getenv("MCP_RETRY_ATTEMPTS", "3")),
                "retry_delay": int(os.getenv("MCP_RETRY_DELAY", "1000")),
                "max_concurrent_calls": int(os.getenv("MCP_MAX_CONCURRENT_CALLS", "5")),
                "enable_cache": os.getenv("MCP_ENABLE_CACHE", "true").lower() == "true",
                "cache_timeout": int(os.getenv("MCP_CACHE_TIMEOUT", "300000"))
            }

            logger.info("✅ 从环境变量加载MCP配置")
            return config_data

        except Exception as e:
            logger.error(f"获取MCP配置失败: {e}")
            # 返回默认配置
            return {
                "timeout": 30000,
                "retry_attempts": 3,
                "retry_delay": 1000,
                "max_concurrent_calls": 5,
                "enable_cache": True,
                "cache_timeout": 300000
            }

    def get_llm_config_manager(self) -> Optional[Any]:
        """获取LLM配置管理器实例"""
        return self.llm_config_manager

    async def reload_llm_config(self):
        """重新加载LLM配置"""
        try:
            if self.llm_config_manager:
                self.llm_config_manager.reload_config()
                logger.info("✅ LLM配置已重新加载")
            else:
                logger.warning("LLM配置管理器未初始化，无法重新加载")
        except Exception as e:
            logger.error(f"重新加载LLM配置失败: {e}")


# 全局配置管理器实例
config_manager = ConfigManager()