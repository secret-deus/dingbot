"""
可选 CrewAI 多智能体编排（环境变量 USE_CREWAI=true）。

与 EnhancedLLMProcessor.stream_chat 并存：由路由层择一调用。
MCP 通过单一 CrewAI Tool `invoke_mcp_tool` 转发，并在内部做 Skill 校验。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from loguru import logger


def use_crewai_enabled() -> bool:
    return os.getenv("USE_CREWAI", "").lower() in ("1", "true", "yes")


def crewai_importable() -> bool:
    """crewai 包是否可用（Python>=3.14 时 Poetry 不会安装该依赖）。"""
    try:
        import importlib.util

        return importlib.util.find_spec("crewai") is not None
    except Exception:
        return False


async def run_crew_chat_async(
    message: str,
    mcp_client: Any,
    llm_config: Dict[str, Any],
    skill_id: Optional[str] = None,
) -> str:
    """
    运行一个最小 Crew：协调员 Agent + 带 MCP 桥接的执行说明。
    在 asyncio 中通过 run_in_executor 执行同步的 crew.kickoff()，避免阻塞事件循环。
    """
    if not crewai_importable():
        raise RuntimeError(
            "未安装 crewai：请在 Python 3.11–3.13 环境下执行 poetry install；"
            "当前解释器若为 3.14+，上游 crewai 尚不支持，请关闭 USE_CREWAI 或使用 3.13 虚拟环境。"
        )

    from src.skills.registry import get_skill_registry

    reg = get_skill_registry()
    all_tools = await mcp_client.list_tools()
    all_names = [t.name for t in all_tools]
    allowed = reg.filter_tool_names(skill_id, all_names)

    def _sync_kickoff() -> str:
        from crewai import Agent, Crew, Process, Task

        try:
            from crewai.tools import tool
        except ImportError as e:
            raise RuntimeError("crewai 未正确安装") from e

        @tool("invoke_mcp_tool")
        def invoke_mcp_tool(tool_name: str, arguments_json: str = "{}") -> str:
            """调用已注册的 MCP 工具。arguments_json 为 JSON 对象字符串。"""
            if tool_name not in allowed:
                return json.dumps(
                    {"error": True, "message": f"工具 {tool_name} 不在当前 Skill 允许范围内"},
                    ensure_ascii=False,
                )
            try:
                params = json.loads(arguments_json) if arguments_json else {}
                if not isinstance(params, dict):
                    params = {"value": params}
            except json.JSONDecodeError as je:
                return json.dumps({"error": True, "message": f"参数非合法 JSON: {je}"})

            async def _call():
                mcp_client.set_skill_context(skill_id or reg.default_skill_id, allowed)
                try:
                    return await mcp_client.call_tool(tool_name, params)
                finally:
                    mcp_client.clear_skill_context()

            import asyncio

            return json.dumps(asyncio.run(_call()), ensure_ascii=False)

        ak = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        if ak:
            os.environ.setdefault("OPENAI_API_KEY", ak)

        coordinator = Agent(
            role="运维协调员",
            goal="理解用户需求并决定是否需要调用 invoke_mcp_tool 获取集群或云资源数据",
            backstory="你负责 Kubernetes 与阿里云 ECS 相关运维问题，必要时通过工具查询事实。",
            tools=[invoke_mcp_tool],
            verbose=False,
            allow_delegation=False,
        )

        task = Task(
            description=(
                f"用户问题：{message}\n\n"
                f"可用工具名（受 Skill 限制）：{', '.join(sorted(allowed))}\n"
                "若需查询数据，请使用 invoke_mcp_tool(tool_name=..., arguments_json='{{...}}')。"
            ),
            expected_output="面向用户的中文回答，包含必要的数据摘要。",
            agent=coordinator,
        )

        crew = Crew(
            agents=[coordinator],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        result = crew.kickoff()
        return str(result)

    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_kickoff)
