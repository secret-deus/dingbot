"""K8s描述Pod工具"""

from typing import Dict, Any
from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient
from ..config import get_config

class K8sDescribePodTool(MCPToolBase):
    def __init__(self):
        super().__init__(name="k8s-describe-pod", description="获取Kubernetes Pod详细信息")
        self.config = get_config()
        self.k8s_client = None
    
    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Pod名称"},
                    "namespace": {"type": "string", "description": "命名空间"}
                },
                "required": ["pod_name"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        try:
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            result = await self.k8s_client.describe_pod(
                arguments.get("pod_name"),
                arguments.get("namespace")
            )
            return MCPCallToolResult.success(result)
        except Exception as e:
            return MCPCallToolResult.error(f"获取Pod详情失败: {str(e)}") 