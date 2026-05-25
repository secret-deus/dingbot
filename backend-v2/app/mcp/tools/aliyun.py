"""Read-only Alibaba Cloud adapter tools exposed through the local MCP registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings
from app.mcp.tools.aliyun_clients import AliyunSDKClientFacade

ALIYUN_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "aliyun-ecs-list-instances",
        "title": "查询 ECS 实例列表",
        "description": "按地域、状态、名称和标签查询 ECS 实例列表",
        "tags": ["aliyun", "ecs", "instance", "实例", "主机", "云服务器"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "status": {"type": "string", "description": "实例状态"},
            "name": {"type": "string", "description": "实例名称关键词"},
            "tag_filters": {"type": "object", "description": "额外标签过滤"},
            "page_size": {"type": "integer", "description": "最大返回数量，默认 50"},
        },
        "required": [],
    },
    {
        "name": "aliyun-ecs-describe-instance",
        "title": "查询 ECS 实例详情",
        "description": "查询单台 ECS 实例详情",
        "tags": ["aliyun", "ecs", "describe", "实例", "详情"],
        "schema": {
            "instance_id": {"type": "string", "description": "ECS 实例 ID"},
            "region_id": {"type": "string", "description": "地域 ID"},
        },
        "required": ["instance_id"],
    },
    {
        "name": "aliyun-ecs-list-security-groups",
        "title": "查询 ECS 安全组",
        "description": "查询 ECS 安全组列表",
        "tags": ["aliyun", "ecs", "security group", "安全组", "网络"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "vpc_id": {"type": "string", "description": "VPC ID"},
            "instance_id": {"type": "string", "description": "ECS 实例 ID"},
        },
        "required": [],
    },
    {
        "name": "aliyun-ecs-describe-security-group-rules",
        "title": "查询 ECS 安全组规则",
        "description": "查询安全组入方向或出方向规则",
        "tags": ["aliyun", "ecs", "security group", "rule", "安全组规则"],
        "schema": {
            "security_group_id": {"type": "string", "description": "安全组 ID"},
            "region_id": {"type": "string", "description": "地域 ID"},
            "direction": {"type": "string", "description": "ingress 或 egress"},
        },
        "required": ["security_group_id"],
    },
    {
        "name": "aliyun-cms-get-ecs-metrics",
        "title": "查询 ECS 监控指标",
        "description": "查询 ECS CPU、内存、磁盘、网络等监控指标",
        "tags": ["aliyun", "cms", "cloudmonitor", "metrics", "监控", "指标", "cpu"],
        "schema": {
            "instance_id": {"type": "string", "description": "ECS 实例 ID"},
            "region_id": {"type": "string", "description": "地域 ID"},
            "metrics": {"type": "array", "items": {"type": "string"}, "description": "指标名"},
            "relative_range": {"type": "string", "description": "相对时间范围，默认 1h"},
            "period": {"type": "integer", "description": "采样周期"},
        },
        "required": ["instance_id"],
    },
    {
        "name": "aliyun-cms-get-alerts",
        "title": "查询 CloudMonitor 告警",
        "description": "查询 CloudMonitor 告警状态",
        "tags": ["aliyun", "cms", "alert", "告警", "报警"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "resource_id": {"type": "string", "description": "资源 ID"},
            "state": {"type": "string", "description": "告警状态"},
            "relative_range": {"type": "string", "description": "相对时间范围"},
        },
        "required": [],
    },
    {
        "name": "aliyun-cms-get-event-history",
        "title": "查询 CloudMonitor 事件",
        "description": "查询 CloudMonitor 事件历史",
        "tags": ["aliyun", "cms", "event", "事件", "云监控"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "resource_id": {"type": "string", "description": "资源 ID"},
            "relative_range": {"type": "string", "description": "相对时间范围"},
            "event_type": {"type": "string", "description": "事件类型"},
        },
        "required": [],
    },
    {
        "name": "aliyun-sls-list-logstores",
        "title": "查询 SLS Logstore 映射",
        "description": "列出已配置服务对应的 SLS project/logstore",
        "tags": ["aliyun", "sls", "logstore", "日志", "服务日志"],
        "schema": {
            "service": {"type": "string", "description": "服务名"},
            "env": {"type": "string", "description": "环境"},
            "region_id": {"type": "string", "description": "地域 ID"},
        },
        "required": [],
    },
    {
        "name": "aliyun-sls-query-logs",
        "title": "查询 SLS 日志",
        "description": "按服务映射查询 SLS 日志",
        "tags": ["aliyun", "sls", "logs", "日志", "错误日志", "exception"],
        "schema": {
            "service": {"type": "string", "description": "服务名"},
            "env": {"type": "string", "description": "环境"},
            "query": {"type": "string", "description": "查询语句"},
            "relative_range": {"type": "string", "description": "相对时间范围"},
            "limit": {"type": "integer", "description": "最大行数，默认 50"},
        },
        "required": [],
    },
    {
        "name": "aliyun-sls-query-error-summary",
        "title": "汇总 SLS 错误日志",
        "description": "按服务映射查询并汇总错误日志",
        "tags": ["aliyun", "sls", "error", "summary", "错误", "异常"],
        "schema": {
            "service": {"type": "string", "description": "服务名"},
            "env": {"type": "string", "description": "环境"},
            "relative_range": {"type": "string", "description": "相对时间范围"},
        },
        "required": ["service"],
    },
    {
        "name": "aliyun-lb-list-instances",
        "title": "查询负载均衡实例",
        "description": "查询 SLB/ALB/NLB 实例列表",
        "tags": ["aliyun", "slb", "alb", "nlb", "load balancer", "负载均衡"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "type": {"type": "string", "description": "slb/alb/nlb"},
            "name": {"type": "string", "description": "名称关键词"},
            "tag_filters": {"type": "object", "description": "额外标签过滤"},
        },
        "required": [],
    },
    {
        "name": "aliyun-lb-describe-health",
        "title": "查询负载均衡后端健康",
        "description": "查询 SLB/ALB/NLB 监听和后端健康状态",
        "tags": ["aliyun", "slb", "alb", "nlb", "health", "健康检查", "后端"],
        "schema": {
            "load_balancer_id": {"type": "string", "description": "负载均衡实例 ID"},
            "region_id": {"type": "string", "description": "地域 ID"},
            "type": {"type": "string", "description": "slb/alb/nlb"},
        },
        "required": ["load_balancer_id"],
    },
    {
        "name": "aliyun-swas-list-instances",
        "title": "查询轻量应用服务器实例",
        "description": "按地域、状态、名称和标签查询轻量应用服务器实例列表",
        "tags": ["aliyun", "swas", "simple application server", "轻量应用服务器", "轻量服务器"],
        "schema": {
            "region_id": {"type": "string", "description": "地域 ID"},
            "status": {"type": "string", "description": "实例状态"},
            "name": {"type": "string", "description": "实例名称关键词"},
            "tag_filters": {"type": "object", "description": "额外标签过滤"},
            "page_size": {"type": "integer", "description": "最大返回数量，默认 50"},
        },
        "required": [],
    },
]


@dataclass(frozen=True)
class AliyunRuntimeConfig:
    enabled: bool = False
    access_key_id: str | None = None
    access_key_secret: str | None = None
    default_region_id: str = "cn-hangzhou"
    allowed_regions: list[str] = field(default_factory=list)
    required_tags: dict[str, list[str]] = field(default_factory=dict)
    allowed_instance_ids: list[str] = field(default_factory=list)
    sls_mappings: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_settings(cls) -> "AliyunRuntimeConfig":
        settings = get_settings()
        return cls(
            enabled=settings.aliyun_mcp_enabled,
            access_key_id=settings.aliyun_access_key_id,
            access_key_secret=settings.aliyun_access_key_secret,
            default_region_id=settings.aliyun_default_region_id,
            allowed_regions=list(settings.aliyun_allowed_regions),
            required_tags=dict(settings.aliyun_required_tags),
            allowed_instance_ids=list(settings.aliyun_allowed_instance_ids),
            sls_mappings=list(settings.aliyun_sls_mappings),
        )

    @property
    def configured(self) -> bool:
        return bool(self.access_key_id and self.access_key_secret)


class AliyunReadOnlyRegistry:
    def __init__(
        self,
        config: AliyunRuntimeConfig | None = None,
        clients: Any | None = None,
    ) -> None:
        self.config = config or AliyunRuntimeConfig.from_settings()
        self.clients = clients or AliyunSDKClientFacade(
            access_key_id=self.config.access_key_id or "",
            access_key_secret=self.config.access_key_secret or "",
            default_region_id=self.config.default_region_id,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        available = self.config.enabled and self.config.configured
        tools = []
        for spec in ALIYUN_TOOL_SPECS:
            tool = {
                "name": spec["name"],
                "title": spec["title"],
                "description": spec["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": spec["schema"],
                    "required": spec["required"],
                },
                "server": "builtin",
                "category": "aliyun",
                "tags": spec["tags"],
                "dangerLevel": "read",
                "executionPolicy": "executable",
                "available": available,
            }
            if not available:
                tool["unavailableReason"] = self._unavailable_reason()
            tools.append(tool)
        return tools

    async def aliyun_ecs_list_instances(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        items = await self.clients.list_ecs_instances(
            region_id=region,
            page_size=kwargs.get("page_size") or 50,
        )
        return self._list_result(
            self._filter_resources(items, id_key="instance_id"),
            total=len(items),
            region_id=region,
        )

    async def aliyun_ecs_describe_instance(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        instance_id = str(kwargs.get("instance_id") or "").strip()
        if not instance_id:
            return {"error": "missing_required_argument", "argument": "instance_id"}
        if not self._resource_id_allowed(instance_id):
            return {"error": "aliyun_resource_not_allowed", "resource_id": instance_id}
        item = await self.clients.describe_ecs_instance(instance_id=instance_id, region_id=region)
        if not self._tags_match(item.get("tags")):
            return {"error": "aliyun_resource_not_allowed", "resource_id": instance_id}
        return {"summary": {"found": True}, "item": item, "filters": self._filters(region)}

    async def aliyun_ecs_list_security_groups(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        items = await self.clients.list_security_groups(
            region_id=region,
            vpc_id=kwargs.get("vpc_id"),
            instance_id=kwargs.get("instance_id"),
        )
        return self._list_result(self._filter_resources(items), total=len(items), region_id=region)

    async def aliyun_ecs_describe_security_group_rules(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        security_group_id = str(kwargs.get("security_group_id") or "").strip()
        if not security_group_id:
            return {"error": "missing_required_argument", "argument": "security_group_id"}
        items = await self.clients.describe_security_group_rules(
            security_group_id=security_group_id,
            region_id=region,
            direction=kwargs.get("direction"),
        )
        return self._list_result(self._bounded(items, 100), total=len(items), region_id=region)

    async def aliyun_cms_get_ecs_metrics(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        instance_id = str(kwargs.get("instance_id") or "").strip()
        if not instance_id:
            return {"error": "missing_required_argument", "argument": "instance_id"}
        if not self._resource_id_allowed(instance_id):
            return {"error": "aliyun_resource_not_allowed", "resource_id": instance_id}
        samples = await self.clients.get_ecs_metrics(
            instance_id=instance_id,
            region_id=region,
            metrics=kwargs.get("metrics"),
            relative_range=kwargs.get("relative_range") or "1h",
            period=kwargs.get("period"),
            max_points=kwargs.get("max_points") or 400,
        )
        bounded = self._bounded(samples, 200)
        return {
            "summary": self._metric_summary(samples),
            "samples": bounded,
            "filters": self._filters(region),
        }

    async def aliyun_cms_get_alerts(self, **kwargs: Any) -> dict[str, Any]:
        return await self._bounded_client_list(
            "get_alerts",
            kwargs,
            limit=50,
            filter_resources=False,
        )

    async def aliyun_cms_get_event_history(self, **kwargs: Any) -> dict[str, Any]:
        return await self._bounded_client_list(
            "get_event_history",
            kwargs,
            limit=50,
            filter_resources=False,
        )

    async def aliyun_sls_list_logstores(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        mappings = self._matching_mappings(
            service=kwargs.get("service"),
            env=kwargs.get("env"),
            region_id=kwargs.get("region_id"),
        )
        allowed_regions = set(self._allowed_regions())
        mappings = [
            mapping
            for mapping in mappings
            if str(mapping.get("region_id") or self.config.default_region_id) in allowed_regions
        ]
        return {
            "summary": {"total": len(mappings), "returned": len(mappings)},
            "items": [self._public_mapping(mapping) for mapping in mappings],
        }

    async def aliyun_sls_query_logs(self, **kwargs: Any) -> dict[str, Any]:
        mapping = self._resolve_sls_mapping(kwargs)
        if "error" in mapping:
            return mapping
        region = self._resolve_region(mapping.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        limit = min(max(int(kwargs.get("limit") or 50), 1), 50)
        logs = await self.clients.query_logs(
            region_id=region,
            project=mapping["project"],
            logstore=mapping["logstore"],
            query=kwargs.get("query") or mapping.get("default_query") or "*",
            relative_range=kwargs.get("relative_range") or "30m",
            limit=limit,
        )
        bounded = self._bounded(logs, limit)
        return {
            "mapping": self._public_mapping(mapping),
            "summary": {"returned": len(bounded), "total": len(logs), "top_errors": []},
            "logs": bounded,
        }

    async def aliyun_sls_query_error_summary(self, **kwargs: Any) -> dict[str, Any]:
        query_kwargs = dict(kwargs)
        query_kwargs.setdefault("query", "level: ERROR or exception")
        result = await self.aliyun_sls_query_logs(**query_kwargs)
        if "error" in result:
            return result
        messages = [str(item.get("message") or item) for item in result.get("logs", [])]
        result["summary"]["top_errors"] = messages[:10]
        return result

    async def aliyun_lb_list_instances(self, **kwargs: Any) -> dict[str, Any]:
        return await self._bounded_client_list("list_load_balancers", kwargs, limit=50)

    async def aliyun_lb_describe_health(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        load_balancer_id = str(kwargs.get("load_balancer_id") or "").strip()
        if not load_balancer_id:
            return {"error": "missing_required_argument", "argument": "load_balancer_id"}
        items = await self.clients.describe_load_balancer_health(
            load_balancer_id=load_balancer_id,
            region_id=region,
            type=kwargs.get("type"),
        )
        unhealthy = [item for item in items if str(item.get("status", "")).lower() != "healthy"]
        return {
            "summary": {
                "total": len(items),
                "returned": min(len(items), 100),
                "unhealthy": len(unhealthy),
            },
            "items": self._bounded(items, 100),
            "filters": self._filters(region),
        }

    async def aliyun_swas_list_instances(self, **kwargs: Any) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        items = await self.clients.list_swas_instances(
            region_id=region,
            status=kwargs.get("status"),
            name=kwargs.get("name"),
            tag_filters=kwargs.get("tag_filters"),
            page_size=kwargs.get("page_size") or 50,
        )
        return self._list_result(
            self._filter_resources(items, id_key="instance_id"),
            total=len(items),
            region_id=region,
        )

    async def _bounded_client_list(
        self,
        method_name: str,
        kwargs: dict[str, Any],
        limit: int,
        filter_resources: bool = True,
    ) -> dict[str, Any]:
        region = self._resolve_region(kwargs.get("region_id"))
        denied = self._preflight(region)
        if denied:
            return denied
        method = getattr(self.clients, method_name)
        call_kwargs = {key: value for key, value in kwargs.items() if key != "region_id"}
        items = await method(region_id=region, **call_kwargs)
        filtered = self._filter_resources(items) if filter_resources else items
        return self._list_result(self._bounded(filtered, limit), total=len(items), region_id=region)

    def _preflight(self, region_id: str) -> dict[str, Any] | None:
        if not self.config.enabled:
            return {"error": "aliyun_not_enabled"}
        if not self.config.configured:
            return {"error": "aliyun_not_configured", "message": self._unavailable_reason()}
        if region_id not in self._allowed_regions():
            return {"error": "aliyun_region_not_allowed", "region_id": region_id}
        return None

    def _resolve_region(self, value: Any) -> str:
        return str(value or self.config.default_region_id or "cn-hangzhou").strip()

    def _allowed_regions(self) -> list[str]:
        return self.config.allowed_regions or [self.config.default_region_id]

    def _filter_resources(
        self,
        items: list[dict[str, Any]],
        id_key: str | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        for item in items:
            if id_key and not self._resource_id_allowed(str(item.get(id_key) or "")):
                continue
            if not self._tags_match(item.get("tags")):
                continue
            result.append(item)
        return result

    def _resource_id_allowed(self, resource_id: str) -> bool:
        allowlist = self.config.allowed_instance_ids
        return not allowlist or resource_id in allowlist

    def _tags_match(self, tags: Any) -> bool:
        required = self.config.required_tags
        if not required:
            return True
        normalized = _normalize_tags(tags)
        for key, allowed_values in required.items():
            if normalized.get(key) not in allowed_values:
                return False
        return True

    def _matching_mappings(
        self,
        service: Any = None,
        env: Any = None,
        region_id: Any = None,
    ) -> list[dict[str, Any]]:
        service_text = str(service or "").strip()
        env_text = str(env or "").strip()
        region_text = str(region_id or "").strip()
        result = []
        for mapping in self.config.sls_mappings:
            if service_text and mapping.get("service") != service_text:
                continue
            if env_text and mapping.get("env") != env_text:
                continue
            mapping_region = mapping.get("region_id", self.config.default_region_id)
            if region_text and mapping_region != region_text:
                continue
            result.append(mapping)
        return result

    def _resolve_sls_mapping(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        matches = self._matching_mappings(
            kwargs.get("service"),
            kwargs.get("env"),
            kwargs.get("region_id"),
        )
        project = kwargs.get("project")
        logstore = kwargs.get("logstore")
        if project or logstore:
            for mapping in matches or self.config.sls_mappings:
                if mapping.get("project") == project and mapping.get("logstore") == logstore:
                    return mapping
        if matches:
            return matches[0]
        return {
            "error": "aliyun_sls_mapping_not_found",
            "service": kwargs.get("service"),
            "env": kwargs.get("env"),
        }

    @staticmethod
    def _public_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
        return {
            "service": mapping.get("service"),
            "env": mapping.get("env"),
            "region_id": mapping.get("region_id"),
            "project": mapping.get("project"),
            "logstore": mapping.get("logstore"),
        }

    def _list_result(
        self,
        items: list[dict[str, Any]],
        total: int,
        region_id: str,
    ) -> dict[str, Any]:
        return {
            "summary": {
                "total": total,
                "returned": len(items),
                "filtered": max(total - len(items), 0),
            },
            "items": items,
            "filters": self._filters(region_id),
        }

    def _filters(self, region_id: str) -> dict[str, Any]:
        return {
            "region_id": region_id,
            "allowed_regions": self._allowed_regions(),
            "required_tags": self.config.required_tags,
            "allowed_instance_ids": self.config.allowed_instance_ids,
        }

    @staticmethod
    def _bounded(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        return list(items[:limit])

    @staticmethod
    def _metric_summary(samples: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        values: dict[str, list[float]] = {}
        for sample in samples:
            metrics = sample.get("metrics") if isinstance(sample, dict) else None
            if not isinstance(metrics, dict):
                continue
            for name, value in metrics.items():
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    continue
                values.setdefault(name, []).append(number)
        return {
            name: {
                "max": max(metric_values),
                "avg": round(sum(metric_values) / len(metric_values), 4),
                "latest": metric_values[-1],
            }
            for name, metric_values in values.items()
            if metric_values
        }

    def _unavailable_reason(self) -> str:
        if not self.config.enabled:
            return "Aliyun 只读 Adapter 未启用"
        return "未配置 Aliyun 只读 AccessKey"


def _normalize_tags(tags: Any) -> dict[str, str]:
    if isinstance(tags, dict):
        return {str(key): str(value) for key, value in tags.items()}
    if isinstance(tags, list):
        result = {}
        for item in tags:
            if not isinstance(item, dict):
                continue
            key = item.get("key") or item.get("Key") or item.get("tag_key")
            value = item.get("value") or item.get("Value") or item.get("tag_value")
            if key is not None and value is not None:
                result[str(key)] = str(value)
        return result
    return {}
