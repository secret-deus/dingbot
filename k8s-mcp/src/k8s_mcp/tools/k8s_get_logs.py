"""
K8s获取Pod日志工具

实现真实的Kubernetes Pod日志查询功能
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sGetLogsTool(MCPToolBase):
    """K8s获取Pod日志工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-get-logs",
            description="获取Kubernetes Pod日志"
        )
        self.config = get_config()
        self.k8s_client = None
        
        logger.info("K8s获取Pod日志工具已初始化")
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Pod名称"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，不指定则使用默认命名空间",
                        "default": self.config.namespace
                    },
                    "lines": {
                        "type": "integer",
                        "description": "返回的日志行数",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["pod_name"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        try:
            # 获取参数
            pod_name = arguments.get("pod_name")
            namespace = arguments.get("namespace")
            lines = arguments.get("lines", 100)
            
            # 参数验证
            if not pod_name:
                return MCPCallToolResult.error("Pod名称不能为空")
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            # 获取日志
            result = await self.k8s_client.get_pod_logs(
                pod_name=pod_name,
                namespace=namespace,
                lines=lines
            )
            
            logger.info(f"获取Pod日志成功: {pod_name}")
            return MCPCallToolResult.success(result)
            
        except K8sClientError as e:
            logger.error(f"K8s客户端错误: {e.message}")
            return MCPCallToolResult.error(f"K8s操作失败: {e.message}")
        except Exception as e:
            logger.error(f"获取Pod日志时发生错误: {e}")
            return MCPCallToolResult.error(f"获取日志失败: {str(e)}") 