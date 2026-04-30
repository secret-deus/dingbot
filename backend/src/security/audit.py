"""Append-only local operation audit log."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from .redaction import redact


def get_audit_log_path() -> Path:
    return Path(os.getenv("OPERATION_AUDIT_LOG_PATH", "logs/operation_audit.jsonl"))


class AuditLogger:
    def __init__(self, path: Path | None = None):
        self.path = path or get_audit_log_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def record(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        result: str,
        request_id: str | None = None,
        resource_id: str | None = None,
        method: str | None = None,
        path: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        details: Any = None,
    ) -> dict[str, Any]:
        item = {
            "id": uuid.uuid4().hex,
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "result": result,
            "request_id": request_id,
            "method": method,
            "path": path,
            "ip": ip,
            "user_agent": user_agent,
            "details": redact(details) if details is not None else None,
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
                file.write("\n")
        return item

    def list(
        self,
        *,
        limit: int = 100,
        actor: str | None = None,
        action: str | None = None,
        result: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        limit = max(1, min(limit, 500))
        items: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if actor and item.get("actor") != actor:
                    continue
                if action and action not in item.get("action", ""):
                    continue
                if result and item.get("result") != result:
                    continue
                items.append(item)
        return list(reversed(items[-limit:]))


@lru_cache(maxsize=1)
def get_audit_logger() -> AuditLogger:
    return AuditLogger()
