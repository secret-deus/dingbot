"""User, role and permission management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ....security.auth import CurrentUser, require_permission
from ....security.audit import get_audit_logger
from ....security.permissions import PERMISSIONS
from ....security.user_store import get_user_store
from ..standard import get_request_id, success_envelope

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=256)
    roles: list[str] = Field(default_factory=lambda: ["viewer"])
    enabled: bool = True


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    password: str | None = Field(default=None, min_length=6, max_length=256)
    roles: list[str] | None = None
    enabled: bool | None = None


@router.get("", summary="用户列表")
async def list_users(
    request: Request,
    _: CurrentUser = Depends(require_permission("users:read")),
):
    store = get_user_store()
    return success_envelope(
        request,
        {
            "users": store.list_users(),
            "roles": store.list_roles(),
            "permissions": PERMISSIONS,
        },
    )


@router.post("", summary="创建用户")
async def create_user(
    request: Request,
    payload: UserCreateRequest,
    actor: CurrentUser = Depends(require_permission("users:write")),
):
    try:
        user = get_user_store().create_user(
            username=payload.username,
            display_name=payload.display_name,
            password=payload.password,
            roles=payload.roles,
            enabled=payload.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    get_audit_logger().record(
        actor=actor.username,
        action="users.create",
        resource="user",
        resource_id=user["id"],
        result="success",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"username": user["username"], "roles": user["roles"]},
    )
    return success_envelope(request, {"user": user})


@router.patch("/{user_id}", summary="更新用户")
async def update_user(
    user_id: str,
    request: Request,
    payload: UserUpdateRequest,
    actor: CurrentUser = Depends(require_permission("users:write")),
):
    try:
        user = get_user_store().update_user(
            user_id,
            display_name=payload.display_name,
            password=payload.password,
            roles=payload.roles,
            enabled=payload.enabled,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    get_audit_logger().record(
        actor=actor.username,
        action="users.update",
        resource="user",
        resource_id=user_id,
        result="success",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={
            "display_name": payload.display_name,
            "roles": payload.roles,
            "enabled": payload.enabled,
            "password_changed": bool(payload.password),
        },
    )
    return success_envelope(request, {"user": user})


@router.delete("/{user_id}", summary="停用用户")
async def disable_user(
    user_id: str,
    request: Request,
    actor: CurrentUser = Depends(require_permission("users:write")),
):
    try:
        user = get_user_store().disable_user(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    get_audit_logger().record(
        actor=actor.username,
        action="users.disable",
        resource="user",
        resource_id=user_id,
        result="success",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"username": user["username"]},
    )
    return success_envelope(request, {"user": user})


@router.get("/roles", summary="角色与权限")
async def list_roles(
    request: Request,
    _: CurrentUser = Depends(require_permission("users:read")),
):
    return success_envelope(
        request,
        {
            "roles": get_user_store().list_roles(),
            "permissions": PERMISSIONS,
        },
    )
