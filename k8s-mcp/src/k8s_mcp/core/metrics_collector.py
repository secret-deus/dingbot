"""
K8s MCP 指标收集器

负责收集和管理K8s MCP服务器的性能指标和监控数据，包括：
- 智能组件性能指标
- 集群同步状态监控
- 知识图谱统计信息
- API调用统计
- 资源使用情况
- 错误率和延迟统计
"""

import time
import threading
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import gc
from loguru import logger


@dataclass
class MetricPoint:
    """单个指标数据点"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags
        }


@dataclass
class PerformanceStats:
    """性能统计信息"""
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    total_requests: int = 0
    error_count: int = 0
    success_rate: float = 100.0
    requests_per_second: float = 0.0
    
    def update(self, response_time: float, is_error: bool = False):
        """更新统计信息"""
        self.total_requests += 1
        if is_error:
            self.error_count += 1
        
        if response_time > self.max_response_time:
            self.max_response_time = response_time
        if response_time < self.min_response_time:
            self.min_response_time = response_time
        
        # 计算移动平均，但对于第一个值直接设置
        if self.total_requests == 1:
            self.avg_response_time = response_time
        else:
            weight = 0.1  # 新值的权重
            self.avg_response_time = (1 - weight) * self.avg_response_time + weight * response_time
        
        # 计算成功率
        self.success_rate = ((self.total_requests - self.error_count) / self.total_requests * 100) if self.total_requests > 0 else 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "avg_response_time": self.avg_response_time,
            "max_response_time": self.max_response_time,
            "min_response_time": self.min_response_time if self.min_response_time != float('inf') else 0.0,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "requests_per_second": self.requests_per_second
        }


class MetricsCollector:
    """指标收集器
    
    收集和管理各种系统指标：
    - 智能组件性能
    - API调用统计
    - 系统资源使用
    - 集群同步状态
    - 错误和异常统计
    """
    
    def __init__(self, max_history_size: int = 1000, collection_interval: int = 30):
        """初始化指标收集器
        
        Args:
            max_history_size: 历史数据最大保存数量
            collection_interval: 收集间隔（秒）
        """
        self.max_history_size = max_history_size
        self.collection_interval = collection_interval
        
        # 指标存储
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.current_metrics: Dict[str, Any] = {}
        
        # 性能统计
        self.api_stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self.tool_stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        
        # 计数器
        self.counters: Dict[str, int] = defaultdict(int)
        
        # 实时数据
        self.realtime_metrics: Dict[str, float] = {}
        
        # 收集器状态
        self.is_running = False
        self.collection_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
        # 回调函数
        self.metric_callbacks: List[Callable[[MetricPoint], None]] = []
        
        logger.info("指标收集器初始化完成")
    
    def start(self):
        """启动指标收集"""
        if self.is_running:
            logger.warning("指标收集器已经在运行")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("指标收集器已启动")
    
    def stop(self):
        """停止指标收集"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("指标收集器已停止")
    
    def _collection_loop(self):
        """收集循环"""
        while self.is_running:
            try:
                self._collect_system_metrics()
                self._calculate_derived_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"指标收集失败: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        timestamp = time.time()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric("system.cpu_percent", cpu_percent, timestamp)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        self.record_metric("system.memory_percent", memory.percent, timestamp)
        self.record_metric("system.memory_used_mb", memory.used / 1024 / 1024, timestamp)
        self.record_metric("system.memory_available_mb", memory.available / 1024 / 1024, timestamp)
        
        # 进程相关指标
        process = psutil.Process()
        process_memory = process.memory_info()
        self.record_metric("process.memory_rss_mb", process_memory.rss / 1024 / 1024, timestamp)
        self.record_metric("process.memory_vms_mb", process_memory.vms / 1024 / 1024, timestamp)
        self.record_metric("process.cpu_percent", process.cpu_percent(), timestamp)
        
        # Python GC指标
        gc_stats = gc.get_stats()
        if gc_stats:
            self.record_metric("python.gc_collections", sum(stat['collections'] for stat in gc_stats), timestamp)
            self.record_metric("python.gc_collected", sum(stat['collected'] for stat in gc_stats), timestamp)
            self.record_metric("python.gc_uncollectable", sum(stat['uncollectable'] for stat in gc_stats), timestamp)
        
        # 线程数
        self.record_metric("process.thread_count", threading.active_count(), timestamp)
    
    def _calculate_derived_metrics(self):
        """计算派生指标"""
        timestamp = time.time()
        
        # 计算API调用频率
        for endpoint, stats in self.api_stats.items():
            if stats.total_requests > 0:
                # 基于最近的时间窗口计算RPS
                recent_window = 60  # 60秒窗口
                recent_metrics = [m for m in self.metrics_history 
                                if m.name == f"api.{endpoint}.requests" and 
                                timestamp - m.timestamp <= recent_window]
                
                if len(recent_metrics) > 1:
                    total_requests = sum(m.value for m in recent_metrics)
                    time_span = max(m.timestamp for m in recent_metrics) - min(m.timestamp for m in recent_metrics)
                    rps = total_requests / time_span if time_span > 0 else 0
                    stats.requests_per_second = rps
                    
                    self.record_metric(f"api.{endpoint}.rps", rps, timestamp)
    
    def record_metric(self, name: str, value: float, timestamp: Optional[float] = None, tags: Optional[Dict[str, str]] = None):
        """记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            timestamp: 时间戳（可选）
            tags: 标签（可选）
        """
        if timestamp is None:
            timestamp = time.time()
        
        if tags is None:
            tags = {}
        
        metric = MetricPoint(name=name, value=value, timestamp=timestamp, tags=tags)
        
        with self.lock:
            self.metrics_history.append(metric)
            self.current_metrics[name] = value
            self.realtime_metrics[name] = value
        
        # 调用回调函数
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                logger.warning(f"指标回调执行失败: {e}")
    
    def record_api_call(self, endpoint: str, response_time: float, is_error: bool = False):
        """记录API调用统计
        
        Args:
            endpoint: API端点
            response_time: 响应时间（秒）
            is_error: 是否出错
        """
        timestamp = time.time()
        
        # 更新统计信息
        self.api_stats[endpoint].update(response_time, is_error)
        
        # 记录指标
        self.record_metric(f"api.{endpoint}.response_time", response_time, timestamp)
        self.record_metric(f"api.{endpoint}.requests", 1, timestamp)
        if is_error:
            self.record_metric(f"api.{endpoint}.errors", 1, timestamp)
            self.counters[f"api.{endpoint}.error_count"] += 1
        
        self.counters[f"api.{endpoint}.total_count"] += 1
    
    def record_tool_call(self, tool_name: str, execution_time: float, is_error: bool = False):
        """记录工具调用统计
        
        Args:
            tool_name: 工具名称
            execution_time: 执行时间（秒）
            is_error: 是否出错
        """
        timestamp = time.time()
        
        # 更新统计信息
        self.tool_stats[tool_name].update(execution_time, is_error)
        
        # 记录指标
        self.record_metric(f"tool.{tool_name}.execution_time", execution_time, timestamp)
        self.record_metric(f"tool.{tool_name}.calls", 1, timestamp)
        if is_error:
            self.record_metric(f"tool.{tool_name}.errors", 1, timestamp)
            self.counters[f"tool.{tool_name}.error_count"] += 1
        
        self.counters[f"tool.{tool_name}.total_count"] += 1
    
    def record_intelligent_metrics(self, kg_nodes: int, kg_edges: int, sync_health: str, last_sync_ago: float):
        """记录智能组件指标
        
        Args:
            kg_nodes: 知识图谱节点数
            kg_edges: 知识图谱边数
            sync_health: 同步健康状态
            last_sync_ago: 最后同步时间（秒前）
        """
        timestamp = time.time()
        
        self.record_metric("intelligent.kg_nodes", kg_nodes, timestamp)
        self.record_metric("intelligent.kg_edges", kg_edges, timestamp)
        self.record_metric("intelligent.last_sync_ago", last_sync_ago, timestamp)
        
        # 将健康状态转换为数值
        health_score = {"healthy": 1.0, "degraded": 0.5, "stale": 0.2, "stopped": 0.0}.get(sync_health, 0.0)
        self.record_metric("intelligent.sync_health_score", health_score, timestamp)
    
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器
        
        Args:
            name: 计数器名称
            value: 增加值
        """
        with self.lock:
            self.counters[name] += value
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        with self.lock:
            return {
                "timestamp": time.time(),
                "metrics": dict(self.current_metrics),
                "counters": dict(self.counters),
                "api_stats": {name: stats.to_dict() for name, stats in self.api_stats.items()},
                "tool_stats": {name: stats.to_dict() for name, stats in self.tool_stats.items()}
            }
    
    def get_metrics_history(self, metric_name: Optional[str] = None, last_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指标历史
        
        Args:
            metric_name: 指标名称过滤（可选）
            last_minutes: 最近N分钟的数据（可选）
        
        Returns:
            List[Dict]: 指标历史数据
        """
        with self.lock:
            history = list(self.metrics_history)
        
        # 时间过滤
        if last_minutes is not None:
            cutoff_time = time.time() - (last_minutes * 60)
            history = [m for m in history if m.timestamp >= cutoff_time]
        
        # 名称过滤
        if metric_name is not None:
            history = [m for m in history if m.name == metric_name]
        
        return [m.to_dict() for m in history]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计"""
        with self.lock:
            current_time = time.time()
            
            # 计算各类指标的汇总
            api_total_calls = sum(stats.total_requests for stats in self.api_stats.values())
            api_total_errors = sum(stats.error_count for stats in self.api_stats.values())
            api_avg_response_time = sum(stats.avg_response_time * stats.total_requests for stats in self.api_stats.values()) / max(api_total_calls, 1)
            
            tool_total_calls = sum(stats.total_requests for stats in self.tool_stats.values())
            tool_total_errors = sum(stats.error_count for stats in self.tool_stats.values())
            tool_avg_execution_time = sum(stats.avg_response_time * stats.total_requests for stats in self.tool_stats.values()) / max(tool_total_calls, 1)
            
            return {
                "timestamp": current_time,
                "uptime_seconds": current_time - (min(m.timestamp for m in self.metrics_history) if self.metrics_history else current_time),
                "total_metrics_collected": len(self.metrics_history),
                "api_summary": {
                    "total_calls": api_total_calls,
                    "total_errors": api_total_errors,
                    "error_rate": (api_total_errors / max(api_total_calls, 1)) * 100,
                    "avg_response_time": api_avg_response_time
                },
                "tool_summary": {
                    "total_calls": tool_total_calls,
                    "total_errors": tool_total_errors,
                    "error_rate": (tool_total_errors / max(tool_total_calls, 1)) * 100,
                    "avg_execution_time": tool_avg_execution_time
                },
                "system_summary": {
                    "cpu_percent": self.realtime_metrics.get("system.cpu_percent", 0),
                    "memory_percent": self.realtime_metrics.get("system.memory_percent", 0),
                    "process_memory_mb": self.realtime_metrics.get("process.memory_rss_mb", 0),
                    "thread_count": self.realtime_metrics.get("process.thread_count", 0)
                },
                "intelligent_summary": {
                    "kg_nodes": self.realtime_metrics.get("intelligent.kg_nodes", 0),
                    "kg_edges": self.realtime_metrics.get("intelligent.kg_edges", 0),
                    "sync_health_score": self.realtime_metrics.get("intelligent.sync_health_score", 0),
                    "last_sync_ago": self.realtime_metrics.get("intelligent.last_sync_ago", 0)
                }
            }
    
    def register_callback(self, callback: Callable[[MetricPoint], None]):
        """注册指标回调
        
        Args:
            callback: 回调函数，接收MetricPoint参数
        """
        self.metric_callbacks.append(callback)
    
    def clear_history(self):
        """清空历史数据"""
        with self.lock:
            self.metrics_history.clear()
            logger.info("指标历史数据已清空")
    
    def export_prometheus_format(self) -> str:
        """导出Prometheus格式的指标"""
        lines = []
        
        with self.lock:
            # 导出当前指标
            for name, value in self.current_metrics.items():
                prometheus_name = name.replace(".", "_")
                lines.append(f"# TYPE k8s_mcp_{prometheus_name} gauge")
                lines.append(f"k8s_mcp_{prometheus_name} {value}")
                lines.append("")
            
            # 导出计数器
            for name, value in self.counters.items():
                prometheus_name = name.replace(".", "_")
                lines.append(f"# TYPE k8s_mcp_{prometheus_name} counter")
                lines.append(f"k8s_mcp_{prometheus_name} {value}")
                lines.append("")
        
        return "\n".join(lines)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取监控系统健康状态"""
        return {
            "collector_running": self.is_running,
            "metrics_count": len(self.metrics_history),
            "api_endpoints_monitored": len(self.api_stats),
            "tools_monitored": len(self.tool_stats),
            "collection_interval": self.collection_interval,
            "uptime": time.time() - (min(m.timestamp for m in self.metrics_history) if self.metrics_history else time.time())
        }


# 全局指标收集器实例
metrics_collector = MetricsCollector()