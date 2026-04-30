"""统一配置管理 - Pydantic Settings, ENV > JSON > 默认值"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # --- 应用 ---
    app_name: str = "ding-robot"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # --- 数据库 ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        alias="DATABASE_URL",
    )

    # --- LLM (LiteLLM) ---
    llm_enabled: bool = True
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2000
    llm_timeout: int = 60

    # --- 数据脱敏 ---
    masking_enabled: bool = Field(default=True, alias="LLM_MASKING_ENABLED")
    masking_key: Optional[str] = Field(default=None, alias="LLM_MASKING_KEY")

    # --- MCP ---
    mcp_config_path: str = Field(
        default="config/mcp_config.json",
        alias="MCP_CONFIG_PATH",
    )
    mcp_timeout: int = 600

    # --- K8s ---
    kubeconfig_path: Optional[str] = Field(default=None, alias="KUBECONFIG_PATH")
    k8s_namespace: str = Field(default="default", alias="K8S_NAMESPACE")
    k8s_in_cluster: bool = Field(default=False, alias="K8S_IN_CLUSTER")

    # --- 阿里云 ECS ---
    alibaba_access_key_id: Optional[str] = Field(default=None, alias="ALIBABA_CLOUD_ACCESS_KEY_ID")
    alibaba_access_key_secret: Optional[str] = Field(default=None, alias="ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    alibaba_region_id: str = Field(default="cn-hangzhou", alias="ALIBABA_CLOUD_REGION_ID")

    # --- 钉钉 ---
    dingtalk_webhook_url: Optional[str] = Field(default=None, alias="DINGTALK_WEBHOOK_URL")
    dingtalk_secret: Optional[str] = Field(default=None, alias="DINGTALK_SECRET")

    # --- 调度器 ---
    scheduler_enabled: bool = True

    # --- 技能配置 ---
    skills_config_path: str = Field(
        default="config/skills.json",
        alias="SKILLS_CONFIG_PATH",
    )


def get_settings() -> AppSettings:
    return AppSettings()
