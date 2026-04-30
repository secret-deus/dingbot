"""Read-only operations overview endpoint."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_runtime_container
from ..standard import success_envelope
from ....app.container import RuntimeContainer
from ....security.auth import require_permission

router = APIRouter(prefix="/ops", tags=["Ops"])


async def _safe_tool_count(container: RuntimeContainer) -> tuple[int, str]:
    client = container.mcp_client
    if not client:
        return 0, "fallback:no_mcp_client"
    try:
        tools = await client.list_tools()
        return len(tools), "runtime:mcp_client.list_tools"
    except Exception:
        available = getattr(client, "available_tools", None)
        if available is not None:
            try:
                return len(available), "runtime:mcp_client.available_tools"
            except Exception:
                pass
    return 0, "fallback:tool_count_unavailable"


async def _safe_mcp_runtime(container: RuntimeContainer) -> Dict[str, Any]:
    client = container.mcp_client
    if not client:
        return {
            "enabled": False,
            "transport": "none",
            "status": "unavailable",
            "tool_count": 0,
            "providers": [],
            "remote_connections": 0,
        }
    try:
        health = await client.health_check()
        local_runtime = health.get("local_runtime") or {}
        return {
            "enabled": bool(local_runtime.get("enabled", True)),
            "transport": local_runtime.get("transport", "local"),
            "status": local_runtime.get("status", health.get("overall_status", "unknown")),
            "tool_count": local_runtime.get("tool_count", health.get("total_tools", 0)),
            "providers": local_runtime.get("providers", []),
            "remote_connections": len(health.get("servers", {})),
        }
    except Exception as exc:
        return {
            "enabled": True,
            "transport": "unknown",
            "status": "degraded",
            "tool_count": 0,
            "providers": [],
            "remote_connections": 0,
            "reason": str(exc),
        }


def _current_skill() -> Dict[str, Any]:
    try:
        from src.skills.registry import get_skill_registry

        registry = get_skill_registry()
        return {
            "id": registry.default_skill_id,
            "source": "config/skills.json",
        }
    except Exception as exc:
        return {
            "id": None,
            "source": "fallback:skills_unavailable",
            "reason": str(exc),
        }


@router.get(
    "/overview",
    summary="Ops workbench overview",
    dependencies=[Depends(require_permission("ops:read"))],
)
async def get_ops_overview(
    request: Request,
    container: RuntimeContainer = Depends(get_runtime_container),
):
    """Return a stable read-only aggregate for the ops prototype workbench."""
    tool_count, tool_source = await _safe_tool_count(container)
    mcp_runtime = await _safe_mcp_runtime(container)
    llm_enabled = container.llm_processor is not None
    mcp_enabled = container.mcp_client is not None
    dingtalk_enabled = container.dingtalk_bot is not None

    risks: List[Dict[str, Any]] = []
    if not llm_enabled:
        risks.append(
            {
                "id": "llm-unavailable",
                "level": "critical",
                "title": "LLM runtime is unavailable",
                "description": "LLM 处理器尚未初始化，AI 诊断会降级为不可用。",
                "state": "需处理",
                "source": "runtime",
            }
        )
    if not mcp_enabled:
        risks.append(
            {
                "id": "mcp-unavailable",
                "level": "warning",
                "title": "MCP tools are unavailable",
                "description": "工具运行时未连接，K8s/ECS 取证能力不可用。",
                "state": "待连接",
                "source": "runtime",
            }
        )
    if not dingtalk_enabled:
        risks.append(
            {
                "id": "dingtalk-disabled",
                "level": "normal",
                "title": "DingTalk notification is not configured",
                "description": "未配置钉钉通知，事故同步和任务通知会跳过。",
                "state": "可选",
                "source": "fallback:env_or_runtime",
            }
        )

    mode = "crewai" if os.getenv("USE_CREWAI", "false").lower() == "true" else "standard"
    status = "healthy" if llm_enabled and mcp_enabled else "degraded"
    health_level = "healthy" if status == "healthy" else "warning"
    now = time.time()
    now_label = time.strftime("%H:%M", time.localtime(now))
    environment = os.getenv("OPS_DEFAULT_ENVIRONMENT", "prod-cn")
    mode_label = "CrewAI / 只读诊断 / 审计开启" if mode == "crewai" else "标准 / 只读诊断 / 审计开启"
    tool_coverage = "100%" if tool_count else "0%"
    source_note = "实时运行时快照" if (llm_enabled or mcp_enabled or dingtalk_enabled) else "运行时未完全初始化，返回降级快照"

    data = {
        "summary": f"{environment} 当前为 {status} 状态，已按只读模式聚合运行时、工具和通知上下文。",
        "environment": environment,
        "environments": [environment, "staging", "dev"],
        "mode": mode_label,
        "healthLevel": health_level,
        "contextNote": f"{source_note}；工具来源：{tool_source}；MCP={mcp_runtime['transport']}:{mcp_runtime['status']}。",
        "metrics": [
            {
                "label": "运行状态",
                "value": "OK" if status == "healthy" else "DEG",
                "detail": "LLM 与 MCP 均可用" if status == "healthy" else "至少一个运行时组件降级",
                "tone": "good" if status == "healthy" else "warning",
            },
            {
                "label": "可用工具",
                "value": str(tool_count),
                "detail": tool_source,
                "tone": "good" if tool_count else "warning",
            },
            {
                "label": "风险项",
                "value": str(len(risks)),
                "detail": "运行时聚合风险",
                "tone": "danger" if any(r["level"] == "critical" for r in risks) else "neutral",
            },
            {
                "label": "通知链路",
                "value": "ON" if dingtalk_enabled else "OFF",
                "detail": "DingTalk 已配置" if dingtalk_enabled else "DingTalk 未配置",
                "tone": "good" if dingtalk_enabled else "neutral",
            },
        ],
        "messages": [
            {
                "id": "ops-user-snapshot",
                "role": "user",
                "actor": "SRE",
                "time": now_label,
                "content": "刷新运维指挥台运行时概览，保持只读诊断。",
            },
            {
                "id": "ops-assistant-snapshot",
                "role": "assistant",
                "actor": "DingOps Copilot",
                "time": now_label,
                "title": "运行时概览",
                "confidence": "runtime",
                "content": f"LLM={llm_enabled}，MCP={mcp_enabled}，DingTalk={dingtalk_enabled}，可用工具数={tool_count}。",
                "findings": [
                    {"label": "LLM", "value": "ON" if llm_enabled else "OFF"},
                    {"label": "MCP", "value": "ON" if mcp_enabled else "OFF"},
                    {"label": "Tools", "value": str(tool_count)},
                ],
            },
        ],
        "toolTraces": [
            {
                "id": "trace-mcp-tools",
                "name": "local_mcp_runtime",
                "state": "green" if tool_count else "amber",
                "stateText": "完成" if tool_count else "降级",
                "description": "读取本地 MCP runtime 工具清单，用于判断当前可取证范围。",
                "evidence": (
                    f"transport={mcp_runtime['transport']}; status={mcp_runtime['status']}; "
                    f"count={tool_count}; remote_connections={mcp_runtime['remote_connections']}"
                ),
            },
            {
                "id": "trace-runtime-container",
                "name": "runtime_container",
                "state": "green" if (llm_enabled or mcp_enabled) else "amber",
                "stateText": "已读取",
                "description": "从 app RuntimeContainer 聚合长生命周期服务状态。",
                "evidence": f"llm={llm_enabled} mcp={mcp_enabled} dingtalk={dingtalk_enabled}",
            },
            {
                "id": "trace-policy",
                "name": "ops_readonly_policy",
                "state": "green",
                "stateText": "只读",
                "description": "该接口只返回概览，不触发任何工具写操作。",
                "evidence": "read_only=true",
            },
        ],
        "system_health": {
            "status": status,
            "components": {
                "llm": {"enabled": llm_enabled, "source": "runtime"},
                "mcp": {
                    "enabled": mcp_enabled,
                    "source": "runtime",
                    "transport": mcp_runtime["transport"],
                    "status": mcp_runtime["status"],
                },
                "dingtalk": {"enabled": dingtalk_enabled, "source": "runtime"},
            },
        },
        "tools": {
            "count": tool_count,
            "source": tool_source,
            "transport": mcp_runtime["transport"],
        },
        "mcpRuntime": mcp_runtime,
        "mcp_runtime": mcp_runtime,
        "risks": risks,
        "timeline": [
            {
                "id": "runtime-snapshot",
                "time": now_label,
                "title": "Runtime snapshot generated",
                "description": "API 聚合运行时组件、工具清单和通知链路状态。",
                "ts": now,
                "source": "runtime",
            }
        ],
        "automationQueue": [
            {
                "id": "queue-readonly",
                "title": "只读诊断策略",
                "status": "已启用",
                "progress": 100,
            },
            {
                "id": "queue-audit",
                "title": "工具调用审计",
                "status": "待接入",
                "progress": 35,
            },
        ],
        "automation_queue": [
            {
                "id": "queue-readonly",
                "title": "只读诊断策略",
                "status": "已启用",
                "progress": 100,
            },
            {
                "id": "queue-audit",
                "title": "工具调用审计",
                "status": "待接入",
                "progress": 35,
            },
        ],
        "topology": {
            "nodes": [
                {"id": "web", "name": "Ops Workbench", "label": "Ops Workbench", "meta": "Vue dashboard", "tone": "blue", "x": 8, "y": 18, "type": "frontend", "source": "contract"},
                {"id": "api", "name": "FastAPI", "label": "FastAPI", "meta": "v2 envelope", "tone": "blue", "x": 38, "y": 34, "type": "backend", "source": "runtime"},
                {"id": "llm", "name": "LLM", "label": "LLM", "meta": "chat runtime", "tone": "green" if llm_enabled else "amber", "x": 68, "y": 16, "type": "service", "source": "runtime"},
                {"id": "mcp", "name": "MCP Tools", "label": "MCP Tools", "meta": f"{tool_count} tools", "tone": "green" if tool_count else "amber", "x": 64, "y": 60, "type": "tool_runtime", "source": "runtime"},
                {"id": "dingtalk", "name": "DingTalk", "label": "DingTalk", "meta": "notification", "tone": "green" if dingtalk_enabled else "amber", "x": 10, "y": 64, "type": "notification", "source": "runtime"},
            ],
            "edges": [
                {"id": "edge-web-api", "from": "web", "to": "api", "label": "HTTPS/API", "left": 24, "top": 30, "width": 22, "rotate": 16, "source": "contract"},
                {"id": "edge-api-llm", "from": "api", "to": "llm", "label": "chat", "left": 52, "top": 32, "width": 20, "rotate": -18, "source": "runtime"},
                {"id": "edge-api-mcp", "from": "api", "to": "mcp", "label": "tool calls", "left": 52, "top": 50, "width": 18, "rotate": 26, "source": "runtime"},
                {"id": "edge-dingtalk-api", "from": "dingtalk", "to": "api", "label": "notifications", "left": 24, "top": 62, "width": 22, "rotate": -20, "source": "runtime"},
            ],
        },
        "current": {
            "skill": _current_skill(),
            "mode": {"id": mode, "source": "env:USE_CREWAI"},
        },
    }
    return success_envelope(request, data, meta={"read_only": True})
