"""
测试LLM资源分析功能集成
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.core.resource_alert_service import (
    ResourceAlertService, 
    ResourceAlertConfig
)


class TestLLMAnalysisIntegration:
    """测试LLM分析功能集成"""
    
    @pytest.fixture
    def enhanced_config(self):
        """增强的测试配置"""
        return ResourceAlertConfig(
            memory_alert_threshold=0.7,
            cpu_alert_threshold=0.8,
            enable_llm_analysis=True,
            enable_dingtalk_alert=True,
            dingtalk_webhook_url="http://test-webhook.com"
        )
    
    @pytest.fixture
    def mock_llm_with_detailed_response(self):
        """模拟LLM处理器，返回详细的分析结果"""
        processor = Mock()
        
        # 模拟专业的LLM分析响应
        mock_result = Mock()
        mock_result.content = """**问题诊断**: deployment/default/high-memory-app 内存利用率75.0%超过阈值70%

**可能原因**: 
- 应用负载增加导致内存需求上升
- 内存配置相对于实际使用偏低
- 可能存在内存使用效率问题

**影响评估**: 可能影响应用性能和用户体验，需要及时关注和处理

**优化建议**: 
1. 调整内存请求量至3.0GB（当前2.5GB不足）
2. 检查应用内存使用模式，排查潜在内存泄漏
3. 启用HPA自动扩缩容机制
4. 监控应用日志，分析内存使用趋势

**紧急程度**: 🟡 中 (3天内处理)"""
        
        processor._chat_without_tools = AsyncMock(return_value=mock_result)
        return processor
    
    @pytest.fixture
    def test_high_memory_data(self):
        """高内存利用率测试数据"""
        return {
            "app_name": "high-memory-app",
            "namespace": "default",
            "memory_utilization_avg_14d": 75.0,  # 75% > 70%阈值
            "cpu_utilization_avg_14d": 60.0,     # 60% < 80%阈值
            "memory_requests": 2.5,
            "cpu_requests": 1.0,
            "last_updated": datetime.now().isoformat()
        }
    
    @pytest.fixture
    def test_high_cpu_data(self):
        """高CPU利用率测试数据"""
        return {
            "app_name": "high-cpu-app",
            "namespace": "production",
            "memory_utilization_avg_14d": 60.0,  # 60% < 70%阈值
            "cpu_utilization_avg_14d": 85.0,     # 85% > 80%阈值
            "memory_requests": 4.0,
            "cpu_requests": 2.0,
            "last_updated": datetime.now().isoformat()
        }
    
    def test_enhanced_analysis_prompt(self, enhanced_config):
        """测试增强的分析提示词"""
        service = ResourceAlertService(config=enhanced_config)
        
        prompt = service._build_analysis_prompt()
        
        # 验证提示词包含关键要素
        assert "Kubernetes运维专家" in prompt
        assert "根因分析" in prompt
        assert "影响评估" in prompt
        assert "优化建议" in prompt
        assert "紧急程度" in prompt
        assert "Markdown格式" in prompt
        assert "400字以内" in prompt
    
    def test_enhanced_metrics_formatting(self, enhanced_config, test_high_memory_data):
        """测试增强的指标格式化"""
        service = ResourceAlertService(config=enhanced_config)
        
        formatted = service._format_metrics_for_llm(
            "deployment/default/high-memory-app", 
            test_high_memory_data
        )
        
        # 验证格式化结果包含关键信息
        assert "DEPLOYMENT" in formatted
        assert "default" in formatted
        assert "high-memory-app" in formatted
        assert "75.0%" in formatted
        assert "🔴 超阈值" in formatted
        assert "🟢 正常" in formatted  # CPU正常
        assert "利用效率" in formatted
        assert "告警触发原因" in formatted
        assert "14天滚动平均值" in formatted
    
    def test_enhanced_fallback_analysis(self, enhanced_config, test_high_memory_data):
        """测试增强的降级分析"""
        service = ResourceAlertService(config=enhanced_config)
        
        analysis = service._generate_fallback_analysis(
            "deployment/default/high-memory-app", 
            test_high_memory_data
        )
        
        # 验证降级分析包含所有必要部分
        assert "问题诊断" in analysis
        assert "可能原因" in analysis
        assert "影响评估" in analysis
        assert "优化建议" in analysis
        assert "紧急程度" in analysis
        
        # 验证具体内容
        assert "75.0%" in analysis
        assert "超过阈值70%" in analysis
        assert "调整内存请求量至" in analysis
        assert "🟡 中" in analysis  # 中等紧急程度
        assert "3天内处理" in analysis
    
    @pytest.mark.asyncio
    async def test_llm_analysis_with_enhanced_prompt(self, enhanced_config, 
                                                   mock_llm_with_detailed_response, 
                                                   test_high_memory_data):
        """测试使用增强提示词的LLM分析"""
        service = ResourceAlertService(
            llm_processor=mock_llm_with_detailed_response,
            config=enhanced_config
        )
        
        result = await service._generate_llm_analysis(
            "deployment/default/high-memory-app", 
            test_high_memory_data
        )
        
        # 验证LLM分析结果
        assert result["success"] is True
        assert result["fallback"] is False
        assert "问题诊断" in result["analysis"]
        assert "可能原因" in result["analysis"]
        assert "优化建议" in result["analysis"]
        assert "紧急程度" in result["analysis"]
        
        # 验证LLM被正确调用
        mock_llm_with_detailed_response._chat_without_tools.assert_called_once()
        
        # 验证调用参数
        call_args = mock_llm_with_detailed_response._chat_without_tools.call_args[0][0]
        assert len(call_args) == 2  # system + user messages
        assert call_args[0].role == "system"
        assert call_args[1].role == "user"
        assert "deployment/default/high-memory-app" in call_args[1].content
    
    @pytest.mark.asyncio
    async def test_input_size_control(self, enhanced_config):
        """测试输入大小控制"""
        # 创建一个会生成超长输入的mock LLM
        mock_llm = Mock()
        mock_result = Mock()
        mock_result.content = "分析结果"
        mock_llm._chat_without_tools = AsyncMock(return_value=mock_result)
        
        service = ResourceAlertService(
            llm_processor=mock_llm,
            config=enhanced_config
        )
        
        # 创建会导致超长格式化结果的数据
        large_data = {
            "app_name": "test-app" * 100,  # 很长的应用名
            "namespace": "test-namespace" * 100,
            "memory_utilization_avg_14d": 75.0,
            "cpu_utilization_avg_14d": 85.0,
            "memory_requests": 2.0,
            "cpu_requests": 1.0,
            "last_updated": datetime.now().isoformat()
        }
        
        result = await service._generate_llm_analysis("deployment/test/test", large_data)
        
        # 验证即使输入很大也能正常处理
        assert result["success"] is True
        
        # 验证LLM被调用
        mock_llm._chat_without_tools.assert_called_once()
        
        # 验证输入被适当控制（通过检查调用参数）
        call_args = mock_llm._chat_without_tools.call_args[0][0]
        user_message_length = len(call_args[1].content)
        assert user_message_length <= 10000  # 应该在合理范围内
    
    @pytest.mark.asyncio
    async def test_cpu_alert_analysis(self, enhanced_config, mock_llm_with_detailed_response, 
                                    test_high_cpu_data):
        """测试CPU告警的分析"""
        service = ResourceAlertService(
            llm_processor=mock_llm_with_detailed_response,
            config=enhanced_config
        )
        
        # 测试格式化
        formatted = service._format_metrics_for_llm(
            "deployment/production/high-cpu-app", 
            test_high_cpu_data
        )
        
        # 验证CPU告警信息
        assert "85.0%" in formatted
        assert "🔴 超阈值" in formatted  # CPU超阈值
        assert "CPU利用率 85.0% 超过阈值 80%" in formatted
        
        # 测试降级分析
        fallback = service._generate_fallback_analysis(
            "deployment/production/high-cpu-app", 
            test_high_cpu_data
        )
        
        assert "CPU利用率85.0%超过阈值80%" in fallback
        assert "CPU密集型任务" in fallback or "计算负载增加" in fallback
        assert "调整CPU请求量至" in fallback


if __name__ == "__main__":
    # 运行增强的LLM分析测试
    async def run_enhanced_test():
        print("🧪 开始增强LLM分析功能测试...")
        
        # 创建增强配置
        config = ResourceAlertConfig(
            memory_alert_threshold=0.7,
            cpu_alert_threshold=0.8,
            enable_llm_analysis=True,
            enable_dingtalk_alert=True,
            dingtalk_webhook_url="http://test-webhook.com"
        )
        
        # 创建模拟LLM
        mock_llm = Mock()
        mock_result = Mock()
        mock_result.content = """**问题诊断**: deployment/default/test-app 内存利用率75.0%超过阈值70%

