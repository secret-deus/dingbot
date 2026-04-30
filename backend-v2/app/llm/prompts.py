"""系统提示词模板、工具调用格式化、上下文窗口管理"""

from __future__ import annotations

import json
from typing import Any, Sequence

from loguru import logger

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# 系统提示词
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_ZH: str = """\
你是一个专业的 Kubernetes 运维助手，服务于钉钉运维机器人平台。你的职责是帮助用户完成
K8s 集群的日常运维操作，包括但不限于：

1. 资源查询：查看 Pod、Deployment、Service、Node、ConfigMap 等资源的状态与详情
2. 故障排查：分析 Pod 异常、事件排查、日志检索、资源瓶颈定位
3. 运维操作：扩缩容、滚动更新、重启 Pod、修改配置等（需确认后执行）
4. 巡检报告：汇总集群健康状态、资源使用率、安全合规检查
5. ECS 运维：实例查询、磁盘扩容、安全组管理等阿里云 ECS 相关操作

工作规范：
- 使用中文回答，专业术语保留英文原文
- 执行变更类操作前必须向用户确认，说明影响范围
- 返回结果要结构化，重点信息加粗标注
- 若信息不足，主动追问而非猜测
- 严格遵守最小权限原则，不做超出用户意图的操作
- 遇到敏感信息（密钥、令牌）在输出中自动脱敏
"""


def get_system_prompt(lang: str = "zh") -> str:
    return SYSTEM_PROMPT_ZH if lang == "zh" else SYSTEM_PROMPT_ZH


# ---------------------------------------------------------------------------
# 工具调用格式化
# ---------------------------------------------------------------------------

def format_tool_description(tool: dict[str, Any]) -> str:
    name = tool.get("name", "unknown")
    desc = tool.get("description", "")
    schema = tool.get("inputSchema", {})
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    params = ", ".join(
        f"{p}: {properties[p].get('type', 'any')}" + (" (必填)" if p in required else "")
        for p in properties
    )
    return f"- {name}({params}): {desc}"


def format_tools_for_prompt(tools: Sequence[dict[str, Any]]) -> str:
    if not tools:
        return ""
    header = "可用工具列表："
    body = "\n".join(format_tool_description(t) for t in tools)
    return f"{header}\n{body}"


def format_tool_result_as_content(tool_name: str, result: Any) -> str:
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(result)


# ---------------------------------------------------------------------------
# 上下文窗口管理 (粗略字符估算，避免引入 tiktoken 依赖)
# ---------------------------------------------------------------------------

CHARS_PER_TOKEN = 4  # 粗略估算：1 token ≈ 4 字符（中英混合）


def count_tokens_approx(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def count_message_tokens_approx(messages: Sequence[dict[str, Any]]) -> int:
    total = 0
    for msg in messages:
        total += 4
        total += count_tokens_approx(msg.get("content", "") or "")
        if tool_calls := msg.get("tool_calls"):
            total += count_tokens_approx(json.dumps(tool_calls, ensure_ascii=False))
    return total


def truncate_messages(
    messages: list[dict[str, Any]],
    max_tokens: int | None = None,
) -> list[dict[str, Any]]:
    if not messages:
        return messages

    settings = get_settings()
    budget = max_tokens if max_tokens is not None else settings.llm_max_tokens

    if count_message_tokens_approx(messages) <= budget:
        return messages

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    body = messages[1:] if system_msg else messages[:]

    while body and count_message_tokens_approx(([system_msg] if system_msg else []) + body) > budget:
        body = body[1:]

    result = ([system_msg] if system_msg else []) + body
    dropped = len(messages) - len(result)
    if dropped:
        logger.warning("上下文截断: 移除了 {} 条消息以适应 {} token 限制", dropped, budget)
    return result
