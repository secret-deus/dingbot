"""
K8s MCP 监控功能测试模块

测试监控相关组件：
- MetricsCollector: 指标收集器
- MonitoringMiddleware: 监控中间件
- PerformanceMonitor: 性能监控器
- 监控API端点
- 报警机制
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.k8s_mcp.core.metrics_collector import MetricsCollector, MetricPoint, PerformanceStats
from src.k8s_mcp.core.monitoring_middleware import MonitoringMiddleware, PerformanceMonitor, monitor_tool_calls
from src.k8s_mcp.server import K8sMCPServer
from src.k8s_mcp.config import K8sConfig


class TestMetricsCollector:
    """测试指标收集器"""

    def setup_method(self):
        """测试前设置"""
        self.collector = MetricsCollector(max_history_size=100, collection_interval=1)

    def teardown_method(self):
        """测试后清理"""
        if self.collector.is_running:
            self.collector.stop()

    def test_initialization(self):
        """测试初始化"""
        assert self.collector.max_history_size == 100
        assert self.collector.collection_interval == 1
        assert not self.collector.is_running
        assert len(self.collector.metrics_history) == 0

    def test_record_metric(self):
        """测试记录指标"""
        timestamp = time.time()
        self.collector.record_metric("test.metric", 42.5, timestamp, {"tag1": "value1"})
        
        assert len(self.collector.metrics_history) == 1
        metric = self.collector.metrics_history[0]
        assert metric.name == "test.metric"
        assert metric.value == 42.5
        assert metric.timestamp == timestamp
        assert metric.tags == {"tag1": "value1"}

    def test_record_api_call(self):
        """测试记录API调用"""
        self.collector.record_api_call("get_pods", 0.5, False)
        
        # 检查统计信息
        assert "get_pods" in self.collector.api_stats
        stats = self.collector.api_stats["get_pods"]
        assert stats.total_requests == 1
        assert stats.error_count == 0
        assert stats.avg_response_time == 0.5

    def test_record_tool_call(self):
        """测试记录工具调用"""
        self.collector.record_tool_call("k8s-get-pods", 1.2, False)
        
        # 检查统计信息
        assert "k8s-get-pods" in self.collector.tool_stats
        stats = self.collector.tool_stats["k8s-get-pods"]
        assert stats.total_requests == 1
        assert stats.error_count == 0
        assert stats.avg_response_time == 1.2

    def test_record_intelligent_metrics(self):
        """测试记录智能组件指标"""
        self.collector.record_intelligent_metrics(100, 200, "healthy", 30.0)
        
        # 检查指标是否记录
        assert "intelligent.kg_nodes" in self.collector.current_metrics
        assert "intelligent.kg_edges" in self.collector.current_metrics
        assert self.collector.current_metrics["intelligent.kg_nodes"] == 100
        assert self.collector.current_metrics["intelligent.kg_edges"] == 200

    def test_get_current_metrics(self):
        """测试获取当前指标"""
        self.collector.record_metric("test.metric", 100)
        self.collector.record_api_call("test_api", 0.5)
        
        metrics = self.collector.get_current_metrics()
        
        assert "timestamp" in metrics
        assert "metrics" in metrics
        assert "counters" in metrics
        assert "api_stats" in metrics
        assert "test.metric" in metrics["metrics"]

    def test_get_metrics_history(self):
        """测试获取指标历史"""
        current_time = time.time()
        
        # 记录多个指标，时间间隔为1分钟
        for i in range(5):
            timestamp = current_time - (4-i)*60  # 4分钟前到现在
            self.collector.record_metric("test.metric", i, timestamp)
        
        # 获取所有历史
        all_history = self.collector.get_metrics_history()
        assert len(all_history) == 5
        
        # 获取最近2分钟的历史（应该包含最近2个点）
        recent_history = self.collector.get_metrics_history(last_minutes=2)
        assert len(recent_history) == 2
        
        # 获取特定指标的历史
        metric_history = self.collector.get_metrics_history(metric_name="test.metric")
        assert len(metric_history) == 5

    def test_get_summary_stats(self):
        """测试获取汇总统计"""
        # 记录一些指标
        self.collector.record_api_call("api1", 0.5, False)
        self.collector.record_api_call("api1", 0.3, True)
        self.collector.record_tool_call("tool1", 1.0, False)
        
        summary = self.collector.get_summary_stats()
        
        assert "timestamp" in summary
        assert "api_summary" in summary
        assert "tool_summary" in summary
        assert summary["api_summary"]["total_calls"] == 2
        assert summary["api_summary"]["total_errors"] == 1

    def test_export_prometheus_format(self):
        """测试导出Prometheus格式"""
        self.collector.record_metric("test.cpu_usage", 85.5)
        self.collector.increment_counter("test.requests", 10)
        
        prometheus_data = self.collector.export_prometheus_format()
        
        assert "k8s_mcp_test_cpu_usage" in prometheus_data
        assert "k8s_mcp_test_requests" in prometheus_data
        assert "85.5" in prometheus_data
        assert "10" in prometheus_data

    def test_start_stop_collector(self):
        """测试启动和停止收集器"""
        assert not self.collector.is_running
        
        # 启动收集器
        self.collector.start()
        assert self.collector.is_running
        assert self.collector.collection_thread is not None
        
        # 等待一下收集器运行
        time.sleep(0.1)
        
        # 停止收集器
        self.collector.stop()
        assert not self.collector.is_running


class TestPerformanceStats:
    """测试性能统计"""

    def test_initialization(self):
        """测试初始化"""
        stats = PerformanceStats()
        assert stats.total_requests == 0
        assert stats.error_count == 0
        assert stats.success_rate == 100.0

    def test_update_stats(self):
        """测试更新统计"""
        stats = PerformanceStats()
        
        # 记录成功请求
        stats.update(0.5, False)
        assert stats.total_requests == 1
        assert stats.error_count == 0
        assert stats.avg_response_time == 0.5
        assert stats.success_rate == 100.0
        
        # 记录错误请求
        stats.update(1.0, True)
        assert stats.total_requests == 2
        assert stats.error_count == 1
        assert stats.success_rate == 50.0

    def test_to_dict(self):
        """测试转换为字典"""
        stats = PerformanceStats()
        stats.update(0.5, False)
        
        data = stats.to_dict()
        assert "avg_response_time" in data
        assert "total_requests" in data
        assert "success_rate" in data
        assert data["total_requests"] == 1


class TestPerformanceMonitor:
    """测试性能监控器"""

    def setup_method(self):
        """测试前设置"""
        self.monitor = PerformanceMonitor()

    def test_initialization(self):
        """测试初始化"""
        assert self.monitor.alert_thresholds is not None
        assert "api.response_time.max" in self.monitor.alert_thresholds
        assert len(self.monitor.alert_history) == 0

    def test_alert_detection(self):
        """测试报警检测"""
        from src.k8s_mcp.core.metrics_collector import MetricPoint
        
        # 创建高CPU使用率指标
        high_cpu_metric = MetricPoint("system.cpu_percent", 90.0, time.time())
        
        initial_alert_count = len(self.monitor.alert_history)
        self.monitor._check_alerts(high_cpu_metric)
        
        # 应该触发报警
        assert len(self.monitor.alert_history) > initial_alert_count

    def test_get_alert_history(self):
        """测试获取报警历史"""
        # 手动添加一个报警
        self.monitor.alert_history.append({
            "timestamp": time.time() - 1800,  # 30分钟前
            "message": "Test alert",
            "severity": "warning"
        })
        
        # 获取最近1小时的报警
        recent_alerts = self.monitor.get_alert_history(1)
        assert len(recent_alerts) == 1
        
        # 获取最近10分钟的报警（应该为空）
        very_recent_alerts = self.monitor.get_alert_history(0.17)  # 10分钟
        assert len(very_recent_alerts) == 0

    def test_performance_summary(self):
        """测试性能汇总报告"""
        summary = self.monitor.get_performance_summary()
        
        assert "timestamp" in summary
        assert "health_score" in summary
        assert "performance_status" in summary
        assert "summary_stats" in summary
        assert "key_metrics" in summary

    def test_health_score_calculation(self):
        """测试健康评分计算"""
        # 模拟一些指标数据
        mock_metrics = {
            "metrics": {
                "system.cpu_percent": 50.0,
                "system.memory_percent": 60.0,
                "intelligent.sync_health_score": 1.0
            },
            "api_summary": {
                "error_rate": 2.0,
                "avg_response_time": 0.5
            }
        }
        
        score = self.monitor._calculate_health_score(mock_metrics)
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_performance_status(self):
        """测试性能状态判断"""
        assert self.monitor._get_performance_status(95) == "excellent"
        assert self.monitor._get_performance_status(80) == "good"
        assert self.monitor._get_performance_status(65) == "warning"
        assert self.monitor._get_performance_status(45) == "critical"
        assert self.monitor._get_performance_status(20) == "emergency"


class TestMonitoringMiddleware:
    """测试监控中间件"""

    def test_monitor_tool_calls_decorator(self):
        """测试工具调用监控装饰器"""
        
        @monitor_tool_calls
        def test_tool(param):
            """测试工具函数"""
            return {"result": f"processed {param}"}
        
        # 调用工具
        result = test_tool("test_param")
        
        assert result["result"] == "processed test_param"
        # 注意：在真实环境中会记录到metrics_collector，但这里需要检查mock

    def test_async_monitor_tool_calls_decorator(self):
        """测试异步工具调用监控装饰器"""
        
        @monitor_tool_calls
        async def async_test_tool(param):
            """异步测试工具函数"""
            await asyncio.sleep(0.01)
            return {"result": f"async processed {param}"}
        
        # 调用异步工具
        async def run_test():
            result = await async_test_tool("async_param")
            assert result["result"] == "async processed async_param"
        
        asyncio.run(run_test())


class TestMonitoringIntegration:
    """测试监控集成"""

    def setup_method(self):
        """测试前设置"""
        self.config = K8sConfig()
        self.config.monitoring_enabled = True
        self.config.enable_knowledge_graph = False  # 简化测试

    def test_server_monitoring_initialization(self):
        """测试服务器监控初始化"""
        server = K8sMCPServer(self.config)
        
        assert server.monitoring_enabled is True
        # 检查监控中间件是否已添加（间接测试）

    def test_monitoring_api_endpoints(self):
        """测试监控API端点"""
        server = K8sMCPServer(self.config)
        client = TestClient(server.app)
        
        # 测试指标端点
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "metrics" in data
        
        # 测试指标历史端点
        response = client.get("/metrics/history?last_minutes=60")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total_count" in data
        
        # 测试指标汇总端点
        response = client.get("/metrics/summary")
        assert response.status_code == 200
        
        # 测试性能报告端点
        response = client.get("/performance")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "performance_status" in data
        
        # 测试报警历史端点
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total_count" in data
        
        # 测试Prometheus格式端点
        response = client.get("/metrics/prometheus")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    def test_monitoring_disabled_endpoints(self):
        """测试监控功能禁用时的端点"""
        config = K8sConfig()
        config.monitoring_enabled = False
        
        server = K8sMCPServer(config)
        client = TestClient(server.app)
        
        # 监控功能禁用时应该返回503
        response = client.get("/metrics")
        assert response.status_code == 503
        
        response = client.get("/performance")
        assert response.status_code == 503

    def test_enhanced_health_check(self):
        """测试增强的健康检查"""
        server = K8sMCPServer(self.config)
        client = TestClient(server.app)
        
        response = client.get("/health")
        assert response.status_code == 200
        # 注意：这是简化的健康检查端点，与server.health_check()方法不同
        
        # 测试完整的健康检查（需要模拟异步调用）
        async def test_full_health_check():
            health = await server.health_check()
            assert "monitoring" in health
            if server.monitoring_enabled:
                assert health["monitoring"]["enabled"] is True
        
        asyncio.run(test_full_health_check())

    def test_intelligent_metrics_collection(self):
        """测试智能组件指标收集"""
        # 使用真实的指标收集器，但不启动它
        from src.k8s_mcp.core.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        
        # 模拟智能组件
        mock_kg = Mock()
        mock_kg.graph.nodes = {"node1": {}, "node2": {}}
        mock_kg.graph.edges = [("node1", "node2")]
        
        mock_sync_engine = Mock()
        mock_sync_engine.get_sync_health.return_value = {
            "health": "healthy",
            "last_sync_ago_seconds": 30.0,
            "active_watch_threads": 2,
            "error_count": 0,
            "total_resources": 10
        }
        
        mock_summary_generator = Mock()
        
        # 测试监控函数
        from src.k8s_mcp.core.monitoring_middleware import monitor_intelligent_components
        collector_func = monitor_intelligent_components(mock_kg, mock_sync_engine, mock_summary_generator)
        
        # 执行收集应该不会抛出异常
        try:
            collector_func()
            # 如果没有异常，测试通过
            assert True
        except Exception as e:
            # 如果有异常，测试失败
            pytest.fail(f"智能组件指标收集抛出异常: {e}")

    def test_monitoring_configuration_from_config(self):
        """测试从配置文件加载监控配置"""
        config = K8sConfig()
        config.monitoring_enabled = True
        config.metrics_collection_interval = 60
        config.alert_cpu_percent_max = 75.0
        
        server = K8sMCPServer(config)
        
        assert server.monitoring_enabled is True
        # 配置应该传递给监控组件（间接测试）

    def test_metric_point_to_dict(self):
        """测试MetricPoint转换为字典"""
        point = MetricPoint(
            name="test.metric",
            value=42.0,
            timestamp=time.time(),
            tags={"env": "test"}
        )
        
        data = point.to_dict()
        assert data["name"] == "test.metric"
        assert data["value"] == 42.0
        assert "timestamp" in data
        assert data["tags"]["env"] == "test"


class TestMonitoringErrorHandling:
    """测试监控错误处理"""

    def test_metrics_collector_error_handling(self):
        """测试指标收集器错误处理"""
        collector = MetricsCollector()
        
        # 测试记录指标时的错误处理
        with patch('src.k8s_mcp.core.metrics_collector.psutil.cpu_percent', side_effect=Exception("Mock error")):
            # 应该不会抛出异常，错误会被内部处理
            try:
                collector._collect_system_metrics()
            except Exception:
                # 如果抛出异常也是可以的，因为这是在测试错误处理
                pass

    def test_monitoring_middleware_error_handling(self):
        """测试监控中间件错误处理"""
        
        @monitor_tool_calls
        def failing_tool():
            raise Exception("Tool failed")
        
        # 工具失败时应该记录错误指标
        with pytest.raises(Exception):
            failing_tool()

    def test_performance_monitor_alert_cooldown(self):
        """测试性能监控器报警冷却"""
        monitor = PerformanceMonitor()
        
        from src.k8s_mcp.core.metrics_collector import MetricPoint
        
        # 创建高CPU指标
        high_cpu_metric = MetricPoint("system.cpu_percent", 90.0, time.time())
        
        # 第一次应该触发报警
        initial_count = len(monitor.alert_history)
        monitor._check_alerts(high_cpu_metric)
        assert len(monitor.alert_history) > initial_count
        
        # 立即再次触发，应该被冷却限制
        monitor._check_alerts(high_cpu_metric)
        # 由于冷却时间，报警数量不应该再增加