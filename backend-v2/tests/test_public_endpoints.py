from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.db.repositories.audit_repo import AuditRepository


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

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        assert openapi.json()["info"]["title"] == "Ops Workbench（智能运维工作台）"
        assert (
            openapi.json()["info"]["description"]
            == "面向 Kubernetes、ECS 与阿里云场景的智能运维工作台。"
        )

        status = client.get(
            "/api/v2/config/status",
            headers={"X-Request-ID": "public-status-smoke"},
        )
        assert status.status_code == 200
        assert status.headers["X-Request-ID"] == "public-status-smoke"
        assert status.json()["status"] == "ok"

        config_health = client.get("/api/v2/config/health")
        assert config_health.status_code == 200
        body = config_health.json()
        assert body["status"] == "healthy"
        assert body["llm_enabled"] is False
        assert body["mcp_servers"]["builtin"]["tools"] >= 9

        audit_rows = asyncio.run(_audit_rows_for("/api/v2/config/status"))
        assert any(
            row.details and row.details.get("request_id") == "public-status-smoke"
            for row in audit_rows
        )


async def _audit_rows_for(resource: str):
    from app.db.session import get_session_factory

    async with get_session_factory()() as session:
        repo = AuditRepository(session)
        return await repo.query(resource=resource, limit=20)
