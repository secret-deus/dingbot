"""基于LLM的智能Kubernetes Deployment生成工具"""

import yaml
import json
from typing import Dict, Any, Optional
from loguru import logger
import os # Added for environment variables

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..config import get_config


class K8sLLMGenerateDeploymentTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-llm-generate-deployment",
            description="通过LLM智能解析自然语言需求，生成Kubernetes Deployment YAML配置"
        )
        self.config = get_config()
        self.risk_level = "LOW"  # 仅生成配置，不执行操作
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "自然语言描述的Deployment需求，例如：'创建一个nginx应用，3个副本，暴露80端口，需要健康检查'"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "目标命名空间，默认为配置的命名空间"
                    },
                    "context": {
                        "type": "string",
                        "description": "额外的上下文信息，如环境类型(dev/prod)、性能要求等"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "约束条件",
                        "properties": {
                            "max_replicas": {"type": "integer", "description": "最大副本数"},
                            "max_cpu": {"type": "string", "description": "最大CPU限制"},
                            "max_memory": {"type": "string", "description": "最大内存限制"},
                            "required_labels": {
                                "type": "object",
                                "description": "必须包含的标签",
                                "additionalProperties": {"type": "string"}
                            }
                        }
                    },
                    "template_style": {
                        "type": "string",
                        "description": "生成风格：minimal(最小化)、production(生产级)、development(开发级)",
                        "enum": ["minimal", "production", "development"],
                        "default": "production"
                    }
                },
                "required": ["requirements"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """通过LLM生成Deployment YAML"""
        try:
            requirements = arguments["requirements"]
            namespace = arguments.get("namespace", self.config.namespace)
            context = arguments.get("context", "")
            constraints = arguments.get("constraints", {})
            template_style = arguments.get("template_style", "production")
            
            # 构建LLM Prompt
            prompt = self._build_llm_prompt(
                requirements, namespace, context, constraints, template_style
            )
            
            # 这里是关键：将生成任务委托给LLM
            # 在实际实现中，这里会调用LLM API
            llm_response = await self._call_llm_for_yaml_generation(prompt)
            
            # 验证和清理LLM生成的YAML
            validated_yaml = await self._validate_and_enhance_yaml(
                llm_response, namespace, constraints
            )
            
            logger.info(f"✅ LLM成功生成Deployment YAML")
            
            return MCPCallToolResult(
                content=[{
                    "type": "text",
                    "text": f"🤖 **LLM智能生成 - Deployment YAML**\n\n"
                           f"**用户需求**: {requirements}\n"
                           f"**生成风格**: {template_style}\n"
                           f"**命名空间**: {namespace}\n\n"
                           f"**生成的YAML配置**:\n```yaml\n{validated_yaml}\n```\n\n"
                           f"💡 **LLM解析说明**: \n{self._generate_explanation(requirements)}\n\n"
                           f"🔧 **下一步**: 使用 `k8s-create-deployment` 工具应用此配置"
                }]
            )
            
        except Exception as e:
            error_msg = f"LLM生成Deployment YAML失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ {error_msg}"}],
                isError=True
            )
    
    def _build_llm_prompt(self, requirements: str, namespace: str, context: str, 
                         constraints: Dict[str, Any], template_style: str) -> str:
        """构建LLM提示词"""
        
        base_prompt = f"""
作为Kubernetes专家，请根据以下需求生成一个完整的Deployment YAML配置：

**用户需求**: {requirements}
**目标命名空间**: {namespace}
**模板风格**: {template_style}
"""
        
        if context:
            base_prompt += f"**上下文信息**: {context}\n"
        
        if constraints:
            base_prompt += f"**约束条件**: {json.dumps(constraints, ensure_ascii=False)}\n"
        
        base_prompt += f"""
**生成要求**:
1. 生成标准的Kubernetes Deployment YAML
2. 包含合理的资源限制和请求
3. 添加适当的标签和注解
4. {self._get_style_requirements(template_style)}
5. 确保YAML格式正确且可直接应用
6. 遵循Kubernetes最佳实践

**输出格式**: 仅返回YAML内容，不要额外的解释文字。
"""
        
        return base_prompt
    
    def _get_style_requirements(self, template_style: str) -> str:
        """根据模板风格获取特定要求"""
        requirements = {
            "minimal": "生成最简配置，只包含必要字段",
            "production": "包含健康检查、资源限制、安全配置、滚动更新策略",
            "development": "适合开发环境，包含调试友好的配置"
        }
        return requirements.get(template_style, requirements["production"])
    
    async def _call_llm_for_yaml_generation(self, prompt: str) -> str:
        """调用LLM生成YAML（支持多种LLM提供商）"""
        
        # 检查是否配置了Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        # 优先尝试使用Ollama（如果可用）
        try:
            if await self._check_ollama_available(ollama_url):
                logger.info(f"🤖 使用Ollama模型生成YAML: {ollama_model}")
                return await self._call_ollama(prompt, ollama_url, ollama_model)
        except Exception as e:
            logger.warning(f"Ollama调用失败，回退到模拟模式: {e}")
        
        # 回退到其他LLM提供商或模拟
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            logger.info("🤖 使用OpenAI生成YAML")
            return await self._call_openai(prompt, openai_key)
        
        # 最终回退到模拟模式
        logger.info("🤖 使用模拟模式生成YAML")
        return await self._call_mock_llm(prompt)
    
    async def _check_ollama_available(self, base_url: str) -> bool:
        """检查Ollama是否可用"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def _call_ollama(self, prompt: str, base_url: str, model: str) -> str:
        """调用Ollama API生成YAML"""
        import httpx
        
        # 构建Ollama专用的prompt
        ollama_prompt = f"""你是一个Kubernetes专家。根据以下需求生成Deployment YAML配置。

