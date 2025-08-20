"""K8s获取Service端点工具"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sGetEndpointsTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="k8s-get-endpoints",
            description="获取Kubernetes Service端点信息，显示实际的Pod IP和端口"
        )
        self.config = get_config()
        self.k8s_client = None
        self.risk_level = "SAFE"  # 查询操作属于安全级别
    
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
                        "description": "Service名称，为空时获取命名空间下所有端点"
                    }
                },
                "required": []
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
            
            # 如果name为空，则获取所有端点
            service_name = name if name else None
            
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            result = await self.k8s_client.get_endpoints(namespace, service_name)
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"获取端点失败: {e.message}")
            return MCPCallToolResult.error(f"获取端点失败: {e.message}")
        except Exception as e:
            logger.error(f"获取端点时发生未知错误: {str(e)}")
            return MCPCallToolResult.error(f"获取端点失败: {str(e)}") 