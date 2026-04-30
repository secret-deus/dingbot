from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v2.endpoints.auth import router as auth_router
from src.api.v2.endpoints.llm_config import get_config_manager, router as llm_config_router
from src.security.audit import get_audit_logger
from src.security.auth import get_auth_service
from src.security.user_store import get_user_store


def reset_security_caches():
    get_user_store.cache_clear()
    get_auth_service.cache_clear()
    get_audit_logger.cache_clear()


def login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "ding2024"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_sensitive_v2_routes_reject_anonymous(monkeypatch, tmp_path):
    monkeypatch.setenv("IAM_USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "ding2024")
    monkeypatch.setenv("OPERATION_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    reset_security_caches()

    import main

    client = TestClient(main.app)
    routes = [
        ("GET", "/api/v2/llm/config/current"),
        ("GET", "/api/v2/config/llm"),
        ("PUT", "/api/v2/config/llm"),
        ("POST", "/api/v2/config/llm/reload"),
        ("PUT", "/api/v2/config/mcp"),
        ("POST", "/api/v2/resources/update-metrics"),
        ("GET", "/api/v2/resources/metrics-coverage"),
        ("POST", "/api/v2/inspection/run"),
        ("GET", "/api/v2/debug/logs"),
        ("POST", "/api/v2/alerts/test"),
    ]

    for method, path in routes:
        response = client.request(method, path, json={})
        assert response.status_code == 401, f"{method} {path}"
        assert response.json()["success"] is False


def test_mcp_config_file_path_is_restricted(monkeypatch, tmp_path):
    monkeypatch.setenv("IAM_USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "ding2024")
    monkeypatch.setenv("OPERATION_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    reset_security_caches()

    import main

    client = TestClient(main.app)
    token = login_admin(client)
    response = client.get(
        "/api/v2/mcp/config/file",
        params={"path": "config/security/users.json"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


class FakeProvider:
    def model_dump(self):
        return {
            "id": "openai",
            "name": "OpenAI",
            "enabled": True,
            "model": "gpt-4.1-mini",
            "api_key": "sk-super-secret-value",
            "base_url": "https://example.test/v1",
        }


class FakeLLMConfigManager:
    def get_config(self):
        return SimpleNamespace(
            version="1.0",
            name="LLM",
            description="test",
            enabled=True,
            providers=[FakeProvider()],
            default_provider="openai",
            global_defaults={"api_key": "global-secret-value"},
            security={},
            logging={},
            cache={},
        )


def test_llm_config_current_redacts_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("IAM_USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "ding2024")
    monkeypatch.setenv("OPERATION_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    reset_security_caches()

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v2")
    app.include_router(llm_config_router, prefix="/api/v2")
    app.dependency_overrides[get_config_manager] = lambda: FakeLLMConfigManager()
    client = TestClient(app)
    token = login_admin(client)

    response = client.get(
        "/api/v2/llm/config/current",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["providers"][0]["api_key"] != "sk-super-secret-value"
    assert body["global_defaults"]["api_key"] != "global-secret-value"
