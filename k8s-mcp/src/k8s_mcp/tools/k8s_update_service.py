"""K8s更新Service工具"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sUpdateServiceTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-update-service",
            description="更新Kubernetes Service配置，包括端口、选择器、类型等"
        )
        self.config = get_config()
        self.k8s_client = None
        self.risk_level = "MEDIUM"  # 更新资源属于中等风险
    
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
                "required": ["name"]
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
            
            # 构建更新规格（只包含要更新的字段）
            service_spec = {}
            
            # 可选更新字段
            if "type" in arguments:
                service_spec["type"] = arguments["type"]
            if "selector" in arguments:
                service_spec["selector"] = arguments["selector"]
            if "ports" in arguments:
                service_spec["ports"] = arguments["ports"]
            if "labels" in arguments:
                service_spec["labels"] = arguments["labels"]
            if "annotations" in arguments:
                service_spec["annotations"] = arguments["annotations"]
            if "external_ips" in arguments:
                service_spec["external_ips"] = arguments["external_ips"]
            if "load_balancer_ip" in arguments:
                service_spec["load_balancer_ip"] = arguments["load_balancer_ip"]
            if "session_affinity" in arguments:
                service_spec["session_affinity"] = arguments["session_affinity"]
            
            if not service_spec:
                return MCPCallToolResult.error("至少需要指定一个要更新的字段")
            
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            result = await self.k8s_client.update_service(namespace, name, service_spec)
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"更新Service失败: {e.message}")
            return MCPCallToolResult.error(f"更新Service失败: {e.message}")
        except Exception as e:
            logger.error(f"更新Service时发生未知错误: {str(e)}")
            return MCPCallToolResult.error(f"更新Service失败: {str(e)}") 