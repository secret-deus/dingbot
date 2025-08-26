"""
K8s资源指标聚合器

定期从Prometheus获取资源使用率数据，计算14天平均值，
并将结果存储到知识图谱中，提供高效的指标查询能力。
"""

import asyncio
import aiohttp
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
from dataclasses import dataclass

from .k8s_graph import K8sKnowledgeGraph, get_shared_knowledge_graph
from ..config import get_config


@dataclass
class MetricsConfig:
    """指标聚合配置"""
    prometheus_url: str
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    auth_type: str = "none"  # none, basic, bearer
    aggregation_interval: int = 3600  # 聚合间隔（秒），默认1小时
    metrics_retention_days: int = 30  # 指标保留天数
    analysis_days: int = 14  # 分析天数
    cpu_threshold: float = 60.0  # CPU利用率阈值
    memory_threshold: float = 60.0  # 内存利用率阈值


class K8sMetricsAggregator:
    """K8s资源指标聚合器
    
    功能：
    - 定期从Prometheus获取资源使用率数据
    - 计算14天内CPU和内存平均利用率
    - 将聚合结果存储到知识图谱
    - 提供指标查询和分析能力
    """
    
    def __init__(self, config: MetricsConfig, knowledge_graph: K8sKnowledgeGraph = None):
        """初始化指标聚合器
        
        Args:
            config: 指标聚合配置
            knowledge_graph: 知识图谱实例，默认使用共享实例
        """
        self.config = config
        self.kg = knowledge_graph or get_shared_knowledge_graph()
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        self.aggregation_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            "aggregations_completed": 0,
            "last_aggregation_time": 0,
            "resources_processed": 0,
            "errors_count": 0,
            "avg_processing_time": 0.0
        }
        
        logger.info("K8s指标聚合器初始化完成")
    
    async def start(self):
        """启动指标聚合服务"""
        if self.is_running:
            logger.warning("指标聚合器已在运行")
            return
        
        self.is_running = True
        
        # 创建HTTP会话
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.config.auth_type == "basic" and self.config.access_key and self.config.secret_key:
            credentials = f"{self.config.access_key}:{self.config.secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        elif self.config.auth_type == "bearer" and self.config.access_key:
            headers["Authorization"] = f"Bearer {self.config.access_key}"
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            headers=headers
        )
        
        # 启动聚合任务
        self.aggregation_task = asyncio.create_task(self._aggregation_loop())
        logger.info("指标聚合服务已启动")
    
    async def stop(self):
        """停止指标聚合服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.aggregation_task:
            self.aggregation_task.cancel()
            try:
                await self.aggregation_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
        
        logger.info("指标聚合服务已停止")
    
    async def _aggregation_loop(self):
        """指标聚合主循环"""
        while self.is_running:
            try:
                start_time = datetime.now()
                
                # 执行指标聚合
                await self._aggregate_metrics()
                
                # 更新统计信息
                processing_time = (datetime.now() - start_time).total_seconds()
                self.stats["aggregations_completed"] += 1
                self.stats["last_aggregation_time"] = start_time.timestamp()
                self.stats["avg_processing_time"] = (
                    (self.stats["avg_processing_time"] * (self.stats["aggregations_completed"] - 1) + processing_time)
                    / self.stats["aggregations_completed"]
                )
                
                logger.info(f"指标聚合完成，耗时: {processing_time:.2f}秒")
                
                # 等待下次聚合
                await asyncio.sleep(self.config.aggregation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标聚合失败: {e}")
                self.stats["errors_count"] += 1
                await asyncio.sleep(60)  # 出错后等待1分钟
    
    async def _aggregate_metrics(self):
        """执行指标聚合"""
        logger.info("开始执行指标聚合")
        
        # 获取时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.config.analysis_days)
        
        # 构建Prometheus查询
        queries = self._build_aggregation_queries()
        
        # 执行查询
        raw_data = await self._execute_prometheus_queries(queries)
        
        # 处理和聚合数据
        aggregated_metrics = await self._process_raw_data(raw_data)
        
        # 更新知识图谱
        await self._update_knowledge_graph(aggregated_metrics)
        
        self.stats["resources_processed"] = len(aggregated_metrics)
        logger.info(f"指标聚合完成，处理了 {len(aggregated_metrics)} 个资源")
    
    def _build_aggregation_queries(self) -> Dict[str, str]:
        """构建聚合查询语句"""
        # 构建14天平均值查询
        queries = {
            # CPU使用率平均值 (14天)
            "cpu_utilization_avg": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, app) (
                            rate(container_cpu_usage_seconds_total{{container!="POD",container!="",app!=""}}[5m])
                        ) / 
                        sum by (namespace, pod, app) (
                            kube_pod_container_resource_requests{{resource="cpu",app!=""}}
                        )
                    )[{self.config.analysis_days}d:1h]
                ) * 100
            '''.strip(),
            
            # 内存使用率平均值 (14天)
            "memory_utilization_avg": f'''
                avg_over_time(
                    (
                        sum by (namespace, pod, app) (
                            container_memory_working_set_bytes{{container!="POD",container!="",app!=""}}
                        ) / 
                        sum by (namespace, pod, app) (
                            kube_pod_container_resource_requests{{resource="memory",app!=""}}
                        )
                    )[{self.config.analysis_days}d:1h]
                ) * 100
            '''.strip(),
            
            # CPU请求量
            "cpu_requests": '''
                sum by (namespace, pod, app) (
                    kube_pod_container_resource_requests{resource="cpu",app!=""}
                )
            '''.strip(),
            
            # 内存请求量
            "memory_requests": '''
                sum by (namespace, pod, app) (
                    kube_pod_container_resource_requests{resource="memory",app!=""}
                ) / 1024 / 1024 / 1024
            '''.strip()
        }
        
        return queries
    
    async def _execute_prometheus_queries(self, queries: Dict[str, str]) -> Dict[str, Any]:
        """执行Prometheus查询"""
        results = {}
        
        for query_name, query in queries.items():
            try:
                logger.debug(f"执行聚合查询: {query_name}")
                
                # 构建查询请求
                current_time = int(datetime.now().timestamp())
                request_body = {
                    "query": query,
                    "time": str(current_time),
                    "timeout": "60000"  # 60秒超时
                }
                
                url = f"{self.config.prometheus_url}/api/v1/query"
                
                async with self.session.post(url, json=request_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            results[query_name] = data.get('data', {}).get('result', [])
                            logger.debug(f"查询 {query_name} 成功，获得 {len(results[query_name])} 条结果")
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
    
    async def _process_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Dict]:
        """处理原始数据并计算聚合指标"""
        app_metrics = {}
        
        # 处理CPU利用率平均值
        for result in raw_data.get("cpu_utilization_avg", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')
            
            app_key = f"{namespace}/{app_name}"
            if app_key not in app_metrics:
                app_metrics[app_key] = {
                    'app_name': app_name,
                    'namespace': namespace,
                    'cpu_utilization_avg_14d': 0.0,
                    'memory_utilization_avg_14d': 0.0,
                    'cpu_requests': 0.0,
                    'memory_requests': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            
            value = float(result.get('value', [0, '0'])[1])
            app_metrics[app_key]['cpu_utilization_avg_14d'] = round(value, 2)
        
        # 处理内存利用率平均值
        for result in raw_data.get("memory_utilization_avg", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')
            
            app_key = f"{namespace}/{app_name}"
            if app_key not in app_metrics:
                app_metrics[app_key] = {
                    'app_name': app_name,
                    'namespace': namespace,
                    'cpu_utilization_avg_14d': 0.0,
                    'memory_utilization_avg_14d': 0.0,
                    'cpu_requests': 0.0,
                    'memory_requests': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            
            value = float(result.get('value', [0, '0'])[1])
            app_metrics[app_key]['memory_utilization_avg_14d'] = round(value, 2)
        
        # 处理CPU请求量
        for result in raw_data.get("cpu_requests", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')
            
            app_key = f"{namespace}/{app_name}"
            if app_key in app_metrics:
                value = float(result.get('value', [0, '0'])[1])
                app_metrics[app_key]['cpu_requests'] = round(value, 3)
        
        # 处理内存请求量
        for result in raw_data.get("memory_requests", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')
            
            app_key = f"{namespace}/{app_name}"
            if app_key in app_metrics:
                value = float(result.get('value', [0, '0'])[1])
                app_metrics[app_key]['memory_requests'] = round(value, 2)
        
        return app_metrics
    
    async def _update_knowledge_graph(self, aggregated_metrics: Dict[str, Dict]):
        """更新知识图谱中的指标数据"""
        for app_key, metrics in aggregated_metrics.items():
            try:
                # 构建资源ID（假设是deployment类型）
                namespace = metrics['namespace']
                app_name = metrics['app_name']
                resource_id = f"deployment/{namespace}/{app_name}"
                
                # 准备指标数据
                metrics_data = {
                    "cpu_utilization_avg_14d": metrics['cpu_utilization_avg_14d'],
                    "memory_utilization_avg_14d": metrics['memory_utilization_avg_14d'],
                    "cpu_requests": metrics['cpu_requests'],
                    "memory_requests": metrics['memory_requests'],
                    "metrics_last_updated": metrics['last_updated'],
                    "needs_optimization": {
                        "cpu": metrics['cpu_utilization_avg_14d'] < self.config.cpu_threshold,
                        "memory": metrics['memory_utilization_avg_14d'] < self.config.memory_threshold
                    }
                }
                
                # 更新知识图谱
                success = self.kg.update_resource_metrics(resource_id, metrics_data)
                if not success:
                    # 如果资源不存在，尝试创建
                    self.kg.add_resource(
                        kind="deployment",
                        namespace=namespace,
                        name=app_name,
                        labels={"app": app_name},
                        metrics=metrics_data
                    )
                    logger.debug(f"创建新资源节点: {resource_id}")
                
            except Exception as e:
                logger.error(f"更新知识图谱指标失败 {app_key}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取聚合器统计信息"""
        return {
            "is_running": self.is_running,
            "config": {
                "aggregation_interval": self.config.aggregation_interval,
                "analysis_days": self.config.analysis_days,
                "cpu_threshold": self.config.cpu_threshold,
                "memory_threshold": self.config.memory_threshold
            },
            "stats": self.stats.copy()
        }
    
    async def force_aggregation(self) -> Dict[str, Any]:
        """强制执行一次指标聚合"""
        if not self.session:
            raise RuntimeError("聚合器未启动")
        
        start_time = datetime.now()
        try:
            await self._aggregate_metrics()
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "processing_time": processing_time,
                "resources_processed": self.stats["resources_processed"]
            }
        except Exception as e:
            logger.error(f"强制聚合失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }


# 全局聚合器实例
_global_aggregator: Optional[K8sMetricsAggregator] = None


def get_metrics_aggregator(config: MetricsConfig = None) -> K8sMetricsAggregator:
    """获取全局指标聚合器实例"""
    global _global_aggregator
    
    if _global_aggregator is None and config:
        _global_aggregator = K8sMetricsAggregator(config)
    
    return _global_aggregator


def create_metrics_config_from_env() -> MetricsConfig:
    """从环境变量创建指标配置"""
    return MetricsConfig(
        prometheus_url=os.getenv("PROMETHEUS_URL", ""),
        access_key=os.getenv("PROMETHEUS_ACCESS_KEY"),
        secret_key=os.getenv("PROMETHEUS_SECRET_KEY"),
        auth_type=os.getenv("PROMETHEUS_AUTH_TYPE", "none"),
        aggregation_interval=int(os.getenv("METRICS_AGGREGATION_INTERVAL", "3600")),
        analysis_days=int(os.getenv("METRICS_ANALYSIS_DAYS", "14")),
        cpu_threshold=float(os.getenv("METRICS_CPU_THRESHOLD", "60.0")),
        memory_threshold=float(os.getenv("METRICS_MEMORY_THRESHOLD", "60.0"))
    )
