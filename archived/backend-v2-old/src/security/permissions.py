"""Permission constants and built-in role definitions."""

from __future__ import annotations

ALL_PERMISSIONS = "*"

PERMISSIONS = {
    "ops:read": "查看运维指挥台",
    "chat:read": "查看智能对话",
    "chat:send": "发送智能对话",
    "llm:read": "查看 LLM 配置",
    "llm:write": "修改 LLM 配置",
    "mcp:read": "查看 MCP 配置",
    "mcp:write": "修改 MCP 配置",
    "resources:read": "查看资源指标",
    "resources:write": "执行资源指标更新",
    "inspection:run": "执行运维巡检",
    "alerts:read": "查看资源告警",
    "alerts:write": "处理资源告警",
    "scheduler:read": "查看任务调度",
    "scheduler:write": "修改任务调度",
    "scheduler:run": "执行任务调度",
    "audit:read": "查看操作日志",
    "users:read": "查看用户与角色",
    "users:write": "管理用户与角色",
    "debug:read": "查看调试信息",
    "debug:write": "执行调试动作",
}

BUILT_IN_ROLES = [
    {
        "id": "admin",
        "name": "系统管理员",
        "description": "拥有系统全部配置、用户和审计权限。",
        "permissions": [ALL_PERMISSIONS],
        "built_in": True,
    },
    {
        "id": "operator",
        "name": "运维工程师",
        "description": "可使用对话、MCP、调度和指挥台，不能管理用户。",
        "permissions": [
            "ops:read",
            "chat:read",
            "chat:send",
            "mcp:read",
            "mcp:write",
            "resources:read",
            "resources:write",
            "inspection:run",
            "alerts:read",
            "alerts:write",
            "scheduler:read",
            "scheduler:write",
            "scheduler:run",
            "audit:read",
        ],
        "built_in": True,
    },
    {
        "id": "viewer",
        "name": "只读观察员",
        "description": "只读访问指挥台、对话历史、MCP 和调度信息。",
        "permissions": [
            "ops:read",
            "chat:read",
            "mcp:read",
            "resources:read",
            "alerts:read",
            "scheduler:read",
            "audit:read",
        ],
        "built_in": True,
    },
]


def expand_permissions(role_ids: list[str], roles: list[dict]) -> list[str]:
    """Expand role IDs into a sorted permission list."""
    permissions: set[str] = set()
    by_id = {role["id"]: role for role in roles}
    for role_id in role_ids:
        role = by_id.get(role_id)
        if not role:
            continue
        role_permissions = role.get("permissions", [])
        if ALL_PERMISSIONS in role_permissions:
            return [ALL_PERMISSIONS]
        permissions.update(role_permissions)
    return sorted(permissions)


def has_permission(user_permissions: list[str], permission: str) -> bool:
    return ALL_PERMISSIONS in user_permissions or permission in user_permissions
