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
    data_quality_issues_count: int = 0
    analysis_summary: str = ""

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
            
            # 3. 生成智能建议（如果启用）
            if include_recommendations and analysis_result.abnormal_resources > 0:
                recommendations = self._generate_smart_recommendations(analysis_result.abnormal_details)
                analysis_result.recommendations = recommendations
            
            # 4. 发送钉钉通知（如果启用且有异常资源）
            if (send_dingtalk_notification and 
                analysis_result.abnormal_resources > 0 and 
                self.http_client):
                await self._send_dingtalk_notification(analysis_result)
            
            # 5. 生成最终报告
            report = self._generate_report(analysis_result)
            
            logger.info(f"✅ 资源分析报告生成完成: {analysis_result.abnormal_resources}/{analysis_result.total_resources} 个真实异常资源")
            if hasattr(analysis_result, 'data_quality_issues_count') and analysis_result.data_quality_issues_count > 0:
                logger.info(f"📊 另发现 {analysis_result.data_quality_issues_count} 个资源存在数据质量问题")
            
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
        """分析资源状态 - 增强版异常检测算法"""
        total_resources = len(deployments)
        normal_resources = 0
        abnormal_resources = 0
        abnormal_details = []
        
        # 计算全局统计信息用于智能阈值调整
        if deployments:
            # 注意：数据已经是比例值，不需要除以100
            cpu_values = [d['cpu_utilization'] for d in deployments if d['cpu_utilization'] is not None]
            memory_values = [d['memory_utilization'] for d in deployments if d['memory_utilization'] is not None]
            
            cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
            memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
            
            # 计算标准差用于异常检测
            cpu_std = (sum((x - cpu_avg) ** 2 for x in cpu_values) / len(cpu_values)) ** 0.5 if cpu_values else 0
            memory_std = (sum((x - memory_avg) ** 2 for x in memory_values) / len(memory_values)) ** 0.5 if memory_values else 0
            
            logger.debug(f"全局统计: CPU平均={cpu_avg:.2%}, 标准差={cpu_std:.2%}, 内存平均={memory_avg:.2%}, 标准差={memory_std:.2%}")
        
        # 统计正常和异常资源
        for deployment in deployments:
            # 注意：从知识图谱获取的数据已经是比例值（如41.5427表示4154.27%），不需要再除以100
            cpu_util = deployment['cpu_utilization'] if deployment['cpu_utilization'] is not None else 0
            memory_util = deployment['memory_utilization'] if deployment['memory_utilization'] is not None else 0
            
            # 多层次异常检测
            issues = []
            severity_score = 0
            
            # 1. 基础阈值检测
            # 设置最小有效利用率阈值，避免将正常的低利用率误判为异常
            min_valid_utilization = 0.05  # 5%，低于此值认为是正常的低利用率
            low_memory_threshold = 0.30  # 30%，内存利用率低于此值认为是资源浪费
            
            # 高利用率异常检测
            is_cpu_abnormal = (
                cpu_util > self.cpu_threshold and 
                cpu_util > min_valid_utilization and 
                has_prometheus_data  # 必须有有效的监控数据
            )
            is_memory_abnormal = (
                memory_util > self.memory_threshold and 
                memory_util > min_valid_utilization and 
                has_prometheus_data  # 必须有有效的监控数据
            )
            
            # 低利用率异常检测（资源浪费）
            is_memory_underutilized = (
                memory_util < low_memory_threshold and 
                memory_util > min_valid_utilization and  # 排除无效数据
                has_prometheus_data  # 必须有有效的监控数据
            )
            
            # 2. 极端值检测（超过3倍标准差）
            is_cpu_extreme = cpu_std > 0 and abs(cpu_util - cpu_avg) > 3 * cpu_std
            is_memory_extreme = memory_std > 0 and abs(memory_util - memory_avg) > 3 * memory_std
            
            # 3. 数据质量检测
            has_prometheus_data = deployment.get('has_prometheus_data', False)
            is_data_suspicious = False
            
            # 检测可能的数据异常（但不过滤，只标记）
            if cpu_util > 10 or memory_util > 10:  # 超过1000%的明显异常数据
                is_data_suspicious = True
                issues.append(f"数据异常: 利用率数值异常高 (可能是配置问题或指标采集异常)")
                severity_score += 3
            
            # 构建问题描述 - 移除 not is_data_suspicious 条件，让异常数据也能显示
            if is_cpu_abnormal:
                if is_cpu_extreme:
                    issues.append(f"CPU利用率极端异常: {cpu_util:.1%} (远超平均值 {cpu_avg:.1%})")
                    severity_score += 3
                else:
                    issues.append(f"CPU利用率过高: {cpu_util:.1%} > {self.cpu_threshold:.1%}")
                    severity_score += 2
            
            if is_memory_abnormal:
                if is_memory_extreme:
                    issues.append(f"内存利用率极端异常: {memory_util:.1%} (远超平均值 {memory_avg:.1%})")
                    severity_score += 3
                else:
                    issues.append(f"内存利用率过高: {memory_util:.1%} > {self.memory_threshold:.1%}")
                    severity_score += 2
            
            # 低利用率检测（资源浪费）- 移除过滤条件
            if is_memory_underutilized:
                issues.append(f"内存利用率过低: {memory_util:.1%} < {low_memory_threshold:.1%} (资源浪费)")
                severity_score += 1  # 低利用率的严重程度较低
            
            # 4. 资源配置合理性检测（只在有明显使用且缺少配置时报告）
            cpu_requests = deployment.get('cpu_requests', 0)
            memory_requests = deployment.get('memory_requests', 0)
            
            # 提高配置问题的检测阈值，避免误报
            config_check_threshold = 0.2  # 20%，只有利用率较高时才检查配置问题
            
            if (cpu_requests == 0 and 
                cpu_util > config_check_threshold):  # 没有设置CPU请求但使用率较高
                issues.append("配置问题: 未设置CPU资源请求")
                severity_score += 1
            
            if (memory_requests == 0 and 
                memory_util > config_check_threshold):  # 没有设置内存请求但使用率较高
                issues.append("配置问题: 未设置内存资源请求")
                severity_score += 1
            
            # 5. 数据完整性检测（仅记录，不作为异常判断依据）
            data_quality_issues = []
            if not has_prometheus_data:
                data_quality_issues.append("数据质量: 缺少Prometheus监控数据，利用率可能不准确")
            
            # 判断是否为异常资源（包含所有问题，不再过滤）
            real_issues = [issue for issue in issues if not issue.startswith("数据质量")]
            
            # 修改逻辑：只要有任何问题（包括数据异常）就认为是异常资源
            if issues:  # 改为检查所有问题，而不只是real_issues
                abnormal_resources += 1
                # 合并真实问题和数据质量问题
                all_issues = real_issues + data_quality_issues
                
                # 计算严重程度等级
                if severity_score >= 5:
                    severity_level = "critical"
                elif severity_score >= 3:
                    severity_level = "high"
                elif severity_score >= 2:
                    severity_level = "medium"
                else:
                    severity_level = "low"
                
                abnormal_details.append({
                    'name': deployment['name'],
                    'namespace': deployment['namespace'],
                    'resource_id': deployment['resource_id'],
                    'cpu_utilization': f"{cpu_util:.1%}",
                    'memory_utilization': f"{memory_util:.1%}",
                    'cpu_requests': deployment['cpu_requests'],
                    'memory_requests': deployment['memory_requests'],
                    'issues': all_issues,
                    'real_issues': real_issues,
                    'data_quality_issues': data_quality_issues,
                    'severity_score': severity_score,
                    'severity_level': severity_level,
                    'has_prometheus_data': has_prometheus_data,
                    'is_data_suspicious': is_data_suspicious
                })
            else:
                normal_resources += 1
        
        # 生成正常资源摘要
        if normal_resources > 0:
            # 计算正常资源的平均利用率（数据已经是比例值）
            normal_cpu_values = [d['cpu_utilization'] for d in deployments if d['cpu_utilization'] <= self.cpu_threshold]
            normal_memory_values = [d['memory_utilization'] for d in deployments if d['memory_utilization'] <= self.memory_threshold]
            
            avg_cpu = sum(normal_cpu_values) / len(normal_cpu_values) if normal_cpu_values else 0
            avg_memory = sum(normal_memory_values) / len(normal_memory_values) if normal_memory_values else 0
            
            # 转换为百分比显示
            normal_summary = f"正常资源 {normal_resources} 个，平均CPU利用率 {avg_cpu:.1%}，平均内存利用率 {avg_memory:.1%}"
        else:
            normal_summary = "无正常资源"
        
        # 统计数据质量问题
        data_quality_issues_count = sum(1 for d in deployments if not d.get('has_prometheus_data', False))
        
        # 生成分析摘要
        analysis_summary = f"共分析 {total_resources} 个资源，发现 {abnormal_resources} 个真实异常资源"
        if data_quality_issues_count > 0:
            analysis_summary += f"，另有 {data_quality_issues_count} 个资源存在数据质量问题"
        
        return ResourceAnalysisResult(
            total_resources=total_resources,
            normal_resources=normal_resources,
            abnormal_resources=abnormal_resources,
            normal_summary=normal_summary,
            abnormal_details=abnormal_details,
            recommendations=[],
            analysis_time=datetime.now().isoformat(),
            data_quality_issues_count=data_quality_issues_count,
            analysis_summary=analysis_summary
        )
    
    def _generate_smart_recommendations(self, abnormal_details: List[Dict[str, Any]]) -> List[str]:
        """生成智能优化建议 - 基于严重程度和问题类型"""
        try:
            if not abnormal_details:
                return []
            
            recommendations = []
            
            # 按严重程度排序
            sorted_details = sorted(abnormal_details, key=lambda x: x.get('severity_score', 0), reverse=True)
            
            # 统计问题类型
            critical_issues = [d for d in abnormal_details if d.get('severity_level') == 'critical']
            high_issues = [d for d in abnormal_details if d.get('severity_level') == 'high']
            data_suspicious_issues = [d for d in abnormal_details if d.get('is_data_suspicious', False)]
            config_issues = [d for d in abnormal_details if any('配置问题' in issue for issue in d.get('real_issues', []))]
            
            # 统计低利用率资源（需要缩容）
            underutilized_issues = [d for d in abnormal_details if any('利用率过低' in issue for issue in d.get('real_issues', []))]
            
            # 统计有真实问题的资源（排除纯数据质量问题）
            real_abnormal_resources = [d for d in abnormal_details if d.get('real_issues', [])]
            data_only_issues = [d for d in abnormal_details if not d.get('real_issues', []) and d.get('data_quality_issues', [])]
            
            # 0. 数据质量问题优先处理
            if data_only_issues:
                recommendations.append(f"📊 数据质量问题: 发现 {len(data_only_issues)} 个资源仅存在监控数据问题")
                recommendations.append("   • 这些资源本身可能正常运行，但缺少Prometheus监控数据")
                recommendations.append("   • 建议优先修复监控系统，而非调整资源配置")
                recommendations.append("   • 检查Prometheus配置和ServiceMonitor设置")
                recommendations.append("")
            
            # 1. 真实异常资源处理建议
            if real_abnormal_resources:
                recommendations.append(f"🚨 真实异常资源: 发现 {len(real_abnormal_resources)} 个需要关注的资源问题")
                
                # 按严重程度处理
                if critical_issues:
                    recommendations.append(f"   🔥 严重问题 ({len(critical_issues)}个): 需要立即处理")
                    for detail in critical_issues[:3]:  # 只显示前3个最严重的
                        app_name = detail['name']
                        namespace = detail['namespace']
                        real_issues = detail.get('real_issues', [])
                        recommendations.append(
                            f"      • {namespace}/{app_name}: {', '.join(real_issues[:2])}"
                        )
                
                if high_issues:
                    recommendations.append(f"   ⚠️ 高优先级问题 ({len(high_issues)}个): 建议尽快处理")
            else:
                recommendations.append("✅ 未发现需要立即处理的资源异常问题")
            
            # 2. 数据质量问题处理
            if data_suspicious_issues:
                recommendations.append(f"🔍 数据质量: 发现 {len(data_suspicious_issues)} 个可疑数据，建议检查监控系统")
                recommendations.append("   • 检查Prometheus指标采集是否正常")
                recommendations.append("   • 验证资源请求配置是否合理")
                recommendations.append("   • 考虑重新同步知识图谱数据")
            
            # 3. 配置问题修复
            if config_issues:
                recommendations.append(f"⚙️ 配置优化: 发现 {len(config_issues)} 个配置问题")
                for detail in config_issues[:5]:
                    app_name = detail['name']
                    namespace = detail['namespace']
                    issues = detail.get('issues', [])
                    config_problems = [issue for issue in issues if '配置问题' in issue]
                    if config_problems:
                        recommendations.append(f"   • {namespace}/{app_name}: {config_problems[0]}")
            
            # 4. 具体资源优化建议
            cpu_issues = [d for d in abnormal_details if any('CPU' in issue for issue in d.get('issues', []))]
            memory_issues = [d for d in abnormal_details if any('内存' in issue for issue in d.get('issues', []))]
            
            if cpu_issues:
                recommendations.append(f"🔧 CPU优化: {len(cpu_issues)} 个资源需要CPU优化")
                # 按CPU利用率排序，优先处理最高的
                cpu_sorted = sorted(cpu_issues, key=lambda x: float(x.get('cpu_utilization', '0%').rstrip('%')), reverse=True)
                for detail in cpu_sorted[:3]:
                    app_name = detail['name']
                    namespace = detail['namespace']
                    cpu_util = detail.get('cpu_utilization', 'N/A')
                    recommendations.append(f"   • {namespace}/{app_name} (CPU: {cpu_util}): 考虑增加CPU配额或优化代码")
            
            if memory_issues:
                recommendations.append(f"💾 内存优化: {len(memory_issues)} 个资源需要内存优化")
                # 按内存利用率排序，优先处理最高的
                memory_sorted = sorted(memory_issues, key=lambda x: float(x.get('memory_utilization', '0%').rstrip('%')), reverse=True)
                for detail in memory_sorted[:3]:
                    app_name = detail['name']
                    namespace = detail['namespace']
                    memory_util = detail.get('memory_utilization', 'N/A')
                    recommendations.append(f"   • {namespace}/{app_name} (内存: {memory_util}): 检查内存泄漏或增加内存配额")
            
            # 低利用率资源缩容建议
            if underutilized_issues:
                recommendations.append(f"📉 资源缩容: {len(underutilized_issues)} 个资源利用率过低，建议缩容")
                # 按内存利用率排序，优先处理利用率最低的
                underutilized_sorted = sorted(underutilized_issues, key=lambda x: float(x.get('memory_utilization', '100%').rstrip('%')))
                for detail in underutilized_sorted[:5]:  # 显示前5个最需要缩容的
                    app_name = detail['name']
                    namespace = detail['namespace']
                    memory_util = detail.get('memory_utilization', 'N/A')
                    recommendations.append(f"   • {namespace}/{app_name} (内存: {memory_util}): 建议减少内存请求或副本数")
                    recommendations.append(f"     kubectl edit deployment {app_name} -n {namespace}  # 手动调整resources.requests.memory")
                recommendations.append("   💡 提示: 缩容前请确认应用在低负载时的正常内存需求")
            
            # 5. 批量处理建议
            if len(abnormal_details) > 5:
                recommendations.append("📋 批量处理建议:")
                recommendations.append("   • 使用 kubectl top pods --all-namespaces --sort-by=memory 查看资源使用排序")
                recommendations.append("   • 考虑批量调整资源配额: kubectl patch deployment <name> -p '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"<container>\",\"resources\":{\"requests\":{\"memory\":\"<new-value>\"}}}]}}}}'")
                recommendations.append("   • 设置资源监控告警，及时发现问题")
            
            # 6. 预防性建议
            recommendations.append("🛡️ 预防措施:")
            recommendations.append("   • 定期检查资源使用趋势，建议每周进行资源分析")
            recommendations.append("   • 设置HPA自动扩缩容，应对负载波动")
            recommendations.append("   • 建立资源配额管理策略，避免资源过度分配")
            
            # 7. 监控优化建议
            if not any(d.get('has_prometheus_data', True) for d in abnormal_details):
                recommendations.append("📊 监控改进:")
                recommendations.append("   • 完善Prometheus监控配置，确保数据采集完整性")
                recommendations.append("   • 设置关键指标告警，CPU > 80%, 内存 > 70%")
                recommendations.append("   • 定期校验监控数据准确性")
            
            return recommendations[:20]  # 最多返回20条建议
            
        except Exception as e:
            logger.error(f"生成智能建议失败: {e}")
            return [f"建议生成失败: {e}"]
    

    
    async def _send_dingtalk_notification(self, analysis_result: ResourceAnalysisResult):
        """发送钉钉通知"""
        try:
            if not self.http_client:
                logger.warning("HTTP客户端未配置，跳过钉钉通知")
                return
            
            # 构建告警数据 - 符合ResourceAlertData模型
            alert_data = {
                "resource_id": "cluster_wide_analysis",
                "metrics": {
                    "alert_type": "resource_analysis",
                    "severity": "high" if analysis_result.abnormal_resources > 5 else "medium", 
                    "summary": f"发现 {analysis_result.abnormal_resources} 个异常资源需要关注",
                    "total_resources": analysis_result.total_resources,
                    "abnormal_resources": analysis_result.abnormal_resources,
                    "normal_summary": analysis_result.normal_summary,
                    "abnormal_details": analysis_result.abnormal_details,  # 发送所有异常资源
                    "recommendations": analysis_result.recommendations[:3],  # 只发送前3条建议
                    "analysis_time": analysis_result.analysis_time
                },
                "timestamp": analysis_result.analysis_time,
                "source": "k8s-mcp-server",
                "alert_reasons": [f"发现 {analysis_result.abnormal_resources} 个异常资源"],
                "thresholds": {
                    "cpu_threshold": self.cpu_threshold,
                    "memory_threshold": self.memory_threshold
                },
                "current_utilization": {
                    "abnormal_ratio": analysis_result.abnormal_resources / analysis_result.total_resources
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
