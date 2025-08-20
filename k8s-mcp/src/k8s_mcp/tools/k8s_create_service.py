"""K8s创建Service工具"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sCreateServiceTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-create-service",
            description="创建Kubernetes Service，支持ClusterIP、NodePort、LoadBalancer等类型"
        )
        self.config = get_config()
        self.k8s_client = None
        self.risk_level = "MEDIUM"  # 创建资源属于中等风险
    
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
                    "type": {
                        "type": "string",
                        "description": "Service类型：ClusterIP、NodePort、LoadBalancer",
                        "enum": ["ClusterIP", "NodePort", "LoadBalancer"]
                    },
                    "selector": {
                        "type": "object",
                        "description": "标签选择器，用于选择目标Pod",
                        "additionalProperties": {"type": "string"}
                    },
                    "ports": {
                        "type": "array",
                        "description": "端口配置列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "端口名称"},
                                "port": {"type": "integer", "description": "Service端口"},
                                "target_port": {"type": ["integer", "string"], "description": "目标端口"},
                                "protocol": {"type": "string", "description": "协议", "enum": ["TCP", "UDP"]},
                                "node_port": {"type": "integer", "description": "NodePort端口（仅NodePort类型）"}
                            },
                            "required": ["port"]
                        }
                    },
                    "labels": {
                        "type": "object",
                        "description": "Service标签",
                        "additionalProperties": {"type": "string"}
                    },
                    "annotations": {
                        "type": "object",
                        "description": "Service注解",
                        "additionalProperties": {"type": "string"}
                    },
                    "cluster_ip": {
                        "type": "string",
                        "description": "指定ClusterIP地址（可选）"
                    },
                    "external_ips": {
                        "type": "array",
                        "description": "外部IP地址列表",
                        "items": {"type": "string"}
                    },
                    "load_balancer_ip": {
                        "type": "string",
                        "description": "LoadBalancer IP地址（仅LoadBalancer类型）"
                    },
                    "session_affinity": {
                        "type": "string",
                        "description": "会话亲和性",
                        "enum": ["None", "ClientIP"]
                    }
                },
                "required": ["name", "selector", "ports"]
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
            
            # 参数验证
            if not name:
                return MCPCallToolResult.error("Service名称不能为空")
            
            selector = arguments.get("selector", {})
            if not selector:
                return MCPCallToolResult.error("标签选择器不能为空")
            
            ports = arguments.get("ports", [])
            if not ports:
                return MCPCallToolResult.error("端口配置不能为空")
            
            # 构建Service规格
            service_spec = {
                "name": name,
                "type": arguments.get("type", "ClusterIP"),
                "selector": selector,
                "ports": ports,
                "labels": arguments.get("labels", {}),
                "annotations": arguments.get("annotations", {}),
                "session_affinity": arguments.get("session_affinity", "None")
            }
            
            # 可选字段
            if arguments.get("cluster_ip"):
                service_spec["cluster_ip"] = arguments["cluster_ip"]
            if arguments.get("external_ips"):
                service_spec["external_ips"] = arguments["external_ips"]
            if arguments.get("load_balancer_ip"):
                service_spec["load_balancer_ip"] = arguments["load_balancer_ip"]
            
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            result = await self.k8s_client.create_service(namespace, service_spec)
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"创建Service失败: {e.message}")
            return MCPCallToolResult.error(f"创建Service失败: {e.message}")
        except Exception as e:
            logger.error(f"创建Service时发生未知错误: {str(e)}")
            return MCPCallToolResult.error(f"创建Service失败: {str(e)}") 