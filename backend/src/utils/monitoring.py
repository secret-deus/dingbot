"""
调试和监控工具
提供性能监控、请求追踪和调试信息收集功能
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from loguru import logger
# 暂时禁用psutil以简化部署
PSUTIL_AVAILABLE = False
import threading
from collections import defaultdict, deque


@dataclass
class RequestMetrics:
    """请求指标数据"""
    request_id: str
    endpoint: str
    method: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系统指标数据"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    request_count: int
    error_count: int
    avg_response_time: float


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_requests: int = 1000):
        self.max_requests = max_requests
        self.requests: deque = deque(maxlen=max_requests)
        self.active_requests: Dict[str, RequestMetrics] = {}
        self.system_metrics: deque = deque(maxlen=100)  # 保留最近100个系统指标
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'errors': 0
        })
        self._lock = threading.Lock()
        self._monitoring_active = False
        self._monitor_task = None
    
    def start_monitoring(self, interval: float = 30.0):
        """开始系统监控"""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitor_task = asyncio.create_task(self._monitor_system(interval))
            logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        if self._monitoring_active:
            self._monitoring_active = False
            if self._monitor_task:
                self._monitor_task.cancel()
            logger.info("性能监控已停止")
    
    async def _monitor_system(self, interval: float):
        """系统监控循环"""
        while self._monitoring_active:
            try:
                # 收集系统指标
                if PSUTIL_AVAILABLE:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    cpu_val = cpu_percent
                    memory_percent = memory.percent
                    memory_used_mb = memory.used / 1024 / 1024
                    disk_percent = disk.percent
                else:
                    # 如果psutil不可用，使用默认值
                    cpu_val = 0.0
                    memory_percent = 0.0
                    memory_used_mb = 0.0
                    disk_percent = 0.0
                
                # 计算请求统计
                recent_requests = [r for r in self.requests if time.time() - r.start_time < 300]  # 最近5分钟
                request_count = len(recent_requests)
                error_count = sum(1 for r in recent_requests if r.error)
                avg_response_time = (
                    sum(r.duration for r in recent_requests if r.duration) / len(recent_requests)
                    if recent_requests else 0
                )
                
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_val,
                    memory_percent=memory_percent,
                    memory_used_mb=memory_used_mb,
                    disk_usage_percent=disk_percent,
                    active_connections=len(self.active_requests),
                    request_count=request_count,
                    error_count=error_count,
                    avg_response_time=avg_response_time
                )
                
                with self._lock:
                    self.system_metrics.append(metrics)
                
                # 记录异常指标（只在psutil可用时检查）
                if PSUTIL_AVAILABLE:
                    if cpu_val > 80:
                        logger.warning(f"CPU使用率过高: {cpu_val}%")
                    if memory_percent > 85:
                        logger.warning(f"内存使用率过高: {memory_percent}%")
                if len(self.active_requests) > 50:
                    logger.warning(f"活跃连接数过多: {len(self.active_requests)}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                await asyncio.sleep(interval)
    
    def start_request(
        self, 
        endpoint: str, 
        method: str = "POST",
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_size: Optional[int] = None
    ) -> str:
        """开始请求追踪"""
        request_id = str(uuid.uuid4())
        
        metrics = RequestMetrics(
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            start_time=time.time(),
            user_agent=user_agent,
            ip_address=ip_address,
            request_size=request_size
        )
        
        with self._lock:
            self.active_requests[request_id] = metrics
        
        logger.debug(f"开始请求追踪: {request_id} - {method} {endpoint}")
        return request_id
    
    def finish_request(
        self,
        request_id: str,
        status_code: int = 200,
        error: Optional[str] = None,
        response_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """完成请求追踪"""
        with self._lock:
            if request_id in self.active_requests:
                metrics = self.active_requests.pop(request_id)
                metrics.end_time = time.time()
                metrics.duration = metrics.end_time - metrics.start_time
                metrics.status_code = status_code
                metrics.error = error
                metrics.response_size = response_size
                if metadata:
                    metrics.metadata.update(metadata)
                
                # 添加到历史记录
                self.requests.append(metrics)
                
                # 更新端点统计
                endpoint_stat = self.endpoint_stats[metrics.endpoint]
                endpoint_stat['count'] += 1
                endpoint_stat['total_time'] += metrics.duration
                endpoint_stat['avg_time'] = endpoint_stat['total_time'] / endpoint_stat['count']
                
                if error:
                    endpoint_stat['errors'] += 1
                    self.error_counts[error] += 1
                
                logger.debug(f"完成请求追踪: {request_id} - {metrics.duration:.3f}s - {status_code}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            recent_requests = [r for r in self.requests if time.time() - r.start_time < 3600]  # 最近1小时
            
            if not recent_requests:
                return {
                    "total_requests": 0,
                    "avg_response_time": 0,
                    "error_rate": 0,
                    "requests_per_minute": 0,
                    "active_connections": len(self.active_requests),
                    "endpoint_stats": dict(self.endpoint_stats),
                    "top_errors": [],
                    "system_metrics": list(self.system_metrics)[-1].__dict__ if self.system_metrics else None
                }
            
            total_requests = len(recent_requests)
            avg_response_time = sum(r.duration for r in recent_requests if r.duration) / total_requests
            error_count = sum(1 for r in recent_requests if r.error)
            error_rate = error_count / total_requests if total_requests > 0 else 0
            requests_per_minute = total_requests / 60  # 简化计算
            
            # 获取最常见的错误
            top_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_requests": total_requests,
                "avg_response_time": avg_response_time,
                "error_rate": error_rate,
                "requests_per_minute": requests_per_minute,
                "active_connections": len(self.active_requests),
                "endpoint_stats": dict(self.endpoint_stats),
                "top_errors": top_errors,
                "system_metrics": list(self.system_metrics)[-1].__dict__ if self.system_metrics else None
            }
    
    def get_request_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取请求历史"""
        with self._lock:
            recent_requests = list(self.requests)[-limit:]
            return [
                {
                    "request_id": r.request_id,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "duration": r.duration,
                    "status_code": r.status_code,
                    "error": r.error,
                    "timestamp": r.start_time,
                    "metadata": r.metadata
                }
                for r in recent_requests
            ]


