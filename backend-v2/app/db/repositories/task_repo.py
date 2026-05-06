"""定时任务 Repository"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScheduledTask, TaskExecution, TaskStatus
from app.db.repositories.base import BaseRepository


class TaskRepository(BaseRepository[ScheduledTask]):
    def __init__(self, session: AsyncSession):
        super().__init__(ScheduledTask, session)

    async def list_active(self) -> list[ScheduledTask]:
        stmt = select(ScheduledTask).where(ScheduledTask.status == TaskStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[ScheduledTask]:
        stmt = select(ScheduledTask).order_by(ScheduledTask.created_at.desc())
        result = await self.get_many(stmt, limit, offset)
        return list(result)

    async def create_task(
        self,
        name: str,
        cron_expr: str,
        prompt: str,
        skill_id: Optional[str] = None,
        notify_dingtalk: bool = False,
    ) -> ScheduledTask:
        task = ScheduledTask(
            name=name, cron_expr=cron_expr, prompt=prompt,
            skill_id=skill_id, notify_dingtalk=notify_dingtalk,
        )
        return await self.create(task)

    async def update_status(self, task_id: str, status: TaskStatus) -> ScheduledTask | None:
        task = await self.get_by_id(task_id)
        if task:
            task.status = status
            await self.session.flush()
        return task


class ExecutionRepository(BaseRepository[TaskExecution]):
    def __init__(self, session: AsyncSession):
        super().__init__(TaskExecution, session)

    async def create_execution(self, task_id: str) -> TaskExecution:
        exe = TaskExecution(task_id=task_id)
        return await self.create(exe)

    async def finish_execution(self, exec_id: str, status: str, result: Optional[str] = None, error: Optional[str] = None) -> None:
        from app.db.models import _now
        exe = await self.get_by_id(exec_id)
        if exe:
            exe.status = status
            exe.result = result
            exe.error = error
            exe.finished_at = _now()
            await self.session.flush()
