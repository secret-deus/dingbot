"""Signed session token helpers and FastAPI auth dependencies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .permissions import has_permission
from .user_store import UserStore, get_user_store

bearer_scheme = HTTPBearer(auto_error=False)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def get_session_secret() -> str:
    env_secret = os.getenv("APP_SESSION_SECRET")
    if env_secret:
        return env_secret

    path = Path(os.getenv("APP_SESSION_SECRET_FILE", "config/security/session_secret.key"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return path.read_text(encoding="utf-8").strip()


@dataclass(frozen=True)
class CurrentUser:
    id: str
    username: str
    display_name: str
    roles: list[str]
    permissions: list[str]

    def can(self, permission: str) -> bool:
        return has_permission(self.permissions, permission)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "roles": self.roles,
            "permissions": self.permissions,
        }


class AuthService:
    def __init__(self, user_store: UserStore | None = None, secret: str | None = None):
        self.user_store = user_store or get_user_store()
        self.secret = secret or get_session_secret()
        self.expires_seconds = int(os.getenv("APP_SESSION_EXPIRES_SECONDS", "86400"))

    def create_token(self, user: dict[str, Any]) -> tuple[str, int]:
        now = int(time.time())
        payload = {
            "sub": user["id"],
            "username": user["username"],
            "iat": now,
            "exp": now + self.expires_seconds,
            "jti": uuid.uuid4().hex,
        }
        header = {"alg": "HS256", "typ": "JWT"}
        signing_input = ".".join(
            [
                _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
                _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
            ]
        )
        signature = hmac.new(
            self.secret.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{signing_input}.{_b64encode(signature)}", self.expires_seconds

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            header_part, payload_part, signature_part = token.split(".", 2)
        except ValueError as exc:
            raise ValueError("无效 token") from exc

        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            self.secret.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _b64decode(signature_part)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("token 签名无效")

        payload = json.loads(_b64decode(payload_part))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("token 已过期")
        return payload

    def current_user_from_token(self, token: str) -> CurrentUser:
        payload = self.decode_token(token)
        user = self.user_store.get_user_by_id(payload["sub"])
        if not user or not user.get("enabled", True):
            raise ValueError("用户不存在或已停用")
        return CurrentUser(
            id=user["id"],
            username=user["username"],
            display_name=user.get("display_name") or user["username"],
            roles=user.get("roles", []),
            permissions=user.get("permissions", []),
        )


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    return AuthService()


def _resolve_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    token = _resolve_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
        )
    try:
        user = get_auth_service().current_user_from_token(token)
        request.state.current_user = user
        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def require_permission(permission: str) -> Callable:
    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.can(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}",
            )
        return user

    return _dependency
