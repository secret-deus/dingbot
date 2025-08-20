"""K8s修改Service工具（JSON Patch方式）"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sPatchServiceTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-patch-service",
            description="使用JSON Patch方式修改Kubernetes Service配置，支持精确的字段修改"
        )
        self.config = get_config()
        self.k8s_client = None
        self.risk_level = "MEDIUM"  # 修改资源属于中等风险
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，默认使用配置的命名空间"
                    },
                    "name": {
                        "type": "string",
                        "description": "Service名称"
                    },
                    "patch_data": {
                        "type": "object",
                        "description": "JSON补丁数据，支持strategic merge patch格式",
                        "properties": {
                            "metadata": {
                                "type": "object",
                                "description": "元数据修改",
                                "properties": {
                                    "labels": {
                                        "type": "object",
                                        "description": "标签修改",
                                        "additionalProperties": {"type": "string"}
                                    },
                                    "annotations": {
                                        "type": "object",
                                        "description": "注解修改",
                                        "additionalProperties": {"type": "string"}
                                    }
                                }
                            },
                            "spec": {
                                "type": "object",
                                "description": "规格修改",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Service类型",
                                        "enum": ["ClusterIP", "NodePort", "LoadBalancer"]
                                    },
                                    "selector": {
                                        "type": "object",
                                        "description": "标签选择器",
                                        "additionalProperties": {"type": "string"}
                                    },
                                    "ports": {
                                        "type": "array",
                                        "description": "端口配置",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "port": {"type": "integer"},
                                                "target_port": {"type": ["integer", "string"]},
                                                "protocol": {"type": "string", "enum": ["TCP", "UDP"]},
                                                "node_port": {"type": "integer"}
                                            }
                                        }
                                    },
                                    "external_ips": {
                                        "type": "array",
                                        "description": "外部IP地址",
                                        "items": {"type": "string"}
                                    },
                                    "load_balancer_ip": {
                                        "type": "string",
                                        "description": "LoadBalancer IP"
                                    },
                                    "session_affinity": {
                                        "type": "string",
                                        "description": "会话亲和性",
                                        "enum": ["None", "ClientIP"]
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["name", "patch_data"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            namespace = arguments.get("namespace") or ""
            name = arguments.get("name") or ""
            
            # 安全地处理字符串参数
            if isinstance(namespace, str):
                namespace = namespace.strip()
            if isinstance(name, str):
                name = name.strip()
            patch_data = arguments.get("patch_data", {})
            
            # 参数验证
            if not name:
                return MCPCallToolResult.error("Service名称不能为空")
            
            if not patch_data:
                return MCPCallToolResult.error("补丁数据不能为空")
            
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            result = await self.k8s_client.patch_service(namespace, name, patch_data)
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"修改Service失败: {e.message}")
            return MCPCallToolResult.error(f"修改Service失败: {e.message}")
        except Exception as e:
            logger.error(f"修改Service时发生未知错误: {str(e)}")
            return MCPCallToolResult.error(f"修改Service失败: {str(e)}") 