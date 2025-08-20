"""
关联查询处理器

负责处理K8s资源关联查询请求，包括：
- 资源影响分析：分析资源变更对下游的影响范围
- 依赖追踪：追踪资源的上游依赖链
- 故障传播路径分析：分析故障可能的传播路径
- 关联资源发现：发现与指定资源相关的其他资源
- 高级查询功能：支持复杂的图遍历和分析查询
"""

import time
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .k8s_graph import K8sKnowledgeGraph, CLUSTER_SCOPED_RESOURCES
from .summary_generator import SummaryGenerator


class QueryType(Enum):
    """查询类型枚举"""
    RELATED_RESOURCES = "related_resources"
    IMPACT_ANALYSIS = "impact_analysis"
    DEPENDENCY_TRACE = "dependency_trace"
    FAILURE_PROPAGATION = "failure_propagation"
    RESOURCE_PATH = "resource_path"
    CLUSTER_TOPOLOGY = "cluster_topology"
    ANOMALY_CORRELATION = "anomaly_correlation"


class RelationType(Enum):
    """关系类型枚举"""
    OWNERSHIP = "ownership"          # 所有权关系 (Pod -> Deployment)
    NETWORKING = "networking"        # 网络关系 (Service -> Pod)
    HOSTING = "hosting"             # 托管关系 (Node -> Pod)
    DEPENDENCY = "dependency"        # 依赖关系 (App -> Database)
    ALL = "all"                     # 所有关系类型


@dataclass
class QueryRequest:
    """查询请求数据结构"""
    query_type: QueryType
    target_resources: List[str]
    max_depth: int = 3
    relation_filter: Optional[Set[str]] = None
    include_metadata: bool = True
    include_health_info: bool = True
    max_results: int = 100
    timeout_seconds: int = 30


@dataclass
class QueryResult:
    """查询结果数据结构"""
    query_id: str
    query_type: QueryType
    target_resources: List[str]
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None


