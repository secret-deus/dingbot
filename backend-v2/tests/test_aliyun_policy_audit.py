from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import AuditLog, Base
from app.mcp.policy import ToolCatalogPolicy
from app.services.chat_service import ChatOrchestrator


def test_aliyun_read_tool_requires_operator_or_admin(tmp_path):
    policy = ToolCatalogPolicy(str(_catalog(tmp_path)))

    viewer = policy.authorize(
        "aliyun-ecs-list-instances",
        {"username": "viewer", "role": "viewer"},
        {"region_id": "cn-hangzhou"},
    )
    operator = policy.authorize(
        "aliyun-ecs-list-instances",
        {"username": "operator", "role": "operator"},
        {"region_id": "cn-hangzhou"},
    )

    assert viewer.allowed is False
    assert viewer.reason == "operator_role_required"
    assert operator.allowed is True
    assert operator.reason == "read_allowed"


@pytest.mark.asyncio
async def test_aliyun_tool_denial_audit_includes_region_and_resource_context(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'audit.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        orchestrator = ChatOrchestrator(
            db=session,
            chat_service=None,
            mcp_manager=_FakeMCP(ToolCatalogPolicy(str(_catalog(tmp_path)))),
            current_user={"username": "eve", "role": "viewer"},
        )

        result = await orchestrator._execute_tool(
            {
                "function": {
                    "name": "aliyun-cms-get-ecs-metrics",
                    "arguments": json.dumps(
                        {
                            "region_id": "cn-hangzhou",
                            "instance_id": "i-prod",
                            "relative_range": "1h",
                        }
                    ),
                }
            }
        )

        assert result["error"] == "tool_execution_denied"
        assert result["reason"] == "operator_role_required"

        rows = (await session.execute(select(AuditLog))).scalars().all()
        assert len(rows) == 1
        assert rows[0].actor == "eve"
        assert rows[0].resource == "aliyun-cms-get-ecs-metrics"
        assert rows[0].result == "denied"
        assert rows[0].details["region_id"] == "cn-hangzhou"
        assert rows[0].details["resource_ids"] == ["i-prod"]
        assert rows[0].details["time_range"] == "1h"

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
                        "name": "aliyun-ecs-list-instances",
                        "title": "查询 ECS 实例",
                        "category": "aliyun",
                        "description": "查询 ECS 实例列表",
                        "tags": ["aliyun", "ecs"],
                        "dangerLevel": "read",
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    },
                    {
                        "name": "aliyun-cms-get-ecs-metrics",
                        "title": "查询 ECS 监控指标",
                        "category": "aliyun",
                        "description": "查询 ECS CPU/内存指标",
                        "tags": ["aliyun", "cms", "metrics"],
                        "dangerLevel": "read",
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                        "examples": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
