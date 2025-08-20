"""K8s获取部署工具"""

from typing import Dict, Any
from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient
from ..config import get_config

class K8sGetDeploymentsTool(MCPToolBase):
    def __init__(self):
        super().__init__(name="k8s-get-deployments", description="获取Kubernetes Deployment列表")
        self.config = get_config()
        self.k8s_client = None
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={"type": "object", "properties": {"namespace": {"type": "string"}}, "required": []}
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            result = await self.k8s_client.get_deployments(arguments.get("namespace"))
            return MCPCallToolResult.success(result)
        except Exception as e:
            return MCPCallToolResult.error(f"获取部署失败: {str(e)}") 