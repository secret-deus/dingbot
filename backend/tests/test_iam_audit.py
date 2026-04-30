from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v2.endpoints.audit import router as audit_router
from src.api.v2.endpoints.auth import router as auth_router
from src.api.v2.endpoints.users import router as users_router
from src.security.audit import get_audit_logger
from src.security.auth import get_auth_service
from src.security.user_store import get_user_store


def reset_security_caches():
    get_user_store.cache_clear()
    get_auth_service.cache_clear()
    get_audit_logger.cache_clear()


def build_app():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v2")
    app.include_router(users_router, prefix="/api/v2")
    app.include_router(audit_router, prefix="/api/v2")
    return app


def test_login_me_and_user_management_use_standard_envelope(monkeypatch, tmp_path):
    monkeypatch.setenv("IAM_USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "ding2024")
    monkeypatch.setenv("OPERATION_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    reset_security_caches()

    client = TestClient(build_app())

    login_response = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "ding2024"},
        headers={"X-Request-ID": "iam-test-001"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["success"] is True
    assert login_body["meta"]["request_id"] == "iam-test-001"
    assert login_body["data"]["user"]["username"] == "admin"
    assert "password_hash" not in login_body["data"]["user"]
    token = login_body["data"]["access_token"]

    auth_headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v2/auth/me", headers=auth_headers)
    assert me_response.status_code == 200
    assert me_response.json()["data"]["user"]["permissions"] == ["*"]

    create_response = client.post(
        "/api/v2/users",
        json={
            "username": "ops",
            "display_name": "Ops Engineer",
            "password": "change-me",
            "roles": ["viewer"],
            "enabled": True,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    created_user = create_response.json()["data"]["user"]
    assert created_user["username"] == "ops"
    assert created_user["permissions"]
    assert "password_hash" not in created_user

    users_response = client.get("/api/v2/users", headers=auth_headers)
    assert users_response.status_code == 200
    body = users_response.json()["data"]
    assert {user["username"] for user in body["users"]} == {"admin", "ops"}
    assert "users:write" in body["permissions"]


def test_audit_logs_are_readable_with_permission(monkeypatch, tmp_path):
    monkeypatch.setenv("IAM_USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_SESSION_SECRET", "test-secret")
    monkeypatch.setenv("APP_ADMIN_PASSWORD", "ding2024")
    monkeypatch.setenv("OPERATION_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))
    reset_security_caches()

    client = TestClient(build_app())
    token = client.post(
        "/api/v2/auth/login",
        json={"username": "admin", "password": "ding2024"},
    ).json()["data"]["access_token"]

    get_audit_logger().record(
        actor="admin",
        action="users.create",
        resource="user",
        result="success",
        details={"token": "super-secret-token-value"},
    )

    logs_response = client.get(
        "/api/v2/audit/logs?limit=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logs_response.status_code == 200
    items = logs_response.json()["data"]["items"]
    assert items
    assert items[0]["actor"] == "admin"
    assert items[0]["details"]["token"] != "super-secret-token-value"
