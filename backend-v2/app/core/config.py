"""统一配置管理 - ENV > JSON > 默认值"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import dotenv_values


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
    llm_config_path: str = Field(default="config/llm_config.json", alias="LLM_CONFIG_PATH")

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
    k8s_mcp_enabled: bool = Field(default=True, alias="K8S_MCP_ENABLED")
    kubeconfig_path: Optional[str] = Field(default=None, alias="KUBECONFIG_PATH")
    k8s_namespace: str = Field(default="default", alias="K8S_NAMESPACE")
    k8s_in_cluster: bool = Field(default=False, alias="K8S_IN_CLUSTER")
    k8s_knowledge_graph_path: str = Field(
        default="backend-v2/data/k8s_knowledge_graph.json",
        alias="K8S_KNOWLEDGE_GRAPH_PATH",
    )
    prometheus_base_url: Optional[str] = Field(default=None, alias="PROMETHEUS_BASE_URL")

    # --- 阿里云 ECS ---
    ecs_mcp_enabled: bool = Field(default=False, alias="ECS_MCP_ENABLED")
    alibaba_access_key_id: Optional[str] = Field(default=None, alias="ALIBABA_CLOUD_ACCESS_KEY_ID")
    alibaba_access_key_secret: Optional[str] = Field(default=None, alias="ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    alibaba_region_id: str = Field(default="cn-hangzhou", alias="ALIBABA_CLOUD_REGION_ID")

    # --- 阿里云只读 Adapter ---
    aliyun_mcp_enabled: bool = Field(default=False, alias="ALIYUN_MCP_ENABLED")
    aliyun_access_key_id: Optional[str] = Field(default=None, alias="ALIYUN_ACCESS_KEY_ID")
    aliyun_access_key_secret: Optional[str] = Field(default=None, alias="ALIYUN_ACCESS_KEY_SECRET")
    aliyun_default_region_id: str = Field(default="cn-hangzhou", alias="ALIYUN_DEFAULT_REGION_ID")
    aliyun_allowed_regions: list[str] = Field(default_factory=list, alias="ALIYUN_ALLOWED_REGIONS")
    aliyun_required_tags: dict[str, list[str]] = Field(default_factory=dict, alias="ALIYUN_REQUIRED_TAGS")
    aliyun_allowed_instance_ids: list[str] = Field(default_factory=list, alias="ALIYUN_ALLOWED_INSTANCE_IDS")
    aliyun_sls_mappings: list[dict[str, Any]] = Field(default_factory=list, alias="ALIYUN_SLS_MAPPINGS")

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
    settings = AppSettings()
    _apply_llm_json_config(settings)
    _apply_mcp_json_config(settings)
    if _is_placeholder_secret(settings.llm_api_key):
        settings.llm_api_key = ""
    if _is_placeholder_secret(settings.alibaba_access_key_id):
        settings.alibaba_access_key_id = None
    if _is_placeholder_secret(settings.alibaba_access_key_secret):
        settings.alibaba_access_key_secret = None
    if _is_placeholder_secret(settings.aliyun_access_key_id):
        settings.aliyun_access_key_id = None
    if _is_placeholder_secret(settings.aliyun_access_key_secret):
        settings.aliyun_access_key_secret = None
    if not settings.aliyun_allowed_regions:
        settings.aliyun_allowed_regions = [settings.aliyun_default_region_id]
    return settings


def resolve_repo_path(path: str) -> Path:
    target = Path(path)
    if target.is_absolute():
        return target
    candidates = [
        Path.cwd() / target,
        _repo_root() / target,
        _repo_root() / "backend-v2" / target,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def is_placeholder_secret(value: Optional[str]) -> bool:
    return _is_placeholder_secret(value)


def _apply_llm_json_config(settings: AppSettings) -> None:
    config_path = resolve_repo_path(settings.llm_config_path)
    if not config_path.exists():
        return
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    provider = _select_llm_provider(config)
    security = config.get("security", {}) if isinstance(config.get("security"), dict) else {}
    mapping: dict[str, tuple[str, Any]] = {
        "llm_enabled": ("LLM_ENABLED", config.get("enabled")),
        "llm_model": ("LLM_MODEL", provider.get("model")),
        "llm_api_key": ("LLM_API_KEY", provider.get("api_key")),
        "llm_base_url": ("LLM_BASE_URL", provider.get("base_url")),
        "llm_temperature": ("LLM_TEMPERATURE", provider.get("temperature")),
        "llm_max_tokens": ("LLM_MAX_TOKENS", provider.get("max_tokens")),
        "llm_timeout": ("LLM_TIMEOUT", provider.get("timeout")),
        "masking_enabled": ("LLM_MASKING_ENABLED", security.get("enable_data_masking")),
    }
    for field_name, (env_name, value) in mapping.items():
        if value is None or _has_env_value(env_name):
            continue
        setattr(settings, field_name, value)


def _apply_mcp_json_config(settings: AppSettings) -> None:
    config_path = resolve_repo_path(settings.mcp_config_path)
    if not config_path.exists():
        return
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    builtin = config.get("builtin", {}) if isinstance(config.get("builtin"), dict) else {}
    k8s = builtin.get("k8s", {}) if isinstance(builtin.get("k8s"), dict) else {}
    ecs = builtin.get("ecs", {}) if isinstance(builtin.get("ecs"), dict) else {}
    aliyun = builtin.get("aliyun", {}) if isinstance(builtin.get("aliyun"), dict) else {}
    aliyun_sls = aliyun.get("sls", {}) if isinstance(aliyun.get("sls"), dict) else {}

    mapping: dict[str, tuple[str, Any]] = {
        "k8s_mcp_enabled": ("K8S_MCP_ENABLED", k8s.get("enabled")),
        "kubeconfig_path": ("KUBECONFIG_PATH", k8s.get("kubeconfig_path")),
        "k8s_namespace": ("K8S_NAMESPACE", k8s.get("namespace")),
        "k8s_in_cluster": ("K8S_IN_CLUSTER", k8s.get("in_cluster")),
        "k8s_knowledge_graph_path": ("K8S_KNOWLEDGE_GRAPH_PATH", k8s.get("knowledge_graph_path")),
        "prometheus_base_url": ("PROMETHEUS_BASE_URL", k8s.get("prometheus_base_url")),
        "ecs_mcp_enabled": ("ECS_MCP_ENABLED", ecs.get("enabled")),
        "alibaba_access_key_id": ("ALIBABA_CLOUD_ACCESS_KEY_ID", ecs.get("access_key_id")),
        "alibaba_access_key_secret": ("ALIBABA_CLOUD_ACCESS_KEY_SECRET", ecs.get("access_key_secret")),
        "alibaba_region_id": ("ALIBABA_CLOUD_REGION_ID", ecs.get("region_id")),
        "aliyun_mcp_enabled": ("ALIYUN_MCP_ENABLED", aliyun.get("enabled")),
        "aliyun_access_key_id": ("ALIYUN_ACCESS_KEY_ID", aliyun.get("access_key_id")),
        "aliyun_access_key_secret": ("ALIYUN_ACCESS_KEY_SECRET", aliyun.get("access_key_secret")),
        "aliyun_default_region_id": ("ALIYUN_DEFAULT_REGION_ID", aliyun.get("default_region_id")),
        "aliyun_allowed_regions": ("ALIYUN_ALLOWED_REGIONS", aliyun.get("allowed_regions")),
        "aliyun_required_tags": ("ALIYUN_REQUIRED_TAGS", aliyun.get("required_tags")),
        "aliyun_allowed_instance_ids": ("ALIYUN_ALLOWED_INSTANCE_IDS", aliyun.get("allowed_instance_ids")),
        "aliyun_sls_mappings": ("ALIYUN_SLS_MAPPINGS", aliyun_sls.get("mappings")),
    }
    for field_name, (env_name, value) in mapping.items():
        if value is None or _has_process_env_value(env_name):
            continue
        setattr(settings, field_name, value)


def _select_llm_provider(config: dict[str, Any]) -> dict[str, Any]:
    providers = config.get("providers", [])
    if not isinstance(providers, list) or not providers:
        return {}
    default_provider = config.get("default_provider")
    for provider in providers:
        if isinstance(provider, dict) and provider.get("id") == default_provider:
            return provider
    first = providers[0]
    return first if isinstance(first, dict) else {}


def _has_env_value(name: str) -> bool:
    if name in os.environ:
        return True
    for env_file in _env_files():
        if not env_file.exists():
            continue
        value = dotenv_values(env_file).get(name)
        if value not in (None, "") and not _is_placeholder_secret(value):
            return True
    return False


def _has_process_env_value(name: str) -> bool:
    value = os.environ.get(name)
    return value not in (None, "") and not _is_placeholder_secret(value)


def _is_placeholder_secret(value: Optional[str]) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if not normalized:
        return False
    placeholders = {
        "your_api_key_here",
        "replace-with-local-secret",
        "replace-with-your-key",
        "change-me",
        "change-me-in-production",
    }
    return normalized in placeholders or normalized.startswith("your_")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _env_files() -> list[Path]:
    return [
        Path.cwd() / ".env",
        _repo_root() / ".env",
        _repo_root() / "backend-v2" / ".env",
    ]
