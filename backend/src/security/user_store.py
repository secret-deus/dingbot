"""Local JSON-backed user and role store."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger

from .permissions import BUILT_IN_ROLES, expand_permissions

PBKDF2_ITERATIONS = 260_000
USER_STORE_LOCK = threading.RLock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_users_path() -> Path:
    return Path(os.getenv("IAM_USERS_PATH", "config/security/users.json"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


class UserStore:
    """Small local store for single-node deployments and development."""

    def __init__(self, path: Path | None = None):
        self.path = path or get_users_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        if self.path.exists():
            self._merge_builtin_roles()
            return

        admin_password = (
            os.getenv("APP_ADMIN_PASSWORD")
            or os.getenv("VITE_ACCESS_PASSWORD")
            or os.getenv("ACCESS_PASSWORD")
        )
        if not admin_password:
            admin_password = secrets.token_urlsafe(18)
            bootstrap_path = self.path.parent / "bootstrap_admin_password.txt"
            bootstrap_path.write_text(admin_password, encoding="utf-8")
            try:
                bootstrap_path.chmod(0o600)
            except OSError:
                pass
            logger.warning(
                "未配置 APP_ADMIN_PASSWORD，已生成一次性初始管理员密码文件: {}",
                bootstrap_path,
            )
        now = utc_now_iso()
        data = {
            "version": "1.0",
            "roles": deepcopy(BUILT_IN_ROLES),
            "users": [
                {
                    "id": "usr_admin",
                    "username": "admin",
                    "display_name": "管理员",
                    "password_hash": hash_password(admin_password),
                    "roles": ["admin"],
                    "enabled": True,
                    "created_at": now,
                    "updated_at": now,
                    "last_login_at": None,
                }
            ],
        }
        self._write(data)
        logger.info("已初始化本地 IAM 用户存储: {}", self.path)

    def _read(self) -> dict[str, Any]:
        with USER_STORE_LOCK:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def _write(self, data: dict[str, Any]) -> None:
        with USER_STORE_LOCK:
            tmp_path = self.path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
            try:
                tmp_path.chmod(0o600)
            except OSError:
                pass
            tmp_path.replace(self.path)
            try:
                self.path.chmod(0o600)
            except OSError:
                pass

    def _merge_builtin_roles(self) -> None:
        with USER_STORE_LOCK:
            data = self._read()
            roles = data.setdefault("roles", [])
            existing = {role.get("id"): role for role in roles}
            changed = False
            for built_in_role in BUILT_IN_ROLES:
                role_id = built_in_role["id"]
                if role_id not in existing:
                    roles.append(deepcopy(built_in_role))
                    changed = True
                    continue
                current_role = existing[role_id]
                if current_role.get("built_in", True):
                    latest_role = deepcopy(built_in_role)
                    if current_role != latest_role:
                        current_role.clear()
                        current_role.update(latest_role)
                        changed = True
            if changed:
                self._write(data)

    def _public_user(self, user: dict[str, Any], roles: list[dict[str, Any]]) -> dict[str, Any]:
        public = {
            key: value
            for key, value in user.items()
            if key not in {"password_hash"}
        }
        public["permissions"] = expand_permissions(public.get("roles", []), roles)
        return public

    def list_roles(self) -> list[dict[str, Any]]:
        return deepcopy(self._read().get("roles", []))

    def list_users(self) -> list[dict[str, Any]]:
        data = self._read()
        roles = data.get("roles", [])
        return [self._public_user(user, roles) for user in data.get("users", [])]

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        data = self._read()
        roles = data.get("roles", [])
        for user in data.get("users", []):
            if user.get("username") == username:
                return self._public_user(user, roles) | {"password_hash": user.get("password_hash")}
        return None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        data = self._read()
        roles = data.get("roles", [])
        for user in data.get("users", []):
            if user.get("id") == user_id:
                return self._public_user(user, roles) | {"password_hash": user.get("password_hash")}
        return None

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_username(username)
        if not user or not user.get("enabled", True):
            return None
        if not verify_password(password, user.get("password_hash", "")):
            return None
        self.touch_last_login(user["id"])
        user = self.get_user_by_id(user["id"])
        if not user:
            return None
        user.pop("password_hash", None)
        return user

    def touch_last_login(self, user_id: str) -> None:
        with USER_STORE_LOCK:
            data = self._read()
            now = utc_now_iso()
            for user in data.get("users", []):
                if user.get("id") == user_id:
                    user["last_login_at"] = now
                    user["updated_at"] = now
                    self._write(data)
                    return

    def create_user(
        self,
        *,
        username: str,
        display_name: str,
        password: str,
        roles: list[str],
        enabled: bool = True,
    ) -> dict[str, Any]:
        with USER_STORE_LOCK:
            data = self._read()
            normalized_username = username.strip()
            if not normalized_username:
                raise ValueError("用户名不能为空")
            if any(user.get("username") == normalized_username for user in data.get("users", [])):
                raise ValueError("用户名已存在")
            self._validate_roles(roles, data.get("roles", []))

            now = utc_now_iso()
            user = {
                "id": f"usr_{uuid.uuid4().hex[:12]}",
                "username": normalized_username,
                "display_name": display_name.strip() or normalized_username,
                "password_hash": hash_password(password),
                "roles": roles,
                "enabled": enabled,
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
            }
            data.setdefault("users", []).append(user)
            self._write(data)
            return self._public_user(user, data.get("roles", []))

    def update_user(
        self,
        user_id: str,
        *,
        display_name: str | None = None,
        password: str | None = None,
        roles: list[str] | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        with USER_STORE_LOCK:
            data = self._read()
            if roles is not None:
                self._validate_roles(roles, data.get("roles", []))

            for user in data.get("users", []):
                if user.get("id") != user_id:
                    continue
                if display_name is not None:
                    user["display_name"] = display_name.strip() or user["username"]
                if password:
                    user["password_hash"] = hash_password(password)
                if roles is not None:
                    user["roles"] = roles
                if enabled is not None:
                    user["enabled"] = enabled
                user["updated_at"] = utc_now_iso()
                self._write(data)
                return self._public_user(user, data.get("roles", []))
            raise KeyError("用户不存在")

    def disable_user(self, user_id: str) -> dict[str, Any]:
        if user_id == "usr_admin":
            raise ValueError("默认管理员不能停用")
        return self.update_user(user_id, enabled=False)

    @staticmethod
    def _validate_roles(role_ids: list[str], roles: list[dict[str, Any]]) -> None:
        available = {role.get("id") for role in roles}
        missing = sorted(set(role_ids) - available)
        if missing:
            raise ValueError(f"角色不存在: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_user_store() -> UserStore:
    return UserStore()
