"""
Kubernetes MCP简化配置管理

只使用两个核心配置字段：
- KUBECONFIG_PATH: kubeconfig文件路径
- K8S_NAMESPACE: 默认命名空间
"""

import os
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv


class K8sConfig(BaseModel):
    """K8s MCP简化配置"""
    kubeconfig_path: Optional[str] = Field(None, description="Kubeconfig文件路径")
    namespace: str = Field("default", description="默认命名空间")
    host: str = Field("localhost", description="服务器绑定地址")
    port: int = Field(8766, description="服务器端口")
    debug: bool = Field(False, description="调试模式")
    
    # 新增智能功能配置（默认关闭）
    enable_knowledge_graph: bool = Field(False, description="启用知识图谱功能")
    sync_interval: int = Field(300, description="集群同步间隔（秒）")
    graph_max_depth: int = Field(3, description="图查询最大深度")
    graph_ttl: int = Field(3600, description="图节点TTL（秒）")
    graph_memory_limit: int = Field(1024, description="图内存限制（MB）")
    max_summary_size_kb: int = Field(10, description="摘要最大大小（KB）")
    watch_timeout: int = Field(600, description="Watch API超时时间（秒）")
    max_retry_count: int = Field(3, description="最大重试次数")
    
    # 监控配置
    monitoring_enabled: bool = Field(True, description="启用监控功能")
    metrics_collection_interval: int = Field(30, description="指标收集间隔（秒）")
    metrics_history_size: int = Field(1000, description="历史数据保存数量")
    health_check_enabled: bool = Field(True, description="启用健康检查")
    health_check_interval: int = Field(30, description="健康检查间隔（秒）")
    
    # 报警阈值
    alert_api_response_time_max: float = Field(5.0, description="API响应时间阈值（秒）")
    alert_cpu_percent_max: float = Field(80.0, description="CPU使用率阈值（%）")
    alert_memory_percent_max: float = Field(85.0, description="内存使用率阈值（%）")
    alert_error_rate_max: float = Field(5.0, description="错误率阈值（%）")
    alert_sync_delay_max: float = Field(300.0, description="同步延迟阈值（秒）")
    
    # 新增：资源告警配置
    resource_alert_enabled: bool = Field(True, description="启用资源告警功能")
    memory_alert_threshold: float = Field(0.7, description="内存告警阈值（0.0-1.0）")
    cpu_alert_threshold: float = Field(0.8, description="CPU告警阈值（0.0-1.0）")
    alert_cooldown_seconds: int = Field(300, description="告警冷却时间（秒）")
    
    # LLM分析配置
    enable_llm_analysis: bool = Field(True, description="启用LLM智能分析")
    llm_analysis_timeout: int = Field(30, description="LLM分析超时时间（秒）")
    
    # 后端API通信配置
    backend_api_url: str = Field("http://localhost:8000", description="后端API地址")
    enable_backend_notifications: bool = Field(True, description="启用后端通知")
    api_timeout: int = Field(30, description="API请求超时时间（秒）")
    api_max_retries: int = Field(3, description="API请求最大重试次数")
    
    @classmethod
    def from_env(cls) -> "K8sConfig":
        """从环境变量加载配置"""
        # 加载本地的.env文件（如果存在）
        load_dotenv()
        
        # 获取kubeconfig路径
        kubeconfig_path = os.getenv("KUBECONFIG_PATH")
        if not kubeconfig_path:
            # 尝试KUBECONFIG环境变量
            kubeconfig_path = os.getenv("KUBECONFIG")
        if not kubeconfig_path:
            # 使用默认路径
            default_path = os.path.expanduser("~/.kube/config")
            if os.path.exists(default_path):
                kubeconfig_path = default_path
        
        # 获取命名空间
        namespace = os.getenv("K8S_NAMESPACE", "default")
        
        # 获取服务器配置
        host = os.getenv("K8S_MCP_HOST", "localhost")
        port = int(os.getenv("K8S_MCP_PORT", "8766"))
        debug = os.getenv("K8S_MCP_DEBUG", "false").lower() == "true"
        
        # 获取智能功能配置
        enable_knowledge_graph = os.getenv("ENABLE_KNOWLEDGE_GRAPH", "false").lower() == "true"
        sync_interval = int(os.getenv("SYNC_INTERVAL", "300"))
        graph_max_depth = int(os.getenv("GRAPH_MAX_DEPTH", "3"))
        graph_ttl = int(os.getenv("GRAPH_TTL", "3600"))
        graph_memory_limit = int(os.getenv("GRAPH_MEMORY_LIMIT", "1024"))
        max_summary_size_kb = int(os.getenv("MAX_SUMMARY_SIZE_KB", "10"))
        watch_timeout = int(os.getenv("WATCH_TIMEOUT", "600"))
        max_retry_count = int(os.getenv("MAX_RETRY_COUNT", "3"))
        
        # 获取监控配置
        monitoring_enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        metrics_collection_interval = int(os.getenv("METRICS_COLLECTION_INTERVAL", "30"))
        metrics_history_size = int(os.getenv("METRICS_HISTORY_SIZE", "1000"))
        health_check_enabled = os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true"
        health_check_interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        
        # 获取报警阈值
        alert_api_response_time_max = float(os.getenv("ALERT_API_RESPONSE_TIME_MAX", "5.0"))
        alert_cpu_percent_max = float(os.getenv("ALERT_CPU_PERCENT_MAX", "80.0"))
        alert_memory_percent_max = float(os.getenv("ALERT_MEMORY_PERCENT_MAX", "85.0"))
        alert_error_rate_max = float(os.getenv("ALERT_ERROR_RATE_MAX", "5.0"))
        alert_sync_delay_max = float(os.getenv("ALERT_SYNC_DELAY_MAX", "300.0"))
        
        # 获取资源告警配置
        resource_alert_enabled = os.getenv("RESOURCE_ALERT_ENABLED", "true").lower() == "true"
        memory_alert_threshold = float(os.getenv("MEMORY_ALERT_THRESHOLD", "0.7"))
        cpu_alert_threshold = float(os.getenv("CPU_ALERT_THRESHOLD", "0.8"))
        alert_cooldown_seconds = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
        
        # 获取LLM分析配置
        enable_llm_analysis = os.getenv("ENABLE_LLM_ANALYSIS", "true").lower() == "true"
        llm_analysis_timeout = int(os.getenv("LLM_ANALYSIS_TIMEOUT", "30"))
        
        # 获取后端API配置
        backend_api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        enable_backend_notifications = os.getenv("ENABLE_BACKEND_NOTIFICATIONS", "true").lower() == "true"
        api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        api_max_retries = int(os.getenv("API_MAX_RETRIES", "3"))
        
        return cls(
            kubeconfig_path=kubeconfig_path,
            namespace=namespace,
            host=host,
            port=port,
            debug=debug,
            enable_knowledge_graph=enable_knowledge_graph,
            sync_interval=sync_interval,
            graph_max_depth=graph_max_depth,
            graph_ttl=graph_ttl,
            graph_memory_limit=graph_memory_limit,
            max_summary_size_kb=max_summary_size_kb,
            watch_timeout=watch_timeout,
            max_retry_count=max_retry_count,
            monitoring_enabled=monitoring_enabled,
            metrics_collection_interval=metrics_collection_interval,
            metrics_history_size=metrics_history_size,
            health_check_enabled=health_check_enabled,
            health_check_interval=health_check_interval,
            alert_api_response_time_max=alert_api_response_time_max,
            alert_cpu_percent_max=alert_cpu_percent_max,
            alert_memory_percent_max=alert_memory_percent_max,
            alert_error_rate_max=alert_error_rate_max,
            alert_sync_delay_max=alert_sync_delay_max,
            # 新增的资源告警配置
            resource_alert_enabled=resource_alert_enabled,
            memory_alert_threshold=memory_alert_threshold,
            cpu_alert_threshold=cpu_alert_threshold,
            alert_cooldown_seconds=alert_cooldown_seconds,
            enable_llm_analysis=enable_llm_analysis,
            llm_analysis_timeout=llm_analysis_timeout,
            # 后端API配置
            backend_api_url=backend_api_url,
            enable_backend_notifications=enable_backend_notifications,
            api_timeout=api_timeout,
            api_max_retries=api_max_retries
        )
    
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            # 检查kubeconfig文件
            if self.kubeconfig_path:
                # 展开波浪号路径
                expanded_path = os.path.expanduser(self.kubeconfig_path)
                if not os.path.exists(expanded_path):
                    logger.warning(f"Kubeconfig文件不存在: {expanded_path} (原路径: {self.kubeconfig_path})")
                    return False
                logger.info(f"使用kubeconfig文件: {expanded_path}")
            else:
                logger.warning("未指定kubeconfig文件路径")
                return False
            
            # 检查命名空间
            if not self.namespace:
                logger.warning("未指定命名空间")
                return False
            
            logger.info(f"使用命名空间: {self.namespace}")
            
            # 验证智能功能配置
            if self.enable_knowledge_graph:
                logger.info("知识图谱功能已启用")
                logger.info(f"同步间隔: {self.sync_interval}秒")
                logger.info(f"图查询最大深度: {self.graph_max_depth}")
                logger.info(f"图节点TTL: {self.graph_ttl}秒")
                logger.info(f"图内存限制: {self.graph_memory_limit}MB")
                
                # 验证配置合理性
                if self.sync_interval < 60:
                    logger.warning("同步间隔过短，建议至少60秒")
                if self.graph_max_depth > 5:
                    logger.warning("图查询深度过大，可能影响性能")
                if self.graph_memory_limit > 2048:
                    logger.warning("图内存限制过大，建议不超过2GB")
            else:
                logger.info("知识图谱功能已关闭，使用传统模式")
            
            # 验证资源告警配置
            if self.resource_alert_enabled:
                logger.info("资源告警功能已启用")
                
                # 验证告警阈值合理性
                if not (0.0 <= self.memory_alert_threshold <= 1.0):
                    logger.error(f"内存告警阈值无效: {self.memory_alert_threshold}, 应在0.0-1.0之间")
                    return False
                if not (0.0 <= self.cpu_alert_threshold <= 1.0):
                    logger.error(f"CPU告警阈值无效: {self.cpu_alert_threshold}, 应在0.0-1.0之间")
                    return False
                
                logger.info(f"内存告警阈值: {self.memory_alert_threshold:.0%}")
                logger.info(f"CPU告警阈值: {self.cpu_alert_threshold:.0%}")
                logger.info(f"告警冷却时间: {self.alert_cooldown_seconds}秒")
                
                # 验证冷却时间合理性
                if self.alert_cooldown_seconds < 60:
                    logger.warning("告警冷却时间过短，建议至少60秒")
                elif self.alert_cooldown_seconds > 3600:
                    logger.warning("告警冷却时间过长，建议不超过3600秒")
                
                # 验证LLM分析配置
                if self.enable_llm_analysis:
                    logger.info("LLM智能分析已启用")
                    if self.llm_analysis_timeout < 10:
                        logger.warning("LLM分析超时时间过短，建议至少10秒")
                    elif self.llm_analysis_timeout > 120:
                        logger.warning("LLM分析超时时间过长，建议不超过120秒")
                else:
                    logger.info("LLM智能分析已禁用")
                
                # 验证后端API配置
                if self.enable_backend_notifications:
                    logger.info("后端通知已启用")
                    if not self.backend_api_url:
                        logger.warning("后端API URL未配置，将无法发送通知")
                    else:
                        # 简单验证URL格式
                        if not self.backend_api_url.startswith(("http://", "https://")):
                            logger.warning("后端API URL格式可能无效")
                        logger.info(f"后端API: {self.backend_api_url}")
                    
                    # 验证API配置
                    if self.api_timeout < 5 or self.api_timeout > 120:
                        logger.warning("API超时时间建议在5-120秒之间")
                    if self.api_max_retries < 0 or self.api_max_retries > 10:
                        logger.warning("API重试次数建议在0-10次之间")
                    
                    logger.info(f"API配置: 超时{self.api_timeout}秒, 重试{self.api_max_retries}次")
                else:
                    logger.info("后端通知已禁用")
                
            else:
                logger.info("资源告警功能已禁用")
            
            return True
        except Exception as e:
            logger.error(f"验证配置失败: {e}")
            return False
    
    def get_kubeconfig_path(self) -> Optional[str]:
        """获取kubeconfig路径"""
        if self.kubeconfig_path:
            return os.path.expanduser(self.kubeconfig_path)
        return self.kubeconfig_path
    
    def get_tool_default_param(self, param_name: str, default_value: Any = None) -> Any:
        """获取工具默认参数
        
        Args:
            param_name: 参数名称
            default_value: 默认值
            
        Returns:
            参数值或默认值
        """
        # 定义工具默认参数映射
        tool_defaults = {
            "logs_tail_lines": 100,
            "max_pods_per_page": 50,
            "default_timeout": 30,
            "max_events": 100,
            "default_replicas": 1
        }
        
        return tool_defaults.get(param_name, default_value)


