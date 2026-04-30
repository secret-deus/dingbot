"""Runtime dependency container for API handlers.

The first phase keeps compatibility with the existing ``main.py`` globals while
moving route handlers to an explicit container boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger


@dataclass
class RuntimeContainer:
    """Holds long-lived runtime services used by API dependencies."""

    mcp_client: Optional[Any] = None
    llm_processor: Optional[Any] = None
    dingtalk_bot: Optional[Any] = None

    async def recreate_llm_processor(self) -> Any:
        """Reload LLM config from disk and replace the runtime processor."""
        from src.llm.config import resolve_llm_processor_config_dict
        from src.llm.config_manager import get_llm_config_manager
        from src.llm.processor import EnhancedLLMProcessor

        mgr = get_llm_config_manager()
        mgr.reload_config()
        llm_config_dict = resolve_llm_processor_config_dict()
        self.llm_processor = EnhancedLLMProcessor(llm_config_dict, self.mcp_client)
        if self.dingtalk_bot is not None:
            self.dingtalk_bot.llm_processor = self.llm_processor
        logger.info("✅ LLM 处理器已按磁盘配置重新构建")
        return self.llm_processor


_active_container: Optional[RuntimeContainer] = None


def set_runtime_container(container: RuntimeContainer) -> None:
    """Register the process-wide runtime container."""
    global _active_container
    _active_container = container


def get_active_container() -> RuntimeContainer:
    """Return the process-wide runtime container for background code paths."""
    global _active_container
    if _active_container is None:
        _active_container = RuntimeContainer()
    return _active_container
