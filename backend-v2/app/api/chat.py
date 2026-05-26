"""聊天 API - 流式/非流式对话、会话管理"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.deps import get_current_user
from app.db.models import MessageRole
from app.db.repositories.session_repo import SessionRepository, MessageRepository
from app.db.session import get_db
from app.services.chat_service import ChatOrchestrator

router = APIRouter(prefix="/chat", tags=["聊天"])


class CreateSessionRequest(BaseModel):
    title: str = "新对话"
    skill_id: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str
    skill_id: Optional[str] = None
    tool_context_enabled: bool = True
    llm_provider_id: Optional[str] = None


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    repo = SessionRepository(db)
    sessions = await repo.list_sessions(limit, offset)
    await db.commit()
    return [
        {"id": s.id, "title": s.title, "skill_id": s.skill_id,
         "created_at": str(s.created_at), "updated_at": str(s.updated_at)}
        for s in sessions
    ]


@router.post("/sessions", status_code=201)
async def create_session(
    req: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    repo = SessionRepository(db)
    s = await repo.create_session(req.title, req.skill_id)
    await db.commit()
    return {"id": s.id, "title": s.title}


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    msg_repo = MessageRepository(db)
    msgs = await msg_repo.list_by_session(session_id)
    await db.commit()
    return [
        {"id": m.id, "role": m.role.value, "content": m.content,
         "tool_calls": m.tool_calls, "tool_results": m.tool_results,
         "created_at": str(m.created_at)}
        for m in msgs
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    repo = SessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s:
        raise HTTPException(404, "会话不存在")
    await repo.delete(s)
    await db.commit()


@router.post("/sessions/{session_id}/stream")
async def stream_chat(
    session_id: str,
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    from app.core.deps import _get_app_state

    state = _get_app_state()
    orchestrator = ChatOrchestrator(
        db=db,
        chat_service=state.get("chat_service"),
        mcp_manager=state.get("mcp_manager"),
        current_user=user,
    )

    async def _generate():
        async for event in orchestrator.handle_message(
            session_id,
            req.content,
            req.skill_id,
            tool_context_enabled=req.tool_context_enabled,
            llm_provider_id=req.llm_provider_id,
        ):
            import json
            yield {"event": event.get("type", "message"), "data": json.dumps(event, ensure_ascii=False)}

    return EventSourceResponse(_generate())


@router.post("/messages/{message_id}/tool-calls/{tool_call_id}/confirm")
async def confirm_tool_call(
    message_id: str,
    tool_call_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    from app.core.deps import _get_app_state

    state = _get_app_state()
    orchestrator = ChatOrchestrator(
        db=db,
        chat_service=state.get("chat_service"),
        mcp_manager=state.get("mcp_manager"),
        current_user=user,
    )
    result = await orchestrator.confirm_tool_call(message_id, tool_call_id)
    if result.get("error") in {"message_not_found", "tool_call_not_found", "confirmation_not_found"}:
        raise HTTPException(404, result.get("message") or result["error"])
    if result.get("error") in {"invalid_tool_arguments", "mcp_unavailable"}:
        raise HTTPException(400, result.get("message") or result["error"])
    if result.get("error") == "tool_execution_denied":
        raise HTTPException(403, result)
    return {"result": result}
