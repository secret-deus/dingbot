"""
K8s Prometheus应用资源分析工具

基于Prometheus查询特定应用的Pod资源使用情况，
返回14天内CPU使用率/请求比例和内存使用率/请求比例的平均值。
"""

import asyncio
import aiohttp
import base64
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.tool_registry import MCPToolBase
from ..config import get_config


class K8sPrometheusAppMetricsTool(MCPToolBase):
    """
    K8s Prometheus应用资源分析工具
    
    功能：
    - 查询指定应用名的Pod资源使用情况
    - 返回14天内CPU使用率/请求比例的平均值
    - 返回14天内内存使用率/请求比例的平均值
    - 支持自定义namespace和时间范围
    """

    def __init__(self):
        """初始化Prometheus应用资源分析工具"""
        super().__init__(
            name="k8s-prometheus-app-metrics",
            description="【推荐】直接从Prometheus查询指定应用的实时CPU和内存利用率数据，提供最准确的14天平均使用率/请求比例分析"
        )
        
        self.config = get_config()
        
        # Prometheus配置
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "")
        self.access_key = os.getenv("PROMETHEUS_ACCESS_KEY")
        self.secret_key = os.getenv("PROMETHEUS_SECRET_KEY")
        self.auth_type = os.getenv("PROMETHEUS_AUTH_TYPE", "none")
        
        logger.info("K8s Prometheus应用资源分析工具已初始化")

    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "应用名称（Deployment名称），必填参数"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间，默认为'default'",
                        "default": "default"
                    },
                    "days": {
                        "type": "integer",
                        "description": "查询天数，默认14天",
                        "default": 14,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "step": {
                        "type": "string",
                        "description": "查询步长，默认'1h'",
                        "default": "1h"
                    },
                    "time_period": {
                        "type": "string",
                        "description": "时间周期模式：14d(14天平均) 或 1d(1天近期)",
                        "default": "14d",
                        "enum": ["14d", "1d"]
                    }
                },
                "required": ["app_name"]
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行Prometheus应用资源查询"""
        try:
            # 参数提取和验证
            app_name = arguments.get("app_name")
            if not app_name:
                return MCPCallToolResult.error("应用名称(app_name)是必填参数")
            
            namespace = arguments.get("namespace", "default")
            days = arguments.get("days", 14)
            step = arguments.get("step", "1h")
            time_period = arguments.get("time_period", "14d")
            
            # 根据时间周期调整参数
            is_day_mode = time_period == "1d"
            if is_day_mode and step == "1h":
                step = "10m"  # 1天模式使用更细粒度的步长
            
            # 确保step参数不为None或空字符串
            if not step or step == "None":
                step = "10m" if is_day_mode else "1h"
            
            if not self.prometheus_url:
                return MCPCallToolResult.error("未配置Prometheus URL，请设置PROMETHEUS_URL环境变量")
            
            logger.info(f"开始查询应用 {namespace}/{app_name} 的资源指标，查询{days}天数据 (模式: {time_period}, 步长: {step})")
            
            # 执行查询
            result = await self._query_app_metrics(app_name, namespace, days, step)
            
            return MCPCallToolResult.success(result)
            
        except Exception as e:
            logger.error(f"Prometheus应用资源查询失败: {e}")
            return MCPCallToolResult.error(f"查询失败: {str(e)}")

    async def _query_app_metrics(self, app_name: str, namespace: str, days: int, step: str) -> Dict[str, Any]:
        """查询应用资源指标"""
        
        # 创建HTTP会话
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # 设置认证
        if self.auth_type == "basic" and self.access_key and self.secret_key:
            credentials = f"{self.access_key}:{self.secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        elif self.auth_type == "bearer" and self.access_key:
            headers["Authorization"] = f"Bearer {self.access_key}"
        
        timeout = aiohttp.ClientTimeout(total=300)
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            
            # 构建查询语句
            queries = self._build_queries(app_name, namespace, days)
            
            # 执行查询
            results = {}
            for metric_name, query in queries.items():
                try:
                    # logger.debug(f"执行查询: {metric_name}")
                    
                    # 计算时间范围
                    end_time = datetime.now()
                    start_time = end_time - timedelta(days=days)
                    
                    # 构建查询参数
                    params = {
                        "query": query,
                        "start": int(start_time.timestamp()),
                        "end": int(end_time.timestamp()),
                        "step": step
                    }
                    
                    url = f"{self.prometheus_url}/api/v1/query_range"
                    
                    async with session.post(url, data=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 'success':
                                results[metric_name] = data.get('data', {}).get('result', [])
                                # logger.debug(f"查询 {metric_name} 成功，获得 {len(results[metric_name])} 条结果")
                                # 打印原始数据到日志
                                if results[metric_name]:
                                    # logger.info(f"📊 {metric_name} 原始数据 (前3条): {json.dumps(results[metric_name][:3], ensure_ascii=False, indent=2)}")
                                    pass
                                else:
                                    logger.warning(f"⚠️  {metric_name} 查询结果为空")
                            else:
                                error_msg = data.get('error', '未知错误')
                                logger.error(f"Prometheus查询 {metric_name} 失败: {error_msg}")
                                results[metric_name] = []
                        else:
                            response_text = await response.text()
                            logger.error(f"HTTP请求失败: {response.status}, 响应: {response_text}")
                            results[metric_name] = []
                            
                except Exception as e:
                    logger.error(f"执行查询 {metric_name} 时出错: {e}")
                    results[metric_name] = []
            
            # 处理查询结果
            return await self._process_results(results, app_name, namespace, days)

    def _build_queries(self, app_name: str, namespace: str, days: int) -> Dict[str, str]:
        """构建基于Grafana查询的Prometheus语句"""
        
        # 简化的CPU使用率查询，获取当前值
        cpu_usage_query = f'''
        rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",container!="",container!="POD"}}[5m])
        '''.strip()
        
        # 简化的内存使用率查询，获取当前值
        memory_usage_query = f'''
        container_memory_working_set_bytes{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",container!="",container!="POD"}}
        '''.strip()
        
        # CPU请求量查询（简单查询）
        cpu_requests_query = f'''
        kube_pod_container_resource_requests{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",resource="cpu"}}
        '''.strip()
        
        # 内存请求量查询（简单查询，原始字节）
        memory_requests_query = f'''
        kube_pod_container_resource_requests{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",resource="memory"}}
        '''.strip()
        
        return {
            "cpu_usage": cpu_usage_query,
            "memory_usage": memory_usage_query,
            "cpu_requests": cpu_requests_query,
            "memory_requests": memory_requests_query,
            # 新增：limits 查询
            "cpu_limits": f'kube_pod_container_resource_limits{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",resource="cpu"}}',
            "memory_limits": f'kube_pod_container_resource_limits{{namespace="{namespace}",pod=~"^{app_name}-[^-]+-.*",resource="memory"}}'
        }

    async def _process_results(self, results: Dict[str, List], app_name: str, namespace: str, days: int) -> Dict[str, Any]:
        """处理查询结果并计算平均值"""
        
        # 初始化结果结构
        processed_result = {
            "app_name": app_name,
            "namespace": namespace,
            "query_days": days,
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": {
                "cpu_utilization_avg": 0.0,
                "memory_utilization_avg": 0.0,
                "cpu_requests_avg": 0.0,
                "memory_requests_avg": 0.0,
                # 新增：limits 聚合
                "cpu_limits_avg": 0.0,
                "memory_limits_avg": 0.0
            },
            "pod_details": [],
            "summary": {
                "total_pods": 0,
                "data_points_cpu": 0,
                "data_points_memory": 0,
                "time_range": {
                    "start": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S"),
                    "end": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        }
        
        # 处理CPU使用量数据
        cpu_usage_values = []
        cpu_requests_values = []
        pod_cpu_data = {}
        
        for result in results.get("cpu_usage", []):
            metric = result.get('metric', {})
            values = result.get('values', [])
            
            pod_name = metric.get('pod', 'unknown')
            
            for timestamp, value in values:
                try:
                    cpu_usage = float(value)
                    if cpu_usage > 0:  # 过滤无效值
                        cpu_usage_values.append(cpu_usage)
                        
                        # 记录Pod级别的数据
                        if pod_name not in pod_cpu_data:
                            pod_cpu_data[pod_name] = []
                        pod_cpu_data[pod_name].append(cpu_usage)
                        
                except (ValueError, TypeError):
                    continue
        
        # 处理内存使用量数据
        memory_usage_values = []
        memory_requests_values = []
        pod_memory_data = {}
        
        for result in results.get("memory_usage", []):
            metric = result.get('metric', {})
            values = result.get('values', [])
            
            pod_name = metric.get('pod', 'unknown')
            
            for timestamp, value in values:
                try:
                    memory_usage = float(value)  # 内存使用量（字节）
                    memory_usage_gb = memory_usage / (1024**3)  # 转换为GB
                    if memory_usage_gb > 0:  # 过滤无效值
                        memory_usage_values.append(memory_usage_gb)
                        
                        # 记录Pod级别的数据
                        if pod_name not in pod_memory_data:
                            pod_memory_data[pod_name] = []
                        pod_memory_data[pod_name].append(memory_usage_gb)
                        
                except (ValueError, TypeError):
                    continue
        
        # 处理CPU请求量数据（统计每个值的出现次数，取最常见的值）
        from collections import Counter
        cpu_request_counter = Counter()
        cpu_limit_counter = Counter()
        for result in results.get("cpu_requests", []):
            values = result.get('values', [])
            if values:  # 只取第一个时间点的值
                timestamp, value = values[0]
                try:
                    cpu_req = float(value)
                    if cpu_req > 0:
                        cpu_request_counter[cpu_req] += 1
                except (ValueError, TypeError):
                    continue
        # CPU limits
        for result in results.get("cpu_limits", []):
            values = result.get('values', [])
            if values:
                timestamp, value = values[0]
                try:
                    cpu_lim = float(value)
                    if cpu_lim > 0:
                        cpu_limit_counter[cpu_lim] += 1
                except (ValueError, TypeError):
                    continue
        
        # 取出现次数最多的CPU请求值
        if cpu_request_counter:
            most_common_cpu = cpu_request_counter.most_common(1)[0][0]
            cpu_requests_values = [most_common_cpu]
        else:
            cpu_requests_values = []
        # logger.info(f"🔍 CPU请求统计: {dict(cpu_request_counter)}, 选择: {cpu_requests_values}")
        if cpu_limit_counter:
            most_common_cpu_lim = cpu_limit_counter.most_common(1)[0][0]
            cpu_limits_values = [most_common_cpu_lim]
        else:
            cpu_limits_values = []
        
        # 处理内存请求量数据（统计每个值的出现次数，取最常见的值，原始字节转换为GB）
        memory_request_counter = Counter()
        memory_limit_counter = Counter()
        for result in results.get("memory_requests", []):
            values = result.get('values', [])
            if values:  # 只取第一个时间点的值
                timestamp, value = values[0]
                try:
                    memory_req_bytes = float(value)  # 原始字节
                    memory_req_gb = memory_req_bytes / (1024**3)  # 直接转换为GB
                    if memory_req_gb > 0:
                        memory_request_counter[memory_req_gb] += 1
                except (ValueError, TypeError):
                    continue
        for result in results.get("memory_limits", []):
            values = result.get('values', [])
            if values:
                timestamp, value = values[0]
                try:
                    memory_lim_bytes = float(value)
                    memory_lim_gb = memory_lim_bytes / (1024**3)
                    if memory_lim_gb > 0:
                        memory_limit_counter[memory_lim_gb] += 1
                except (ValueError, TypeError):
                    continue
        
        # 取出现次数最多的内存请求值
        if memory_request_counter:
            most_common_memory = memory_request_counter.most_common(1)[0][0]
            memory_requests_values = [most_common_memory]
        else:
            memory_requests_values = []
        # logger.info(f"🔍 内存请求统计: {dict(memory_request_counter)}, 选择: {memory_requests_values}")
        if memory_limit_counter:
            most_common_memory_lim = memory_limit_counter.most_common(1)[0][0]
            memory_limits_values = [most_common_memory_lim]
        else:
            memory_limits_values = []
        

        
        if cpu_requests_values:
            cpu_req_avg = sum(cpu_requests_values) / len(cpu_requests_values)
            processed_result["metrics"]["cpu_requests_avg"] = round(cpu_req_avg, 6)
            # logger.info(f"💡 CPU请求量计算: {len(cpu_requests_values)}个数据点，平均值={cpu_req_avg:.4f}核")
        
        if memory_requests_values:
            memory_req_avg = sum(memory_requests_values) / len(memory_requests_values)
            processed_result["metrics"]["memory_requests_avg"] = round(memory_req_avg, 3)
            # logger.info(f"💡 内存请求量计算: {len(memory_requests_values)}个数据点，平均值={memory_req_avg:.4f}GB")
        if cpu_limits_values:
            cpu_lim_avg = sum(cpu_limits_values) / len(cpu_limits_values)
            processed_result["metrics"]["cpu_limits_avg"] = round(cpu_lim_avg, 6)
        if memory_limits_values:
            mem_lim_avg = sum(memory_limits_values) / len(memory_limits_values)
            processed_result["metrics"]["memory_limits_avg"] = round(mem_lim_avg, 3)
        
        # 计算利用率比例（使用量/请求量）
        if cpu_usage_values and cpu_requests_values:
            cpu_usage_avg = sum(cpu_usage_values) / len(cpu_usage_values)
            cpu_req_avg = sum(cpu_requests_values) / len(cpu_requests_values)
            cpu_utilization_ratio = cpu_usage_avg / cpu_req_avg if cpu_req_avg > 0 else 0
            processed_result["metrics"]["cpu_utilization_avg"] = round(cpu_utilization_ratio, 6)
            processed_result["metrics"]["cpu_utilization_percent"] = f"{cpu_utilization_ratio:.2%}"
            # logger.info(f"💡 CPU利用率: {cpu_usage_avg:.6f}核 / {cpu_req_avg:.2f}核 = {cpu_utilization_ratio:.2%}")
            # 若存在limits，计算使用/limits比例
            if cpu_limits_values:
                cpu_lim_avg = sum(cpu_limits_values) / len(cpu_limits_values)
                cpu_usage_limit_ratio = cpu_usage_avg / cpu_lim_avg if cpu_lim_avg > 0 else 0
                processed_result["metrics"]["cpu_utilization_vs_limit"] = round(cpu_usage_limit_ratio, 6)
        
        if memory_usage_values and memory_requests_values:
            memory_usage_avg = sum(memory_usage_values) / len(memory_usage_values) 
            memory_req_avg = sum(memory_requests_values) / len(memory_requests_values)
            memory_utilization_ratio = memory_usage_avg / memory_req_avg if memory_req_avg > 0 else 0
            processed_result["metrics"]["memory_utilization_avg"] = round(memory_utilization_ratio, 6)
            processed_result["metrics"]["memory_utilization_percent"] = f"{memory_utilization_ratio:.2%}"
            # logger.info(f"💡 内存利用率: {memory_usage_avg:.3f}GB / {memory_req_avg:.2f}GB = {memory_utilization_ratio:.2%}")
            if memory_limits_values:
                mem_lim_avg = sum(memory_limits_values) / len(memory_limits_values)
                mem_usage_limit_ratio = memory_usage_avg / mem_lim_avg if mem_lim_avg > 0 else 0
                processed_result["metrics"]["memory_utilization_vs_limit"] = round(mem_usage_limit_ratio, 6)
        
        # 生成Pod详细信息
        all_pods = set(list(pod_cpu_data.keys()) + list(pod_memory_data.keys()))
        for pod_name in all_pods:
            pod_cpu_utilization_ratio = 0.0
            pod_memory_utilization_ratio = 0.0
            
            # 计算Pod级别的CPU利用率（使用量/请求量）
            if pod_name in pod_cpu_data and cpu_requests_values:
                pod_cpu_usage_avg = sum(pod_cpu_data[pod_name]) / len(pod_cpu_data[pod_name])
                cpu_req_avg = sum(cpu_requests_values) / len(cpu_requests_values)
                pod_cpu_utilization_ratio = pod_cpu_usage_avg / cpu_req_avg if cpu_req_avg > 0 else 0
            
            # 计算Pod级别的内存利用率（使用量/请求量）
            if pod_name in pod_memory_data and memory_requests_values:
                pod_memory_usage_avg = sum(pod_memory_data[pod_name]) / len(pod_memory_data[pod_name])
                memory_req_avg = sum(memory_requests_values) / len(memory_requests_values)
                pod_memory_utilization_ratio = pod_memory_usage_avg / memory_req_avg if memory_req_avg > 0 else 0
            
            processed_result["pod_details"].append({
                "pod_name": pod_name,
                "cpu_utilization_avg": round(pod_cpu_utilization_ratio, 6),
                "memory_utilization_avg": round(pod_memory_utilization_ratio, 6),
                "cpu_utilization_percent": f"{pod_cpu_utilization_ratio:.2%}",
                "memory_utilization_percent": f"{pod_memory_utilization_ratio:.2%}",
                "cpu_data_points": len(pod_cpu_data.get(pod_name, [])),
                "memory_data_points": len(pod_memory_data.get(pod_name, []))
            })
        
        # 更新汇总信息
        processed_result["summary"]["total_pods"] = len(all_pods)
        processed_result["summary"]["data_points_cpu"] = len(cpu_usage_values)
        processed_result["summary"]["data_points_memory"] = len(memory_usage_values)
        
        # 添加使用率分析
        processed_result["analysis"] = {
            "cpu_utilization_status": self._analyze_utilization(processed_result["metrics"]["cpu_utilization_avg"]),
            "memory_utilization_status": self._analyze_utilization(processed_result["metrics"]["memory_utilization_avg"]),
            "recommendations": self._generate_recommendations(processed_result["metrics"])
        }
        
        # 添加数据完整性检查
        data_quality = {
            "has_cpu_data": len(cpu_usage_values) > 0,
            "has_memory_data": len(memory_usage_values) > 0,
            "has_request_data": len(cpu_requests_values) > 0 or len(memory_requests_values) > 0,
            "data_completeness": "complete" if (len(cpu_usage_values) > 0 and len(memory_usage_values) > 0) else "partial",
            "query_success": True
        }
        
        processed_result["data_quality"] = data_quality
        
        # 添加诊断信息
        processed_result["diagnostics"] = {
            "prometheus_queries_executed": 4,
            "cpu_usage_results": len(results.get("cpu_usage", [])),
            "memory_usage_results": len(results.get("memory_usage", [])),
            "cpu_requests_results": len(results.get("cpu_requests", [])),
            "memory_requests_results": len(results.get("memory_requests", [])),
            "total_data_points_found": len(cpu_usage_values) + len(memory_usage_values)
        }
        
        logger.info(f"应用 {namespace}/{app_name} 指标处理完成: CPU平均利用率={processed_result['metrics']['cpu_utilization_avg']:.2%}, 内存平均利用率={processed_result['metrics']['memory_utilization_avg']:.2%}")
        
        return processed_result

    def _analyze_utilization(self, utilization_ratio: float) -> str:
        """分析利用率状态"""
        if utilization_ratio == 0:
            return "无数据"
        elif utilization_ratio < 0.3:
            return "利用率过低"
        elif utilization_ratio < 0.6:
            return "利用率较低"
        elif utilization_ratio < 0.8:
            return "利用率正常"
        elif utilization_ratio < 1.0:
            return "利用率较高"
        else:
            return "利用率过高"

    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        cpu_ratio = metrics["cpu_utilization_avg"]
        memory_ratio = metrics["memory_utilization_avg"]
        
        if cpu_ratio < 0.3:
            recommendations.append(f"CPU利用率过低({cpu_ratio:.1%})，建议减少CPU请求量")
        elif cpu_ratio > 0.9:
            recommendations.append(f"CPU利用率过高({cpu_ratio:.1%})，建议增加CPU请求量或优化应用性能")
        
        if memory_ratio < 0.3:
            recommendations.append(f"内存利用率过低({memory_ratio:.1%})，建议减少内存请求量")
        elif memory_ratio > 0.9:
            recommendations.append(f"内存利用率过高({memory_ratio:.1%})，建议增加内存请求量")
        
        if not recommendations:
            recommendations.append("资源配置合理，无需调整")
        
        return recommendations
