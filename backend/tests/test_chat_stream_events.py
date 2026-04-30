"""Chat stream event contract helpers."""

import json

from src.api.v2.stream_events import (
    DONE_TOKEN,
    encode_done,
    encode_sse_event,
    normalize_stream_chunk,
)


def test_text_chunk_becomes_message_delta_event():
    events = normalize_stream_chunk("hello\nworld")

    assert events == [{"type": "message_delta", "content": "hello\nworld"}]
    frame = encode_sse_event(events[0])
    assert frame.startswith("data: ")
    assert json.loads(frame.removeprefix("data: ").strip()) == events[0]


def test_legacy_tool_start_is_flattened_but_keeps_legacy_payload():
    events = normalize_stream_chunk(
        {
            "type": "tool_call_start",
            "tool_call": {
                "id": "call_1",
                "name": "k8s-get-pods",
                "arguments": "{\"namespace\":\"default\"}",
            },
        }
    )

    assert events[0]["type"] == "tool_call_start"
    assert events[0]["id"] == "call_1"
    assert events[0]["tool"] == "k8s-get-pods"
    assert events[0]["arguments"] == {"namespace": "default"}
    assert events[0]["tool_call"]["id"] == "call_1"


def test_legacy_tool_update_becomes_tool_result():
    events = normalize_stream_chunk(
        {
            "type": "tool_call_update",
            "tool_call": {
                "id": "call_1",
                "name": "k8s-get-pods",
                "status": "success",
                "duration": 0.2,
            },
            "result": {"count": 2},
        }
    )

    assert events[0]["type"] == "tool_call_result"
    assert events[0]["legacy_type"] == "tool_call_update"
    assert events[0]["id"] == "call_1"
    assert events[0]["tool"] == "k8s-get-pods"
    assert events[0]["success"] is True
    assert events[0]["result"] == {"count": 2}


def test_done_marker_is_kept_for_compatibility():
    assert encode_done() == f"data: {DONE_TOKEN}\n\n"
