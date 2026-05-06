from __future__ import annotations

from fastapi.testclient import TestClient


def test_public_health_endpoints(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.main import app

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        status = client.get("/api/v2/config/status")
        assert status.status_code == 200
        assert status.json()["status"] == "ok"

        config_health = client.get("/api/v2/config/health")
        assert config_health.status_code == 200
        body = config_health.json()
        assert body["status"] == "healthy"
        assert body["llm_enabled"] is False
        assert body["mcp_servers"]["builtin"]["tools"] >= 9
