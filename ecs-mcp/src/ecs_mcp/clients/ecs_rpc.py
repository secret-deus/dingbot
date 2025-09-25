"""
阿里云 RPC 协议签名与调用（不依赖 SDK 凭证链）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import httpx
from urllib.parse import quote


def _percent_encode(s: str) -> str:
    return quote(s, safe='-_.~')


def _iso8601_utc() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sign_parameters(params: Dict[str, Any], access_key_id: str, access_key_secret: str, method: str = 'GET') -> str:
    """返回带签名的查询字符串"""
    # 1. 添加公共参数
    merged = {
        'Format': 'JSON',
        'Version': '2014-05-26',
        'AccessKeyId': access_key_id,
        'SignatureMethod': 'HMAC-SHA1',
        'Timestamp': _iso8601_utc(),
        'SignatureVersion': '1.0',
        'SignatureNonce': str(uuid.uuid4()),
    }
    merged.update({k: v for k, v in params.items() if v is not None})

    # 2. 参数排序与编码
    sorted_items = sorted(merged.items(), key=lambda x: x[0])
    canonicalized = '&'.join(f"{_percent_encode(str(k))}={_percent_encode(str(v))}" for k, v in sorted_items)

    # 3. 构造签名字符串
    string_to_sign = f"{method}&%2F&{_percent_encode(canonicalized)}"

    # 4. 计算签名
    key = (access_key_secret + "&").encode('utf-8')
    message = string_to_sign.encode('utf-8')
    signature = base64.b64encode(hmac.new(key, message, hashlib.sha1).digest()).decode('utf-8')

    # 5. 组合最终查询
    signed_query = f"Signature={_percent_encode(signature)}&{canonicalized}"
    return signed_query


async def rpc_get(params: Dict[str, Any], access_key_id: str, access_key_secret: str, endpoint: str = 'https://ecs.aliyuncs.com') -> Dict[str, Any]:
    query = sign_parameters(params, access_key_id, access_key_secret, method='GET')
    url = f"{endpoint}/?{query}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()






