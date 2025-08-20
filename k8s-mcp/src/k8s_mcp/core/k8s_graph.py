"""
K8s知识图谱模块

使用NetworkX构建K8s资源关系图，支持：
- 资源节点管理
- 关系建立和查询
- 深度遍历
- 内存管理和TTL
- 线程安全操作
- 全局单例模式（共享实例）
"""

import networkx as nx
import threading
import time
import weakref
from typing import Dict, List, Optional, Set, Tuple, Any
from loguru import logger
from collections import defaultdict


# 集群级别资源类型定义
CLUSTER_SCOPED_RESOURCES = {
    'node', 'namespace', 'persistentvolume', 'clusterrole', 
    'clusterrolebinding', 'storageclass', 'customresourcedefinition',
    'priorityclass', 'volumeattachment', 'certificatesigningrequest',
    'lease', 'runtimeclass', 'podtemplate', 'componentstatus',
    'apiservice', 'mutatingwebhookconfiguration', 'validatingwebhookconfiguration'
}


class K8sKnowledgeGraph:
    """K8s知识图谱
    
    使用有向图存储K8s资源及其关系，提供高效的关联查询能力。
    支持线程安全的并发操作，自动内存管理和过期清理。
    """
    
    def __init__(self, config=None):
        """初始化知识图谱
        
        Args:
            config: 配置对象，包含TTL、内存限制等参数
        """
        self.graph = nx.DiGraph()
        self.lock = threading.RLock()  # 支持重入锁
        self.last_updated = 0
        self.config = config
        
        # 内存管理
        self._node_timestamps = {}
        self._memory_usage = 0
        
        # 性能统计
        self.stats = {
            "nodes_total": 0,
            "edges_total": 0,
            "queries_total": 0,
            "cache_hits": 0,
            "cleanup_runs": 0
        }
        
        logger.info("K8s知识图谱初始化完成")
    
    def add_resource(self, kind: str, namespace: str, name: str, 
                    metadata: dict = None, labels: dict = None) -> str:
        """添加资源节点
        
        Args:
            kind: 资源类型（pod, deployment, service等）
            namespace: 命名空间（集群级别资源可以为None）
            name: 资源名称
            metadata: 资源元数据
            labels: 资源标签
            
        Returns:
            str: 节点ID
        """
        # 集群级别资源没有命名空间
        if kind.lower() in CLUSTER_SCOPED_RESOURCES:
            namespace = None
            node_id = f"{kind}/{name}"
        else:
            # 命名空间级别资源
            if namespace is None:
                namespace = "default"
            node_id = f"{kind}/{namespace}/{name}"
        current_time = time.time()
        
        with self.lock:
            # 检查内存限制
            if self._check_memory_limit():
                self.cleanup_expired_nodes()
            
            # 添加或更新节点
            self.graph.add_node(
                node_id,
                kind=kind,
                namespace=namespace,
                name=name,
                metadata=metadata or {},
                labels=labels or {},
                last_updated=current_time,
                created_at=current_time if node_id not in self.graph else 
                          self.graph.nodes[node_id].get('created_at', current_time)
            )
            
            self._node_timestamps[node_id] = current_time
            self.stats["nodes_total"] = len(self.graph.nodes)
            
            logger.debug(f"添加资源节点: {node_id}")
            return node_id
    
    def add_relation(self, source: str, target: str, relation_type: str, 
                    metadata: dict = None) -> bool:
        """添加资源关系
        
        Args:
            source: 源节点ID
            target: 目标节点ID
            relation_type: 关系类型（ownedBy, manages, routes等）
            metadata: 关系元数据
            
        Returns:
            bool: 是否成功添加
        """
        with self.lock:
            # 验证节点存在
            if source not in self.graph or target not in self.graph:
                logger.warning(f"关系添加失败：节点不存在 {source} -> {target}")
                return False
            
            # 添加边
            self.graph.add_edge(
                source, target,
                relation=relation_type,
                metadata=metadata or {},
                created_at=time.time()
            )
            
            self.stats["edges_total"] = len(self.graph.edges)
            logger.debug(f"添加关系: {source} --{relation_type}--> {target}")
            return True
    
    def get_related_resources(self, resource_id: str, max_depth: int = 2,
                             relation_filter: Set[str] = None) -> List[Dict]:
        """获取关联资源（带深度限制和关系过滤）
        
        Args:
            resource_id: 资源ID
            max_depth: 最大遍历深度
            relation_filter: 关系类型过滤器
            
        Returns:
            List[Dict]: 关联资源列表
        """
        with self.lock:
            self.stats["queries_total"] += 1
            
            if resource_id not in self.graph:
                logger.warning(f"资源不存在: {resource_id}")
                return []
            
            results = []
            visited = set()
            result_nodes = set()  # 跟踪已添加到结果的节点，避免重复
            queue = [(resource_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth > max_depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # 获取出边（当前节点指向的节点）
                for neighbor in self.graph.successors(current_id):
                    edge_data = self.graph.get_edge_data(current_id, neighbor)
                    relation = edge_data.get("relation", "unknown")
                    
                    # 应用关系过滤器
                    if relation_filter and relation not in relation_filter:
                        continue
                    
                    # 避免重复添加同一个节点（但允许不同深度的相同节点）
                    result_key = (neighbor, depth + 1, "outgoing", relation)
                    if result_key not in result_nodes:
                        neighbor_data = self.graph.nodes[neighbor]
                        results.append({
                            "resource_id": neighbor,
                            "kind": neighbor_data.get("kind", "unknown"),
                            "namespace": neighbor_data.get("namespace", "unknown"),
                            "name": neighbor_data.get("name", "unknown"),
                            "relation": relation,
                            "relation_direction": "outgoing",
                            "depth": depth + 1,
                            "metadata": neighbor_data.get("metadata", {})
                        })
                        result_nodes.add(result_key)
                    
                    if depth + 1 < max_depth:
                        queue.append((neighbor, depth + 1))
                
                # 获取入边（指向当前节点的节点）
                for predecessor in self.graph.predecessors(current_id):
                    edge_data = self.graph.get_edge_data(predecessor, current_id)
                    relation = edge_data.get("relation", "unknown")
                    
                    if relation_filter and relation not in relation_filter:
                        continue
                    
                    # 避免重复添加同一个节点
                    result_key = (predecessor, depth + 1, "incoming", relation)
                    if result_key not in result_nodes:
                        predecessor_data = self.graph.nodes[predecessor]
                        results.append({
                            "resource_id": predecessor,
                            "kind": predecessor_data.get("kind", "unknown"),
                            "namespace": predecessor_data.get("namespace", "unknown"),
                            "name": predecessor_data.get("name", "unknown"),
                            "relation": relation,
                            "relation_direction": "incoming",
                            "depth": depth + 1,
                            "metadata": predecessor_data.get("metadata", {})
                        })
                        result_nodes.add(result_key)
                    
                    if depth + 1 < max_depth:
                        queue.append((predecessor, depth + 1))
            
            logger.debug(f"关联查询完成: {resource_id}, 找到 {len(results)} 个关联资源")
            return results
    
    def analyze_impact_scope(self, resource_id: str, max_depth: int = 3) -> Dict:
        """分析资源影响范围（下游依赖分析）
        
        Args:
            resource_id: 资源ID
            max_depth: 最大分析深度
            
        Returns:
            Dict: 影响范围分析结果
        """
        with self.lock:
            if resource_id not in self.graph:
                return {"error": f"资源不存在: {resource_id}"}
            
            affected_resources = []
            visited = set()
            queue = [(resource_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # 只分析出边（下游依赖）
                for neighbor in self.graph.successors(current_id):
                    edge_data = self.graph.get_edge_data(current_id, neighbor)
                    neighbor_data = self.graph.nodes[neighbor]
                    
                    affected_resources.append({
                        "resource_id": neighbor,
                        "kind": neighbor_data.get("kind"),
                        "namespace": neighbor_data.get("namespace"),
                        "name": neighbor_data.get("name"),
                        "relation": edge_data.get("relation"),
                        "impact_level": depth + 1
                    })
                    
                    queue.append((neighbor, depth + 1))
            
            # 按影响级别分组
            impact_levels = {}
            for resource in affected_resources:
                level = resource["impact_level"]
                if level not in impact_levels:
                    impact_levels[level] = []
                impact_levels[level].append(resource)
            
            return {
                "source_resource": resource_id,
                "total_affected": len(affected_resources),
                "impact_levels": impact_levels,
                "max_depth_reached": max([r["impact_level"] for r in affected_resources]) if affected_resources else 0
            }
    
    def trace_dependency_chain(self, resource_id: str, max_depth: int = 3) -> Dict:
        """追踪依赖链（上游依赖分析）
        
        Args:
            resource_id: 资源ID
            max_depth: 最大追踪深度
            
        Returns:
            Dict: 依赖链分析结果
        """
        with self.lock:
            if resource_id not in self.graph:
                return {"error": f"资源不存在: {resource_id}"}
            
            dependency_chain = []
            visited = set()
            queue = [(resource_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth or current_id in visited:
                    continue
                
                visited.add(current_id)
                
                # 只分析入边（上游依赖）
                for predecessor in self.graph.predecessors(current_id):
                    edge_data = self.graph.get_edge_data(predecessor, current_id)
                    predecessor_data = self.graph.nodes[predecessor]
                    
                    dependency_chain.append({
                        "resource_id": predecessor,
                        "kind": predecessor_data.get("kind"),
                        "namespace": predecessor_data.get("namespace"),
                        "name": predecessor_data.get("name"),
                        "relation": edge_data.get("relation"),
                        "dependency_level": depth + 1
                    })
                    
                    queue.append((predecessor, depth + 1))
            
            # 按依赖级别分组
            dependency_levels = {}
            for resource in dependency_chain:
                level = resource["dependency_level"]
                if level not in dependency_levels:
                    dependency_levels[level] = []
                dependency_levels[level].append(resource)
            
            return {
                "target_resource": resource_id,
                "total_dependencies": len(dependency_chain),
                "dependency_levels": dependency_levels,
                "max_depth_reached": max([r["dependency_level"] for r in dependency_chain]) if dependency_chain else 0
            }
    
    def find_resources_by_labels(self, label_selectors: Dict[str, str], 
                                namespace: str = None) -> List[str]:
        """根据标签选择器查找资源
        
        Args:
            label_selectors: 标签选择器字典
            namespace: 限制命名空间，None表示所有命名空间
            
        Returns:
            List[str]: 匹配的资源ID列表
        """
        with self.lock:
            matching_resources = []
            
            for node_id, data in self.graph.nodes(data=True):
                # 检查命名空间过滤
                if namespace and data.get("namespace") != namespace:
                    continue
                
                # 检查标签匹配
                node_labels = data.get("labels", {})
                if all(node_labels.get(k) == v for k, v in label_selectors.items()):
                    matching_resources.append(node_id)
            
            logger.debug(f"标签查询完成: {label_selectors}, 找到 {len(matching_resources)} 个资源")
            return matching_resources
    
    def cleanup_expired_nodes(self, ttl_seconds: int = None) -> int:
        """清理过期节点
        
        Args:
            ttl_seconds: TTL时间，默认使用配置值
            
        Returns:
            int: 清理的节点数量
        """
        if ttl_seconds is None:
            ttl_seconds = self.config.graph_ttl if self.config else 3600
        
        current_time = time.time()
        expired_nodes = []
        
        with self.lock:
            for node_id, timestamp in self._node_timestamps.items():
                if current_time - timestamp > ttl_seconds:
                    expired_nodes.append(node_id)
            
            # 移除过期节点
            for node_id in expired_nodes:
                if node_id in self.graph:
                    self.graph.remove_node(node_id)
                if node_id in self._node_timestamps:
                    del self._node_timestamps[node_id]
            
            # 更新统计
            self.stats["nodes_total"] = len(self.graph.nodes)
            self.stats["edges_total"] = len(self.graph.edges)
            self.stats["cleanup_runs"] += 1
        
        if expired_nodes:
            logger.info(f"清理过期节点: {len(expired_nodes)} 个")
        
        return len(expired_nodes)
    
    def get_resource_details(self, resource_id: str) -> Optional[Dict]:
        """获取资源详细信息
        
        Args:
            resource_id: 资源ID
            
        Returns:
            Optional[Dict]: 资源详细信息，不存在则返回None
        """
        with self.lock:
            if resource_id not in self.graph:
                return None
            
            node_data = self.graph.nodes[resource_id]
            in_degree = self.graph.in_degree(resource_id)
            out_degree = self.graph.out_degree(resource_id)
            
            return {
                "resource_id": resource_id,
                "kind": node_data.get("kind", "unknown"),
                "namespace": node_data.get("namespace", "unknown"),
                "name": node_data.get("name", "unknown"),
                "metadata": node_data.get("metadata", {}),
                "labels": node_data.get("labels", {}),
                "created_at": node_data.get("created_at", 0),
                "last_updated": node_data.get("last_updated", 0),
                "in_degree": in_degree,
                "out_degree": out_degree,
                "total_relations": in_degree + out_degree
            }
    
    def remove_resource(self, resource_id: str) -> bool:
        """移除资源节点
        
        Args:
            resource_id: 资源ID
            
        Returns:
            bool: 是否成功移除
        """
        with self.lock:
            if resource_id not in self.graph:
                logger.warning(f"资源不存在，无法移除: {resource_id}")
                return False
            
            # 移除节点（会自动移除相关的边）
            self.graph.remove_node(resource_id)
            
            # 清理时间戳记录
            if resource_id in self._node_timestamps:
                del self._node_timestamps[resource_id]
            
            # 更新统计
            self.stats["nodes_total"] = len(self.graph.nodes)
            self.stats["edges_total"] = len(self.graph.edges)
            
            logger.debug(f"移除资源节点: {resource_id}")
            return True
    
    def _check_memory_limit(self) -> bool:
        """检查内存使用是否超限"""
        if not self.config:
            return False
        
        # 简单估算：每个节点约1KB，每条边约0.5KB
        estimated_memory = (len(self.graph.nodes) * 1 + len(self.graph.edges) * 0.5) / 1024  # MB
        return estimated_memory > self.config.graph_memory_limit
    
    def get_statistics(self) -> Dict:
        """获取图统计信息"""
        with self.lock:
            return {
                "nodes_total": len(self.graph.nodes),
                "edges_total": len(self.graph.edges),
                "queries_total": self.stats["queries_total"],
                "cache_hits": self.stats["cache_hits"],
                "cleanup_runs": self.stats["cleanup_runs"],
                "last_updated": self.last_updated,
                "memory_estimate_mb": (len(self.graph.nodes) * 1 + len(self.graph.edges) * 0.5) / 1024
            }
    
    def get_namespace_summary(self) -> Dict[str, Dict]:
        """获取命名空间摘要统计"""
        with self.lock:
            namespace_stats = defaultdict(lambda: {"total": 0, "by_kind": defaultdict(int)})
            cluster_stats = {"total": 0, "by_kind": defaultdict(int)}
            
            for node_id, data in self.graph.nodes(data=True):
                kind = data.get("kind", "unknown")
                namespace = data.get("namespace", "unknown")
                
                # 检查是否为集群级别资源
                if kind.lower() in CLUSTER_SCOPED_RESOURCES:
                    cluster_stats["total"] += 1
                    cluster_stats["by_kind"][kind] += 1
                else:
                    # 命名空间级别资源
                    namespace_stats[namespace]["total"] += 1
                    namespace_stats[namespace]["by_kind"][kind] += 1
            
            # 转换为普通字典
            result = {}
            for ns, stats in namespace_stats.items():
                result[ns] = {
                    "total": stats["total"],
                    "by_kind": dict(stats["by_kind"])
                }
            
            # 添加集群级别资源统计
            if cluster_stats["total"] > 0:
                result["cluster-scoped"] = {
                    "total": cluster_stats["total"],
                    "by_kind": dict(cluster_stats["by_kind"])
                }
            
            return result
    
    def clear(self):
        """清空图数据"""
        with self.lock:
            self.graph.clear()
            self._node_timestamps.clear()
            self.stats = {
                "nodes_total": 0, 
                "edges_total": 0, 
                "queries_total": 0, 
                "cache_hits": 0,
                "cleanup_runs": 0
            }
            logger.info("知识图谱已清空")
    
    def export_graph_data(self) -> Dict:
        """导出图数据（用于调试和可视化）"""
        with self.lock:
            nodes = []
            edges = []
            
            # 导出节点
            for node_id, data in self.graph.nodes(data=True):
                nodes.append({
                    "id": node_id,
                    "kind": data.get("kind", "unknown"),
                    "namespace": data.get("namespace", "unknown"),
                    "name": data.get("name", "unknown"),
                    "metadata": data.get("metadata", {}),
                    "labels": data.get("labels", {}),
                    "created_at": data.get("created_at", 0),
                    "last_updated": data.get("last_updated", 0)
                })
            
            # 导出边
            for source, target, data in self.graph.edges(data=True):
                edges.append({
                    "source": source,
                    "target": target,
                    "relation": data.get("relation", "unknown"),
                    "metadata": data.get("metadata", {}),
                    "created_at": data.get("created_at", 0)
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "statistics": self.get_statistics(),
                "timestamp": time.time()
            }


# 全局知识图谱实例管理
_global_kg_instance: Optional[K8sKnowledgeGraph] = None
_global_kg_lock = threading.Lock()


def get_shared_knowledge_graph(config=None) -> K8sKnowledgeGraph:
    """获取共享的知识图谱实例（单例模式）
    
    Args:
        config: 配置对象，仅在首次创建时使用
        
    Returns:
        K8sKnowledgeGraph: 共享的知识图谱实例
    """
    global _global_kg_instance
    
    with _global_kg_lock:
        if _global_kg_instance is None:
            _global_kg_instance = K8sKnowledgeGraph(config)
            logger.info("创建全局共享知识图谱实例")
        return _global_kg_instance


def reset_shared_knowledge_graph():
    """重置共享的知识图谱实例（主要用于测试）"""
    global _global_kg_instance
    
    with _global_kg_lock:
        if _global_kg_instance:
            _global_kg_instance.clear()
        _global_kg_instance = None
        logger.info("全局共享知识图谱实例已重置")