#!/usr/bin/env python3
"""
测试配置系统集成功能

验证K8sConfig中的新增资源告警配置项，包括：
1. 环境变量加载
2. 配置验证
3. 配置工厂函数
4. 与现有组件的集成
"""

import os
import tempfile
from pathlib import Path
import pytest

# 导入测试目标
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from k8s_mcp.config import (
    K8sConfig, 
    create_resource_alert_config_from_k8s_config,
    create_metrics_config_from_k8s_config
)


def test_k8s_config_default_values():
    """测试K8s配置的默认值"""
    print("\n" + "="*60)
    print("🧪 测试K8s配置的默认值")
    print("="*60)
    
    config = K8sConfig()
    
    # 验证资源告警默认配置
    assert config.resource_alert_enabled == True
    assert config.memory_alert_threshold == 0.7
    assert config.cpu_alert_threshold == 0.8
    assert config.alert_cooldown_seconds == 300
    
    # 验证LLM分析默认配置
    assert config.enable_llm_analysis == True
    assert config.llm_analysis_timeout == 30
    
    # 验证钉钉告警默认配置
    assert config.enable_dingtalk_alert == True
    assert config.dingtalk_webhook_url is None
    assert config.dingtalk_secret is None
    assert config.dingtalk_retry_attempts == 3
    assert config.dingtalk_retry_delay == 2.0
    assert config.alert_message_max_length == 3500
    
    print("✅ 默认值测试通过")


def test_k8s_config_from_env():
    """测试从环境变量加载配置"""
    print("\n" + "="*60)
    print("🧪 测试从环境变量加载配置")
    print("="*60)
    
    # 创建临时kubeconfig文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("apiVersion: v1\nkind: Config\n")
        temp_kubeconfig = f.name
    
    try:
        # 设置环境变量
        env_vars = {
            "KUBECONFIG_PATH": temp_kubeconfig,
            "K8S_NAMESPACE": "test-namespace",
            "RESOURCE_ALERT_ENABLED": "false",
            "MEMORY_ALERT_THRESHOLD": "0.8",
            "CPU_ALERT_THRESHOLD": "0.9",
            "ALERT_COOLDOWN_SECONDS": "600",
            "ENABLE_LLM_ANALYSIS": "false",
            "LLM_ANALYSIS_TIMEOUT": "60",
            "ENABLE_DINGTALK_ALERT": "false",
            "DINGTALK_WEBHOOK_URL": "https://oapi.dingtalk.com/robot/send?access_token=test",
            "DINGTALK_SECRET": "test-secret",
            "DINGTALK_RETRY_ATTEMPTS": "5",
            "DINGTALK_RETRY_DELAY": "3.0",
            "ALERT_MESSAGE_MAX_LENGTH": "4000"
        }
        
        # 备份原始环境变量
        original_env = {}
        for key in env_vars:
            original_env[key] = os.environ.get(key)
        
        # 设置测试环境变量
        for key, value in env_vars.items():
            os.environ[key] = value
        
        # 从环境变量加载配置
        config = K8sConfig.from_env()
        
        # 验证加载的配置
        assert config.kubeconfig_path == temp_kubeconfig
        assert config.namespace == "test-namespace"
        assert config.resource_alert_enabled == False
        assert config.memory_alert_threshold == 0.8
        assert config.cpu_alert_threshold == 0.9
        assert config.alert_cooldown_seconds == 600
        assert config.enable_llm_analysis == False
        assert config.llm_analysis_timeout == 60
        assert config.enable_dingtalk_alert == False
        assert config.dingtalk_webhook_url == "https://oapi.dingtalk.com/robot/send?access_token=test"
        assert config.dingtalk_secret == "test-secret"
        assert config.dingtalk_retry_attempts == 5
        assert config.dingtalk_retry_delay == 3.0
        assert config.alert_message_max_length == 4000
        
        print(f"📋 Kubeconfig路径: {config.kubeconfig_path}")
        print(f"📋 命名空间: {config.namespace}")
        print(f"📋 资源告警启用: {config.resource_alert_enabled}")
        print(f"📋 内存阈值: {config.memory_alert_threshold}")
        print(f"📋 CPU阈值: {config.cpu_alert_threshold}")
        print(f"📋 钉钉Webhook: {config.dingtalk_webhook_url[:50]}...")
        
        print("✅ 环境变量加载测试通过")
        
    finally:
        # 恢复原始环境变量
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # 删除临时文件
        Path(temp_kubeconfig).unlink(missing_ok=True)


def test_config_validation():
    """测试配置验证功能"""
    print("\n" + "="*60)
    print("🧪 测试配置验证功能")
    print("="*60)
    
    # 创建临时kubeconfig文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("apiVersion: v1\nkind: Config\n")
        temp_kubeconfig = f.name
    
    try:
        # 测试有效配置
        valid_config = K8sConfig(
            kubeconfig_path=temp_kubeconfig,
            namespace="test",
            memory_alert_threshold=0.7,
            cpu_alert_threshold=0.8,
            alert_cooldown_seconds=300,
            dingtalk_webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
        )
        
        assert valid_config.validate_config() == True
        print("✅ 有效配置验证通过")
        
        # 测试无效阈值
        invalid_config = K8sConfig(
            kubeconfig_path=temp_kubeconfig,
            namespace="test",
            memory_alert_threshold=1.5,  # 无效：超过1.0
            cpu_alert_threshold=-0.1     # 无效：小于0.0
        )
        
        assert invalid_config.validate_config() == False
        print("✅ 无效配置验证通过")
        
    finally:
        Path(temp_kubeconfig).unlink(missing_ok=True)


