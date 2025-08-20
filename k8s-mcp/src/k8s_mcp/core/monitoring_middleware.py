"""
K8s MCP 监控中间件

提供自动化的监控和指标收集功能：
- API请求/响应监控
- 工具调用监控
- 错误率统计
- 性能指标收集
- 异常检测和报警
"""

import time
import asyncio
import functools
from typing import Callable, Any, Optional, Dict
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from .metrics_collector import metrics_collector


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件
    
    自动监控所有HTTP请求的性能指标：
    - 请求计数
    - 响应时间
    - 错误率
    - 状态码分布
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        """初始化监控中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 需要排除监控的路径列表
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        logger.info("监控中间件初始化完成")
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并收集指标"""
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # 检查是否需要排除
        if any(excluded in path for excluded in self.exclude_paths):
            return await call_next(request)
        
        # 创建端点标识
        endpoint = f"{method}_{path.replace('/', '_').strip('_')}"
        
        # 记录请求开始
        metrics_collector.increment_counter("http.requests.total")
        metrics_collector.increment_counter(f"http.requests.{endpoint}")
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 判断是否为错误
            is_error = response.status_code >= 400
            
            # 记录指标
            metrics_collector.record_api_call(endpoint, response_time, is_error)
            
            # 记录状态码
            status_class = f"{response.status_code // 100}xx"
            metrics_collector.increment_counter(f"http.status.{status_class}")
            metrics_collector.increment_counter(f"http.status.{response.status_code}")
            
            # 添加监控头部
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            # 记录异常
            response_time = time.time() - start_time
            metrics_collector.record_api_call(endpoint, response_time, is_error=True)
            metrics_collector.increment_counter("http.exceptions.total")
            metrics_collector.increment_counter(f"http.exceptions.{type(e).__name__}")
            
            logger.error(f"请求处理异常 {endpoint}: {e}")
            raise


