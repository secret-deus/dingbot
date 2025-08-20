"""K8s获取事件工具"""

from typing import Dict, Any
from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient
from ..config import get_config

class K8sGetEventsTool(MCPToolBase):
    def __init__(self):
        super().__init__(name="k8s-get-events", description="获取Kubernetes事件列表")
        self.config = get_config()
        self.k8s_client = None
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "命名空间"},
                    "limit": {"type": "integer", "description": "返回事件数量限制"}
                },
                "required": []
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            result = await self.k8s_client.get_events(
                arguments.get("namespace"),
                arguments.get("limit")
            )
            return MCPCallToolResult.success(result)
        except Exception as e:
            return MCPCallToolResult.error(f"获取事件失败: {str(e)}") 