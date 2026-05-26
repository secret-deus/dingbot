from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_can_list_create_and_update_users(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.main import app

    with TestClient(app) as client:
        admin_token = _login(client, "admin", "admin")

        created = client.post(
            "/api/v2/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "ops-user",
                "password": "ops-pass",
                "role": "operator",
                "display_name": "Ops User",
            },
        )
        assert created.status_code == 201

        listed = client.get(
            "/api/v2/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert listed.status_code == 200
        users = {item["username"]: item for item in listed.json()}
        assert users["ops-user"]["display_name"] == "Ops User"
        assert users["ops-user"]["role"] == "operator"
        assert users["ops-user"]["is_active"] is True
        assert users["ops-user"]["created_at"]

        updated = client.patch(
            "/api/v2/auth/users/ops-user",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "viewer", "display_name": "Read Only", "is_active": False},
        )
        assert updated.status_code == 200
        assert updated.json()["role"] == "viewer"
        assert updated.json()["display_name"] == "Read Only"
        assert updated.json()["is_active"] is False


def test_user_management_rejects_non_admin_and_self_lockout(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.main import app

    with TestClient(app) as client:
        admin_token = _login(client, "admin", "admin")
        client.post(
            "/api/v2/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"username": "viewer-user", "password": "viewer-pass", "role": "viewer"},
        )
        viewer_token = _login(client, "viewer-user", "viewer-pass")

        forbidden = client.get(
            "/api/v2/auth/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert forbidden.status_code == 403

        promoted = client.patch(
            "/api/v2/auth/users/viewer-user",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "admin"},
        )
        assert promoted.status_code == 200
        assert promoted.json()["role"] == "admin"

        role_refreshed = client.get(
            "/api/v2/auth/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert role_refreshed.status_code == 200

        disabled = client.patch(
            "/api/v2/auth/users/viewer-user",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )
        assert disabled.status_code == 200

        inactive = client.get(
            "/api/v2/auth/me",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert inactive.status_code == 403
        assert inactive.json()["detail"] == "账号已禁用"

        self_demote = client.patch(
            "/api/v2/auth/users/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "viewer"},
        )
        assert self_demote.status_code == 400
        assert self_demote.json()["detail"] == "不能修改自己的管理员角色"

        self_disable = client.patch(
            "/api/v2/auth/users/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False},
        )
        assert self_disable.status_code == 400
        assert self_disable.json()["detail"] == "不能停用当前登录账号"


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v2/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
