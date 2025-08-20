#!/usr/bin/env python3
"""演示LLM驱动的Deployment工作流"""

import asyncio
import sys
from pathlib import Path

# 添加源码路径
sys.path.insert(0, str(Path('src')))

from k8s_mcp.tools.k8s_llm_generate_deployment import K8sLLMGenerateDeploymentTool
from k8s_mcp.tools.k8s_create_deployment import K8sCreateDeploymentTool

async def demo_llm_workflow():
    """演示完整的LLM驱动工作流"""
    print("=" * 80)
    print("🤖 LLM驱动的Kubernetes Deployment工作流演示")
    print("=" * 80)
    
    # 第一步：LLM理解自然语言需求并生成YAML
    print("\n📝 第一步：LLM智能生成YAML")
    print("-" * 50)
    
    llm_tool = K8sLLMGenerateDeploymentTool()
    
    # 模拟用户的自然语言需求
    user_requirements = [
        "创建一个高可用的Redis集群，需要3个副本，配置密码，生产环境用",
        "部署一个nginx web服务器，开发环境，需要挂载配置文件，暴露80端口",
        "我需要一个PostgreSQL数据库，单实例，持久化存储，限制资源使用"
    ]
    
    generated_yamls = []
    
    for i, requirement in enumerate(user_requirements, 1):
        print(f"\n🎯 需求 {i}: {requirement}")
        
        # 构建LLM参数
        llm_args = {
            "requirements": requirement,
            "template_style": "production" if "生产" in requirement else "development",
            "context": "高性能集群环境" if "高可用" in requirement else "标准开发环境",
            "constraints": {
                "max_replicas": 5,
                "required_labels": {
                    "team": "devops",
                    "managed-by": "llm-mcp"
                }
            }
        }
        
        result = await llm_tool.execute(llm_args)
        
        if result.content and len(result.content) > 0 and "text" in result.content[0] and not getattr(result, 'is_error', False):
            print("✅ LLM生成成功")
            generated_yamls.append(result.content[0]["text"])
            # 只显示摘要，不显示完整YAML
            lines = result.content[0]["text"].split('\n')
            summary_lines = [line for line in lines[:10] if not line.startswith('```')]
            print("📄 生成摘要:", " | ".join(summary_lines[:3]))
        else:
            print("❌ LLM生成失败")
    
    # 第二步：使用生成的YAML创建Deployment（演练模式）
    print(f"\n🛠️ 第二步：应用生成的配置（演练模式）")
    print("-" * 50)
    
    create_tool = K8sCreateDeploymentTool()
    
    # 模拟提取第一个生成的YAML
    if generated_yamls:
        # 从第一个结果中提取YAML
        first_result = generated_yamls[0]
        yaml_start = first_result.find("```yaml\n") + 8
        yaml_end = first_result.find("\n```", yaml_start)
        
        if yaml_start > 7 and yaml_end > yaml_start:
            extracted_yaml = first_result[yaml_start:yaml_end]
            
            create_args = {
                "yaml_config": extracted_yaml,
                "dry_run": True  # 演练模式
            }
            
            result = await create_tool.execute(create_args)
            
            if result.content and len(result.content) > 0 and "text" in result.content[0] and not getattr(result, 'is_error', False):
                print("✅ 配置验证通过")
                # 显示验证结果摘要
                content = result.content[0]["text"]
                if "配置验证通过" in content:
                    print("🔍 演练结果: 配置格式正确，可以安全部署")
                    # 提取关键信息
                    lines = content.split('\n')
                    for line in lines:
                        if "Deployment名称" in line or "命名空间" in line or "操作" in line:
                            print(f"   {line.strip()}")
            else:
                print("❌ 配置验证失败")
    
    print(f"\n" + "=" * 80)
    print("🎉 工作流演示完成！")
    
    print("\n💡 LLM驱动工作流的优势:")
    print("   ✨ 自然语言交互 - 无需记忆复杂的YAML语法")
    print("   🧠 智能推理 - LLM自动补充最佳实践配置") 
    print("   🔒 安全保障 - 自动添加安全配置和约束检查")
    print("   🎯 上下文理解 - 根据环境类型生成合适配置")
    print("   ⚡ 高效部署 - 一键从需求到部署")
    
    print("\n🔄 完整工作流:")
    print("   1. 用户用自然语言描述需求")
    print("   2. LLM理解并生成标准YAML配置")
    print("   3. 系统验证和增强生成的配置")
    print("   4. MCP工具安全地应用到K8s集群")
    
    print("\n🚀 实际部署:")
    print("   • 移除演练模式 (dry_run: false)")
    print("   • 配置真实的K8s集群连接")
    print("   • 使用生产级别的约束和安全策略")
    print("=" * 80)

async def main():
    """主函数"""
    try:
        await demo_llm_workflow()
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 