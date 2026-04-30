"""
K8s资源分析报告MCP工具包装器
"""

from typing import Dict, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPCallToolResult, MCPToolSchema
from ..core.k8s_graph import get_shared_knowledge_graph
from ..config import get_config
from .k8s_resource_analysis_report import k8s_resource_analysis_report

class K8sResourceAnalysisReportTool(MCPToolBase):
    """K8s资源分析报告MCP工具"""

    def __init__(self):
        super().__init__(
            name="k8s-resource-analysis-report",
            description="分析知识图谱中的K8s资源数据，生成异常资源报告和优化建议，支持钉钉通知"
        )

    def get_schema(self) -> MCPToolSchema:
        """获取工具schema"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace_filter": {
                        "type": "string",
                        "description": "命名空间过滤器，为空表示分析所有命名空间的资源。例如: 'test', 'default', 'prod'",
                        "examples": ["test", "default", "prod", ""]
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "是否包含LLM生成的优化建议。默认为true",
                        "default": True
                    },
                    "send_dingtalk_notification": {
                        "type": "boolean",
                        "description": "是否发送钉钉通知（仅当发现异常资源时）。默认为true",
                        "default": True
                    }
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行资源分析报告"""
        try:
            # 获取参数
            namespace_filter = arguments.get("namespace_filter", "")
            include_recommendations = arguments.get("include_recommendations", True)
            send_dingtalk_notification = arguments.get("send_dingtalk_notification", True)

            logger.info(f"🔍 开始K8s资源分析报告: namespace_filter={namespace_filter}")

            # 获取必要的依赖
            kg = get_shared_knowledge_graph()
            config = get_config()

            if not kg:
                error_msg = "知识图谱未初始化"
                return MCPCallToolResult(
                    content=[{"type": "text", "text": f"执行失败: {error_msg}"}],
                    is_error=True
                )

            # 执行分析
            result = await k8s_resource_analysis_report(
                kg=kg,
                config=config,
                namespace_filter=namespace_filter,
                include_recommendations=include_recommendations,
                send_dingtalk_notification=send_dingtalk_notification
            )

            logger.info(f"✅ 资源分析报告完成: {result.get('statistics', {})}")

            # 构建返回结果
            if result.get("success", False):
                report_text = result.get("report", "")
                return MCPCallToolResult(
                    content=[{"type": "text", "text": report_text}],
                    is_error=False
                )
            else:
                error_msg = result.get("error", "未知错误")
                return MCPCallToolResult(
                    content=[{"type": "text", "text": f"执行失败: {error_msg}"}],
                    is_error=True
                )

        except Exception as e:
            error_msg = f"资源分析报告执行失败: {str(e)}"
            logger.error(error_msg)
            return MCPCallToolResult(
                content=[{"type": "text", "text": error_msg}],
                is_error=True
            )
