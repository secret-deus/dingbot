"""Ollama LLM适配器 - 支持结构化输出和伪工具调用"""

import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger


class OllamaAdapter:
    """Ollama LLM适配器，通过Prompt Engineering实现工具调用效果"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_yaml(self, requirements: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成Kubernetes YAML配置"""
        try:
            prompt = self._build_yaml_prompt(requirements, context or {})

            # 调用Ollama API
            response = await self._call_ollama(prompt, response_format="json")

            # 解析响应
            result = self._parse_yaml_response(response)

            return {
                "success": True,
                "yaml_content": result.get("yaml", ""),
                "explanation": result.get("explanation", ""),
                "warnings": result.get("warnings", [])
            }

        except Exception as e:
            logger.error(f"Ollama YAML生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "yaml_content": "",
                "explanation": "",
                "warnings": []
            }

    def _build_yaml_prompt(self, requirements: str, context: Dict[str, Any]) -> str:
        """构建优化的Prompt"""

        system_instruction = """你是一个Kubernetes专家。你的任务是根据用户需求生成标准的Deployment YAML配置。

CRITICAL: 你必须严格按照以下JSON格式回复，不要添加任何其他文字：

{
  "yaml": "完整的YAML配置内容（使用\\n表示换行）",
  "explanation": "简要说明生成的配置特点",
  "warnings": ["如果有任何注意事项，在这里列出"]
}"""

        user_prompt = f"""
用户需求: {requirements}

上下文信息:
- 命名空间: {context.get('namespace', 'default')}
- 环境类型: {context.get('environment', 'production')}
- 资源限制: {context.get('constraints', {})}

生成要求:
1. 生成完整的Kubernetes Deployment YAML
2. 包含生产级安全配置
3. 添加健康检查（liveness/readiness probes）
4. 设置合理的资源限制
5. 包含滚动更新策略
6. 确保YAML格式正确

请严格按照JSON格式回复。"""

        return f"{system_instruction}\n\n{user_prompt}"

    async def _call_ollama(self, prompt: str, response_format: str = "json") -> str:
        """调用Ollama API"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": response_format if response_format == "json" else None,
            "options": {
                "temperature": 0.1,  # 较低温度确保一致性
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2048  # 允许较长的输出
            }
        }

        logger.info(f"🤖 调用Ollama模型: {self.model}")

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API调用失败: {response.status_code} - {response.text}")

        result = response.json()
        return result.get("response", "")

    def _parse_yaml_response(self, response: str) -> Dict[str, Any]:
        """解析Ollama的JSON响应"""
        try:
            # 尝试直接解析JSON
            parsed = json.loads(response)
            return parsed

        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            logger.warning("直接JSON解析失败，尝试提取JSON内容")

            # 查找JSON块
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return parsed
                except json.JSONDecodeError:
                    pass

            # 如果仍然失败，返回原始响应作为YAML
            logger.warning("JSON提取失败，将原始响应作为YAML处理")
            return {
                "yaml": response,
                "explanation": "由于响应格式问题，无法提供详细解析",
                "warnings": ["响应格式不是标准JSON，请检查生成的YAML"]
            }

    async def analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """分析用户需求，提取关键信息"""

        prompt = f"""
分析以下Kubernetes部署需求，提取关键信息：

用户需求: {requirements}

请以JSON格式回复，包含以下信息：
{{
  "app_name": "推断的应用名称",
  "image": "推荐的容器镜像",
  "replicas": 推荐的副本数,
  "ports": [推荐的端口配置],
  "environment": "推断的环境类型(development/staging/production)",
  "resources_needed": "资源需求评估",
  "security_level": "安全级别(low/medium/high)",
  "additional_components": ["可能需要的额外组件列表"]
}}
"""

        try:
            response = await self._call_ollama(prompt, "json")
            return json.loads(response)
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            return {}

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class OllamaToolManager:
    """Ollama工具管理器 - 模拟工具调用功能"""

    def __init__(self, ollama_adapter: OllamaAdapter):
        self.adapter = ollama_adapter
        self.available_tools = {
            "generate_deployment_yaml": self._generate_deployment_yaml,
            "analyze_requirements": self._analyze_requirements,
            "suggest_optimizations": self._suggest_optimizations
        }

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定的工具"""
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"未知工具: {tool_name}",
                "available_tools": list(self.available_tools.keys())
            }

        try:
            result = await self.available_tools[tool_name](arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_deployment_yaml(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """生成Deployment YAML"""
        requirements = args.get("requirements", "")
        context = args.get("context", {})

        return await self.adapter.generate_yaml(requirements, context)

    async def _analyze_requirements(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求"""
        requirements = args.get("requirements", "")
        return await self.adapter.analyze_requirements(requirements)

    async def _suggest_optimizations(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """建议优化方案"""
        yaml_content = args.get("yaml_content", "")

        prompt = f"""
分析以下Kubernetes YAML配置，提供优化建议：

YAML配置:
{yaml_content}

请以JSON格式提供优化建议：
{{
  "performance_optimizations": ["性能优化建议"],
  "security_improvements": ["安全性改进"],
  "resource_optimizations": ["资源优化建议"],
  "best_practices": ["最佳实践建议"],
  "potential_issues": ["潜在问题"]
}}
"""

        try:
            response = await self.adapter._call_ollama(prompt, "json")
            return json.loads(response)
        except Exception as e:
            logger.error(f"优化建议生成失败: {e}")
            return {"error": str(e)}


# 使用示例和测试函数
async def demo_ollama_tools():
    """演示Ollama工具调用功能"""
    print("🤖 Ollama LLM工具调用演示")
    print("=" * 50)

    # 初始化适配器
    adapter = OllamaAdapter(model="llama3.1:8b")  # 或其他支持的模型
    tool_manager = OllamaToolManager(adapter)

    try:
        # 测试需求分析
        print("\n📋 1. 需求分析")
        analysis_result = await tool_manager.execute_tool(
            "analyze_requirements",
            {"requirements": "我需要部署一个高性能的nginx web服务器，生产环境，3个副本"}
        )

        if analysis_result["success"]:
            print("✅ 需求分析成功:")
            result = analysis_result["result"]
            print(f"   应用名: {result.get('app_name', 'N/A')}")
            print(f"   推荐镜像: {result.get('image', 'N/A')}")
            print(f"   副本数: {result.get('replicas', 'N/A')}")
            print(f"   环境类型: {result.get('environment', 'N/A')}")
        else:
            print(f"❌ 需求分析失败: {analysis_result.get('error')}")

        # 测试YAML生成
        print("\n🚀 2. YAML生成")
        yaml_result = await tool_manager.execute_tool(
            "generate_deployment_yaml",
            {
                "requirements": "创建一个Redis缓存服务，单实例，开发环境",
                "context": {
                    "namespace": "dev",
                    "environment": "development"
                }
            }
        )

        if yaml_result["success"]:
            result = yaml_result["result"]
            if result["success"]:
                print("✅ YAML生成成功")
                print(f"   说明: {result.get('explanation', '')}")
                if result.get('warnings'):
                    print(f"   警告: {result['warnings']}")
                # 显示YAML前几行
                yaml_lines = result.get('yaml_content', '').split('\\n')[:5]
                print(f"   YAML预览: {' | '.join(yaml_lines)}")
            else:
                print(f"❌ YAML生成失败: {result.get('error')}")
        else:
            print(f"❌ 工具调用失败: {yaml_result.get('error')}")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
    finally:
        await adapter.close()

if __name__ == "__main__":
    asyncio.run(demo_ollama_tools())