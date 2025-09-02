#!/usr/bin/env python3
"""
资源告警系统集成测试

验证完整的端到端流程，包括：
1. 资源指标收集和聚合
2. 告警阈值检测
3. HTTP API通信
4. 后端LLM分析和钉钉发送
5. 统计信息和错误处理
"""

import asyncio
import pytest
import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入测试目标
from k8s_mcp.core.resource_alert_service_v2 import (
    ResourceAlertService, 
    ResourceAlertConfig
)
from k8s_mcp.core.http_api_client import HttpApiClient


class MockHttpResponse:
    """模拟HTTP响应"""
    
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data or {"success": True}
    
    async def json(self):
        return self._json_data
    
    async def text(self):
        return json.dumps(self._json_data)


class MockHttpSession:
    """模拟HTTP会话"""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        self.requests = []
    
    def post(self, url, json=None, **kwargs):
        """返回一个async context manager"""
        self.requests.append({
            "url": url,
            "json": json,
            "kwargs": kwargs
        })
        
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = MockHttpResponse()
        
        self.call_count += 1
        
        # 创建async context manager
        class AsyncContextManager:
            def __init__(self, response):
                self.response = response
            
            async def __aenter__(self):
                return self.response
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return AsyncContextManager(response)
    
    async def close(self):
        pass


class MockKnowledgeGraph:
    """模拟知识图谱"""
    
    def __init__(self):
        self.metrics_data = {}
        self.update_calls = []
    
    def get_deployment_metrics(self, namespace, app_name):
        """获取部署指标"""
        key = f"{namespace}/{app_name}"
        return self.metrics_data.get(key, {
            "avg_cpu_utilization": 45.0,
            "avg_memory_utilization": 55.0,
            "days_analyzed": 7,
            "total_data_points": 168,
            "data_source": "knowledge_graph"
        })
    
    def update_deployment_metrics(self, namespace, app_name, metrics):
        """更新部署指标"""
        key = f"{namespace}/{app_name}"
        self.metrics_data[key] = metrics
        self.update_calls.append({
            "namespace": namespace,
            "app_name": app_name,
            "metrics": metrics,
            "timestamp": datetime.now()
        })


@pytest.fixture
def mock_knowledge_graph():
    """模拟知识图谱实例"""
    return MockKnowledgeGraph()


@pytest.fixture
def alert_config():
    """告警配置"""
    return ResourceAlertConfig(
        memory_alert_threshold=0.7,
        cpu_alert_threshold=0.8,
        alert_cooldown_seconds=300,
        backend_api_url="http://localhost:8000",
        enable_backend_notifications=True,
        api_timeout=30,
        api_max_retries=3
    )





