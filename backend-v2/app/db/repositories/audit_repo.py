"""审计日志 Repository"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.db.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log(
        self,
        actor: str,
        action: str,
        resource: str = "",
        resource_id: Optional[str] = None,
        result: str = "success",
        ip: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor=actor, action=action, resource=resource,
            resource_id=resource_id, result=result, ip=ip, details=details,
        )
        return await self.create(entry)

    async def query(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if actor:
            stmt = stmt.where(AuditLog.actor == actor)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        result = await self.get_many(stmt, limit, offset)
        return list(result)
