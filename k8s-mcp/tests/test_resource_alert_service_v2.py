"""
测试ResourceAlertService V2功能 - 重构版本

验证新的ResourceAlertService V2的各项功能，包括：
1. 告警检测和阈值验证
2. 冷却机制
3. HTTP API调用
4. 统计信息管理
5. 错误处理
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.core.resource_alert_service_v2 import (
    ResourceAlertService, 
    ResourceAlertConfig
)
from k8s_mcp.core.http_api_client import HttpApiClient


@pytest.fixture
def alert_config():
    """创建测试用的告警配置"""
    return ResourceAlertConfig(
        memory_alert_threshold=0.7,
        cpu_alert_threshold=0.8,
        alert_cooldown_seconds=300,
        backend_api_url="http://localhost:8000",
        enable_backend_notifications=True,
        api_timeout=30,
        api_max_retries=3
    )


@pytest.fixture
def mock_http_client():
    """模拟HTTP客户端"""
    client = Mock(spec=HttpApiClient)
    client.send_resource_alert = AsyncMock(return_value=True)
    client.get_statistics = Mock(return_value={
        "requests_sent": 5,
        "requests_success": 4,
        "requests_failed": 1
    })
    return client


@pytest.fixture
def alert_service(alert_config):
    """创建测试用的告警服务"""
    service = ResourceAlertService(alert_config)
    return service


@pytest.fixture
def sample_metrics_data():
    """样本指标数据"""
    return {
        "avg_cpu_utilization": 85.0,  # 85% - 超过80%阈值
        "avg_memory_utilization": 72.0,  # 72% - 超过70%阈值
        "days_analyzed": 7,
        "total_data_points": 168,
        "analysis_period": "last_7_days"
    }


class TestResourceAlertConfig:
    """测试ResourceAlertConfig配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ResourceAlertConfig()
        
        assert config.memory_alert_threshold == 0.7
        assert config.cpu_alert_threshold == 0.8
        assert config.alert_cooldown_seconds == 300
        assert config.backend_api_url is None
        assert config.enable_backend_notifications == True
        assert config.api_timeout == 30
        assert config.api_max_retries == 3
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ResourceAlertConfig(
            memory_alert_threshold=0.8,
            cpu_alert_threshold=0.9,
            alert_cooldown_seconds=600,
            backend_api_url="http://test-api.com",
            enable_backend_notifications=False
        )
        
        assert config.memory_alert_threshold == 0.8
        assert config.cpu_alert_threshold == 0.9
        assert config.alert_cooldown_seconds == 600
        assert config.backend_api_url == "http://test-api.com"
        assert config.enable_backend_notifications == False
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试无效的阈值
        with pytest.raises(ValueError, match="内存告警阈值必须在0.0-1.0之间"):
            ResourceAlertConfig(memory_alert_threshold=1.5)
        
        with pytest.raises(ValueError, match="CPU告警阈值必须在0.0-1.0之间"):
            ResourceAlertConfig(cpu_alert_threshold=-0.1)
        
        with pytest.raises(ValueError, match="告警冷却时间不能为负数"):
            ResourceAlertConfig(alert_cooldown_seconds=-1)