def test_resource_alert_config_factory():
    """测试ResourceAlertConfig工厂函数"""
    print("\n" + "="*60)
    print("🧪 测试ResourceAlertConfig工厂函数")
    print("="*60)
    
    k8s_config = K8sConfig(
        memory_alert_threshold=0.75,
        cpu_alert_threshold=0.85,
        alert_cooldown_seconds=600,
        enable_llm_analysis=False,
        enable_dingtalk_alert=True,
        dingtalk_webhook_url="https://test.webhook.com",
        dingtalk_secret="test-secret",
        dingtalk_retry_attempts=5,
        dingtalk_retry_delay=3.0,
        alert_message_max_length=4000
    )
    
    # 创建ResourceAlertConfig
    alert_config = create_resource_alert_config_from_k8s_config(k8s_config)
    
    # 验证转换正确
    assert alert_config.memory_alert_threshold == 0.75
    assert alert_config.cpu_alert_threshold == 0.85
    assert alert_config.alert_cooldown_seconds == 600
    assert alert_config.enable_llm_analysis == False
    assert alert_config.enable_dingtalk_alert == True
    assert alert_config.dingtalk_webhook_url == "https://test.webhook.com"
    assert alert_config.dingtalk_secret == "test-secret"
    assert alert_config.dingtalk_retry_attempts == 5
    assert alert_config.dingtalk_retry_delay == 3.0
    assert alert_config.alert_message_max_length == 4000
    
    print(f"📋 转换后的告警配置:")
    print(f"   内存阈值: {alert_config.memory_alert_threshold}")
    print(f"   CPU阈值: {alert_config.cpu_alert_threshold}")
    print(f"   冷却时间: {alert_config.alert_cooldown_seconds}秒")
    print(f"   LLM分析: {alert_config.enable_llm_analysis}")
    print(f"   钉钉告警: {alert_config.enable_dingtalk_alert}")
    
    print("✅ ResourceAlertConfig工厂函数测试通过")


def test_metrics_config_factory():
    """测试MetricsConfig工厂函数"""
    print("\n" + "="*60)
    print("🧪 测试MetricsConfig工厂函数")
    print("="*60)
    
    k8s_config = K8sConfig(
        resource_alert_enabled=False,
        memory_alert_threshold=0.6,
        cpu_alert_threshold=0.7,
        alert_cooldown_seconds=900
    )
    
    # 创建MetricsConfig
    metrics_config = create_metrics_config_from_k8s_config(
        k8s_config, 
        prometheus_url="http://prometheus:9090"
    )
    
    # 验证转换正确
    assert metrics_config.enable_resource_alerts == False
    assert metrics_config.memory_alert_threshold == 0.6
    assert metrics_config.cpu_alert_threshold == 0.7
    assert metrics_config.alert_cooldown_seconds == 900
    
    print(f"📋 转换后的指标配置:")
    print(f"   告警启用: {metrics_config.enable_resource_alerts}")
    print(f"   内存阈值: {metrics_config.memory_alert_threshold}")
    print(f"   CPU阈值: {metrics_config.cpu_alert_threshold}")
    print(f"   冷却时间: {metrics_config.alert_cooldown_seconds}秒")
    
    print("✅ MetricsConfig工厂函数测试通过")


def test_config_edge_cases():
    """测试配置边界情况"""
    print("\n" + "="*60)
    print("🧪 测试配置边界情况")
    print("="*60)
    
    # 测试极端值
    edge_config = K8sConfig(
        memory_alert_threshold=0.0,  # 最小值
        cpu_alert_threshold=1.0,     # 最大值
        alert_cooldown_seconds=1,    # 极小冷却时间
        dingtalk_retry_attempts=1,   # 最少重试次数
        dingtalk_retry_delay=0.5,    # 极短延迟
        alert_message_max_length=100 # 极短消息长度
    )
    
    print(f"📊 极端配置值:")
    print(f"   内存阈值: {edge_config.memory_alert_threshold}")
    print(f"   CPU阈值: {edge_config.cpu_alert_threshold}")
    print(f"   冷却时间: {edge_config.alert_cooldown_seconds}秒")
    print(f"   重试次数: {edge_config.dingtalk_retry_attempts}")
    print(f"   重试延迟: {edge_config.dingtalk_retry_delay}秒")
    print(f"   消息长度: {edge_config.alert_message_max_length}")
    
    # 测试None值处理
    none_config = K8sConfig(
        dingtalk_webhook_url=None,
        dingtalk_secret=None
    )
    
    assert none_config.dingtalk_webhook_url is None
    assert none_config.dingtalk_secret is None
    
    print("✅ 边界情况测试通过")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始配置系统集成测试")
    print("=" * 80)
    
    tests = [
        ("默认值", test_k8s_config_default_values),
        ("环境变量加载", test_k8s_config_from_env),
        ("配置验证", test_config_validation),
        ("ResourceAlertConfig工厂", test_resource_alert_config_factory),
        ("MetricsConfig工厂", test_metrics_config_factory),
        ("边界情况", test_config_edge_cases)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
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
        print("🎉 所有测试都通过了！配置系统集成功能正常工作。")
        return True
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查相关功能。")
        return False


if __name__ == "__main__":
    # 运行测试
    success = run_all_tests()
    exit(0 if success else 1)
