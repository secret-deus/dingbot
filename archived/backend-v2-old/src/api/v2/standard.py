"""Standard API response helpers for v2 endpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from fastapi import Request


def get_request_id(request: Request) -> str:
    request_id = request.headers.get("x-request-id") or getattr(request.state, "request_id", None)
    if request_id:
        return str(request_id)
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    return request_id


def success_envelope(
    request: Request,
    data: Any,
    *,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response_meta = {
        "request_id": get_request_id(request),
        "timestamp": time.time(),
    }
    if meta:
        response_meta.update(meta)
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": response_meta,
    }


def error_envelope(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response_meta = {
        "request_id": get_request_id(request),
        "timestamp": time.time(),
    }
    if meta:
        response_meta.update(meta)
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": response_meta,
    }
