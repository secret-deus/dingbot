"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ....security.audit import get_audit_logger
from ....security.auth import CurrentUser, get_auth_service, get_current_user
from ....security.user_store import get_user_store
from ..standard import get_request_id, success_envelope

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str = Field(default="admin", min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


@router.post("/login", summary="登录")
async def login(request: Request, payload: LoginRequest):
    user_store = get_user_store()
    user = user_store.authenticate(payload.username, payload.password)
    audit_logger = get_audit_logger()
    request_id = get_request_id(request)

    if not user:
        audit_logger.record(
            actor=payload.username,
            action="auth.login",
            resource="auth",
            result="failure",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token, expires_in = get_auth_service().create_token(user)
    audit_logger.record(
        actor=user["username"],
        action="auth.login",
        resource="auth",
        result="success",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_envelope(
        request,
        {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": user,
        },
    )


@router.get("/me", summary="当前用户")
async def me(request: Request, user: CurrentUser = Depends(get_current_user)):
    return success_envelope(request, {"user": user.to_public_dict()})


@router.post("/logout", summary="退出登录")
async def logout(request: Request, user: CurrentUser = Depends(get_current_user)):
    get_audit_logger().record(
        actor=user.username,
        action="auth.logout",
        resource="auth",
        result="success",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_envelope(request, {"message": "已退出登录"})
