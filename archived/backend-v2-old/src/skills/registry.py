"""
项目内 Skill：按配置限制可调用的 MCP 工具名（非 IDE）。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from src.mcp.types import MCPTool


@dataclass(frozen=True)
class SkillDefinition:
    id: str
    display_name: str
    description: str = ""
    allowed_tool_names: tuple[str, ...] = ()
    allowed_prefixes: tuple[str, ...] = ()


class SkillRegistry:
    """加载 config/skills.json，解析默认 skill 与过滤规则。"""

    def __init__(self, config_path: Optional[str] = None):
        backend_root = Path(__file__).resolve().parents[2]
        repo_root = backend_root.parent
        env_path = os.getenv("SKILLS_CONFIG_PATH", "").strip()
        self._path = Path(config_path or env_path or (repo_root / "config" / "skills.json"))
        self._skills: Dict[str, SkillDefinition] = {}
        self.default_skill_id: str = "full"
        self._load()

    def _load(self) -> None:
        self._skills.clear()
        if not self._path.exists():
            logger.warning("Skill 配置文件不存在: %s，仅提供 full", self._path)
            self._skills["full"] = SkillDefinition(
                id="full",
                display_name="全量工具",
                description="未配置 skills.json",
            )
            self.default_skill_id = "full"
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        self.default_skill_id = data.get("default_skill_id", "full")
        for raw in data.get("skills", []):
            sid = raw.get("id")
            if not sid:
                continue
            names = raw.get("allowed_tool_names") or []
            prefs = raw.get("allowed_prefixes") or []
            self._skills[sid] = SkillDefinition(
                id=sid,
                display_name=raw.get("display_name", sid),
                description=raw.get("description", ""),
                allowed_tool_names=tuple(names),
                allowed_prefixes=tuple(prefs),
            )
        if "full" not in self._skills:
            self._skills["full"] = SkillDefinition(id="full", display_name="全量工具")

    def reload(self) -> None:
        self._load()

    def get(self, skill_id: Optional[str]) -> SkillDefinition:
        sid = skill_id or self.default_skill_id
        if sid in self._skills:
            return self._skills[sid]
        logger.warning("未知 skill_id=%s，回退到 default=%s", sid, self.default_skill_id)
        return self._skills.get(self.default_skill_id, self._skills["full"])

    def list_public(self) -> List[Dict[str, Any]]:
        """供 API 返回（不含敏感字段）。"""
        return [
            {
                "id": s.id,
                "display_name": s.display_name,
                "description": s.description,
            }
            for s in self._skills.values()
        ]

    def is_tool_allowed(self, skill_id: Optional[str], tool_name: str) -> bool:
        s = self.get(skill_id)
        if not s.allowed_tool_names and not s.allowed_prefixes:
            return True
        if tool_name in s.allowed_tool_names:
            return True
        for p in s.allowed_prefixes:
            if tool_name.startswith(p):
                return True
        return False

    def filter_tool_names(self, skill_id: Optional[str], all_names: List[str]) -> Set[str]:
        return {n for n in all_names if self.is_tool_allowed(skill_id, n)}

    def filter_mcptools(self, skill_id: Optional[str], tools: List[MCPTool]) -> List[MCPTool]:
        return [t for t in tools if self.is_tool_allowed(skill_id, t.name)]


_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
