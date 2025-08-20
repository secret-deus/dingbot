"""
Kubernetes MCP简化配置管理

只使用两个核心配置字段：
- KUBECONFIG_PATH: kubeconfig文件路径
- K8S_NAMESPACE: 默认命名空间
"""

import os
from pathlib import Path
from typing import Optional
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
            alert_sync_delay_max=alert_sync_delay_max
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
            
            return True
        except Exception as e:
            logger.error(f"验证配置失败: {e}")
            return False
    
    def get_kubeconfig_path(self) -> Optional[str]:
        """获取kubeconfig路径"""
        if self.kubeconfig_path:
            return os.path.expanduser(self.kubeconfig_path)
        return self.kubeconfig_path


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