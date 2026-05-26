"""认证 API - 登录、注册、令牌刷新"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.core.security import (
    Role,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: Role = Role.VIEWER
    display_name: str = ""


class UpdateUserRequest(BaseModel):
    role: Optional[Role] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_username(req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号已禁用")
    token = create_access_token(user.username, user.role.value)
    await db.commit()
    return LoginResponse(access_token=token, username=user.username, role=user.role.value)


@router.post("/register", status_code=201)
async def register(
    req: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    repo = UserRepository(db)
    existing = await repo.get_by_username(req.username)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    hashed = hash_password(req.password)
    user = await repo.create_user(req.username, hashed, req.role)
    user.display_name = req.display_name
    await db.commit()
    return {"id": user.id, "username": user.username, "role": user.role.value}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    repo = UserRepository(db)
    users = await repo.list_all(limit=limit, offset=offset)
    await db.commit()
    return [_user_response(user) for user in users]


@router.patch("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    req: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if username == admin["username"]:
        if req.role is not None and req.role != user.role:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能修改自己的管理员角色")
        if req.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能停用当前登录账号")

    if req.role is not None:
        user.role = req.role
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.is_active is not None:
        user.is_active = req.is_active

    await db.commit()
    return _user_response(user)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"]}


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=str(user.created_at),
        updated_at=str(user.updated_at),
    )
