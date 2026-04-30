"""通用 Repository 基类"""

from __future__ import annotations

from typing import AsyncGenerator, Generic, TypeVar, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: str) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def get_many(self, stmt: Select | None = None, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        query = stmt if stmt is not None else select(self.model)
        result = await self.session.execute(query.limit(limit).offset(offset))
        return result.scalars().all()

    async def count(self, stmt: Select | None = None) -> int:
        base = stmt if stmt is not None else select(self.model)
        count_stmt = select(func.count()).select_from(base.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()
