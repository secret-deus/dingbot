"""Runtime LLM configuration store.

The UI-managed configuration is intentionally read from disk for every new
message so model/API changes can take effect without restarting FastAPI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings, is_placeholder_secret, resolve_repo_path


DEFAULT_PROVIDER_ID = "openai-compatible"
DEFAULT_PROVIDER_NAME = "OpenAI compatible endpoint"


@dataclass(frozen=True)
class LLMProviderRuntime:
    id: str
    name: str
    enabled: bool
    model: str
    api_key: str
    base_url: Optional[str]
    temperature: float
    max_tokens: int
    timeout: int
    stream: bool

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key and not is_placeholder_secret(self.api_key))

    @property
    def active(self) -> bool:
        return bool(self.enabled and self.model and self.api_key_configured)


@dataclass(frozen=True)
class LLMRuntimeConfig:
    enabled: bool
    masking_enabled: bool
    config_path: Path
    source: str
    default_provider: Optional[str]
    selected_provider_id: Optional[str]
    providers: list[dict[str, Any]]
    provider: Optional[LLMProviderRuntime]

    @property
    def active(self) -> bool:
        return bool(self.enabled and self.provider and self.provider.active)

    @property
    def configured(self) -> bool:
        return bool(self.enabled and any(p.get("api_key_configured") for p in self.providers))


def load_llm_runtime(provider_id: Optional[str] = None) -> LLMRuntimeConfig:
    settings = get_settings()
    config_path = resolve_repo_path(settings.llm_config_path)
    document, source = read_llm_document(config_path)
    providers = _provider_list(document)

    if not providers and source != "json":
        providers = [_provider_from_settings(settings)]
        document["providers"] = providers
        document["default_provider"] = providers[0]["id"]
        document.setdefault("enabled", settings.llm_enabled)

    selected = select_provider(document, provider_id)
    security = document.get("security", {}) if isinstance(document.get("security"), dict) else {}
    enabled = bool(document.get("enabled", settings.llm_enabled))
    masking_enabled = bool(security.get("enable_data_masking", settings.masking_enabled))

    public_providers = [public_provider(provider) for provider in providers]
    runtime_provider = provider_to_runtime(selected) if selected else None
    selected_provider_id = runtime_provider.id if runtime_provider else None

    return LLMRuntimeConfig(
        enabled=enabled,
        masking_enabled=masking_enabled,
        config_path=config_path,
        source=source,
        default_provider=document.get("default_provider"),
        selected_provider_id=selected_provider_id,
        providers=public_providers,
        provider=runtime_provider,
    )


def read_llm_document(config_path: Optional[Path] = None) -> tuple[dict[str, Any], str]:
    path = config_path or resolve_repo_path(get_settings().llm_config_path)
    if path.exists():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            return _normalize_document(document), "json"
        except (OSError, json.JSONDecodeError):
            pass

    example_path = resolve_repo_path("config/llm_config.example.json")
    if example_path.exists():
        try:
            document = json.loads(example_path.read_text(encoding="utf-8"))
            return _normalize_document(document), "example"
        except (OSError, json.JSONDecodeError):
            pass

    return _normalize_document({}), "default"


def write_llm_document(document: dict[str, Any], config_path: Optional[Path] = None) -> None:
    path = config_path or resolve_repo_path(get_settings().llm_config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_document(document), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_provider(document: dict[str, Any], provider_id: Optional[str] = None) -> dict[str, Any]:
    providers = _provider_list(document)
    if not providers:
        return {}

    wanted = provider_id or document.get("default_provider")
    for provider in providers:
        if provider.get("id") == wanted:
            return provider
    return providers[0]


def public_provider(provider: dict[str, Any]) -> dict[str, Any]:
    api_key = provider.get("api_key")
    api_key_placeholder = is_placeholder_secret(api_key)
    return {
        "id": provider.get("id", ""),
        "name": provider.get("name") or provider.get("id", ""),
        "enabled": bool(provider.get("enabled", True)),
        "model": provider.get("model", ""),
        "base_url": provider.get("base_url"),
        "temperature": _as_float(provider.get("temperature"), 0.3),
        "max_tokens": _as_int(provider.get("max_tokens"), 2000),
        "timeout": _as_int(provider.get("timeout"), 60),
        "stream": bool(provider.get("stream", True)),
        "api_key_configured": bool(api_key and not api_key_placeholder),
        "api_key_placeholder": api_key_placeholder,
    }


def provider_to_runtime(provider: dict[str, Any]) -> LLMProviderRuntime:
    api_key = provider.get("api_key") or ""
    if is_placeholder_secret(api_key):
        api_key = ""
    return LLMProviderRuntime(
        id=str(provider.get("id") or DEFAULT_PROVIDER_ID),
        name=str(provider.get("name") or provider.get("id") or DEFAULT_PROVIDER_NAME),
        enabled=bool(provider.get("enabled", True)),
        model=str(provider.get("model") or ""),
        api_key=str(api_key),
        base_url=provider.get("base_url") or None,
        temperature=_as_float(provider.get("temperature"), 0.3),
        max_tokens=_as_int(provider.get("max_tokens"), 2000),
        timeout=_as_int(provider.get("timeout"), 60),
        stream=bool(provider.get("stream", True)),
    )


def upsert_provider(document: dict[str, Any], provider_updates: dict[str, Any]) -> dict[str, Any]:
    providers = document.setdefault("providers", [])
    if not isinstance(providers, list):
        providers = []
        document["providers"] = providers

    requested_id = normalize_provider_id(provider_updates.get("id") or provider_updates.get("name") or DEFAULT_PROVIDER_ID)
    provider = next((item for item in providers if isinstance(item, dict) and item.get("id") == requested_id), None)
    if provider is None:
        provider = _default_provider(requested_id)
        providers.append(provider)

    allowed_fields = {
        "name",
        "enabled",
        "model",
        "base_url",
        "temperature",
        "max_tokens",
        "timeout",
        "stream",
    }
    for field in allowed_fields:
        if field in provider_updates:
            provider[field] = provider_updates[field]

    api_key = provider_updates.get("api_key")
    if isinstance(api_key, str) and api_key.strip():
        provider["api_key"] = api_key.strip()

    if not document.get("default_provider"):
        document["default_provider"] = provider["id"]
    return provider


def delete_provider(document: dict[str, Any], provider_id: str) -> bool:
    providers = _provider_list(document)
    remaining = [provider for provider in providers if provider.get("id") != provider_id]
    if len(remaining) == len(providers):
        return False

    document["providers"] = remaining
    if document.get("default_provider") == provider_id:
        document["default_provider"] = remaining[0]["id"] if remaining else None
    return True


def normalize_provider_id(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", str(value or "").strip().lower()).strip("-_")
    return normalized or DEFAULT_PROVIDER_ID


def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        document = {}
    document.setdefault("version", "runtime")
    document.setdefault("name", "LLM配置")
    document.setdefault("description", "由本地管理页维护的运行时配置")
    document.setdefault("enabled", False)
    document.setdefault("providers", [])
    document.setdefault("default_provider", None)
    document.setdefault("global_defaults", {"temperature": 0.3, "max_tokens": 2000, "timeout": 60, "stream": True})
    document.setdefault("security", {"enable_data_masking": True, "mask_sensitive_data": True})
    if not isinstance(document["providers"], list):
        document["providers"] = []
    return document


def _provider_list(document: dict[str, Any]) -> list[dict[str, Any]]:
    providers = document.get("providers", [])
    return [provider for provider in providers if isinstance(provider, dict)]


def _default_provider(provider_id: str) -> dict[str, Any]:
    return {
        "id": provider_id,
        "name": provider_id,
        "enabled": True,
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout": 60,
        "stream": True,
        "supports_functions": True,
        "supports_streaming": True,
    }


def _provider_from_settings(settings: Any) -> dict[str, Any]:
    return {
        "id": DEFAULT_PROVIDER_ID,
        "name": DEFAULT_PROVIDER_NAME,
        "enabled": settings.llm_enabled,
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
        "stream": True,
    }


def _as_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default
