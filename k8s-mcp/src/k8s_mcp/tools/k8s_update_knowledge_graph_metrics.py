"""
K8s知识图谱指标更新工具

使用Prometheus工具批量获取应用资源利用率，并更新到知识图谱中
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPCallToolResult, MCPToolSchema
from .k8s_prometheus_app_metrics import K8sPrometheusAppMetricsTool
from ..core.k8s_graph import get_shared_knowledge_graph


class K8sUpdateKnowledgeGraphMetricsTool(MCPToolBase):
    """K8s知识图谱指标更新工具
    
    功能：
    - 从知识图谱获取所有应用列表
    - 使用Prometheus工具批量获取资源利用率
    - 更新知识图谱中的指标数据
    - 提供批量更新进度和统计信息
    """
    
    def __init__(self):
        super().__init__(
            name="k8s-update-knowledge-graph-metrics",
            description="批量更新知识图谱中应用的资源利用率指标"
        )
        self.input_schema = {
            "type": "object",
            "properties": {
                "namespace_filter": {
                    "type": "string",
                    "description": "命名空间过滤器（正则表达式），为空则处理所有命名空间",
                    "default": ""
                },
                "app_name_filter": {
                    "type": "string", 
                    "description": "应用名过滤器（正则表达式），为空则处理所有应用",
                    "default": ""
                },
                "days": {
                    "type": "integer",
                    "description": "分析天数",
                    "default": 14,
                    "minimum": 1,
                    "maximum": 30
                },
                "max_concurrent": {
                    "type": "integer",
                    "description": "最大并发查询数",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "time_period": {
                    "type": "string",
                    "description": "时间周期模式：14d(14天平均) 或 1d(1天近期)",
                    "default": "14d",
                    "enum": ["14d", "1d"]
                }
            },
            "required": []
        }
        self.kg = get_shared_knowledge_graph()
        self.prometheus_tool = K8sPrometheusAppMetricsTool()
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行知识图谱指标更新"""
        try:
            # 解析参数
            namespace_filter = arguments.get("namespace_filter", "")
            app_name_filter = arguments.get("app_name_filter", "")
            days = arguments.get("days", 14)
            max_concurrent = arguments.get("max_concurrent", 5)
            time_period = arguments.get("time_period", "14d")
            
            # 根据时间周期调整参数
            is_day_mode = time_period == "1d"
            if is_day_mode and days > 1:
                days = 1  # 1天模式确保只查询1天数据
            
            logger.info(f"开始批量更新知识图谱指标: namespace={namespace_filter or 'all'}, app={app_name_filter or 'all'}, days={days}, mode={time_period}")
            
            # 获取需要更新的应用列表
            apps_to_update = await self._get_apps_from_knowledge_graph(namespace_filter, app_name_filter)
            
            if not apps_to_update:
                return MCPCallToolResult(
                    content=[{"type": "text", "text": "❌ 未找到需要更新的应用"}],
                    is_error=False
                )
            
            logger.info(f"找到 {len(apps_to_update)} 个应用需要更新指标")
            
            # 批量获取指标并更新
            results = await self._batch_update_metrics(apps_to_update, days, max_concurrent, time_period)
            
            # 生成报告
            report = self._generate_update_report(results)
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": report}],
                is_error=False
            )
            
        except Exception as e:
            logger.error(f"知识图谱指标更新失败: {e}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"❌ 知识图谱指标更新失败: {str(e)}"}],
                is_error=True
            )
    
    async def _get_apps_from_knowledge_graph(self, namespace_filter: str, app_name_filter: str) -> List[Dict]:
        """从知识图谱获取应用列表"""
        import re
        
        apps = []
        
        with self.kg.lock:
            for node_id, node_data in self.kg.graph.nodes(data=True):
                try:
                    # 只处理deployment类型的资源
                    if node_data.get('kind') != 'deployment':
                        continue
                    
                    namespace = node_data.get('namespace', '')
                    name = node_data.get('name', '')
                    
                    # 应用过滤器
                    if namespace_filter:
                        if not re.search(namespace_filter, namespace, re.IGNORECASE):
                            continue
                    
                    if app_name_filter:
                        if not re.search(app_name_filter, name, re.IGNORECASE):
                            continue
                    
                    apps.append({
                        'resource_id': node_id,
                        'namespace': namespace,
                        'name': name,
                        'labels': node_data.get('labels', {}),
                        'current_metrics': node_data.get('metrics', {})
                    })
                    
                except Exception as e:
                    logger.warning(f"处理节点 {node_id} 时出错: {e}")
                    continue
        
        return apps
    
    async def _batch_update_metrics(self, apps: List[Dict], days: int, max_concurrent: int, time_period: str = "14d") -> List[Dict]:
        """批量更新指标"""
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def update_single_app(app: Dict) -> Dict:
            async with semaphore:
                return await self._update_single_app_metrics(app, days, time_period)
        
        # 并发执行更新
        tasks = [update_single_app(app) for app in apps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'app': apps[i],
                    'success': False,
                    'error': str(result),
                    'metrics': None
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _update_single_app_metrics(self, app: Dict, days: int, time_period: str = "14d") -> Dict:
        """更新单个应用的指标"""
        try:
            namespace = app['namespace']
            name = app['name']
            resource_id = app['resource_id']
            
            logger.debug(f"正在更新应用指标: {namespace}/{name} (模式: {time_period})")
            
            # 根据时间周期设置不同的查询参数
            is_day_mode = time_period == "1d"
            step = "10m" if is_day_mode else "1h"  # 1天模式使用10分钟步长，14天模式使用1小时步长
            
            # 使用Prometheus工具获取指标
            prometheus_result = await self.prometheus_tool.execute({
                'app_name': name,
                'namespace': namespace,
                'days': days,
                'step': step,
                'time_period': time_period  # 传递时间周期参数
            })
            
            if prometheus_result.is_error:
                return {
                    'app': app,
                    'success': False,
                    'error': f"Prometheus查询失败: {prometheus_result.content}",
                    'metrics': None
                }
            
            # 解析Prometheus结果
            import json
            prometheus_data = json.loads(prometheus_result.content[0]['text'])
            metrics = prometheus_data.get('metrics', {})

            # 统一将利用率转换为百分比数值（0-100）
            def _to_percent(v: Any) -> float:
                try:
                    if v is None:
                        return 0.0
                    # 字符串百分比形式，如 "106.85%"
                    if isinstance(v, str) and v.endswith('%'):
                        return round(float(v.rstrip('%')), 2)
                    # 数值：<=1 视为比例，乘以100；>1 视为百分比
                    if isinstance(v, (int, float)):
                        return round((float(v) * 100.0) if float(v) <= 1.0 else float(v), 2)
                    return 0.0
                except Exception:
                    return 0.0

            cpu_util_percent = _to_percent(metrics.get('cpu_utilization_avg', 0.0))
            mem_util_percent = _to_percent(metrics.get('memory_utilization_avg', 0.0))
            
            # 构建知识图谱指标数据
            kg_metrics = {
                "cpu_utilization_avg_14d": cpu_util_percent,
                "memory_utilization_avg_14d": mem_util_percent,
                "cpu_requests": metrics.get('cpu_requests_avg', 0.0),
                "memory_requests": metrics.get('memory_requests_avg', 0.0),
                "metrics_last_updated": datetime.now().isoformat(),
                "needs_optimization": {
                    # 阈值使用百分比
                    "cpu": cpu_util_percent < 60.0,
                    "memory": mem_util_percent < 60.0
                },
                # 标记数据来源与可用性，便于资源分析工具识别为“有监控数据”
                "data_source": "prometheus",
                "has_prometheus_data": True,
                "data_quality": prometheus_data.get('data_quality', {}),
                "query_time_range": prometheus_data.get('query_time_range', {})
            }
            
            # 更新知识图谱
            success = self.kg.update_resource_metrics(resource_id, kg_metrics)
            
            if not success:
                return {
                    'app': app,
                    'success': False,
                    'error': "知识图谱更新失败",
                    'metrics': kg_metrics
                }
            
            logger.debug(f"成功更新应用指标: {namespace}/{name}")
            
            return {
                'app': app,
                'success': True,
                'error': None,
                'metrics': kg_metrics
            }
            
        except Exception as e:
            logger.error(f"更新应用 {app.get('namespace', '')}/{app.get('name', '')} 指标失败: {e}")
            return {
                'app': app,
                'success': False,
                'error': str(e),
                'metrics': None
            }
    
    def _generate_update_report(self, results: List[Dict]) -> str:
        """生成更新报告"""
        total_apps = len(results)
        successful_updates = sum(1 for r in results if r['success'])
        failed_updates = total_apps - successful_updates
        
        report = f"""
🔄 **知识图谱指标更新完成**

📊 **更新统计**:
- 总应用数: {total_apps}
- 成功更新: {successful_updates}
- 更新失败: {failed_updates}
- 成功率: {(successful_updates/total_apps*100):.1f}%

"""
        
        if successful_updates > 0:
            report += "✅ **成功更新的应用**:\n"
            for result in results:
                if result['success']:
                    app = result['app']
                    metrics = result['metrics']
                    report += f"- {app['namespace']}/{app['name']}: "
                    report += f"CPU={metrics['cpu_utilization_avg_14d']:.1f}%, "
                    report += f"内存={metrics['memory_utilization_avg_14d']:.1f}%\n"
        
        if failed_updates > 0:
            report += "\n❌ **更新失败的应用**:\n"
            for result in results:
                if not result['success']:
                    app = result['app']
                    report += f"- {app['namespace']}/{app['name']}: {result['error']}\n"
        
        report += f"\n⏰ **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report
