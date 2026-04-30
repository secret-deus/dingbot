"""阿里云 ECS 客户端 - 封装核心 ECS 操作"""

from __future__ import annotations

from typing import Any

from loguru import logger


class ECSClient:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-hangzhou") -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_ecs20140526 import client as ecs_client

            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )
            config.endpoint = f"ecs.{self.region_id}.aliyuncs.com"
            self._client = ecs_client(config)
        return self._client

    async def ecs_list_instances(self, **kwargs: Any) -> dict:
        from alibabacloud_ecs20140526 import models as ecs_models

        client = self._get_client()
        page_size = kwargs.get("page_size", 20)
        request = ecs_models.DescribeInstancesRequest(region_id=self.region_id, page_size=page_size)
        response = client.describe_instances(request)
        body = response.body
        items = []
        for inst in (body.instances.instance if body.instances else []):
            items.append({
                "instance_id": inst.instance_id,
                "instance_name": inst.instance_name,
                "status": inst.status,
                "instance_type": inst.instance_type,
                "region_id": inst.region_id,
                "public_ip": (inst.public_ip_address.ip_address if inst.public_ip_address and inst.public_ip_address.ip_address else []),
                "private_ip": (inst.vpc_attributes.private_ip_address.ip_address if inst.vpc_attributes and inst.vpc_attributes.private_ip_address else []),
            })
        return {"total": body.total_count if body else 0, "items": items}

    async def ecs_describe_instance(self, **kwargs: Any) -> dict:
        from alibabacloud_ecs20140526 import models as ecs_models

        client = self._get_client()
        instance_id = kwargs.get("instance_id", "")
        if not instance_id:
            return {"error": "instance_id 参数必填"}
        request = ecs_models.DescribeInstancesRequest(
            region_id=self.region_id, instance_ids=f'["{instance_id}"]',
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
