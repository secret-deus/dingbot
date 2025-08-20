"""K8s创建Deployment工具"""

import yaml
from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sCreateDeploymentTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-create-deployment",
            description="创建或应用Kubernetes Deployment，支持YAML配置和参数配置"
        )
        self.config = get_config()
        self.k8s_client = None
        self.risk_level = "HIGH"  # 创建Deployment属于高风险操作
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "yaml_config": {
                        "type": "string",
                        "description": "Deployment的YAML配置内容（优先使用）"
                    },
                    "app_name": {
                        "type": "string",
                        "description": "应用名称（当未提供yaml_config时必需）"
                    },
                    "image": {
                        "type": "string",
                        "description": "容器镜像地址（当未提供yaml_config时必需）"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，默认使用配置的命名空间"
                    },
                    "replicas": {
                        "type": "integer",
                        "description": "副本数量",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "labels": {
                        "type": "object",
                        "description": "自定义标签",
                        "additionalProperties": {"type": "string"}
                    },
                    "env_vars": {
                        "type": "array",
                        "description": "环境变量列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            },
                            "required": ["name", "value"]
                        }
                    },
                    "ports": {
                        "type": "array",
                        "description": "容器端口配置",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "containerPort": {"type": "integer"},
                                "protocol": {"type": "string", "enum": ["TCP", "UDP"], "default": "TCP"}
                            },
                            "required": ["containerPort"]
                        }
                    },
                    "resources": {
                        "type": "object",
                        "description": "资源限制配置",
                        "properties": {
                            "limits": {
                                "type": "object",
                                "properties": {
                                    "cpu": {"type": "string"},
                                    "memory": {"type": "string"}
                                }
                            },
                            "requests": {
                                "type": "object",
                                "properties": {
                                    "cpu": {"type": "string"},
                                    "memory": {"type": "string"}
                                }
                            }
                        }
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "是否为演练模式（仅验证配置，不实际创建）",
                        "default": False
                    },
                    "force": {
                        "type": "boolean",
                        "description": "是否强制替换已存在的Deployment",
                        "default": False
                    }
                },
                "anyOf": [
                    {"required": ["yaml_config"]},
                    {"required": ["app_name", "image"]}
                ]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """创建Deployment"""
        try:
            namespace = arguments.get("namespace", self.config.namespace)
            dry_run = arguments.get("dry_run", False)
            force = arguments.get("force", False)
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
            
            # 解析配置
            if "yaml_config" in arguments:
                # 使用YAML配置
                yaml_config = arguments["yaml_config"]
                try:
                    deployment_config = yaml.safe_load(yaml_config)
                except yaml.YAMLError as e:
                    return MCPCallToolResult(
                        content=[{"type": "text", "text": f"❌ YAML配置解析失败: {str(e)}"}],
                        isError=True
                    )
                
                app_name = deployment_config.get("metadata", {}).get("name")
                if not app_name:
                    return MCPCallToolResult(
                        content=[{"type": "text", "text": "❌ YAML配置中缺少Deployment名称"}],
                        isError=True
                    )
                
                # 确保命名空间正确
                if "metadata" not in deployment_config:
                    deployment_config["metadata"] = {}
                deployment_config["metadata"]["namespace"] = namespace
                
            else:
                # 使用参数构建配置
                app_name = arguments["app_name"]
                image = arguments["image"]
                replicas = arguments.get("replicas", 1)
                labels = arguments.get("labels", {})
                env_vars = arguments.get("env_vars", [])
                ports = arguments.get("ports", [])
                resources = arguments.get("resources", {})
                
                # 构建基础标签
                base_labels = {
                    "app": app_name,
                    "version": "v1",
                    **labels
                }
                
                # 构建Deployment配置
                deployment_config = {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": app_name,
                        "namespace": namespace,
                        "labels": base_labels
                    },
                    "spec": {
                        "replicas": replicas,
                        "selector": {
                            "matchLabels": {"app": app_name}
                        },
                        "template": {
                            "metadata": {
                                "labels": base_labels
                            },
                            "spec": {
                                "containers": [{
                                    "name": app_name,
                                    "image": image,
                                    "imagePullPolicy": "IfNotPresent"
                                }]
                            }
                        }
                    }
                }
                
                container = deployment_config["spec"]["template"]["spec"]["containers"][0]
                
                # 添加环境变量
                if env_vars:
                    container["env"] = env_vars
                
                # 添加端口配置
                if ports:
                    container["ports"] = ports
                
                # 添加资源限制
                if resources:
                    container["resources"] = resources
            
            # 检查Deployment是否已存在
            existing_deployment = None
            try:
                existing_deployment = await self.k8s_client.get_deployment(namespace, app_name)
            except K8sClientError:
                # Deployment不存在，可以创建
                pass
            
            if existing_deployment and not force:
                return MCPCallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"⚠️ Deployment `{app_name}` 在命名空间 `{namespace}` 中已存在\n\n"
                               f"如需强制替换，请设置 `force: true` 参数"
                    }]
                )
            
            # 演练模式
            if dry_run:
                yaml_content = yaml.dump(deployment_config, default_flow_style=False, allow_unicode=True)
                return MCPCallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"🔍 **演练模式 - 配置验证通过**\n\n"
                               f"**Deployment名称**: {app_name}\n"
                               f"**命名空间**: {namespace}\n"
                               f"**操作**: {'替换' if existing_deployment else '创建'}\n\n"
                               f"**YAML配置**:\n```yaml\n{yaml_content}\n```\n\n"
                               f"💡 **提示**: 移除 `dry_run: true` 参数以实际执行创建操作"
                    }]
                )
            
            # 执行创建或更新
            if existing_deployment:
                # 更新现有Deployment
                result = await self.k8s_client.update_deployment(namespace, app_name, deployment_config)
                operation = "更新"
            else:
                # 创建新Deployment
                result = await self.k8s_client.create_deployment(namespace, deployment_config)
                operation = "创建"
            
            logger.info(f"✅ 成功{operation}Deployment: {app_name} (命名空间: {namespace})")
            
            # 获取部署状态
            deployment_info = await self.k8s_client.get_deployment(namespace, app_name)
            status = deployment_info.get("status", {})
            
            return MCPCallToolResult(
                content=[{
                    "type": "text",
                    "text": f"✅ **Deployment {operation}成功**\n\n"
                           f"**名称**: {app_name}\n"
                           f"**命名空间**: {namespace}\n"
                           f"**副本状态**: {status.get('readyReplicas', 0)}/{status.get('replicas', 0)}\n"
                           f"**更新状态**: {status.get('conditions', [{}])[-1].get('type', '未知') if status.get('conditions') else '未知'}\n\n"
                           f"🔍 **查看状态**: 使用 `k8s-get-deployments` 工具查看详细状态\n"
                           f"📋 **查看Pod**: 使用 `k8s-get-pods` 工具查看相关Pod状态"
                }]
            )
            
        except K8sClientError as e:
            error_msg = f"Kubernetes操作失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ {error_msg}"}],
                isError=True
            )
        except Exception as e:
            error_msg = f"创建Deployment失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ {error_msg}"}],
                isError=True
            ) 