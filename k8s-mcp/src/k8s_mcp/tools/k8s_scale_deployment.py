"""
K8s扩缩容Deployment工具

实现真实的Kubernetes Deployment扩缩容功能
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sScaleDeploymentTool(MCPToolBase):
    """K8s扩缩容Deployment工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-scale-deployment",
            description="扩缩容Kubernetes Deployment副本数量"
        )
        self.config = get_config()
        self.k8s_client = None
        
        logger.info("K8s扩缩容Deployment工具已初始化")
    
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
                    "replicas": {
                        "type": "integer",
                        "description": "目标副本数量",
                        "minimum": 0
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，不指定则使用默认命名空间",
                        "default": self.config.namespace
                    }
                },
                "required": ["name", "replicas"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        try:
            # 获取参数
            name = arguments.get("name")
            replicas = arguments.get("replicas")
            namespace = arguments.get("namespace")
            
            # 参数验证
            if not name:
                return MCPCallToolResult.error("Deployment名称不能为空")
            
            if replicas is None or replicas < 0:
                return MCPCallToolResult.error("副本数量必须是非负整数")
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            # 执行扩缩容
            result = await self.k8s_client.scale_deployment(
                name=name,
                replicas=replicas,
                namespace=namespace
            )
            
            # 格式化结果
            formatted_result = self._format_scale_result(result)
            
            logger.info(f"扩缩容Deployment成功: {name} -> {replicas} 副本")
            return MCPCallToolResult.success(formatted_result)
            
        except K8sClientError as e:
            logger.error(f"K8s客户端错误: {e.message}")
            return MCPCallToolResult.error(f"K8s操作失败: {e.message}")
        except Exception as e:
            logger.error(f"扩缩容Deployment时发生错误: {e}")
            return MCPCallToolResult.error(f"扩缩容失败: {str(e)}")
    
    def _format_scale_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化扩缩容结果"""
        return {
            "deployment_name": result["deployment_name"],
            "namespace": result["namespace"],
            "scaling_info": {
                "previous_replicas": result["previous_replicas"],
                "target_replicas": result["target_replicas"],
                "current_replicas": result["current_replicas"]
            },
            "success": result["success"],
            "message": result["message"]
        } 