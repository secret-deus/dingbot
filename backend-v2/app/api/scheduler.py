"""调度器 API - 定时任务 CRUD 与执行历史"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_operator
from app.db.models import TaskStatus
from app.db.repositories.task_repo import TaskRepository, ExecutionRepository
from app.db.session import get_db

router = APIRouter(prefix="/scheduler", tags=["调度器"])


class CreateTaskRequest(BaseModel):
    name: str
    cron_expr: str
    prompt: str
    skill_id: Optional[str] = None
    notify_dingtalk: bool = False

class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    prompt: Optional[str] = None
    status: Optional[str] = None


@router.get("/tasks")
async def list_tasks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    repo = TaskRepository(db)
    tasks = await repo.list_all(limit, offset)
    await db.commit()
    return [
        {"id": t.id, "name": t.name, "cron_expr": t.cron_expr, "prompt": t.prompt,
         "skill_id": t.skill_id, "notify_dingtalk": t.notify_dingtalk,
         "status": t.status.value, "last_run_at": str(t.last_run_at) if t.last_run_at else None,
         "created_at": str(t.created_at)}
        for t in tasks
    ]


@router.post("/tasks", status_code=201)
async def create_task(
    req: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_operator),
):
    repo = TaskRepository(db)
    task = await repo.create_task(req.name, req.cron_expr, req.prompt, req.skill_id, req.notify_dingtalk)
    await db.commit()
    return {"id": task.id, "name": task.name, "status": task.status.value}


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    req: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_operator),
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if req.name:
        task.name = req.name
    if req.cron_expr:
        task.cron_expr = req.cron_expr
    if req.prompt:
        task.prompt = req.prompt
    if req.status:
        try:
            task.status = TaskStatus(req.status)
        except ValueError:
            raise HTTPException(400, f"无效状态: {req.status}")
    await db.commit()
    return {"id": task.id, "status": task.status.value}


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_operator),
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    await repo.delete(task)
    await db.commit()


@router.get("/tasks/{task_id}/executions")
async def list_executions(
    task_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.db.models import TaskExecution
    stmt = select(TaskExecution).where(TaskExecution.task_id == task_id).order_by(TaskExecution.started_at.desc()).limit(limit)
    result = await db.execute(stmt)
    execs = result.scalars().all()
    await db.commit()
    return [
        {"id": e.id, "status": e.status, "started_at": str(e.started_at),
         "finished_at": str(e.finished_at) if e.finished_at else None,
         "error": e.error}
        for e in execs
    ]
