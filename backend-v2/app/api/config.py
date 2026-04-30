"""系统配置 & MCP 工具状态 API"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, require_admin
from app.db.repositories.audit_repo import AuditRepository
from app.db.session import get_db

router = APIRouter(prefix="/config", tags=["配置"])


@router.get("/status")
async def get_status():
    return {"status": "ok", "version": "3.0.0"}


@router.get("/health")
async def health_check():
    from app.core.deps import _get_app_state
    state = _get_app_state()
    mcp_manager = state.get("mcp_manager")
    mcp_health = await mcp_manager.health_check() if mcp_manager else {}
    return {
        "status": "healthy",
        "llm_enabled": state.get("chat_service") is not None,
        "mcp_servers": mcp_health,
    }


@router.get("/tools")
async def list_tools(_user: dict = Depends(get_current_user)):
    from app.core.deps import _get_app_state
    state = _get_app_state()
    mcp_manager = state.get("mcp_manager")
    if not mcp_manager:
        return {"tools": []}
    tools = await mcp_manager.list_tools()
    return {"tools": tools}


@router.get("/llm")
async def get_llm_config(_user: dict = Depends(get_current_user)):
    settings = get_settings()
    return {
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "masking_enabled": settings.masking_enabled,
    }


class UpdateLLMConfigRequest(BaseModel):
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@router.patch("/llm")
async def update_llm_config(
    req: UpdateLLMConfigRequest,
    _user: dict = Depends(require_admin),
):
    settings = get_settings()
    updates = req.model_dump(exclude_none=True)
    for k, v in updates.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    return {"updated": list(updates.keys())}


@router.get("/audit")
async def get_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    repo = AuditRepository(db)
    logs = await repo.query(actor=actor, action=action, limit=limit, offset=offset)
    await db.commit()
    return [
        {"id": l.id, "actor": l.actor, "action": l.action, "resource": l.resource,
         "result": l.result, "ip": l.ip, "created_at": str(l.created_at)}
        for l in logs
    ]
