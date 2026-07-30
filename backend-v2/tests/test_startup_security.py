from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_production_startup_rejects_insecure_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "admin")

    from app.core.config import get_settings, validate_startup_security

    with pytest.raises(RuntimeError) as exc:
        validate_startup_security(get_settings())

    message = str(exc.value)
    assert "SECRET_KEY" in message
    assert "CORS_ALLOW_ORIGINS" in message
    assert "BOOTSTRAP_ADMIN_PASSWORD" in message


def test_production_startup_accepts_hardened_settings(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://ops.example.com")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "replace-this-local-admin-password")

    from app.core.config import get_settings, validate_startup_security

    validate_startup_security(get_settings())


def test_bootstrap_admin_uses_configured_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-enough-length")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_USERNAME", "root-admin")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "local-root-admin-password")

    from app.main import app

    with TestClient(app) as client:
        configured = client.post(
            "/api/v2/auth/login",
            json={"username": "root-admin", "password": "local-root-admin-password"},
        )
        assert configured.status_code == 200

        default = client.post(
            "/api/v2/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert default.status_code == 401
