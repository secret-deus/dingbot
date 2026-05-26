from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.repositories.audit_repo import AuditRepository


@pytest.mark.asyncio
async def test_audit_repository_filters_by_resource_result_and_resource_id(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repo = AuditRepository(session)
        await repo.log(
            actor="admin",
            action="tool.execute",
            resource="/api/v2/chat/sessions/abc/stream",
            resource_id="pod-nginx",
            result="failure",
            details={"reason": "confirmation_required"},
        )
        await repo.log(
            actor="admin",
            action="api.get",
            resource="/api/v2/config/dashboard",
            resource_id="dashboard",
            result="success",
        )
        await session.commit()

        rows = await repo.query(
            action="tool",
            resource="/chat",
            resource_id="nginx",
            result="failure",
        )

    assert len(rows) == 1
    assert rows[0].resource_id == "pod-nginx"
    assert rows[0].details == {"reason": "confirmation_required"}

    await engine.dispose()


def test_audit_endpoint_requires_admin_and_returns_filter_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.main import app

    with TestClient(app) as client:
        admin_login = client.post(
            "/api/v2/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]

        register_viewer = client.post(
            "/api/v2/auth/register",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"username": "audit-viewer", "password": "viewer-pass", "role": "viewer"},
        )
        assert register_viewer.status_code == 201
        viewer_login = client.post(
            "/api/v2/auth/login",
            json={"username": "audit-viewer", "password": "viewer-pass"},
        )
        assert viewer_login.status_code == 200
        viewer_token = viewer_login.json()["access_token"]

        forbidden = client.get(
            "/api/v2/config/audit",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert forbidden.status_code == 403

        asyncio.run(_seed_audit_row())

        response = client.get(
            "/api/v2/config/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "actor": "ops",
                "action": "tool",
                "resource": "aliyun",
                "resource_id": "swas",
                "result": "success",
            },
        )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["resource_id"] == "swas-list"
    assert rows[0]["details"] == {"region_id": "cn-beijing", "result_count": 1}


async def _seed_audit_row() -> None:
    from app.db.session import get_session_factory

    async with get_session_factory()() as session:
        repo = AuditRepository(session)
        await repo.log(
            actor="ops-user",
            action="tool.execute",
            resource="aliyun-swas-list-instances",
            resource_id="swas-list",
            result="success",
            details={"region_id": "cn-beijing", "result_count": 1},
        )
        await repo.log(
            actor="ops-user",
            action="tool.execute",
            resource="aliyun-ecs-list-instances",
            resource_id="ecs-list",
            result="failure",
        )
        await session.commit()
