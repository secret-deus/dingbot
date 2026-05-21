from __future__ import annotations

from fastapi.testclient import TestClient


def test_dashboard_summary_returns_chatops_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.main import app

    with TestClient(app) as client:
        login = client.post(
            "/api/v2/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.get(
            "/api/v2/config/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["cluster"]["namespace"]
    assert body["tools"]["total"] >= 9
    assert body["tools"]["available"] <= body["tools"]["total"]
    assert body["theme"]["surface"] == "#111827"
    assert body["theme"]["primary"] == "#22c55e"
    assert body["icon_pack"]["kubernetes"] == "kubernetes-cluster"
    assert body["icon_pack"]["bot"] == "bot-core"
    assert [item["id"] for item in body["insights"]] == [
        "kubernetes",
        "mcp-tools",
        "knowledge-graph",
        "scheduler",
    ]
    assert [node["kind"] for node in body["resource_map"]] == [
        "Deployment",
        "ReplicaSet",
        "Pod",
        "Event",
    ]
    assert body["execution_timeline"][-1]["id"] == "answer"
    assert body["next_actions"][0]["route"] == "Chat"
