"""FastAPI 主入口 - 应用生命周期、路由注册、中间件"""

from __future__ import annotations

import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.responses import Response

from app.core.config import (
    AppSettings,
    get_settings,
    is_placeholder_secret,
    is_unsafe_bootstrap_admin_password,
    validate_startup_security,
)
from app.db.session import close_db, init_db
from app.llm.config_store import load_llm_runtime
from app.mcp.manager import MCPManager

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------


def _setup_logging() -> None:
    settings = get_settings()
    level = settings.log_level.upper()
    fmt = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<7}</level> | {message}"
    try:
        logger.remove()
    except Exception:
        pass
    logger.add(sys.stdout, level=level, format=fmt, colorize=True, enqueue=True)
    from pathlib import Path

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_dir / "app.log"),
        level=level,
        rotation="1 week",
        retention="4 weeks",
        encoding="utf-8",
        enqueue=True,
        format=fmt,
    )


_setup_logging()

# ---------------------------------------------------------------------------
# 全局应用状态
# ---------------------------------------------------------------------------

_app_state: dict = {}


def get_app_state() -> dict:
    return _app_state


# ---------------------------------------------------------------------------
# 生命周期
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_startup_security(settings)
    if not settings.is_production and is_placeholder_secret(settings.secret_key):
        logger.warning("当前 SECRET_KEY 仍是占位值，仅适合本地开发环境")
    await init_db()
    logger.info("数据库初始化完成")

    chat_service = None
    mcp_manager = None

    llm_runtime = load_llm_runtime()
    if llm_runtime.active and llm_runtime.provider:
        logger.info(
            "LLM 运行时配置就绪: {} / {}", llm_runtime.provider.name, llm_runtime.provider.model
        )
    else:
        logger.warning("LLM 运行时配置未启用或未配置 API Key，可在 LLM 配置页保存后立即用于新消息")

    if settings.mcp_config_path:
        mcp_manager = MCPManager()
        try:
            await mcp_manager.connect_all()
        except Exception as e:
            logger.error("MCP 连接失败: {}", e)
            mcp_manager = None

    scheduler_runner = None
    if settings.scheduler_enabled:
        from app.services.scheduler_service import SchedulerRunner

        scheduler_runner = SchedulerRunner(
            chat_service=chat_service,
            mcp_manager=mcp_manager,
            enabled=settings.scheduler_enabled,
        )
        await scheduler_runner.start()

    _app_state["chat_service"] = chat_service
    _app_state["mcp_manager"] = mcp_manager
    _app_state["scheduler_runner"] = scheduler_runner

    # 注入到 deps 模块
    import app.core.deps as deps

    deps._app_state = _app_state

    await _ensure_admin_user(settings)

    logger.info("服务启动完成")
    yield

    if scheduler_runner:
        await scheduler_runner.stop()
    if mcp_manager:
        await mcp_manager.disconnect_all()
    await close_db()
    logger.info("服务关闭完成")


async def _ensure_admin_user(settings: AppSettings | None = None) -> None:
    settings = settings or get_settings()
    from app.core.security import hash_password
    from app.db.repositories.user_repo import UserRepository
    from app.db.session import get_db

    async for db in get_db():
        repo = UserRepository(db)
        admin = await repo.get_first_admin()
        if not admin:
            if not settings.bootstrap_admin_enabled:
                logger.warning("当前数据库没有管理员账号，且 BOOTSTRAP_ADMIN_ENABLED=false")
                await db.commit()
                return
            username = settings.bootstrap_admin_username.strip()
            if not username:
                raise RuntimeError("BOOTSTRAP_ADMIN_USERNAME 不能为空")
            if settings.is_production and is_unsafe_bootstrap_admin_password(
                settings.bootstrap_admin_password
            ):
                raise RuntimeError("生产环境初始化管理员密码不安全")
            from app.db.models import Role

            hashed = hash_password(settings.bootstrap_admin_password)
            await repo.create_user(username, hashed, Role.ADMIN)
            if settings.bootstrap_admin_password == "admin":
                logger.info("已创建默认管理员账号 {}/admin", username)
            else:
                logger.info("已创建初始化管理员账号 {}", username)
        await db.commit()


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ops Workbench（智能运维工作台）",
    description="面向 Kubernetes、ECS 与阿里云场景的智能运维工作台。",
    version="3.0.0",
    lifespan=lifespan,
)

_settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=_settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    started = time.time()
    request_id = _request_id(request)
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    if request.url.path.startswith("/api") and request.method != "OPTIONS":
        from app.core.security import decode_access_token

        actor = "anonymous"
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            payload = decode_access_token(auth.split(" ", 1)[1].strip())
            if payload:
                actor = payload.get("sub", "unknown")
        _add_background_task(
            response,
            _write_api_audit_log,
            actor=actor,
            action=f"api.{request.method.lower()}",
            resource=request.url.path,
            result="success" if response.status_code < 400 else "failure",
            ip=request.client.host if request.client else None,
            details={
                "request_id": request_id,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round((time.time() - started) * 1000, 2),
                "user_agent": request.headers.get("user-agent", ""),
            },
        )
    return response


def _request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "").strip()
    if incoming and len(incoming) <= 128:
        return incoming
    return uuid.uuid4().hex


def _add_background_task(response: Response, func, **kwargs) -> None:
    task = BackgroundTask(func, **kwargs)
    if response.background is None:
        response.background = task
        return
    tasks = BackgroundTasks()
    tasks.add_task(response.background)
    tasks.add_task(func, **kwargs)
    response.background = tasks


async def _write_api_audit_log(
    *,
    actor: str,
    action: str,
    resource: str,
    result: str,
    ip: str | None,
    details: dict,
) -> None:
    try:
        from app.db.repositories.audit_repo import AuditRepository
        from app.db.session import get_db

        async for db in get_db():
            repo = AuditRepository(db)
            await repo.log(
                actor=actor,
                action=action,
                resource=resource,
                result=result,
                ip=ip,
                details=details,
            )
            await db.commit()
    except Exception as e:
        logger.debug("审计记录失败: {}", e)


# ---------------------------------------------------------------------------
# 路由注册
# ---------------------------------------------------------------------------

from app.api.auth import router as auth_router  # noqa: E402
from app.api.chat import router as chat_router  # noqa: E402
from app.api.config import router as config_router  # noqa: E402
from app.api.scheduler import router as scheduler_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v2")
app.include_router(chat_router, prefix="/api/v2")
app.include_router(scheduler_router, prefix="/api/v2")
app.include_router(config_router, prefix="/api/v2")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
