"""
K8s资源关联查询工具

提供Kubernetes资源关联查询功能，包括：
- 关联资源查询：获取与指定资源相关的其他资源
- 影响分析：分析资源变更的影响范围
- 依赖追踪：追踪资源的依赖链
- 故障传播分析：分析故障传播路径
- 集群拓扑发现：发现集群拓扑结构
"""

import time
from typing import Dict, Any, List, Optional
from loguru import logger

from ..core.tool_registry import MCPToolBase
from ..core.mcp_protocol import MCPToolSchema, MCPCallToolResult
from ..core.relation_query_handler import (
    RelationQueryHandler, QueryType, QueryRequest, RelationType
)
from ..core.k8s_graph import K8sKnowledgeGraph
from ..core.summary_generator import SummaryGenerator
from ..k8s_client import K8sClient, K8sClientError
from ..config import get_config


class K8sRelationQueryTool(MCPToolBase):
    """K8s资源关联查询工具"""
    
    def __init__(self):
        """初始化工具"""
        super().__init__(
            name="k8s-relation-query",
            description="查询Kubernetes资源之间的关联关系，支持影响分析、依赖追踪和故障传播分析"
        )
        self.config = get_config()
        self.k8s_client = None
        self.query_handler = None
        self.knowledge_graph = None
        self.summary_generator = None
        
        # 初始化智能组件（如果启用）
        self._initialize_intelligent_components()
        
        logger.info("K8s资源关联查询工具已初始化")
    
    def _initialize_intelligent_components(self):
        """初始化智能组件"""
        if not self.config.enable_knowledge_graph:
            logger.info("知识图谱功能未启用，关联查询工具将使用基础模式")
            return
        
        try:
            # 使用共享的知识图谱
            from ..core.k8s_graph import get_shared_knowledge_graph
            self.knowledge_graph = get_shared_knowledge_graph(self.config)
            
            # 创建摘要生成器
            self.summary_generator = SummaryGenerator(self.knowledge_graph, self.config)
            
            # 创建关联查询处理器
            self.query_handler = RelationQueryHandler(
                self.knowledge_graph, 
                self.summary_generator, 
                self.config
            )
            
            logger.info("智能关联查询组件初始化完成（使用共享知识图谱）")
            
        except Exception as e:
            logger.error(f"智能组件初始化失败: {e}")
            self.query_handler = None
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema定义"""
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            input_schema={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "查询类型",
                        "enum": [
                            "related_resources",      # 关联资源查询
                            "impact_analysis",        # 影响分析
                            "dependency_trace",       # 依赖追踪
                            "failure_propagation",    # 故障传播分析
                            "cluster_topology",       # 集群拓扑发现
                            "anomaly_correlation"     # 异常关联分析
                        ],
                        "default": "related_resources"
                    },
                    "target_resources": {
                        "type": "array",
                        "description": "目标资源列表，格式：['kind/namespace/name', ...]",
                        "items": {
                            "type": "string",
                            "pattern": "^[a-zA-Z0-9-]+/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+$"
                        },
                        "minItems": 0
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "查询最大深度",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3
                    },
                    "relation_filter": {
                        "type": "array",
                        "description": "关系类型过滤器",
                        "items": {
                            "type": "string",
                            "enum": ["ownedBy", "routes", "hosts", "dependsOn", "connects", "uses"]
                        },
                        "default": None
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "是否包含资源元数据",
                        "default": True
                    },
                    "include_health_info": {
                        "type": "boolean",
                        "description": "是否包含健康状态信息",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数量",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100
                    },
                    "focus_namespace": {
                        "type": "string",
                        "description": "聚焦的命名空间（仅用于cluster_topology）",
                        "default": None
                    },
                    "resource_types": {
                        "type": "array",
                        "description": "关注的资源类型列表（仅用于cluster_topology）",
                        "items": {
                            "type": "string"
                        },
                        "default": None
                    }
                },
                "required": ["query_type"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行关联查询
        
        Args:
            arguments: 查询参数
            
        Returns:
            MCPCallToolResult: 查询结果
        """
        start_time = time.time()
        
        try:
            # 解析查询参数
            query_type = arguments.get("query_type", "related_resources")
            target_resources = arguments.get("target_resources", [])
            max_depth = arguments.get("max_depth", 3)
            relation_filter = arguments.get("relation_filter")
            include_metadata = arguments.get("include_metadata", True)
            include_health_info = arguments.get("include_health_info", True)
            max_results = arguments.get("max_results", 100)
            focus_namespace = arguments.get("focus_namespace")
            resource_types = arguments.get("resource_types")
            
            # 验证参数
            if not self._validate_arguments(query_type, target_resources):
                return MCPCallToolResult(
                content=[{"type": "text", "text": "参数验证失败"}],
                is_error=True
            )
            
            # 检查智能功能是否可用
            if not self.query_handler:
                return await self._execute_basic_query(arguments)
            
            # 执行智能关联查询
            result = await self._execute_intelligent_query(
                query_type, target_resources, max_depth, relation_filter,
                include_metadata, include_health_info, max_results,
                focus_namespace, resource_types
            )
            
            execution_time = time.time() - start_time
            
            # 格式化结果
            formatted_result = self._format_query_result(result, execution_time)
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": formatted_result}],
                is_error=False
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"关联查询执行失败: {str(e)}"
            logger.error(f"{error_msg} (耗时: {execution_time:.3f}s)")
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": error_msg}],
                is_error=True
            )
    
    def _validate_arguments(self, query_type: str, target_resources: List[str]) -> bool:
        """验证查询参数"""
        # 验证查询类型
        valid_types = [
            "related_resources", "impact_analysis", "dependency_trace",
            "failure_propagation", "cluster_topology", "anomaly_correlation"
        ]
        if query_type not in valid_types:
            logger.error(f"无效的查询类型: {query_type}")
            return False
        
        # 集群拓扑查询不需要目标资源
        if query_type == "cluster_topology":
            return True
        
        # 其他查询类型需要目标资源
        if not target_resources:
            logger.error(f"查询类型 {query_type} 需要指定目标资源")
            return False
        
        # 验证资源ID格式
        for resource_id in target_resources:
            if not self._is_valid_resource_id(resource_id):
                logger.error(f"无效的资源ID格式: {resource_id}")
                return False
        
        return True
    
    def _is_valid_resource_id(self, resource_id: str) -> bool:
        """验证资源ID格式"""
        parts = resource_id.split('/')
        return len(parts) == 3 and all(part.strip() for part in parts)
    
    async def _execute_basic_query(self, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """执行基础查询（无智能功能）"""
        query_type = arguments.get("query_type", "related_resources")
        
        basic_result = {
            "query_type": query_type,
            "status": "basic_mode",
            "message": "智能关联查询功能未启用，请启用知识图谱功能以获得完整的关联查询能力",
            "suggestion": "设置环境变量 ENABLE_KNOWLEDGE_GRAPH=true 以启用智能功能",
            "available_basic_tools": [
                "k8s-get-pods", "k8s-get-deployments", "k8s-get-services",
                "k8s-get-nodes", "k8s-describe-pod"
            ]
        }
        
        import json
        return MCPCallToolResult(
            content=[{"type": "text", "text": json.dumps(basic_result, ensure_ascii=False, indent=2)}],
            is_error=False
        )
    
    async def _execute_intelligent_query(self, query_type: str, target_resources: List[str],
                                       max_depth: int, relation_filter: Optional[List[str]],
                                       include_metadata: bool, include_health_info: bool,
                                       max_results: int, focus_namespace: Optional[str],
                                       resource_types: Optional[List[str]]):
        """执行智能关联查询"""
        
        # 转换查询类型
        query_type_enum = self._convert_query_type(query_type)
        
        # 转换关系过滤器
        relation_filter_set = set(relation_filter) if relation_filter else None
        
        # 构建查询请求
        request = QueryRequest(
            query_type=query_type_enum,
            target_resources=target_resources,
            max_depth=max_depth,
            relation_filter=relation_filter_set,
            include_metadata=include_metadata,
            include_health_info=include_health_info,
            max_results=max_results
        )
        
        # 为集群拓扑查询添加额外参数
        if query_type == "cluster_topology":
            if not hasattr(request, 'extra_params'):
                request.extra_params = {}
            request.extra_params['focus_namespace'] = focus_namespace
            request.extra_params['resource_types'] = resource_types
        
        # 执行查询
        if query_type == "related_resources":
            return self.query_handler.query_related_resources(
                target_resources, max_depth, relation_filter_set, include_metadata
            )
        elif query_type == "impact_analysis":
            return self.query_handler.analyze_impact(
                target_resources, max_depth, include_health_info
            )
        elif query_type == "dependency_trace":
            return self.query_handler.trace_dependencies(
                target_resources, max_depth
            )
        elif query_type == "failure_propagation":
            return self.query_handler.analyze_failure_propagation(
                target_resources, max_depth
            )
        elif query_type == "cluster_topology":
            return self.query_handler.discover_cluster_topology(
                focus_namespace, resource_types
            )
        elif query_type == "anomaly_correlation":
            return self.query_handler.execute_query(request)
        else:
            return self.query_handler.execute_query(request)
    
    def _convert_query_type(self, query_type: str) -> QueryType:
        """转换查询类型为枚举"""
        mapping = {
            "related_resources": QueryType.RELATED_RESOURCES,
            "impact_analysis": QueryType.IMPACT_ANALYSIS,
            "dependency_trace": QueryType.DEPENDENCY_TRACE,
            "failure_propagation": QueryType.FAILURE_PROPAGATION,
            "cluster_topology": QueryType.CLUSTER_TOPOLOGY,
            "anomaly_correlation": QueryType.ANOMALY_CORRELATION
        }
        return mapping.get(query_type, QueryType.RELATED_RESOURCES)
    
    def _format_query_result(self, result, execution_time: float) -> str:
        """格式化查询结果"""
        import json
        
        if not result.success:
            return json.dumps({
                "success": False,
                "error": result.error_message,
                "execution_time": execution_time,
                "timestamp": result.timestamp
            }, ensure_ascii=False, indent=2)
        
        # 构建格式化的结果
        formatted_result = {
            "success": True,
            "query_id": result.query_id,
            "query_type": result.query_type.value,
            "target_resources": result.target_resources,
            "execution_time": execution_time,
            "results_count": len(result.results),
            "timestamp": result.timestamp,
            "metadata": result.metadata,
            "results": result.results
        }
        
        # 添加查询类型特定的摘要
        if result.query_type == QueryType.RELATED_RESOURCES:
            formatted_result["summary"] = self._summarize_related_resources(result.results)
        elif result.query_type == QueryType.IMPACT_ANALYSIS:
            formatted_result["summary"] = self._summarize_impact_analysis(result.results)
        elif result.query_type == QueryType.DEPENDENCY_TRACE:
            formatted_result["summary"] = self._summarize_dependency_trace(result.results)
        elif result.query_type == QueryType.FAILURE_PROPAGATION:
            formatted_result["summary"] = self._summarize_failure_propagation(result.results)
        elif result.query_type == QueryType.CLUSTER_TOPOLOGY:
            formatted_result["summary"] = self._summarize_cluster_topology(result.results)
        
        return json.dumps(formatted_result, ensure_ascii=False, indent=2)
    
    def _summarize_related_resources(self, results: List[Dict]) -> Dict:
        """汇总关联资源查询结果"""
        if not results:
            return {"message": "未找到关联资源"}
        
        # 按关系类型分组
        by_relation = {}
        by_depth = {}
        
        for item in results:
            relation = item.get("relation", "unknown")
            depth = item.get("depth", 0)
            
            if relation not in by_relation:
                by_relation[relation] = []
            by_relation[relation].append(item["resource_id"])
            
            if depth not in by_depth:
                by_depth[depth] = 0
            by_depth[depth] += 1
        
        return {
            "total_related": len(results),
            "by_relation_type": {k: len(v) for k, v in by_relation.items()},
            "by_depth": by_depth,
            "max_depth": max(by_depth.keys()) if by_depth else 0
        }
    
    def _summarize_impact_analysis(self, results: List[Dict]) -> Dict:
        """汇总影响分析结果"""
        if not results:
            return {"message": "未找到受影响的资源"}
        
        # 按影响级别和风险分数分析
        by_level = {}
        risk_scores = []
        
        for item in results:
            level = item.get("impact_level", 0)
            risk_score = item.get("risk_score", 0)
            
            if level not in by_level:
                by_level[level] = 0
            by_level[level] += 1
            
            risk_scores.append(risk_score)
        
        return {
            "total_affected": len(results),
            "by_impact_level": by_level,
            "risk_assessment": {
                "max_risk_score": max(risk_scores) if risk_scores else 0,
                "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
                "high_risk_count": len([s for s in risk_scores if s >= 70])
            }
        }
    
    def _summarize_dependency_trace(self, results: List[Dict]) -> Dict:
        """汇总依赖追踪结果"""
        if not results:
            return {"message": "未找到依赖资源"}
        
        # 按依赖级别和关键性分析
        by_level = {}
        criticalities = []
        
        for item in results:
            level = item.get("dependency_level", 0)
            criticality = item.get("criticality", 0)
            
            if level not in by_level:
                by_level[level] = 0
            by_level[level] += 1
            
            criticalities.append(criticality)
        
        return {
            "total_dependencies": len(results),
            "by_dependency_level": by_level,
            "criticality_assessment": {
                "max_criticality": max(criticalities) if criticalities else 0,
                "avg_criticality": sum(criticalities) / len(criticalities) if criticalities else 0,
                "critical_dependencies": len([c for c in criticalities if c >= 80])
            }
        }
    
    def _summarize_failure_propagation(self, results: List[Dict]) -> Dict:
        """汇总故障传播分析结果"""
        if not results:
            return {"message": "未找到故障传播路径"}
        
        # 分析传播概率和严重性
        probabilities = []
        severities = []
        
        for item in results:
            prob = item.get("propagation_probability", 0)
            severity = item.get("severity", "low")
            
            probabilities.append(prob)
            severities.append(severity)
        
        severity_counts = {s: severities.count(s) for s in set(severities)}
        
        return {
            "total_propagation_paths": len(results),
            "probability_assessment": {
                "max_probability": max(probabilities) if probabilities else 0,
                "avg_probability": sum(probabilities) / len(probabilities) if probabilities else 0,
                "high_probability_paths": len([p for p in probabilities if p >= 0.7])
            },
            "severity_distribution": severity_counts
        }
    
    def _summarize_cluster_topology(self, results: List[Dict]) -> Dict:
        """汇总集群拓扑结果"""
        if not results:
            return {"message": "未发现集群拓扑信息"}
        
        # 按级别分析
        nodes = [r for r in results if r.get("level") == "node"]
        namespaces = [r for r in results if r.get("level") == "namespace"]
        
        node_summary = {
            "total_nodes": len(nodes),
            "healthy_nodes": len([n for n in nodes if n.get("health_status") == "healthy"]),
            "total_hosted_resources": sum(n.get("hosted_resources", 0) for n in nodes)
        }
        
        namespace_summary = {
            "total_namespaces": len(namespaces),
            "total_namespace_resources": sum(ns.get("total_resources", 0) for ns in namespaces)
        }
        
        return {
            "cluster_overview": {
                "nodes": node_summary,
                "namespaces": namespace_summary
            }
        }
    
    async def get_k8s_client(self) -> K8sClient:
        """获取K8s客户端"""
        if not self.k8s_client:
            self.k8s_client = K8sClient()
            await self.k8s_client.initialize()
        return self.k8s_client
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        base_stats = {
            "tool_name": self.name,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
            "intelligent_mode_enabled": self.query_handler is not None
        }
        
        if self.query_handler:
            base_stats.update({
                "query_handler_stats": self.query_handler.get_query_stats()
            })
        
        return base_stats