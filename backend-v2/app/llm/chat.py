"""LLM 对话服务 - 基于 LiteLLM 的多供应商适配"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

import litellm
from litellm import acompletion
from loguru import logger

from app.core.config import get_settings
from app.llm.config_store import LLMProviderRuntime
from app.llm.prompts import (
    format_tool_result_as_content,
    format_tools_for_prompt,
    get_system_prompt,
    truncate_messages,
)

litellm.drop_params = True


class ChatService:
    def __init__(self, provider: LLMProviderRuntime | None = None) -> None:
        if provider:
            self.provider_id = provider.id
            self.model = provider.model
            self.api_key = provider.api_key
            self.base_url = provider.base_url
            self.temperature = provider.temperature
            self.max_tokens = provider.max_tokens
            self.timeout = provider.timeout
            self.stream = provider.stream
            return

        settings = get_settings()
        self.provider_id = "env"
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
        self.stream = True

    def _build_kwargs(self, stream: bool = False) -> dict:
        kwargs: dict = {
            "model": self._litellm_model(),
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

    def _litellm_model(self) -> str:
        if "/" in self.model:
            return self.model
        if self.base_url and self.provider_id in {"openai", "openai-compatible", "env"}:
            return f"openai/{self.model}"
        return self.model

    def _prepare_messages(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> list[dict]:
        prepared = list(messages)
        if not prepared or prepared[0].get("role") != "system":
            system_content = get_system_prompt()
            if tools:
                system_content += "\n\n" + format_tools_for_prompt(tools)
            prepared.insert(0, {"role": "system", "content": system_content})
        return truncate_messages(prepared, max_tokens=self.max_tokens)

    async def stream_chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        prepared = self._prepare_messages(messages, tools)
        kwargs = self._build_kwargs(stream=self.stream)

        if tools:
            kwargs["tools"] = self._format_tools(tools)

        try:
            response = await acompletion(messages=prepared, **kwargs)
        except Exception as e:
            logger.error("LLM 调用失败: {}", e)
            yield {"type": "error", "message": f"LLM 调用失败: {e}"}
            return

        if not self.stream:
            choice = response.choices[0] if response.choices else None
            message = choice.message if choice else None
            reasoning_content = self._extract_reasoning_content(message)
            if message and message.content:
                yield {"type": "token", "content": message.content}
            if message and message.tool_calls:
                for tc in message.tool_calls:
                    event = {
                        "type": "tool_call",
                        "tool_call": {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        },
                    }
                    if reasoning_content:
                        event["reasoning_content"] = reasoning_content
                    yield event
            yield {"type": "done"}
            return

        tool_calls_acc: dict[int, dict] = {}
        reasoning_content_acc = ""

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            if reasoning_delta := self._extract_reasoning_content(delta):
                reasoning_content_acc += reasoning_delta

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
                    event = {"type": "tool_call", "tool_call": tc}
                    if reasoning_content_acc:
                        event["reasoning_content"] = reasoning_content_acc
                    yield event

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
        if reasoning_content := self._extract_reasoning_content(choice.message):
            result["reasoning_content"] = reasoning_content
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

    @staticmethod
    def _extract_reasoning_content(message: object) -> str:
        if message is None:
            return ""
        value = None
        if isinstance(message, dict):
            value = message.get("reasoning_content")
        else:
            value = getattr(message, "reasoning_content", None)
            if value is None and hasattr(message, "get"):
                value = message.get("reasoning_content")
        if value is None:
            for extra_name in ("provider_specific_fields", "model_extra", "additional_kwargs"):
                extra = message.get(extra_name) if isinstance(message, dict) else getattr(message, extra_name, None)
                if isinstance(extra, dict) and isinstance(extra.get("reasoning_content"), str):
                    value = extra["reasoning_content"]
                    break
        return value if isinstance(value, str) else ""