class RelationQueryHandler:
    """关联查询处理器
    
    负责处理各种类型的资源关联查询，包括：
    - 基础关联查询：获取直接相关的资源
    - 影响分析：分析资源变更的影响范围
    - 依赖追踪：追踪资源的依赖链
    - 故障传播分析：分析故障传播路径
    - 拓扑发现：发现集群拓扑结构
    """

    def __init__(self, knowledge_graph: K8sKnowledgeGraph, 
                 summary_generator: SummaryGenerator = None, 
                 config=None):
        """初始化关联查询处理器
        
        Args:
            knowledge_graph: 知识图谱实例
            summary_generator: 摘要生成器实例（可选）
            config: 配置对象
        """
        self.kg = knowledge_graph
        self.summary_gen = summary_generator
        self.config = config
        
        # 配置参数
        self.default_max_depth = config.graph_max_depth if config else 3
        self.default_timeout = 30
        self.max_results_limit = 1000
        
        # 关系类型映射
        self.relation_type_mapping = {
            RelationType.OWNERSHIP: {"ownedBy", "owns", "controls"},
            RelationType.NETWORKING: {"routes", "exposes", "connects", "loadBalances"},
            RelationType.HOSTING: {"hosts", "scheduledOn", "runsOn"},
            RelationType.DEPENDENCY: {"dependsOn", "requires", "uses", "consumes"},
            RelationType.ALL: set()  # 空集表示所有类型
        }
        
        # 查询统计
        self.stats = {
            "queries_executed": 0,
            "avg_execution_time": 0.0,
            "queries_by_type": defaultdict(int),
            "cache_hits": 0,
            "timeouts": 0,
            "errors": 0
        }
        
        # 查询缓存（简单的时间窗口缓存）
        self.query_cache = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        logger.info("关联查询处理器初始化完成")
    
    def execute_query(self, request: QueryRequest) -> QueryResult:
        """执行查询请求
        
        Args:
            request: 查询请求对象
            
        Returns:
            QueryResult: 查询结果对象
        """
        query_id = self._generate_query_id()
        start_time = time.time()
        
        try:
            # 验证请求
            self._validate_request(request)
            
            # 检查缓存
            cache_key = self._generate_cache_key(request)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                logger.debug(f"查询 {query_id} 命中缓存")
                return cached_result
            
            # 执行具体查询
            results = self._execute_specific_query(request)
            
            # 生成查询结果
            execution_time = time.time() - start_time
            query_result = QueryResult(
                query_id=query_id,
                query_type=request.query_type,
                target_resources=request.target_resources,
                results=results,
                metadata=self._generate_metadata(request, execution_time),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                success=True
            )
            
            # 缓存结果
            self._cache_result(cache_key, query_result)
            
            # 更新统计
            self._update_stats(request, execution_time, success=True)
            
            logger.info(f"查询 {query_id} 执行完成，耗时 {execution_time:.3f}s，结果数 {len(results)}")
            return query_result
            
        except TimeoutError as e:
            self.stats["timeouts"] += 1
            execution_time = time.time() - start_time
            logger.error(f"查询 {query_id} 超时: {e}")
            return self._create_error_result(query_id, request, str(e), execution_time)
            
        except Exception as e:
            self.stats["errors"] += 1
            execution_time = time.time() - start_time
            logger.error(f"查询 {query_id} 执行失败: {e}")
            return self._create_error_result(query_id, request, str(e), execution_time)
    
    def query_related_resources(self, target_resources: List[str], 
                               max_depth: int = 3,
                               relation_filter: Optional[Set[str]] = None,
                               include_metadata: bool = True) -> QueryResult:
        """查询关联资源（便捷方法）
        
        Args:
            target_resources: 目标资源列表
            max_depth: 最大查询深度
            relation_filter: 关系类型过滤器
            include_metadata: 是否包含元数据
            
        Returns:
            QueryResult: 查询结果
        """
        request = QueryRequest(
            query_type=QueryType.RELATED_RESOURCES,
            target_resources=target_resources,
            max_depth=max_depth,
            relation_filter=relation_filter,
            include_metadata=include_metadata
        )
        return self.execute_query(request)
    
    def analyze_impact(self, target_resources: List[str],
                      max_depth: int = 3,
                      include_health_info: bool = True) -> QueryResult:
        """分析资源影响范围（便捷方法）
        
        Args:
            target_resources: 目标资源列表
            max_depth: 分析深度
            include_health_info: 是否包含健康信息
            
        Returns:
            QueryResult: 影响分析结果
        """
        request = QueryRequest(
            query_type=QueryType.IMPACT_ANALYSIS,
            target_resources=target_resources,
            max_depth=max_depth,
            include_health_info=include_health_info
        )
        return self.execute_query(request)
    
    def trace_dependencies(self, target_resources: List[str],
                          max_depth: int = 3) -> QueryResult:
        """追踪资源依赖链（便捷方法）
        
        Args:
            target_resources: 目标资源列表
            max_depth: 追踪深度
            
        Returns:
            QueryResult: 依赖追踪结果
        """
        request = QueryRequest(
            query_type=QueryType.DEPENDENCY_TRACE,
            target_resources=target_resources,
            max_depth=max_depth
        )
        return self.execute_query(request)
    
    def analyze_failure_propagation(self, failed_resources: List[str],
                                   max_depth: int = 3) -> QueryResult:
        """分析故障传播路径（便捷方法）
        
        Args:
            failed_resources: 故障资源列表
            max_depth: 分析深度
            
        Returns:
            QueryResult: 故障传播分析结果
        """
        request = QueryRequest(
            query_type=QueryType.FAILURE_PROPAGATION,
            target_resources=failed_resources,
            max_depth=max_depth,
            include_health_info=True
        )
        return self.execute_query(request)
    
    def discover_cluster_topology(self, focus_namespace: str = None,
                                 resource_types: List[str] = None) -> QueryResult:
        """发现集群拓扑结构（便捷方法）
        
        Args:
            focus_namespace: 聚焦的命名空间
            resource_types: 关注的资源类型列表
            
        Returns:
            QueryResult: 集群拓扑结果
        """
        # 对于拓扑发现，目标资源为空，在具体实现中处理
        request = QueryRequest(
            query_type=QueryType.CLUSTER_TOPOLOGY,
            target_resources=[],
            max_depth=2,
            include_metadata=True
        )
        
        # 将参数传递到metadata中
        if not hasattr(request, 'extra_params'):
            request.extra_params = {}
        request.extra_params['focus_namespace'] = focus_namespace
        request.extra_params['resource_types'] = resource_types
        
        return self.execute_query(request)
    
    def _execute_specific_query(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """执行具体的查询类型"""
        if request.query_type == QueryType.RELATED_RESOURCES:
            return self._query_related_resources(request)
        elif request.query_type == QueryType.IMPACT_ANALYSIS:
            return self._analyze_impact(request)
        elif request.query_type == QueryType.DEPENDENCY_TRACE:
            return self._trace_dependencies(request)
        elif request.query_type == QueryType.FAILURE_PROPAGATION:
            return self._analyze_failure_propagation(request)
        elif request.query_type == QueryType.RESOURCE_PATH:
            return self._find_resource_path(request)
        elif request.query_type == QueryType.CLUSTER_TOPOLOGY:
            return self._discover_cluster_topology(request)
        elif request.query_type == QueryType.ANOMALY_CORRELATION:
            return self._analyze_anomaly_correlation(request)
        else:
            raise ValueError(f"不支持的查询类型: {request.query_type}")
    
    def _query_related_resources(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """查询关联资源"""
        all_results = []
        processed_resources = set()
        
        for target_resource in request.target_resources:
            if not self.kg.graph.has_node(target_resource):
                logger.warning(f"资源不存在: {target_resource}")
                continue
            
            # 获取关联资源
            related = self.kg.get_related_resources(
                target_resource,
                max_depth=request.max_depth,
                relation_filter=request.relation_filter
            )
            
            # 处理结果
            for item in related:
                resource_id = item["resource_id"]
                if resource_id not in processed_resources:
                    processed_resources.add(resource_id)
                    
                    result_item = {
                        "resource_id": resource_id,
                        "kind": item["kind"],
                        "namespace": item["namespace"],
                        "name": item["name"],
                        "relation": item["relation"],
                        "relation_direction": item["relation_direction"],
                        "depth": item["depth"],
                        "source_resource": target_resource
                    }
                    
                    # 添加元数据
                    if request.include_metadata:
                        result_item["metadata"] = item.get("metadata", {})
                    
                    # 添加健康信息
                    if request.include_health_info:
                        result_item["health_status"] = self._get_resource_health(resource_id)
                    
                    all_results.append(result_item)
        
        return self._limit_results(all_results, request.max_results)
    
    def _analyze_impact(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """分析资源影响范围"""
        impact_results = []
        
        for target_resource in request.target_resources:
            if not self.kg.graph.has_node(target_resource):
                continue
            
            # 使用知识图谱的影响分析
            impact_analysis = self.kg.analyze_impact_scope(
                target_resource,
                max_depth=request.max_depth
            )
            
            if "error" in impact_analysis:
                continue
            
            # 分析每个影响级别
            impact_levels = impact_analysis.get("impact_levels", {})
            for level, resources in impact_levels.items():
                for resource in resources:
                    result_item = {
                        "source_resource": target_resource,
                        "affected_resource": resource["resource_id"],
                        "kind": resource["kind"],
                        "namespace": resource["namespace"],
                        "name": resource["name"],
                        "impact_level": resource["impact_level"],
                        "relation": resource["relation"],
                        "risk_score": self._calculate_impact_risk_score(resource)
                    }
                    
                    # 添加健康信息
                    if request.include_health_info:
                        result_item["current_health"] = self._get_resource_health(resource["resource_id"])
                        result_item["impact_severity"] = self._assess_impact_severity(
                            target_resource, resource["resource_id"]
                        )
                    
                    impact_results.append(result_item)
        
        # 按风险分数排序
        impact_results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        return self._limit_results(impact_results, request.max_results)
    
    def _trace_dependencies(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """追踪资源依赖链"""
        dependency_results = []
        
        for target_resource in request.target_resources:
            if not self.kg.graph.has_node(target_resource):
                continue
            
            # 使用知识图谱的依赖追踪
            dependency_analysis = self.kg.trace_dependency_chain(
                target_resource,
                max_depth=request.max_depth
            )
            
            if "error" in dependency_analysis:
                continue
            
            # 分析每个依赖级别
            for level, dependencies in dependency_analysis.get("dependency_levels", {}).items():
                for dependency in dependencies:
                    result_item = {
                        "target_resource": target_resource,
                        "dependency_resource": dependency["resource_id"],
                        "kind": dependency["kind"],
                        "namespace": dependency["namespace"],
                        "name": dependency["name"],
                        "dependency_level": dependency["dependency_level"],
                        "relation": dependency["relation"],
                        "criticality": self._assess_dependency_criticality(dependency)
                    }
                    
                    # 添加健康信息
                    if request.include_health_info:
                        result_item["dependency_health"] = self._get_resource_health(dependency["resource_id"])
                        result_item["failure_risk"] = self._assess_dependency_failure_risk(
                            target_resource, dependency["resource_id"]
                        )
                    
                    dependency_results.append(result_item)
        
        # 按关键性排序
        dependency_results.sort(key=lambda x: x.get("criticality", 0), reverse=True)
        return self._limit_results(dependency_results, request.max_results)
    
    def _analyze_failure_propagation(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """分析故障传播路径"""
        propagation_results = []
        
        for failed_resource in request.target_resources:
            if not self.kg.graph.has_node(failed_resource):
                continue
            
            # 获取所有可能受影响的资源
            impact_analysis = self.kg.analyze_impact_scope(
                failed_resource,
                max_depth=request.max_depth
            )
            
            if "error" in impact_analysis:
                continue
            
            # 分析传播路径
            propagation_paths = self._calculate_propagation_paths(
                failed_resource, 
                impact_analysis.get("impact_levels", {}),
                request.max_depth
            )
            
            for path in propagation_paths:
                result_item = {
                    "source_failure": failed_resource,
                    "propagation_path": path["path"],
                    "target_resource": path["target"],
                    "propagation_probability": path["probability"],
                    "estimated_time_to_impact": path["time_estimate"],
                    "severity": path["severity"],
                    "mitigation_suggestions": path.get("mitigations", [])
                }
                
                propagation_results.append(result_item)
        
        # 按传播概率和严重性排序
        propagation_results.sort(
            key=lambda x: (x.get("propagation_probability", 0), x.get("severity", 0)),
            reverse=True
        )
        return self._limit_results(propagation_results, request.max_results)
    
    def _find_resource_path(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """查找资源之间的路径"""
        if len(request.target_resources) < 2:
            return []
        
        source = request.target_resources[0]
        target = request.target_resources[1]
        
        paths = self._find_shortest_paths(source, target, request.max_depth)
        
        path_results = []
        for path in paths:
            result_item = {
                "source_resource": source,
                "target_resource": target,
                "path": path["path"],
                "path_length": len(path["path"]) - 1,
                "relations": path["relations"],
                "path_strength": path.get("strength", 0)
            }
            path_results.append(result_item)
        
        return path_results
    
    def _discover_cluster_topology(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """发现集群拓扑结构"""
        topology_results = []
        
        # 获取额外参数
        extra_params = getattr(request, 'extra_params', {})
        focus_namespace = extra_params.get('focus_namespace')
        resource_types = extra_params.get('resource_types')
        
        # 分析节点层级
        nodes = self._get_cluster_nodes()
        for node in nodes:
            # 获取节点上的Pod
            hosted_pods = self._get_pods_on_node(node["resource_id"])
            
            node_info = {
                "level": "node",
                "resource_id": node["resource_id"],
                "kind": "node",
                "name": node["name"],
                "hosted_resources": len(hosted_pods),
                "resources": hosted_pods,
                "health_status": self._get_resource_health(node["resource_id"])
            }
            
            if not focus_namespace or any(pod.get("namespace") == focus_namespace for pod in hosted_pods):
                topology_results.append(node_info)
        
        # 分析命名空间层级
        namespaces = self._get_cluster_namespaces(focus_namespace)
        for namespace in namespaces:
            namespace_resources = self._get_namespace_resources(
                namespace["name"], 
                resource_types
            )
            
            namespace_info = {
                "level": "namespace",
                "resource_id": namespace["resource_id"],
                "kind": "namespace",
                "name": namespace["name"],
                "total_resources": len(namespace_resources),
                "resource_breakdown": self._categorize_resources(namespace_resources),
                "health_summary": self._get_namespace_health_summary(namespace["name"])
            }
            
            topology_results.append(namespace_info)
        
        return topology_results
    
    def _analyze_anomaly_correlation(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """分析异常关联性"""
        if not self.summary_gen:
            logger.warning("无摘要生成器，无法执行异常关联分析")
            return []
        
        correlation_results = []
        
        # 获取异常资源
        abnormal_resources = self.summary_gen._detect_abnormal_resources()
        
        # 分析目标资源的异常关联
        for target_resource in request.target_resources:
            if not self.kg.graph.has_node(target_resource):
                continue
            
            # 获取相关资源
            related = self.kg.get_related_resources(
                target_resource,
                max_depth=request.max_depth
            )
            
            # 检查相关资源中的异常
            correlated_anomalies = []
            for abnormal in abnormal_resources:
                abnormal_id = abnormal["resource_id"]
                
                # 检查是否在相关资源中
                for rel in related:
                    if rel["resource_id"] == abnormal_id:
                        correlation = {
                            "anomaly_resource": abnormal_id,
                            "anomaly_severity": abnormal["severity"],
                            "anomaly_issues": abnormal["issues"],
                            "relation_to_target": rel["relation"],
                            "relation_depth": rel["depth"],
                            "correlation_strength": self._calculate_correlation_strength(
                                target_resource, abnormal_id, rel
                            )
                        }
                        correlated_anomalies.append(correlation)
            
            if correlated_anomalies:
                result_item = {
                    "target_resource": target_resource,
                    "correlated_anomalies": correlated_anomalies,
                    "total_correlations": len(correlated_anomalies),
                    "max_severity": max(c["anomaly_severity"] for c in correlated_anomalies),
                    "analysis_timestamp": datetime.now().isoformat()
                }
                correlation_results.append(result_item)
        
        return correlation_results
    
    def _calculate_propagation_paths(self, source: str, impact_levels: Dict, 
                                   max_depth: int) -> List[Dict]:
        """计算故障传播路径"""
        paths = []
        
        for level, resources in impact_levels.items():
            for resource in resources:
                target_id = resource["resource_id"]
                
                # 计算传播概率（基于关系类型和距离）
                probability = self._calculate_propagation_probability(
                    source, target_id, resource["relation"], resource["impact_level"]
                )
                
                # 估算传播时间
                time_estimate = self._estimate_propagation_time(
                    resource["relation"], resource["impact_level"]
                )
                
                # 评估严重性
                severity = self._assess_propagation_severity(source, target_id)
                
                path = {
                    "path": [source, target_id],
                    "target": target_id,
                    "probability": probability,
                    "time_estimate": time_estimate,
                    "severity": severity,
                    "mitigations": self._suggest_mitigations(source, target_id)
                }
                paths.append(path)
        
        return paths
    
    def _find_shortest_paths(self, source: str, target: str, 
                           max_depth: int) -> List[Dict]:
        """查找最短路径"""
        if not self.kg.graph.has_node(source) or not self.kg.graph.has_node(target):
            return []
        
        # 使用BFS查找最短路径
        queue = deque([(source, [source], [])])
        visited = set()
        paths = []
        min_length = float('inf')
        
        while queue:
            current, path, relations = queue.popleft()
            
            if len(path) > max_depth + 1:
                continue
            
            if current == target:
                if len(path) <= min_length:
                    if len(path) < min_length:
                        min_length = len(path)
                        paths = []
                    
                    path_info = {
                        "path": path,
                        "relations": relations,
                        "strength": self._calculate_path_strength(path, relations)
                    }
                    paths.append(path_info)
                continue
            
            if current in visited:
                continue
            visited.add(current)
            
            # 探索邻居节点
            for neighbor in self.kg.graph.neighbors(current):
                if neighbor not in path:  # 避免循环
                    edge_data = self.kg.graph.get_edge_data(current, neighbor)
                    relation = edge_data.get("relation", "unknown")
                    
                    new_path = path + [neighbor]
                    new_relations = relations + [relation]
                    queue.append((neighbor, new_path, new_relations))
        
        return paths[:5]  # 返回最多5条路径
    
    def _get_cluster_nodes(self) -> List[Dict]:
        """获取集群节点"""
        nodes = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("kind") == "node":
                nodes.append({
                    "resource_id": node_id,
                    "name": data.get("name", "unknown"),
                    "metadata": data.get("metadata", {})
                })
        return nodes
    
    def _get_pods_on_node(self, node_id: str) -> List[Dict]:
        """获取节点上的Pod"""
        pods = []
        for successor in self.kg.graph.successors(node_id):
            data = self.kg.graph.nodes[successor]
            if data.get("kind") == "pod":
                pods.append({
                    "resource_id": successor,
                    "name": data.get("name", "unknown"),
                    "namespace": data.get("namespace", "unknown"),
                    "metadata": data.get("metadata", {})
                })
        return pods
    
    def _get_cluster_namespaces(self, focus_namespace: str = None) -> List[Dict]:
        """获取集群命名空间"""
        namespaces = []
        seen_namespaces = set()
        
        for node_id, data in self.kg.graph.nodes(data=True):
            namespace = data.get("namespace")
            if namespace and namespace not in seen_namespaces:
                if not focus_namespace or namespace == focus_namespace:
                    namespaces.append({
                        "resource_id": f"namespace/{namespace}",
                        "name": namespace
                    })
                    seen_namespaces.add(namespace)
        
        return namespaces
    
    def _get_namespace_resources(self, namespace: str, 
                               resource_types: List[str] = None) -> List[Dict]:
        """获取命名空间内的资源"""
        resources = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("namespace") == namespace:
                kind = data.get("kind", "unknown")
                if not resource_types or kind in resource_types:
                    resources.append({
                        "resource_id": node_id,
                        "kind": kind,
                        "name": data.get("name", "unknown"),
                        "metadata": data.get("metadata", {})
                    })
        return resources
    
    def _categorize_resources(self, resources: List[Dict]) -> Dict[str, int]:
        """分类统计资源"""
        breakdown = defaultdict(int)
        for resource in resources:
            breakdown[resource["kind"]] += 1
        return dict(breakdown)
    
    def _get_namespace_health_summary(self, namespace: str) -> Dict:
        """获取命名空间健康摘要"""
        if not self.summary_gen:
            return {"status": "unknown", "message": "无摘要生成器"}
        
        # 生成命名空间资源摘要
        summary = self.summary_gen.generate_resource_summary("pod", namespace=namespace)
        
        return {
            "total_pods": summary.get("total_count", 0),
            "abnormal_pods": summary.get("abnormal_count", 0),
            "health_score": summary.get("key_metrics", {}).get("health_score", 0)
        }
    
    def _get_resource_health(self, resource_id: str) -> str:
        """获取资源健康状态"""
        if not self.kg.graph.has_node(resource_id):
            return "unknown"
        
        data = self.kg.graph.nodes[resource_id]
        kind = data.get("kind", "unknown")
        metadata = data.get("metadata", {})
        
        if kind == "pod":
            phase = metadata.get("phase", "Unknown")
            restart_count = metadata.get("restart_count", 0)
            
            if phase == "Running" and restart_count < 5:
                return "healthy"
            elif phase in ["Failed", "CrashLoopBackOff"]:
                return "critical"
            else:
                return "warning"
        
        elif kind == "deployment":
            replicas = metadata.get("replicas", 0)
            ready = metadata.get("ready_replicas", 0)
            
            if ready >= replicas:
                return "healthy"
            elif ready == 0:
                return "critical"
            else:
                return "warning"
        
        elif kind == "node":
            ready = metadata.get("ready", True)
            return "healthy" if ready else "critical"
        
        return "unknown"
    
    def _calculate_impact_risk_score(self, resource: Dict) -> float:
        """计算影响风险分数"""
        base_score = resource.get("impact_level", 1) * 10
        
        # 根据资源类型调整
        kind = resource.get("kind", "unknown")
        if kind == "node":
            base_score *= 2.0
        elif kind == "deployment":
            base_score *= 1.5
        elif kind == "service":
            base_score *= 1.3
        
        return min(base_score, 100.0)
    
    def _assess_impact_severity(self, source: str, target: str) -> str:
        """评估影响严重性"""
        source_health = self._get_resource_health(source)
        target_health = self._get_resource_health(target)
        
        if source_health == "critical":
            return "high" if target_health == "healthy" else "critical"
        elif source_health == "warning":
            return "medium"
        else:
            return "low"
    
    def _assess_dependency_criticality(self, dependency: Dict) -> float:
        """评估依赖关键性"""
        base_criticality = (4 - dependency.get("dependency_level", 1)) * 25
        
        # 根据资源类型调整
        kind = dependency.get("kind", "unknown")
        if kind in ["database", "storage"]:
            base_criticality *= 1.5
        elif kind in ["service", "ingress"]:
            base_criticality *= 1.2
        
        return min(base_criticality, 100.0)
    
    def _assess_dependency_failure_risk(self, target: str, dependency: str) -> str:
        """评估依赖故障风险"""
        dep_health = self._get_resource_health(dependency)
        
        if dep_health == "critical":
            return "high"
        elif dep_health == "warning":
            return "medium"
        else:
            return "low"
    
    def _calculate_propagation_probability(self, source: str, target: str,
                                         relation: str, depth: int) -> float:
        """计算传播概率"""
        # 基础概率随深度递减
        base_prob = max(0.1, 1.0 - (depth - 1) * 0.2)
        
        # 根据关系类型调整
        relation_multiplier = {
            "ownedBy": 0.9,
            "routes": 0.8,
            "hosts": 0.7,
            "dependsOn": 0.85
        }.get(relation, 0.5)
        
        return min(base_prob * relation_multiplier, 1.0)
    
    def _estimate_propagation_time(self, relation: str, depth: int) -> str:
        """估算传播时间"""
        base_time = depth * 30  # 每层30秒
        
        if relation in ["ownedBy", "routes"]:
            base_time *= 0.5  # 快速传播
        elif relation == "hosts":
            base_time *= 2.0  # 较慢传播
        
        if base_time < 60:
            return f"{int(base_time)}秒"
        elif base_time < 3600:
            return f"{int(base_time/60)}分钟"
        else:
            return f"{int(base_time/3600)}小时"
    
    def _assess_propagation_severity(self, source: str, target: str) -> str:
        """评估传播严重性"""
        target_data = self.kg.graph.nodes.get(target, {})
        target_kind = target_data.get("kind", "unknown")
        
        if target_kind == "node":
            return "critical"
        elif target_kind in ["deployment", "service"]:
            return "high"
        elif target_kind == "pod":
            return "medium"
        else:
            return "low"
    
    def _suggest_mitigations(self, source: str, target: str) -> List[str]:
        """建议缓解措施"""
        mitigations = []
        
        target_data = self.kg.graph.nodes.get(target, {})
        target_kind = target_data.get("kind", "unknown")
        
        if target_kind == "pod":
            mitigations.extend([
                "增加Pod副本数",
                "配置Pod反亲和性",
                "设置资源限制"
            ])
        elif target_kind == "deployment":
            mitigations.extend([
                "配置滚动更新策略",
                "设置健康检查",
                "增加副本数"
            ])
        elif target_kind == "service":
            mitigations.extend([
                "配置多个后端Pod",
                "设置会话亲和性",
                "启用负载均衡"
            ])
        
        return mitigations
    
    def _calculate_path_strength(self, path: List[str], 
                                relations: List[str]) -> float:
        """计算路径强度"""
        if not relations:
            return 0.0
        
        # 基于关系类型的强度映射
        strength_map = {
            "ownedBy": 0.9,
            "routes": 0.8,
            "hosts": 0.7,
            "dependsOn": 0.85,
            "connects": 0.6
        }
        
        total_strength = 0.0
        for relation in relations:
            total_strength += strength_map.get(relation, 0.5)
        
        return total_strength / len(relations)
    
    def _calculate_correlation_strength(self, target: str, anomaly: str, 
                                      relation: Dict) -> float:
        """计算异常关联强度"""
        base_strength = 1.0 - (relation["depth"] - 1) * 0.2
        
        # 根据关系类型调整
        relation_multiplier = {
            "ownedBy": 0.9,
            "routes": 0.8,
            "hosts": 0.7,
            "dependsOn": 0.85
        }.get(relation["relation"], 0.5)
        
        return min(base_strength * relation_multiplier, 1.0)
    
    def _validate_request(self, request: QueryRequest):
        """验证查询请求"""
        if not request.target_resources and request.query_type != QueryType.CLUSTER_TOPOLOGY:
            raise ValueError("目标资源列表不能为空")
        
        if request.max_depth <= 0 or request.max_depth > 10:
            raise ValueError("查询深度必须在1-10之间")
        
        if request.max_results <= 0 or request.max_results > self.max_results_limit:
            raise ValueError(f"结果数量限制必须在1-{self.max_results_limit}之间")
    
    def _generate_query_id(self) -> str:
        """生成查询ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _generate_cache_key(self, request: QueryRequest) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{request.query_type.value}:{','.join(sorted(request.target_resources))}:{request.max_depth}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[QueryResult]:
        """获取缓存结果"""
        if cache_key in self.query_cache:
            cached_item = self.query_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["result"]
            else:
                del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: QueryResult):
        """缓存查询结果"""
        self.query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        # 简单的缓存清理（保持最多100个条目）
        if len(self.query_cache) > 100:
            # 删除最旧的条目
            oldest_key = min(
                self.query_cache.keys(),
                key=lambda k: self.query_cache[k]["timestamp"]
            )
            del self.query_cache[oldest_key]
    
    def _generate_metadata(self, request: QueryRequest, 
                          execution_time: float) -> Dict[str, Any]:
        """生成查询元数据"""
        return {
            "query_depth": request.max_depth,
            "execution_time": execution_time,
            "result_limit": request.max_results,
            "include_metadata": request.include_metadata,
            "include_health_info": request.include_health_info,
            "graph_stats": {
                "total_nodes": len(self.kg.graph.nodes),
                "total_edges": len(self.kg.graph.edges)
            }
        }
    
    def _limit_results(self, results: List[Dict], max_results: int) -> List[Dict]:
        """限制结果数量"""
        if len(results) > max_results:
            logger.warning(f"结果数量 {len(results)} 超过限制 {max_results}，截取前 {max_results} 个")
            return results[:max_results]
        return results
    
    def _create_error_result(self, query_id: str, request: QueryRequest,
                           error_message: str, execution_time: float) -> QueryResult:
        """创建错误结果"""
        return QueryResult(
            query_id=query_id,
            query_type=request.query_type,
            target_resources=request.target_resources,
            results=[],
            metadata={"error": error_message},
            execution_time=execution_time,
            timestamp=datetime.now().isoformat(),
            success=False,
            error_message=error_message
        )
    
    def _update_stats(self, request: QueryRequest, execution_time: float, 
                     success: bool):
        """更新查询统计"""
        self.stats["queries_executed"] += 1
        
        if success:
            # 更新平均执行时间
            total_time = self.stats["avg_execution_time"] * (self.stats["queries_executed"] - 1)
            self.stats["avg_execution_time"] = (total_time + execution_time) / self.stats["queries_executed"]
            
            # 更新查询类型统计
            self.stats["queries_by_type"][request.query_type.value] += 1
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return self.stats.copy()
    
    def clear_cache(self):
        """清空查询缓存"""
        self.query_cache.clear()
        logger.info("查询缓存已清空")
    
    def clear_stats(self):
        """清空查询统计"""
        self.stats = {
            "queries_executed": 0,
            "avg_execution_time": 0.0,
            "queries_by_type": defaultdict(int),
            "cache_hits": 0,
            "timeouts": 0,
            "errors": 0
        }
        logger.info("查询统计已清空")