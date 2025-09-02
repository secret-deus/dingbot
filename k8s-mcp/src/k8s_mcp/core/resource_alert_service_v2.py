"""
资源告警服务 V2 - 重构版本

专注于资源告警检测，通过HTTP API与后端通信，
不再直接处理LLM分析和钉钉发送，实现职责分离。
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger

from .http_api_client import get_global_http_client


class ResourceAlertConfig:
    """资源告警配置 - 简化版本"""
    
    def __init__(self, 
                 memory_alert_threshold: float = 0.7,
                 cpu_alert_threshold: float = 0.8,
                 alert_cooldown_seconds: int = 300,
                 backend_api_url: Optional[str] = None,
                 enable_backend_notifications: bool = True,
                 api_timeout: int = 30,
                 api_max_retries: int = 3):
        """初始化告警配置
        
        Args:
            memory_alert_threshold: 内存告警阈值 (0.0-1.0)
            cpu_alert_threshold: CPU告警阈值 (0.0-1.0)
            alert_cooldown_seconds: 告警冷却时间（秒）
            backend_api_url: 后端API地址
            enable_backend_notifications: 是否启用后端通知
            api_timeout: API请求超时时间（秒）
            api_max_retries: API请求最大重试次数
        """
        self.memory_alert_threshold = memory_alert_threshold
        self.cpu_alert_threshold = cpu_alert_threshold
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self.backend_api_url = backend_api_url
        self.enable_backend_notifications = enable_backend_notifications
        self.api_timeout = api_timeout
        self.api_max_retries = api_max_retries
        
        # 验证配置
        self._validate_config()
        
        logger.info("ResourceAlertConfig初始化完成")
    
    def _validate_config(self):
        """验证配置参数"""
        if not 0.0 <= self.memory_alert_threshold <= 1.0:
            raise ValueError(f"内存告警阈值必须在0.0-1.0之间: {self.memory_alert_threshold}")
        
        if not 0.0 <= self.cpu_alert_threshold <= 1.0:
            raise ValueError(f"CPU告警阈值必须在0.0-1.0之间: {self.cpu_alert_threshold}")
        
        if self.alert_cooldown_seconds < 0:
            raise ValueError(f"告警冷却时间不能为负数: {self.alert_cooldown_seconds}")
        
        if self.enable_backend_notifications and not self.backend_api_url:
            logger.warning("启用了后端通知但未配置backend_api_url")


class ResourceAlertService:
    """资源告警服务 - 重构版本
    
    专注于告警检测和冷却管理，通过HTTP API与后端通信
    """
    
    def __init__(self, config: ResourceAlertConfig):
        """初始化告警服务
        
        Args:
            config: 告警配置
        """
        self.config = config
        
        # 告警冷却缓存 {resource_id: last_alert_time}
        self.alert_cooldown_cache: Dict[str, datetime] = {}
        
        # 统计信息
        self.stats = {
            "alerts_detected": 0,
            "alerts_sent_to_backend": 0,
            "alerts_suppressed_by_cooldown": 0,
            "backend_api_success": 0,
            "backend_api_failed": 0,
            "last_alert_time": None,
            "last_backend_call_time": None
        }
        
        # 初始化HTTP客户端
        self.http_client = None
        if self.config.backend_api_url:
            self.http_client = get_global_http_client(self.config.backend_api_url)
        
        logger.info("ResourceAlertService V2 初始化完成")
    
    async def check_and_alert(self, resource_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查资源指标并触发告警
        
        Args:
            resource_id: 资源标识符
            metrics_data: 指标数据字典
            
        Returns:
            Dict[str, Any]: 告警处理结果
        """
        logger.info(f"开始处理资源告警检查: {resource_id}")
        
        try:
            # 检查是否需要告警
            alert_reasons = self._check_thresholds(metrics_data)
            
            if not alert_reasons:
                logger.debug(f"资源 {resource_id} 未达到告警阈值")
                return {
                    "alert_triggered": False,
                    "reason": "未达到告警阈值",
                    "thresholds": {
                        "memory": self.config.memory_alert_threshold,
                        "cpu": self.config.cpu_alert_threshold
                    },
                    "current_utilization": {
                        "memory": metrics_data.get("avg_memory_utilization", 0) / 100.0,
                        "cpu": metrics_data.get("avg_cpu_utilization", 0) / 100.0
                    }
                }
            
            # 检查告警冷却
            if self._is_in_cooldown(resource_id):
                self.stats["alerts_suppressed_by_cooldown"] += 1
                logger.debug(f"资源 {resource_id} 告警被冷却抑制")
                return {
                    "alert_triggered": False,
                    "reason": "告警冷却期内",
                    "cooldown_remaining": self._get_cooldown_remaining(resource_id),
                    "alert_reasons": alert_reasons
                }
            
            # 记录告警
            self.stats["alerts_detected"] += 1
            self.stats["last_alert_time"] = datetime.now().isoformat()
            self._record_alert_time(resource_id)
            
            # 构建告警数据
            alert_data = {
                "resource_id": resource_id,
                "metrics": metrics_data,
                "alert_reasons": alert_reasons,
                "timestamp": datetime.now().isoformat(),
                "thresholds": {
                    "memory": self.config.memory_alert_threshold,
                    "cpu": self.config.cpu_alert_threshold
                },
                "current_utilization": {
                    "memory": metrics_data.get("avg_memory_utilization", 0) / 100.0,
                    "cpu": metrics_data.get("avg_cpu_utilization", 0) / 100.0
                }
            }
            
            # 发送到后端处理
            backend_result = await self._send_to_backend(alert_data)
            
            return {
                "alert_triggered": True,
                "alert_reasons": alert_reasons,
                "backend_notification": backend_result,
                "alert_data": alert_data
            }
            
        except Exception as e:
            logger.error(f"处理资源告警失败: {e}")
            return {
                "alert_triggered": False,
                "reason": f"处理失败: {str(e)}",
                "error": True
            }
    
    def _check_thresholds(self, metrics_data: Dict[str, Any]) -> List[str]:
        """检查指标是否超过阈值
        
        Args:
            metrics_data: 指标数据
            
        Returns:
            List[str]: 超过阈值的指标列表
        """
        alert_reasons = []
        
        # 获取利用率数据（百分比转小数）
        memory_util = metrics_data.get("avg_memory_utilization", 0) / 100.0
        cpu_util = metrics_data.get("avg_cpu_utilization", 0) / 100.0
        
        # 检查内存阈值
        if memory_util > self.config.memory_alert_threshold:
            alert_reasons.append(f"内存利用率过高: {memory_util:.1%} > {self.config.memory_alert_threshold:.1%}")
        
        # 检查CPU阈值
        if cpu_util > self.config.cpu_alert_threshold:
            alert_reasons.append(f"CPU利用率过高: {cpu_util:.1%} > {self.config.cpu_alert_threshold:.1%}")
        
        return alert_reasons
    
    def _is_in_cooldown(self, resource_id: str) -> bool:
        """检查资源是否在告警冷却期内
        
        Args:
            resource_id: 资源ID
            
        Returns:
            bool: 是否在冷却期内
        """
        last_alert_time = self.alert_cooldown_cache.get(resource_id)
        if not last_alert_time:
            return False
        
        cooldown_until = last_alert_time + timedelta(seconds=self.config.alert_cooldown_seconds)
        return datetime.now() < cooldown_until
    
    def _get_cooldown_remaining(self, resource_id: str) -> Optional[int]:
        """获取剩余冷却时间
        
        Args:
            resource_id: 资源ID
            
        Returns:
            Optional[int]: 剩余秒数，如果不在冷却期返回None
        """
        last_alert_time = self.alert_cooldown_cache.get(resource_id)
        if not last_alert_time:
            return None
        
        cooldown_until = last_alert_time + timedelta(seconds=self.config.alert_cooldown_seconds)
        now = datetime.now()
        
        if now < cooldown_until:
            return int((cooldown_until - now).total_seconds())
        return None
    
    def _record_alert_time(self, resource_id: str):
        """记录告警时间
        
        Args:
            resource_id: 资源ID
        """
        self.alert_cooldown_cache[resource_id] = datetime.now()
        logger.debug(f"记录资源 {resource_id} 的告警时间")
    
    async def _send_to_backend(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送告警数据到后端API
        
        Args:
            alert_data: 告警数据
            
        Returns:
            Dict[str, Any]: 后端处理结果
        """
        if not self.config.enable_backend_notifications:
            logger.debug("后端通知已禁用")
            return {
                "sent": False,
                "reason": "后端通知已禁用"
            }
        
        if not self.http_client:
            logger.warning("HTTP客户端未初始化，无法发送后端通知")
            self.stats["backend_api_failed"] += 1
            return {
                "sent": False,
                "reason": "HTTP客户端未初始化"
            }
        
        try:
            self.stats["last_backend_call_time"] = datetime.now().isoformat()
            logger.info(f"发送告警数据到后端: {alert_data['resource_id']}")
            
            success = await self.http_client.send_resource_alert(
                alert_data["resource_id"],
                alert_data["metrics"],
                {
                    "alert_reasons": alert_data["alert_reasons"],
                    "thresholds": alert_data["thresholds"],
                    "current_utilization": alert_data["current_utilization"]
                }
            )
            
            if success:
                self.stats["backend_api_success"] += 1
                self.stats["alerts_sent_to_backend"] += 1
                logger.info(f"后端通知发送成功: {alert_data['resource_id']}")
                return {
                    "sent": True,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.stats["backend_api_failed"] += 1
                logger.error(f"后端通知发送失败: {alert_data['resource_id']}")
                return {
                    "sent": True,
                    "success": False,
                    "reason": "HTTP请求失败"
                }
        
        except Exception as e:
            self.stats["backend_api_failed"] += 1
            logger.error(f"发送后端通知时发生异常: {e}")
            return {
                "sent": True,
                "success": False,
                "reason": f"异常: {str(e)}"
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        result = {
            "config": {
                "memory_alert_threshold": self.config.memory_alert_threshold,
                "cpu_alert_threshold": self.config.cpu_alert_threshold,
                "alert_cooldown_seconds": self.config.alert_cooldown_seconds,
                "backend_api_url": self.config.backend_api_url,
                "enable_backend_notifications": self.config.enable_backend_notifications
            },
            "stats": self.stats.copy(),
            "cooldown_cache_size": len(self.alert_cooldown_cache)
        }
        
        # 添加HTTP客户端统计
        if self.http_client:
            result["http_client"] = self.http_client.get_statistics()
        
        return result
    
    async def close(self):
        """关闭服务，清理资源"""
        logger.info("ResourceAlertService正在关闭...")
        
        # HTTP客户端由全局管理，这里不需要关闭
        
        # 清理缓存
        self.alert_cooldown_cache.clear()
        
        logger.info("ResourceAlertService已关闭")
