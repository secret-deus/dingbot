"""
K8s资源分析报告工具

查询知识图谱中的资源数据，生成异常资源分析报告，
包含正常资源摘要和异常资源的详细信息及修改建议。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..core.k8s_graph import get_shared_knowledge_graph
from ..core.http_api_client import HttpApiClient
from ..config import get_config
from loguru import logger

@dataclass
class ResourceAnalysisResult:
    """资源分析结果"""
    total_resources: int
    normal_resources: int
    abnormal_resources: int
    normal_summary: str
    abnormal_details: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_time: str

class K8sResourceAnalysisReportTool:
    """K8s资源分析报告工具"""
    
    def __init__(self, kg, config):
        self.kg = kg
        self.config = config
        # 构建后端API URL
        backend_url = getattr(config, 'backend_api_url', 'http://localhost:8000')
        self.http_client = HttpApiClient(backend_url) if getattr(config, 'enable_backend_notifications', False) else None
        
        # 阈值配置
        self.cpu_threshold = getattr(config, 'cpu_alert_threshold', 0.8)  # 80%
        self.memory_threshold = getattr(config, 'memory_alert_threshold', 0.7)  # 70%
        
    async def execute(self, 
                     namespace_filter: str = "",
                     include_recommendations: bool = True,
                     send_dingtalk_notification: bool = True) -> Dict[str, Any]:
        """
        执行资源分析报告
        
        Args:
            namespace_filter: 命名空间过滤器
            include_recommendations: 是否包含LLM生成的建议
            send_dingtalk_notification: 是否发送钉钉通知
            
        Returns:
            分析报告结果
        """
        try:
            logger.info(f"🔍 开始资源分析报告生成...")
            
            # 1. 从知识图谱获取所有deployment资源
            deployments = await self._get_deployments_from_kg(namespace_filter)
            logger.info(f"📊 发现 {len(deployments)} 个deployment资源")
            
            # 2. 分析资源状态
            analysis_result = await self._analyze_resources(deployments)
            
            # 3. 生成简单建议（如果启用）
            if include_recommendations and analysis_result.abnormal_resources > 0:
                recommendations = self._generate_simple_recommendations(analysis_result.abnormal_details)
                analysis_result.recommendations = recommendations
            
            # 4. 发送钉钉通知（如果启用且有异常资源）
            if (send_dingtalk_notification and 
                analysis_result.abnormal_resources > 0 and 
                self.http_client):
                await self._send_dingtalk_notification(analysis_result)
            
            # 5. 生成最终报告
            report = self._generate_report(analysis_result)
            
            logger.info(f"✅ 资源分析报告生成完成: {analysis_result.abnormal_resources}/{analysis_result.total_resources} 个异常资源")
            
            return {
                "success": True,
                "report": report,
                "statistics": {
                    "total_resources": analysis_result.total_resources,
                    "normal_resources": analysis_result.normal_resources,
                    "abnormal_resources": analysis_result.abnormal_resources,
                    "analysis_time": analysis_result.analysis_time
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 资源分析报告生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "report": f"资源分析报告生成失败: {e}"
            }
    
    async def _get_deployments_from_kg(self, namespace_filter: str) -> List[Dict[str, Any]]:
        """从知识图谱获取deployment资源"""
        deployments = []
        
        try:
            with self.kg.lock:
                for node_id, node_data in self.kg.graph.nodes(data=True):
                    if node_data.get('kind') == 'deployment':
                        namespace = node_data.get('namespace', 'default')
                        
                        # 应用命名空间过滤
                        if namespace_filter and namespace != namespace_filter:
                            continue
                            
                        # 获取资源指标
                        metrics = node_data.get('metrics', {})
                        
                        deployment_info = {
                            'resource_id': node_id,
                            'name': node_data.get('name', ''),
                            'namespace': namespace,
                            'labels': node_data.get('labels', {}),
                            'cpu_utilization': metrics.get('cpu_utilization_avg_14d', 0.0),
                            'memory_utilization': metrics.get('memory_utilization_avg_14d', 0.0),
                            'cpu_requests': metrics.get('cpu_requests', 0.0),
                            'memory_requests': metrics.get('memory_requests', 0.0),
                            'last_updated': metrics.get('last_updated', ''),
                            'has_prometheus_data': metrics.get('has_prometheus_data', False)
                        }
                        
                        deployments.append(deployment_info)
            
            return deployments
            
        except Exception as e:
            logger.error(f"从知识图谱获取deployment失败: {e}")
            return []
    
    async def _analyze_resources(self, deployments: List[Dict[str, Any]]) -> ResourceAnalysisResult:
        """分析资源状态"""
        total_resources = len(deployments)
        normal_resources = 0
        abnormal_resources = 0
        abnormal_details = []
        
        # 统计正常和异常资源
        for deployment in deployments:
            cpu_util = deployment['cpu_utilization'] / 100.0  # 转换为小数
            memory_util = deployment['memory_utilization'] / 100.0
            
            is_cpu_abnormal = cpu_util > self.cpu_threshold
            is_memory_abnormal = memory_util > self.memory_threshold
            
            if is_cpu_abnormal or is_memory_abnormal:
                abnormal_resources += 1
                
                # 构建异常详情
                issues = []
                if is_cpu_abnormal:
                    issues.append(f"CPU利用率过高: {cpu_util:.1%} > {self.cpu_threshold:.1%}")
                if is_memory_abnormal:
                    issues.append(f"内存利用率过高: {memory_util:.1%} > {self.memory_threshold:.1%}")
                
                abnormal_details.append({
                    'name': deployment['name'],
                    'namespace': deployment['namespace'],
                    'resource_id': deployment['resource_id'],
                    'cpu_utilization': f"{cpu_util:.1%}",
                    'memory_utilization': f"{memory_util:.1%}",
                    'cpu_requests': deployment['cpu_requests'],
                    'memory_requests': deployment['memory_requests'],
                    'issues': issues,
                    'has_prometheus_data': deployment['has_prometheus_data']
                })
            else:
                normal_resources += 1
        
        # 生成正常资源摘要
        if normal_resources > 0:
            avg_cpu = sum(d['cpu_utilization'] for d in deployments if d['cpu_utilization'] / 100.0 <= self.cpu_threshold) / max(normal_resources, 1)
            avg_memory = sum(d['memory_utilization'] for d in deployments if d['memory_utilization'] / 100.0 <= self.memory_threshold) / max(normal_resources, 1)
            normal_summary = f"正常资源 {normal_resources} 个，平均CPU利用率 {avg_cpu:.1f}%，平均内存利用率 {avg_memory:.1f}%"
        else:
            normal_summary = "无正常资源"
        
        return ResourceAnalysisResult(
            total_resources=total_resources,
            normal_resources=normal_resources,
            abnormal_resources=abnormal_resources,
            normal_summary=normal_summary,
            abnormal_details=abnormal_details,
            recommendations=[],
            analysis_time=datetime.now().isoformat()
        )
    
    def _generate_simple_recommendations(self, abnormal_details: List[Dict[str, Any]]) -> List[str]:
        """生成简单的优化建议"""
        try:
            if not abnormal_details:
                return []
            
            recommendations = []
            
            for detail in abnormal_details:
                app_name = detail['name']
                namespace = detail['namespace']
                issues = detail['issues']
                
                for issue in issues:
                    if "CPU利用率过高" in issue:
                        recommendations.append(
                            f"🔧 {namespace}/{app_name}: 建议增加CPU请求量或优化应用CPU使用"
                        )
                    elif "内存利用率过高" in issue:
                        recommendations.append(
                            f"💾 {namespace}/{app_name}: 建议增加内存请求量或检查内存泄漏"
                        )
            
            # 添加通用建议
            if len(abnormal_details) > 3:
                recommendations.append("📊 建议定期监控资源使用情况，设置合适的资源限制")
                recommendations.append("⚡ 考虑使用HPA（水平Pod自动扩缩）来应对负载变化")
            
            return recommendations[:10]  # 最多返回10条建议
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return [f"建议生成失败: {e}"]
    

    
    async def _send_dingtalk_notification(self, analysis_result: ResourceAnalysisResult):
        """发送钉钉通知"""
        try:
            if not self.http_client:
                logger.warning("HTTP客户端未配置，跳过钉钉通知")
                return
            
            # 构建告警数据
            alert_data = {
                "alert_type": "resource_analysis",
                "resource_id": "cluster_wide",
                "severity": "high" if analysis_result.abnormal_resources > 5 else "medium",
                "summary": f"发现 {analysis_result.abnormal_resources} 个异常资源需要关注",
                "details": {
                    "total_resources": analysis_result.total_resources,
                    "abnormal_resources": analysis_result.abnormal_resources,
                    "normal_summary": analysis_result.normal_summary,
                    "abnormal_details": analysis_result.abnormal_details[:5],  # 只发送前5个
                    "recommendations": analysis_result.recommendations[:3],  # 只发送前3条建议
                    "analysis_time": analysis_result.analysis_time
                }
            }
            
            # 发送到后端
            await self.http_client.post_alert(alert_data)
            logger.info("✅ 钉钉通知发送成功")
            
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
    
    def _generate_report(self, analysis_result: ResourceAnalysisResult) -> str:
        """生成最终报告"""
        report_lines = [
            "# 📊 K8s资源分析报告",
            f"**分析时间**: {analysis_result.analysis_time}",
            "",
            "## 📈 资源统计",
            f"- **总资源数**: {analysis_result.total_resources}",
            f"- **正常资源**: {analysis_result.normal_resources}",
            f"- **异常资源**: {analysis_result.abnormal_resources}",
            "",
            "## ✅ 正常资源摘要",
            analysis_result.normal_summary,
            ""
        ]
        
        if analysis_result.abnormal_resources > 0:
            report_lines.extend([
                "## ⚠️ 异常资源详情",
                ""
            ])
            
            for i, detail in enumerate(analysis_result.abnormal_details, 1):
                report_lines.extend([
                    f"### {i}. {detail['name']} ({detail['namespace']})",
                    f"- **CPU利用率**: {detail['cpu_utilization']}",
                    f"- **内存利用率**: {detail['memory_utilization']}",
                    f"- **问题**: {', '.join(detail['issues'])}",
                    f"- **数据来源**: {'Prometheus' if detail['has_prometheus_data'] else '默认值'}",
                    ""
                ])
            
            if analysis_result.recommendations:
                report_lines.extend([
                    "## 💡 优化建议",
                    ""
                ])
                
                for i, rec in enumerate(analysis_result.recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
                
                report_lines.append("")
        else:
            report_lines.extend([
                "## 🎉 所有资源运行正常",
                "未发现需要关注的异常资源。",
                ""
            ])
        
        return "\n".join(report_lines)


# MCP工具接口
async def k8s_resource_analysis_report(
    kg,
    config,
    namespace_filter: str = "",
    include_recommendations: bool = True,
    send_dingtalk_notification: bool = True
) -> Dict[str, Any]:
    """
    K8s资源分析报告工具
    
    Args:
        kg: K8s知识图谱实例
        config: 配置对象
        namespace_filter: 命名空间过滤器，为空表示所有命名空间
        include_recommendations: 是否包含LLM生成的优化建议
        send_dingtalk_notification: 是否发送钉钉通知
        
    Returns:
        包含分析报告的字典
    """
    tool = K8sResourceAnalysisReportTool(kg, config)
    return await tool.execute(
        namespace_filter=namespace_filter,
        include_recommendations=include_recommendations,
        send_dingtalk_notification=send_dingtalk_notification
    )
