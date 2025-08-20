"""
K8s获取Pod列表工具

实现真实的Kubernetes Pod查询功能
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sGetPodsTool(MCPToolBase):
    """K8s获取Pod列表工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-get-pods",
            description="获取Kubernetes Pod列表，支持命名空间和标签过滤"
        )
        self.config = get_config()
        self.k8s_client = None
        
        logger.info("K8s获取Pod列表工具已初始化")
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间名称，'all' 表示所有命名空间，不指定则使用默认命名空间",
                        "default": self.config.namespace
                    },
                    "label_selector": {
                        "type": "string",
                        "description": "标签选择器，例如 'app=nginx,env=prod'",
                        "default": None
                    }
                },
                "required": []
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行工具"""
        try:
            # 获取参数
            namespace = arguments.get("namespace")
            label_selector = arguments.get("label_selector")
            
            # 初始化K8s客户端
            if not self.k8s_client:
                self.k8s_client = K8sClient(self.config)
                await self.k8s_client.connect()
            
            # 获取Pod列表
            result = await self.k8s_client.get_pods(
                namespace=namespace,
                label_selector=label_selector
            )
            
            # 格式化结果
            formatted_result = self._format_pods_result(result)
            
            logger.info(f"获取Pod列表成功: {result['total']} 个Pod")
            return MCPCallToolResult.success(formatted_result)
            
        except K8sClientError as e:
            logger.error(f"K8s客户端错误: {e.message}")
            return MCPCallToolResult.error(f"K8s操作失败: {e.message}")
        except Exception as e:
            logger.error(f"获取Pod列表时发生错误: {e}")
            return MCPCallToolResult.error(f"获取Pod列表失败: {str(e)}")
    
    def _format_pods_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化Pod结果"""
        formatted = {
            "summary": {
                "namespace": result["namespace"],
                "total_pods": result["total"],
                "status_summary": self._get_status_summary(result["items"])
            },
            "pods": []
        }
        
        for pod in result["items"]:
            formatted_pod = {
                "name": pod["name"],
                "namespace": pod["namespace"],
                "status": pod["phase"],
                "ready": pod["ready"],
                "restarts": pod["restarts"],
                "age": pod["age"],
                "node": pod["node"],
                "ip": pod["ip"],
                "containers": []
            }
            
            # 格式化容器信息
            for container in pod.get("containers", []):
                formatted_container = {
                    "name": container["name"],
                    "image": container["image"],
                    "ready": container["ready"],
                    "restarts": container["restart_count"]
                }
                formatted_pod["containers"].append(formatted_container)
            
            formatted["pods"].append(formatted_pod)
        
        return formatted
    
    def _get_status_summary(self, pods: list) -> Dict[str, int]:
        """获取Pod状态摘要"""
        summary = {
            "Running": 0,
            "Pending": 0,
            "Succeeded": 0,
            "Failed": 0,
            "Unknown": 0
        }
        
        for pod in pods:
            status = pod.get("phase", "Unknown")
            if status in summary:
                summary[status] += 1
            else:
                summary["Unknown"] += 1
        
        return summary 