**可能原因**: 应用负载增加或内存配置偏低; 可能存在内存使用效率问题

**影响评估**: 可能影响应用性能和用户体验，需要及时关注

**优化建议**: 调整内存请求量至3.0GB; 检查内存使用模式; 启用HPA; 监控应用日志

**紧急程度**: 🟡 中 (3天内处理)"""
        
        mock_llm._chat_without_tools = AsyncMock(return_value=mock_result)
        
        # 创建服务
        service = ResourceAlertService(
            llm_processor=mock_llm,
            config=config
        )
        
        # 测试数据
        test_data = {
            "app_name": "test-app",
            "namespace": "default",
            "memory_utilization_avg_14d": 75.0,
            "cpu_utilization_avg_14d": 60.0,
            "memory_requests": 2.5,
            "cpu_requests": 1.0,
            "last_updated": datetime.now().isoformat()
        }
        
        # 测试增强的分析提示词
        prompt = service._build_analysis_prompt()
        assert "根因分析" in prompt
        assert "影响评估" in prompt
        print("✅ 增强分析提示词验证通过")
        
        # 测试增强的指标格式化
        formatted = service._format_metrics_for_llm("deployment/default/test-app", test_data)
        assert "🔴 超阈值" in formatted
        assert "利用效率" in formatted
        assert "告警触发原因" in formatted
        print("✅ 增强指标格式化验证通过")
        
        # 测试增强的降级分析
        fallback = service._generate_fallback_analysis("deployment/default/test-app", test_data)
        assert "问题诊断" in fallback
        assert "可能原因" in fallback
        assert "优化建议" in fallback
        assert "紧急程度" in fallback
        print("✅ 增强降级分析验证通过")
        
        # 测试LLM分析
        result = await service._generate_llm_analysis("deployment/default/test-app", test_data)
        assert result["success"] is True
        assert "问题诊断" in result["analysis"]
        print("✅ LLM分析调用验证通过")
        
        # 验证输入大小控制
        call_args = mock_llm._chat_without_tools.call_args[0][0]
        user_content_length = len(call_args[1].content)
        assert user_content_length < 10000  # 合理的输入大小
        print(f"✅ 输入大小控制验证通过 ({user_content_length}字符)")
        
        print("🎉 增强LLM分析功能测试全部通过！")
    
    asyncio.run(run_enhanced_test())
