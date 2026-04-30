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
    aggregation_interval: int = 1209600  # 聚合间隔（秒），默认2周 (14天 * 24小时 * 3600秒)
    metrics_retention_days: int = 30  # 指标保留天数
    analysis_days: int = 14  # 分析天数
    cpu_threshold: float = 60.0  # CPU利用率阈值
    memory_threshold: float = 60.0  # 内存利用率阈值

    # 新增告警配置
    memory_alert_threshold: float = 0.7  # 内存告警阈值（70%）
    cpu_alert_threshold: float = 0.8  # CPU告警阈值（80%）
    alert_cooldown_seconds: int = 300  # 告警冷却时间（5分钟）
    enable_resource_alerts: bool = True  # 是否启用资源告警


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
            "avg_processing_time": 0.0,
            "alerts_triggered": 0,  # 新增：触发的告警数量
            "alerts_suppressed": 0,  # 新增：被冷却抑制的告警数量
            # 新增：deployment覆盖统计
            "deployments_discovered": 0,  # 发现的deployment总数
            "deployments_updated": 0,     # 成功更新的deployment数
            "deployments_failed": 0,      # 更新失败的deployment数
            "retry_attempts": 0,          # 重试次数
            "last_discovery_time": 0,     # 最后一次发现deployment的时间
            "failed_deployments": []      # 失败的deployment列表（最近10个）
        }

        # 新增：告警冷却记录
        self.alert_cooldown_cache: Dict[str, float] = {}

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

        try:
            # 1. 发现所有deployment
            all_deployments = await self._discover_all_deployments()
            self.stats["deployments_discovered"] = len(all_deployments)
            self.stats["last_discovery_time"] = datetime.now().timestamp()

            logger.info(f"发现 {len(all_deployments)} 个deployment需要更新指标")

            # 2. 获取时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.config.analysis_days)

            # 3. 构建Prometheus查询
            queries = self._build_aggregation_queries()

            # 4. 执行查询
            raw_data = await self._execute_prometheus_queries(queries)

            # 5. 处理和聚合数据
            aggregated_metrics = await self._process_raw_data(raw_data)

            # 6. 确保所有deployment都有指标数据（补充缺失的）
            complete_metrics = await self._ensure_all_deployments_covered(
                all_deployments, aggregated_metrics
            )

            # 7. 更新知识图谱（带重试机制）
            await self._update_knowledge_graph_with_retry(complete_metrics)

            # 8. 检查资源告警
            if self.config.enable_resource_alerts:
                await self._check_resource_alerts(complete_metrics)

            self.stats["resources_processed"] = len(complete_metrics)
            logger.info(f"指标聚合完成，处理了 {len(complete_metrics)} 个资源")

        except Exception as e:
            logger.error(f"指标聚合过程中发生错误: {e}")
            self.stats["errors_count"] += 1
            raise

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

                # 构建查询请求 - 使用和工具相同的格式
                current_time = int(datetime.now().timestamp())
                start_time = current_time - (self.config.analysis_days * 24 * 3600)

                # 使用query_range API和params参数
                params = {
                    "query": query,
                    "start": str(start_time),
                    "end": str(current_time),
                    "step": "1h"
                }

                url = f"{self.config.prometheus_url}/api/v1/query_range"

                async with self.session.post(url, data=params) as response:
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

            # query_range返回values数组，计算平均值
            values = result.get('values', [])
            if values:
                avg_value = sum(float(v[1]) for v in values) / len(values)
                app_metrics[app_key]['cpu_utilization_avg_14d'] = round(avg_value, 2)

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

            # query_range返回values数组，计算平均值
            values = result.get('values', [])
            if values:
                avg_value = sum(float(v[1]) for v in values) / len(values)
                app_metrics[app_key]['memory_utilization_avg_14d'] = round(avg_value, 2)

        # 处理CPU请求量
        for result in raw_data.get("cpu_requests", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')

            app_key = f"{namespace}/{app_name}"
            if app_key in app_metrics:
                # query_range返回values数组，取最新值
                values = result.get('values', [])
                if values:
                    latest_value = float(values[-1][1])
                    app_metrics[app_key]['cpu_requests'] = round(latest_value, 3)

        # 处理内存请求量
        for result in raw_data.get("memory_requests", []):
            metric = result.get('metric', {})
            app_name = metric.get('app', 'unknown')
            namespace = metric.get('namespace', 'default')

            app_key = f"{namespace}/{app_name}"
            if app_key in app_metrics:
                # query_range返回values数组，取最新值
                values = result.get('values', [])
                if values:
                    latest_value = float(values[-1][1])
                    app_metrics[app_key]['memory_requests'] = round(latest_value, 2)

        return app_metrics


    async def _check_resource_alerts(self, aggregated_metrics: Dict[str, Dict]):
        """检查资源告警阈值"""
        current_time = datetime.now().timestamp()

        for app_key, metrics in aggregated_metrics.items():
            try:
                # 获取资源利用率（转换为小数形式）
                memory_util = metrics.get('memory_utilization_avg_14d', 0) / 100.0
                cpu_util = metrics.get('cpu_utilization_avg_14d', 0) / 100.0

                # 构建资源ID
                namespace = metrics['namespace']
                app_name = metrics['app_name']
                resource_id = f"deployment/{namespace}/{app_name}"

                # 检查内存告警阈值
                if memory_util > self.config.memory_alert_threshold:
                    await self._trigger_alert(
                        resource_id=resource_id,
                        alert_type="memory",
                        current_value=memory_util,
                        threshold=self.config.memory_alert_threshold,
                        metrics_data=metrics,
                        current_time=current_time
                    )

                # 检查CPU告警阈值
                if cpu_util > self.config.cpu_alert_threshold:
                    await self._trigger_alert(
                        resource_id=resource_id,
                        alert_type="cpu",
                        current_value=cpu_util,
                        threshold=self.config.cpu_alert_threshold,
                        metrics_data=metrics,
                        current_time=current_time
                    )

            except Exception as e:
                logger.error(f"检查资源告警失败 {app_key}: {e}")

    async def _trigger_alert(self, resource_id: str, alert_type: str, current_value: float,
                           threshold: float, metrics_data: Dict, current_time: float):
        """触发资源告警"""
        # 构建告警键用于冷却检查
        alert_key = f"{resource_id}_{alert_type}"

        # 检查告警冷却
        last_alert_time = self.alert_cooldown_cache.get(alert_key, 0)
        if current_time - last_alert_time < self.config.alert_cooldown_seconds:
            logger.debug(f"告警被冷却抑制: {alert_key}")
            self.stats["alerts_suppressed"] += 1
            return

        # 记录告警时间
        self.alert_cooldown_cache[alert_key] = current_time
        self.stats["alerts_triggered"] += 1

        # 记录告警日志
        logger.warning(
            f"🚨 资源告警触发: {resource_id} - {alert_type.upper()}利用率 "
            f"{current_value:.1%} 超过阈值 {threshold:.1%}"
        )

        # 这里预留接口供后续任务集成ResourceAlertService
        # 当前只记录日志，后续任务会实现LLM分析和钉钉告警
        logger.info(f"告警详情: {metrics_data}")

    async def _discover_all_deployments(self) -> List[Dict[str, str]]:
        """从知识图谱中获取所有deployment"""
        deployments = []

        try:
            # 直接从知识图谱中获取所有deployment
            with self.kg.lock:
                for node_id, node_data in self.kg.graph.nodes(data=True):
                    if node_data.get('kind') == 'deployment':
                        namespace = node_data.get('namespace', 'default')
                        name = node_data.get('name', '')
                        if name:  # 确保有名称
                            deployments.append({
                                'resource_id': node_id,
                                'namespace': namespace,
                                'name': name,
                                'app_label': node_data.get('labels', {}).get('app', name)
                            })

            logger.info(f"从知识图谱发现 {len(deployments)} 个deployment")
            return deployments

        except Exception as e:
            logger.error(f"从知识图谱获取deployment失败: {e}")
            return []

    async def _ensure_all_deployments_covered(self,
                                           all_deployments: List[Dict[str, str]],
                                           aggregated_metrics: Dict[str, Dict]) -> Dict[str, Dict]:
        """确保所有deployment都有指标数据"""
        complete_metrics = aggregated_metrics.copy()

        for deployment in all_deployments:
            namespace = deployment['namespace']
            name = deployment['name']
            app_key = f"{namespace}/{name}"

            # 如果该deployment没有指标数据，创建默认数据
            if app_key not in complete_metrics:
                logger.warning(f"Deployment {app_key} 缺少指标数据，使用默认值")
                complete_metrics[app_key] = {
                    'namespace': namespace,
                    'app_name': name,
                    'cpu_utilization_avg_14d': 0.0,
                    'memory_utilization_avg_14d': 0.0,
                    'cpu_requests': 0.0,
                    'memory_requests': 0.0,
                    'last_updated': datetime.now().isoformat(),
                    'data_source': 'default_fallback',
                    'has_prometheus_data': False
                }

        return complete_metrics

    async def _update_knowledge_graph_with_retry(self, aggregated_metrics: Dict[str, Dict]):
        """带重试机制的知识图谱更新"""
        max_retries = 3
        successful_updates = 0
        failed_updates = []

        for app_key, metrics in aggregated_metrics.items():
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    # 构建资源ID
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
                        },
                        "data_source": metrics.get('data_source', 'prometheus'),
                        "has_prometheus_data": metrics.get('has_prometheus_data', True)
                    }

                    # 更新知识图谱
                    update_success = self.kg.update_resource_metrics(resource_id, metrics_data)

                    if not update_success:
                        # 如果资源不存在，尝试创建
                        self.kg.add_resource(
                            kind="deployment",
                            namespace=namespace,
                            name=app_name,
                            labels={"app": app_name},
                            metrics=metrics_data
                        )
                        logger.debug(f"创建新资源节点: {resource_id}")

                    successful_updates += 1
                    success = True

                except Exception as e:
                    retry_count += 1
                    self.stats["retry_attempts"] += 1
                    logger.warning(f"更新 {app_key} 失败 (尝试 {retry_count}/{max_retries}): {e}")

                    if retry_count < max_retries:
                        await asyncio.sleep(1)  # 重试前等待1秒
                    else:
                        failed_updates.append({
                            'app_key': app_key,
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })

        # 更新统计信息
        self.stats["deployments_updated"] = successful_updates
        self.stats["deployments_failed"] = len(failed_updates)

        # 保留最近10个失败记录
        self.stats["failed_deployments"] = failed_updates[-10:]

        if failed_updates:
            logger.error(f"有 {len(failed_updates)} 个deployment更新失败")
            for failure in failed_updates[-3:]:  # 只记录最近3个失败
                logger.error(f"失败详情: {failure}")

        logger.info(f"知识图谱更新完成: 成功 {successful_updates}, 失败 {len(failed_updates)}")

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
        aggregation_interval=int(os.getenv("METRICS_AGGREGATION_INTERVAL", "1209600")),  # 默认2周
        analysis_days=int(os.getenv("METRICS_ANALYSIS_DAYS", "14")),
        cpu_threshold=float(os.getenv("METRICS_CPU_THRESHOLD", "60.0")),
        memory_threshold=float(os.getenv("METRICS_MEMORY_THRESHOLD", "60.0")),

        # 新增告警配置的环境变量支持
        memory_alert_threshold=float(os.getenv("MEMORY_ALERT_THRESHOLD", "0.7")),
        cpu_alert_threshold=float(os.getenv("CPU_ALERT_THRESHOLD", "0.8")),
        alert_cooldown_seconds=int(os.getenv("ALERT_COOLDOWN_SECONDS", "300")),
        enable_resource_alerts=os.getenv("ENABLE_RESOURCE_ALERTS", "true").lower() == "true"
    )
