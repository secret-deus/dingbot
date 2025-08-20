"""K8s获取服务工具"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sGetServicesTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-get-services",
            description="获取Kubernetes Service列表"
        )
        self.config = get_config()
        self.k8s_client = None
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称"
                    }
                },
                "required": []
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            namespace = arguments.get("namespace")
            
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            result = await self.k8s_client.get_services(namespace=namespace)
            return MCPCallToolResult.success(result)
            
        except Exception as e:
            return MCPCallToolResult.error(f"获取服务失败: {str(e)}") 