"""Operation audit log endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ....security.auth import CurrentUser, require_permission
from ....security.audit import get_audit_logger
from ..standard import success_envelope

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", summary="操作日志")
async def list_audit_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    actor: str | None = Query(None),
    action: str | None = Query(None),
    result: str | None = Query(None),
    _: CurrentUser = Depends(require_permission("audit:read")),
):
    items = get_audit_logger().list(
        limit=limit,
        actor=actor or None,
        action=action or None,
        result=result or None,
    )
    return success_envelope(
        request,
        {
            "items": items,
            "total": len(items),
        },
    )
