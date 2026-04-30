"""
钉钉机器人 + LLM + MCP 集成系统
FastAPI 主应用入口 - 集成前后端服务
"""

# 导入必要的模块
import asyncio
import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

# 环境变量加载
from dotenv import load_dotenv

# FastAPI相关
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 日志配置
from loguru import logger

# 本地模块
from src.api.v2.router import api_v2_router
from src.app.container import RuntimeContainer, set_runtime_container
from src.mcp.enhanced_client import EnhancedMCPClient
from src.config.manager import config_manager
from src.llm.processor import EnhancedLLMProcessor
from src.llm.config import resolve_llm_processor_config_dict
from src.dingtalk.bot import DingTalkBot

# 日志设置（在任何日志输出前执行）
def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    fmt_console = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | {message}"
    fmt_file = "{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}"
    try:
        logger.remove()
    except Exception:
        pass
    logger.add(sys.stdout, level=level, format=fmt_console, colorize=True, enqueue=True)
    # 文件日志
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(str(log_dir / "app.log"), level=level, rotation="1 week", retention="4 weeks", encoding="utf-8", enqueue=True, format=fmt_file)

setup_logging()

# 加载环境变量文件
config_file = "config.env"
if os.path.exists(config_file):
    load_dotenv(config_file, override=True)
    logger.info(f"📄 已加载 {config_file} 配置文件")
else:
    logger.warning(f"⚠️ 配置文件 {config_file} 不存在，使用系统环境变量")

def check_and_migrate_config():
    """检查并执行配置迁移"""
    try:
        logger.info("🔄 开始配置迁移检查...")

        # 检查LLM配置文件是否存在
        llm_config_file = Path("config/llm_config.json")

        if not llm_config_file.exists():
            logger.info("📦 检测到首次启动或配置缺失，开始自动迁移...")

            # 创建配置目录
            llm_config_file.parent.mkdir(parents=True, exist_ok=True)

            # 导入并初始化LLM配置管理器进行迁移
            try:
                from src.llm.config_manager import get_llm_config_manager
                llm_manager = get_llm_config_manager()

                # 尝试从环境变量迁移
                if llm_manager.migrate_from_env():
                    logger.info("✅ LLM配置迁移成功！已从环境变量创建配置文件")

                    # 记录迁移状态
                    migration_log = {
                        "migrated_at": str(Path.cwd()),  # 工作目录
                        "source": "environment_variables",
                        "target": str(llm_config_file),
                        "timestamp": str(logger._core.get_time()),
                        "status": "success"
                    }

                    # 保存迁移记录
                    migration_log_file = llm_config_file.parent / "migration.log"
                    with open(migration_log_file, "w", encoding="utf-8") as f:
                        import json
                        json.dump(migration_log, f, indent=2, ensure_ascii=False)

                    logger.info(f"📝 迁移记录已保存到: {migration_log_file}")
                else:
                    logger.warning("⚠️ 配置迁移失败，将继续使用环境变量配置")

            except ImportError as e:
                logger.warning(f"⚠️ 无法导入LLM配置管理器: {e}，将继续使用环境变量配置")
        else:
            logger.info("✅ LLM配置文件已存在，跳过迁移")

        # 验证配置文件完整性
        if llm_config_file.exists():
            try:
                with open(llm_config_file, "r", encoding="utf-8") as f:
                    import json
                    config_data = json.load(f)

                if "providers" in config_data and config_data["providers"]:
                    logger.info(f"✅ 配置文件验证通过，包含 {len(config_data['providers'])} 个提供商")
                else:
                    logger.warning("⚠️ 配置文件缺少提供商配置，可能需要手动配置")

            except Exception as e:
                logger.error(f"❌ 配置文件验证失败: {e}")

        logger.info("🎯 配置迁移检查完成")

    except Exception as e:
        logger.error(f"❌ 配置迁移检查失败: {e}")
        logger.info("📌 将继续使用环境变量配置启动")

# 全局变量存储服务实例（保留给非 API 旧代码兼容）
mcp_client = None
llm_processor = None
dingtalk_bot = None
runtime_container = RuntimeContainer()
set_runtime_container(runtime_container)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        await initialize_services()
        logger.info("🚀 服务启动完成")
        yield
    finally:
        await cleanup_services()
        logger.info("🛑 服务关闭完成")

