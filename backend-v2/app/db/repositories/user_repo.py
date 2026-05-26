"""用户 Repository"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Role
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True)).order_by(User.created_at.desc())
        result = await self.get_many(stmt, limit, offset)
        return list(result)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.get_many(stmt, limit, offset)
        return list(result)

    async def create_user(self, username: str, hashed_password: str, role: Role = Role.VIEWER) -> User:
        user = User(username=username, hashed_password=hashed_password, role=role)
        return await self.create(user)
