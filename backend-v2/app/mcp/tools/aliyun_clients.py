"""Thin Alibaba Cloud SDK wrappers for the read-only Aliyun adapter."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.mcp.tools.ecs import ECSClient

_RELATIVE_RANGES = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(days=1),
    "7d": timedelta(days=7),
}

_CMS_ECS_METRIC_NAMES = {
    "CPU": "CPUUtilization",
    "CPUUtilization": "CPUUtilization",
    "MemoryUtilization": "memory_usedutilization",
    "memory_usedutilization": "memory_usedutilization",
    "InternetInRate": "InternetInRate",
    "InternetOutRate": "InternetOutRate",
    "IntranetInRate": "IntranetInRate",
    "IntranetOutRate": "IntranetOutRate",
}


class AliyunSDKClientFacade:
    """SDK boundary kept small so tests can replace it with fake clients."""

    def __init__(self, access_key_id: str, access_key_secret: str, default_region_id: str) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.default_region_id = default_region_id
        self._ecs_clients: dict[str, ECSClient] = {}
        self._cms_clients: dict[str, Any] = {}
        self._sls_clients: dict[str, Any] = {}
        self._slb_clients: dict[str, Any] = {}
        self._alb_clients: dict[str, Any] = {}
        self._nlb_clients: dict[str, Any] = {}
        self._swas_clients: dict[str, Any] = {}

    def _ecs_client(self, region_id: str | None = None) -> ECSClient:
        target_region = region_id or self.default_region_id
        if target_region not in self._ecs_clients:
            self._ecs_clients[target_region] = ECSClient(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                region_id=target_region,
            )
        return self._ecs_clients[target_region]

    def _cms_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_cms20190101 import client as cms_client

        target_region = region_id or self.default_region_id
        if target_region not in self._cms_clients:
            self._cms_clients[target_region] = cms_client.Client(
                self._openapi_config(target_region, endpoint=f"metrics.{target_region}.aliyuncs.com")
            )
        return self._cms_clients[target_region]

    def _sls_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_sls20201230 import client as sls_client

        target_region = region_id or self.default_region_id
        if target_region not in self._sls_clients:
            self._sls_clients[target_region] = sls_client.Client(
                self._openapi_config(target_region)
            )
        return self._sls_clients[target_region]

    def _slb_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_slb20140515 import client as slb_client

        target_region = region_id or self.default_region_id
        if target_region not in self._slb_clients:
            self._slb_clients[target_region] = slb_client.Client(
                self._openapi_config(target_region)
            )
        return self._slb_clients[target_region]

    def _alb_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_alb20200616 import client as alb_client

        target_region = region_id or self.default_region_id
        if target_region not in self._alb_clients:
            self._alb_clients[target_region] = alb_client.Client(
                self._openapi_config(target_region)
            )
        return self._alb_clients[target_region]

    def _nlb_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_nlb20220430 import client as nlb_client

        target_region = region_id or self.default_region_id
        if target_region not in self._nlb_clients:
            self._nlb_clients[target_region] = nlb_client.Client(
                self._openapi_config(target_region)
            )
        return self._nlb_clients[target_region]

    def _swas_client(self, region_id: str | None = None) -> Any:
        from alibabacloud_swas_open20200601 import client as swas_client

        target_region = region_id or self.default_region_id
        if target_region not in self._swas_clients:
            self._swas_clients[target_region] = swas_client.Client(
                self._openapi_config(target_region, endpoint=f"swas.{target_region}.aliyuncs.com")
            )
        return self._swas_clients[target_region]

    def _openapi_config(self, region_id: str, endpoint: str | None = None) -> Any:
        from alibabacloud_tea_openapi import models as open_api_models

        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=region_id,
        )
        if endpoint:
            config.endpoint = endpoint
        return config

    async def list_ecs_instances(self, **kwargs: Any) -> list[dict[str, Any]]:
        client = self._ecs_client(kwargs.get("region_id"))
        result = await client.ecs_list_instances(
            region_id=kwargs.get("region_id"),
            page_size=kwargs.get("page_size", 50),
        )
        return result.get("items", []) if isinstance(result, dict) else []

    async def describe_ecs_instance(self, **kwargs: Any) -> dict[str, Any]:
        client = self._ecs_client(kwargs.get("region_id"))
        result = await client.ecs_describe_instance(
            instance_id=kwargs.get("instance_id"),
            region_id=kwargs.get("region_id"),
        )
        return result if isinstance(result, dict) else {"error": "aliyun_api_error"}

    async def list_security_groups(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_ecs20140526 import models as ecs_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        client = self._ecs_client(region_id)._get_client(region_id)
        request = ecs_models.DescribeSecurityGroupsRequest(
            region_id=region_id,
            page_size=min(max(int(kwargs.get("page_size") or 50), 1), 100),
            vpc_id=kwargs.get("vpc_id"),
        )
        response = client.describe_security_groups(request)
        groups = _extract_sdk_list(response.body, "security_groups", "security_group")
        return [_normalize_security_group(group, region_id) for group in groups]

    async def describe_security_group_rules(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_ecs20140526 import models as ecs_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        client = self._ecs_client(region_id)._get_client(region_id)
        request = ecs_models.DescribeSecurityGroupAttributeRequest(
            region_id=region_id,
            security_group_id=kwargs.get("security_group_id"),
            direction=kwargs.get("direction"),
        )
        response = client.describe_security_group_attribute(request)
        rules = _extract_sdk_list(response.body, "permissions", "permission")
        return [_normalize_security_group_rule(rule) for rule in rules]

    async def get_ecs_metrics(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_cms20190101 import models as cms_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        instance_id = str(kwargs.get("instance_id") or "")
        metrics = _normalize_metric_names(kwargs.get("metrics") or ["CPU"])
        start_time, end_time = _time_window(kwargs.get("relative_range") or "1h")
        samples_by_ts: dict[str, dict[str, Any]] = {}

        for metric in metrics:
            request = cms_models.DescribeMetricListRequest(
                region_id=region_id,
                namespace="acs_ecs_dashboard",
                metric_name=metric,
                dimensions=json.dumps([{"instanceId": instance_id}], separators=(",", ":")),
                start_time=str(int(start_time.timestamp() * 1000)),
                end_time=str(int(end_time.timestamp() * 1000)),
                period=str(kwargs.get("period") or "60"),
                length=str(min(max(int(kwargs.get("max_points") or 400), 1), 1000)),
            )
            response = self._cms_client(region_id).describe_metric_list(request)
            for point in _parse_datapoints(getattr(response.body, "datapoints", None)):
                timestamp = str(point.get("timestamp") or point.get("Timestamp") or "")
                if not timestamp:
                    continue
                sample = samples_by_ts.setdefault(
                    timestamp,
                    {"timestamp": timestamp, "metrics": {}},
                )
                value = _metric_value(point)
                if value is not None:
                    sample["metrics"][metric] = value

        return list(samples_by_ts.values())

    async def get_alerts(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_cms20190101 import models as cms_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        request = cms_models.DescribeMetricRuleListRequest(
            region_id=region_id,
            namespace=kwargs.get("namespace"),
            metric_name=kwargs.get("metric_name"),
            alert_state=kwargs.get("state") or kwargs.get("alert_state"),
            page=1,
            page_size=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._cms_client(region_id).describe_metric_rule_list(request)
        alarms = _extract_sdk_list(response.body, "alarms", "alarm")
        return [_normalize_alert(alarm, region_id) for alarm in alarms]

    async def get_event_history(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_cms20190101 import models as cms_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        start_time, end_time = _time_window(kwargs.get("relative_range"))
        request = cms_models.DescribeSystemEventAttributeRequest(
            region_id=region_id,
            product=kwargs.get("product") or "ECS",
            event_type=kwargs.get("event_type"),
            status=kwargs.get("status"),
            level=kwargs.get("level"),
            start_time=str(int(start_time.timestamp() * 1000)),
            end_time=str(int(end_time.timestamp() * 1000)),
            page_number=1,
            page_size=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._cms_client(region_id).describe_system_event_attribute(request)
        events = _extract_sdk_list(response.body, "system_events", "system_event")
        return [_normalize_system_event(event) for event in events]

    async def list_logstores(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_sls20201230 import models as sls_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        project = str(kwargs.get("project") or "").strip()
        request = sls_models.ListLogStoresRequest(
            offset=0,
            size=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._sls_client(region_id).list_log_stores(project, request)
        logstores = list(getattr(response.body, "logstores", None) or [])
        return [
            {"project": project, "logstore": logstore, "region_id": region_id}
            for logstore in logstores
        ]

    async def query_logs(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_sls20201230 import models as sls_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        start_time, end_time = _time_window(kwargs.get("relative_range"))
        request = sls_models.GetLogsV2Request(
            from_=int(start_time.timestamp()),
            to=int(end_time.timestamp()),
            query=str(kwargs.get("query") or "*"),
            line=min(max(int(kwargs.get("limit") or 50), 1), 50),
            offset=0,
            reverse=True,
        )
        response = self._sls_client(region_id).get_logs_v2(
            str(kwargs.get("project") or ""),
            str(kwargs.get("logstore") or ""),
            request,
        )
        return [dict(item) for item in (getattr(response.body, "data", None) or [])]

    async def list_load_balancers(self, **kwargs: Any) -> list[dict[str, Any]]:
        lb_type = str(kwargs.get("type") or "slb").strip().lower()
        if lb_type == "alb":
            return self._list_alb_load_balancers(**kwargs)
        if lb_type == "nlb":
            return self._list_nlb_load_balancers(**kwargs)
        return self._list_slb_load_balancers(**kwargs)

    def _list_slb_load_balancers(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_slb20140515 import models as slb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        request = slb_models.DescribeLoadBalancersRequest(
            region_id=region_id,
            load_balancer_id=kwargs.get("load_balancer_id"),
            load_balancer_name=kwargs.get("name") or kwargs.get("load_balancer_name"),
            load_balancer_status=kwargs.get("status"),
            vpc_id=kwargs.get("vpc_id"),
            page_number=1,
            page_size=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._slb_client(region_id).describe_load_balancers(request)
        balancers = _extract_sdk_list(response.body, "load_balancers", "load_balancer")
        return [_normalize_slb_load_balancer(balancer, region_id) for balancer in balancers]

    def _list_alb_load_balancers(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_alb20200616 import models as alb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        load_balancer_ids = [kwargs["load_balancer_id"]] if kwargs.get("load_balancer_id") else None
        request = alb_models.ListLoadBalancersRequest(
            load_balancer_ids=load_balancer_ids,
            load_balancer_names=[kwargs["name"]] if kwargs.get("name") else None,
            load_balancer_status=kwargs.get("status"),
            vpc_ids=[kwargs["vpc_id"]] if kwargs.get("vpc_id") else None,
            max_results=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._alb_client(region_id).list_load_balancers(request)
        return [
            _normalize_modern_load_balancer(balancer, region_id, "alb")
            for balancer in (getattr(response.body, "load_balancers", None) or [])
        ]

    def _list_nlb_load_balancers(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_nlb20220430 import models as nlb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        load_balancer_ids = [kwargs["load_balancer_id"]] if kwargs.get("load_balancer_id") else None
        request = nlb_models.ListLoadBalancersRequest(
            region_id=region_id,
            load_balancer_ids=load_balancer_ids,
            load_balancer_names=[kwargs["name"]] if kwargs.get("name") else None,
            load_balancer_status=kwargs.get("status"),
            vpc_ids=[kwargs["vpc_id"]] if kwargs.get("vpc_id") else None,
            max_results=min(max(int(kwargs.get("limit") or 50), 1), 100),
        )
        response = self._nlb_client(region_id).list_load_balancers(request)
        return [
            _normalize_modern_load_balancer(balancer, region_id, "nlb")
            for balancer in (getattr(response.body, "load_balancers", None) or [])
        ]

    async def describe_load_balancer_health(self, **kwargs: Any) -> list[dict[str, Any]]:
        lb_type = str(kwargs.get("type") or "slb").strip().lower()
        if lb_type == "alb":
            return self._describe_alb_health(**kwargs)
        if lb_type == "nlb":
            return self._describe_nlb_health(**kwargs)
        return self._describe_slb_health(**kwargs)

    async def list_swas_instances(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_swas_open20200601 import models as swas_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        request = swas_models.ListInstancesRequest(
            region_id=region_id,
            instance_name=kwargs.get("name"),
            status=kwargs.get("status"),
            page_number=1,
            page_size=min(max(int(kwargs.get("page_size") or 50), 1), 100),
            tag=_swas_request_tags(kwargs.get("tag_filters")),
        )
        response = self._swas_client(region_id).list_instances(request)
        return [
            _normalize_swas_instance(instance, region_id)
            for instance in (getattr(response.body, "instances", None) or [])
        ]

    def _describe_slb_health(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_slb20140515 import models as slb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        request = slb_models.DescribeHealthStatusRequest(
            region_id=region_id,
            load_balancer_id=kwargs.get("load_balancer_id"),
            listener_port=_optional_int(kwargs.get("listener_port")),
            listener_protocol=kwargs.get("listener_protocol"),
        )
        response = self._slb_client(region_id).describe_health_status(request)
        backends = _extract_sdk_list(response.body, "backend_servers", "backend_server")
        return [_normalize_backend_health(backend) for backend in backends]

    def _describe_alb_health(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_alb20200616 import models as alb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        listeners = self._list_alb_listeners(region_id, str(kwargs.get("load_balancer_id") or ""))
        result = []
        for listener in listeners:
            request = alb_models.GetListenerHealthStatusRequest(
                listener_id=getattr(listener, "listener_id", None),
                include_rule=True,
                max_results=100,
            )
            response = self._alb_client(region_id).get_listener_health_status(request)
            result.extend(_normalize_modern_health(response.body, "alb"))
        return result

    def _describe_nlb_health(self, **kwargs: Any) -> list[dict[str, Any]]:
        from alibabacloud_nlb20220430 import models as nlb_models

        region_id = str(kwargs.get("region_id") or self.default_region_id)
        listeners = self._list_nlb_listeners(region_id, str(kwargs.get("load_balancer_id") or ""))
        result = []
        for listener in listeners:
            request = nlb_models.GetListenerHealthStatusRequest(
                listener_id=getattr(listener, "listener_id", None),
                region_id=region_id,
            )
            response = self._nlb_client(region_id).get_listener_health_status(request)
            result.extend(_normalize_modern_health(response.body, "nlb"))
        return result

    def _list_alb_listeners(self, region_id: str, load_balancer_id: str) -> list[Any]:
        from alibabacloud_alb20200616 import models as alb_models

        request = alb_models.ListListenersRequest(
            load_balancer_ids=[load_balancer_id],
            max_results=100,
        )
        response = self._alb_client(region_id).list_listeners(request)
        return list(getattr(response.body, "listeners", None) or [])

    def _list_nlb_listeners(self, region_id: str, load_balancer_id: str) -> list[Any]:
        from alibabacloud_nlb20220430 import models as nlb_models

        request = nlb_models.ListListenersRequest(
            region_id=region_id,
            load_balancer_ids=[load_balancer_id],
            max_results=100,
        )
        response = self._nlb_client(region_id).list_listeners(request)
        return list(getattr(response.body, "listeners", None) or [])


def _extract_sdk_list(body: Any, container_name: str, item_name: str) -> list[Any]:
    container = getattr(body, container_name, None)
    if container is None:
        return []
    items = getattr(container, item_name, None)
    return list(items or [])


def _normalize_security_group(group: Any, region_id: str) -> dict[str, Any]:
    return {
        "security_group_id": getattr(group, "security_group_id", None),
        "name": getattr(group, "security_group_name", None),
        "description": getattr(group, "description", None),
        "vpc_id": getattr(group, "vpc_id", None),
        "type": getattr(group, "security_group_type", None),
        "region_id": region_id,
        "tags": _sdk_tags_to_dict(getattr(group, "tags", None)),
    }


def _normalize_security_group_rule(rule: Any) -> dict[str, Any]:
    return {
        "rule_id": getattr(rule, "security_group_rule_id", None),
        "direction": getattr(rule, "direction", None),
        "ip_protocol": getattr(rule, "ip_protocol", None),
        "port_range": getattr(rule, "port_range", None),
        "source_cidr_ip": getattr(rule, "source_cidr_ip", None),
        "dest_cidr_ip": getattr(rule, "dest_cidr_ip", None),
        "policy": getattr(rule, "policy", None),
        "priority": getattr(rule, "priority", None),
        "description": getattr(rule, "description", None),
    }


def _normalize_alert(alert: Any, region_id: str) -> dict[str, Any]:
    return {
        "id": getattr(alert, "rule_id", None),
        "name": getattr(alert, "rule_name", None),
        "state": getattr(alert, "alert_state", None),
        "enabled": getattr(alert, "enable_state", None),
        "namespace": getattr(alert, "namespace", None),
        "metric_name": getattr(alert, "metric_name", None),
        "dimensions": _parse_jsonish(getattr(alert, "dimensions", None)),
        "resources": _parse_jsonish(getattr(alert, "resources", None)),
        "region_id": region_id,
    }


def _normalize_system_event(event: Any) -> dict[str, Any]:
    return {
        "id": getattr(event, "id", None),
        "name": getattr(event, "name", None),
        "product": getattr(event, "product", None),
        "level": getattr(event, "level", None),
        "status": getattr(event, "status", None),
        "resource_id": getattr(event, "resource_id", None),
        "instance_name": getattr(event, "instance_name", None),
        "region_id": getattr(event, "region_id", None),
        "time": getattr(event, "time", None),
        "content": _parse_jsonish(getattr(event, "content", None)),
    }


def _normalize_slb_load_balancer(balancer: Any, region_id: str) -> dict[str, Any]:
    return {
        "load_balancer_id": getattr(balancer, "load_balancer_id", None),
        "name": getattr(balancer, "load_balancer_name", None),
        "status": getattr(balancer, "load_balancer_status", None),
        "address": getattr(balancer, "address", None),
        "address_type": getattr(balancer, "address_type", None),
        "network_type": getattr(balancer, "network_type", None),
        "vpc_id": getattr(balancer, "vpc_id", None),
        "region_id": getattr(balancer, "region_id", None) or region_id,
        "tags": _sdk_tags_to_dict(getattr(balancer, "tags", None)),
    }


def _normalize_modern_load_balancer(
    balancer: Any,
    region_id: str,
    lb_type: str,
) -> dict[str, Any]:
    return {
        "load_balancer_id": getattr(balancer, "load_balancer_id", None),
        "name": getattr(balancer, "load_balancer_name", None),
        "status": getattr(balancer, "load_balancer_status", None),
        "address": getattr(balancer, "dnsname", None),
        "address_type": getattr(balancer, "address_type", None),
        "network_type": lb_type,
        "vpc_id": getattr(balancer, "vpc_id", None),
        "region_id": getattr(balancer, "region_id", None) or region_id,
        "type": lb_type,
        "tags": _sdk_tags_to_dict(getattr(balancer, "tags", None)),
    }


def _normalize_backend_health(backend: Any) -> dict[str, Any]:
    status = str(getattr(backend, "server_health_status", None) or "").lower()
    return {
        "listener": getattr(backend, "listener_port", None),
        "port": getattr(backend, "port", None),
        "protocol": getattr(backend, "protocol", None),
        "backend": getattr(backend, "server_id", None),
        "server_ip": getattr(backend, "server_ip", None),
        "status": "healthy" if status == "normal" else status or "unknown",
    }


def _normalize_modern_health(body: Any, lb_type: str) -> list[dict[str, Any]]:
    result = []
    for listener in getattr(body, "listener_health_status", None) or []:
        listener_id = getattr(listener, "listener_id", None)
        listener_port = getattr(listener, "listener_port", None)
        protocol = getattr(listener, "listener_protocol", None)
        server_groups = getattr(listener, "server_group_infos", None) or []
        if not server_groups:
            result.append(
                {
                    "type": lb_type,
                    "listener": listener_port,
                    "listener_id": listener_id,
                    "protocol": protocol,
                    "status": "healthy",
                }
            )
            continue
        for server_group in server_groups:
            non_normal = getattr(server_group, "non_normal_servers", None) or []
            if not non_normal:
                result.append(
                    {
                        "type": lb_type,
                        "listener": listener_port,
                        "listener_id": listener_id,
                        "protocol": protocol,
                        "server_group_id": getattr(server_group, "server_group_id", None),
                        "status": "healthy",
                    }
                )
                continue
            for server in non_normal:
                result.append(
                    {
                        "type": lb_type,
                        "listener": listener_port,
                        "listener_id": listener_id,
                        "protocol": protocol,
                        "server_group_id": getattr(server_group, "server_group_id", None),
                        "backend": getattr(server, "server_id", None),
                        "server_ip": getattr(server, "server_ip", None),
                        "port": getattr(server, "port", None),
                        "status": getattr(server, "status", None) or "unhealthy",
                    }
                )
    return result


def _sdk_tags_to_dict(tags: Any) -> dict[str, str]:
    raw_tags = tags if isinstance(tags, list) else getattr(tags, "tag", None)
    if not raw_tags:
        return {}
    result = {}
    for tag in raw_tags:
        key = getattr(tag, "tag_key", None) or getattr(tag, "key", None)
        value = getattr(tag, "tag_value", None) or getattr(tag, "value", None)
        if key:
            result[str(key)] = str(value or "")
    return result


def _swas_request_tags(tag_filters: Any) -> list[Any] | None:
    if not isinstance(tag_filters, dict) or not tag_filters:
        return None
    from alibabacloud_swas_open20200601 import models as swas_models

    return [
        swas_models.ListInstancesRequestTag(key=str(key), value=str(value))
        for key, value in tag_filters.items()
        if key and value is not None
    ] or None


def _normalize_swas_instance(instance: Any, region_id: str) -> dict[str, Any]:
    resource_spec = getattr(instance, "resource_spec", None)
    image = getattr(instance, "image", None)
    return {
        "instance_id": getattr(instance, "instance_id", None),
        "name": getattr(instance, "instance_name", None),
        "status": getattr(instance, "status", None),
        "business_status": getattr(instance, "business_status", None),
        "region_id": getattr(instance, "region_id", None) or region_id,
        "public_ip": getattr(instance, "public_ip_address", None),
        "inner_ip": getattr(instance, "inner_ip_address", None),
        "plan_type": getattr(instance, "plan_type", None),
        "cpu": getattr(resource_spec, "cpu", None),
        "memory": getattr(resource_spec, "memory", None),
        "image_name": getattr(image, "image_name", None),
        "expired_time": getattr(instance, "expired_time", None),
        "tags": _swas_tags_to_dict(getattr(instance, "tags", None)),
    }


def _swas_tags_to_dict(tags: Any) -> dict[str, str]:
    result = {}
    for tag in list(tags or []):
        key = getattr(tag, "key", None)
        value = getattr(tag, "value", None)
        if key:
            result[str(key)] = str(value or "")
    return result


def _time_window(relative_range: Any) -> tuple[datetime, datetime]:
    end_time = datetime.now(timezone.utc).replace(microsecond=0)
    delta = _RELATIVE_RANGES.get(str(relative_range or "30m"), _RELATIVE_RANGES["30m"])
    return end_time - delta, end_time


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normalize_metric_names(value: Any) -> list[str]:
    if isinstance(value, str):
        raw_values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        raw_values = [str(item).strip() for item in value]
    else:
        raw_values = ["CPU"]
    metrics = [_CMS_ECS_METRIC_NAMES[item] for item in raw_values if item in _CMS_ECS_METRIC_NAMES]
    return metrics or ["CPUUtilization"]


def _parse_datapoints(value: Any) -> list[dict[str, Any]]:
    parsed = _parse_jsonish(value)
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def _metric_value(point: dict[str, Any]) -> float | None:
    for key in ["Average", "average", "Value", "value", "Maximum", "maximum"]:
        if key not in point:
            continue
        try:
            return float(point[key])
        except (TypeError, ValueError):
            return None
    return None