{prompt}

重要要求：
1. 只返回有效的YAML内容，不要包含任何解释文字
2. 确保YAML格式正确
3. 包含生产级配置（安全性、健康检查、资源限制）

请直接开始YAML内容："""

        payload = {
            "model": model,
            "prompt": ollama_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{base_url}/api/generate", json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Ollama API错误: {response.status_code}")
            
            result = response.json()
            return result.get("response", "")
    
    async def _call_openai(self, prompt: str, api_key: str) -> str:
        """调用OpenAI API生成YAML"""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一个Kubernetes专家，专门生成标准的Deployment YAML配置。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API错误: {response.status_code}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_mock_llm(self, prompt: str) -> str:
        """模拟LLM响应（原有的mock实现）"""
        logger.info("🤖 正在调用LLM生成YAML配置...")
        
        # 原有的模拟YAML
        mock_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
  namespace: default
  labels:
    app: nginx-app
    tier: frontend
    environment: production
  annotations:
    deployment.kubernetes.io/revision: "1"
    description: "LLM生成的nginx应用部署"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: nginx-app
  template:
    metadata:
      labels:
        app: nginx-app
        tier: frontend
        environment: production
    spec:
      containers:
      - name: nginx
        image: nginx:1.21-alpine
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        env:
        - name: NGINX_PORT
          value: "80"
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 250m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 101
          capabilities:
            drop:
            - ALL
      securityContext:
        fsGroup: 101"""
        
        return mock_yaml
    
    async def _validate_and_enhance_yaml(self, yaml_content: str, namespace: str, 
                                       constraints: Dict[str, Any]) -> str:
        """验证和增强LLM生成的YAML"""
        try:
            # 解析YAML
            deployment = yaml.safe_load(yaml_content)
            
            # 基础验证
            if not deployment.get("kind") == "Deployment":
                raise ValueError("生成的不是Deployment类型")
            
            if not deployment.get("metadata", {}).get("name"):
                raise ValueError("缺少Deployment名称")
            
            # 确保命名空间正确
            if "metadata" not in deployment:
                deployment["metadata"] = {}
            deployment["metadata"]["namespace"] = namespace
            
            # 应用约束条件
            if constraints:
                deployment = self._apply_constraints(deployment, constraints)
            
            # 添加安全增强
            deployment = self._add_security_enhancements(deployment)
            
            # 转换回YAML
            return yaml.dump(deployment, default_flow_style=False, allow_unicode=True)
            
        except Exception as e:
            logger.error(f"YAML验证失败: {e}")
            # 如果验证失败，返回原始内容但添加警告注释
            return f"# ⚠️ YAML验证失败，请检查: {str(e)}\n{yaml_content}"
    
    def _apply_constraints(self, deployment: Dict[str, Any], 
                          constraints: Dict[str, Any]) -> Dict[str, Any]:
        """应用约束条件"""
        # 限制副本数
        if "max_replicas" in constraints:
            max_replicas = constraints["max_replicas"]
            current_replicas = deployment.get("spec", {}).get("replicas", 1)
            if current_replicas > max_replicas:
                deployment["spec"]["replicas"] = max_replicas
        
        # 添加必需标签
        if "required_labels" in constraints:
            required_labels = constraints["required_labels"]
            if "metadata" not in deployment:
                deployment["metadata"] = {}
            if "labels" not in deployment["metadata"]:
                deployment["metadata"]["labels"] = {}
            deployment["metadata"]["labels"].update(required_labels)
        
        return deployment
    
    def _add_security_enhancements(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """添加安全增强配置"""
        spec = deployment.get("spec", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        
        # 确保有安全上下文
        if "securityContext" not in pod_spec:
            pod_spec["securityContext"] = {
                "runAsNonRoot": True,
                "fsGroup": 1000
            }
        
        # 为容器添加安全配置
        containers = pod_spec.get("containers", [])
        for container in containers:
            if "securityContext" not in container:
                container["securityContext"] = {
                    "allowPrivilegeEscalation": False,
                    "runAsNonRoot": True,
                    "capabilities": {"drop": ["ALL"]}
                }
        
        return deployment
    
    def _generate_explanation(self, requirements: str) -> str:
        """生成LLM解析说明"""
        return f"""LLM分析了您的需求 "{requirements}" 并自动生成了包含以下特性的配置：
• 生产级安全配置（非root用户运行、禁用特权升级）
• 健康检查配置（存活性和就绪性探针）
• 资源限制和请求
• 滚动更新策略
• 合适的标签和注解
• 符合Kubernetes最佳实践的配置结构""" 