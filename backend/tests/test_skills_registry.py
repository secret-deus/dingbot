"""项目内 Skill 注册表测试。"""
from pathlib import Path

import pytest

from src.skills.registry import SkillRegistry


@pytest.fixture
def skills_path() -> Path:
    repo = Path(__file__).resolve().parents[2]
    return repo / "config" / "skills.example.json"


def test_skill_full_allows_any(skills_path: Path):
    reg = SkillRegistry(config_path=str(skills_path))
    assert reg.is_tool_allowed("full", "k8s-get-pods")
    assert reg.is_tool_allowed("full", "ecs-list-instances")


def test_k8s_readonly_prefix(skills_path: Path):
    reg = SkillRegistry(config_path=str(skills_path))
    assert reg.is_tool_allowed("k8s_readonly", "k8s-get-pods")
    assert not reg.is_tool_allowed("k8s_readonly", "ecs-list-instances")


def test_filter_tool_names(skills_path: Path):
    reg = SkillRegistry(config_path=str(skills_path))
    names = ["k8s-get-pods", "k8s-delete-pod", "ecs-list-instances"]
    allowed = reg.filter_tool_names("k8s_readonly", names)
    assert "k8s-get-pods" in allowed
    assert "k8s-delete-pod" not in allowed
    assert "ecs-list-instances" not in allowed
