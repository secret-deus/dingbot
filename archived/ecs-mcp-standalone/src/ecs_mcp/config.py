"""
ECS MCP 配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _load_envs():
    """加载环境变量，优先读取 k8s-mcp/config.env，其次本模块 config.env/.env。"""
    try:
        here = Path(__file__).resolve()
        # 目录层级: .../ecs-mcp/src/ecs_mcp/config.py
        project_root = here.parents[3]  # 仓库根目录: ding-robot/
        ecs_mcp_dir = project_root / "ecs-mcp"

        candidates = [
            ecs_mcp_dir / "config.env",
            ecs_mcp_dir / ".env",
            project_root / "k8s-mcp" / "config.env",  # 与k8s-mcp共享的环境
            project_root / "backend" / "config.env",
            project_root / ".env",
        ]

        for p in candidates:
            try:
                if p.exists():
                    load_dotenv(p, override=False)
            except Exception:
                # 静默忽略单个文件加载失败
                pass
    except Exception:
        # 静默忽略路径推断失败
        pass


# 进程初始化时尝试加载环境变量文件
_load_envs()


class ECSConfig(BaseModel):
    host: str = Field(default=os.getenv("ECS_MCP_HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("ECS_MCP_PORT", "8002")))
    debug: bool = Field(default=os.getenv("ECS_MCP_DEBUG", "false").lower() == "true")

    # 阿里云配置
    access_key_id: str | None = Field(default=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"))
    access_key_secret: str | None = Field(default=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"))
    security_token: str | None = Field(default=os.getenv("ALIBABA_CLOUD_SECURITY_TOKEN"))
    region_id: str = Field(default=os.getenv("ALIBABA_CLOUD_ECS_REGION_ID", "cn-hangzhou"))

    # 调用与并发
    call_timeout_seconds: int = Field(default=int(os.getenv("ECS_CALL_TIMEOUT", "30")))
    retry_attempts: int = Field(default=int(os.getenv("ECS_RETRY_ATTEMPTS", "3")))
    max_concurrency: int = Field(default=int(os.getenv("ECS_MAX_CONCURRENCY", "3")))


def get_config() -> ECSConfig:
    return ECSConfig()


