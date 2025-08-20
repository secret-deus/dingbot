"""
数据摘要生成器

负责K8s集群数据的智能摘要和压缩，包括：
- 智能数据裁剪：确保输出在LLM上下文限制内（<10KB）
- 异常资源检测：识别和优先展示问题资源
- 关键指标提取：计算和展示重要的集群指标
- 上下文优化：为LLM提供最相关的信息
- 优先级排序：根据重要性对资源进行排序
"""

import json
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from .k8s_graph import K8sKnowledgeGraph, CLUSTER_SCOPED_RESOURCES


class SummaryGenerator:
    """数据摘要生成器
    
    负责从K8s知识图谱中生成智能摘要，包括：
    - 异常资源检测和优先级排序
    - 关键指标计算和统计
    - 数据压缩和大小控制
    - 上下文相关性分析
    """

    def __init__(self, knowledge_graph: K8sKnowledgeGraph, config=None):
        """初始化摘要生成器
        
        Args:
            knowledge_graph: 知识图谱实例
            config: 配置对象
        """
        self.kg = knowledge_graph
        self.config = config
        
        # 配置参数
        self.max_summary_size_kb = config.max_summary_size_kb if config else 10
        self.max_summary_bytes = self.max_summary_size_kb * 1024
        
        # 资源优先级配置
        self.resource_priorities = {
            "pod": 10,
            "deployment": 9,
            "service": 8,
            "replicaset": 7,
            "node": 9,
            "namespace": 6
        }
        
        # 异常状态配置
        self.abnormal_conditions = {
            "pod": ["Failed", "Pending", "CrashLoopBackOff", "ImagePullBackOff", "Error"],
            "deployment": ["Progressing", "ReplicaFailure"],
            "node": ["NotReady", "MemoryPressure", "DiskPressure", "PIDPressure", "NetworkUnavailable"]
        }
        
        # 关键字段配置
        self.important_fields = {
            "pod": ["phase", "restart_count", "node_name", "pod_ip"],
            "deployment": ["replicas", "ready_replicas", "available_replicas"],
            "service": ["type", "cluster_ip"],
            "node": ["ready", "kernel_version", "kubelet_version"]
        }
        
        # 性能统计
        self.stats = {
            "summaries_generated": 0,
            "avg_compression_ratio": 0.0,
            "abnormal_resources_detected": 0,
            "last_generation_time": 0
        }
        
        logger.info("数据摘要生成器初始化完成")
    
    def generate_cluster_summary(self, focus_namespace: str = None, 
                                include_details: bool = True) -> Dict[str, Any]:
        """生成集群总体摘要
        
        Args:
            focus_namespace: 重点关注的命名空间
            include_details: 是否包含详细信息
            
        Returns:
            Dict: 集群摘要信息
        """
        start_time = time.time()
        
        try:
            # 收集基础统计
            basic_stats = self._collect_basic_statistics()
            
            # 检测异常资源
            abnormal_resources = self._detect_abnormal_resources()
            
            # 生成关键指标
            key_metrics = self._calculate_key_metrics()
            
            # 收集命名空间统计
            namespace_stats = self._collect_namespace_statistics(focus_namespace)
            
            # 生成资源健康状态
            health_status = self._generate_health_status()
            
            # 组装基础摘要
            summary = {
                "timestamp": datetime.now().isoformat(),
                "cluster_stats": basic_stats,
                "health_status": health_status,
                "key_metrics": key_metrics,
                "namespace_breakdown": namespace_stats,
                "abnormal_resources": abnormal_resources[:10],  # 最多10个异常资源
                "graph_info": {
                    "total_nodes": len(self.kg.graph.nodes),
                    "total_edges": len(self.kg.graph.edges),
                    "last_updated": self.kg.last_updated
                }
            }
            
            # 如果需要详细信息且大小允许，添加更多内容
            if include_details:
                summary = self._add_detailed_information(summary)
            
            # 压缩到指定大小
            final_summary = self._compress_to_size_limit(summary)
            
            # 更新统计
            duration = time.time() - start_time
            self.stats["summaries_generated"] += 1
            self.stats["last_generation_time"] = duration
            self.stats["abnormal_resources_detected"] = len(abnormal_resources)
            
            # 计算压缩比
            original_size = len(json.dumps(summary, ensure_ascii=False))
            final_size = len(json.dumps(final_summary, ensure_ascii=False))
            compression_ratio = final_size / original_size if original_size > 0 else 1.0
            self.stats["avg_compression_ratio"] = (
                self.stats["avg_compression_ratio"] * (self.stats["summaries_generated"] - 1) + 
                compression_ratio
            ) / self.stats["summaries_generated"]
            
            logger.info(f"集群摘要生成完成，耗时 {duration:.2f}s，压缩比 {compression_ratio:.2f}")
            return final_summary
            
        except Exception as e:
            logger.error(f"生成集群摘要失败: {e}")
            return self._generate_error_summary(str(e))
    
    def generate_resource_summary(self, resource_type: str, 
                                 namespace: str = None, 
                                 include_relations: bool = True) -> Dict[str, Any]:
        """生成特定资源类型的摘要
        
        Args:
            resource_type: 资源类型
            namespace: 命名空间过滤
            include_relations: 是否包含关联关系
            
        Returns:
            Dict: 资源摘要信息
        """
        try:
            # 获取指定类型的资源
            resources = self._get_resources_by_type(resource_type, namespace)
            
            if not resources:
                return {
                    "resource_type": resource_type,
                    "namespace": namespace,
                    "total_count": 0,
                    "message": f"未找到 {resource_type} 资源"
                }
            
            # 分析资源状态分布
            status_distribution = self._analyze_status_distribution(resources, resource_type)
            
            # 检测异常资源
            abnormal_resources = [
                res for res in resources 
                if self._is_resource_abnormal(res["resource_id"], resource_type, res["data"])
            ]
            
            # 计算关键指标
            metrics = self._calculate_resource_metrics(resources, resource_type)
            
            # 生成摘要
            summary = {
                "resource_type": resource_type,
                "namespace": namespace,
                "total_count": len(resources),
                "status_distribution": status_distribution,
                "key_metrics": metrics,
                "abnormal_count": len(abnormal_resources),
                "abnormal_resources": abnormal_resources[:5],  # 最多5个异常资源
                "sample_resources": resources[:3] if len(resources) <= 10 else []  # 少量资源时显示全部
            }
            
            # 如果需要关联关系
            if include_relations and len(resources) <= 20:  # 只有资源数量不多时才包含关系
                summary["relationships"] = self._get_resource_relationships(resources)
            
            # 压缩到大小限制
            return self._compress_to_size_limit(summary)
            
        except Exception as e:
            logger.error(f"生成 {resource_type} 资源摘要失败: {e}")
            return self._generate_error_summary(f"生成 {resource_type} 摘要失败: {str(e)}")
    
    def generate_focused_summary(self, focus_resources: List[str], 
                                context_depth: int = 2) -> Dict[str, Any]:
        """生成聚焦于特定资源的摘要
        
        Args:
            focus_resources: 重点关注的资源ID列表
            context_depth: 上下文深度（关联资源的层级）
            
        Returns:
            Dict: 聚焦摘要信息
        """
        try:
            if not focus_resources:
                return {"error": "未提供聚焦资源"}
            
            # 验证资源存在性
            valid_resources = [
                res_id for res_id in focus_resources 
                if self.kg.graph.has_node(res_id)
            ]
            
            if not valid_resources:
                return {"error": "指定的资源不存在"}
            
            # 收集焦点资源信息
            focus_info = []
            all_related_resources = set()
            
            for resource_id in valid_resources:
                resource_data = self.kg.graph.nodes[resource_id]
                
                # 获取关联资源
                related = self.kg.get_related_resources(resource_id, max_depth=context_depth)
                all_related_resources.update([r["resource_id"] for r in related])
                
                # 分析影响范围
                impact_analysis = self.kg.analyze_impact_scope(resource_id, max_depth=context_depth)
                
                # 依赖追踪
                dependency_analysis = self.kg.trace_dependency_chain(resource_id, max_depth=context_depth)
                
                focus_info.append({
                    "resource_id": resource_id,
                    "resource_data": self._filter_important_fields(resource_data),
                    "status": self._determine_resource_status(resource_id, resource_data),
                    "related_count": len(related),
                    "impact_scope": impact_analysis.get("total_affected", 0),
                    "dependency_count": dependency_analysis.get("total_dependencies", 0),
                    "key_relationships": related[:5]  # 最重要的5个关系
                })
            
            # 生成上下文摘要
            context_summary = self._generate_context_summary(list(all_related_resources))
            
            # 生成风险评估
            risk_assessment = self._assess_risks(valid_resources, list(all_related_resources))
            
            summary = {
                "focus_resources": focus_info,
                "context_summary": context_summary,
                "risk_assessment": risk_assessment,
                "total_resources_analyzed": len(valid_resources) + len(all_related_resources),
                "analysis_depth": context_depth,
                "timestamp": datetime.now().isoformat()
            }
            
            return self._compress_to_size_limit(summary)
            
        except Exception as e:
            logger.error(f"生成聚焦摘要失败: {e}")
            return self._generate_error_summary(f"生成聚焦摘要失败: {str(e)}")
    
    def _collect_basic_statistics(self) -> Dict[str, Any]:
        """收集基础统计信息"""
        stats = {}
        
        # 按资源类型统计
        for node_id, data in self.kg.graph.nodes(data=True):
            kind = data.get("kind", "unknown")
            if kind not in stats:
                stats[kind] = 0
            stats[kind] += 1
        
        # 按命名空间统计（正确处理集群级别资源）
        namespace_counts = defaultdict(int)
        for node_id, data in self.kg.graph.nodes(data=True):
            kind = data.get("kind", "unknown")
            namespace = data.get("namespace")
            
            # 集群级别资源使用 cluster-scoped 分类
            if kind.lower() in CLUSTER_SCOPED_RESOURCES:
                namespace_counts["cluster-scoped"] += 1
            else:
                # 命名空间级别资源
                if namespace is None:
                    namespace = "default"
                namespace_counts[namespace] += 1
        
        return {
            "resource_counts": stats,
            "namespace_counts": dict(namespace_counts),
            "total_resources": len(self.kg.graph.nodes),
            "total_relationships": len(self.kg.graph.edges)
        }
    
    def _detect_abnormal_resources(self) -> List[Dict[str, Any]]:
        """检测异常资源"""
        abnormal_resources = []
        
        for node_id, data in self.kg.graph.nodes(data=True):
            kind = data.get("kind", "unknown")
            
            if self._is_resource_abnormal(node_id, kind, data):
                severity_score = self._calculate_severity(kind, data)
                abnormal_info = {
                    "resource_id": node_id,
                    "kind": kind,
                    "namespace": data.get("namespace", "cluster-scope"),
                    "name": data.get("name", "unknown"),
                    "issues": self._identify_resource_issues(kind, data),
                    "severity": severity_score,  # 保持向后兼容
                    "severity_score": severity_score,  # 新的标准字段
                    "last_updated": data.get("last_updated", 0)
                }
                abnormal_resources.append(abnormal_info)
        
        # 按严重程度排序
        abnormal_resources.sort(key=lambda x: x["severity"], reverse=True)
        return abnormal_resources
    
    def _is_resource_abnormal(self, resource_id: str, kind: str, data: Dict) -> bool:
        """判断资源是否异常"""
        metadata = data.get("metadata", {})
        
        if kind == "pod":
            phase = metadata.get("phase", "Unknown")
            restart_count = metadata.get("restart_count", 0)
            
            # 安全地处理None值
            restart_count = restart_count if restart_count is not None else 0
            
            return phase in self.abnormal_conditions.get("pod", []) or restart_count > 5
            
        elif kind == "deployment":
            replicas = metadata.get("replicas", 0)
            ready_replicas = metadata.get("ready_replicas", 0)
            available_replicas = metadata.get("available_replicas", 0)
            
            # 安全地处理None值
            replicas = replicas if replicas is not None else 0
            ready_replicas = ready_replicas if ready_replicas is not None else 0
            available_replicas = available_replicas if available_replicas is not None else 0
            
            return ready_replicas < replicas or available_replicas < replicas
            
        elif kind == "node":
            ready = metadata.get("ready", True)
            return not ready
            
        elif kind == "service":
            # Service通常较少异常，主要检查配置问题
            return False
            
        return False
    
    def _identify_resource_issues(self, kind: str, data: Dict) -> List[str]:
        """识别资源具体问题"""
        issues = []
        metadata = data.get("metadata", {})
        
        if kind == "pod":
            phase = metadata.get("phase", "Unknown")
            restart_count = metadata.get("restart_count", 0)
            container_states = metadata.get("container_states", [])
            restart_count = restart_count if restart_count is not None else 0
            
            # 检查容器状态，提供更详细的问题描述
            container_issues = []
            for container in container_states:
                container_name = container.get("name", "unknown")
                if container.get("state") == "waiting":
                    reason = container.get("reason", "Unknown")
                    message = container.get("message", "")
                    if reason == "ImagePullBackOff":
                        container_issues.append(f"容器 {container_name} 镜像拉取失败: {reason}")
                    elif reason == "CrashLoopBackOff":
                        container_issues.append(f"容器 {container_name} 崩溃循环: {reason}")
                    elif reason == "ErrImagePull":
                        container_issues.append(f"容器 {container_name} 镜像拉取错误: {reason}")
                    elif reason == "InvalidImageName":
                        container_issues.append(f"容器 {container_name} 镜像名称无效: {reason}")
                    elif reason in ["CreateContainerConfigError", "CreateContainerError"]:
                        container_issues.append(f"容器 {container_name} 创建失败: {reason}")
                    else:
                        container_issues.append(f"容器 {container_name} 等待中: {reason}")
                elif container.get("state") == "terminated":
                    exit_code = container.get("exit_code", 0)
                    reason = container.get("reason", "Unknown")
                    if exit_code != 0:
                        container_issues.append(f"容器 {container_name} 异常退出: {reason} (exit code: {exit_code})")
            
            # 如果有容器问题，优先显示容器问题
            if container_issues:
                issues.extend(container_issues)
            elif phase in ["Failed", "Pending"]:
                # 如果没有具体容器问题但Pod状态异常，显示Pod状态
                if phase == "Pending" and container_states:
                    issues.append(f"Pod状态异常: {phase} (容器未就绪)")
                else:
                    issues.append(f"Pod状态异常: {phase}")
            
            if restart_count > 5:
                issues.append(f"重启次数过多: {restart_count}")
                
        elif kind == "deployment":
            replicas = metadata.get("replicas", 0)
            ready_replicas = metadata.get("ready_replicas", 0)
            available_replicas = metadata.get("available_replicas", 0)
            
            # 安全地处理None值  
            replicas = replicas if replicas is not None else 0
            ready_replicas = ready_replicas if ready_replicas is not None else 0
            available_replicas = available_replicas if available_replicas is not None else 0
            
            if ready_replicas < replicas:
                issues.append(f"就绪副本不足: {ready_replicas}/{replicas}")
            if available_replicas < replicas:
                issues.append(f"可用副本不足: {available_replicas}/{replicas}")
                
        elif kind == "node":
            ready = metadata.get("ready", True)
            if not ready:
                issues.append("节点未就绪")
        
        return issues
    
    def _calculate_severity(self, kind: str, data: Dict) -> int:
        """计算资源异常严重程度（1-10，10最严重）"""
        base_severity = self.resource_priorities.get(kind, 5)
        metadata = data.get("metadata", {})
        
        if kind == "pod":
            phase = metadata.get("phase", "Unknown")
            restart_count = metadata.get("restart_count", 0)
            container_states = metadata.get("container_states", [])
            
            # 安全地处理None值
            restart_count = restart_count if restart_count is not None else 0
            
            # 检查容器状态，优先级最高
            for container in container_states:
                if container.get("state") == "waiting":
                    reason = container.get("reason", "")
                    if reason == "ImagePullBackOff":
                        return 9  # 镜像拉取失败，严重问题
                    elif reason == "CrashLoopBackOff":
                        return 9  # 崩溃循环，严重问题
                    elif reason in ["ErrImagePull", "InvalidImageName"]:
                        return 8  # 镜像相关问题
                elif container.get("state") == "terminated":
                    exit_code = container.get("exit_code", 0)
                    if exit_code != 0:
                        return 8  # 非正常退出
            
            # 检查Pod phase
            if phase == "Failed":
                return 9
            elif phase == "Pending":
                # Pending状态需要结合容器状态判断严重程度
                if any(c.get("state") == "waiting" and c.get("reason") for c in container_states):
                    return 8  # 有具体的waiting reason
                else:
                    return 6  # 普通的pending
            elif restart_count > 10:
                return 7
            elif restart_count > 5:
                return 6
                
        elif kind == "deployment":
            replicas = metadata.get("replicas", 0)
            ready_replicas = metadata.get("ready_replicas", 0)
            
            # 安全地处理None值
            replicas = replicas if replicas is not None else 0
            ready_replicas = ready_replicas if ready_replicas is not None else 0
            
            if ready_replicas == 0 and replicas > 0:
                return 9
            elif ready_replicas < replicas * 0.5:
                return 7
            elif ready_replicas < replicas:
                return 5
                
        elif kind == "node":
            ready = metadata.get("ready", True)
            if not ready:
                return 10  # 节点问题最严重
        
        return base_severity
    
    def _calculate_key_metrics(self) -> Dict[str, Any]:
        """计算关键指标"""
        metrics = {}
        
        # Pod相关指标
        pod_stats = self._calculate_pod_metrics()
        if pod_stats:
            metrics["pods"] = pod_stats
        
        # Deployment相关指标
        deployment_stats = self._calculate_deployment_metrics()
        if deployment_stats:
            metrics["deployments"] = deployment_stats
        
        # Node相关指标
        node_stats = self._calculate_node_metrics()
        if node_stats:
            metrics["nodes"] = node_stats
        
        # 整体健康度
        metrics["overall_health"] = self._calculate_overall_health()
        
        return metrics
    
    def _calculate_pod_metrics(self) -> Dict[str, Any]:
        """计算Pod相关指标"""
        pods = self._get_resources_by_type("pod")
        if not pods:
            return {}
        
        total_pods = len(pods)
        running_pods = 0
        failed_pods = 0
        pending_pods = 0
        total_restarts = 0
        
        for pod in pods:
            metadata = pod["data"].get("metadata", {})
            phase = metadata.get("phase", "Unknown")
            restarts = metadata.get("restart_count", 0)
            restarts = restarts if restarts is not None else 0
            
            if phase == "Running":
                running_pods += 1
            elif phase == "Failed":
                failed_pods += 1
            elif phase == "Pending":
                pending_pods += 1
            
            total_restarts += restarts
        
        return {
            "total": total_pods,
            "running": running_pods,
            "failed": failed_pods,
            "pending": pending_pods,
            "success_rate": running_pods / total_pods if total_pods > 0 else 0,
            "avg_restarts": total_restarts / total_pods if total_pods > 0 else 0,
            "health_score": (running_pods / total_pods * 100) if total_pods > 0 else 0
        }
    
    def _calculate_deployment_metrics(self) -> Dict[str, Any]:
        """计算Deployment相关指标"""
        deployments = self._get_resources_by_type("deployment")
        if not deployments:
            return {}
        
        total_deployments = len(deployments)
        healthy_deployments = 0
        total_replicas = 0
        ready_replicas = 0
        
        for deployment in deployments:
            metadata = deployment["data"].get("metadata", {})
            replicas = metadata.get("replicas", 0)
            ready = metadata.get("ready_replicas", 0)
            
            # 安全地处理None值
            replicas = replicas if replicas is not None else 0
            ready = ready if ready is not None else 0
            
            total_replicas += replicas
            ready_replicas += ready
            
            if ready >= replicas:
                healthy_deployments += 1
        
        return {
            "total": total_deployments,
            "healthy": healthy_deployments,
            "total_replicas": total_replicas,
            "ready_replicas": ready_replicas,
            "availability_rate": ready_replicas / total_replicas if total_replicas > 0 else 0,
            "deployment_success_rate": healthy_deployments / total_deployments if total_deployments > 0 else 0
        }
    
    def _calculate_node_metrics(self) -> Dict[str, Any]:
        """计算Node相关指标"""
        nodes = self._get_resources_by_type("node")
        if not nodes:
            return {}
        
        total_nodes = len(nodes)
        ready_nodes = 0
        
        for node in nodes:
            metadata = node["data"].get("metadata", {})
            ready = metadata.get("ready", False)
            
            if ready:
                ready_nodes += 1
        
        return {
            "total": total_nodes,
            "ready": ready_nodes,
            "not_ready": total_nodes - ready_nodes,
            "readiness_rate": ready_nodes / total_nodes if total_nodes > 0 else 0
        }
    
    def _calculate_overall_health(self) -> Dict[str, Any]:
        """计算整体健康度"""
        total_resources = len(self.kg.graph.nodes)
        abnormal_resources = len(self._detect_abnormal_resources())
        
        health_score = ((total_resources - abnormal_resources) / total_resources * 100) if total_resources > 0 else 100
        
        if health_score >= 95:
            status = "excellent"
        elif health_score >= 85:
            status = "good"
        elif health_score >= 70:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "score": round(health_score, 2),
            "status": status,
            "total_resources": total_resources,
            "abnormal_resources": abnormal_resources
        }
    
    def _collect_namespace_statistics(self, focus_namespace: str = None) -> Dict[str, Any]:
        """收集命名空间统计信息"""
        namespace_stats = defaultdict(lambda: defaultdict(int))
        cluster_stats = defaultdict(int)
        
        for node_id, data in self.kg.graph.nodes(data=True):
            kind = data.get("kind", "unknown")
            namespace = data.get("namespace", "unknown")
            
            # 检查是否为集群级别资源
            if kind.lower() in CLUSTER_SCOPED_RESOURCES:
                cluster_stats[kind] += 1
            else:
                # 命名空间级别资源
                namespace_stats[namespace][kind] += 1
        
        # 构建结果字典
        result = {ns: dict(stats) for ns, stats in namespace_stats.items()}
        
        # 添加集群级别资源统计
        if cluster_stats:
            result["cluster-scoped"] = dict(cluster_stats)
        
        # 如果指定了重点关注的命名空间，提供更详细的信息
        if focus_namespace and focus_namespace in namespace_stats:
            return {
                "focus_namespace": focus_namespace,
                "focus_details": dict(namespace_stats[focus_namespace]),
                "all_namespaces": result
            }
        
        return result
    
    def _generate_health_status(self) -> Dict[str, str]:
        """生成健康状态总结"""
        abnormal_resources = self._detect_abnormal_resources()
        total_resources = len(self.kg.graph.nodes)
        
        if not abnormal_resources:
            return {"overall": "healthy", "message": "所有资源运行正常"}
        
        critical_issues = [r for r in abnormal_resources if r["severity"] >= 8]
        warning_issues = [r for r in abnormal_resources if r["severity"] >= 6]
        
        if critical_issues:
            return {
                "overall": "critical", 
                "message": f"发现 {len(critical_issues)} 个严重问题，需要立即处理"
            }
        elif warning_issues:
            return {
                "overall": "warning", 
                "message": f"发现 {len(warning_issues)} 个警告问题，建议检查"
            }
        else:
            return {
                "overall": "minor_issues", 
                "message": f"发现 {len(abnormal_resources)} 个轻微问题"
            }
    
    def _get_resources_by_type(self, resource_type: str, namespace: str = None) -> List[Dict]:
        """获取指定类型的资源"""
        resources = []
        
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("kind") == resource_type:
                resource_namespace = data.get("namespace")
                
                # 检查是否为集群级别资源
                if resource_type.lower() in CLUSTER_SCOPED_RESOURCES:
                    # 集群级别资源没有命名空间限制
                    if namespace is None or namespace == "cluster-scoped":
                        resources.append({
                            "resource_id": node_id,
                            "data": data
                        })
                else:
                    # 命名空间级别资源
                    if namespace is None or resource_namespace == namespace:
                        resources.append({
                            "resource_id": node_id,
                            "data": data
                        })
        
        return resources
    
    def _analyze_status_distribution(self, resources: List[Dict], resource_type: str) -> Dict[str, int]:
        """分析资源状态分布"""
        distribution = defaultdict(int)
        
        for resource in resources:
            metadata = resource["data"].get("metadata", {})
            
            if resource_type == "pod":
                status = metadata.get("phase", "Unknown")
            elif resource_type == "deployment":
                replicas = metadata.get("replicas", 0)
                ready = metadata.get("ready_replicas", 0)
                
                # 安全地处理None值
                replicas = replicas if replicas is not None else 0
                ready = ready if ready is not None else 0
                
                if ready >= replicas:
                    status = "Healthy"
                elif ready > 0:
                    status = "Degraded"
                else:
                    status = "Failed"
            elif resource_type == "node":
                status = "Ready" if metadata.get("ready", False) else "NotReady"
            else:
                status = "Unknown"
            
            distribution[status] += 1
        
        return dict(distribution)
    
    def _calculate_resource_metrics(self, resources: List[Dict], resource_type: str) -> Dict[str, Any]:
        """计算资源指标"""
        if resource_type == "pod":
            return self._calculate_pod_metrics()
        elif resource_type == "deployment":
            return self._calculate_deployment_metrics()
        elif resource_type == "node":
            return self._calculate_node_metrics()
        else:
            return {"total_count": len(resources)}
    
    def _get_resource_relationships(self, resources: List[Dict]) -> Dict[str, List[Dict]]:
        """获取资源关系"""
        relationships = {}
        
        for resource in resources[:10]:  # 限制处理数量
            resource_id = resource["resource_id"]
            related = self.kg.get_related_resources(resource_id, max_depth=1)
            
            if related:
                relationships[resource_id] = [
                    {
                        "target": r["resource_id"],
                        "relation": r["relation"],
                        "direction": r["relation_direction"]
                    }
                    for r in related[:5]  # 最多5个关系
                ]
        
        return relationships
    
    def _add_detailed_information(self, summary: Dict) -> Dict:
        """添加详细信息"""
        # 添加重要资源列表
        important_resources = self._get_important_resources()
        if important_resources:
            summary["important_resources"] = important_resources
        
        # 添加趋势信息（如果有历史数据）
        # 这里可以添加资源变化趋势分析
        
        return summary
    
    def _get_important_resources(self) -> List[Dict]:
        """获取重要资源"""
        important = []
        
        # 获取高连接度的资源（中心节点）
        high_degree_nodes = [
            (node, len(list(self.kg.graph.neighbors(node))))
            for node in self.kg.graph.nodes()
        ]
        high_degree_nodes.sort(key=lambda x: x[1], reverse=True)
        
        for node_id, degree in high_degree_nodes[:5]:
            data = self.kg.graph.nodes[node_id]
            important.append({
                "resource_id": node_id,
                "kind": data.get("kind", "unknown"),
                "connection_count": degree,
                "importance_reason": "high_connectivity"
            })
        
        return important
    
    def _compress_to_size_limit(self, summary: Dict) -> Dict:
        """将摘要压缩到大小限制内"""
        current_size = len(json.dumps(summary, ensure_ascii=False))
        
        if current_size <= self.max_summary_bytes:
            return summary
        
        # 逐步移除非关键信息
        compressed_summary = summary.copy()
        
        # 1. 移除详细的资源列表
        if "sample_resources" in compressed_summary:
            del compressed_summary["sample_resources"]
        
        # 2. 限制异常资源数量
        if "abnormal_resources" in compressed_summary:
            compressed_summary["abnormal_resources"] = compressed_summary["abnormal_resources"][:5]
        
        # 3. 移除关系信息
        if "relationships" in compressed_summary:
            del compressed_summary["relationships"]
        
        # 4. 简化命名空间统计
        if "namespace_breakdown" in compressed_summary:
            namespace_data = compressed_summary["namespace_breakdown"]
            if isinstance(namespace_data, dict) and len(namespace_data) > 10:
                # 只保留前10个命名空间
                def get_namespace_size(item):
                    """计算命名空间的资源数量"""
                    try:
                        if isinstance(item[1], dict):
                            return sum(v for v in item[1].values() if isinstance(v, (int, float)))
                        return 0
                    except (TypeError, AttributeError):
                        return 0
                
                sorted_namespaces = sorted(
                    namespace_data.items(), 
                    key=get_namespace_size, 
                    reverse=True
                )
                compressed_summary["namespace_breakdown"] = dict(sorted_namespaces[:10])
        
        # 5. 如果还是太大，移除更多信息
        current_size = len(json.dumps(compressed_summary, ensure_ascii=False))
        if current_size > self.max_summary_bytes:
            # 只保留最关键的信息
            essential_summary = {
                "timestamp": compressed_summary.get("timestamp"),
                "cluster_stats": compressed_summary.get("cluster_stats", {}),
                "health_status": compressed_summary.get("health_status", {}),
                "key_metrics": compressed_summary.get("key_metrics", {}),
                "abnormal_resources": compressed_summary.get("abnormal_resources", [])[:3],
                "compression_applied": True
            }
            return essential_summary
        
        compressed_summary["compression_applied"] = True
        return compressed_summary
    
    def _generate_error_summary(self, error_message: str) -> Dict[str, Any]:
        """生成错误摘要"""
        try:
            nodes_count = len(self.kg.graph.nodes)
            edges_count = len(self.kg.graph.edges)
        except (AttributeError, TypeError):
            nodes_count = 0
            edges_count = 0
            
        return {
            "error": True,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "graph_stats": {
                "nodes": nodes_count,
                "edges": edges_count
            }
        }
    
    def _filter_important_fields(self, data: Dict) -> Dict:
        """过滤重要字段"""
        kind = data.get("kind", "unknown")
        important_fields = self.important_fields.get(kind, ["name", "namespace"])
        
        filtered = {
            "kind": kind,
            "name": data.get("name"),
            "namespace": data.get("namespace")
        }
        
        metadata = data.get("metadata", {})
        for field in important_fields:
            if field in metadata:
                filtered[field] = metadata[field]
        
        return filtered
    
    def _determine_resource_status(self, resource_id: str, data: Dict) -> str:
        """确定资源状态"""
        kind = data.get("kind", "unknown")
        
        if self._is_resource_abnormal(resource_id, kind, data):
            severity = self._calculate_severity(kind, data)
            if severity >= 8:
                return "critical"
            elif severity >= 6:
                return "warning"
            else:
                return "minor_issue"
        
        return "healthy"
    
    def _generate_context_summary(self, related_resources: List[str]) -> Dict[str, Any]:
        """生成上下文摘要"""
        if not related_resources:
            return {"message": "无相关资源"}
        
        # 按类型统计相关资源
        type_counts = defaultdict(int)
        for resource_id in related_resources:
            if self.kg.graph.has_node(resource_id):
                kind = self.kg.graph.nodes[resource_id].get("kind", "unknown")
                type_counts[kind] += 1
        
        return {
            "total_related": len(related_resources),
            "resource_types": dict(type_counts),
            "summary": f"发现 {len(related_resources)} 个相关资源，涉及 {len(type_counts)} 种类型"
        }
    
    def _assess_risks(self, focus_resources: List[str], related_resources: List[str]) -> Dict[str, Any]:
        """评估风险"""
        risks = []
        
        # 检查焦点资源的异常状态
        for resource_id in focus_resources:
            if self.kg.graph.has_node(resource_id):
                data = self.kg.graph.nodes[resource_id]
                kind = data.get("kind", "unknown")
                
                if self._is_resource_abnormal(resource_id, kind, data):
                    severity = self._calculate_severity(kind, data)
                    risks.append({
                        "resource": resource_id,
                        "type": "resource_abnormal",
                        "severity": severity,
                        "description": f"{kind} 资源状态异常"
                    })
        
        # 检查依赖关系风险
        for resource_id in focus_resources:
            impact = self.kg.analyze_impact_scope(resource_id, max_depth=2)
            if impact.get("total_affected", 0) > 10:
                risks.append({
                    "resource": resource_id,
                    "type": "high_impact",
                    "severity": 7,
                    "description": f"影响范围较大，可能影响 {impact['total_affected']} 个资源"
                })
        
        # 计算整体风险等级
        if not risks:
            risk_level = "low"
        elif any(r["severity"] >= 8 for r in risks):
            risk_level = "high"
        elif any(r["severity"] >= 6 for r in risks):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "level": risk_level,
            "risks": risks[:5],  # 最多5个风险
            "total_risks": len(risks)
        }
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return self.stats.copy()
    
    def clear_stats(self):
        """清除统计信息"""
        self.stats = {
            "summaries_generated": 0,
            "avg_compression_ratio": 0.0,
            "abnormal_resources_detected": 0,
            "last_generation_time": 0
        }