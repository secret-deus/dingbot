"""Chat stream event encoding and compatibility helpers."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, Optional


DONE_TOKEN = "[DONE]"


def encode_sse_event(event: Dict[str, Any]) -> str:
    """Encode a structured event as one SSE data frame."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def encode_done() -> str:
    """Temporary compatibility marker for the current frontend."""
    return f"data: {DONE_TOKEN}\n\n"


def message_delta(content: str) -> Dict[str, Any]:
    return {
        "type": "message_delta",
        "content": content,
    }


def final_event(
    content: str = "",
    tool_call_count: int = 0,
) -> Dict[str, Any]:
    return {
        "type": "final",
        "content": content,
        "tool_call_count": tool_call_count,
    }


def error_event(
    message: str,
    *,
    code: str = "STREAM_ERROR",
    recoverable: bool = True,
    suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "type": "error",
        "code": code,
        "message": message,
        "recoverable": recoverable,
        "timestamp": time.time(),
    }
    if suggestions:
        event["suggestions"] = suggestions
    return event


def normalize_stream_chunk(chunk: Any) -> List[Dict[str, Any]]:
    """Convert legacy processor chunks into contract-level stream events.

    The existing processor still yields a mixture of text and legacy dict
    payloads. This function is the API boundary that keeps those internals from
    leaking into the frontend while the chat use case is being refactored.
    """
    if chunk is None:
        return []

    if isinstance(chunk, str):
        if chunk == "":
            return []
        return [message_delta(chunk)]

    if isinstance(chunk, dict):
        return [_normalize_dict_event(chunk)]

    text = str(chunk)
    if not text.strip():
        return []
    return [message_delta(text)]


def iter_sse_frames(events: Iterable[Dict[str, Any]]) -> Iterable[str]:
    for event in events:
        yield encode_sse_event(event)


def _normalize_dict_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event_type = event.get("type")

    if event_type == "tool_call_start":
        tool_call = event.get("tool_call") or {}
        arguments = _parse_arguments(tool_call.get("arguments"))
        return {
            **event,
            "type": "tool_call_start",
            "id": tool_call.get("id") or event.get("id"),
            "tool": tool_call.get("name") or event.get("tool"),
            "arguments": arguments,
        }

    if event_type in {"tool_call_update", "tool_call_complete", "tool_result"}:
        tool_call = event.get("tool_call") or {}
        status = tool_call.get("status") or event.get("status")
        success = status != "error" and not event.get("error")
        normalized = {
            **event,
            "type": "tool_call_result",
            "legacy_type": event_type,
            "id": tool_call.get("id") or event.get("id"),
            "tool": tool_call.get("name") or event.get("tool"),
            "success": success,
            "result": event.get("result"),
        }
        if "duration" in tool_call:
            normalized["duration"] = tool_call.get("duration")
        if event.get("error"):
            normalized["error"] = event.get("error")
        return normalized

    if event_type == "error":
        return {
            **event,
            "type": "error",
            "code": event.get("code") or event.get("error_code") or "STREAM_ERROR",
            "message": event.get("message") or event.get("detail") or "流式响应失败",
            "recoverable": event.get("recoverable", True),
        }

    if event_type == "final":
        return {
            **event,
            "type": "final",
            "content": event.get("content", ""),
            "tool_call_count": event.get("tool_call_count", 0),
        }

    if event_type:
        return event

    if "content" in event:
        return message_delta(str(event.get("content") or ""))

    return message_delta(json.dumps(event, ensure_ascii=False))


def _parse_arguments(arguments: Any) -> Dict[str, Any]:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            return {"raw": arguments}
    return {"value": arguments}
