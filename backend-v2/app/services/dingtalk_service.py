"""DingTalk webhook notification service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx


class DingTalkNotifier:
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
        timeout: float = 10,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        self.webhook_url = webhook_url if webhook_url is not None else settings.dingtalk_webhook_url
        self.secret = secret if secret is not None else settings.dingtalk_secret
        self.timeout = timeout
        self.transport = transport

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    async def send_task_result(
        self,
        task_name: str,
        status: str,
        result: str,
        error: Optional[str] = None,
    ) -> dict[str, Any]:
        title = f"定时任务{self._status_label(status)}: {task_name}"
        lines = [
            f"### {title}",
            "",
            f"- 状态: {status}",
            f"- 任务: {task_name}",
        ]
        if error:
            lines.extend(["", "#### 错误", error])
        if result:
            lines.extend(["", "#### 输出", self._truncate(result)])
        return await self.send_markdown(title=title, text="\n".join(lines))

    async def send_markdown(self, title: str, text: str) -> dict[str, Any]:
        if not self.webhook_url:
            return {"skipped": True, "reason": "DingTalk webhook is not configured"}

        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
        }
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await client.post(self._signed_url(), json=payload)

        if response.status_code >= 400:
            raise RuntimeError(f"DingTalk webhook returned HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if isinstance(body, dict) and body.get("errcode") not in (None, 0):
            raise RuntimeError(f"DingTalk webhook failed: {body}")
        return {"skipped": False, "response": body}

    def _signed_url(self) -> str:
        if not self.secret:
            return self.webhook_url or ""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}".encode("utf-8")
        digest = hmac.new(self.secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(digest))
        sep = "&" if "?" in (self.webhook_url or "") else "?"
        return f"{self.webhook_url}{sep}timestamp={timestamp}&sign={sign}"

    @staticmethod
    def _status_label(status: str) -> str:
        return "成功" if status == "success" else "失败"

    @staticmethod
    def _truncate(value: str, limit: int = 1800) -> str:
        if len(value) <= limit:
            return value
        return value[:limit] + "\n..."
