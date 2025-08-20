"""
K8s获取Deployment历史版本工具

查看Kubernetes Deployment的版本历史和变更记录
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sGetDeploymentHistoryTool(MCPToolBase):
    """K8s获取Deployment历史版本工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-get-deployment-history",
            description="获取Kubernetes Deployment的版本历史和变更记录"
        )
        self.config = get_config()
        self.k8s_client = None
        
        logger.info("K8s获取Deployment历史版本工具已初始化")
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Deployment名称"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，不指定则使用默认命名空间",
                        "default": self.config.namespace
                    }
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        try:
            # 获取参数
            name = arguments.get("name")
            namespace = arguments.get("namespace")
            
            # 参数验证
            if not name or not name.strip():
                return MCPCallToolResult.error("Deployment名称不能为空")
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            # 获取Deployment历史版本
            result = await self.k8s_client.get_deployment_history(
                name=name,
                namespace=namespace
            )
            
            logger.info(f"获取Deployment历史版本成功: {name}, 共 {result['total_revisions']} 个版本")
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"K8s客户端错误: {e.message}")
            return MCPCallToolResult.error(f"K8s操作失败: {e.message}")
        except Exception as e:
            logger.error(f"获取Deployment历史版本时发生错误: {e}")
            return MCPCallToolResult.error(f"获取历史版本失败: {str(e)}") 