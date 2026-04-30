"""
K8s指标覆盖报告工具

提供deployment指标覆盖情况和错误处理统计
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPCallToolResult, MCPToolSchema
from ..core.k8s_graph import get_shared_knowledge_graph
from ..core.metrics_aggregator import get_metrics_aggregator


class K8sMetricsCoverageReportTool(MCPToolBase):
    """K8s指标覆盖报告工具

    功能：
    - 检查知识图谱中所有deployment的指标覆盖情况
    - 显示指标更新统计和错误处理信息
    - 提供deployment指标健康度评估
    """

    def __init__(self):
        super().__init__(
            name="k8s-metrics-coverage-report",
            description="生成deployment指标覆盖情况和错误处理统计报告"
        )
        self.input_schema = {
            "type": "object",
            "properties": {
                "include_details": {
                    "type": "boolean",
                    "description": "是否包含详细的deployment信息",
                    "default": False
                },
                "filter_namespace": {
                    "type": "string",
                    "description": "过滤特定命名空间（可选）",
                    "default": ""
                },
                "show_failed_only": {
                    "type": "boolean",
                    "description": "只显示更新失败的deployment",
                    "default": False
                }
            },
            "required": []
        }
        self.kg = get_shared_knowledge_graph()

    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行指标覆盖报告生成"""
        try:
            # 解析参数
            include_details = arguments.get("include_details", False)
            filter_namespace = arguments.get("filter_namespace", "")
            show_failed_only = arguments.get("show_failed_only", False)

            logger.info(f"生成指标覆盖报告: namespace={filter_namespace or 'all'}, details={include_details}")

            # 获取所有deployment信息
            deployment_info = await self._analyze_deployment_coverage(filter_namespace)

            # 获取聚合器统计信息
            aggregator_stats = self._get_aggregator_statistics()

            # 生成报告
            report = self._generate_coverage_report(
                deployment_info,
                aggregator_stats,
                include_details,
                show_failed_only
            )

            return MCPCallToolResult(
                content=[{"type": "text", "text": report}],
                is_error=False
            )

        except Exception as e:
            logger.error(f"生成指标覆盖报告失败: {e}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ 生成指标覆盖报告失败: {str(e)}"}],
                is_error=True
            )

    async def _analyze_deployment_coverage(self, filter_namespace: str) -> Dict[str, Any]:
        """分析deployment指标覆盖情况"""
        deployments_with_metrics = []
        deployments_without_metrics = []
        outdated_deployments = []

        current_time = datetime.now()

        with self.kg.lock:
            for node_id, node_data in self.kg.graph.nodes(data=True):
                if node_data.get('kind') != 'deployment':
                    continue

                namespace = node_data.get('namespace', 'default')
                name = node_data.get('name', '')

                # 应用命名空间过滤
                if filter_namespace and namespace != filter_namespace:
                    continue

                if not name:
                    continue

                metrics = node_data.get('metrics', {})
                deployment_info = {
                    'resource_id': node_id,
                    'namespace': namespace,
                    'name': name,
                    'labels': node_data.get('labels', {}),
                    'created_at': node_data.get('created_at'),
                    'last_updated': node_data.get('last_updated')
                }

                if metrics:
                    # 检查指标是否过期（超过2周）
                    last_metrics_update = metrics.get('metrics_last_updated')
                    if last_metrics_update:
                        try:
                            if isinstance(last_metrics_update, str):
                                update_time = datetime.fromisoformat(last_metrics_update.replace('Z', '+00:00'))
                            else:
                                update_time = datetime.fromtimestamp(last_metrics_update)

                            days_old = (current_time - update_time).days

                            deployment_info.update({
                                'has_metrics': True,
                                'cpu_utilization': metrics.get('cpu_utilization_avg_14d', 0),
                                'memory_utilization': metrics.get('memory_utilization_avg_14d', 0),
                                'metrics_age_days': days_old,
                                'data_source': metrics.get('data_source', 'unknown'),
                                'has_prometheus_data': metrics.get('has_prometheus_data', True)
                            })

                            if days_old > 14:
                                outdated_deployments.append(deployment_info)
                            else:
                                deployments_with_metrics.append(deployment_info)

                        except Exception as e:
                            logger.warning(f"解析指标时间失败 {node_id}: {e}")
                            deployment_info['has_metrics'] = True
                            deployment_info['metrics_age_days'] = -1
                            deployments_with_metrics.append(deployment_info)
                    else:
                        deployment_info['has_metrics'] = True
                        deployment_info['metrics_age_days'] = -1
                        deployments_with_metrics.append(deployment_info)
                else:
                    deployment_info['has_metrics'] = False
                    deployments_without_metrics.append(deployment_info)

        return {
            'with_metrics': deployments_with_metrics,
            'without_metrics': deployments_without_metrics,
            'outdated_metrics': outdated_deployments,
            'total_deployments': len(deployments_with_metrics) + len(deployments_without_metrics) + len(outdated_deployments)
        }

    def _get_aggregator_statistics(self) -> Dict[str, Any]:
        """获取聚合器统计信息"""
        try:
            aggregator = get_metrics_aggregator()
            if aggregator:
                return aggregator.get_statistics()
            else:
                return {
                    "is_running": False,
                    "stats": {},
                    "config": {}
                }
        except Exception as e:
            logger.warning(f"获取聚合器统计失败: {e}")
            return {
                "is_running": False,
                "error": str(e),
                "stats": {},
                "config": {}
            }

    def _generate_coverage_report(self,
                                deployment_info: Dict[str, Any],
                                aggregator_stats: Dict[str, Any],
                                include_details: bool,
                                show_failed_only: bool) -> str:
        """生成覆盖报告"""

        with_metrics = deployment_info['with_metrics']
        without_metrics = deployment_info['without_metrics']
        outdated_metrics = deployment_info['outdated_metrics']
        total = deployment_info['total_deployments']

        # 计算覆盖率
        coverage_rate = (len(with_metrics) / total * 100) if total > 0 else 0

        report = f"""
📊 **K8s Deployment指标覆盖报告**

## 📈 覆盖统计
- **总Deployment数**: {total}
- **有指标数据**: {len(with_metrics)} ({len(with_metrics)/total*100:.1f}%)
- **缺少指标**: {len(without_metrics)} ({len(without_metrics)/total*100:.1f}%)
- **指标过期**: {len(outdated_metrics)} ({len(outdated_metrics)/total*100:.1f}%)
- **整体覆盖率**: {coverage_rate:.1f}%

## 🔄 聚合器状态
- **运行状态**: {'✅ 运行中' if aggregator_stats.get('is_running') else '❌ 未运行'}
"""

        # 添加聚合器统计
        stats = aggregator_stats.get('stats', {})
        if stats:
            report += f"""
- **已完成聚合**: {stats.get('aggregations_completed', 0)} 次
- **发现的Deployment**: {stats.get('deployments_discovered', 0)}
- **成功更新**: {stats.get('deployments_updated', 0)}
- **更新失败**: {stats.get('deployments_failed', 0)}
- **重试次数**: {stats.get('retry_attempts', 0)}
- **错误总数**: {stats.get('errors_count', 0)}
"""

            # 显示最后聚合时间
            last_aggregation = stats.get('last_aggregation_time', 0)
            if last_aggregation:
                last_time = datetime.fromtimestamp(last_aggregation)
                report += f"- **最后聚合**: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # 显示配置信息
        config = aggregator_stats.get('config', {})
        if config:
            interval_hours = config.get('aggregation_interval', 0) / 3600
            report += f"""
## ⚙️ 配置信息
- **聚合间隔**: {interval_hours:.1f} 小时
- **分析天数**: {config.get('analysis_days', 0)} 天
- **CPU阈值**: {config.get('cpu_threshold', 0)}%
- **内存阈值**: {config.get('memory_threshold', 0)}%
"""

        # 显示失败的deployment
        failed_deployments = stats.get('failed_deployments', [])
        if failed_deployments:
            report += f"\n## ❌ 最近失败的Deployment\n"
            for failure in failed_deployments[-5:]:  # 显示最近5个失败
                report += f"- **{failure.get('app_key', 'unknown')}**: {failure.get('error', 'unknown error')}\n"

        # 详细信息
        if include_details and not show_failed_only:
            if without_metrics:
                report += f"\n## 🔍 缺少指标的Deployment\n"
                for dep in without_metrics[:10]:  # 最多显示10个
                    report += f"- `{dep['namespace']}/{dep['name']}`\n"
                if len(without_metrics) > 10:
                    report += f"- ... 还有 {len(without_metrics) - 10} 个\n"

            if outdated_metrics:
                report += f"\n## ⏰ 指标过期的Deployment\n"
                for dep in outdated_metrics[:10]:
                    age = dep.get('metrics_age_days', 0)
                    report += f"- `{dep['namespace']}/{dep['name']}` (过期 {age} 天)\n"
                if len(outdated_metrics) > 10:
                    report += f"- ... 还有 {len(outdated_metrics) - 10} 个\n"

        elif show_failed_only:
            # 只显示有问题的deployment
            problem_deployments = without_metrics + outdated_metrics
            if problem_deployments:
                report += f"\n## ⚠️ 有问题的Deployment ({len(problem_deployments)}个)\n"
                for dep in problem_deployments:
                    status = "缺少指标" if not dep.get('has_metrics') else f"指标过期({dep.get('metrics_age_days', 0)}天)"
                    report += f"- `{dep['namespace']}/{dep['name']}` - {status}\n"

        # 健康度评估
        if coverage_rate >= 90:
            health_status = "🟢 优秀"
        elif coverage_rate >= 70:
            health_status = "🟡 良好"
        elif coverage_rate >= 50:
            health_status = "🟠 一般"
        else:
            health_status = "🔴 需要关注"

        report += f"\n## 📋 健康度评估\n**指标覆盖健康度**: {health_status} ({coverage_rate:.1f}%)\n"

        # 建议
        if coverage_rate < 90:
            report += f"\n## 💡 改进建议\n"
            if without_metrics:
                report += "- 检查缺少指标的deployment是否有对应的Prometheus数据\n"
            if outdated_metrics:
                report += "- 考虑手动触发指标聚合更新过期数据\n"
            if stats.get('deployments_failed', 0) > 0:
                report += "- 检查失败的deployment错误原因并修复\n"

        report += f"\n⏰ **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return report
