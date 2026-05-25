"""会话 & 消息 Repository"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Session, Message, MessageRole
from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> list[Session]:
        stmt = select(Session).order_by(Session.updated_at.desc())
        result = await self.get_many(stmt, limit, offset)
        return list(result)

    async def get_with_messages(self, session_id: str) -> Session | None:
        stmt = select(Session).where(Session.id == session_id).options(selectinload(Session.messages))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_session(self, title: str = "新对话", skill_id: Optional[str] = None) -> Session:
        s = Session(title=title, skill_id=skill_id)
        return await self.create(s)

    async def update_title(self, session_id: str, title: str) -> Session | None:
        s = await self.get_by_id(session_id)
        if s:
            s.title = title
            await self.session.flush()
        return s


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def list_by_session(self, session_id: str, limit: int = 200) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.seq.asc())
        )
        result = await self.session.execute(stmt.limit(limit))
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        seq: int,
        tool_calls: Optional[dict] = None,
        tool_results: Optional[dict] = None,
        tool_call_id: Optional[str] = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            seq=seq,
            tool_calls=tool_calls,
            tool_results=tool_results,
            tool_call_id=tool_call_id,
        )
        return await self.create(msg)

    async def next_seq(self, session_id: str) -> int:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.seq.desc()).limit(1)
        result = await self.session.execute(stmt)
        last = result.scalar_one_or_none()
        return (last.seq + 1) if last else 1
