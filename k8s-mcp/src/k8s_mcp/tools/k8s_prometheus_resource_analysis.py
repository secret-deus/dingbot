"""
Kubernetes Prometheus资源利用率分析工具

通过Prometheus接口获取14天内Pod的CPU和内存实际利用率，
识别资源利用率低于阈值的应用，用于资源优化建议。
"""

import asyncio
import aiohttp
import json
import re
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode
from loguru import logger

from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.tool_registry import MCPToolBase
from ..config import get_config


class K8sPrometheusResourceAnalysisTool(MCPToolBase):
    """
    Kubernetes Prometheus资源利用率分析工具
    
    功能：
    - 通过Prometheus API获取14天内Pod资源利用率数据
    - 按应用名称(selector=appname)分组统计
    - 计算CPU和内存的平均利用率(实际使用/request)
    - 识别利用率低于阈值的应用
    - 提供资源优化建议
    """

    def __init__(self):
        """初始化Prometheus资源分析工具"""
        super().__init__(
            name="k8s-prometheus-resource-analysis",
            description="通过Prometheus接口分析K8s集群Pod资源利用率，识别资源配置过高的应用"
        )
        
        self.config = get_config()
        self.prometheus_url = None
        self.session = None
        
        logger.info("Prometheus资源分析工具已初始化")

    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "prometheus_url": {
                        "type": "string",
                        "description": "Prometheus服务器URL，如果不提供则从环境变量PROMETHEUS_URL获取。例如: http://prometheus.monitoring.svc.cluster.local:9090 或阿里云ARMS Prometheus URL"
                    },
                    "access_key": {
                        "type": "string",
                        "description": "阿里云AccessKey，如果不提供则从环境变量PROMETHEUS_ACCESS_KEY获取"
                    },
                    "secret_key": {
                        "type": "string",
                        "description": "阿里云SecretKey，如果不提供则从环境变量PROMETHEUS_SECRET_KEY获取"
                    },
                    "auth_type": {
                        "type": "string",
                        "description": "认证类型：none(无认证)、basic(Basic认证，用于阿里云)、bearer(Bearer Token)",
                        "enum": ["none", "basic", "bearer"],
                        "default": "none"
                    },
                    "days": {
                        "type": "integer",
                        "description": "分析天数，默认14天",
                        "default": 14,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "cpu_threshold": {
                        "type": "number",
                        "description": "CPU利用率阈值(百分比)，低于此值的应用将被标记，默认60%",
                        "default": 60.0,
                        "minimum": 10.0,
                        "maximum": 95.0
                    },
                    "memory_threshold": {
                        "type": "number",
                        "description": "内存利用率阈值(百分比)，低于此值的应用将被标记，默认60%",
                        "default": 60.0,
                        "minimum": 10.0,
                        "maximum": 95.0
                    },
                    "namespace_filter": {
                        "type": "string",
                        "description": "命名空间过滤器，支持正则表达式，例如: test|prod"
                    },
                    "app_selector": {
                        "type": "string",
                        "description": "应用选择器标签名，默认为app",
                        "default": "app"
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "指定要分析的Deployment名称，支持正则表达式"
                    },
                    "analysis_mode": {
                        "type": "string",
                        "description": "分析模式：deployment(按Deployment分析)或app(按应用标签分析)",
                        "enum": ["deployment", "app"],
                        "default": "app"
                    },
                    "custom_queries": {
                        "type": "object",
                        "description": "自定义Prometheus查询语句",
                        "properties": {
                            "cpu_usage_query": {
                                "type": "string",
                                "description": "CPU使用率查询语句"
                            },
                            "memory_usage_query": {
                                "type": "string",
                                "description": "内存使用率查询语句"
                            },
                            "cpu_request_query": {
                                "type": "string",
                                "description": "CPU请求量查询语句"
                            },
                            "memory_request_query": {
                                "type": "string",
                                "description": "内存请求量查询语句"
                            }
                        }
                    }
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行Prometheus资源利用率分析"""
        try:
            # 参数验证和提取
            self.prometheus_url = arguments.get("prometheus_url") or os.getenv("PROMETHEUS_URL")
            if not self.prometheus_url:
                return MCPCallToolResult.error("prometheus_url参数是必需的，请在参数中提供或设置环境变量PROMETHEUS_URL")
            
            days = arguments.get("days", 14)
            cpu_threshold = arguments.get("cpu_threshold", 60.0)
            memory_threshold = arguments.get("memory_threshold", 60.0)
            namespace_filter = arguments.get("namespace_filter")
            app_selector = arguments.get("app_selector", "app")
            deployment_name = arguments.get("deployment_name")
            analysis_mode = arguments.get("analysis_mode", "app")
            custom_queries = arguments.get("custom_queries", {})
            
            # 认证相关参数
            access_key = arguments.get("access_key") or os.getenv("PROMETHEUS_ACCESS_KEY")
            secret_key = arguments.get("secret_key") or os.getenv("PROMETHEUS_SECRET_KEY")
            auth_type = arguments.get("auth_type", "none")
            
            logger.info(f"开始分析{days}天内的资源利用率，CPU阈值: {cpu_threshold}%, 内存阈值: {memory_threshold}%")
            
            # 准备认证头
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            if auth_type == "basic" and access_key and secret_key:
                # 阿里云Basic认证
                credentials = f"{access_key}:{secret_key}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded_credentials}"
                logger.info("使用Basic认证(阿里云ARMS)")
            elif auth_type == "bearer" and access_key:
                # Bearer Token认证
                headers["Authorization"] = f"Bearer {access_key}"
                logger.info("使用Bearer Token认证")
            else:
                logger.info("使用无认证模式")
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300),  # 5分钟超时
                headers=headers
            )
            
            try:
                # 获取时间范围
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                # 构建Prometheus查询
                queries = self._build_prometheus_queries(
                    start_time, end_time, namespace_filter, app_selector, 
                    deployment_name, analysis_mode, custom_queries
                )
                
                # 执行查询并获取数据
                raw_data = await self._execute_prometheus_queries(queries)
                
                # 分析数据并生成报告
                analysis_result = await self._analyze_resource_utilization(
                    raw_data, cpu_threshold, memory_threshold, days
                )
                
                return MCPCallToolResult.success(analysis_result)
                
            finally:
                if self.session:
                    await self.session.close()
                    
        except Exception as e:
            logger.error(f"Prometheus资源利用率分析失败: {e}")
            if self.session:
                await self.session.close()
            return MCPCallToolResult.error(f"分析失败: {str(e)}")

    def _build_prometheus_queries(
        self, 
        start_time: datetime, 
        end_time: datetime,
        namespace_filter: Optional[str],
        app_selector: str,
        deployment_name: Optional[str],
        analysis_mode: str,
        custom_queries: Dict[str, str]
    ) -> Dict[str, str]:
        """构建Prometheus查询语句"""
        
        # 根据分析模式选择查询方式
        if analysis_mode == "deployment":
            return self._build_deployment_queries(namespace_filter, deployment_name, custom_queries)
        else:
            return self._build_app_queries(start_time, end_time, namespace_filter, app_selector, custom_queries)
    
    def _build_deployment_queries(
        self, 
        namespace_filter: Optional[str], 
        deployment_name: Optional[str],
        custom_queries: Dict[str, str]
    ) -> Dict[str, str]:
        """构建基于Deployment的精确查询语句"""
        
        # 构建命名空间条件
        namespace_condition = f'namespace="{namespace_filter}"' if namespace_filter else 'namespace!=""'
        
        # 构建Deployment名称条件
        deployment_condition = f'owner_name=~"{deployment_name}"' if deployment_name else 'owner_name!=""'
        
        # 基于用户提供的精确查询语句
        default_queries = {
            # 内存使用率 - 基于用户提供的查询语句
            "memory_utilization": f'''
                label_replace(
                  max(kube_pod_info{{{namespace_condition},created_by_kind="ReplicaSet", pod_ip!=""}}) by (created_by_name, uid, pod, pod_ip, node),
                  "replicaset",
                  "$1",
                  "created_by_name",
                  "(.+)"
                ) * on(replicaset) group_left() max(kube_replicaset_owner{{{namespace_condition},{deployment_condition},owner_kind="Deployment"}}) by (replicaset)
                * on(pod) group_right() max by(container, pod) (container_memory_working_set_bytes{{{namespace_condition}, container!="", image!="", container!="POD"}})/max by(container, pod) (kube_pod_container_resource_requests{{resource="memory", {namespace_condition}}})
            '''.strip(),
            
            # CPU使用率 - 对应的CPU查询
            "cpu_utilization": f'''
                label_replace(
                  max(kube_pod_info{{{namespace_condition},created_by_kind="ReplicaSet", pod_ip!=""}}) by (created_by_name, uid, pod, pod_ip, node),
                  "replicaset",
                  "$1",
                  "created_by_name",
                  "(.+)"
                ) * on(replicaset) group_left() max(kube_replicaset_owner{{{namespace_condition},{deployment_condition},owner_kind="Deployment"}}) by (replicaset)
                * on(pod) group_right() rate(container_cpu_usage_seconds_total{{{namespace_condition}, container!="", image!="", container!="POD"}}[5m])/max by(container, pod) (kube_pod_container_resource_requests{{resource="cpu", {namespace_condition}}})
            '''.strip(),
            
            # 内存请求量
            "memory_requests": f'''
                label_replace(
                  max(kube_pod_info{{{namespace_condition},created_by_kind="ReplicaSet", pod_ip!=""}}) by (created_by_name, uid, pod, pod_ip, node),
                  "replicaset",
                  "$1",
                  "created_by_name",
                  "(.+)"
                ) * on(replicaset) group_left() max(kube_replicaset_owner{{{namespace_condition},{deployment_condition},owner_kind="Deployment"}}) by (replicaset)
                * on(pod) group_right() max by(container, pod) (kube_pod_container_resource_requests{{resource="memory", {namespace_condition}}}) / 1024 / 1024 / 1024
            '''.strip(),
            
            # CPU请求量
            "cpu_requests": f'''
                label_replace(
                  max(kube_pod_info{{{namespace_condition},created_by_kind="ReplicaSet", pod_ip!=""}}) by (created_by_name, uid, pod, pod_ip, node),
                  "replicaset",
                  "$1",
                  "created_by_name",
                  "(.+)"
                ) * on(replicaset) group_left() max(kube_replicaset_owner{{{namespace_condition},{deployment_condition},owner_kind="Deployment"}}) by (replicaset)
                * on(pod) group_right() max by(container, pod) (kube_pod_container_resource_requests{{resource="cpu", {namespace_condition}}})
            '''.strip()
        }
        
        # 使用自定义查询覆盖默认查询
        queries = default_queries.copy()
        if custom_queries.get("memory_usage_query"):
            queries["memory_utilization"] = custom_queries["memory_usage_query"]
        if custom_queries.get("cpu_usage_query"):
            queries["cpu_utilization"] = custom_queries["cpu_usage_query"]
        if custom_queries.get("memory_request_query"):
            queries["memory_requests"] = custom_queries["memory_request_query"]
        if custom_queries.get("cpu_request_query"):
            queries["cpu_requests"] = custom_queries["cpu_request_query"]
        
        return queries
    
    def _build_app_queries(
        self, 
        start_time: datetime, 
        end_time: datetime,
        namespace_filter: Optional[str],
        app_selector: str,
        custom_queries: Dict[str, str]
    ) -> Dict[str, str]:
        """构建基于应用标签的传统查询语句"""
        
        # 构建命名空间过滤条件
        namespace_condition = ""
        if namespace_filter:
            namespace_condition = f',namespace=~"{namespace_filter}"'
        
        # 默认查询语句
        default_queries = {
            # CPU使用率 - 14天平均值
            "cpu_usage": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, {app_selector}) (
                            rate(container_cpu_usage_seconds_total{{container!="POI",container!="",{app_selector}!=""{namespace_condition}}}[5m])
                        )
                    )[{(end_time - start_time).days}d:5m]
                ) * 100
            '''.strip(),
            
            # CPU请求量
            "cpu_requests": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, {app_selector}) (
                            kube_pod_container_resource_requests{{resource="cpu",{app_selector}!=""{namespace_condition}}}
                        )
                    )[{(end_time - start_time).days}d:5m]
                ) * 100
            '''.strip(),
            
            # 内存使用率 - 14天平均值
            "memory_usage": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, {app_selector}) (
                            container_memory_working_set_bytes{{container!="POI",container!="",{app_selector}!=""{namespace_condition}}}
                        )
                    )[{(end_time - start_time).days}d:5m]
                ) / 1024 / 1024 / 1024
            '''.strip(),
            
            # 内存请求量
            "memory_requests": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, {app_selector}) (
                            kube_pod_container_resource_requests{{resource="memory",{app_selector}!=""{namespace_condition}}}
                        )
                    )[{(end_time - start_time).days}d:5m]
                ) / 1024 / 1024 / 1024
            '''.strip()
        }
        
        # 使用自定义查询覆盖默认查询
        queries = default_queries.copy()
        if custom_queries.get("cpu_usage_query"):
            queries["cpu_usage"] = custom_queries["cpu_usage_query"]
        if custom_queries.get("memory_usage_query"):
            queries["memory_usage"] = custom_queries["memory_usage_query"]
        if custom_queries.get("cpu_request_query"):
            queries["cpu_requests"] = custom_queries["cpu_request_query"]
        if custom_queries.get("memory_request_query"):
            queries["memory_requests"] = custom_queries["memory_request_query"]
        
        return queries

    async def _execute_prometheus_queries(self, queries: Dict[str, str]) -> Dict[str, Any]:
        """执行Prometheus查询"""
        results = {}
        
        for query_name, query in queries.items():
            try:
                logger.info(f"执行Prometheus查询: {query_name}")
                
                # 构建查询请求体 (阿里云ARMS格式)
                current_time = int(datetime.now().timestamp())
                request_body = {
                    "query": query,
                    "time": str(current_time),
                    "timeout": "30000"  # 30秒超时
                }
                
                # API端点URL
                url = f"{self.prometheus_url}/api/v1/query"
                
                logger.debug(f"请求URL: {url}")
                logger.debug(f"请求体: {json.dumps(request_body, indent=2)}")
                
                # 执行HTTP POST请求 (阿里云ARMS使用POST)
                async with self.session.post(url, json=request_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            results[query_name] = data.get('data', {}).get('result', [])
                            logger.info(f"查询 {query_name} 成功，获得 {len(results[query_name])} 条结果")
                        else:
                            error_msg = data.get('error', '未知错误')
                            logger.error(f"Prometheus查询 {query_name} 失败: {error_msg}")
                            results[query_name] = []
                    else:
                        response_text = await response.text()
                        logger.error(f"HTTP请求失败: {response.status}, 响应: {response_text}")
                        results[query_name] = []
                        
            except Exception as e:
                logger.error(f"执行查询 {query_name} 时出错: {e}")
                results[query_name] = []
        
        return results

    async def _analyze_resource_utilization(
        self, 
        raw_data: Dict[str, Any], 
        cpu_threshold: float, 
        memory_threshold: float,
        days: int
    ) -> Dict[str, Any]:
        """分析资源利用率数据"""
        
        analysis_result = {
            "analysis_period": {
                "days": days,
                "start_time": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_time": datetime.now().isoformat()
            },
            "thresholds": {
                "cpu_threshold_percent": cpu_threshold,
                "memory_threshold_percent": memory_threshold
            },
            "summary": {
                "total_applications": 0,
                "low_cpu_utilization_apps": 0,
                "low_memory_utilization_apps": 0,
                "both_low_utilization_apps": 0
            },
            "applications": [],
            "recommendations": []
        }
        
        # 解析数据并按应用分组
        app_data = self._group_by_application(raw_data)
        
        analysis_result["summary"]["total_applications"] = len(app_data)
        
        # 分析每个应用的资源利用率
        for app_name, metrics in app_data.items():
            app_analysis = self._analyze_single_application(
                app_name, metrics, cpu_threshold, memory_threshold
            )
            analysis_result["applications"].append(app_analysis)
            
            # 更新统计信息
            if app_analysis["cpu_utilization_percent"] < cpu_threshold:
                analysis_result["summary"]["low_cpu_utilization_apps"] += 1
            if app_analysis["memory_utilization_percent"] < memory_threshold:
                analysis_result["summary"]["low_memory_utilization_apps"] += 1
            if (app_analysis["cpu_utilization_percent"] < cpu_threshold and 
                app_analysis["memory_utilization_percent"] < memory_threshold):
                analysis_result["summary"]["both_low_utilization_apps"] += 1
        
        # 生成优化建议
        analysis_result["recommendations"] = self._generate_recommendations(
            analysis_result["applications"], cpu_threshold, memory_threshold
        )
        
        # 按利用率排序
        analysis_result["applications"].sort(
            key=lambda x: (x["cpu_utilization_percent"] + x["memory_utilization_percent"]) / 2
        )
        
        return analysis_result

    def _group_by_application(self, raw_data: Dict[str, Any]) -> Dict[str, Dict]:
        """按应用名称分组数据"""
        app_data = {}
        
        # 处理每种类型的指标数据
        for metric_type, results in raw_data.items():
            for result in results:
                metric = result.get('metric', {})
                app_name = metric.get('app', 'unknown')
                namespace = metric.get('namespace', 'default')
                
                # 创建应用键
                app_key = f"{namespace}/{app_name}"
                
                if app_key not in app_data:
                    app_data[app_key] = {
                        'app_name': app_name,
                        'namespace': namespace,
                        'cpu_usage': 0,
                        'cpu_requests': 0,
                        'memory_usage': 0,
                        'memory_requests': 0,
                        'pod_count': 0
                    }
                
                # 提取指标值
                value = float(result.get('value', [0, '0'])[1])
                
                if metric_type == 'cpu_usage':
                    app_data[app_key]['cpu_usage'] = value
                elif metric_type == 'cpu_requests':
                    app_data[app_key]['cpu_requests'] = value
                elif metric_type == 'memory_usage':
                    app_data[app_key]['memory_usage'] = value
                elif metric_type == 'memory_requests':
                    app_data[app_key]['memory_requests'] = value
        
        return app_data

    def _analyze_single_application(
        self, 
        app_name: str, 
        metrics: Dict, 
        cpu_threshold: float, 
        memory_threshold: float
    ) -> Dict[str, Any]:
        """分析单个应用的资源利用率"""
        
        # 计算利用率
        cpu_utilization = 0
        if metrics['cpu_requests'] > 0:
            cpu_utilization = (metrics['cpu_usage'] / metrics['cpu_requests']) * 100
        
        memory_utilization = 0
        if metrics['memory_requests'] > 0:
            memory_utilization = (metrics['memory_usage'] / metrics['memory_requests']) * 100
        
        # 判断是否需要优化
        needs_cpu_optimization = cpu_utilization < cpu_threshold
        needs_memory_optimization = memory_utilization < memory_threshold
        
        return {
            "app_name": metrics['app_name'],
            "namespace": metrics['namespace'],
            "cpu_usage_cores": round(metrics['cpu_usage'], 3),
            "cpu_requests_cores": round(metrics['cpu_requests'], 3),
            "cpu_utilization_percent": round(cpu_utilization, 2),
            "memory_usage_gb": round(metrics['memory_usage'], 3),
            "memory_requests_gb": round(metrics['memory_requests'], 3),
            "memory_utilization_percent": round(memory_utilization, 2),
            "needs_optimization": {
                "cpu": needs_cpu_optimization,
                "memory": needs_memory_optimization,
                "overall": needs_cpu_optimization or needs_memory_optimization
            },
            "optimization_potential": {
                "cpu_reduction_percent": max(0, cpu_threshold - cpu_utilization) if needs_cpu_optimization else 0,
                "memory_reduction_percent": max(0, memory_threshold - memory_utilization) if needs_memory_optimization else 0
            }
        }

    def _generate_recommendations(
        self, 
        applications: List[Dict], 
        cpu_threshold: float, 
        memory_threshold: float
    ) -> List[Dict[str, Any]]:
        """生成资源优化建议"""
        recommendations = []
        
        # 找出需要优化的应用
        apps_needing_optimization = [
            app for app in applications 
            if app["needs_optimization"]["overall"]
        ]
        
        if not apps_needing_optimization:
            recommendations.append({
                "type": "info",
                "title": "资源配置良好",
                "description": "所有应用的资源利用率都在合理范围内，无需优化。"
            })
            return recommendations
        
        # CPU优化建议
        cpu_apps = [app for app in apps_needing_optimization if app["needs_optimization"]["cpu"]]
        if cpu_apps:
            total_cpu_waste = sum(
                app["cpu_requests_cores"] * (app["optimization_potential"]["cpu_reduction_percent"] / 100)
                for app in cpu_apps
            )
            recommendations.append({
                "type": "cpu_optimization",
                "title": f"CPU资源优化建议 - 可节省约{total_cpu_waste:.2f}核",
                "description": f"发现{len(cpu_apps)}个应用的CPU利用率低于{cpu_threshold}%",
                "applications": [
                    {
                        "name": f"{app['namespace']}/{app['app_name']}",
                        "current_request": f"{app['cpu_requests_cores']}核",
                        "utilization": f"{app['cpu_utilization_percent']}%",
                        "suggested_request": f"{app['cpu_requests_cores'] * (app['cpu_utilization_percent'] / cpu_threshold):.3f}核"
                    }
                    for app in cpu_apps[:10]  # 只显示前10个
                ]
            })
        
        # 内存优化建议
        memory_apps = [app for app in apps_needing_optimization if app["needs_optimization"]["memory"]]
        if memory_apps:
            total_memory_waste = sum(
                app["memory_requests_gb"] * (app["optimization_potential"]["memory_reduction_percent"] / 100)
                for app in memory_apps
            )
            recommendations.append({
                "type": "memory_optimization",
                "title": f"内存资源优化建议 - 可节省约{total_memory_waste:.2f}GB",
                "description": f"发现{len(memory_apps)}个应用的内存利用率低于{memory_threshold}%",
                "applications": [
                    {
                        "name": f"{app['namespace']}/{app['app_name']}",
                        "current_request": f"{app['memory_requests_gb']:.2f}GB",
                        "utilization": f"{app['memory_utilization_percent']}%",
                        "suggested_request": f"{app['memory_requests_gb'] * (app['memory_utilization_percent'] / memory_threshold):.2f}GB"
                    }
                    for app in memory_apps[:10]  # 只显示前10个
                ]
            })
        
        # 综合优化建议
        both_apps = [app for app in apps_needing_optimization if 
                    app["needs_optimization"]["cpu"] and app["needs_optimization"]["memory"]]
        if both_apps:
            recommendations.append({
                "type": "comprehensive_optimization",
                "title": f"综合优化建议 - {len(both_apps)}个应用CPU和内存都可优化",
                "description": "这些应用的CPU和内存利用率都较低，建议优先优化",
                "applications": [
                    f"{app['namespace']}/{app['app_name']}"
                    for app in both_apps[:20]
                ]
            })
        
        return recommendations
