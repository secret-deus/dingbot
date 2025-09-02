#!/usr/bin/env python3
"""
测试K8s资源监控MCP工具

验证K8sResourceMonitorTool的各项功能，包括：
1. 工具注册和Schema验证
2. 应用监控功能
3. 告警测试功能
4. 统计信息查询
5. 应用列表功能
6. 错误处理
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 导入测试目标
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.tools.k8s_resource_monitor import K8sResourceMonitorTool
from k8s_mcp.core.mcp_protocol import MCPCallToolResult


def parse_result_content(result: MCPCallToolResult) -> dict:
    """解析MCPCallToolResult的内容为字典"""
    import json
    if result.is_error:
        return json.loads(result.content[0]["text"])
    else:
        return json.loads(result.content[0]["text"])


class MockResourceAlertService:
    """模拟的ResourceAlertService"""
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            "alerts_processed": 2,
            "llm_analysis_success": 1,
            "llm_analysis_failed": 0,
            "dingtalk_sent_success": 1,
            "dingtalk_sent_failed": 0
        }
    
    async def check_and_alert(self, resource_id, metrics_data):
        """模拟告警检查"""
        # 模拟告警逻辑
        memory_util = metrics_data.get("avg_memory_utilization", 0) / 100.0
        cpu_util = metrics_data.get("avg_cpu_utilization", 0) / 100.0
        
        alert_triggered = (
            memory_util > self.config.memory_alert_threshold or 
            cpu_util > self.config.cpu_alert_threshold
        )
        
        if alert_triggered:
            return {
                "alert_triggered": True,
                "triggered_by": "memory" if memory_util > self.config.memory_alert_threshold else "cpu",
                "utilization": {
                    "memory": memory_util,
                    "cpu": cpu_util
                },
                "thresholds": {
                    "memory": self.config.memory_alert_threshold,
                    "cpu": self.config.cpu_alert_threshold
                },
                "llm_analysis": {
                    "status": "success",
                    "recommendations": ["扩容建议", "优化建议"],
                    "urgency": "high"
                },
                "dingtalk_sent": {
                    "success": True,
                    "message_length": 1500
                }
            }
        else:
            return {
                "alert_triggered": False,
                "utilization": {
                    "memory": memory_util,
                    "cpu": cpu_util
                },
                "thresholds": {
                    "memory": self.config.memory_alert_threshold,
                    "cpu": self.config.cpu_alert_threshold
                },
                "message": "资源利用率正常"
            }
    
    def get_statistics(self):
        """获取统计信息"""
        return {"stats": self.stats}


class MockMetricsAggregator:
    """模拟的MetricsAggregator"""
    
    def __init__(self):
        pass


class MockKnowledgeGraph:
    """模拟的知识图谱"""
    
    async def get_deployment_node(self, namespace, app_name):
        """模拟获取部署节点"""
        if app_name == "test-app":
            return {
                "data": {
                    "name": app_name,
                    "namespace": namespace,
                    "metrics": {
                        "avg_cpu_utilization": 45.5,
                        "avg_memory_utilization": 67.2,
                        "days_analyzed": 14,
                        "total_data_points": 336,
                        "analysis_period": "2025-01-18 to 2025-02-01",
                        "updated_at": "2025-02-01T16:00:00Z"
                    }
                }
            }
        elif app_name == "high-usage-app":
            return {
                "data": {
                    "name": app_name,
                    "namespace": namespace,
                    "metrics": {
                        "avg_cpu_utilization": 85.0,  # 超过阈值
                        "avg_memory_utilization": 75.0,  # 超过阈值
                        "days_analyzed": 14,
                        "total_data_points": 336,
                        "analysis_period": "2025-01-18 to 2025-02-01",
                        "updated_at": "2025-02-01T16:00:00Z"
                    }
                }
            }
        return None
    
    async def get_nodes_by_type(self, node_type):
        """模拟获取节点列表"""
        if node_type == "Deployment":
            return [
                {
                    "data": {
                        "name": "test-app",
                        "namespace": "default",
                        "metrics": {
                            "avg_cpu_utilization": 45.5,
                            "avg_memory_utilization": 67.2,
                            "updated_at": "2025-02-01T16:00:00Z"
                        }
                    }
                },
                {
                    "data": {
                        "name": "high-usage-app",
                        "namespace": "production",
                        "metrics": {
                            "avg_cpu_utilization": 85.0,
                            "avg_memory_utilization": 75.0,
                            "updated_at": "2025-02-01T16:00:00Z"
                        }
                    }
                }
            ]
        return []


def test_tool_initialization():
    """测试工具初始化"""
    print("\n" + "="*60)
    print("🧪 测试工具初始化")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    # 验证基本属性
    assert tool.name == "k8s-resource-monitor"
    assert "资源监控" in tool.description
    assert tool.enabled == True
    
    # 验证统计信息
    stats = tool.stats
    assert "monitors_triggered" in stats
    assert "alerts_triggered" in stats
    assert stats["monitors_triggered"] == 0
    assert stats["alerts_triggered"] == 0
    
    print(f"✅ 工具名称: {tool.name}")
    print(f"✅ 工具描述: {tool.description[:50]}...")
    print(f"✅ 初始统计: {stats}")
    print("✅ 工具初始化测试通过")


def test_tool_schema():
    """测试工具Schema"""
    print("\n" + "="*60)
    print("🧪 测试工具Schema")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    schema = tool.get_schema()
    
    # 验证Schema结构
    assert schema.name == "k8s-resource-monitor"
    assert "input_schema" in schema.__dict__
    
    input_schema = schema.input_schema
    assert input_schema["type"] == "object"
    assert "properties" in input_schema
    assert "required" in input_schema
    
    # 验证必需参数
    assert "action" in input_schema["required"]
    
    # 验证参数定义
    properties = input_schema["properties"]
    assert "action" in properties
    assert "app_name" in properties
    assert "namespace" in properties
    
    # 验证action枚举值
    action_enum = properties["action"]["enum"]
    expected_actions = ["monitor", "test-alert", "get-stats", "list-apps"]
    for action in expected_actions:
        assert action in action_enum
    
    print(f"✅ Schema名称: {schema.name}")
    print(f"✅ 支持的动作: {action_enum}")
    print(f"✅ 必需参数: {input_schema['required']}")
    print("✅ Schema验证测试通过")


async def test_monitor_application():
    """测试应用监控功能"""
    print("\n" + "="*60)
    print("🧪 测试应用监控功能")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    # 模拟服务
    with patch.object(tool, 'knowledge_graph', MockKnowledgeGraph()):
        # 测试正常监控
        arguments = {
            "action": "monitor",
            "app_name": "test-app",
            "namespace": "default"
        }
        
        result = await tool.execute(arguments)
        
        assert result.is_error == False
        content_data = parse_result_content(result)
        
        assert "metrics" in content_data
        assert "resource_id" in content_data
        assert content_data["resource_id"] == "deployment/default/test-app"
        
        metrics = content_data["metrics"]
        assert metrics["avg_cpu_utilization"] == 45.5
        assert metrics["avg_memory_utilization"] == 67.2
        assert metrics["data_source"] == "knowledge_graph"
        
        print(f"✅ 资源ID: {content_data['resource_id']}")
        print(f"✅ CPU利用率: {metrics['avg_cpu_utilization']}%")
        print(f"✅ 内存利用率: {metrics['avg_memory_utilization']}%")
        print(f"✅ 数据源: {metrics['data_source']}")
        
        # 测试缺少参数的情况
        invalid_arguments = {"action": "monitor"}
        result = await tool.execute(invalid_arguments)
        assert result.is_error == True
        error_data = parse_result_content(result)
        assert "缺少必需参数" in error_data.get("error", "")
        
        print("✅ 参数验证正常")
        print("✅ 应用监控功能测试通过")


async def test_alert_functionality():
    """测试告警功能"""
    print("\n" + "="*60)
    print("🧪 测试告警功能")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    # 创建模拟配置
    mock_config = MagicMock()
    mock_config.memory_alert_threshold = 0.7
    mock_config.cpu_alert_threshold = 0.8
    mock_config.alert_cooldown_seconds = 300
    mock_config.enable_llm_analysis = True
    mock_config.enable_dingtalk_alert = True
    
    # 模拟服务
    mock_alert_service = MockResourceAlertService(mock_config)
    
    with patch.object(tool, 'alert_service', mock_alert_service), \
         patch.object(tool, 'knowledge_graph', MockKnowledgeGraph()):
        
        # 测试正常告警检查
        arguments = {
            "action": "monitor",
            "app_name": "high-usage-app",
            "namespace": "production"
        }
        
        result = await tool.execute(arguments)
        
        assert result.is_error == False
        content_data = parse_result_content(result)
        assert "alert" in content_data
        
        alert_info = content_data["alert"]
        assert alert_info["alert_triggered"] == True
        assert "llm_analysis" in alert_info
        assert "dingtalk_sent" in alert_info
        
        print(f"✅ 告警触发: {alert_info['alert_triggered']}")
        print(f"✅ 触发原因: {alert_info['triggered_by']}")
        print(f"✅ LLM分析: {alert_info['llm_analysis']['status']}")
        print(f"✅ 钉钉发送: {alert_info['dingtalk_sent']['success']}")
        
        # 测试强制告警测试
        test_arguments = {
            "action": "test-alert",
            "app_name": "test-app",
            "namespace": "default",
            "force_alert": True
        }
        
        result = await tool.execute(test_arguments)
        
        assert result.is_error == False
        content_data = parse_result_content(result)
        assert "alert_result" in content_data
        assert "test_metrics" in content_data
        
        test_metrics = content_data["test_metrics"]
        assert test_metrics["test_mode"] == True
        assert test_metrics["avg_cpu_utilization"] == 95.0  # 强制高利用率
        
        print(f"✅ 测试模式CPU: {test_metrics['avg_cpu_utilization']}%")
        print(f"✅ 测试模式内存: {test_metrics['avg_memory_utilization']}%")
        print("✅ 告警功能测试通过")


async def test_statistics_query():
    """测试统计信息查询"""
    print("\n" + "="*60)
    print("🧪 测试统计信息查询")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    # 模拟一些操作以产生统计数据
    tool.stats["monitors_triggered"] = 5
    tool.stats["alerts_triggered"] = 2
    tool.stats["successful_monitors"] = 4
    tool.stats["failed_monitors"] = 1
    
    # 模拟告警服务
    mock_config = MagicMock()
    mock_alert_service = MockResourceAlertService(mock_config)
    
    with patch.object(tool, 'alert_service', mock_alert_service):
        arguments = {"action": "get-stats"}
        result = await tool.execute(arguments)
        
        assert result.is_error == False
        content_data = parse_result_content(result)
        assert "tool_stats" in content_data
        assert "config_info" in content_data
        assert "service_status" in content_data
        
        tool_stats = content_data["tool_stats"]
        assert tool_stats["monitors_triggered"] == 5
        assert tool_stats["alerts_triggered"] == 2
        
        service_status = content_data["service_status"]
        assert "alert_service_available" in service_status
        assert "metrics_aggregator_available" in service_status
        assert "knowledge_graph_available" in service_status
        
        print(f"✅ 监控触发次数: {tool_stats['monitors_triggered']}")
        print(f"✅ 告警触发次数: {tool_stats['alerts_triggered']}")
        print(f"✅ 成功监控: {tool_stats['successful_monitors']}")
        print(f"✅ 失败监控: {tool_stats['failed_monitors']}")
        print(f"✅ 服务状态: {service_status}")
        
        # 验证告警服务统计
        if "alert_service_stats" in content_data:
            alert_stats = content_data["alert_service_stats"]
            print(f"✅ 告警服务统计: {alert_stats}")
        
        print("✅ 统计信息查询测试通过")


async def test_list_applications():
    """测试应用列表功能"""
    print("\n" + "="*60)
    print("🧪 测试应用列表功能")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    with patch.object(tool, 'knowledge_graph', MockKnowledgeGraph()):
        arguments = {"action": "list-apps"}
        result = await tool.execute(arguments)
        
        assert result.is_error == False
        content_data = parse_result_content(result)
        assert "applications" in content_data
        assert "total_count" in content_data
        
        applications = content_data["applications"]
        assert len(applications) == 2
        
        # 验证第一个应用
        app1 = applications[0]
        assert app1["name"] == "test-app"
        assert app1["namespace"] == "default"
        assert app1["has_metrics"] == True
        assert "metrics_summary" in app1
        
        # 验证第二个应用
        app2 = applications[1]
        assert app2["name"] == "high-usage-app"
        assert app2["namespace"] == "production"
        assert app2["has_metrics"] == True
        
        print(f"✅ 应用总数: {content_data['total_count']}")
        print(f"✅ 数据源: {content_data['data_source']}")
        
        for i, app in enumerate(applications):
            print(f"✅ 应用{i+1}: {app['name']} (命名空间: {app['namespace']})")
            if app.get("metrics_summary"):
                metrics = app["metrics_summary"]
                print(f"    CPU: {metrics['cpu_utilization']}%, 内存: {metrics['memory_utilization']}%")
        
        print("✅ 应用列表功能测试通过")


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("🧪 测试错误处理")
    print("="*60)
    
    tool = K8sResourceMonitorTool()
    
    # 测试不支持的动作
    arguments = {"action": "invalid-action"}
    result = await tool.execute(arguments)
    assert result.is_error == True
    error_data = parse_result_content(result)
    assert "不支持的动作" in error_data.get("error", "")
    print("✅ 不支持的动作处理正常")
    
    # 测试告警服务为空的情况 - 先禁用告警服务
    tool_without_alerts = K8sResourceMonitorTool()
    tool_without_alerts.alert_service = None
    arguments = {
        "action": "test-alert",
        "app_name": "test-app"
    }
    result = await tool_without_alerts.execute(arguments)
    assert result.is_error == True
    error_data = parse_result_content(result)
    assert "告警服务未初始化" in error_data.get("error", "")
    print("✅ 告警服务检查正常")
    
    # 测试无法获取指标数据的情况
    with patch.object(tool, 'knowledge_graph', None):
        arguments = {
            "action": "monitor",
            "app_name": "nonexistent-app",
            "namespace": "default"
        }
        result = await tool.execute(arguments)
        # 应该使用占位符数据
        assert result.is_error == False
        content_data = parse_result_content(result)
        metrics = content_data["metrics"]
        assert metrics["data_source"] == "placeholder"
        print("✅ 占位符数据处理正常")
    
    print("✅ 错误处理测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始K8s资源监控MCP工具测试")
    print("=" * 80)
    
    tests = [
        ("工具初始化", test_tool_initialization),
        ("工具Schema", test_tool_schema),
        ("应用监控", test_monitor_application),
        ("告警功能", test_alert_functionality),
        ("统计查询", test_statistics_query),
        ("应用列表", test_list_applications),
        ("错误处理", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
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
        print("🎉 所有测试都通过了！K8s资源监控MCP工具功能正常。")
        return True
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查相关功能。")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
