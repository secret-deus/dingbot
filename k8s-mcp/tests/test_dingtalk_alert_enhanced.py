#!/usr/bin/env python3
"""
测试增强的钉钉告警消息发送功能

验证ResourceAlertService中的钉钉消息发送功能，包括：
1. 增强的消息模板构建
2. 重试机制
3. 紧急程度计算
4. 错误处理
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# 导入测试目标
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.core.resource_alert_service import ResourceAlertService, ResourceAlertConfig


class MockDingTalkBot:
    """模拟钉钉Bot，用于测试"""
    
    def __init__(self, should_succeed: bool = True, fail_attempts: int = 0):
        self.should_succeed = should_succeed
        self.fail_attempts = fail_attempts  # 前N次调用失败
        self.call_count = 0
        self.sent_messages = []
    
    async def send_markdown_message(self, webhook_url: str, title: str, markdown_text: str) -> bool:
        """模拟发送Markdown消息"""
        self.call_count += 1
        
        # 记录发送的消息
        self.sent_messages.append({
            "webhook_url": webhook_url,
            "title": title,
            "markdown_text": markdown_text,
            "timestamp": datetime.now().isoformat(),
            "attempt": self.call_count
        })
        
        print(f"📤 模拟钉钉消息发送 (第{self.call_count}次调用)")
        print(f"   标题: {title}")
        print(f"   消息长度: {len(markdown_text)} 字符")
        print(f"   Webhook: {webhook_url}")
        
        # 模拟前N次失败
        if self.call_count <= self.fail_attempts:
            print(f"   ❌ 模拟失败 (第{self.call_count}次尝试)")
            return False
        
        # 根据配置决定成功或失败
        if self.should_succeed:
            print(f"   ✅ 模拟成功")
            return True
        else:
            print(f"   ❌ 模拟失败")
            return False


class MockLLMProcessor:
    """模拟LLM处理器"""
    
    def __init__(self):
        self.call_count = 0
    
    async def _chat_without_tools(self, messages):
        """模拟LLM聊天"""
        self.call_count += 1
        
        # 模拟返回分析结果
        class MockResult:
            def __init__(self, content: str):
                self.content = content
        
        analysis = """**问题诊断**: 应用内存利用率85.5%超过阈值70%，存在资源压力

**可能原因**: 应用负载增加导致内存需求上升；内存配置偏低无法满足实际需求

**影响评估**: 可能影响应用性能和用户体验，存在服务响应缓慢风险

**优化建议**: 调整内存请求量至2.1GB；检查应用内存使用模式；启用HPA自动扩缩容；监控应用日志排查性能问题

**紧急程度**: 🟠 高 (24小时内处理)"""
        
        return MockResult(analysis)


def create_test_metrics_data() -> Dict[str, Any]:
    """创建测试用的指标数据"""
    return {
        'memory_utilization_avg_14d': 85.5,  # 超过70%阈值
        'cpu_utilization_avg_14d': 65.2,     # 未超过80%阈值
        'memory_requests': 1.5,
        'cpu_requests': 0.8,
        'namespace': 'production',
        'app_name': 'user-service'
    }


def create_test_analysis_result() -> Dict[str, Any]:
    """创建测试用的LLM分析结果"""
    return {
        "analysis": """**问题诊断**: 应用内存利用率85.5%超过阈值70%

**可能原因**: 
- 应用负载增加导致内存需求上升
- 内存配置偏低无法满足实际需求

**影响评估**: 可能影响应用性能和用户体验

**优化建议**: 
1. 调整内存请求量至2.1GB
2. 检查应用内存使用模式
3. 启用HPA自动扩缩容
4. 监控应用日志排查性能问题

