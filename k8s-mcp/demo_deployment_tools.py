#!/usr/bin/env python3
"""演示新Deployment工具的功能"""

import asyncio
import sys
from pathlib import Path

# 添加源码路径
sys.path.insert(0, str(Path('src')))

from k8s_mcp.tools.k8s_generate_deployment_yaml import K8sGenerateDeploymentYamlTool
from k8s_mcp.tools.k8s_create_deployment import K8sCreateDeploymentTool

async def demo_generate_yaml():
    """演示生成Deployment YAML功能"""
    print("🚀 演示: 生成Deployment YAML")
    print("-" * 40)
    
    tool = K8sGenerateDeploymentYamlTool()
    
    # 示例参数
    arguments = {
        "app_name": "my-nginx-app",
        "image": "nginx:1.21",
        "replicas": 3,
        "ports": [{"containerPort": 80, "name": "http"}],
        "env_vars": [
            {"name": "ENV", "value": "production"},
            {"name": "LOG_LEVEL", "value": "info"}
        ],
        "resources": {
            "limits": {"cpu": "500m", "memory": "512Mi"},
            "requests": {"cpu": "250m", "memory": "256Mi"}
        }
    }
    
    result = await tool.execute(arguments)
    
    if result.content and len(result.content) > 0 and "text" in result.content[0]:
        print(result.content[0]["text"])
    else:
        print("❌ 生成YAML失败")
    
    print("\n" + "=" * 80)

async def demo_create_deployment():
    """演示创建Deployment功能（演练模式）"""
    print("📦 演示: 创建Deployment (演练模式)")
    print("-" * 40)
    
    tool = K8sCreateDeploymentTool()
    
    # 示例参数
    arguments = {
        "app_name": "demo-web-app",
        "image": "nginx:alpine",
        "replicas": 2,
        "ports": [{"containerPort": 80, "name": "web"}],
        "dry_run": True,  # 演练模式，不实际创建
        "env_vars": [
            {"name": "MODE", "value": "demo"}
        ]
    }
    
    result = await tool.execute(arguments)
    
    if result.content and len(result.content) > 0 and "text" in result.content[0]:
        print(result.content[0]["text"])
    else:
        print("❌ 创建Deployment失败")

async def main():
    """主演示函数"""
    print("=" * 60)
    print("🎯 K8s Deployment工具演示")
    print("=" * 60)
    
    try:
        # 演示生成YAML
        await demo_generate_yaml()
        
        # 演示创建Deployment（演练模式）
        await demo_create_deployment()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("💡 提示:")
        print("   • k8s-generate-deployment-yaml: 智能生成YAML配置")
        print("   • k8s-create-deployment: 创建/更新Deployment")
        print("   • 支持完整的K8s Deployment配置选项")
        print("   • 包含安全检查和演练模式")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 