"""FastAPI 依赖注入"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings, get_settings
from app.core.security import Role, decode_access_token, has_permission
from app.db.session import get_db

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未提供认证凭据")
    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效或过期的令牌")
    return {"username": payload["sub"], "role": payload["role"]}


def require_role(min_role: Role):
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        user_role = Role(user["role"])
        if not has_permission(user_role, min_role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return user

    return _check


# 便捷别名
require_admin = require_role(Role.ADMIN)
require_operator = require_role(Role.OPERATOR)


# 应用全局状态（由 main.py 在启动时注入）
_app_state: dict = {}


def _get_app_state() -> dict:
    return _app_state
