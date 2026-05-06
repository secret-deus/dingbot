"""Scheduler runner for persisted scheduled tasks."""

from __future__ import annotations

from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import ScheduledTask, TaskExecution, TaskStatus, _now
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.task_repo import ExecutionRepository, TaskRepository
from app.db.session import get_session_factory
from app.services.chat_service import ChatOrchestrator
from app.services.dingtalk_service import DingTalkNotifier


class SchedulerRunner:
    def __init__(
        self,
        chat_service: Any = None,
        mcp_manager: Any = None,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
        notifier: Optional[Any] = None,
        enabled: bool = True,
    ) -> None:
        self.chat_service = chat_service
        self.mcp_manager = mcp_manager
        self.session_factory = session_factory or get_session_factory()
        self.notifier = notifier or DingTalkNotifier()
        self.enabled = enabled
        self.scheduler = AsyncIOScheduler()

    @property
    def running(self) -> bool:
        return bool(self.scheduler.running)

    async def start(self) -> None:
        if not self.enabled or self.running:
            return
        self.scheduler.start()
        await self.sync_jobs()
        logger.info("定时任务调度器已启动")

    async def stop(self) -> None:
        if self.running:
            self.scheduler.shutdown(wait=False)
            logger.info("定时任务调度器已停止")

    async def sync_jobs(self) -> None:
        if not self.enabled or not self.running:
            return

        async with self.session_factory() as db:
            tasks = await TaskRepository(db).list_active()

        active_job_ids = set()
        for task in tasks:
            job_id = self._job_id(task.id)
            active_job_ids.add(job_id)
            try:
                trigger = self._build_trigger(task.cron_expr)
            except ValueError as exc:
                logger.warning("跳过无效定时任务 {}: {}", task.id, exc)
                continue
            self.scheduler.add_job(
                self.run_task_once,
                trigger=trigger,
                id=job_id,
                args=[task.id],
                kwargs={"manual": False},
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

        for job in self.scheduler.get_jobs():
            if job.id.startswith("task-") and job.id not in active_job_ids:
                self.scheduler.remove_job(job.id)

    async def run_task_once(self, task_id: str, manual: bool = True) -> dict[str, Any]:
        async with self.session_factory() as db:
            task = await TaskRepository(db).get_by_id(task_id)
            if task is None:
                raise KeyError(task_id)
            if not manual and task.status != TaskStatus.ACTIVE:
                return {"skipped": True, "reason": "task is not active", "task_id": task_id}

            execution = await ExecutionRepository(db).create_execution(task.id)
            await db.commit()

            result_text = ""
            try:
                result_text = await self._execute_prompt(db, task)
                notification = await self._notify_if_needed(task, "success", result_text)
                self._mark_success(task, execution, result_text, notification)
                await db.commit()
                return {
                    "task_id": task.id,
                    "execution_id": execution.id,
                    "status": execution.status,
                    "result": result_text,
                    "notification": notification,
                }
            except Exception as exc:
                error = str(exc)
                self._mark_failed(task, execution, result_text, error)
                await db.commit()
                logger.error("定时任务执行失败 {}: {}", task.id, error)
                return {
                    "task_id": task.id,
                    "execution_id": execution.id,
                    "status": execution.status,
                    "result": result_text,
                    "error": error,
                }

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "running": self.running,
            "jobs": len(self.scheduler.get_jobs()) if self.running else 0,
            "dingtalk_enabled": bool(getattr(self.notifier, "enabled", False)),
        }

    async def _execute_prompt(self, db: AsyncSession, task: ScheduledTask) -> str:
        session = await SessionRepository(db).create_session(
            title=f"定时任务: {task.name[:80]}",
            skill_id=task.skill_id,
        )
        await db.flush()

        orchestrator = ChatOrchestrator(
            db=db,
            chat_service=self.chat_service,
            mcp_manager=self.mcp_manager,
            current_user={"username": "scheduler", "role": "admin"},
        )

        tokens: list[str] = []
        errors: list[str] = []
        async for event in orchestrator.handle_message(session.id, task.prompt, task.skill_id):
            if event["type"] == "token":
                tokens.append(event["content"])
            elif event["type"] == "error":
                errors.append(event.get("message", "unknown error"))

        if errors:
            raise RuntimeError("; ".join(errors))
        return "".join(tokens).strip() or "任务执行完成，无模型输出"

    async def _notify_if_needed(
        self,
        task: ScheduledTask,
        status: str,
        result: str,
        error: Optional[str] = None,
    ) -> dict[str, Any]:
        if not task.notify_dingtalk:
            return {"skipped": True, "reason": "task notification disabled"}
        return await self.notifier.send_task_result(
            task_name=task.name,
            status=status,
            result=result,
            error=error,
        )

    @staticmethod
    def _mark_success(
        task: ScheduledTask,
        execution: TaskExecution,
        result_text: str,
        notification: dict[str, Any],
    ) -> None:
        now = _now()
        execution.status = "success"
        execution.result = result_text
        execution.error = None
        execution.finished_at = now
        task.last_run_at = now
        task.last_result = SchedulerRunner._with_notification_summary(result_text, notification)

    @staticmethod
    def _mark_failed(
        task: ScheduledTask,
        execution: TaskExecution,
        result_text: str,
        error: str,
    ) -> None:
        now = _now()
        execution.status = "failed"
        execution.result = result_text or None
        execution.error = error
        execution.finished_at = now
        task.last_run_at = now
        task.last_result = result_text or None

    @staticmethod
    def _with_notification_summary(result_text: str, notification: dict[str, Any]) -> str:
        if not notification.get("skipped"):
            return result_text
        reason = notification.get("reason")
        if reason:
            return f"{result_text}\n\n通知: {reason}"
        return result_text

    @staticmethod
    def _build_trigger(cron_expr: str) -> CronTrigger:
        parts = cron_expr.split()
        if len(parts) == 5:
            return CronTrigger.from_crontab(cron_expr)
        if len(parts) == 6:
            second, minute, hour, day, month, day_of_week = parts
            return CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            )
        raise ValueError("cron expression must have 5 or 6 fields")

    @staticmethod
    def _job_id(task_id: str) -> str:
        return f"task-{task_id}"
