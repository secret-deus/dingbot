from __future__ import annotations

import pytest

from app.mcp.tools.aliyun import AliyunReadOnlyRegistry, AliyunRuntimeConfig


def test_aliyun_registry_exposes_exactly_13_readonly_tools():
    registry = AliyunReadOnlyRegistry(_config(configured=True), _FakeAliyunClients())
    tools = registry.list_tools()

    assert [tool["name"] for tool in tools] == [
        "aliyun-ecs-list-instances",
        "aliyun-ecs-describe-instance",
        "aliyun-ecs-list-security-groups",
        "aliyun-ecs-describe-security-group-rules",
        "aliyun-cms-get-ecs-metrics",
        "aliyun-cms-get-alerts",
        "aliyun-cms-get-event-history",
        "aliyun-sls-list-logstores",
        "aliyun-sls-query-logs",
        "aliyun-sls-query-error-summary",
        "aliyun-lb-list-instances",
        "aliyun-lb-describe-health",
        "aliyun-swas-list-instances",
    ]
    assert all(tool["dangerLevel"] == "read" for tool in tools)
    assert all(tool["executionPolicy"] == "executable" for tool in tools)
    assert all(tool["available"] is True for tool in tools)


def test_aliyun_registry_marks_tools_unavailable_when_credentials_missing():
    registry = AliyunReadOnlyRegistry(_config(configured=False), _FakeAliyunClients())
    tools = registry.list_tools()

    assert len(tools) == 13
    assert all(tool["available"] is False for tool in tools)
    assert tools[0]["unavailableReason"] == "未配置 Aliyun 只读 AccessKey"


@pytest.mark.asyncio
async def test_aliyun_region_guard_rejects_disallowed_region_before_client_call():
    clients = _FakeAliyunClients()
    registry = AliyunReadOnlyRegistry(_config(configured=True), clients)

    result = await registry.aliyun_ecs_list_instances(region_id="cn-beijing")

    assert result["error"] == "aliyun_region_not_allowed"
    assert result["region_id"] == "cn-beijing"
    assert clients.calls == []


@pytest.mark.asyncio
async def test_aliyun_list_instances_applies_required_tags_and_allowlist():
    clients = _FakeAliyunClients()
    registry = AliyunReadOnlyRegistry(_config(configured=True), clients)

    result = await registry.aliyun_ecs_list_instances(region_id="cn-hangzhou")

    assert result["summary"] == {"total": 3, "returned": 1, "filtered": 2}
    assert [item["instance_id"] for item in result["items"]] == ["i-prod"]
    assert result["filters"]["required_tags"] == {"Environment": ["prod"]}


@pytest.mark.asyncio
async def test_aliyun_sls_query_logs_resolves_mapping_and_bounds_rows():
    clients = _FakeAliyunClients()
    registry = AliyunReadOnlyRegistry(_config(configured=True), clients)

    result = await registry.aliyun_sls_query_logs(service="ding-robot", env="prod", limit=200)

    assert result["mapping"] == {
        "service": "ding-robot",
        "env": "prod",
        "region_id": "cn-hangzhou",
        "project": "prod-log-project",
        "logstore": "app-log",
    }
    assert result["summary"]["returned"] == 50
    assert len(result["logs"]) == 50
    assert clients.calls[-1][0] == "query_logs"
    assert clients.calls[-1][1]["project"] == "prod-log-project"


@pytest.mark.asyncio
async def test_aliyun_sls_missing_mapping_returns_structured_error():
    registry = AliyunReadOnlyRegistry(_config(configured=True), _FakeAliyunClients())

    result = await registry.aliyun_sls_query_logs(service="unknown", env="prod")

    assert result["error"] == "aliyun_sls_mapping_not_found"
    assert result["service"] == "unknown"
    assert result["env"] == "prod"


@pytest.mark.asyncio
async def test_aliyun_sls_list_logstores_requires_enabled_before_exposing_mappings():
    registry = AliyunReadOnlyRegistry(
        AliyunRuntimeConfig(
            enabled=False,
            access_key_id="ak",
            access_key_secret="secret",
            default_region_id="cn-hangzhou",
            allowed_regions=["cn-hangzhou"],
            sls_mappings=[
                {
                    "service": "ding-robot",
                    "env": "prod",
                    "region_id": "cn-hangzhou",
                    "project": "prod-log-project",
                    "logstore": "app-log",
                }
            ],
        ),
        _FakeAliyunClients(),
    )

    result = await registry.aliyun_sls_list_logstores()

    assert result["error"] == "aliyun_not_enabled"


@pytest.mark.asyncio
async def test_aliyun_metrics_are_summarized_and_samples_bounded():
    registry = AliyunReadOnlyRegistry(_config(configured=True), _FakeAliyunClients())

    result = await registry.aliyun_cms_get_ecs_metrics(instance_id="i-prod")

    assert result["summary"]["CPU"] == {"max": 90.0, "avg": 50.0, "latest": 90.0}
    assert result["summary"]["MemoryUtilization"] == {"max": 80.0, "avg": 55.0, "latest": 80.0}
    assert len(result["samples"]) == 3


@pytest.mark.asyncio
async def test_aliyun_alerts_are_not_filtered_by_resource_tags():
    registry = AliyunReadOnlyRegistry(_config(configured=True), _FakeAliyunClients())

    result = await registry.aliyun_cms_get_alerts(region_id="cn-hangzhou")

    assert result["summary"] == {"total": 1, "returned": 1, "filtered": 0}
    assert result["items"] == [{"id": "alert-1", "name": "CPU high"}]


