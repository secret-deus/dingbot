"""FastAPI dependencies for runtime services."""

from __future__ import annotations

from fastapi import HTTPException, Request

from ...app.container import RuntimeContainer, get_active_container, set_runtime_container


def get_runtime_container(request: Request) -> RuntimeContainer:
    """Resolve the runtime container from ``request.app.state``."""
    container = getattr(request.app.state, "container", None)
    if container is None:
        container = get_active_container()
        request.app.state.container = container
    return container


def get_mcp_client(request: Request):
    return get_runtime_container(request).mcp_client


def get_llm_processor(request: Request):
    llm_processor = get_runtime_container(request).llm_processor
    if not llm_processor:
        raise HTTPException(status_code=503, detail="LLM处理器未初始化")
    return llm_processor


def get_dingtalk_bot(request: Request):
    return get_runtime_container(request).dingtalk_bot


async def recreate_llm_processor(request: Request):
    return await get_runtime_container(request).recreate_llm_processor()
