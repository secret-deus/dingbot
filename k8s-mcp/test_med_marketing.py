#!/usr/bin/env python3
"""
测试Prometheus工具 - med-marketing应用
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from k8s_mcp.tools.k8s_prometheus_app_metrics import K8sPrometheusAppMetricsTool


async def test_med_marketing_app():
    """测试med-marketing应用的资源指标"""
    
    print("🔧 初始化Prometheus应用资源分析工具...")
    tool = K8sPrometheusAppMetricsTool()
    
    print("📋 工具信息:")
    schema = tool.get_schema()
    print(f"  名称: {schema.name}")
    print(f"  描述: {schema.description}")
    
    # 测试med-marketing应用
    print("\n🚀 测试med-marketing应用资源指标...")
    
    test_cases = [
        {
            "name": "默认配置",
            "params": {
                "app_name": "med-marketing"
            }
        },
        {
            "name": "指定命名空间",
            "params": {
                "app_name": "med-marketing",
                "namespace": "default"
            }
        },
        {
            "name": "7天数据",
            "params": {
                "app_name": "med-marketing",
                "namespace": "default",
                "days": 7
            }
        },
        {
            "name": "1天数据（快速测试）",
            "params": {
                "app_name": "med-marketing",
                "namespace": "default", 
                "days": 1
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 测试用例 {i}: {test_case['name']}")
        print(f"   参数: {json.dumps(test_case['params'], ensure_ascii=False)}")
        
        try:
            result = await tool.execute(test_case['params'])
            
            if result.is_error:
                print(f"   ❌ 执行失败: {result.content}")
            else:
                print(f"   ✅ 执行成功!")
                
                # 解析结果
                if result.content and len(result.content) > 0:
                    content_text = result.content[0].get('text', '{}')
                    try:
                        data = json.loads(content_text)
                        
                        # 显示关键指标
                        print(f"   📈 应用: {data.get('app_name')}")
                        print(f"   🏷️  命名空间: {data.get('namespace')}")
                        print(f"   📅 查询天数: {data.get('query_days')}")
                        
                        metrics = data.get('metrics', {})
                        cpu_util = metrics.get('cpu_utilization_avg', 0)
                        memory_util = metrics.get('memory_utilization_avg', 0)
                        cpu_req = metrics.get('cpu_requests_avg', 0)
                        memory_req = metrics.get('memory_requests_avg', 0)
                        
                        print(f"   🔥 CPU平均利用率: {cpu_util:.2%}")
                        print(f"   💾 内存平均利用率: {memory_util:.2%}")
                        print(f"   ⚙️  CPU平均请求: {cpu_req:.3f}核")
                        print(f"   📦 内存平均请求: {memory_req:.2f}GB")
                        
                        summary = data.get('summary', {})
                        print(f"   🎯 Pod总数: {summary.get('total_pods', 0)}")
                        print(f"   📊 CPU数据点: {summary.get('data_points_cpu', 0)}")
                        print(f"   📊 内存数据点: {summary.get('data_points_memory', 0)}")
                        
                        analysis = data.get('analysis', {})
                        print(f"   📋 CPU状态: {analysis.get('cpu_utilization_status', 'unknown')}")
                        print(f"   📋 内存状态: {analysis.get('memory_utilization_status', 'unknown')}")
                        
                        recommendations = analysis.get('recommendations', [])
                        if recommendations:
                            print(f"   💡 优化建议:")
                            for rec in recommendations:
                                print(f"      - {rec}")
                        
                        # 显示Pod详情（如果有）
                        pod_details = data.get('pod_details', [])
                        if pod_details:
                            print(f"   🔍 Pod详情 (前3个):")
                            for pod in pod_details[:3]:
                                pod_name = pod.get('pod_name', 'unknown')
                                pod_cpu = pod.get('cpu_utilization_avg', 0)
                                pod_memory = pod.get('memory_utilization_avg', 0)
                                print(f"      📦 {pod_name}: CPU={pod_cpu:.2%}, 内存={pod_memory:.2%}")
                        
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON解析失败: {e}")
                        print(f"   原始内容: {content_text[:200]}...")
                else:
                    print(f"   ⚠️  无返回内容")
                    
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
    
    print("\n✅ 测试完成!")


async def test_error_cases():
    """测试错误情况"""
    print("\n🧪 测试错误情况...")
    
    tool = K8sPrometheusAppMetricsTool()
    
    error_cases = [
        {
            "name": "缺少app_name",
            "params": {}
        },
        {
            "name": "空app_name", 
            "params": {"app_name": ""}
        },
        {
            "name": "无效天数",
            "params": {"app_name": "test", "days": 0}
        }
    ]
    
    for i, test_case in enumerate(error_cases, 1):
        print(f"\n❌ 错误测试 {i}: {test_case['name']}")
        print(f"   参数: {json.dumps(test_case['params'], ensure_ascii=False)}")
        
        try:
            result = await tool.execute(test_case['params'])
            
            if result.is_error:
                print(f"   ✅ 正确捕获错误: {result.content[0].get('text', 'unknown error') if result.content else 'no content'}")
            else:
                print(f"   ⚠️  应该返回错误但没有")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")


async def main():
    """主函数"""
    print("🎯 测试Prometheus应用资源分析工具 - med-marketing")
    print("=" * 60)
    
    # 检查环境配置
    import os
    prometheus_url = os.getenv("PROMETHEUS_URL")
    if prometheus_url:
        print(f"✅ Prometheus URL: {prometheus_url}")
    else:
        print("⚠️  未配置PROMETHEUS_URL，将测试配置检查功能")
    
    # 测试正常情况
    await test_med_marketing_app()
    
    # 测试错误情况
    await test_error_cases()
    
    print(f"\n🎉 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