@pytest.mark.asyncio
async def test_aliyun_load_balancer_health_summarizes_unhealthy_backends():
    registry = AliyunReadOnlyRegistry(_config(configured=True), _FakeAliyunClients())

    result = await registry.aliyun_lb_describe_health(
        region_id="cn-hangzhou",
        load_balancer_id="lb-1",
        type="slb",
    )

    assert result["summary"] == {"total": 2, "returned": 2, "unhealthy": 1}
    assert [item["status"] for item in result["items"]] == ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_aliyun_swas_list_instances_uses_readonly_list_result():
    clients = _FakeAliyunClients()
    registry = AliyunReadOnlyRegistry(_config(configured=True), clients)

    result = await registry.aliyun_swas_list_instances(region_id="cn-hangzhou", page_size=20)

    assert result["summary"] == {"total": 1, "returned": 1, "filtered": 0}
    assert result["items"] == [
        {
            "instance_id": "swas-1",
            "name": "lightweight-app",
            "status": "Running",
            "region_id": "cn-hangzhou",
            "tags": {"Environment": "prod"},
        }
    ]
    assert clients.calls[-1][0] == "list_swas_instances"
    assert clients.calls[-1][1]["region_id"] == "cn-hangzhou"
    assert clients.calls[-1][1]["page_size"] == 20


def _config(configured: bool) -> AliyunRuntimeConfig:
    return AliyunRuntimeConfig(
        enabled=True,
        access_key_id="ak" if configured else None,
        access_key_secret="secret" if configured else None,
        default_region_id="cn-hangzhou",
        allowed_regions=["cn-hangzhou"],
        required_tags={"Environment": ["prod"]},
        allowed_instance_ids=["i-prod", "i-missing-tag", "swas-1"],
        sls_mappings=[
            {
                "service": "ding-robot",
                "env": "prod",
                "region_id": "cn-hangzhou",
                "project": "prod-log-project",
                "logstore": "app-log",
                "default_query": "level: ERROR",
            }
        ],
    )


class _FakeAliyunClients:
    def __init__(self):
        self.calls = []

    async def list_ecs_instances(self, **kwargs):
        self.calls.append(("list_ecs_instances", kwargs))
        return [
            {
                "instance_id": "i-prod",
                "instance_name": "prod-api-1",
                "status": "Running",
                "region_id": kwargs["region_id"],
                "tags": {"Environment": "prod"},
            },
            {
                "instance_id": "i-dev",
                "instance_name": "dev-api-1",
                "status": "Running",
                "region_id": kwargs["region_id"],
                "tags": {"Environment": "dev"},
            },
            {
                "instance_id": "i-missing-tag",
                "instance_name": "unknown",
                "status": "Stopped",
                "region_id": kwargs["region_id"],
                "tags": {},
            },
        ]

    async def describe_ecs_instance(self, **kwargs):
        self.calls.append(("describe_ecs_instance", kwargs))
        return {"instance_id": kwargs["instance_id"], "tags": {"Environment": "prod"}}

    async def list_security_groups(self, **kwargs):
        self.calls.append(("list_security_groups", kwargs))
        return [{"security_group_id": "sg-1", "tags": {"Environment": "prod"}}]

    async def describe_security_group_rules(self, **kwargs):
        self.calls.append(("describe_security_group_rules", kwargs))
        return [{"rule_id": "r-1", "direction": kwargs.get("direction") or "ingress"}]

    async def get_ecs_metrics(self, **kwargs):
        self.calls.append(("get_ecs_metrics", kwargs))
        return [
            {"timestamp": "2026-05-22T00:00:00Z", "metrics": {"CPU": 10, "MemoryUtilization": 20}},
            {"timestamp": "2026-05-22T00:01:00Z", "metrics": {"CPU": 50, "MemoryUtilization": 65}},
            {"timestamp": "2026-05-22T00:02:00Z", "metrics": {"CPU": 90, "MemoryUtilization": 80}},
        ]

    async def get_alerts(self, **kwargs):
        self.calls.append(("get_alerts", kwargs))
        return [{"id": "alert-1", "name": "CPU high"}]

    async def get_event_history(self, **kwargs):
        self.calls.append(("get_event_history", kwargs))
        return [{"id": "event-1", "name": "Instance restart"}]

    async def list_logstores(self, **kwargs):
        self.calls.append(("list_logstores", kwargs))
        return [{"project": kwargs["project"], "logstore": kwargs["logstore"]}]

    async def query_logs(self, **kwargs):
        self.calls.append(("query_logs", kwargs))
        return [{"time": i, "message": f"error {i}"} for i in range(80)]

    async def list_load_balancers(self, **kwargs):
        self.calls.append(("list_load_balancers", kwargs))
        return [{"load_balancer_id": "lb-1", "tags": {"Environment": "prod"}}]

    async def describe_load_balancer_health(self, **kwargs):
        self.calls.append(("describe_load_balancer_health", kwargs))
        return [
            {"listener": "80", "backend": "i-prod", "status": "healthy"},
            {"listener": "80", "backend": "i-dev", "status": "unhealthy"},
        ]

    async def list_swas_instances(self, **kwargs):
        self.calls.append(("list_swas_instances", kwargs))
        return [
            {
                "instance_id": "swas-1",
                "name": "lightweight-app",
                "status": "Running",
                "region_id": kwargs["region_id"],
                "tags": {"Environment": "prod"},
            }
        ]
