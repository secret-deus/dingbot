"""
钉钉机器人 + LLM + MCP 集成系统
FastAPI 主应用入口 - 集成前后端服务
"""

# 导入必要的模块
import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager

# 环境变量加载
from dotenv import load_dotenv

# FastAPI相关
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# 日志配置
from loguru import logger

# 本地模块
from src.api.v2.router import api_v2_router
from src.mcp.enhanced_client import EnhancedMCPClient
from src.config.manager import config_manager
from src.llm.processor import EnhancedLLMProcessor
from src.dingtalk.bot import DingTalkBot

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

# 全局变量存储服务实例
mcp_client = None
llm_processor = None
dingtalk_bot = None

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

    try:
        # 1. 初始化增强MCP客户端
        logger.info("初始化增强MCP客户端...")
        mcp_client = EnhancedMCPClient()
        await mcp_client.connect()
        logger.info("✅ 增强MCP客户端初始化成功")

        # 2. 简化的LLM处理器初始化（直接从环境变量）
        logger.info("正在初始化简化LLM处理器...")
        
        # 直接从环境变量获取简单配置
        llm_config_dict = await config_manager.get_current_llm_config()
        
        logger.info(f"✅ LLM配置加载成功：{llm_config_dict.get('provider', 'unknown')} - {llm_config_dict.get('model', 'unknown')}")
        
        # 使用简化的LLM处理器，传入字典配置
        llm_processor = EnhancedLLMProcessor(llm_config_dict, mcp_client)
        logger.info("✅ LLM 处理器初始化成功")
        
        # 3. 初始化钉钉机器人
        webhook_url = os.getenv("DINGTALK_WEBHOOK_URL")
        if webhook_url:
            dingtalk_bot = DingTalkBot(
                webhook_url=webhook_url,
                secret=os.getenv("DINGTALK_SECRET"),
                llm_processor=llm_processor
            )
            logger.info("✅ 钉钉机器人初始化成功")
        else:
            logger.info("钉钉机器人配置未提供，跳过初始化")

    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
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

async def cleanup_services():
    """清理所有服务"""
    global mcp_client, llm_processor, dingtalk_bot

    if mcp_client:
        await mcp_client.disconnect()
    
    # 重置全局变量
    mcp_client = None
    llm_processor = None
    dingtalk_bot = None

# 创建FastAPI应用
app = FastAPI(
    title="钉钉机器人 API",
    description="基于FastAPI的钉钉机器人服务",
    version="2.0.0",
    lifespan=lifespan
)

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
logger.info(f"✅ 挂载静态文件: {static_dir}")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
    return FileResponse(str(spa_index))

# SPA路由处理（确保单页应用路由正常工作）
@app.get("/spa/{path:path}")
async def spa_routes(path: str):
    """SPA路由处理"""
    file_path = static_dir / "spa" / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    else:
        # 如果文件不存在，返回index.html（用于前端路由）
        return FileResponse(str(spa_index))

# 获取全局服务实例的辅助函数
def get_mcp_client():
    """获取MCP客户端实例"""
    return mcp_client

def get_llm_processor():
    """获取LLM处理器实例"""
    return llm_processor

def get_dingtalk_bot():
    """获取钉钉机器人实例"""
    return dingtalk_bot

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mcp_connected": mcp_client is not None and hasattr(mcp_client, 'available_tools') and len(mcp_client.available_tools) > 0,
        "llm_enabled": llm_processor is not None,
        "dingtalk_enabled": dingtalk_bot is not None
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