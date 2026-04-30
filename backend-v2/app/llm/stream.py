"""SSE 流式输出 - 与前端 EventSource 对接"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

from sse_starlette.sse import EventSourceResponse

from app.llm.chat import ChatService


async def create_sse_stream(
    chat_service: ChatService,
    messages: list[dict],
    tools: Optional[list[dict]] = None,
) -> EventSourceResponse:
    async def _generate():
        async for event in chat_service.stream_chat(messages, tools):
            event_type = event.get("type", "unknown")
            data = json.dumps(event, ensure_ascii=False)
            yield {"event": event_type, "data": data}

    return EventSourceResponse(_generate())


async def stream_events(
    chat_service: ChatService,
    messages: list[dict],
    tools: Optional[list[dict]] = None,
) -> AsyncGenerator[str, None]:
    async for event in chat_service.stream_chat(messages, tools):
        event_type = event.get("type", "unknown")
        data = json.dumps(event, ensure_ascii=False)
        yield f"event: {event_type}\ndata: {data}\n\n"
