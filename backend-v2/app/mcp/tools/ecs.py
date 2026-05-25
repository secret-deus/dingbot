"""阿里云 ECS 客户端 - 封装核心 ECS 操作"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

_MONITOR_METRICS = {
    "CPU": ("cpu", "percent"),
    "InternetRX": ("internet_rx", "Kbit"),
    "InternetTX": ("internet_tx", "Kbit"),
    "InternetBandwidth": ("internet_bandwidth", "Kbit/s"),
    "IntranetRX": ("intranet_rx", "Kbit"),
    "IntranetTX": ("intranet_tx", "Kbit"),
    "IntranetBandwidth": ("intranet_bandwidth", "Kbit/s"),
    "BPSRead": ("bpsread", "Byte/s"),
    "BPSWrite": ("bpswrite", "Byte/s"),
    "IOPSRead": ("iopsread", "ops/s"),
    "IOPSWrite": ("iopswrite", "ops/s"),
    "CPUCreditUsage": ("cpucredit_usage", "credit"),
    "CPUCreditBalance": ("cpucredit_balance", "credit"),
    "CPUAdvanceCreditBalance": ("cpuadvance_credit_balance", "credit"),
    "CPUNotpaidSurplusCreditUsage": ("cpunotpaid_surplus_credit_usage", "credit"),
}

_MONITOR_METRIC_ALIASES = {key.lower(): key for key in _MONITOR_METRICS} | {
    attr.lower(): key for key, (attr, _unit) in _MONITOR_METRICS.items()
}

_RELATIVE_RANGES = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class ECSClient:
    def __init__(
        self, access_key_id: str, access_key_secret: str, region_id: str = "cn-hangzhou"
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        self._client: Any = None

    def _get_client(self, region_id: str | None = None) -> Any:
        target_region = region_id or self.region_id
        if target_region == self.region_id and self._client is not None:
            return self._client

        from alibabacloud_ecs20140526 import client as ecs_client
        from alibabacloud_tea_openapi import models as open_api_models

        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        config.endpoint = f"ecs.{target_region}.aliyuncs.com"
        client = ecs_client.Client(config)
        if target_region == self.region_id:
            self._client = client
        return client

    async def ecs_list_instances(self, **kwargs: Any) -> dict:
        from alibabacloud_ecs20140526 import models as ecs_models

        region_id = str(kwargs.get("region_id") or self.region_id).strip() or self.region_id
        client = self._get_client(region_id)
        page_size = kwargs.get("page_size", 20)
        request = ecs_models.DescribeInstancesRequest(region_id=region_id, page_size=page_size)
        response = client.describe_instances(request)
        body = response.body
        items = []
        for inst in body.instances.instance if body.instances else []:
            items.append(
                {
                    "instance_id": inst.instance_id,
                    "instance_name": inst.instance_name,
                    "status": inst.status,
                    "instance_type": inst.instance_type,
                    "region_id": inst.region_id,
                    "public_ip": (
                        inst.public_ip_address.ip_address
                        if inst.public_ip_address and inst.public_ip_address.ip_address
                        else []
                    ),
                    "private_ip": (
                        inst.vpc_attributes.private_ip_address.ip_address
                        if inst.vpc_attributes and inst.vpc_attributes.private_ip_address
                        else []
                    ),
                    "tags": _sdk_tags_to_dict(getattr(inst, "tags", None)),
                }
            )
        return {"total": body.total_count if body else 0, "items": items}

    async def ecs_describe_instance(self, **kwargs: Any) -> dict:
        from alibabacloud_ecs20140526 import models as ecs_models

        region_id = str(kwargs.get("region_id") or self.region_id).strip() or self.region_id
        client = self._get_client(region_id)
        instance_id = kwargs.get("instance_id", "")
        if not instance_id:
            return {"error": "instance_id 参数必填"}
        request = ecs_models.DescribeInstancesRequest(
            region_id=region_id,
            instance_ids=f'["{instance_id}"]',
        )
        response = client.describe_instances(request)
        body = response.body
        instances = body.instances.instance if body and body.instances else []
        if not instances:
            return {"error": f"实例 {instance_id} 不存在"}
        inst = instances[0]
        return {
            "instance_id": inst.instance_id,
            "instance_name": inst.instance_name,
            "status": inst.status,
            "instance_type": inst.instance_type,
            "cpu": inst.cpu,
            "memory": inst.memory,
            "os": inst.os_name_en if hasattr(inst, "os_name_en") else "",
            "created": inst.creation_time,
            "tags": _sdk_tags_to_dict(getattr(inst, "tags", None)),
        }

    async def ecs_describe_instance_monitor_data(self, **kwargs: Any) -> dict:
        from alibabacloud_ecs20140526 import models as ecs_models

        instance_id = str(kwargs.get("instance_id") or "").strip()
        if not instance_id:
            return {"error": "instance_id 参数必填"}

        end_time = _parse_utc_time(kwargs.get("end_time")) or datetime.now(timezone.utc).replace(
            microsecond=0
        )
        start_time = _parse_utc_time(kwargs.get("start_time"))
        if start_time is None:
            relative_range = str(kwargs.get("relative_range") or "1h").strip()
            start_time = end_time - _RELATIVE_RANGES.get(relative_range, _RELATIVE_RANGES["1h"])

        max_points = _safe_positive_int(kwargs.get("max_points"), 400)
        period = _resolve_period(kwargs.get("period"), start_time, end_time, max_points)
        metrics = _normalize_monitor_metrics(
            kwargs.get("metrics") or kwargs.get("metric_name") or ["CPU"]
        )
        if not metrics:
            return {
                "error": "unsupported_metrics",
                "supported_metrics": sorted(_MONITOR_METRICS.keys()),
            }

        original_region = self.region_id
        region_id = str(kwargs.get("region_id") or original_region).strip() or original_region
        client = self._get_client(region_id)
        request = ecs_models.DescribeInstanceMonitorDataRequest(
            instance_id=instance_id,
            start_time=_format_utc_time(start_time),
            end_time=_format_utc_time(end_time),
            period=period,
        )
        response = client.describe_instance_monitor_data(request)
        body = response.body
        monitor_data = body.monitor_data.instance_monitor_data if body and body.monitor_data else []

        samples = []
        values_by_metric: dict[str, list[float]] = {metric: [] for metric in metrics}
        for point in monitor_data:
            point_metrics = {}
            for metric in metrics:
                attr, _unit = _MONITOR_METRICS[metric]
                value = getattr(point, attr, None)
                if value is None:
                    continue
                point_metrics[metric] = value
                values_by_metric[metric].append(value)
            samples.append(
                {
                    "timestamp": getattr(point, "time_stamp", None),
                    "metrics": point_metrics,
                }
            )

        return {
            "instance_id": instance_id,
            "region_id": region_id,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "period": period,
            "summary": _summarize_monitor_metrics(values_by_metric),
            "samples": samples,
        }

    async def ecs_inspect(self, **kwargs: Any) -> dict:
        instance_ids_str = kwargs.get("instance_ids", "")
        if not instance_ids_str:
            result = await self.ecs_list_instances(page_size=50)
        else:
            ids = [i.strip() for i in instance_ids_str.split(",") if i.strip()]
            result = {"items": [], "total": 0}
            for iid in ids:
                detail = await self.ecs_describe_instance(instance_id=iid)
                if "error" not in detail:
                    result["items"].append(detail)
            result["total"] = len(result["items"])

        items = result.get("items", [])
        summary = {"total": len(items), "running": 0, "stopped": 0, "issues": []}
        for inst in items:
            status = inst.get("status", "")
            if status == "Running":
                summary["running"] += 1
            else:
                summary["stopped"] += 1
                summary["issues"].append(f"{inst.get('instance_id', '?')} 状态: {status}")

        return {"summary": summary, "instances": items}


def _parse_utc_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _format_utc_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _sdk_tags_to_dict(tags: Any) -> dict[str, str]:
    raw_tags = getattr(tags, "tag", None) if tags is not None else None
    if not raw_tags:
        return {}
    result = {}
    for tag in raw_tags:
        key = getattr(tag, "tag_key", None) or getattr(tag, "key", None)
        value = getattr(tag, "tag_value", None) or getattr(tag, "value", None)
        if key:
            result[str(key)] = str(value or "")
    return result


def _resolve_period(value: Any, start_time: datetime, end_time: datetime, max_points: int) -> int:
    requested = _safe_positive_int(value, 0)
    if requested in {60, 600, 3600}:
        return requested
    duration_seconds = max(60, int((end_time - start_time).total_seconds()))
    for period in (60, 600, 3600):
        if duration_seconds / period <= max_points:
            return period
    return 3600


def _normalize_monitor_metrics(value: Any) -> list[str]:
    raw_metrics = value
    if isinstance(raw_metrics, str):
        raw_metrics = [raw_metrics]
    if not isinstance(raw_metrics, list):
        return []

    metrics: list[str] = []
    for item in raw_metrics:
        normalized = _MONITOR_METRIC_ALIASES.get(str(item).strip().lower())
        if normalized and normalized not in metrics:
            metrics.append(normalized)
    return metrics


def _summarize_monitor_metrics(
    values_by_metric: dict[str, list[float]],
) -> dict[str, dict[str, Any]]:
    summary = {}
    for metric, values in values_by_metric.items():
        _attr, unit = _MONITOR_METRICS[metric]
        if not values:
            summary[metric] = {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None,
                "unit": unit,
            }
            continue
        summary[metric] = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 4),
            "latest": values[-1],
            "unit": unit,
        }
    return summary
