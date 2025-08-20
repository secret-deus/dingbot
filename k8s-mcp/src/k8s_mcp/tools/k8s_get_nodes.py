"""K8s获取节点工具"""

from typing import Dict, Any
from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient
from ..config import get_config

class K8sGetNodesTool(MCPToolBase):
    def __init__(self):
        super().__init__(name="k8s-get-nodes", description="获取Kubernetes Node列表")
        self.config = get_config()
        self.k8s_client = None
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={"type": "object", "properties": {}, "required": []}
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            result = await self.k8s_client.get_nodes()
            return MCPCallToolResult.success(result)
        except Exception as e:
            return MCPCallToolResult.error(f"获取节点失败: {str(e)}") 