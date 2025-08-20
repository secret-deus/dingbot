"""K8s生成Deployment YAML工具"""

import yaml
from typing import Dict, Any, List, Optional
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..config import get_config


class K8sGenerateDeploymentYamlTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-generate-deployment-yaml",
            description="通过LLM智能生成Kubernetes Deployment的YAML配置文件"
        )
        self.config = get_config()
        self.risk_level = "LOW"  # 仅生成YAML，不执行操作，风险较低
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "应用名称"
                    },
                    "image": {
                        "type": "string",
                        "description": "容器镜像地址，例如：nginx:1.21、redis:6.2"
                    },
                    "replicas": {
                        "type": "integer",
                        "description": "副本数量",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，默认使用配置的命名空间"
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
                                    "cpu": {"type": "string", "description": "CPU限制，如：100m, 1"},
                                    "memory": {"type": "string", "description": "内存限制，如：128Mi, 1Gi"}
                                }
                            },
                            "requests": {
                                "type": "object",
                                "properties": {
                                    "cpu": {"type": "string", "description": "CPU请求，如：50m, 0.5"},
                                    "memory": {"type": "string", "description": "内存请求，如：64Mi, 512Mi"}
                                }
                            }
                        }
                    },
                    "volume_mounts": {
                        "type": "array",
                        "description": "卷挂载配置",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "mountPath": {"type": "string"},
                                "readOnly": {"type": "boolean", "default": False}
                            },
                            "required": ["name", "mountPath"]
                        }
                    },
                    "volumes": {
                        "type": "array",
                        "description": "卷配置",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "enum": ["emptyDir", "configMap", "secret", "persistentVolumeClaim"]},
                                "source": {"type": "string", "description": "根据类型提供相应的源，如ConfigMap名称、PVC名称等"}
                            },
                            "required": ["name", "type"]
                        }
                    },
                    "strategy": {
                        "type": "object",
                        "description": "部署策略配置",
                        "properties": {
                            "type": {"type": "string", "enum": ["RollingUpdate", "Recreate"], "default": "RollingUpdate"},
                            "maxUnavailable": {"type": "string", "description": "最大不可用数量或百分比"},
                            "maxSurge": {"type": "string", "description": "最大超出数量或百分比"}
                        }
                    }
                },
                "required": ["app_name", "image"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """生成Deployment YAML配置"""
        try:
            app_name = arguments["app_name"]
            image = arguments["image"]
            replicas = arguments.get("replicas", 1)
            namespace = arguments.get("namespace", self.config.namespace)
            labels = arguments.get("labels", {})
            env_vars = arguments.get("env_vars", [])
            ports = arguments.get("ports", [])
            resources = arguments.get("resources", {})
            volume_mounts = arguments.get("volume_mounts", [])
            volumes = arguments.get("volumes", [])
            strategy = arguments.get("strategy", {})
            
            # 构建基础标签
            base_labels = {
                "app": app_name,
                "version": "v1",
                **labels
            }
            
            # 构建Deployment配置
            deployment = {
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
            
            container = deployment["spec"]["template"]["spec"]["containers"][0]
            
            # 添加环境变量
            if env_vars:
                container["env"] = env_vars
            
            # 添加端口配置
            if ports:
                container["ports"] = ports
            
            # 添加资源限制
            if resources:
                container["resources"] = resources
            
            # 添加卷挂载
            if volume_mounts:
                container["volumeMounts"] = volume_mounts
            
            # 添加卷配置
            if volumes:
                deployment["spec"]["template"]["spec"]["volumes"] = []
                for vol in volumes:
                    volume_config = {"name": vol["name"]}
                    
                    if vol["type"] == "emptyDir":
                        volume_config["emptyDir"] = {}
                    elif vol["type"] == "configMap":
                        volume_config["configMap"] = {"name": vol.get("source", vol["name"])}
                    elif vol["type"] == "secret":
                        volume_config["secret"] = {"secretName": vol.get("source", vol["name"])}
                    elif vol["type"] == "persistentVolumeClaim":
                        volume_config["persistentVolumeClaim"] = {"claimName": vol.get("source", vol["name"])}
                    
                    deployment["spec"]["template"]["spec"]["volumes"].append(volume_config)
            
            # 添加部署策略
            if strategy:
                deployment["spec"]["strategy"] = {
                    "type": strategy.get("type", "RollingUpdate")
                }
                if strategy.get("type") == "RollingUpdate":
                    rolling_update = {}
                    if strategy.get("maxUnavailable"):
                        rolling_update["maxUnavailable"] = strategy["maxUnavailable"]
                    if strategy.get("maxSurge"):
                        rolling_update["maxSurge"] = strategy["maxSurge"]
                    if rolling_update:
                        deployment["spec"]["strategy"]["rollingUpdate"] = rolling_update
            
            # 转换为YAML
            yaml_content = yaml.dump(deployment, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"✅ 成功生成Deployment YAML: {app_name}")
            
            return MCPCallToolResult(
                content=[{
                    "type": "text",
                    "text": f"🚀 **Deployment YAML已生成**\n\n"
                           f"**应用名称**: {app_name}\n"
                           f"**镜像**: {image}\n"
                           f"**副本数**: {replicas}\n"
                           f"**命名空间**: {namespace}\n\n"
                           f"**YAML配置**:\n```yaml\n{yaml_content}\n```\n\n"
                           f"💡 **使用提示**: 可以使用 `k8s-create-deployment` 工具直接应用此配置"
                }]
            )
            
        except Exception as e:
            error_msg = f"生成Deployment YAML失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ {error_msg}"}],
                isError=True
            ) 