def monitor_tool_calls(func: Callable) -> Callable:
    """工具调用监控装饰器
    
    自动监控工具执行的性能指标：
    - 执行时间
    - 成功/失败率
    - 调用频率
    
    Args:
        func: 被装饰的工具函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        tool_name = getattr(func, '__name__', 'unknown_tool')
        start_time = time.time()
        
        try:
            # 执行工具
            result = await func(*args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 判断是否成功（基于结果中的错误标志）
            is_error = False
            if hasattr(result, 'is_error'):
                is_error = result.is_error
            elif isinstance(result, dict) and 'error' in result:
                is_error = True
            
            # 记录指标
            metrics_collector.record_tool_call(tool_name, execution_time, is_error)
            
            return result
            
        except Exception as e:
            # 记录异常
            execution_time = time.time() - start_time
            metrics_collector.record_tool_call(tool_name, execution_time, is_error=True)
            
            logger.error(f"工具执行异常 {tool_name}: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tool_name = getattr(func, '__name__', 'unknown_tool')
        start_time = time.time()
        
        try:
            # 执行工具
            result = func(*args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 判断是否成功
            is_error = False
            if hasattr(result, 'is_error'):
                is_error = result.is_error
            elif isinstance(result, dict) and 'error' in result:
                is_error = True
            
            # 记录指标
            metrics_collector.record_tool_call(tool_name, execution_time, is_error)
            
            return result
            
        except Exception as e:
            # 记录异常
            execution_time = time.time() - start_time
            metrics_collector.record_tool_call(tool_name, execution_time, is_error=True)
            
            logger.error(f"工具执行异常 {tool_name}: {e}")
            raise
    
    # 根据函数类型返回对应的包装器
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def monitor_intelligent_components(kg_service, sync_engine, summary_generator):
    """监控智能组件状态
    
    定期收集智能组件的性能指标：
    - 知识图谱大小
    - 同步状态
    - 摘要生成性能
    
    Args:
        kg_service: 知识图谱服务
        sync_engine: 集群同步引擎  
        summary_generator: 摘要生成器
    """
    def collect_intelligent_metrics():
        """收集智能组件指标"""
        try:
            # 知识图谱指标
            kg_nodes = 0
            kg_edges = 0
            if kg_service and hasattr(kg_service, 'graph'):
                kg_nodes = len(kg_service.graph.nodes)
                kg_edges = len(kg_service.graph.edges)
            
            # 同步引擎指标
            sync_health = "stopped"
            last_sync_ago = float('inf')
            if sync_engine:
                sync_status = sync_engine.get_sync_health()
                sync_health = sync_status.get("health", "unknown")
                last_sync_ago = sync_status.get("last_sync_ago_seconds", float('inf'))
                
                # 记录额外的同步指标
                metrics_collector.record_metric("sync.active_watchers", sync_status.get("active_watch_threads", 0))
                metrics_collector.record_metric("sync.error_count", sync_status.get("error_count", 0))
                metrics_collector.record_metric("sync.total_resources", sync_status.get("total_resources", 0))
            
            # 记录智能组件指标
            metrics_collector.record_intelligent_metrics(kg_nodes, kg_edges, sync_health, last_sync_ago)
            
            # 摘要生成器指标（如果有统计信息）
            if summary_generator and hasattr(summary_generator, 'get_stats'):
                stats = summary_generator.get_stats()
                for key, value in stats.items():
                    metrics_collector.record_metric(f"summary.{key}", value)
            
        except Exception as e:
            logger.error(f"收集智能组件指标失败: {e}")
    
    return collect_intelligent_metrics


class PerformanceMonitor:
    """性能监控器
    
    提供更高级的监控功能：
    - 阈值检测
    - 异常报警
    - 趋势分析
    """
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        """初始化性能监控器
        
        Args:
            alert_thresholds: 报警阈值配置
        """
        self.alert_thresholds = alert_thresholds or {
            "api.response_time.max": 5.0,      # API响应时间阈值(秒)
            "system.cpu_percent.max": 80.0,    # CPU使用率阈值(%)
            "system.memory_percent.max": 85.0, # 内存使用率阈值(%)
            "error_rate.max": 5.0,             # 错误率阈值(%)
            "sync.last_sync_ago.max": 300.0    # 同步延迟阈值(秒)
        }
        
        self.alert_history = []
        self.alert_cooldown = {}  # 防止重复报警
        
        # 注册指标回调
        metrics_collector.register_callback(self._check_alerts)
        
        logger.info("性能监控器初始化完成")
    
    def _check_alerts(self, metric: 'MetricPoint'):
        """检查指标是否触发报警"""
        current_time = time.time()
        
        # 检查各类阈值
        alert_triggered = False
        alert_message = ""
        
        # API响应时间检查
        if "response_time" in metric.name and metric.value > self.alert_thresholds.get("api.response_time.max", 5.0):
            alert_triggered = True
            alert_message = f"API响应时间过高: {metric.name} = {metric.value:.2f}s"
        
        # 系统资源检查
        elif metric.name == "system.cpu_percent" and metric.value > self.alert_thresholds.get("system.cpu_percent.max", 80.0):
            alert_triggered = True
            alert_message = f"CPU使用率过高: {metric.value:.1f}%"
        
        elif metric.name == "system.memory_percent" and metric.value > self.alert_thresholds.get("system.memory_percent.max", 85.0):
            alert_triggered = True
            alert_message = f"内存使用率过高: {metric.value:.1f}%"
        
        # 同步延迟检查
        elif metric.name == "intelligent.last_sync_ago" and metric.value > self.alert_thresholds.get("sync.last_sync_ago.max", 300.0):
            alert_triggered = True
            alert_message = f"集群同步延迟过高: {metric.value:.0f}秒"
        
        # 发送报警（带冷却时间）
        if alert_triggered:
            alert_key = f"{metric.name}_{alert_message[:20]}"
            last_alert_time = self.alert_cooldown.get(alert_key, 0)
            
            # 5分钟冷却时间
            if current_time - last_alert_time > 300:
                self._send_alert(alert_message, metric)
                self.alert_cooldown[alert_key] = current_time
    
    def _send_alert(self, message: str, metric: 'MetricPoint'):
        """发送报警"""
        alert_info = {
            "timestamp": time.time(),
            "message": message,
            "metric_name": metric.name,
            "metric_value": metric.value,
            "severity": "warning"
        }
        
        self.alert_history.append(alert_info)
        
        # 保留最近100个报警
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # 记录到日志
        logger.warning(f"监控报警: {message}")
        
        # 记录报警指标
        metrics_collector.increment_counter("monitoring.alerts.total")
        metrics_collector.increment_counter(f"monitoring.alerts.{metric.name}")
    
    def get_alert_history(self, last_hours: int = 24) -> list:
        """获取报警历史
        
        Args:
            last_hours: 最近几小时的报警
        
        Returns:
            list: 报警历史列表
        """
        cutoff_time = time.time() - (last_hours * 3600)
        return [alert for alert in self.alert_history if alert["timestamp"] >= cutoff_time]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能汇总报告"""
        current_metrics = metrics_collector.get_current_metrics()
        summary_stats = metrics_collector.get_summary_stats()
        
        # 计算健康评分
        health_score = self._calculate_health_score(current_metrics)
        
        return {
            "timestamp": time.time(),
            "health_score": health_score,
            "performance_status": self._get_performance_status(health_score),
            "summary_stats": summary_stats,
            "recent_alerts": self.get_alert_history(1),  # 最近1小时的报警
            "alert_thresholds": self.alert_thresholds,
            "key_metrics": {
                "avg_api_response_time": summary_stats.get("api_summary", {}).get("avg_response_time", 0),
                "api_error_rate": summary_stats.get("api_summary", {}).get("error_rate", 0),
                "cpu_usage": current_metrics.get("metrics", {}).get("system.cpu_percent", 0),
                "memory_usage": current_metrics.get("metrics", {}).get("system.memory_percent", 0),
                "sync_health": current_metrics.get("metrics", {}).get("intelligent.sync_health_score", 0)
            }
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """计算系统健康评分 (0-100)"""
        score = 100.0
        current_values = metrics.get("metrics", {})
        
        # CPU使用率评分 (权重 20%)
        cpu_percent = current_values.get("system.cpu_percent", 0)
        if cpu_percent > 80:
            score -= 20 * (cpu_percent - 80) / 20  # 超过80%开始扣分
        
        # 内存使用率评分 (权重 20%)
        memory_percent = current_values.get("system.memory_percent", 0)
        if memory_percent > 80:
            score -= 20 * (memory_percent - 80) / 20
        
        # API错误率评分 (权重 30%)
        api_summary = metrics.get("api_summary", {})
        error_rate = api_summary.get("error_rate", 0)
        if error_rate > 0:
            score -= 30 * min(error_rate / 10, 1)  # 10%错误率扣满分
        
        # 同步健康评分 (权重 20%)
        sync_health_score = current_values.get("intelligent.sync_health_score", 1.0)
        score -= 20 * (1 - sync_health_score)
        
        # 响应时间评分 (权重 10%)
        avg_response_time = api_summary.get("avg_response_time", 0)
        if avg_response_time > 1:
            score -= 10 * min(avg_response_time / 5, 1)  # 5秒响应时间扣满分
        
        return max(0, min(100, score))
    
    def _get_performance_status(self, health_score: float) -> str:
        """根据健康评分获取性能状态"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "warning"
        elif health_score >= 40:
            return "critical"
        else:
            return "emergency"


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()