from __future__ import annotations

import json

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, ScheduledTask, TaskExecution
from app.db.repositories.task_repo import TaskRepository
from app.services.dingtalk_service import DingTalkNotifier
from app.services.scheduler_service import SchedulerRunner


@pytest.mark.asyncio
async def test_scheduler_runner_records_success_and_sends_notification(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'scheduler-success.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        task = await TaskRepository(session).create_task(
            name="cluster report",
            cron_expr="*/5 * * * *",
            prompt="生成集群报告",
            notify_dingtalk=True,
        )
        await session.commit()
        task_id = task.id

    notifier = _FakeNotifier()
    runner = SchedulerRunner(
        chat_service=_FakeChat("集群状态正常"),
        session_factory=session_factory,
        notifier=notifier,
    )

    result = await runner.run_task_once(task_id)

    assert result["status"] == "success"
    assert result["result"] == "集群状态正常"
    assert notifier.calls == [("cluster report", "success", "集群状态正常", None)]

    async with session_factory() as session:
        task = await session.get(ScheduledTask, task_id)
        executions = (await session.execute(select(TaskExecution))).scalars().all()
        assert task is not None
        assert task.last_run_at is not None
        assert task.last_result == "集群状态正常"
        assert len(executions) == 1
        assert executions[0].status == "success"
        assert executions[0].result == "集群状态正常"
        assert executions[0].finished_at is not None
        assert executions[0].error is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_scheduler_runner_records_failed_notification(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'scheduler-notify-fail.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        task = await TaskRepository(session).create_task(
            name="notify fail",
            cron_expr="*/5 * * * *",
            prompt="执行巡检",
            notify_dingtalk=True,
        )
        await session.commit()
        task_id = task.id

    runner = SchedulerRunner(
        chat_service=_FakeChat("巡检完成"),
        session_factory=session_factory,
        notifier=_FailingNotifier(),
    )

    result = await runner.run_task_once(task_id)

    assert result["status"] == "failed"
    assert result["result"] == "巡检完成"
    assert "webhook down" in result["error"]

    async with session_factory() as session:
        execution = (await session.execute(select(TaskExecution))).scalar_one()
        assert execution.status == "failed"
        assert execution.result == "巡检完成"
        assert "webhook down" in execution.error
        assert execution.finished_at is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_dingtalk_notifier_success_with_mock_transport():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["msgtype"] == "markdown"
        assert payload["markdown"]["title"].startswith("定时任务成功")
        assert "timestamp=" in str(request.url)
        assert "sign=" in str(request.url)
        return httpx.Response(200, json={"errcode": 0, "errmsg": "ok"})

    notifier = DingTalkNotifier(
        webhook_url="https://example.test/robot/send?access_token=test",
        secret="secret",
        transport=httpx.MockTransport(handler),
    )

    result = await notifier.send_task_result("nightly", "success", "done")

    assert result["skipped"] is False
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_dingtalk_notifier_raises_on_api_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errcode": 310000, "errmsg": "invalid token"})

    notifier = DingTalkNotifier(
        webhook_url="https://example.test/robot/send",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeError, match="DingTalk webhook failed"):
        await notifier.send_task_result("nightly", "failed", "", "boom")


class _FakeChat:
    def __init__(self, content: str):
        self.content = content

    async def stream_chat(self, messages, tools=None):
        yield {"type": "token", "content": self.content}
        yield {"type": "done"}


class _FakeNotifier:
    enabled = True

    def __init__(self):
        self.calls = []

    async def send_task_result(self, task_name, status, result, error=None):
        self.calls.append((task_name, status, result, error))
        return {"skipped": False, "response": {"errcode": 0}}


class _FailingNotifier:
    enabled = True

    async def send_task_result(self, task_name, status, result, error=None):
        raise RuntimeError("webhook down")
