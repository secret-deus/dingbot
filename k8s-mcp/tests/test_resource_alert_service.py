"""
测试ResourceAlertService功能
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.core.resource_alert_service import (
    ResourceAlertService, 
    ResourceAlertConfig,
    create_resource_alert_service
)


@pytest.fixture
def alert_config():
    """创建测试用的告警配置"""
    return ResourceAlertConfig(
        memory_alert_threshold=0.7,
        cpu_alert_threshold=0.8,
        enable_llm_analysis=True,
        enable_dingtalk_alert=True,
        dingtalk_webhook_url="http://test-webhook.com",
        alert_message_max_length=3000
    )


@pytest.fixture
def mock_llm_processor():
    """模拟LLM处理器"""
    processor = Mock()
    
    # 模拟LLM响应
    mock_result = Mock()
    mock_result.content = "这是一个测试的LLM分析结果：内存利用率过高，建议优化应用或增加资源配置。"
    
    processor._chat_without_tools = AsyncMock(return_value=mock_result)
    return processor


@pytest.fixture
def mock_dingtalk_bot():
    """模拟钉钉Bot"""
    bot = Mock()
    bot.send_markdown_message = AsyncMock(return_value=True)
    return bot


@pytest.fixture
def test_metrics_data():
    """测试用的指标数据"""
    return {
        "app_name": "test-app",
        "namespace": "default",
        "memory_utilization_avg_14d": 75.0,  # 75% > 70%阈值
        "cpu_utilization_avg_14d": 60.0,     # 60% < 80%阈值
        "memory_requests": 2.5,
        "cpu_requests": 1.0,
        "last_updated": datetime.now().isoformat()
    }


class TestResourceAlertService:
    """测试ResourceAlertService类"""
    
    def test_service_initialization(self, alert_config, mock_llm_processor, mock_dingtalk_bot):
        """测试服务初始化"""
        service = ResourceAlertService(
            llm_processor=mock_llm_processor,
            dingtalk_bot=mock_dingtalk_bot,
            config=alert_config
        )
        
        assert service.llm_processor == mock_llm_processor
        assert service.dingtalk_bot == mock_dingtalk_bot
        assert service.config == alert_config
        assert isinstance(service.alert_history, dict)
        assert service.stats["alerts_processed"] == 0
    
    def test_factory_function(self):
        """测试工厂函数"""
        service = create_resource_alert_service()
        
        assert isinstance(service, ResourceAlertService)
        assert service.llm_processor is None
        assert service.dingtalk_bot is None
        assert isinstance(service.config, ResourceAlertConfig)
    
    def test_should_alert_memory_threshold(self, alert_config):
        """测试内存阈值告警判断"""
        service = ResourceAlertService(config=alert_config)
        
        # 超过内存阈值
        metrics_high_memory = {
            "memory_utilization_avg_14d": 75.0,  # 75% > 70%
            "cpu_utilization_avg_14d": 60.0      # 60% < 80%
        }
        assert service._should_alert(metrics_high_memory) is True
        
        # 未超过阈值
        metrics_normal = {
            "memory_utilization_avg_14d": 60.0,  # 60% < 70%
            "cpu_utilization_avg_14d": 60.0      # 60% < 80%
        }
        assert service._should_alert(metrics_normal) is False
    
    def test_should_alert_cpu_threshold(self, alert_config):
        """测试CPU阈值告警判断"""
        service = ResourceAlertService(config=alert_config)
        
        # 超过CPU阈值
        metrics_high_cpu = {
            "memory_utilization_avg_14d": 60.0,  # 60% < 70%
            "cpu_utilization_avg_14d": 85.0      # 85% > 80%
        }
        assert service._should_alert(metrics_high_cpu) is True
    
    def test_format_metrics_for_llm(self, alert_config, test_metrics_data):
        """测试LLM指标格式化"""
        service = ResourceAlertService(config=alert_config)
        
        formatted = service._format_metrics_for_llm("deployment/default/test-app", test_metrics_data)
        
        assert "deployment/default/test-app" in formatted
        assert "75.0%" in formatted  # 内存利用率
        assert "60.0%" in formatted  # CPU利用率
        assert "2.50GB" in formatted  # 内存请求量
        assert "1.000核" in formatted  # CPU请求量
    
    def test_generate_fallback_analysis(self, alert_config, test_metrics_data):
        """测试降级分析生成"""
        service = ResourceAlertService(config=alert_config)
        
        analysis = service._generate_fallback_analysis("deployment/default/test-app", test_metrics_data)
        
        assert "内存利用率告警" in analysis
        assert "75.0%" in analysis
        assert "建议" in analysis
        assert "紧急程度" in analysis
    
    def test_build_alert_message(self, alert_config, test_metrics_data):
        """测试告警消息构建"""
        service = ResourceAlertService(config=alert_config)
        
        analysis_result = {
            "success": True,
            "analysis": "测试分析结果",
            "fallback": False
        }
        
        message = service._build_alert_message(
            "deployment/default/test-app", 
            test_metrics_data, 
            analysis_result
        )
        
        assert "🚨 K8s资源利用率告警" in message
        assert "deployment/default/test-app" in message
        assert "75.0%" in message  # 内存利用率
        assert "测试分析结果" in message
        assert "处理建议" in message
    
    @pytest.mark.asyncio
    async def test_generate_llm_analysis_success(self, alert_config, mock_llm_processor, test_metrics_data):
        """测试LLM分析成功场景"""
        service = ResourceAlertService(
            llm_processor=mock_llm_processor,
            config=alert_config
        )
        
        result = await service._generate_llm_analysis("deployment/default/test-app", test_metrics_data)
        
        assert result["success"] is True
        assert result["fallback"] is False
        assert "测试的LLM分析结果" in result["analysis"]
        assert service.stats["llm_analysis_success"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_llm_analysis_disabled(self, test_metrics_data):
        """测试LLM分析禁用场景"""
        config = ResourceAlertConfig(enable_llm_analysis=False)
        service = ResourceAlertService(config=config)
        
        result = await service._generate_llm_analysis("deployment/default/test-app", test_metrics_data)
        
        assert result["success"] is False
        assert result["fallback"] is True
        assert "LLM分析未启用" in result["analysis"]
    
    @pytest.mark.asyncio
    async def test_generate_llm_analysis_failure(self, alert_config, test_metrics_data):
        """测试LLM分析失败场景"""
        # 创建会抛出异常的mock LLM处理器
        mock_processor = Mock()
        mock_processor._chat_without_tools = AsyncMock(side_effect=Exception("LLM调用失败"))
        
        service = ResourceAlertService(
            llm_processor=mock_processor,
            config=alert_config
        )
        
        result = await service._generate_llm_analysis("deployment/default/test-app", test_metrics_data)
        
        assert result["success"] is False
        assert result["fallback"] is True
        assert "内存利用率告警" in result["analysis"]  # 降级分析
        assert service.stats["llm_analysis_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_send_dingtalk_alert_success(self, alert_config, mock_dingtalk_bot, test_metrics_data):
        """测试钉钉告警发送成功"""
        service = ResourceAlertService(
            dingtalk_bot=mock_dingtalk_bot,
            config=alert_config
        )
        
        analysis_result = {"success": True, "analysis": "测试分析"}
        
        result = await service._send_dingtalk_alert(
            "deployment/default/test-app", 
            test_metrics_data, 
            analysis_result
        )
        
        assert result["success"] is True
        assert "message_length" in result
        assert service.stats["dingtalk_sent_success"] == 1
        
        # 验证钉钉Bot被正确调用
        mock_dingtalk_bot.send_markdown_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_dingtalk_alert_disabled(self, test_metrics_data):
        """测试钉钉告警禁用场景"""
        config = ResourceAlertConfig(enable_dingtalk_alert=False)
        service = ResourceAlertService(config=config)
        
        analysis_result = {"success": True, "analysis": "测试分析"}
        
        result = await service._send_dingtalk_alert(
            "deployment/default/test-app", 
            test_metrics_data, 
            analysis_result
        )
        
        assert result["success"] is False
        assert "钉钉告警未启用" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_check_and_alert_full_flow(self, alert_config, mock_llm_processor, 
                                           mock_dingtalk_bot, test_metrics_data):
        """测试完整的告警流程"""
        service = ResourceAlertService(
            llm_processor=mock_llm_processor,
            dingtalk_bot=mock_dingtalk_bot,
            config=alert_config
        )
        
        result = await service.check_and_alert("deployment/default/test-app", test_metrics_data)
        
        assert result["alert_triggered"] is True
        assert result["resource_id"] == "deployment/default/test-app"
        assert result["llm_analysis"]["success"] is True
        assert result["dingtalk_sent"]["success"] is True
        
        # 验证统计信息
        assert service.stats["alerts_processed"] == 1
        assert service.stats["llm_analysis_success"] == 1
        assert service.stats["dingtalk_sent_success"] == 1
        
        # 验证告警历史记录
        assert "deployment/default/test-app" in service.alert_history
        assert len(service.alert_history["deployment/default/test-app"]) == 1
    
    @pytest.mark.asyncio
    async def test_check_and_alert_no_threshold(self, alert_config, mock_llm_processor, 
                                              mock_dingtalk_bot):
        """测试未达到阈值的场景"""
        service = ResourceAlertService(
            llm_processor=mock_llm_processor,
            dingtalk_bot=mock_dingtalk_bot,
            config=alert_config
        )
        
        # 正常利用率数据
        normal_metrics = {
            "memory_utilization_avg_14d": 60.0,  # 60% < 70%
            "cpu_utilization_avg_14d": 60.0,     # 60% < 80%
            "memory_requests": 2.0,
            "cpu_requests": 1.0
        }
        
        result = await service.check_and_alert("deployment/default/test-app", normal_metrics)
        
        assert result["alert_triggered"] is False
        assert "未达到告警阈值" in result["reason"]
        
        # 验证没有调用LLM和钉钉
        mock_llm_processor._chat_without_tools.assert_not_called()
        mock_dingtalk_bot.send_markdown_message.assert_not_called()
    
    def test_get_statistics(self, alert_config):
        """测试统计信息获取"""
        service = ResourceAlertService(config=alert_config)
        
        stats = service.get_statistics()
        
        assert "stats" in stats
        assert "config" in stats
        assert "alert_history_count" in stats
        assert stats["config"]["memory_alert_threshold"] == 0.7
        assert stats["config"]["cpu_alert_threshold"] == 0.8


if __name__ == "__main__":
    # 运行简单的测试
    async def run_basic_test():
        print("🧪 开始ResourceAlertService基础测试...")
        
        # 创建测试配置
        config = ResourceAlertConfig(
            memory_alert_threshold=0.7,
            cpu_alert_threshold=0.8,
            enable_llm_analysis=True,
            enable_dingtalk_alert=True,
            dingtalk_webhook_url="http://test-webhook.com"  # 添加测试webhook URL
        )
        
        # 创建模拟的依赖
        mock_llm = Mock()
        mock_result = Mock()
        mock_result.content = "模拟LLM分析：内存利用率过高，建议优化应用。"
        mock_llm._chat_without_tools = AsyncMock(return_value=mock_result)
        
        mock_dingtalk = Mock()
        mock_dingtalk.send_markdown_message = AsyncMock(return_value=True)
        
        # 创建服务
        service = ResourceAlertService(
            llm_processor=mock_llm,
            dingtalk_bot=mock_dingtalk,
            config=config
        )
        
        # 测试数据
        test_data = {
            "app_name": "test-app",
            "namespace": "default",
            "memory_utilization_avg_14d": 75.0,  # 超过70%阈值
            "cpu_utilization_avg_14d": 60.0,
            "memory_requests": 2.0,
            "cpu_requests": 1.0,
            "last_updated": datetime.now().isoformat()
        }
        
        # 执行告警检查
        result = await service.check_and_alert("deployment/default/test-app", test_data)
        
        # 验证结果
        assert result["alert_triggered"] is True
        assert result["llm_analysis"]["success"] is True
        assert result["dingtalk_sent"]["success"] is True
        
        print("✅ 告警触发成功")
        print("✅ LLM分析调用成功")
        print("✅ 钉钉消息发送成功")
        
        # 测试统计信息
        stats = service.get_statistics()
        print(f"✅ 处理告警数量: {stats['stats']['alerts_processed']}")
        print(f"✅ LLM分析成功: {stats['stats']['llm_analysis_success']}")
        print(f"✅ 钉钉发送成功: {stats['stats']['dingtalk_sent_success']}")
        
        # 测试阈值判断
        normal_data = {
            "memory_utilization_avg_14d": 60.0,  # 低于70%阈值
            "cpu_utilization_avg_14d": 60.0
        }
        
        result2 = await service.check_and_alert("deployment/default/normal-app", normal_data)
        assert result2["alert_triggered"] is False
        print("✅ 正常利用率不触发告警")
        
        print("🎉 ResourceAlertService基础测试全部通过！")
    
    asyncio.run(run_basic_test())
