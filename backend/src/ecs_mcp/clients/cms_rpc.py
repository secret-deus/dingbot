"""
CloudMonitor (CMS) RPC 签名与调用

默认使用公共域名 https://metrics.aliyuncs.com
可根据需要切换区域域名 https://metrics.<region>.aliyuncs.com
API 版本：2019-01-01（QueryMetricList / GetMetricStatistics 等）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any
from urllib.parse import quote

import httpx


def _percent_encode(s: str) -> str:
    return quote(s, safe="-_.~")


def _iso8601_utc() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_cms_time(dt: datetime) -> str:
    # CMS常用 yyyy-MM-dd HH:mm:ss（按UTC输出）
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def sign_parameters(params: Dict[str, Any], access_key_id: str, access_key_secret: str, *, method: str = "GET") -> str:
    merged = {
        "Format": "JSON",
        "Version": "2019-01-01",
        "AccessKeyId": access_key_id,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": _iso8601_utc(),
        "SignatureVersion": "1.0",
        "SignatureNonce": _iso8601_utc(),  # 简化：用时间戳作为随机串
    }
    merged.update({k: v for k, v in params.items() if v is not None})

    sorted_items = sorted(merged.items(), key=lambda x: x[0])
    canonicalized = "&".join(f"{_percent_encode(str(k))}={_percent_encode(str(v))}" for k, v in sorted_items)
    string_to_sign = f"{method}&%2F&{_percent_encode(canonicalized)}"

    key = (access_key_secret + "&").encode("utf-8")
    message = string_to_sign.encode("utf-8")
    signature = base64.b64encode(hmac.new(key, message, hashlib.sha1).digest()).decode("utf-8")
    return f"Signature={_percent_encode(signature)}&{canonicalized}"


async def rpc_get(params: Dict[str, Any], access_key_id: str, access_key_secret: str, *, endpoint: str = "https://metrics.aliyuncs.com") -> Dict[str, Any]:
    query = sign_parameters(params, access_key_id, access_key_secret, method="GET")
    url = f"{endpoint}/?{query}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


__all__ = ["rpc_get", "_format_cms_time"]
