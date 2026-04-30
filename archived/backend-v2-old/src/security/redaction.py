"""Shared log and response redaction helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "access_key",
    "access_key_id",
    "access_key_secret",
    "authorization",
    "auth_header",
    "auth_headers",
    "auth_token",
    "bearer",
    "secret",
    "security_token",
    "sessionwebhook",
    "session_webhook",
    "token",
    "webhook",
    "webhook_url",
}

SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|sessionWebhook|webhook)"
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.replace("-", "_").lower()
    return normalized in SENSITIVE_KEYS or bool(SENSITIVE_PATTERN.search(key))


def mask_secret(value: Any) -> str:
    text = str(value)
    if not text:
        return "***"
    if len(text) <= 8:
        return "***"
    return f"{text[:2]}***{text[-4:]}"


def redact(value: Any) -> Any:
    """Recursively redact sensitive mappings and dataclass/model objects."""
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        if SENSITIVE_PATTERN.search(value) and len(value) > 16:
            return "***"
        return value
    if isinstance(value, Mapping):
        return {
            key: mask_secret(item) if is_sensitive_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        redacted = [redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(redacted)
        if isinstance(value, set):
            return set(redacted)
        return redacted
    if hasattr(value, "model_dump"):
        return redact(value.model_dump())
    if is_dataclass(value):
        return redact(asdict(value))
    if hasattr(value, "__dict__"):
        return redact(vars(value))
    return value


def redact_for_log(value: Any) -> str:
    return str(redact(value))