async def initialize_services():
    """初始化所有服务"""
    global mcp_client, llm_processor, dingtalk_bot

    # 1. 初始化增强MCP客户端（允许禁用或失败时降级）
    try:
        logger.info("初始化增强MCP客户端...")
        from src.mcp.config import get_config_manager  # 修正import路径
        mcp_config_manager = get_config_manager()
        logger.info(f"🔍 配置管理器类型: {type(mcp_config_manager)}")
        logger.info(f"🔍 current_config: {mcp_config_manager.current_config}")

        enabled_servers = mcp_config_manager.get_enabled_servers()
        if mcp_config_manager.current_config:
            logger.info(f"🔍 current_config.servers: {len(mcp_config_manager.current_config.servers)} 个服务器")
            for s in mcp_config_manager.current_config.servers:
                logger.info(f"🔍   - {s.name}: enabled={s.enabled}, type={s.type}")
        logger.info(f"🔍 启用的服务器数量: {len(enabled_servers)}")

        from src.mcp.builtin_k8s_ecs import builtin_k8s_ecs_tools_enabled

        use_builtin_k8s_ecs = builtin_k8s_ecs_tools_enabled()
        if not enabled_servers and not use_builtin_k8s_ecs:
            logger.warning(
                "⚠️ 未启用任何远程 MCP 且已关闭进程内 K8s/ECS 工具，将以无工具模式启动（LLM 仍可用）"
            )
            mcp_client = None
            runtime_container.mcp_client = None
        else:
            mcp_client = EnhancedMCPClient(config_manager=mcp_config_manager)
            runtime_container.mcp_client = mcp_client
            logger.info(f"🔍 MCP客户端类型: {type(mcp_client)}")
            await mcp_client.connect()
            logger.info("✅ 增强MCP客户端初始化成功（含进程内 K8s/ECS 时无需单独起 k8s-mcp/ecs-mcp）")

    except Exception as e:
        # MCP初始化失败时不阻塞服务启动，只记录日志并降级
        logger.error(f"❌ 增强MCP客户端初始化失败，将以“无MCP工具”模式启动: {e}")
        mcp_client = None
        runtime_container.mcp_client = None

    # 2. LLM 处理器（优先 config/llm_config.json，环境变量为回退）
    try:
        logger.info("正在初始化 LLM 处理器...")
        llm_config_dict = resolve_llm_processor_config_dict()
        logger.info(
            f"✅ LLM 配置已解析：{llm_config_dict.get('provider', 'unknown')} - "
            f"{llm_config_dict.get('model', 'unknown')}"
        )
        llm_processor = EnhancedLLMProcessor(llm_config_dict, mcp_client)
        runtime_container.llm_processor = llm_processor
        logger.info("✅ LLM 处理器初始化成功")

        # 3. 初始化钉钉机器人
        webhook_url = os.getenv("DINGTALK_WEBHOOK_URL")
        if webhook_url:
            dingtalk_bot = DingTalkBot(
                webhook_url=webhook_url,
                secret=os.getenv("DINGTALK_SECRET"),
                llm_processor=llm_processor
            )
            runtime_container.dingtalk_bot = dingtalk_bot
            logger.info("✅ 钉钉机器人初始化成功")
        else:
            runtime_container.dingtalk_bot = None
            logger.info("钉钉机器人配置未提供，跳过初始化")

    except Exception as e:
        logger.error(f"❌ LLM / 钉钉服务初始化失败: {e}")
        # LLM是核心能力，这里仍然保留失败即中止启动的语义
        raise e

    # 4. 启动最小定时巡检（可选，基于asyncio，不引入新依赖）
    try:
        enabled = os.getenv("INSPECTION_ENABLED", "false").lower() == "true"
        interval_minutes = int(os.getenv("INSPECTION_INTERVAL_MINUTES", "0") or 0)
        if enabled and interval_minutes > 0:
            logger.info(f"⏰ 启动最小定时巡检任务，每 {interval_minutes} 分钟执行一次")
            app = globals().get('app')

            async def _periodic_inspection_task():
                from src.api.v2.endpoints.inspection import perform_inspection, InspectionScope, InspectionOptions
                while True:
                    try:
                        logger.info("⏳ 定时巡检触发")
                        scope = InspectionScope()
                        options = InspectionOptions(
                            sendToDingTalk=os.getenv("INSPECTION_SEND_TO_DINGTALK", "true").lower() == "true"
                        )
                        dingtalk_enabled = globals().get('dingtalk_bot') is not None
                        await perform_inspection(
                            mcp_client=globals().get('mcp_client'),
                            llm_processor=globals().get('llm_processor'),
                            scope=scope,
                            options=options,
                            dingtalk_enabled=dingtalk_enabled,
                        )
                        logger.info("✅ 定时巡检完成")
                    except Exception as e:
                        logger.error(f"❌ 定时巡检失败: {e}")
                    finally:
                        await asyncio.sleep(max(60, interval_minutes * 60))

            # 后台运行
            asyncio.create_task(_periodic_inspection_task())
        else:
            logger.info("定时巡检未启用（INSPECTION_ENABLED=false 或未配置间隔）")
    except Exception as e:
        logger.warning(f"定时巡检初始化失败: {e}")

    # 5. 启动增强任务调度器（基于现有asyncio模式）
    try:
        scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
        if scheduler_enabled:
            logger.info("⏰ 启动增强任务调度器...")
            from src.scheduler.task_scheduler import initialize_scheduler
            await initialize_scheduler()
            logger.info("✅ 增强任务调度器启动成功")
        else:
            logger.info("增强任务调度器未启用（SCHEDULER_ENABLED=false）")
    except Exception as e:
        logger.warning(f"增强任务调度器初始化失败: {e}")

async def recreate_llm_processor():
    """重新读取 LLM 配置文件并替换运行时处理器（钉钉机器人共用同一实例）。"""
    global llm_processor, dingtalk_bot
    llm_processor = await runtime_container.recreate_llm_processor()
    dingtalk_bot = runtime_container.dingtalk_bot


