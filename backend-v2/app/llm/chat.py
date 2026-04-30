"""LLM 对话服务 - 基于 LiteLLM 的多供应商适配"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

import litellm
from litellm import acompletion
from loguru import logger

from app.core.config import get_settings
from app.llm.prompts import (
    format_tool_result_as_content,
    format_tools_for_prompt,
    get_system_prompt,
    truncate_messages,
)

litellm.drop_params = True


class ChatService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout

    def _build_kwargs(self, stream: bool = False) -> dict:
        kwargs: dict = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "stream": stream,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url
        return kwargs

    @staticmethod
    def _prepare_messages(
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> list[dict]:
        prepared = list(messages)
        if not prepared or prepared[0].get("role") != "system":
            system_content = get_system_prompt()
            if tools:
                system_content += "\n\n" + format_tools_for_prompt(tools)
            prepared.insert(0, {"role": "system", "content": system_content})
        settings = get_settings()
        return truncate_messages(prepared, max_tokens=settings.llm_max_tokens)

    async def stream_chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        prepared = self._prepare_messages(messages, tools)
        kwargs = self._build_kwargs(stream=True)

        if tools:
            kwargs["tools"] = self._format_tools(tools)

        try:
            response = await acompletion(messages=prepared, **kwargs)
        except Exception as e:
            logger.error("LLM 调用失败: {}", e)
            yield {"type": "error", "message": f"LLM 调用失败: {e}"}
            return

        tool_calls_acc: dict[int, dict] = {}

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            if delta.content:
                yield {"type": "token", "content": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": tc.id or "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    if tc.id:
                        tool_calls_acc[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_acc[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_acc[idx]["function"]["arguments"] += tc.function.arguments

            if chunk.choices and chunk.choices[0].finish_reason == "tool_calls":
                for tc in sorted(tool_calls_acc.values(), key=lambda x: x.get("id", "")):
                    yield {"type": "tool_call", "tool_call": tc}

        yield {"type": "done"}

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> dict:
        prepared = self._prepare_messages(messages, tools)
        kwargs = self._build_kwargs(stream=False)
        if tools:
            kwargs["tools"] = self._format_tools(tools)

        try:
            response = await acompletion(messages=prepared, **kwargs)
        except Exception as e:
            logger.error("LLM 调用失败: {}", e)
            return {"error": str(e)}

        choice = response.choices[0]
        result: dict = {"content": choice.message.content or ""}
        if choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
        return result

    @staticmethod
    def _format_tools(tools: list[dict]) -> list[dict]:
        formatted = []
        for t in tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("inputSchema", {}),
                },
            })
        return formatted