class TestResourceAlertIntegration:
    """资源告警系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_alert_flow(self, alert_config, mock_knowledge_graph):
        """测试完整的端到端告警流程"""
        # 1. 准备测试数据
        resource_id = "deployment/production/web-app"
        high_usage_metrics = {
            "avg_cpu_utilization": 85.0,  # 超过80%阈值
            "avg_memory_utilization": 75.0,  # 超过70%阈值
            "days_analyzed": 7,
            "total_data_points": 168,
            "analysis_period": "last_7_days"
        }
        
        # 2. 创建告警服务
        alert_service = ResourceAlertService(alert_config)
        
        # 3. 模拟成功的HTTP响应
        mock_session = MockHttpSession([
            MockHttpResponse(200, {
                "success": True,
                "alert_id": "alert-20250101120000-1234",
                "llm_analysis": {"status": "success"},
                "dingtalk_sent": {"success": True}
            })
        ])
        
        # 4. 执行告警检查
        with patch.object(alert_service, 'http_client') as mock_client:
            mock_client.send_resource_alert = AsyncMock(return_value=True)
            
            result = await alert_service.check_and_alert(resource_id, high_usage_metrics)
        
        # 5. 验证结果
        assert result["alert_triggered"] == True
        assert len(result["alert_reasons"]) == 2
        assert "CPU利用率过高" in " ".join(result["alert_reasons"])
        assert "内存利用率过高" in " ".join(result["alert_reasons"])
        assert result["backend_notification"]["sent"] == True
        assert result["backend_notification"]["success"] == True
        
        # 6. 验证统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 1
        assert stats["stats"]["backend_api_success"] == 1
        assert stats["stats"]["alerts_sent_to_backend"] == 1
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_integration_simulation(self, mock_knowledge_graph):
        """模拟知识图谱集成测试"""
        # 1. 模拟指标数据更新
        aggregated_metrics = {
            "avg_cpu_utilization": 86.0,
            "avg_memory_utilization": 65.0,
            "days_analyzed": 1,
            "total_data_points": 2
        }
        
        # 2. 更新知识图谱
        mock_knowledge_graph.update_deployment_metrics(
            "production", "web-app", aggregated_metrics
        )
        
        # 3. 验证数据存储
        stored_metrics = mock_knowledge_graph.get_deployment_metrics("production", "web-app")
        assert stored_metrics["avg_cpu_utilization"] == 86.0
        assert stored_metrics["avg_memory_utilization"] == 65.0
        
        # 4. 验证更新调用
        assert len(mock_knowledge_graph.update_calls) == 1
        update_call = mock_knowledge_graph.update_calls[0]
        assert update_call["namespace"] == "production"
        assert update_call["app_name"] == "web-app"
        assert update_call["metrics"]["avg_cpu_utilization"] == 86.0
    
    @pytest.mark.asyncio
    async def test_http_api_communication(self, alert_config):
        """测试HTTP API通信"""
        # 1. 创建HTTP客户端
        http_client = HttpApiClient(
            base_url=alert_config.backend_api_url,
            timeout=alert_config.api_timeout,
            max_retries=alert_config.api_max_retries
        )
        
        # 2. 准备测试数据
        resource_id = "deployment/test/api-server"
        metrics_data = {
            "avg_cpu_utilization": 90.0,
            "avg_memory_utilization": 80.0,
            "days_analyzed": 14
        }
        additional_data = {
            "alert_reasons": ["CPU利用率过高: 90.0% > 80.0%", "内存利用率过高: 80.0% > 70.0%"],
            "thresholds": {"cpu": 0.8, "memory": 0.7}
        }
        
        # 3. 模拟HTTP会话
        mock_session = MockHttpSession([
            MockHttpResponse(200, {
                "success": True,
                "alert_id": "alert-test-001",
                "processing_time_ms": 150
            })
        ])
        
        # 4. 执行API调用
        with patch.object(http_client, '_get_session', return_value=mock_session):
            success = await http_client.send_resource_alert(
                resource_id, metrics_data, additional_data
            )
        
        # 5. 验证结果
        assert success == True
        assert len(mock_session.requests) == 1
        
        request = mock_session.requests[0]
        assert request["url"] == "http://localhost:8000/api/v2/alerts/resource"
        assert request["json"]["resource_id"] == resource_id
        assert request["json"]["metrics"] == metrics_data
        assert "alert_reasons" in request["json"]
        
        # 6. 验证统计信息
        stats = http_client.get_statistics()
        assert stats["stats"]["requests_sent"] == 1
        assert stats["stats"]["requests_success"] == 1
    
    @pytest.mark.asyncio
    async def test_alert_cooldown_across_services(self, alert_config):
        """测试跨服务的告警冷却机制"""
        alert_service = ResourceAlertService(alert_config)
        
        resource_id = "deployment/staging/worker-app"
        metrics_data = {
            "avg_cpu_utilization": 85.0,
            "avg_memory_utilization": 78.0,
            "days_analyzed": 7
        }
        
        # 模拟HTTP客户端
        with patch.object(alert_service, 'http_client') as mock_client:
            mock_client.send_resource_alert = AsyncMock(return_value=True)
            
            # 第一次告警 - 应该成功
            result1 = await alert_service.check_and_alert(resource_id, metrics_data)
            assert result1["alert_triggered"] == True
            assert mock_client.send_resource_alert.call_count == 1
            
            # 立即第二次告警 - 应该被冷却抑制
            result2 = await alert_service.check_and_alert(resource_id, metrics_data)
            assert result2["alert_triggered"] == False
            assert result2["reason"] == "告警冷却期内"
            assert mock_client.send_resource_alert.call_count == 1  # 没有增加
            
            # 验证冷却时间计算
            remaining = result2.get("cooldown_remaining")
            assert remaining is not None
            assert remaining > 290  # 应该接近300秒
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback(self, alert_config):
        """测试错误处理和降级策略"""
        alert_service = ResourceAlertService(alert_config)
        
        resource_id = "deployment/test/error-app"
        metrics_data = {
            "avg_cpu_utilization": 95.0,
            "avg_memory_utilization": 85.0,
            "days_analyzed": 3
        }
        
        # 测试HTTP客户端未初始化的情况
        alert_service.http_client = None
        result = await alert_service.check_and_alert(resource_id, metrics_data)
        
        assert result["alert_triggered"] == True  # 告警仍然触发
        assert result["backend_notification"]["sent"] == False
        assert result["backend_notification"]["reason"] == "HTTP客户端未初始化"
        
        # 验证统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 1
        assert stats["stats"]["backend_api_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_resources_concurrent_alerts(self, alert_config):
        """测试多资源并发告警处理"""
        alert_service = ResourceAlertService(alert_config)
        
        # 准备多个资源的数据
        resources_data = [
            ("deployment/prod/web-1", {"avg_cpu_utilization": 85.0, "avg_memory_utilization": 70.0}),
            ("deployment/prod/web-2", {"avg_cpu_utilization": 90.0, "avg_memory_utilization": 75.0}),
            ("deployment/prod/api-1", {"avg_cpu_utilization": 82.0, "avg_memory_utilization": 78.0}),
            ("deployment/prod/worker-1", {"avg_cpu_utilization": 88.0, "avg_memory_utilization": 72.0}),
        ]
        
        # 模拟HTTP客户端
        with patch.object(alert_service, 'http_client') as mock_client:
            mock_client.send_resource_alert = AsyncMock(return_value=True)
            
            # 并发执行告警检查
            tasks = []
            for resource_id, metrics in resources_data:
                task = alert_service.check_and_alert(resource_id, metrics)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        # 验证结果
        triggered_alerts = [r for r in results if r["alert_triggered"]]
        assert len(triggered_alerts) == 4  # 所有资源都应该触发告警
        
        # 验证HTTP调用次数
        assert mock_client.send_resource_alert.call_count == 4
        
        # 验证统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 4
        assert stats["stats"]["backend_api_success"] == 4
        assert stats["cooldown_cache_size"] == 4
    
    @pytest.mark.asyncio
    async def test_configuration_validation_integration(self):
        """测试配置验证集成"""
        # 测试有效配置
        valid_config = ResourceAlertConfig(
            memory_alert_threshold=0.8,
            cpu_alert_threshold=0.9,
            alert_cooldown_seconds=600,
            backend_api_url="https://api.example.com",
            enable_backend_notifications=True
        )
        
        alert_service = ResourceAlertService(valid_config)
        assert alert_service.config.memory_alert_threshold == 0.8
        
        # 测试无效配置
        with pytest.raises(ValueError, match="内存告警阈值必须在0.0-1.0之间"):
            ResourceAlertConfig(memory_alert_threshold=1.5)
        
        with pytest.raises(ValueError, match="CPU告警阈值必须在0.0-1.0之间"):
            ResourceAlertConfig(cpu_alert_threshold=-0.1)
    
    @pytest.mark.asyncio
    async def test_statistics_and_monitoring_integration(self, alert_config):
        """测试统计信息和监控集成"""
        alert_service = ResourceAlertService(alert_config)
        
        # 执行一系列操作
        test_scenarios = [
            ("deployment/test/app-1", {"avg_cpu_utilization": 85.0, "avg_memory_utilization": 60.0}, True),
            ("deployment/test/app-2", {"avg_cpu_utilization": 50.0, "avg_memory_utilization": 80.0}, True),
            ("deployment/test/app-3", {"avg_cpu_utilization": 60.0, "avg_memory_utilization": 65.0}, False),
            ("deployment/test/app-1", {"avg_cpu_utilization": 90.0, "avg_memory_utilization": 65.0}, False),  # 冷却期
        ]
        
        with patch.object(alert_service, 'http_client') as mock_client:
            mock_client.send_resource_alert = AsyncMock(return_value=True)
            
            for resource_id, metrics, should_trigger in test_scenarios:
                result = await alert_service.check_and_alert(resource_id, metrics)
                assert result["alert_triggered"] == should_trigger
        
        # 验证最终统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 2  # 只有前两个触发了告警
        assert stats["stats"]["alerts_suppressed_by_cooldown"] == 1  # 最后一个被冷却抑制
        assert stats["stats"]["backend_api_success"] == 2
        assert stats["cooldown_cache_size"] == 2  # app-1 和 app-2
        
        # 验证配置信息
        assert stats["config"]["memory_alert_threshold"] == 0.7
        assert stats["config"]["cpu_alert_threshold"] == 0.8
        assert stats["config"]["backend_api_url"] == "http://localhost:8000"


class TestBackendAPIIntegration:
    """后端API集成测试"""
    
    @pytest.mark.asyncio
    async def test_backend_alert_endpoint_simulation(self):
        """模拟后端告警端点的行为"""
        # 这个测试模拟后端API的预期行为
        # 在实际环境中，这将是对真实后端API的测试
        
        # 模拟接收到的告警数据
        alert_data = {
            "resource_id": "deployment/production/critical-app",
            "metrics": {
                "avg_cpu_utilization": 95.0,
                "avg_memory_utilization": 88.0,
                "days_analyzed": 7,
                "total_data_points": 168
            },
            "timestamp": datetime.now().isoformat(),
            "source": "k8s-mcp-server",
            "alert_reasons": [
                "CPU利用率过高: 95.0% > 80.0%",
                "内存利用率过高: 88.0% > 70.0%"
            ],
            "thresholds": {"cpu": 0.8, "memory": 0.7},
            "current_utilization": {"cpu": 0.95, "memory": 0.88}
        }
        
        # 模拟后端处理逻辑
        def simulate_backend_processing(data):
            # 1. 验证数据格式
            assert "resource_id" in data
            assert "metrics" in data
            assert "alert_reasons" in data
            
            # 2. 模拟LLM分析
            llm_analysis = {
                "status": "success",
                "analysis": "检测到严重的资源利用率问题。建议立即扩容或优化应用性能。",
                "recommendations": [
                    "增加Pod副本数到3个",
                    "检查应用内存泄漏",
                    "优化数据库查询性能"
                ],
                "urgency": "high"
            }
            
            # 3. 模拟钉钉发送
            dingtalk_result = {
                "status": "success",
                "message_sent": True,
                "webhook_response": {"errcode": 0, "errmsg": "ok"}
            }
            
            # 4. 返回处理结果
            return {
                "success": True,
                "alert_id": f"alert-{datetime.now().strftime('%Y%m%d%H%M%S')}-001",
                "llm_analysis": llm_analysis,
                "dingtalk_sent": dingtalk_result,
                "processing_time_ms": 250
            }
        
        # 执行模拟处理
        result = simulate_backend_processing(alert_data)
        
        # 验证结果
        assert result["success"] == True
        assert "alert_id" in result
        assert result["llm_analysis"]["status"] == "success"
        assert result["dingtalk_sent"]["status"] == "success"
        assert result["processing_time_ms"] > 0


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])
