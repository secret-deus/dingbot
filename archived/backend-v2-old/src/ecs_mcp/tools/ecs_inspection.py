"""
ECS 批量巡检工具：ecs-inspect

功能：
- 基于 DescribeInstances 获取实例集合（按状态/名称包含/Zone过滤，限制最大实例数）
- 基于已实现的 ecs-describe-instance-monitor-data 工具获取各实例监控摘要
- 应用阈值规则（CPU/内存/磁盘）输出风险列表与总体汇总
- 生成 Markdown 报告并存档到 project_document/reports/ecs/
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..config import get_config
from ..clients.ecs_rpc import rpc_get as ecs_rpc_get
from .ecs_monitor_data import EcsDescribeInstanceMonitorDataTool


class EcsInspectionTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="ecs-inspect",
            description="批量巡检ECS实例（按条件筛选），生成风险摘要与报告（Markdown）",
            timeout=120,  # 巡检工具需要更长时间，设置2分钟超时
            category="ecs"
        )
        self.config = get_config()

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            timeout=self.timeout,
            category=self.category,
            input_schema={
                "type": "object",
                "properties": {
                    "region_id": {"type": "string", "description": "地域ID（默认配置值）"},
                    "region_ids": {"type": "array", "items": {"type": "string"}, "description": "多地域扫描，优先于 region_id"},
                    "status": {"type": "string", "description": "实例状态过滤，如 Running/Stopped"},
                    "name_contains": {"type": "string", "description": "实例名包含关键字"},
                    "zone_id": {"type": "string", "description": "可用区过滤"},
                    "max_instances": {"type": "integer", "default": 1000, "description": "最大实例数（防止过大扫描）"},
                    "page_size": {"type": "integer", "default": 100, "description": "分页大小（最大100）"},
                    "scan_all_pages": {"type": "boolean", "default": True, "description": "是否遍历所有页直到达到max_instances或无更多数据"},
                    "max_concurrency": {"type": "integer", "default": 5, "description": "监控抓取并发度"},

                    "two_phase": {"type": "boolean", "default": False, "description": "是否启用两阶段扫描（此版本实现快速阶段）"},
                    "quick_window": {"type": "string", "default": "15m", "description": "快速阶段窗口，如 15m/30m"},
                    "quick_metrics": {"type": "array", "items": {"type": "string"}, "default": ["CPUUtilization","IntranetInRate","IntranetOutRate"], "description": "快速阶段指标"},

                    "relative_range": {"type": "string", "default": "1h", "description": "兼容参数：单阶段时的窗口"},
                    "period": {"type": "integer", "enum": [60, 600, 3600], "description": "Period（可选）"},
                    "thresholds": {
                        "type": "object",
                        "properties": {
                            "cpu_p95_high": {"type": "number", "default": 80},
                            "memory_util_high": {"type": "number", "default": 85},
                            "disk_util_high": {"type": "number", "default": 80}
                        },
                        "additionalProperties": False
                    }
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.config.access_key_id or not self.config.access_key_secret:
                return MCPCallToolResult.error("未配置阿里云AK/SK，请设置 ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET")

            # 多地域支持
            region_ids = arguments.get("region_ids") or []
            if not region_ids:
                region_ids = [arguments.get("region_id") or self.config.region_id]
            status = arguments.get("status") or "Running"
            name_contains = arguments.get("name_contains")
            zone_id = arguments.get("zone_id")
            # 安全处理可能为None的整数参数
            max_instances_val = arguments.get("max_instances")
            max_instances = int(max_instances_val) if max_instances_val is not None else 200
            page_size_val = arguments.get("page_size")
            page_size = max(1, min(100, int(page_size_val) if page_size_val is not None else 100))
            scan_all_pages = bool(arguments.get("scan_all_pages", True))

            # 快速阶段参数
            two_phase = bool(arguments.get("two_phase", False))
            quick_window = arguments.get("quick_window") or "15m"
            quick_metrics = arguments.get("quick_metrics") or ["CPUUtilization","IntranetInRate","IntranetOutRate"]

            # 单阶段兼容
            relative_range = arguments.get("relative_range") or "1h"
            period = arguments.get("period")
            thresholds = arguments.get("thresholds") or {}
            # 安全处理可能为None的浮点数参数
            cpu_p95_high_val = thresholds.get("cpu_p95_high")
            cpu_p95_high = float(cpu_p95_high_val) if cpu_p95_high_val is not None else 80.0
            mem_high_val = thresholds.get("memory_util_high")
            mem_high = float(mem_high_val) if mem_high_val is not None else 85.0
            disk_high_val = thresholds.get("disk_util_high")
            disk_high = float(disk_high_val) if disk_high_val is not None else 80.0

            # 1) 列出实例（按状态/名称/Zone过滤），支持多地域与分页
            candidates: List[Dict[str, Any]] = []
            for region_id in region_ids:
                page_number = 1
                while True:
                    params = {
                        "Action": "DescribeInstances",
                        "RegionId": region_id,
                        "PageNumber": page_number,
                        "PageSize": page_size,
                    }
                    if status:
                        params["Status"] = status
                    if zone_id:
                        params["ZoneId"] = zone_id
                    resp = await ecs_rpc_get(
                        params,
                        access_key_id=self.config.access_key_id,
                        access_key_secret=self.config.access_key_secret,
                        endpoint="https://ecs.aliyuncs.com",
                    )
                    inst_list = resp.get("Instances", {}).get("Instance", [])
                    if not inst_list:
                        break
                    for it in inst_list:
                        if not isinstance(it, dict):
                            continue
                        iid = it.get("InstanceId")
                        iname = it.get("InstanceName")
                        izone = it.get("ZoneId")
                        istatus = it.get("Status")
                        if name_contains and iname and name_contains not in iname:
                            continue
                        candidates.append({
                            "instance_id": iid,
                            "instance_name": iname,
                            "status": istatus,
                            "zone_id": izone,
                            "region_id": region_id,
                        })
                        if len(candidates) >= max_instances:
                            break
                    if len(candidates) >= max_instances or not scan_all_pages:
                        break
                    page_number += 1
                if len(candidates) >= max_instances:
                    break

            if not candidates:
                return MCPCallToolResult.success({
                    "regions": region_ids,
                    "instances": [],
                    "summary": {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0},
                    "report_path": None,
                    "message": "未匹配到实例"
                })

            # 2) 并发获取监控摘要
            monitor_tool = EcsDescribeInstanceMonitorDataTool()
            # 安全处理可能为None的整数参数
            concurrency_val = arguments.get("max_concurrency")
            concurrency = int(concurrency_val) if concurrency_val is not None else 5
            sem = asyncio.Semaphore(max(1, concurrency))

            async def fetch_one(inst: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    try:
                        res = await monitor_tool.execute({
                            "instance_id": inst["instance_id"],
                            "region_id": inst.get("region_id"),
                            # 快速阶段使用 quick_window/quick_metrics；当 two_phase=False 时与 relative_range/metrics 同效
                            "relative_range": quick_window if two_phase else (arguments.get("relative_range") or "1h"),
                            "metrics": quick_metrics if two_phase else arguments.get("metrics"),
                            **({"period": period} if period else {})
                        })
                        # 解析工具结果（MCPCallToolResult → JSON字符串 → dict）
                        if getattr(res, "is_error", False):
                            return {**inst, "error": "monitor_failed"}
                        content = res.content[0]["text"] if res.content else "{}"
                        import json as _json
                        data = _json.loads(content)
                        return {**inst, "monitor": data}
                    except Exception as e:
                        return {**inst, "error": str(e)}

            results = await asyncio.gather(*(fetch_one(i) for i in candidates))

            # 3) 打标签（风险等级）
            def compute_risk(item: Dict[str, Any]) -> Dict[str, Any]:
                mon = item.get("monitor") or {}
                summary = mon.get("summary") or {}
                data_sample = mon.get("data_sample") or []
                cpu_p95 = summary.get("cpu_p95")
                # 从采样中估计内存/磁盘最大值
                mem_max = None
                disk_max = None
                try:
                    mem_vals = [p.get("MemoryUtilization") for p in data_sample if isinstance(p.get("MemoryUtilization"), (int, float))]
                    disk_vals = [p.get("DiskUsageUtilization") for p in data_sample if isinstance(p.get("DiskUsageUtilization"), (int, float))]
                    mem_max = max(mem_vals) if mem_vals else None
                    disk_max = max(disk_vals) if disk_vals else None
                except Exception:
                    pass

                risk_flags = {
                    "cpu_p95_high": (cpu_p95 is not None and cpu_p95 >= cpu_p95_high),
                    "memory_high": (mem_max is not None and mem_max >= mem_high),
                    "disk_high": (disk_max is not None and disk_max >= disk_high),
                }
                risk_level = "low"
                if any([risk_flags["cpu_p95_high"], risk_flags["memory_high"], risk_flags["disk_high"]]):
                    # 多项命中判为高
                    hits = sum(1 for v in risk_flags.values() if v)
                    risk_level = "high" if hits >= 2 else "medium"
                return {**item, "risk_flags": risk_flags, "risk_level": risk_level, "cpu_p95": cpu_p95, "mem_max": mem_max, "disk_max": disk_max}

            enriched = [compute_risk(r) for r in results]

            total = len(enriched)
            high = sum(1 for x in enriched if x.get("risk_level") == "high")
            medium = sum(1 for x in enriched if x.get("risk_level") == "medium")
            low = total - high - medium

            # 记录时间
            finished_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            lines: List[str] = []
            lines.append(f"# ECS巡检报告\n")
            started_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            lines.append(f"- 开始: {started_utc}")
            lines.append(f"- 结束: {finished_utc}")
            lines.append(f"- 地域: {region_ids}")
            lines.append(f"- 实例数: {total}")
            lines.append(f"- 窗口: {relative_range}")
            lines.append(f"- 并发: {concurrency}")
            lines.append(f"- 阈值: CPU p95>={cpu_p95_high}%, 内存>={mem_high}%, 磁盘>={disk_high}%\n")
            lines.append(f"## 汇总")
            lines.append(f"- 高风险: {high}")
            lines.append(f"- 中风险: {medium}")
            lines.append(f"- 低风险: {low}\n")

            # Top 风险实例（按 cpu_p95 / mem_max / disk_max 排序优先展示）
            def risk_score(x: Dict[str, Any]) -> float:
                s = 0.0
                if isinstance(x.get("cpu_p95"), (int, float)):
                    s += float(x["cpu_p95"]) * 1.0
                if isinstance(x.get("mem_max"), (int, float)):
                    s += float(x["mem_max"]) * 0.8
                if isinstance(x.get("disk_max"), (int, float)):
                    s += float(x["disk_max"]) * 0.6
                return s

            top = sorted(enriched, key=risk_score, reverse=True)[:min(10, total)]
            lines.append("## Top 风险实例")
            lines.append("| 实例ID | 名称 | 风险等级 | CPU p95% | 内存max% | 磁盘max% | 区域 | 状态 |")
            lines.append("|---|---|---|---:|---:|---:|---|---|")
            for t in top:
                lines.append(
                    f"| {t.get('instance_id')} | {t.get('instance_name') or ''} | {t.get('risk_level')} | "
                    f"{(t.get('cpu_p95') if t.get('cpu_p95') is not None else '-')} | "
                    f"{(round(t.get('mem_max'),3) if isinstance(t.get('mem_max'), (int,float)) else '-')} | "
                    f"{(round(t.get('disk_max'),3) if isinstance(t.get('disk_max'), (int,float)) else '-')} | "
                    f"{t.get('zone_id') or ''} | {t.get('status') or ''} |"
                )

            lines.append("\n## 明细（采样）")
            for item in enriched:
                mon = item.get("monitor") or {}
                summary = mon.get("summary") or {}
                lines.append(f"### {item.get('instance_id')} ({item.get('instance_name') or ''})")
                lines.append(f"- 风险: {item.get('risk_level')} | 标记: {item.get('risk_flags')}")
                lines.append(f"- CPU: avg={summary.get('cpu_avg')}, p95={summary.get('cpu_p95')}, max={summary.get('cpu_max')}")
                # 采样点最多仅展示3条
                sample = (mon.get("data_sample") or [])[:3]
                if sample:
                    import json as _json
                    lines.append("- 样例点: \n```json\n" + _json.dumps(sample, ensure_ascii=False, indent=2) + "\n```")
                lines.append("")

            # 写入报告（仓库根 project_document/reports/ecs）
            repo_root = Path(__file__).resolve().parents[4]
            report_dir = repo_root / "project_document" / "reports" / "ecs"
            report_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"inspection_{'-'.join(region_ids)}_{ts}.md"
            report_path.write_text("\n".join(lines), encoding="utf-8")

            # 结果对象（同时存 JSON）
            duration_seconds = round(max(0.0, time.time() - time.mktime(datetime.strptime(started_utc, "%Y-%m-%d %H:%M:%S UTC").timetuple())), 3) if started_utc else None
            result = {
                "regions": region_ids,
                "window": relative_range,
                "instances": [{k: v for k, v in x.items() if k in ("instance_id", "instance_name", "status", "zone_id", "risk_level", "risk_flags", "cpu_p95", "mem_max", "disk_max") } for x in enriched],
                "summary": {"total": total, "high_risk": high, "medium_risk": medium, "low_risk": low},
                "report_path": str(report_path.relative_to(repo_root)),
                "finished_at_utc": finished_utc,
                "started_at_utc": started_utc,
                "duration_seconds": duration_seconds,
                "max_concurrency": concurrency,
            }
            try:
                import json as _json
                json_path = report_dir / f"inspection_{'-'.join(region_ids)}_{ts}.json"
                json_path.write_text(_json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                result["result_json_path"] = str(json_path.relative_to(repo_root))
            except Exception:
                pass
            return MCPCallToolResult.success(result)

        except Exception as e:
            logger.error(f"巡检执行失败: {e}")
            return MCPCallToolResult.error(f"巡检失败: {str(e)}")
