from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.mcp.builtin import BuiltinToolRegistry
from app.mcp.tools.ecs import ECSClient


def test_builtin_registry_exposes_ecs_monitor_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "mcp_config.json"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("ECS_MCP_ENABLED", "true")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "local-access-key-id")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "local-access-key-secret")
    monkeypatch.setenv("ALIBABA_CLOUD_REGION_ID", "cn-shanghai")
    monkeypatch.delenv("KUBECONFIG_PATH", raising=False)

    registry = BuiltinToolRegistry()
    tools = {tool["name"]: tool for tool in registry.list_tools()}

    assert tools["ecs-describe-instance-monitor-data"]["available"] is True
    schema = tools["ecs-describe-instance-monitor-data"]["inputSchema"]
    assert schema["required"] == ["instance_id"]
    assert "period" in schema["properties"]
    assert "relative_range" in schema["properties"]


@pytest.mark.asyncio
async def test_ecs_describe_instance_monitor_data_returns_summary_and_samples():
    client = ECSClient("access-key-id", "access-key-secret", "cn-shanghai")
    fake_api = _FakeECSApi()
    client._client = fake_api

    result = await client.ecs_describe_instance_monitor_data(
        instance_id="i-test123",
        start_time="2026-05-18T00:00:00Z",
        end_time="2026-05-18T00:20:00Z",
        period=600,
        metrics=["CPU", "InternetRX"],
    )

    assert fake_api.request.instance_id == "i-test123"
    assert fake_api.request.start_time == "2026-05-18T00:00:00Z"
    assert fake_api.request.end_time == "2026-05-18T00:20:00Z"
    assert fake_api.request.period == 600
    assert result["instance_id"] == "i-test123"
    assert result["region_id"] == "cn-shanghai"
    assert result["period"] == 600
    assert result["summary"] == {
        "CPU": {
            "count": 2,
            "min": 12.5,
            "max": 37.5,
            "avg": 25.0,
            "latest": 37.5,
            "unit": "percent",
        },
        "InternetRX": {
            "count": 2,
            "min": 1024,
            "max": 2048,
            "avg": 1536.0,
            "latest": 2048,
            "unit": "Kbit",
        },
    }
    assert result["samples"] == [
        {"timestamp": "2026-05-18T00:00:00Z", "metrics": {"CPU": 12.5, "InternetRX": 1024}},
        {"timestamp": "2026-05-18T00:10:00Z", "metrics": {"CPU": 37.5, "InternetRX": 2048}},
    ]


@pytest.mark.asyncio
async def test_ecs_describe_instance_monitor_data_requires_instance_id():
    client = ECSClient("access-key-id", "access-key-secret", "cn-shanghai")

    result = await client.ecs_describe_instance_monitor_data()

    assert result == {"error": "instance_id 参数必填"}


class _FakeECSApi:
    def __init__(self) -> None:
        self.request = None

    def describe_instance_monitor_data(self, request):
        self.request = request
        points = [
            SimpleNamespace(
                instance_id="i-test123",
                time_stamp="2026-05-18T00:00:00Z",
                cpu=12.5,
                internet_rx=1024,
            ),
            SimpleNamespace(
                instance_id="i-test123",
                time_stamp="2026-05-18T00:10:00Z",
                cpu=37.5,
                internet_rx=2048,
            ),
        ]
        return SimpleNamespace(
            body=SimpleNamespace(
                monitor_data=SimpleNamespace(instance_monitor_data=points),
            ),
        )
