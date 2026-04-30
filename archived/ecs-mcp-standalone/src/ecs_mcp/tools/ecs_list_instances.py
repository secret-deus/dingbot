"""
ECS 实例列表工具：ecs-list-instances

返回指定地域下可用实例ID列表（可按状态/分页获取）。
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..config import get_config

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as open_api_models
from ..clients.ecs_rpc import rpc_get


class EcsListInstancesTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="ecs-list-instances",
            description="列出ECS实例，返回实例ID清单与少量元数据"
        )
        self.config = get_config()

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "region_id": {"type": "string", "description": "地域ID，默认使用配置值"},
                    "status": {"type": "string", "description": "按状态过滤，如 Running/Stopped"},
                    "page_number": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 50}
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            region_id = arguments.get("region_id") or self.config.region_id
            status = arguments.get("status")
            # 安全处理可能为 None/null 的整数参数
            page_number_val = arguments.get("page_number")
            page_number = int(page_number_val) if page_number_val is not None else 1
            page_size_val = arguments.get("page_size")
            page_size = int(page_size_val) if page_size_val is not None else 50

            if not self.config.access_key_id or not self.config.access_key_secret:
                return MCPCallToolResult.error("未配置阿里云AK/SK，请设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET")

            # 使用自签名RPC调用，绕过SDK凭证链兼容问题
            params = {
                "Action": "DescribeInstances",
                "RegionId": region_id,
                "PageNumber": page_number,
                "PageSize": page_size,
            }
            if status:
                params["Status"] = status

            resp_json = await rpc_get(
                params,
                access_key_id=self.config.access_key_id,
                access_key_secret=self.config.access_key_secret,
                endpoint="https://ecs.aliyuncs.com",
            )

            body = resp_json
            instances = (
                body.get("Instances", {}).get("Instance")
                if isinstance(body, dict)
                else None
            )
            total_count = body.get("TotalCount", 0) if isinstance(body, dict) else 0

            items: List[Dict[str, Any]] = []
            if instances:
                for it in instances:
                    if isinstance(it, dict):
                        items.append({
                            "instance_id": it.get("InstanceId"),
                            "instance_name": it.get("InstanceName"),
                            "status": it.get("Status"),
                            "zone_id": it.get("ZoneId"),
                        })
                    else:
                        # 兼容SDK对象（若后续切回SDK）
                        items.append({
                            "instance_id": getattr(it, "instance_id", None) or getattr(it, "InstanceId", None),
                            "instance_name": getattr(it, "instance_name", None) or getattr(it, "InstanceName", None),
                            "status": getattr(it, "status", None) or getattr(it, "Status", None),
                            "zone_id": getattr(it, "zone_id", None) or getattr(it, "ZoneId", None),
                        })

            return MCPCallToolResult.success({
                "region_id": region_id,
                "page_number": page_number,
                "page_size": page_size,
                "total_count": total_count,
                "items": items
            })

        except Exception as e:
            logger.error(f"列出实例失败: {e}")
            return MCPCallToolResult.error(f"查询失败: {str(e)}")