class TestResourceAlertService:
    """测试ResourceAlertService V2功能"""
    
    def test_service_initialization(self, alert_config):
        """测试服务初始化"""
        service = ResourceAlertService(alert_config)
        
        assert service.config == alert_config
        assert len(service.alert_cooldown_cache) == 0
        assert service.stats["alerts_detected"] == 0
        assert service.stats["alerts_sent_to_backend"] == 0
    
    @pytest.mark.asyncio
    async def test_threshold_detection(self, alert_service, sample_metrics_data):
        """测试阈值检测功能"""
        resource_id = "deployment/test/demo-app"
        
        # 测试超过阈值的情况
        result = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        
        assert result["alert_triggered"] == True
        assert len(result["alert_reasons"]) == 2  # CPU和内存都超过阈值
        # 验证告警原因包含CPU和内存（不依赖顺序）
        alert_reasons_text = " ".join(result["alert_reasons"])
        assert "CPU利用率过高" in alert_reasons_text
        assert "内存利用率过高" in alert_reasons_text
        
        # 验证统计信息更新
        assert alert_service.stats["alerts_detected"] == 1
    
    @pytest.mark.asyncio
    async def test_no_alert_below_threshold(self, alert_service):
        """测试未达到阈值时不触发告警"""
        resource_id = "deployment/test/low-usage-app"
        low_usage_metrics = {
            "avg_cpu_utilization": 50.0,  # 50% - 低于80%阈值
            "avg_memory_utilization": 60.0,  # 60% - 低于70%阈值
            "days_analyzed": 7,
            "total_data_points": 168
        }
        
        result = await alert_service.check_and_alert(resource_id, low_usage_metrics)
        
        assert result["alert_triggered"] == False
        assert result["reason"] == "未达到告警阈值"
        assert "thresholds" in result
        assert "current_utilization" in result
        
        # 验证统计信息未变化
        assert alert_service.stats["alerts_detected"] == 0
    
    @pytest.mark.asyncio
    async def test_cooldown_mechanism(self, alert_service, sample_metrics_data):
        """测试告警冷却机制"""
        resource_id = "deployment/test/demo-app"
        
        # 第一次告警应该成功
        result1 = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        assert result1["alert_triggered"] == True
        assert alert_service.stats["alerts_detected"] == 1
        
        # 立即再次告警应该被冷却抑制
        result2 = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        assert result2["alert_triggered"] == False
        assert result2["reason"] == "告警冷却期内"
        assert "cooldown_remaining" in result2
        assert result2["cooldown_remaining"] > 0
        assert alert_service.stats["alerts_suppressed_by_cooldown"] == 1
        
        # 验证告警检测次数没有增加
        assert alert_service.stats["alerts_detected"] == 1
    
    @pytest.mark.asyncio
    async def test_backend_notification_enabled(self, alert_service, sample_metrics_data, mock_http_client):
        """测试启用后端通知时的行为"""
        resource_id = "deployment/test/demo-app"
        
        # 模拟HTTP客户端
        with patch.object(alert_service, 'http_client', mock_http_client):
            result = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        
        assert result["alert_triggered"] == True
        assert "backend_notification" in result
        
        # 验证HTTP客户端被调用
        mock_http_client.send_resource_alert.assert_called_once()
        call_args = mock_http_client.send_resource_alert.call_args
        assert call_args[0][0] == resource_id  # resource_id参数
        assert call_args[0][1] == sample_metrics_data  # metrics_data参数
        
        # 验证统计信息
        assert alert_service.stats["backend_api_success"] == 1
        assert alert_service.stats["alerts_sent_to_backend"] == 1
    
    @pytest.mark.asyncio
    async def test_backend_notification_disabled(self, alert_config, sample_metrics_data):
        """测试禁用后端通知时的行为"""
        # 创建禁用后端通知的配置
        alert_config.enable_backend_notifications = False
        alert_service = ResourceAlertService(alert_config)
        
        resource_id = "deployment/test/demo-app"
        result = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        
        assert result["alert_triggered"] == True
        assert result["backend_notification"]["sent"] == False
        assert result["backend_notification"]["reason"] == "后端通知已禁用"
    
    @pytest.mark.asyncio
    async def test_backend_api_failure(self, alert_service, sample_metrics_data, mock_http_client):
        """测试后端API调用失败的情况"""
        resource_id = "deployment/test/demo-app"
        
        # 模拟API调用失败
        mock_http_client.send_resource_alert = AsyncMock(return_value=False)
        
        with patch.object(alert_service, 'http_client', mock_http_client):
            result = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        
        assert result["alert_triggered"] == True
        assert result["backend_notification"]["sent"] == True
        assert result["backend_notification"]["success"] == False
        
        # 验证失败统计
        assert alert_service.stats["backend_api_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_backend_api_exception(self, alert_service, sample_metrics_data, mock_http_client):
        """测试后端API调用异常的情况"""
        resource_id = "deployment/test/demo-app"
        
        # 模拟API调用异常
        mock_http_client.send_resource_alert = AsyncMock(side_effect=Exception("网络连接失败"))
        
        with patch.object(alert_service, 'http_client', mock_http_client):
            result = await alert_service.check_and_alert(resource_id, sample_metrics_data)
        
        assert result["alert_triggered"] == True
        assert result["backend_notification"]["sent"] == True
        assert result["backend_notification"]["success"] == False
        assert "网络连接失败" in result["backend_notification"]["reason"]
        
        # 验证异常统计
        assert alert_service.stats["backend_api_failed"] == 1
    
    def test_threshold_checking(self, alert_service):
        """测试阈值检查逻辑"""
        # 测试内存超过阈值
        metrics_memory_high = {
            "avg_cpu_utilization": 50.0,  # 正常
            "avg_memory_utilization": 80.0,  # 超过70%阈值
        }
        reasons = alert_service._check_thresholds(metrics_memory_high)
        assert len(reasons) == 1
        assert "内存利用率过高" in reasons[0]
        
        # 测试CPU超过阈值
        metrics_cpu_high = {
            "avg_cpu_utilization": 90.0,  # 超过80%阈值
            "avg_memory_utilization": 60.0,  # 正常
        }
        reasons = alert_service._check_thresholds(metrics_cpu_high)
        assert len(reasons) == 1
        assert "CPU利用率过高" in reasons[0]
        
        # 测试都超过阈值
        metrics_both_high = {
            "avg_cpu_utilization": 85.0,  # 超过80%阈值
            "avg_memory_utilization": 75.0,  # 超过70%阈值
        }
        reasons = alert_service._check_thresholds(metrics_both_high)
        assert len(reasons) == 2
        
        # 测试都不超过阈值
        metrics_normal = {
            "avg_cpu_utilization": 50.0,  # 正常
            "avg_memory_utilization": 60.0,  # 正常
        }
        reasons = alert_service._check_thresholds(metrics_normal)
        assert len(reasons) == 0
    
    def test_cooldown_timing(self, alert_service):
        """测试冷却时间计算"""
        resource_id = "deployment/test/demo-app"
        
        # 没有记录时不在冷却期
        assert not alert_service._is_in_cooldown(resource_id)
        assert alert_service._get_cooldown_remaining(resource_id) is None
        
        # 记录告警时间
        alert_service._record_alert_time(resource_id)
        
        # 刚记录后应该在冷却期
        assert alert_service._is_in_cooldown(resource_id)
        remaining = alert_service._get_cooldown_remaining(resource_id)
        assert remaining is not None
        assert remaining > 295  # 应该接近300秒
        
        # 模拟时间过去
        past_time = datetime.now() - timedelta(seconds=400)
        alert_service.alert_cooldown_cache[resource_id] = past_time
        
        # 超过冷却时间后不应该在冷却期
        assert not alert_service._is_in_cooldown(resource_id)
        assert alert_service._get_cooldown_remaining(resource_id) is None
    
    def test_statistics_tracking(self, alert_service):
        """测试统计信息跟踪"""
        # 初始统计
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 0
        assert stats["stats"]["backend_api_success"] == 0
        assert stats["cooldown_cache_size"] == 0
        
        # 验证配置信息
        assert stats["config"]["memory_alert_threshold"] == 0.7
        assert stats["config"]["cpu_alert_threshold"] == 0.8
        assert stats["config"]["backend_api_url"] == "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_service_cleanup(self, alert_service):
        """测试服务清理"""
        # 添加一些数据
        alert_service.alert_cooldown_cache["test-resource"] = datetime.now()
        assert len(alert_service.alert_cooldown_cache) == 1
        
        # 关闭服务
        await alert_service.close()
        
        # 验证缓存被清理
        assert len(alert_service.alert_cooldown_cache) == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, alert_service):
        """测试错误处理"""
        resource_id = "deployment/test/demo-app"
        
        # 测试无效的指标数据
        invalid_metrics = None
        result = await alert_service.check_and_alert(resource_id, invalid_metrics)
        
        assert result["alert_triggered"] == False
        assert result["error"] == True
        assert "reason" in result


