"""FastAPI 主入口 - 应用生命周期、路由注册、中间件"""

from __future__ import annotations

import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import get_settings
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
    logger.add(str(log_dir / "app.log"), level=level, rotation="1 week", retention="4 weeks",
               encoding="utf-8", enqueue=True, format=fmt)


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
    await init_db()
    logger.info("数据库初始化完成")

    chat_service = None
    mcp_manager = None

    llm_runtime = load_llm_runtime()
    if llm_runtime.active and llm_runtime.provider:
        logger.info("LLM 运行时配置就绪: {} / {}", llm_runtime.provider.name, llm_runtime.provider.model)
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

    await _ensure_admin_user()

    logger.info("服务启动完成")
    yield

    if scheduler_runner:
        await scheduler_runner.stop()
    if mcp_manager:
        await mcp_manager.disconnect_all()
    await close_db()
    logger.info("服务关闭完成")


async def _ensure_admin_user() -> None:
    from app.db.session import get_db
    from app.db.repositories.user_repo import UserRepository
    from app.core.security import hash_password

    async for db in get_db():
        repo = UserRepository(db)
        admin = await repo.get_by_username("admin")
        if not admin:
            from app.db.models import Role
            hashed = hash_password("admin")
            await repo.create_user("admin", hashed, Role.ADMIN)
            logger.info("已创建默认管理员账号 admin/admin")
        await db.commit()


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------

app = FastAPI(
    title="钉钉K8s运维机器人",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    started = time.time()
    response = await call_next(request)
    if request.url.path.startswith("/api") and request.method != "OPTIONS":
        from app.core.security import decode_access_token
        actor = "anonymous"
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            payload = decode_access_token(auth.split(" ", 1)[1].strip())
            if payload:
                actor = payload.get("sub", "unknown")
        try:
            from app.db.session import get_db
            from app.db.repositories.audit_repo import AuditRepository
            async for db in get_db():
                repo = AuditRepository(db)
                await repo.log(
                    actor=actor,
                    action=f"api.{request.method.lower()}",
                    resource=request.url.path,
                    result="success" if response.status_code < 400 else "failure",
                    ip=request.client.host if request.client else None,
                    details={"status_code": response.status_code, "duration_ms": round((time.time() - started) * 1000, 2)},
                )
                await db.commit()
        except Exception as e:
            logger.debug("审计记录失败: {}", e)
    return response


# ---------------------------------------------------------------------------
# 路由注册
# ---------------------------------------------------------------------------

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.scheduler import router as scheduler_router
from app.api.config import router as config_router

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