# 全局配置实例
_global_config: Optional[K8sConfig] = None


def get_config() -> K8sConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = K8sConfig.from_env()
        logger.info("从环境变量加载配置")
    
    return _global_config


def set_config(config: K8sConfig):
    """设置全局配置实例"""
    global _global_config
    _global_config = config


def create_resource_alert_config_from_k8s_config(k8s_config: K8sConfig) -> 'ResourceAlertConfig':
    """从K8sConfig创建ResourceAlertConfig
    
    Args:
        k8s_config: K8s配置实例
        
    Returns:
        ResourceAlertConfig: 资源告警配置实例
    """
    # 导入V2版本ResourceAlertConfig类（避免循环导入）
    from .core.resource_alert_service_v2 import ResourceAlertConfig
    
    return ResourceAlertConfig(
        memory_alert_threshold=k8s_config.memory_alert_threshold,
        cpu_alert_threshold=k8s_config.cpu_alert_threshold,
        alert_cooldown_seconds=k8s_config.alert_cooldown_seconds,
        backend_api_url=k8s_config.backend_api_url,
        enable_backend_notifications=k8s_config.enable_backend_notifications,
        api_timeout=k8s_config.api_timeout,
        api_max_retries=k8s_config.api_max_retries
    )


def create_metrics_config_from_k8s_config(k8s_config: K8sConfig, 
                                          prometheus_url: str = "",
                                          access_key: Optional[str] = None,
                                          secret_key: Optional[str] = None,
                                          auth_type: str = "none") -> 'MetricsConfig':
    """从K8sConfig创建MetricsConfig
    
    Args:
        k8s_config: K8s配置实例
        prometheus_url: Prometheus服务器URL
        access_key: 访问密钥（可选）
        secret_key: 秘密密钥（可选）
        auth_type: 认证类型
        
    Returns:
        MetricsConfig: 指标配置实例
    """
    # 导入MetricsConfig类（避免循环导入）
    from .core.metrics_aggregator import MetricsConfig
    
    return MetricsConfig(
        prometheus_url=prometheus_url,
        access_key=access_key,
        secret_key=secret_key,
        auth_type=auth_type,
        memory_alert_threshold=k8s_config.memory_alert_threshold,
        cpu_alert_threshold=k8s_config.cpu_alert_threshold,
        alert_cooldown_seconds=k8s_config.alert_cooldown_seconds,
        enable_resource_alerts=k8s_config.resource_alert_enabled
    ) 