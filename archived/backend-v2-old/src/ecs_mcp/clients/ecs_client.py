"""
阿里云 ECS SDK 客户端封装（异步包装）
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_credentials.models import Config as CredConfig
from alibabacloud_credentials.client import Client as CredClient


class ECSSDKClient:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str, security_token: Optional[str] = None):
        cfg = open_api_models.Config(region_id=region_id)
        cfg.endpoint = "ecs.aliyuncs.com"
        # 使用显式凭证对象，规避 provider_name 属性缺失问题
        cred_cfg = CredConfig(
            type="access_key",
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token,
        )
        cred_client = CredClient(cred_cfg)
        cfg.credential = cred_client
        self._client = Ecs20140526Client(cfg)
        self._region_id = region_id

    async def describe_instance_monitor_data(
        self,
        instance_id: str,
        start_time_iso: str,
        end_time_iso: str,
        period: int,
    ) -> List[Dict[str, Any]]:
        """调用DescribeInstanceMonitorData，返回实例监控点位列表（字典化）。"""
        req = ecs_models.DescribeInstanceMonitorDataRequest(
            instance_id=instance_id,
            start_time=start_time_iso,
            end_time=end_time_iso,
            period=period,
        )

        def _call_sync():
            return self._client.describe_instance_monitor_data(req)

        try:
            resp = await asyncio.to_thread(_call_sync)
            body = getattr(resp, "body", None)
            monitor_data = getattr(body, "monitor_data", None) if body else None
            items = getattr(monitor_data, "instance_monitor_data", None) if monitor_data else None
            result: List[Dict[str, Any]] = []
            if items:
                for it in items:
                    # 将SDK模型转为dict
                    d = {
                        "TimeStamp": getattr(it, "time_stamp", None),
                        "CPU": getattr(it, "cpu", None),
                        "CPUCreditBalance": getattr(it, "cpu_credit_balance", None),
                        "CPUCreditUsage": getattr(it, "cpu_credit_usage", None),
                        "CPUNotpaidSurplusCreditUsage": getattr(it, "cpu_notpaid_surplus_credit_usage", None),
                        "CPUAdvanceCreditBalance": getattr(it, "cpu_advance_credit_balance", None),
                        "InternetRX": getattr(it, "internet_rx", None),
                        "InternetTX": getattr(it, "internet_tx", None),
                        "InternetBandwidth": getattr(it, "internet_bandwidth", None),
                        "IntranetRX": getattr(it, "intranet_rx", None),
                        "IntranetTX": getattr(it, "intranet_tx", None),
                        "IntranetBandwidth": getattr(it, "intranet_bandwidth", None),
                        "BPSRead": getattr(it, "bps_read", None),
                        "BPSWrite": getattr(it, "bps_write", None),
                        "IOPSRead": getattr(it, "iops_read", None),
                        "IOPSWrite": getattr(it, "iops_write", None),
                        "InstanceId": getattr(it, "instance_id", None),
                    }
                    result.append(d)
            return result
        except Exception as e:
            # 直接抛给上层，由工具进行统一错误映射
            logger.error(f"ECS SDK 调用失败: {e}")
            raise
