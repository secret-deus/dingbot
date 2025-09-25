"""
ECS 监控查询工具：ecs-describe-instance-monitor-data

基于阿里云 DescribeInstanceMonitorData，实现时间窗/Period自动选择、点数<=400、必要时分片聚合、下采样与统计。
（已按 aliyun-api.md 优化：地域自动解析、指标别名归一化、Statistics、百分比限幅、meta.units 与字符串字段）
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..config import get_config
from ..clients.ecs_client import ECSSDKClient
from ..clients.ecs_rpc import rpc_get as ecs_rpc_get
from ..clients.cms_rpc import rpc_get as cms_rpc_get, _format_cms_time


def _parse_iso_utc(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(timezone.utc)


def _ceil_to_next_minute(dt: datetime) -> datetime:
    if dt.second == 0 and dt.microsecond == 0:
        return dt
    return (dt + timedelta(minutes=1)).replace(second=0, microsecond=0)


def _parse_relative_range(end_utc: datetime, rr: str) -> datetime:
    units = {"m": 60, "h": 3600, "d": 86400}
    try:
        value = int(rr[:-1])
        unit = rr[-1]
        seconds = value * units[unit]
        return end_utc - timedelta(seconds=seconds)
    except Exception:
        raise ValueError("relative_range 格式无效，示例: 15m/30m/1h/6h/24h/7d/30d")


def _choose_period(total_seconds: int) -> int:
    # 返回允许的最小period使点数<=400，否则返回最大3600并由分片处理
    candidates = [60, 600, 3600]
    for p in candidates:
        if (total_seconds + p - 1) // p <= 400:
            return p
    return 3600


def _split_windows(start_utc: datetime, end_utc: datetime, period: int) -> List[tuple[datetime, datetime]]:
    max_points = 400
    max_span = timedelta(seconds=period * max_points)
    windows = []
    cur = start_utc
    while cur < end_utc:
        nxt = min(cur + max_span, end_utc)
        windows.append((cur, nxt))
        cur = nxt
    return windows


@dataclass
class MonitorStats:
    cpu_avg: Optional[float] = None
    cpu_p95: Optional[float] = None
    cpu_max: Optional[float] = None
    credit_min: Optional[float] = None


class EcsDescribeInstanceMonitorDataTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="ecs-describe-instance-monitor-data",
            description="查询ECS实例监控数据，自动Period/分片聚合，返回summary与采样数据",
        )
        self.config = get_config()

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "ECS实例ID"},
                    "region_id": {"type": "string", "description": "地域ID（可覆盖配置）"},
                    "start_time": {"type": "string", "description": "ISO8601 UTC，示例 2024-10-29T23:00:00Z"},
                    "end_time": {"type": "string", "description": "ISO8601 UTC，默认当前UTC"},
                    "relative_range": {"type": "string", "description": "相对范围: 1h/6h/24h/7d/30d，与end_time组合"},
                    "period": {"type": "integer", "enum": [60, 600, 3600], "description": "不填自动选择"},
                    "metrics": {"type": "array", "items": {"type": "string"}, "description": "需要字段过滤"},
                    "max_points": {"type": "integer", "default": 400, "description": "最大返回点数，超出进行下采样"},
                },
                "required": ["instance_id"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            instance_id: str = arguments.get("instance_id")
            if not instance_id:
                return MCPCallToolResult.error("缺少必需参数: instance_id")

            end_time_arg = arguments.get("end_time")
            start_time_arg = arguments.get("start_time")
            relative_range = arguments.get("relative_range")
            period = arguments.get("period")
            max_points = int(arguments.get("max_points", 400))

            end_utc = _parse_iso_utc(end_time_arg) if end_time_arg else datetime.now(timezone.utc)
            end_utc = _ceil_to_next_minute(end_utc)
            if relative_range:
                start_utc = _parse_relative_range(end_utc, relative_range)
            else:
                if not start_time_arg:
                    return MCPCallToolResult.error("start_time 或 relative_range 必须提供一个")
                start_utc = _ceil_to_next_minute(_parse_iso_utc(start_time_arg))

            if start_utc >= end_utc:
                return MCPCallToolResult.error("结束时间不能早于开始时间")

            total_seconds = int((end_utc - start_utc).total_seconds())
            if total_seconds > 30 * 24 * 3600:
                return MCPCallToolResult.error("时间窗口超过30天限制")

            chosen_period = period or _choose_period(total_seconds)
            windows = _split_windows(start_utc, end_utc, chosen_period)

            if not self.config.access_key_id or not self.config.access_key_secret:
                return MCPCallToolResult.error("未配置阿里云AK/SK，请设置 ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET")

            points: List[Dict[str, Any]] = []

            # 地域自动解析
            async def _instance_exists_in_region(target_region: str) -> bool:
                try:
                    params = {
                        "Action": "DescribeInstances",
                        "RegionId": target_region,
                        "PageNumber": 1,
                        "PageSize": 1,
                        "InstanceIds": "[\"%s\"]" % instance_id,
                    }
                    body = await ecs_rpc_get(
                        params,
                        access_key_id=self.config.access_key_id,
                        access_key_secret=self.config.access_key_secret,
                        endpoint="https://ecs.aliyuncs.com",
                    )
                    insts = body.get("Instances", {}).get("Instance", []) if isinstance(body, dict) else []
                    return bool(insts)
                except Exception:
                    return False

            def _region_candidates() -> List[str]:
                import os as _os
                env_cands = _os.getenv("ALIBABA_CLOUD_REGION_CANDIDATES", "")
                parts = [p.strip() for p in env_cands.split(",") if p.strip()]
                defaults = [
                    "cn-hangzhou",
                    "cn-beijing",
                    "cn-shanghai",
                    "cn-shenzhen",
                    "cn-hongkong",
                    "cn-zhangjiakou",
                    "cn-huhehaote",
                    "cn-chengdu",
                    "cn-qingdao",
                    "cn-guangzhou",
                ]
                res: List[str] = []
                start_region = (arguments.get("region_id") or self.config.region_id)
                if start_region:
                    res.append(start_region)
                for r in parts:
                    if r not in res:
                        res.append(r)
                for r in defaults:
                    if r not in res:
                        res.append(r)
                return res

            resolved_region: Optional[str] = None
            initial_region = (arguments.get("region_id") or self.config.region_id)
            if initial_region and await _instance_exists_in_region(initial_region):
                resolved_region = initial_region
            else:
                for rid_try in _region_candidates():
                    if await _instance_exists_in_region(rid_try):
                        resolved_region = rid_try
                        break
            rid = resolved_region or initial_region

            for ws, we in windows:
                start_cms = _format_cms_time(ws)
                end_cms = _format_cms_time(we)
                cms_endpoints = [
                    f"https://metrics.{rid}.aliyuncs.com",
                    "https://metrics.aliyuncs.com",
                ]
                cms_actions = ["DescribeMetricList", "QueryMetricList"]

                cpu_points: List[Dict[str, Any]] = []
                cpu_namespaces = ["acs_ecs", "acs_ecs_dashboard"]
                for ep in cms_endpoints:
                    for action in cms_actions:
                        for ns in cpu_namespaces:
                            for p_try in ([chosen_period] + ([300] if chosen_period == 60 else [])):
                                try:
                                    params = {
                                        "Action": action,
                                        "Namespace": ns,
                                        "MetricName": "CPUUtilization",
                                        "Period": p_try,
                                        "Statistics": "Average,Maximum,Minimum",
                                        "StartTime": start_cms,
                                        "EndTime": end_cms,
                                        "Dimensions": f"{'{'}\"instanceId\":\"{instance_id}\"{'}'}",
                                        "RegionId": rid,
                                    }
                                    resp = await cms_rpc_get(
                                        params,
                                        access_key_id=self.config.access_key_id,
                                        access_key_secret=self.config.access_key_secret,
                                        endpoint=ep,
                                    )
                                    datapoints = resp.get("Datapoints")
                                    if isinstance(datapoints, str):
                                        import json as _json
                                        cpu_points = _json.loads(datapoints)
                                    elif isinstance(datapoints, list):
                                        cpu_points = datapoints
                                    else:
                                        cpu_points = []
                                    if cpu_points:
                                        break
                                except Exception:
                                    cpu_points = []
                            if cpu_points:
                                break
                        if cpu_points:
                            break
                    if cpu_points:
                        break

                window_map: Dict[str, Dict[str, Any]] = {}

                def _ts_to_iso(ts_val: Any) -> Optional[str]:
                    if isinstance(ts_val, (int, float)):
                        return datetime.utcfromtimestamp(ts_val / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")
                    return None

                for p in cpu_points:
                    ts = p.get("timestamp")
                    ts_iso = _ts_to_iso(ts)
                    if not ts_iso:
                        continue
                    cpu = p.get("Average") or p.get("Maximum") or p.get("Minimum") or p.get("Value")
                    try:
                        if isinstance(cpu, (int, float)):
                            if cpu < 0:
                                cpu = 0
                            elif cpu > 100:
                                cpu = 100
                    except Exception:
                        pass
                    window_map.setdefault(ts_iso, {"TimeStamp": ts_iso})["CPU"] = cpu

                # 指标别名归一化
                request_metrics_raw = arguments.get("metrics")
                alias_map = {
                    "networkin": "InternetInRate",
                    "networkout": "InternetOutRate",
                    "network_in": "InternetInRate",
                    "network_out": "InternetOutRate",
                    "internetinrate": "InternetInRate",
                    "internetoutrate": "InternetOutRate",
                    "intranetinrate": "IntranetInRate",
                    "intranetoutrate": "IntranetOutRate",
                    "diskreadiops": "DiskReadIOPS",
                    "diskwriteiops": "DiskWriteIOPS",
                    "vm.memoryutilization": "MemoryUtilization",
                    "diskusage_utilization": "DiskUsageUtilization",
                }
                request_metrics: Optional[List[str]] = None
                if request_metrics_raw:
                    nm: List[str] = []
                    for m in request_metrics_raw:
                        key = str(m).replace(" ", "").replace("-", "_").lower()
                        nm.append(alias_map.get(key, m))
                    request_metrics = nm

                async def _cms_try_fetch(metric_names: List[str], namespaces: List[str]) -> List[Dict[str, Any]]:
                    if request_metrics:
                        allowed = set([m.lower() for m in request_metrics])
                    else:
                        allowed = None
                    for ep in cms_endpoints:
                        for action in cms_actions:
                            for ns in namespaces:
                                for mn in metric_names:
                                    # 过滤时也按别名映射比对
                                    if allowed is not None:
                                        chk = alias_map.get(mn.lower(), mn.lower())
                                        if chk not in allowed and mn.lower() not in allowed:
                                            continue
                                    try:
                                        params = {
                                            "Action": action,
                                            "Namespace": ns,
                                            "MetricName": mn,
                                            "Period": chosen_period,
                                            "Statistics": "Average,Maximum,Minimum",
                                            "StartTime": start_cms,
                                            "EndTime": end_cms,
                                            "Dimensions": f"{'{'}\"instanceId\":\"{instance_id}\"{'}'}",
                                        }
                                        params["RegionId"] = rid
                                        r = await cms_rpc_get(
                                            params,
                                            access_key_id=self.config.access_key_id,
                                            access_key_secret=self.config.access_key_secret,
                                            endpoint=ep,
                                        )
                                        dps = r.get("Datapoints")
                                        if isinstance(dps, str):
                                            import json as _json
                                            dps = _json.loads(dps)
                                        if isinstance(dps, list) and dps:
                                            return dps
                                    except Exception:
                                        continue
                    return []

                # 2) 外网带宽
                net_out = await _cms_try_fetch(["InternetOutRate", "internet_out_rate"], ["acs_ecs", "acs_ecs_dashboard"])
                net_in = await _cms_try_fetch(["InternetInRate", "internet_in_rate"], ["acs_ecs", "acs_ecs_dashboard"])
                for arr, key in [(net_in, "InternetRX"), (net_out, "InternetTX")]:
                    for p in arr:
                        ts_iso = _ts_to_iso(p.get("timestamp"))
                        if not ts_iso:
                            continue
                        val = p.get("Average") or p.get("Maximum") or p.get("Minimum") or p.get("Value")
                        window_map.setdefault(ts_iso, {"TimeStamp": ts_iso})[key] = val

                # 3) 内网带宽
                intranet_out = await _cms_try_fetch(["IntranetOutRate", "intranet_out_rate"], ["acs_ecs", "acs_ecs_dashboard"])
                intranet_in = await _cms_try_fetch(["IntranetInRate", "intranet_in_rate"], ["acs_ecs", "acs_ecs_dashboard"])
                for arr, key in [(intranet_in, "IntranetInRate"), (intranet_out, "IntranetOutRate")]:
                    for p in arr:
                        ts_iso = _ts_to_iso(p.get("timestamp"))
                        if not ts_iso:
                            continue
                        val = p.get("Average") or p.get("Maximum") or p.get("Minimum") or p.get("Value")
                        window_map.setdefault(ts_iso, {"TimeStamp": ts_iso})[key] = val

                # 5) 内存利用率（按要求使用 vm.MemoryUtilization，命名空间 acs_ecs_dashboard）
                mem = await _cms_try_fetch(["vm.MemoryUtilization"], ["acs_ecs_dashboard"])
                for p in mem:
                    ts_iso = _ts_to_iso(p.get("timestamp"))
                    if not ts_iso:
                        continue
                    val = p.get("Average") or p.get("Maximum") or p.get("Minimum") or p.get("Value")
                    window_map.setdefault(ts_iso, {"TimeStamp": ts_iso})["MemoryUtilization"] = val

                # 6) 磁盘使用率（按要求使用 diskusage_utilization，命名空间 acs_ecs_dashboard）
                disk = await _cms_try_fetch(["diskusage_utilization"], ["acs_ecs_dashboard"])
                for p in disk:
                    ts_iso = _ts_to_iso(p.get("timestamp"))
                    if not ts_iso:
                        continue
                    val = p.get("Average") or p.get("Maximum") or p.get("Minimum") or p.get("Value")
                    window_map.setdefault(ts_iso, {"TimeStamp": ts_iso})["DiskUsageUtilization"] = val

                try:
                    def _iso_to_epoch_ms(s: str) -> float:
                        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp() * 1000

                    sorted_points = sorted(window_map.values(), key=lambda d: _iso_to_epoch_ms(d["TimeStamp"]))
                except Exception:
                    sorted_points = [window_map[k] for k in sorted(window_map.keys())]
                points.extend(sorted_points)

            stats = self._calc_stats(points)
            sampled = self._downsample(points, max_points)

            result = {
                "instance_id": instance_id,
                "window": {
                    "start": start_utc.isoformat().replace("+00:00", "Z"),
                    "end": end_utc.isoformat().replace("+00:00", "Z"),
                    "period": chosen_period,
                    "windows": len(windows),
                    "total_points": len(points),
                },
                "summary": {
                    "cpu_avg": stats.cpu_avg,
                    "cpu_p95": stats.cpu_p95,
                    "cpu_max": stats.cpu_max,
                    "cpu_avg_str": (f"{stats.cpu_avg:.2f}%" if isinstance(stats.cpu_avg, (int, float)) else None),
                    "cpu_p95_str": (f"{stats.cpu_p95:.2f}%" if isinstance(stats.cpu_p95, (int, float)) else None),
                    "cpu_max_str": (f"{stats.cpu_max:.2f}%" if isinstance(stats.cpu_max, (int, float)) else None),
                    "credit_min": stats.credit_min,
                    "points_truncated": len(sampled) < len(points),
                },
                "data_sample": sampled[:50],  # 控制体量
                "meta": {
                    "resolved_region": rid,
                    "units": {
                        "CPU": "%",
                        "InternetRX": "bps",
                        "InternetTX": "bps",
                        "IntranetInRate": "bps",
                        "IntranetOutRate": "bps",
                        "IOPSRead": "ops/s",
                        "IOPSWrite": "ops/s",
                        "MemoryUtilization": "%",
                        "DiskUsageUtilization": "%",
                    },
                },
                "warnings": [],
            }

            if len(points) > 400 and chosen_period == 3600:
                result["warnings"].append("时间窗较大，已分片聚合，建议缩小范围或增加period")

            return MCPCallToolResult.success(result)

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return MCPCallToolResult.error(f"查询失败: {str(e)}")

    async def _simulate_fetch(self, instance_id: str, start: datetime, end: datetime, period: int) -> List[Dict[str, Any]]:
        await asyncio.sleep(0)
        pts = []
        cur = start
        while cur < end:
            pts.append(
                {
                    "TimeStamp": cur.isoformat().replace("+00:00", "Z"),
                    "CPU": 20 + (hash((instance_id, cur.minute)) % 50),
                    "CPUCreditBalance": max(0, 100 - (cur.minute % 20) * 2),
                    "InternetRX": (cur.minute * 3) % 500,
                    "InternetTX": (cur.minute * 5) % 800,
                    "IOPSRead": (cur.minute * 7) % 1000,
                    "IOPSWrite": (cur.minute * 11) % 1200,
                }
            )
            cur += timedelta(seconds=period)
        return pts

    def _calc_stats(self, points: List[Dict[str, Any]]) -> MonitorStats:
        if not points:
            return MonitorStats()
        cpu_vals = [p.get("CPU") for p in points if isinstance(p.get("CPU"), (int, float))]
        credit_vals = [p.get("CPUCreditBalance") for p in points if isinstance(p.get("CPUCreditBalance"), (int, float))]
        cpu_vals_sorted = sorted(cpu_vals)
        p95 = None
        if cpu_vals_sorted:
            idx = int(0.95 * (len(cpu_vals_sorted) - 1))
            p95 = float(cpu_vals_sorted[idx])
        return MonitorStats(
            cpu_avg=(sum(cpu_vals) / len(cpu_vals)) if cpu_vals else None,
            cpu_p95=p95,
            cpu_max=max(cpu_vals) if cpu_vals else None,
            credit_min=min(credit_vals) if credit_vals else None,
        )

    def _downsample(self, points: List[Dict[str, Any]], max_points: int) -> List[Dict[str, Any]]:
        if len(points) <= max_points:
            return points
        step = max(1, len(points) // max_points)
        return [points[i] for i in range(0, len(points), step)][:max_points]


