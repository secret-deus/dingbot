"""LLM 处理器上下文与结果体量限制（从 processor 拆分）。"""

import json
from typing import Any

from loguru import logger

MAX_RESULT_SIZE = 50000
MAX_RESULT_LINES = 1000
SUMMARY_TARGET_SIZE = 8000
MAX_CONTEXT_TOKENS = 100000
MAX_HISTORY_MESSAGES = 20


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（约 4 字符/token）。"""
    return len(text) // 4


def check_result_size_exceeds(
    result: Any,
    max_size_bytes: int = MAX_RESULT_SIZE,
    max_lines: int = MAX_RESULT_LINES,
) -> bool:
    """判断序列化后的结果是否超过体量上限。"""
    try:
        result_str = json.dumps(result, ensure_ascii=False, indent=2)
        result_size = len(result_str.encode("utf-8"))
        result_lines = result_str.count("\n")
        logger.debug(f"结果大小检查: {result_size} bytes, {result_lines} lines")
        return result_size > max_size_bytes or result_lines > max_lines
    except Exception as e:
        logger.warning(f"检查结果大小时出错: {e}")
        return False
