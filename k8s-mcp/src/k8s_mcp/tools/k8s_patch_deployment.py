"""
K8s更新Deployment配置工具

实现Kubernetes Deployment配置更新功能
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sPatchDeploymentTool(MCPToolBase):
    """K8s更新Deployment配置工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-patch-deployment",
            description="更新Kubernetes Deployment配置，如镜像版本、环境变量、资源限制等"
        )
        self.config = get_config()
        self.k8s_client = None
        
        logger.info("K8s更新Deployment配置工具已初始化")
    
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
                    "patch_data": {
                        "type": "object",
                        "description": "要更新的配置数据（JSON格式），如：{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"container-name\",\"image\":\"new-image:tag\"}]}}}}",
                        "additionalProperties": True
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，不指定则使用默认命名空间",
                        "default": self.config.namespace
                    }
                },
                "required": ["name", "patch_data"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        try:
            # 获取参数
            name = arguments.get("name")
            patch_data = arguments.get("patch_data")
            namespace = arguments.get("namespace")
            
            # 参数验证
            if not name or not name.strip():
                return MCPCallToolResult.error("Deployment名称不能为空")
            
            if not patch_data:
                return MCPCallToolResult.error("更新配置数据不能为空")
            
            if not isinstance(patch_data, dict):
                return MCPCallToolResult.error("更新配置数据必须是JSON对象格式")
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            # 更新Deployment配置
            result = await self.k8s_client.patch_deployment(
                name=name,
                patch_data=patch_data,
                namespace=namespace
            )
            
            logger.info(f"更新Deployment配置成功: {name}")
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"K8s客户端错误: {e.message}")
            return MCPCallToolResult.error(f"K8s操作失败: {e.message}")
        except Exception as e:
            logger.error(f"更新Deployment配置时发生错误: {e}")
            return MCPCallToolResult.error(f"配置更新失败: {str(e)}") 