async def cleanup_services():
    """清理所有服务"""
    global mcp_client, llm_processor, dingtalk_bot

    # 清理增强任务调度器
    try:
        from src.scheduler.task_scheduler import cleanup_scheduler
        await cleanup_scheduler()
        logger.info("✅ 增强任务调度器已清理")
    except Exception as e:
        logger.warning(f"清理增强任务调度器失败: {e}")

    if mcp_client:
        await mcp_client.disconnect()

    # 重置全局变量
    mcp_client = None
    llm_processor = None
    dingtalk_bot = None
    runtime_container.mcp_client = None
    runtime_container.llm_processor = None
    runtime_container.dingtalk_bot = None

# 创建FastAPI应用
app = FastAPI(
    title="钉钉机器人 API",
    description="基于FastAPI的钉钉机器人服务",
    version="2.0.0",
    lifespan=lifespan
)
app.state.container = runtime_container


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Keep API v2 errors in the standard envelope while preserving SPA behavior."""
    if request.url.path.startswith("/api/v2"):
        from src.api.v2.standard import error_envelope

        detail = exc.detail
        message = detail if isinstance(detail, str) else "请求失败"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                request,
                code=f"HTTP_{exc.status_code}",
                message=message,
                details=detail,
            ),
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/v2"):
        from src.api.v2.standard import error_envelope

        return JSONResponse(
            status_code=422,
            content=error_envelope(
                request,
                code="VALIDATION_ERROR",
                message="请求参数校验失败",
                details=exc.errors(),
            ),
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.middleware("http")
async def operation_audit_middleware(request: Request, call_next):
    """Record API operations without blocking the request path."""
    started_at = time.time()
    response = await call_next(request)

    path = request.url.path
    if path.startswith("/api/v2") and request.method != "OPTIONS":
        try:
            from src.api.v2.standard import get_request_id
            from src.security.audit import get_audit_logger
            from src.security.auth import get_auth_service

            actor = "anonymous"
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                token = authorization.split(" ", 1)[1].strip()
                try:
                    actor = get_auth_service().current_user_from_token(token).username
                except Exception:
                    actor = "invalid-token"

            segments = [segment for segment in path.split("/") if segment]
            resource = segments[2] if len(segments) > 2 else "api"
            audit_logger = get_audit_logger()
            asyncio.create_task(
                asyncio.to_thread(
                    audit_logger.record,
                    actor=actor,
                    action=f"api.{request.method.lower()}",
                    resource=resource,
                    resource_id=None,
                    result="success" if response.status_code < 400 else "failure",
                    request_id=get_request_id(request),
                    method=request.method,
                    path=path,
                    ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "status_code": response.status_code,
                        "duration_ms": round((time.time() - started_at) * 1000, 2),
                    },
                )
            )
        except Exception as audit_error:
            logger.debug(f"操作审计记录失败: {audit_error}")

    return response

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    logger.info(f"✅ 挂载静态文件: {static_dir}")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning(f"⚠️ 静态文件目录不存在，后端将以 API-only 模式启动: {static_dir}")

# 检查SPA文件是否存在
spa_index = static_dir / "spa" / "index.html"
if spa_index.exists():
    logger.info(f"✅ SPA应用目录存在: {static_dir}/spa")
else:
    logger.warning(f"⚠️ SPA应用目录不存在: {static_dir}/spa")

# 注册API路由
app.include_router(api_v2_router)

# 根路径重定向到SPA应用
@app.get("/")
async def root():
    """根路径返回SPA应用"""
    if not spa_index.exists():
        return JSONResponse(
            status_code=200,
            content={
                "status": "api_only",
                "message": "SPA static files are not available. Use /api/v2 or deploy frontend assets.",
                "api": "/api/v2/status",
            },
        )
    return FileResponse(str(spa_index))

# SPA路由处理（确保单页应用路由正常工作）
@app.get("/spa/{path:path}")
async def spa_routes(path: str):
    """SPA路由处理"""
    file_path = static_dir / "spa" / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    if spa_index.exists():
        # 如果文件不存在，返回index.html（用于前端路由）
        return FileResponse(str(spa_index))
    raise HTTPException(status_code=404, detail="SPA static files are not available")

# 获取全局服务实例的辅助函数
def get_mcp_client():
    """获取MCP客户端实例"""
    return runtime_container.mcp_client

def get_llm_processor():
    """获取LLM处理器实例"""
    return runtime_container.llm_processor

def get_dingtalk_bot():
    """获取钉钉机器人实例"""
    return runtime_container.dingtalk_bot

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mcp_connected": runtime_container.mcp_client is not None and hasattr(runtime_container.mcp_client, 'available_tools') and len(runtime_container.mcp_client.available_tools) > 0,
        "llm_enabled": runtime_container.llm_processor is not None,
        "dingtalk_enabled": runtime_container.dingtalk_bot is not None
    }

if __name__ == "__main__":
    import uvicorn

    # 执行配置迁移检查
    check_and_migrate_config()

    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
