"""认证 API - 登录、注册、令牌刷新"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.core.security import (
    Role,
    create_access_token,
    decode_access_token,
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


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"]}
