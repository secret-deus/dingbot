"""
K8s集群资源监控工具

获取集群的CPU和内存使用情况，包括：
- 节点级别的资源使用统计
- 集群整体资源使用情况
- 资源使用率和可用性分析
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from loguru import logger

from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.tool_registry import MCPToolBase
from ..k8s_client import K8sClient
from ..config import get_config


class K8sGetClusterMetricsTool(MCPToolBase):
    """K8s集群资源监控工具
    
    获取集群的CPU和内存使用情况，提供资源监控数据
    """

    def __init__(self):
        super().__init__(
            name="k8s-get-cluster-metrics",
            description="获取K8s集群的CPU和内存使用情况，包括节点级别和集群整体的资源监控数据"
        )
        self.config = get_config()
        self.k8s_client = None

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "include_node_details": {
                        "type": "boolean",
                        "description": "是否包含每个节点的详细资源使用情况",
                        "default": True
                    },
                    "include_pod_metrics": {
                        "type": "boolean", 
                        "description": "是否包含Pod级别的资源使用统计",
                        "default": False
                    }
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()

            include_node_details = arguments.get("include_node_details", True)
            include_pod_metrics = arguments.get("include_pod_metrics", False)

            # 获取节点信息
            nodes_data = await self.k8s_client.get_nodes()
            
            # 获取所有命名空间的Pod信息用于计算实际使用量
            pods_data = await self.k8s_client.get_pods(namespace="all")

            # 计算集群资源监控数据
            metrics_data = await self._calculate_cluster_metrics(
                nodes_data, pods_data, include_node_details, include_pod_metrics
            )

            return MCPCallToolResult.success(metrics_data)

        except Exception as e:
            logger.error(f"获取集群资源监控数据失败: {e}")
            return MCPCallToolResult.error(f"获取集群资源监控数据失败: {str(e)}")

    async def _calculate_cluster_metrics(
        self, 
        nodes_data: Dict[str, Any], 
        pods_data: Dict[str, Any],
        include_node_details: bool,
        include_pod_metrics: bool
    ) -> Dict[str, Any]:
        """计算集群资源监控数据"""
        
        cluster_metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "cluster_summary": {},
            "resource_utilization": {},
            "capacity_analysis": {}
        }

        # 解析节点数据
        nodes = nodes_data.get("items", [])
        total_nodes = len(nodes)
        ready_nodes = 0
        
        # 集群总容量
        total_cpu_capacity = 0
        total_memory_capacity = 0  # 以字节为单位
        total_cpu_allocatable = 0
        total_memory_allocatable = 0

        # 节点详细信息
        node_details = []

        for node in nodes:
            node_name = node.get("name", "unknown")
            node_status = node.get("status", "NotReady")
            node_ready = node_status == "Ready"
            
            if node_ready:
                ready_nodes += 1

            # 解析容量信息
            capacity = node.get("capacity", {})
            allocatable = node.get("allocatable", {})
            
            node_cpu_capacity = self._parse_cpu_value(capacity.get("cpu", "0"))
            node_memory_capacity = self._parse_memory_value(capacity.get("memory", "0"))
            node_cpu_allocatable = self._parse_cpu_value(allocatable.get("cpu", "0"))
            node_memory_allocatable = self._parse_memory_value(allocatable.get("memory", "0"))

            total_cpu_capacity += node_cpu_capacity
            total_memory_capacity += node_memory_capacity
            total_cpu_allocatable += node_cpu_allocatable
            total_memory_allocatable += node_memory_allocatable

            if include_node_details:
                node_detail = {
                    "name": node_name,
                    "ready": node_ready,
                    "capacity": {
                        "cpu_cores": node_cpu_capacity,
                        "memory_bytes": node_memory_capacity,
                        "memory_gb": round(node_memory_capacity / (1024**3), 2)
                    },
                    "allocatable": {
                        "cpu_cores": node_cpu_allocatable,
                        "memory_bytes": node_memory_allocatable,
                        "memory_gb": round(node_memory_allocatable / (1024**3), 2)
                    }
                }
                node_details.append(node_detail)

        # 计算Pod资源请求总量
        pods = pods_data.get("items", [])
        total_cpu_requests = 0
        total_memory_requests = 0
        running_pods = 0

        pod_metrics = []

        for pod in pods:
            pod_name = pod.get("name", "unknown")
            pod_namespace = pod.get("namespace", "default")
            pod_phase = pod.get("phase", "unknown")
            
            if pod_phase == "Running":
                running_pods += 1

            # 解析Pod的资源请求
            containers = pod.get("containers", [])
            pod_cpu_requests = 0
            pod_memory_requests = 0

            for container in containers:
                resources = container.get("resources", {})
                requests = resources.get("requests", {})
                
                cpu_request = self._parse_cpu_value(requests.get("cpu", "0"))
                memory_request = self._parse_memory_value(requests.get("memory", "0"))
                
                pod_cpu_requests += cpu_request
                pod_memory_requests += memory_request

            total_cpu_requests += pod_cpu_requests
            total_memory_requests += pod_memory_requests

            if include_pod_metrics and pod_phase == "Running":
                pod_metric = {
                    "name": pod_name,
                    "namespace": pod_namespace,
                    "phase": pod_phase,
                    "cpu_requests": pod_cpu_requests,
                    "cpu_requests_cores": round(pod_cpu_requests, 3),
                    "memory_requests": pod_memory_requests,
                    "memory_requests_mb": round(pod_memory_requests / (1024**2), 2),
                    "memory_requests_gb": round(pod_memory_requests / (1024**3), 3)
                }
                pod_metrics.append(pod_metric)

        # 计算使用率
        cpu_utilization = (total_cpu_requests / total_cpu_allocatable * 100) if total_cpu_allocatable > 0 else 0
        memory_utilization = (total_memory_requests / total_memory_allocatable * 100) if total_memory_allocatable > 0 else 0

        # 填充集群摘要
        cluster_metrics["cluster_summary"] = {
            "total_nodes": total_nodes,
            "ready_nodes": ready_nodes,
            "running_pods": running_pods,
            "total_pods": len(pods)
        }

        # 填充资源利用率
        cluster_metrics["resource_utilization"] = {
            "cpu": {
                "total_capacity_cores": round(total_cpu_capacity, 2),
                "total_allocatable_cores": round(total_cpu_allocatable, 2),
                "total_requests_cores": round(total_cpu_requests, 2),
                "utilization_percentage": round(cpu_utilization, 2),
                "available_cores": round(total_cpu_allocatable - total_cpu_requests, 2)
            },
            "memory": {
                "total_capacity_gb": round(total_memory_capacity / (1024**3), 2),
                "total_allocatable_gb": round(total_memory_allocatable / (1024**3), 2),
                "total_requests_gb": round(total_memory_requests / (1024**3), 2),
                "utilization_percentage": round(memory_utilization, 2),
                "available_gb": round((total_memory_allocatable - total_memory_requests) / (1024**3), 2)
            }
        }

        # 容量分析
        cluster_metrics["capacity_analysis"] = {
            "cpu_pressure": "high" if cpu_utilization > 80 else "medium" if cpu_utilization > 60 else "low",
            "memory_pressure": "high" if memory_utilization > 80 else "medium" if memory_utilization > 60 else "low",
            "overall_health": "good" if cpu_utilization < 70 and memory_utilization < 70 else "warning" if cpu_utilization < 90 and memory_utilization < 90 else "critical"
        }

        # 添加节点详细信息
        if include_node_details:
            cluster_metrics["node_details"] = node_details

        # 添加Pod指标
        if include_pod_metrics:
            cluster_metrics["pod_metrics"] = pod_metrics[:20]  # 限制返回前20个Pod

        return cluster_metrics

    def _parse_cpu_value(self, cpu_str: str) -> float:
        """解析CPU值，返回核心数"""
        if not cpu_str or cpu_str == "unknown":
            return 0.0
        
        cpu_str = str(cpu_str).strip()
        
        # 处理millicores (例如: 100m = 0.1 cores)
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        
        # 处理纯数字 (例如: 2 = 2 cores)
        try:
            return float(cpu_str)
        except ValueError:
            logger.warning(f"无法解析CPU值: {cpu_str}")
            return 0.0

    def _parse_memory_value(self, memory_str: str) -> int:
        """解析内存值，返回字节数"""
        if not memory_str or memory_str == "unknown":
            return 0
        
        memory_str = str(memory_str).strip()
        
        # 使用正则表达式解析内存值，支持更多单位
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTPE]i?|[kmgtpe])?$', memory_str)
        if not match:
            logger.warning(f"无法解析内存值: {memory_str}")
            return 0
        
        value = float(match.group(1))
        unit = match.group(2) or ""
        
        # 转换为字节
        multipliers = {
            "": 1,
            "K": 1000, "Ki": 1024, "k": 1000,
            "M": 1000**2, "Mi": 1024**2, "m": 1000**2,
            "G": 1000**3, "Gi": 1024**3, "g": 1000**3,
            "T": 1000**4, "Ti": 1024**4, "t": 1000**4,
            "P": 1000**5, "Pi": 1024**5, "p": 1000**5,
            "E": 1000**6, "Ei": 1024**6, "e": 1000**6
        }
        
        multiplier = multipliers.get(unit, 1)
        return int(value * multiplier)
