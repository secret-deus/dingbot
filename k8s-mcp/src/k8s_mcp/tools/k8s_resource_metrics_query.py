"""
K8s资源指标查询工具

直接从知识图谱查询预计算的14天CPU/内存使用率指标，
提供高效的资源利用率分析和优化建议。
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.tool_registry import MCPToolBase
from ..core.k8s_graph import get_shared_knowledge_graph
from ..config import get_config


class K8sResourceMetricsQueryTool(MCPToolBase):
    """
    K8s资源指标查询工具
    
    功能：
    - 从知识图谱查询预计算的14天CPU/内存平均使用率
    - 识别资源利用率低于阈值的应用
    - 提供快速的资源优化建议
    - 支持按命名空间、应用名称过滤
    """

    def __init__(self):
        """初始化资源指标查询工具"""
        super().__init__(
            name="k8s-resource-metrics-query",
            description="从知识图谱查询K8s资源的14天平均CPU/内存使用率指标，提供快速的资源优化分析"
        )
        
        self.config = get_config()
        self.kg = get_shared_knowledge_graph()
        
        logger.info("K8s资源指标查询工具已初始化")

    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "namespace_filter": {
                        "type": "string",
                        "description": "命名空间过滤器，支持正则表达式，例如: test|prod"
                    },
                    "app_name_filter": {
                        "type": "string",
                        "description": "应用名称过滤器，支持正则表达式"
                    },
                    "cpu_threshold": {
                        "type": "number",
                        "description": "CPU利用率阈值(百分比)，低于此值的应用将被标记，默认60%",
                        "default": 60.0,
                        "minimum": 10.0,
                        "maximum": 95.0
                    },
                    "memory_threshold": {
                        "type": "number",
                        "description": "内存利用率阈值(百分比)，低于此值的应用将被标记，默认60%",
                        "default": 60.0,
                        "minimum": 10.0,
                        "maximum": 95.0
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "排序方式",
                        "enum": ["cpu_utilization", "memory_utilization", "overall_utilization", "app_name"],
                        "default": "overall_utilization"
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "排序顺序",
                        "enum": ["asc", "desc"],
                        "default": "asc"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制，默认50",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    },
                    "include_optimization_only": {
                        "type": "boolean",
                        "description": "是否只返回需要优化的应用",
                        "default": False
                    },
                    "metrics_freshness_hours": {
                        "type": "integer",
                        "description": "指标数据新鲜度要求（小时），默认24小时",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168
                    }
                },
                "required": []
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行资源指标查询"""
        try:
            # 参数提取
            namespace_filter = arguments.get("namespace_filter")
            app_name_filter = arguments.get("app_name_filter")
            cpu_threshold = arguments.get("cpu_threshold", 60.0)
            memory_threshold = arguments.get("memory_threshold", 60.0)
            sort_by = arguments.get("sort_by", "overall_utilization")
            sort_order = arguments.get("sort_order", "asc")
            limit = arguments.get("limit", 50)
            include_optimization_only = arguments.get("include_optimization_only", False)
            metrics_freshness_hours = arguments.get("metrics_freshness_hours", 24)
            
            logger.info(f"开始查询资源指标，CPU阈值: {cpu_threshold}%, 内存阈值: {memory_threshold}%")
            
            # 从知识图谱获取资源数据
            resources_data = await self._query_resources_from_kg(
                namespace_filter, app_name_filter, metrics_freshness_hours
            )
            
            if not resources_data:
                return MCPCallToolResult.success({
                    "message": "未找到符合条件的资源或指标数据",
                    "summary": {
                        "total_resources": 0,
                        "resources_with_metrics": 0,
                        "low_cpu_utilization": 0,
                        "low_memory_utilization": 0,
                        "both_low_utilization": 0
                    },
                    "resources": [],
                    "recommendations": []
                })
            
            # 分析资源指标
            analysis_result = await self._analyze_resources_metrics(
                resources_data, cpu_threshold, memory_threshold, 
                sort_by, sort_order, limit, include_optimization_only
            )
            
            return MCPCallToolResult.success(analysis_result)
            
        except Exception as e:
            logger.error(f"资源指标查询失败: {e}")
            return MCPCallToolResult.error(f"查询失败: {str(e)}")

    async def _query_resources_from_kg(
        self, 
        namespace_filter: Optional[str], 
        app_name_filter: Optional[str],
        metrics_freshness_hours: int
    ) -> List[Dict]:
        """从知识图谱查询资源数据"""
        import re
        
        resources_with_metrics = []
        cutoff_time = datetime.now() - timedelta(hours=metrics_freshness_hours)
        
        # 获取图统计信息
        stats = self.kg.get_statistics()
        logger.info(f"知识图谱状态: {stats['nodes_total']} 个节点, {stats['edges_total']} 条边")
        
        # 遍历所有节点，查找有指标数据的资源
        with self.kg.lock:
            for node_id, node_data in self.kg.graph.nodes(data=True):
                try:
                    # 检查是否有指标数据
                    metrics = node_data.get('metrics', {})
                    if not metrics or 'cpu_utilization_avg_14d' not in metrics:
                        continue
                    
                    # 检查指标数据新鲜度
                    metrics_last_updated = metrics.get('metrics_last_updated')
                    if metrics_last_updated:
                        try:
                            last_updated = datetime.fromisoformat(metrics_last_updated.replace('Z', '+00:00'))
                            if last_updated < cutoff_time:
                                continue
                        except (ValueError, AttributeError):
                            # 如果时间格式有问题，跳过新鲜度检查
                            pass
                    
                    # 应用过滤器
                    namespace = node_data.get('namespace', '')
                    name = node_data.get('name', '')
                    
                    if namespace_filter:
                        if not re.search(namespace_filter, namespace, re.IGNORECASE):
                            continue
                    
                    if app_name_filter:
                        if not re.search(app_name_filter, name, re.IGNORECASE):
                            continue
                    
                    # 构建资源信息
                    resource_info = {
                        "resource_id": node_id,
                        "kind": node_data.get('kind', 'unknown'),
                        "namespace": namespace,
                        "name": name,
                        "labels": node_data.get('labels', {}),
                        "metrics": metrics,
                        "last_updated": node_data.get('last_updated', 0)
                    }
                    
                    resources_with_metrics.append(resource_info)
                    
                except Exception as e:
                    logger.warning(f"处理节点 {node_id} 时出错: {e}")
                    continue
        
        logger.info(f"从知识图谱查询到 {len(resources_with_metrics)} 个有指标数据的资源")
        return resources_with_metrics

    async def _analyze_resources_metrics(
        self,
        resources_data: List[Dict],
        cpu_threshold: float,
        memory_threshold: float,
        sort_by: str,
        sort_order: str,
        limit: int,
        include_optimization_only: bool
    ) -> Dict[str, Any]:
        """分析资源指标数据"""
        
        analyzed_resources = []
        summary = {
            "total_resources": len(resources_data),
            "resources_with_metrics": 0,
            "low_cpu_utilization": 0,
            "low_memory_utilization": 0,
            "both_low_utilization": 0,
            "query_time": datetime.now().isoformat(),
            "thresholds": {
                "cpu_threshold_percent": cpu_threshold,
                "memory_threshold_percent": memory_threshold
            }
        }
        
        for resource in resources_data:
            try:
                metrics = resource['metrics']
                
                # 提取指标值
                cpu_utilization = metrics.get('cpu_utilization_avg_14d', 0.0)
                memory_utilization = metrics.get('memory_utilization_avg_14d', 0.0)
                cpu_requests = metrics.get('cpu_requests', 0.0)
                memory_requests = metrics.get('memory_requests', 0.0)
                
                # 判断是否需要优化
                needs_cpu_optimization = cpu_utilization < cpu_threshold
                needs_memory_optimization = memory_utilization < memory_threshold
                needs_optimization = needs_cpu_optimization or needs_memory_optimization
                
                # 如果只返回需要优化的应用，跳过不需要优化的
                if include_optimization_only and not needs_optimization:
                    continue
                
                # 计算整体利用率
                overall_utilization = (cpu_utilization + memory_utilization) / 2
                
                # 构建分析结果
                analyzed_resource = {
                    "resource_id": resource['resource_id'],
                    "kind": resource['kind'],
                    "namespace": resource['namespace'],
                    "name": resource['name'],
                    "labels": resource['labels'],
                    "cpu_utilization_avg_14d": round(cpu_utilization, 2),
                    "memory_utilization_avg_14d": round(memory_utilization, 2),
                    "overall_utilization_avg": round(overall_utilization, 2),
                    "cpu_requests": round(cpu_requests, 3),
                    "memory_requests": round(memory_requests, 2),
                    "needs_optimization": {
                        "cpu": needs_cpu_optimization,
                        "memory": needs_memory_optimization,
                        "overall": needs_optimization
                    },
                    "optimization_potential": {
                        "cpu_reduction_percent": max(0, cpu_threshold - cpu_utilization) if needs_cpu_optimization else 0,
                        "memory_reduction_percent": max(0, memory_threshold - memory_utilization) if needs_memory_optimization else 0
                    },
                    "metrics_last_updated": metrics.get('metrics_last_updated', 'unknown')
                }
                
                analyzed_resources.append(analyzed_resource)
                
                # 更新统计信息
                summary["resources_with_metrics"] += 1
                if needs_cpu_optimization:
                    summary["low_cpu_utilization"] += 1
                if needs_memory_optimization:
                    summary["low_memory_utilization"] += 1
                if needs_cpu_optimization and needs_memory_optimization:
                    summary["both_low_utilization"] += 1
                    
            except Exception as e:
                logger.warning(f"分析资源 {resource.get('resource_id', 'unknown')} 时出错: {e}")
                continue
        
        # 排序
        analyzed_resources = self._sort_resources(analyzed_resources, sort_by, sort_order)
        
        # 限制结果数量
        if limit > 0:
            analyzed_resources = analyzed_resources[:limit]
        
        # 生成优化建议
        recommendations = self._generate_optimization_recommendations(
            analyzed_resources, cpu_threshold, memory_threshold
        )
        
        return {
            "summary": summary,
            "resources": analyzed_resources,
            "recommendations": recommendations,
            "data_source": "knowledge_graph",
            "query_performance": {
                "total_nodes_scanned": summary["total_resources"],
                "results_returned": len(analyzed_resources),
                "data_freshness": "预计算的14天平均值"
            }
        }

    def _sort_resources(self, resources: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
        """对资源列表进行排序"""
        reverse = sort_order == "desc"
        
        if sort_by == "cpu_utilization":
            return sorted(resources, key=lambda x: x["cpu_utilization_avg_14d"], reverse=reverse)
        elif sort_by == "memory_utilization":
            return sorted(resources, key=lambda x: x["memory_utilization_avg_14d"], reverse=reverse)
        elif sort_by == "overall_utilization":
            return sorted(resources, key=lambda x: x["overall_utilization_avg"], reverse=reverse)
        elif sort_by == "app_name":
            return sorted(resources, key=lambda x: f"{x['namespace']}/{x['name']}", reverse=reverse)
        else:
            return resources

    def _generate_optimization_recommendations(
        self,
        resources: List[Dict],
        cpu_threshold: float,
        memory_threshold: float
    ) -> List[Dict[str, Any]]:
        """生成资源优化建议"""
        recommendations = []
        
        # 找出需要优化的应用
        apps_needing_optimization = [
            app for app in resources 
            if app["needs_optimization"]["overall"]
        ]
        
        if not apps_needing_optimization:
            recommendations.append({
                "type": "info",
                "title": "资源配置良好",
                "description": "所有查询到的应用的资源利用率都在合理范围内，无需优化。",
                "priority": "low"
            })
            return recommendations
        
        # CPU优化建议
        cpu_apps = [app for app in apps_needing_optimization if app["needs_optimization"]["cpu"]]
        if cpu_apps:
            total_cpu_waste = sum(
                app["cpu_requests"] * (app["optimization_potential"]["cpu_reduction_percent"] / 100)
                for app in cpu_apps if app["cpu_requests"] > 0
            )
            recommendations.append({
                "type": "cpu_optimization",
                "title": f"CPU资源优化建议 - 可节省约{total_cpu_waste:.2f}核",
                "description": f"发现{len(cpu_apps)}个应用的14天平均CPU利用率低于{cpu_threshold}%",
                "priority": "high" if len(cpu_apps) > 10 else "medium",
                "affected_count": len(cpu_apps),
                "potential_savings": f"{total_cpu_waste:.2f}核",
                "top_candidates": [
                    {
                        "name": f"{app['namespace']}/{app['name']}",
                        "current_utilization": f"{app['cpu_utilization_avg_14d']}%",
                        "current_request": f"{app['cpu_requests']}核",
                        "suggested_reduction": f"{app['optimization_potential']['cpu_reduction_percent']:.1f}%"
                    }
                    for app in sorted(cpu_apps, key=lambda x: x['optimization_potential']['cpu_reduction_percent'], reverse=True)[:5]
                ]
            })
        
        # 内存优化建议
        memory_apps = [app for app in apps_needing_optimization if app["needs_optimization"]["memory"]]
        if memory_apps:
            total_memory_waste = sum(
                app["memory_requests"] * (app["optimization_potential"]["memory_reduction_percent"] / 100)
                for app in memory_apps if app["memory_requests"] > 0
            )
            recommendations.append({
                "type": "memory_optimization",
                "title": f"内存资源优化建议 - 可节省约{total_memory_waste:.2f}GB",
                "description": f"发现{len(memory_apps)}个应用的14天平均内存利用率低于{memory_threshold}%",
                "priority": "high" if len(memory_apps) > 10 else "medium",
                "affected_count": len(memory_apps),
                "potential_savings": f"{total_memory_waste:.2f}GB",
                "top_candidates": [
                    {
                        "name": f"{app['namespace']}/{app['name']}",
                        "current_utilization": f"{app['memory_utilization_avg_14d']}%",
                        "current_request": f"{app['memory_requests']:.2f}GB",
                        "suggested_reduction": f"{app['optimization_potential']['memory_reduction_percent']:.1f}%"
                    }
                    for app in sorted(memory_apps, key=lambda x: x['optimization_potential']['memory_reduction_percent'], reverse=True)[:5]
                ]
            })
        
        # 综合优化建议
        both_apps = [app for app in apps_needing_optimization if 
                    app["needs_optimization"]["cpu"] and app["needs_optimization"]["memory"]]
        if both_apps:
            recommendations.append({
                "type": "comprehensive_optimization",
                "title": f"综合优化建议 - {len(both_apps)}个应用CPU和内存都可优化",
                "description": "这些应用的CPU和内存利用率都较低，建议优先优化",
                "priority": "high",
                "affected_count": len(both_apps),
                "applications": [
                    {
                        "name": f"{app['namespace']}/{app['name']}",
                        "cpu_utilization": f"{app['cpu_utilization_avg_14d']}%",
                        "memory_utilization": f"{app['memory_utilization_avg_14d']}%",
                        "overall_utilization": f"{app['overall_utilization_avg']}%"
                    }
                    for app in sorted(both_apps, key=lambda x: x['overall_utilization_avg'])[:10]
                ]
            })
        
        return recommendations
