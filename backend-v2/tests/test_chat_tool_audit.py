from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import AuditLog, Base
from app.mcp.policy import ToolCatalogPolicy
from app.services.chat_service import ChatOrchestrator


@pytest.mark.asyncio
async def test_chat_tool_denial_is_audited(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=None,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "alice", "role": "viewer"},
        )

        result = await orchestrator._execute_tool(
            {
                "function": {
                    "name": "k8s-get-deployment-history",
                    "arguments": json.dumps({"deployment_name": "nginx"}),
                }
            }
        )

        assert result["error"] == "tool_execution_denied"
        assert result["reason"] == "catalog_only_tool_cannot_execute"

        rows = (await session.execute(select(AuditLog))).scalars().all()
        assert len(rows) == 1
        assert rows[0].actor == "alice"
        assert rows[0].action == "tool.execute"
        assert rows[0].resource == "k8s-get-deployment-history"
        assert rows[0].result == "denied"
        assert rows[0].details["executionPolicy"] == "catalog_only"
        assert rows[0].details["argumentPreview"] == {"deployment_name": "nginx"}

    await engine.dispose()


class _FakeMCP:
    def __init__(self, policy: ToolCatalogPolicy):
        self.policy = policy

    def authorize_tool_call(self, name, user, arguments=None):
        return self.policy.authorize(name, user, arguments)

    async def call_tool(self, name, arguments, user=None):
        return {"result": f"called {name}"}


def _catalog(tmp_path):
    path = tmp_path / "tool_catalog.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "tools": [
                    {
                        "name": "k8s-get-deployment-history",
                        "title": "获取 Deployment 版本历史",
                        "category": "kubernetes",
                        "description": "获取 Kubernetes Deployment 的版本历史",
                        "tags": ["k8s", "deployment"],
                        "dangerLevel": "read",
                        "server": "catalog",
                        "executionPolicy": "catalog_only",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
