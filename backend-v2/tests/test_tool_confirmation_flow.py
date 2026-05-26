from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import AuditLog, Base, MessageRole
from app.db.repositories.session_repo import MessageRepository, SessionRepository
from app.mcp.policy import ToolCatalogPolicy
from app.services.chat_service import ChatOrchestrator


@pytest.mark.asyncio
async def test_chat_confirmation_executes_pending_write_tool(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'confirm-flow.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db:
        chat_session = await SessionRepository(db).create_session("confirm flow")
        await db.commit()

        mcp = _ConfirmableToolMCP(tmp_path)
        orchestrator = ChatOrchestrator(
            db=db,
            mcp_manager=mcp,
            current_user={"username": "operator", "role": "operator"},
        )
        arguments = {"namespace": "default", "deployment_name": "web", "replicas": 2}
        tool_call = _scale_tool_call(arguments)

        pending = await orchestrator._execute_tool(tool_call)
        assert pending["error"] == "tool_execution_denied"
        assert pending["reason"] == "confirmation_required"
        assert pending["requires_confirmation"] is True
        assert pending["confirmation"]["token"]
        assert mcp.called_arguments == []

        message = await MessageRepository(db).add_message(
            chat_session.id,
            MessageRole.ASSISTANT,
            "",
            1,
            tool_calls=[tool_call],
            tool_results=[
                {
                    "tool_call_id": "call-scale",
                    "tool_name": "k8s-scale-deployment",
                    "result": pending,
                }
            ],
        )
        await db.commit()

        confirmed = await orchestrator.confirm_tool_call(message.id, "call-scale")

        assert confirmed["result"]["scaled"] is True
        assert mcp.called_arguments == [arguments]

        stored = await MessageRepository(db).get_by_id(message.id)
        assert stored is not None
        assert len(stored.tool_results) == 2
        assert stored.tool_results[-1]["tool_call_id"] == "call-scale"
        assert stored.tool_results[-1]["result"]["result"]["scaled"] is True

        audit_rows = list((await db.execute(select(AuditLog).order_by(AuditLog.id))).scalars())
        assert [(row.action, row.result) for row in audit_rows] == [
            ("tool.execute", "denied"),
            ("tool.confirm", "allowed"),
        ]

    await engine.dispose()


def test_chat_confirm_endpoint_executes_pending_tool(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.db'}")
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "missing-mcp.json"))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(tmp_path / "missing-llm.json"))
    monkeypatch.setenv("LLM_API_KEY", "")

    from app.core import deps
    from app.db.session import get_session_factory
    from app.main import app

    mcp = _ConfirmableToolMCP(tmp_path)
    with TestClient(app) as client:
        deps._app_state["mcp_manager"] = mcp
        login = client.post("/api/v2/auth/login", json={"username": "admin", "password": "admin"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        created = client.post(
            "/api/v2/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "confirm endpoint"},
        )
        assert created.status_code == 201
        session_id = created.json()["id"]

        async def _insert_pending_message():
            async with get_session_factory()() as db:
                orchestrator = ChatOrchestrator(
                    db=db,
                    mcp_manager=mcp,
                    current_user={"username": "admin", "role": "admin"},
                )
                arguments = {"namespace": "default", "deployment_name": "web", "replicas": 2}
                tool_call = _scale_tool_call(arguments)
                pending = await orchestrator._execute_tool(tool_call)
                message = await MessageRepository(db).add_message(
                    session_id,
                    MessageRole.ASSISTANT,
                    "",
                    2,
                    tool_calls=[tool_call],
                    tool_results=[
                        {
                            "tool_call_id": "call-scale",
                            "tool_name": "k8s-scale-deployment",
                            "result": pending,
                        }
                    ],
                )
                await db.commit()
                return message.id

        import anyio

        message_id = anyio.run(_insert_pending_message)
        response = client.post(
            f"/api/v2/chat/messages/{message_id}/tool-calls/call-scale/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["result"]["result"]["scaled"] is True
        assert mcp.called_arguments == [
            {"namespace": "default", "deployment_name": "web", "replicas": 2}
        ]


class _ConfirmableToolMCP:
    def __init__(self, tmp_path):
        self.policy = ToolCatalogPolicy(str(_catalog(tmp_path)))
        self.called_arguments: list[dict] = []

    def authorize_tool_call(self, name, user, arguments=None):
        return self.policy.authorize(name, user, arguments)

    async def call_tool(self, name, arguments, user=None):
        decision = self.policy.authorize(name, user, arguments)
        if not decision.allowed:
            return {
                "error": "tool_execution_denied",
                "reason": decision.reason,
                "requires_confirmation": decision.requires_confirmation,
                "tool": name,
            }
        public_arguments = {
            key: value
            for key, value in arguments.items()
            if not key.startswith("__confirmation")
        }
        self.called_arguments.append(public_arguments)
        return {"result": {"scaled": True, "arguments": public_arguments}}


def _catalog(tmp_path):
    path = tmp_path / "tool_catalog.json"
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "tools": [
                    {
                        "name": "k8s-scale-deployment",
                        "title": "调整 Deployment 副本数",
                        "category": "kubernetes",
                        "description": "调整 Kubernetes Deployment 副本数",
                        "tags": ["k8s", "deployment"],
                        "dangerLevel": "write",
                        "server": "builtin",
                        "executionPolicy": "executable",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "namespace": {"type": "string"},
                                "deployment_name": {"type": "string"},
                                "replicas": {"type": "integer"},
                            },
                            "required": ["namespace", "deployment_name", "replicas"],
                        },
                        "examples": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _scale_tool_call(arguments: dict) -> dict:
    return {
        "id": "call-scale",
        "type": "function",
        "function": {
            "name": "k8s-scale-deployment",
            "arguments": json.dumps(arguments),
        },
    }
