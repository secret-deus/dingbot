"""
K8s集群摘要工具

提供集群状态的智能摘要功能，包括：
- 集群整体健康状态
- 资源统计和分布
- 异常资源检测和分析
- 性能指标聚合
- 命名空间详细分析
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from loguru import logger

from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.tool_registry import MCPToolBase
from ..core.k8s_graph import K8sKnowledgeGraph
from ..core.summary_generator import SummaryGenerator
from ..config import get_config


class K8sClusterSummaryTool(MCPToolBase):
    """K8s集群摘要工具
    
    负责生成集群的智能摘要报告，提供集群状态概览、
    异常检测、资源统计等功能。支持双模式运行：
    - 智能模式：使用知识图谱和摘要生成器
    - 基础模式：基于现有工具的简化摘要
    """

    def __init__(self):
        """初始化集群摘要工具"""
        super().__init__(
            name="k8s-cluster-summary",
            description="生成K8s集群的智能摘要报告，包含集群健康状态、资源统计、异常检测等信息"
        )
        
        # 执行统计
        self.execution_count = 0
        self.last_execution_time = None
        self.avg_execution_time = 0
        
        # 初始化智能组件（如果启用）
        self._initialize_intelligent_components()
        
        logger.info("K8s集群摘要工具 已初始化")

    def _initialize_intelligent_components(self):
        """初始化智能组件"""
        try:
            config = get_config()
            
            if config.enable_knowledge_graph:
                # 智能模式：使用共享的知识图谱
                logger.info("启用智能模式，使用共享知识图谱...")
                
                from ..core.k8s_graph import get_shared_knowledge_graph
                self.kg = get_shared_knowledge_graph(config)
                self.summary_generator = SummaryGenerator(self.kg, config)
                self.intelligent_mode = True
                
                logger.info("智能集群摘要组件初始化完成（使用共享知识图谱）")
            else:
                # 基础模式
                logger.info("知识图谱功能未启用，集群摘要工具将使用基础模式")
                self.kg = None
                self.summary_generator = None
                self.intelligent_mode = False
                
        except Exception as e:
            logger.warning(f"智能组件初始化失败，回退到基础模式: {e}")
            self.kg = None
            self.summary_generator = None
            self.intelligent_mode = False

    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "摘要范围类型",
                        "enum": [
                            "cluster",           # 全集群摘要
                            "namespace",         # 命名空间级摘要
                            "health",           # 健康状态摘要
                            "resources",        # 资源统计摘要
                            "anomalies",        # 异常检测摘要
                            "performance"       # 性能指标摘要
                        ],
                        "default": "cluster"
                    },
                    "focus_namespace": {
                        "type": "string",
                        "description": "聚焦分析的命名空间（仅用于namespace范围）",
                        "default": None
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "是否包含详细分析信息",
                        "default": True
                    },
                    "max_size_kb": {
                        "type": "integer",
                        "description": "输出最大大小（KB）",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    },
                    "anomaly_threshold": {
                        "type": "string",
                        "description": "异常检测敏感度",
                        "enum": ["low", "medium", "high"],
                        "default": "medium"
                    },
                    "include_historical": {
                        "type": "boolean",
                        "description": "是否包含历史趋势信息",
                        "default": False
                    },
                    "resource_types": {
                        "type": "array",
                        "description": "关注的资源类型列表",
                        "items": {
                            "type": "string"
                        },
                        "default": None
                    },
                    "time_range": {
                        "type": "string",
                        "description": "时间范围（用于历史分析）",
                        "enum": ["1h", "6h", "24h", "7d"],
                        "default": "1h"
                    }
                },
                "required": ["scope"]
            }
        )

    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行集群摘要生成"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # 参数验证
            validation_result = self._validate_arguments(arguments)
            if validation_result:
                return validation_result
            
            # 提取参数（确保安全的默认值）
            scope = arguments.get("scope", "cluster")
            focus_namespace = arguments.get("focus_namespace")
            include_details = bool(arguments.get("include_details", True))
            
            # 安全处理max_size_kb参数
            max_size_kb = arguments.get("max_size_kb", 10)
            if max_size_kb is None:
                max_size_kb = 10
            elif isinstance(max_size_kb, str) and max_size_kb.isdigit():
                max_size_kb = int(max_size_kb)
            elif not isinstance(max_size_kb, int):
                try:
                    max_size_kb = int(max_size_kb)
                except (ValueError, TypeError):
                    max_size_kb = 10
            
            anomaly_threshold = arguments.get("anomaly_threshold", "medium")
            include_historical = bool(arguments.get("include_historical", False))
            resource_types = arguments.get("resource_types")
            time_range = arguments.get("time_range", "1h")
            
            # 生成摘要
            if self.intelligent_mode and self.kg and self.summary_generator:
                # 智能模式
                result = await self._generate_intelligent_summary(
                    scope, focus_namespace, include_details, max_size_kb,
                    anomaly_threshold, include_historical, resource_types, time_range
                )
            else:
                # 基础模式
                result = await self._generate_basic_summary(
                    scope, focus_namespace, include_details,
                    anomaly_threshold, resource_types
                )
            
            # 更新统计
            execution_time = time.time() - start_time
            self._update_execution_stats(execution_time)
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                is_error=False
            )
            
        except Exception as e:
            import traceback
            error_msg = f"集群摘要生成失败: {str(e)}"
            logger.error(f"{error_msg}\n详细错误堆栈:\n{traceback.format_exc()}")
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": json.dumps({"error": error_msg, "traceback": traceback.format_exc()}, ensure_ascii=False)}],
                is_error=True
            )

    def _validate_arguments(self, arguments: Dict[str, Any]) -> Optional[MCPCallToolResult]:
        """验证输入参数"""
        try:
            scope = arguments.get("scope", "cluster")
            if scope not in ["cluster", "namespace", "health", "resources", "anomalies", "performance"]:
                error_msg = f"无效的摘要范围: {scope}"
                logger.error(error_msg)
                return MCPCallToolResult(
                    content=[{"type": "text", "text": json.dumps({"error": f"参数验证失败: {error_msg}"}, ensure_ascii=False)}],
                    is_error=True
                )
            
            # 验证命名空间范围参数
            if scope == "namespace":
                focus_namespace = arguments.get("focus_namespace")
                if not focus_namespace:
                    error_msg = "命名空间范围摘要需要指定focus_namespace参数"
                    logger.error(error_msg)
                    return MCPCallToolResult(
                        content=[{"type": "text", "text": json.dumps({"error": f"参数验证失败: {error_msg}"}, ensure_ascii=False)}],
                        is_error=True
                    )
            
            # 验证大小限制
            max_size_kb = arguments.get("max_size_kb", 10)
            
            # 处理None值和类型转换
            if max_size_kb is None:
                max_size_kb = 10
            elif isinstance(max_size_kb, str) and max_size_kb.isdigit():
                max_size_kb = int(max_size_kb)
            elif not isinstance(max_size_kb, int):
                try:
                    max_size_kb = int(max_size_kb)
                except (ValueError, TypeError):
                    max_size_kb = 10  # 回退到默认值
            
            if max_size_kb < 1 or max_size_kb > 50:
                error_msg = f"无效的大小限制: {max_size_kb}KB，必须在1-50之间"
                logger.error(error_msg)
                return MCPCallToolResult(
                    content=[{"type": "text", "text": json.dumps({"error": f"参数验证失败: {error_msg}"}, ensure_ascii=False)}],
                    is_error=True
                )
            
            return None  # 验证通过
            
        except Exception as e:
            error_msg = f"参数验证过程出错: {str(e)}"
            logger.error(error_msg)
            return MCPCallToolResult(
                content=[{"type": "text", "text": json.dumps({"error": error_msg}, ensure_ascii=False)}],
                is_error=True
            )

    async def _generate_intelligent_summary(self, scope: str, focus_namespace: str,
                                          include_details: bool, max_size_kb: int,
                                          anomaly_threshold: str, include_historical: bool,
                                          resource_types: List[str], time_range: str) -> Dict[str, Any]:
        """使用智能模式生成摘要"""
        try:
            logger.debug(f"生成智能摘要: scope={scope}, namespace={focus_namespace}")
            
            # 根据不同范围生成相应摘要
            if scope == "cluster":
                # 全集群摘要
                summary = self.summary_generator.generate_cluster_summary(
                    focus_namespace=focus_namespace,
                    include_details=include_details
                )
                
                # 添加工具特定信息
                summary["scope"] = "cluster"
                summary["generation_mode"] = "intelligent"
                summary["features"] = {
                    "knowledge_graph_enabled": True,
                    "real_time_sync": True,
                    "anomaly_detection": True,
                    "relationship_analysis": True
                }
                
            elif scope == "namespace":
                # 命名空间级摘要
                summary = self._generate_namespace_summary(focus_namespace, include_details)
                
            elif scope == "health":
                # 健康状态摘要
                summary = self._generate_health_summary(anomaly_threshold)
                
            elif scope == "resources":
                # 资源统计摘要
                summary = self._generate_resources_summary(resource_types, focus_namespace)
                
            elif scope == "anomalies":
                # 异常检测摘要
                summary = self._generate_anomalies_summary(anomaly_threshold, focus_namespace)
                
            elif scope == "performance":
                # 性能指标摘要
                summary = self._generate_performance_summary(time_range, include_historical)
                
            else:
                raise ValueError(f"不支持的摘要范围: {scope}")
            
            # 添加生成元信息
            summary["generation_info"] = {
                "timestamp": datetime.now().isoformat(),
                "tool": self.name,
                "mode": "intelligent",
                "execution_count": self.execution_count,
                "graph_nodes": len(self.kg.graph.nodes) if self.kg else 0,
                "graph_edges": len(self.kg.graph.edges) if self.kg else 0
            }
            
            # 控制输出大小
            if max_size_kb and max_size_kb < 50:
                summary = self._compress_summary_to_size(summary, max_size_kb)
            
            return summary
            
        except Exception as e:
            logger.error(f"智能摘要生成失败: {e}")
            raise

    async def _generate_basic_summary(self, scope: str, focus_namespace: str,
                                    include_details: bool, anomaly_threshold: str,
                                    resource_types: List[str]) -> Dict[str, Any]:
        """使用基础模式生成摘要"""
        logger.info("使用基础模式生成集群摘要")
        
        # 基础模式返回简化摘要和工具建议
        summary = {
            "status": "basic_mode",
            "message": "集群摘要工具运行在基础模式，智能功能未启用",
            "scope": scope,
            "generation_mode": "basic",
            "timestamp": datetime.now().isoformat(),
            "limitations": [
                "无法访问知识图谱数据",
                "无法进行实时异常检测",
                "无法分析资源关联关系",
                "无法提供智能摘要压缩"
            ],
            "recommendations": {
                "enable_intelligent_mode": "设置环境变量 ENABLE_KNOWLEDGE_GRAPH=true 启用智能模式",
                "alternative_tools": [
                    "k8s-get-pods: 获取Pod状态信息",
                    "k8s-get-deployments: 获取Deployment信息",
                    "k8s-get-services: 获取Service信息",
                    "k8s-get-nodes: 获取节点信息",
                    "k8s-get-events: 查看集群事件"
                ]
            },
            "basic_analysis": {
                "suggested_workflow": [
                    "1. 使用 k8s-get-nodes 检查节点状态",
                    "2. 使用 k8s-get-pods 检查Pod运行状况",
                    "3. 使用 k8s-get-events 查看最近事件",
                    "4. 使用 k8s-get-deployments 检查应用状态"
                ],
                "focus_areas_by_scope": {
                    "cluster": "全集群资源状态和事件",
                    "namespace": f"命名空间 {focus_namespace or 'default'} 的资源",
                    "health": "异常Pod和失败的Deployment",
                    "resources": "资源数量统计和分布",
                    "anomalies": "错误事件和异常状态资源",
                    "performance": "资源使用情况和性能指标"
                }.get(scope, "集群整体状态")
            }
        }
        
        return summary

    def _generate_namespace_summary(self, namespace: str, include_details: bool) -> Dict[str, Any]:
        """生成命名空间级摘要"""
        try:
            # 使用摘要生成器的命名空间功能
            cluster_summary = self.summary_generator.generate_cluster_summary(
                focus_namespace=namespace,
                include_details=include_details
            )
            
            # 提取命名空间相关信息
            namespace_data = cluster_summary.get("namespace_breakdown", {}).get(namespace, {})
            
            summary = {
                "scope": "namespace",
                "target_namespace": namespace,
                "resource_count": namespace_data.get("resource_count", 0),
                "resource_types": namespace_data.get("resource_types", {}),
                "health_status": namespace_data.get("health_status", "unknown"),
                "abnormal_resources": [
                    res for res in cluster_summary.get("abnormal_resources", [])
                    if res.get("namespace") == namespace
                ],
                "key_metrics": {
                    "pod_count": namespace_data.get("pod_count", 0),
                    "service_count": namespace_data.get("service_count", 0),
                    "deployment_count": namespace_data.get("deployment_count", 0),
                    "failed_pods": len([
                        res for res in cluster_summary.get("abnormal_resources", [])
                        if res.get("namespace") == namespace and res.get("kind") == "Pod"
                    ])
                }
            }
            
            if include_details:
                summary["detailed_analysis"] = namespace_data.get("detailed_analysis", {})
            
            return summary
            
        except Exception as e:
            logger.error(f"命名空间摘要生成失败: {e}")
            return {"error": f"命名空间摘要生成失败: {str(e)}"}

    def _generate_health_summary(self, threshold: str) -> Dict[str, Any]:
        """生成健康状态摘要"""
        try:
            cluster_summary = self.summary_generator.generate_cluster_summary(
                include_details=True
            )
            
            health_status = cluster_summary.get("health_status", {})
            abnormal_resources = cluster_summary.get("abnormal_resources", [])
            
            # 根据阈值过滤异常
            threshold_mapping = {"low": 10, "medium": 50, "high": 100}
            min_severity = threshold_mapping.get(threshold, 50)
            
            filtered_anomalies = [
                res for res in abnormal_resources
                if self._safe_get_severity(res) >= min_severity
            ]
            
            summary = {
                "scope": "health",
                "overall_health": health_status.get("overall", "unknown"),
                "health_score": health_status.get("score", 0),
                "anomaly_threshold": threshold,
                "critical_issues": len([r for r in filtered_anomalies if r.get("severity") == "critical"]),
                "warning_issues": len([r for r in filtered_anomalies if r.get("severity") == "warning"]),
                "total_anomalies": len(filtered_anomalies),
                "top_issues": filtered_anomalies[:10],  # 前10个问题
                "health_breakdown": health_status.get("breakdown", {}),
                "recommendations": self._generate_health_recommendations(filtered_anomalies)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"健康状态摘要生成失败: {e}")
            return {"error": f"健康状态摘要生成失败: {str(e)}"}

    def _generate_resources_summary(self, resource_types: List[str], namespace: str) -> Dict[str, Any]:
        """生成资源统计摘要"""
        try:
            cluster_summary = self.summary_generator.generate_cluster_summary(
                focus_namespace=namespace,
                include_details=True
            )
            
            resource_stats = cluster_summary.get("resource_statistics", {})
            
            # 过滤指定的资源类型
            if resource_types:
                filtered_stats = {
                    k: v for k, v in resource_stats.items()
                    if k in resource_types or any(rt.lower() in k.lower() for rt in resource_types)
                }
            else:
                filtered_stats = resource_stats
            
            summary = {
                "scope": "resources",
                "target_namespace": namespace,
                "filter_types": resource_types,
                "resource_statistics": filtered_stats,
                "total_resources": sum(v for v in filtered_stats.values() if isinstance(v, int)),
                "resource_distribution": self._calculate_resource_distribution(filtered_stats),
                "growth_trends": cluster_summary.get("growth_trends", {}),
                "capacity_analysis": cluster_summary.get("capacity_analysis", {})
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"资源统计摘要生成失败: {e}")
            return {"error": f"资源统计摘要生成失败: {str(e)}"}

    def _generate_anomalies_summary(self, threshold: str, namespace: str) -> Dict[str, Any]:
        """生成异常检测摘要"""
        try:
            cluster_summary = self.summary_generator.generate_cluster_summary(
                focus_namespace=namespace,
                include_details=True
            )
            
            abnormal_resources = cluster_summary.get("abnormal_resources", [])
            
            # 应用阈值过滤
            threshold_mapping = {"low": 10, "medium": 50, "high": 100}
            min_severity = threshold_mapping.get(threshold, 50)
            
            filtered_anomalies = [
                res for res in abnormal_resources
                if self._safe_get_severity(res) >= min_severity
            ]
            
            # 按命名空间过滤
            if namespace:
                filtered_anomalies = [
                    res for res in filtered_anomalies
                    if res.get("namespace") == namespace
                ]
            
            # 分类统计
            anomaly_categories = self._categorize_anomalies(filtered_anomalies)
            
            summary = {
                "scope": "anomalies",
                "detection_threshold": threshold,
                "target_namespace": namespace,
                "total_anomalies": len(filtered_anomalies),
                "anomaly_categories": anomaly_categories,
                "severity_breakdown": {
                    "critical": len([r for r in filtered_anomalies if r.get("severity") == "critical"]),
                    "warning": len([r for r in filtered_anomalies if r.get("severity") == "warning"]),
                    "info": len([r for r in filtered_anomalies if r.get("severity") == "info"])
                },
                "top_anomalies": filtered_anomalies[:15],  # 前15个异常
                "patterns": self._detect_anomaly_patterns(filtered_anomalies),
                "remediation_suggestions": self._generate_remediation_suggestions(filtered_anomalies)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"异常检测摘要生成失败: {e}")
            return {"error": f"异常检测摘要生成失败: {str(e)}"}

    def _generate_performance_summary(self, time_range: str, include_historical: bool) -> Dict[str, Any]:
        """生成性能指标摘要"""
        try:
            cluster_summary = self.summary_generator.generate_cluster_summary(
                include_details=True
            )
            
            key_metrics = cluster_summary.get("key_metrics", {})
            
            summary = {
                "scope": "performance",
                "time_range": time_range,
                "include_historical": include_historical,
                "performance_metrics": key_metrics,
                "resource_utilization": {
                    "nodes": key_metrics.get("node_utilization", {}),
                    "pods": key_metrics.get("pod_metrics", {}),
                    "storage": key_metrics.get("storage_metrics", {})
                },
                "bottlenecks": self._identify_performance_bottlenecks(key_metrics),
                "optimization_recommendations": self._generate_optimization_recommendations(key_metrics)
            }
            
            if include_historical:
                summary["historical_trends"] = self._generate_historical_trends(time_range)
            
            return summary
            
        except Exception as e:
            logger.error(f"性能指标摘要生成失败: {e}")
            return {"error": f"性能指标摘要生成失败: {str(e)}"}

    def _calculate_resource_distribution(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """计算资源分布"""
        try:
            total = sum(v for v in stats.values() if isinstance(v, (int, float)))
            if total == 0:
                return {}
            
            distribution = {}
            for resource_type, count in stats.items():
                if isinstance(count, (int, float)):
                    distribution[resource_type] = {
                        "count": count,
                        "percentage": round((count / total) * 100, 2)
                    }
            
            return distribution
        except Exception:
            return {}

    def _categorize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分类异常"""
        categories = {
            "pod_failures": [],
            "deployment_issues": [],
            "service_problems": [],
            "node_issues": [],
            "storage_problems": [],
            "network_issues": [],
            "other": []
        }
        
        for anomaly in anomalies:
            kind = anomaly.get("kind", "").lower()
            reason = anomaly.get("reason", "").lower()
            
            if kind == "pod" or "pod" in reason:
                categories["pod_failures"].append(anomaly)
            elif kind == "deployment" or "deploy" in reason:
                categories["deployment_issues"].append(anomaly)
            elif kind == "service" or "service" in reason:
                categories["service_problems"].append(anomaly)
            elif kind == "node" or "node" in reason:
                categories["node_issues"].append(anomaly)
            elif "storage" in reason or "volume" in reason:
                categories["storage_problems"].append(anomaly)
            elif "network" in reason or "dns" in reason:
                categories["network_issues"].append(anomaly)
            else:
                categories["other"].append(anomaly)
        
        # 返回非空分类的统计
        return {k: len(v) for k, v in categories.items() if v}

    def _detect_anomaly_patterns(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """检测异常模式"""
        patterns = []
        
        # 检测常见模式
        if len([a for a in anomalies if a.get("kind") == "Pod" and "ImagePullBackOff" in str(a.get("reason", ""))]) >= 3:
            patterns.append("检测到多个镜像拉取失败，可能是镜像仓库问题或网络问题")
        
        if len([a for a in anomalies if "OutOfMemory" in str(a.get("reason", ""))]) >= 2:
            patterns.append("检测到内存不足问题，建议检查资源限制和节点容量")
        
        if len([a for a in anomalies if a.get("namespace") == "kube-system"]) >= 2:
            patterns.append("系统命名空间出现异常，可能影响集群核心功能")
        
        return patterns

    def _generate_health_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """生成健康建议"""
        recommendations = []
        
        if anomalies:
            recommendations.append(f"发现 {len(anomalies)} 个异常，建议优先处理高严重性问题")
        
        critical_count = len([a for a in anomalies if a.get("severity") == "critical"])
        if critical_count > 0:
            recommendations.append(f"有 {critical_count} 个严重问题需要立即处理")
        
        return recommendations

    def _generate_remediation_suggestions(self, anomalies: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """生成修复建议"""
        suggestions = {
            "immediate_actions": [],
            "preventive_measures": [],
            "monitoring_improvements": []
        }
        
        for anomaly in anomalies[:5]:  # 前5个异常
            reason = anomaly.get("reason", "")
            if "ImagePullBackOff" in reason:
                suggestions["immediate_actions"].append("检查镜像仓库连接和镜像标签")
            elif "CrashLoopBackOff" in reason:
                suggestions["immediate_actions"].append("检查应用日志和配置")
            elif "OutOfMemory" in reason:
                suggestions["immediate_actions"].append("调整内存限制或优化应用内存使用")
        
        return suggestions

    def _identify_performance_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        # 检查节点利用率
        node_util = metrics.get("node_utilization", {})
        cpu_util = node_util.get("average_cpu_percent", 0)
        memory_util = node_util.get("average_memory_percent", 0)
        
        if cpu_util > 80:
            bottlenecks.append(f"CPU利用率过高: {cpu_util}%")
        if memory_util > 80:
            bottlenecks.append(f"内存利用率过高: {memory_util}%")
        
        return bottlenecks

    def _generate_optimization_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        node_util = metrics.get("node_utilization", {})
        cpu_util = node_util.get("average_cpu_percent", 0)
        
        if cpu_util > 70:
            recommendations.append("考虑增加节点或优化CPU密集型应用")
        
        pod_count = metrics.get("total_pods", 0)
        if pod_count > 100:
            recommendations.append("Pod数量较多，建议监控资源分配和调度策略")
        
        return recommendations

    def _generate_historical_trends(self, time_range: str) -> Dict[str, Any]:
        """生成历史趋势（模拟实现）"""
        return {
            "time_range": time_range,
            "note": "历史趋势功能需要持久化存储支持",
            "available_metrics": [],
            "recommendation": "启用监控系统如Prometheus来收集历史数据"
        }

    def _compress_summary_to_size(self, summary: Dict[str, Any], max_size_kb: int) -> Dict[str, Any]:
        """压缩摘要到指定大小"""
        try:
            current_size = len(json.dumps(summary).encode('utf-8'))
            target_size = max_size_kb * 1024
            
            if current_size <= target_size:
                return summary
            
            # 逐步删除非关键信息
            compressed = summary.copy()
            
            # 1. 移除详细分析
            if "detailed_analysis" in compressed:
                del compressed["detailed_analysis"]
                current_size = len(json.dumps(compressed).encode('utf-8'))
                if current_size <= target_size:
                    return compressed
            
            # 2. 限制异常数量
            if "abnormal_resources" in compressed:
                compressed["abnormal_resources"] = compressed["abnormal_resources"][:5]
                current_size = len(json.dumps(compressed).encode('utf-8'))
                if current_size <= target_size:
                    return compressed
            
            # 3. 简化元数据
            if "generation_info" in compressed:
                compressed["generation_info"] = {
                    "timestamp": compressed["generation_info"].get("timestamp"),
                    "mode": compressed["generation_info"].get("mode")
                }
            
            return compressed
            
        except Exception as e:
            logger.warning(f"摘要压缩失败: {e}")
            return summary

    def _safe_get_severity(self, resource: Dict[str, Any]) -> int:
        """安全获取资源严重程度分数"""
        # 优先使用severity_score字段，如果不存在则使用severity字段
        severity_score = resource.get("severity_score")
        if severity_score is not None and isinstance(severity_score, (int, float)):
            return int(severity_score)
        
        severity = resource.get("severity")
        if severity is not None and isinstance(severity, (int, float)):
            return int(severity)
        
        # 如果都不存在或无效，返回默认值0
        return 0

    def _update_execution_stats(self, execution_time: float):
        """更新执行统计"""
        self.last_execution_time = execution_time
        
        if self.execution_count == 1:
            self.avg_execution_time = execution_time
        else:
            self.avg_execution_time = (self.avg_execution_time * (self.execution_count - 1) + execution_time) / self.execution_count

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取工具执行统计"""
        return {
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
            "avg_execution_time": self.avg_execution_time,
            "intelligent_mode_enabled": self.intelligent_mode,
            "knowledge_graph_status": "enabled" if self.kg else "disabled",
            "summary_generator_status": "enabled" if self.summary_generator else "disabled"
        }