class DebugCollector:
    """调试信息收集器"""
    
    def __init__(self, max_logs: int = 500):
        self.max_logs = max_logs
        self.debug_logs: deque = deque(maxlen=max_logs)
        self.context_data: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def add_debug_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        """添加调试日志"""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "context": context or {},
            "request_id": request_id
        }
        
        with self._lock:
            self.debug_logs.append(log_entry)
    
    def set_context(self, key: str, value: Any):
        """设置上下文数据"""
        with self._lock:
            self.context_data[key] = value
    
    def get_debug_info(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """获取调试信息"""
        with self._lock:
            logs = list(self.debug_logs)
            
            if request_id:
                logs = [log for log in logs if log.get("request_id") == request_id]
            
            return {
                "logs": logs,
                "context": dict(self.context_data),
                "timestamp": time.time()
            }


# 全局监控实例
performance_monitor = PerformanceMonitor()
debug_collector = DebugCollector()


@asynccontextmanager
async def request_tracking(
    endpoint: str,
    method: str = "POST",
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """请求追踪上下文管理器"""
    request_id = performance_monitor.start_request(
        endpoint=endpoint,
        method=method,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    try:
        yield request_id
        performance_monitor.finish_request(request_id, status_code=200)
    except Exception as e:
        performance_monitor.finish_request(
            request_id,
            status_code=500,
            error=str(e)
        )
        raise


def debug_log(level: str = "INFO"):
    """调试日志装饰器"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = str(uuid.uuid4())
            
            debug_collector.add_debug_log(
                level="DEBUG",
                message=f"开始执行 {func.__name__}",
                context={"args": str(args), "kwargs": str(kwargs)},
                request_id=request_id
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                debug_collector.add_debug_log(
                    level="DEBUG",
                    message=f"完成执行 {func.__name__}",
                    context={"duration": duration, "success": True},
                    request_id=request_id
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                debug_collector.add_debug_log(
                    level="ERROR",
                    message=f"执行失败 {func.__name__}: {str(e)}",
                    context={"duration": duration, "error": str(e)},
                    request_id=request_id
                )
                
                raise
        
        return wrapper
    return decorator


# 启动监控
def start_monitoring():
    """启动监控系统"""
    performance_monitor.start_monitoring()
    logger.info("监控系统已启动")


def stop_monitoring():
    """停止监控系统"""
    performance_monitor.stop_monitoring()
    logger.info("监控系统已停止")