**紧急程度**: 🟠 高 (24小时内处理)""",
        "fallback": False
    }


async def test_enhanced_message_building():
    """测试增强的消息构建功能"""
    print("\n" + "="*60)
    print("🧪 测试增强的消息构建功能")
    print("="*60)
    
    # 创建配置和服务
    config = ResourceAlertConfig(
        memory_alert_threshold=0.7,
        cpu_alert_threshold=0.8,
        dingtalk_webhook_url="http://test-webhook.com",
        alert_message_max_length=3500
    )
    
    mock_dingtalk_bot = MockDingTalkBot(should_succeed=True)
    mock_llm_processor = MockLLMProcessor()
    
    service = ResourceAlertService(
        llm_processor=mock_llm_processor,
        dingtalk_bot=mock_dingtalk_bot,
        config=config
    )
    
    # 测试数据
    resource_id = "deployment/production/user-service"
    metrics_data = create_test_metrics_data()
    analysis_result = create_test_analysis_result()
    
    # 测试消息构建
    title, content = service._build_enhanced_alert_message(resource_id, metrics_data, analysis_result)
    
    print(f"📋 生成的消息标题: {title}")
    print(f"📏 消息内容长度: {len(content)} 字符")
    print(f"📝 消息内容预览:")
    print("-" * 40)
    print(content[:500] + "..." if len(content) > 500 else content)
    print("-" * 40)
    
    # 验证消息内容包含关键信息
    assert "user-service" in title
    assert "production" in content
    assert "85.5%" in content  # 内存利用率
    assert "65.2%" in content  # CPU利用率
    assert "🟠 高级告警" in content  # 紧急程度
    assert "智能分析" in content  # LLM分析
    assert "快速处理指南" in content  # 处理指南
    
    print("✅ 消息构建测试通过")
    return True


async def test_urgency_level_calculation():
    """测试紧急程度计算"""
    print("\n" + "="*60)
    print("🧪 测试紧急程度计算")
    print("="*60)
    
    config = ResourceAlertConfig()
    service = ResourceAlertService(config=config)
    
    # 测试不同利用率的紧急程度
    test_cases = [
        (0.96, "🔴 紧急告警", "🚨"),
        (0.88, "🟠 高级告警", "⚠️"),
        (0.78, "🟡 中级告警", "⚡"),
        (0.72, "🟢 低级告警", "📊")
    ]
    
    for utilization, expected_level, expected_emoji in test_cases:
        urgency = service._calculate_urgency_level(utilization)
        print(f"📊 利用率 {utilization:.0%}: {urgency['level']} {urgency['emoji']}")
        
        assert urgency['level'] == expected_level
        assert urgency['emoji'] == expected_emoji
        assert 'priority' in urgency
        assert 'timeline' in urgency
        assert 'description' in urgency
    
    print("✅ 紧急程度计算测试通过")
    return True


async def test_retry_mechanism():
    """测试重试机制"""
    print("\n" + "="*60)
    print("🧪 测试钉钉消息发送重试机制")
    print("="*60)
    
    # 配置：前2次失败，第3次成功
    config = ResourceAlertConfig(
        memory_alert_threshold=0.7,
        dingtalk_webhook_url="http://test-webhook.com",
        dingtalk_retry_attempts=3,
        dingtalk_retry_delay=0.1  # 快速重试用于测试
    )
    
    mock_dingtalk_bot = MockDingTalkBot(should_succeed=True, fail_attempts=2)
    service = ResourceAlertService(dingtalk_bot=mock_dingtalk_bot, config=config)
    
    # 测试数据
    resource_id = "deployment/production/test-app"
    metrics_data = create_test_metrics_data()
    analysis_result = create_test_analysis_result()
    
    # 发送告警
    start_time = datetime.now()
    result = await service._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
    end_time = datetime.now()
    
    print(f"⏱️  总耗时: {(end_time - start_time).total_seconds():.2f}秒")
    print(f"📞 总调用次数: {mock_dingtalk_bot.call_count}")
    print(f"📊 发送结果: {result}")
    
    # 验证结果
    assert result["success"] == True
    assert result["attempts"] == 3  # 第3次成功
    assert mock_dingtalk_bot.call_count == 3
    assert service.stats["dingtalk_retry_success"] == 1
    
    print("✅ 重试机制测试通过")
    return True


async def test_failure_handling():
    """测试失败处理"""
    print("\n" + "="*60)
    print("🧪 测试钉钉消息发送失败处理")
    print("="*60)
    
    # 配置：所有尝试都失败
    config = ResourceAlertConfig(
        memory_alert_threshold=0.7,
        dingtalk_webhook_url="http://test-webhook.com",
        dingtalk_retry_attempts=3,
        dingtalk_retry_delay=0.1
    )
    
    mock_dingtalk_bot = MockDingTalkBot(should_succeed=False)
    service = ResourceAlertService(dingtalk_bot=mock_dingtalk_bot, config=config)
    
    # 测试数据
    resource_id = "deployment/production/failing-app"
    metrics_data = create_test_metrics_data()
    analysis_result = create_test_analysis_result()
    
    # 发送告警
    result = await service._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
    
    print(f"📞 总调用次数: {mock_dingtalk_bot.call_count}")
    print(f"📊 发送结果: {result}")
    
    # 验证结果
    assert result["success"] == False
    assert result["attempts"] == 3
    assert mock_dingtalk_bot.call_count == 3
    assert service.stats["dingtalk_sent_failed"] == 1
    assert service.stats["dingtalk_retry_failed"] == 1
    
    print("✅ 失败处理测试通过")
    return True


async def test_message_length_control():
    """测试消息长度控制"""
    print("\n" + "="*60)
    print("🧪 测试消息长度控制")
    print("="*60)
    
    # 配置较小的消息长度限制
    config = ResourceAlertConfig(
        alert_message_max_length=500  # 很小的限制
    )
    
    service = ResourceAlertService(config=config)
    
    # 创建包含长分析内容的测试数据
    long_analysis_result = {
        "analysis": "这是一个非常长的分析内容。" * 100,  # 很长的内容
        "fallback": False
    }
    
    resource_id = "deployment/production/long-message-app"
    metrics_data = create_test_metrics_data()
    
    # 构建消息
    title, content = service._build_enhanced_alert_message(resource_id, metrics_data, long_analysis_result)
    
    print(f"📏 原始分析长度: {len(long_analysis_result['analysis'])} 字符")
    print(f"📏 最终消息长度: {len(content)} 字符")
    print(f"📏 配置的最大长度: {config.alert_message_max_length} 字符")
    
    # 验证消息被正确截断
    assert len(content) <= config.alert_message_max_length
    assert "已智能截断" in content or "已截断" in content
    
    print("✅ 消息长度控制测试通过")
    return True


async def test_statistics_tracking():
    """测试统计信息跟踪"""
    print("\n" + "="*60)
    print("🧪 测试统计信息跟踪")
    print("="*60)
    
    config = ResourceAlertConfig(
        dingtalk_webhook_url="http://test-webhook.com",
        dingtalk_retry_attempts=2
    )
    
    # 测试成功发送
    mock_bot_success = MockDingTalkBot(should_succeed=True)
    service = ResourceAlertService(dingtalk_bot=mock_bot_success, config=config)
    
    resource_id = "deployment/test/stats-app"
    metrics_data = create_test_metrics_data()
    analysis_result = create_test_analysis_result()
    
    # 发送成功的告警
    await service._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
    
    # 测试重试后成功
    mock_bot_retry = MockDingTalkBot(should_succeed=True, fail_attempts=1)
    service.dingtalk_bot = mock_bot_retry
    await service._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
    
    # 测试完全失败
    mock_bot_fail = MockDingTalkBot(should_succeed=False)
    service.dingtalk_bot = mock_bot_fail
    await service._send_dingtalk_alert(resource_id, metrics_data, analysis_result)
    
    # 检查统计信息
    stats_info = service.get_statistics()
    stats = stats_info["stats"]  # 获取实际的统计数据
    print(f"📊 统计信息: {json.dumps(stats_info, indent=2, ensure_ascii=False)}")
    
    assert stats["dingtalk_sent_success"] == 1  # 第一次直接成功
    assert stats["dingtalk_retry_success"] == 1  # 第二次重试成功
    assert stats["dingtalk_sent_failed"] == 1   # 第三次完全失败
    assert stats["dingtalk_retry_failed"] == 1  # 第三次重试失败
    
    print("✅ 统计信息跟踪测试通过")
    return True


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始钉钉告警消息发送功能测试")
    print("=" * 80)
    
    tests = [
        ("消息构建", test_enhanced_message_building),
        ("紧急程度计算", test_urgency_level_calculation),
        ("重试机制", test_retry_mechanism),
        ("失败处理", test_failure_handling),
        ("消息长度控制", test_message_length_control),
        ("统计信息跟踪", test_statistics_tracking)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
            print(f"✅ {test_name} 测试通过")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"🏁 测试完成: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试都通过了！钉钉告警消息发送功能正常工作。")
        return True
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查相关功能。")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