class TestIntegrationScenarios:
    """集成测试场景"""
    
    @pytest.mark.asyncio
    async def test_multiple_resources_alert_flow(self, alert_config):
        """测试多个资源的告警流程"""
        alert_service = ResourceAlertService(alert_config)
        
        # 准备多个资源的指标数据
        resources = {
            "deployment/prod/web-app": {
                "avg_cpu_utilization": 85.0,
                "avg_memory_utilization": 75.0,
                "days_analyzed": 7
            },
            "deployment/prod/api-app": {
                "avg_cpu_utilization": 90.0,
                "avg_memory_utilization": 65.0,
                "days_analyzed": 7
            },
            "deployment/prod/cache-app": {
                "avg_cpu_utilization": 50.0,
                "avg_memory_utilization": 60.0,
                "days_analyzed": 7
            }
        }
        
        # 模拟HTTP客户端成功
        mock_client = Mock(spec=HttpApiClient)
        mock_client.send_resource_alert = AsyncMock(return_value=True)
        
        alert_results = {}
        with patch.object(alert_service, 'http_client', mock_client):
            for resource_id, metrics in resources.items():
                result = await alert_service.check_and_alert(resource_id, metrics)
                alert_results[resource_id] = result
        
        # 验证结果
        assert alert_results["deployment/prod/web-app"]["alert_triggered"] == True  # CPU和内存都超标
        assert alert_results["deployment/prod/api-app"]["alert_triggered"] == True   # CPU超标
        assert alert_results["deployment/prod/cache-app"]["alert_triggered"] == False  # 都正常
        
        # 验证统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 2
        assert stats["stats"]["backend_api_success"] == 2
        assert stats["cooldown_cache_size"] == 2
    
    @pytest.mark.asyncio
    async def test_cooldown_with_different_resources(self, alert_config):
        """测试不同资源的冷却机制独立性"""
        alert_service = ResourceAlertService(alert_config)
        
        metrics = {
            "avg_cpu_utilization": 85.0,
            "avg_memory_utilization": 75.0,
            "days_analyzed": 7
        }
        
        # 对资源A进行告警
        result_a1 = await alert_service.check_and_alert("deployment/prod/app-a", metrics)
        assert result_a1["alert_triggered"] == True
        
        # 对资源B进行告警（应该成功，因为冷却是独立的）
        result_b1 = await alert_service.check_and_alert("deployment/prod/app-b", metrics)
        assert result_b1["alert_triggered"] == True
        
        # 对资源A再次告警（应该被冷却抑制）
        result_a2 = await alert_service.check_and_alert("deployment/prod/app-a", metrics)
        assert result_a2["alert_triggered"] == False
        assert result_a2["reason"] == "告警冷却期内"
        
        # 对资源B再次告警（也应该被冷却抑制）
        result_b2 = await alert_service.check_and_alert("deployment/prod/app-b", metrics)
        assert result_b2["alert_triggered"] == False
        assert result_b2["reason"] == "告警冷却期内"
        
        # 验证统计信息
        stats = alert_service.get_statistics()
        assert stats["stats"]["alerts_detected"] == 2
        assert stats["stats"]["alerts_suppressed_by_cooldown"] == 2
        assert stats["cooldown_cache_size"] == 2


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
