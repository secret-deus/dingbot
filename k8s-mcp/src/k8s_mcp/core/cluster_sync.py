"""
集群同步引擎

负责K8s集群数据的实时同步，包括：
- 全量同步：定期同步所有资源
- 增量同步：基于Watch API的实时监听
- 关系建立：分析资源间的依赖关系
- 错误恢复：网络中断自动重连
- 性能优化：批量处理和增量更新
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from loguru import logger
from kubernetes import client, watch
from kubernetes.client.rest import ApiException

from .k8s_graph import K8sKnowledgeGraph, CLUSTER_SCOPED_RESOURCES
from ..k8s_client import K8sClient, K8sClientError


class ClusterSyncEngine:
    """集群同步引擎
    
    负责K8s集群数据的实时同步，包括：
    - 全量同步：定期同步所有资源
    - 增量同步：基于Watch API的实时监听
    - 关系建立：分析资源间的依赖关系
    - 错误恢复：网络中断自动重连
    """

    def __init__(self, knowledge_graph: K8sKnowledgeGraph, 
                 k8s_client: K8sClient, config=None):
        """初始化同步引擎
        
        Args:
            knowledge_graph: 知识图谱实例
            k8s_client: K8s客户端实例（复用现有连接）
            config: 配置对象
        """
        self.kg = knowledge_graph
        self.k8s_client = k8s_client
        self.config = config
        
        # 同步配置
        self.sync_interval = config.sync_interval if config else 300  # 5分钟
        self.watch_timeout = config.watch_timeout if config else 600  # Watch超时时间
        self.max_retry_count = config.max_retry_count if config else 3
        
        # 同步状态
        self.is_running = False
        self.last_full_sync = 0
        self.sync_errors = 0
        self.watch_threads = {}
        self._sync_lock = threading.RLock()
        
        # 性能统计
        self.stats = {
            "full_syncs": 0,
            "resources_synced": 0,
            "watch_events": 0,
            "sync_errors": 0,
            "last_sync_duration": 0,
            "relationship_builds": 0
        }
        
        # 支持的资源类型及其API配置
        self.supported_resources = {
            "pod": {
                "api": "core_v1", 
                "method": "list_pod_for_all_namespaces",
                "watch_method": "list_pod_for_all_namespaces"
            },
            "service": {
                "api": "core_v1", 
                "method": "list_service_for_all_namespaces",
                "watch_method": "list_service_for_all_namespaces"
            },
            "deployment": {
                "api": "apps_v1", 
                "method": "list_deployment_for_all_namespaces",
                "watch_method": "list_deployment_for_all_namespaces"
            },
            "replicaset": {
                "api": "apps_v1", 
                "method": "list_replica_set_for_all_namespaces",
                "watch_method": "list_replica_set_for_all_namespaces"
            },
            "node": {
                "api": "core_v1", 
                "method": "list_node",
                "watch_method": "list_node"
            },
            "namespace": {
                "api": "core_v1", 
                "method": "list_namespace",
                "watch_method": "list_namespace"
            }
        }
        
        logger.info("集群同步引擎初始化完成")
    
    async def start(self) -> bool:
        """启动同步引擎
        
        Returns:
            bool: 启动是否成功
        """
        if self.is_running:
            logger.warning("同步引擎已在运行")
            return False
        
        try:
            # 验证K8s连接
            if not self.k8s_client.connected:
                logger.error("K8s客户端未连接，无法启动同步引擎")
                return False
            
            self.is_running = True
            
            # 启动全量同步线程
            sync_thread = threading.Thread(
                target=self._periodic_full_sync,
                name="cluster-sync",
                daemon=True
            )
            sync_thread.start()
            
            # 启动Watch监听线程
            watch_thread = threading.Thread(
                target=self._start_watch_listeners,
                name="watch-listeners",
                daemon=True
            )
            watch_thread.start()
            
            # 立即执行一次全量同步
            initial_sync_thread = threading.Thread(
                target=self._run_full_sync,
                name="initial-sync",
                daemon=True
            )
            initial_sync_thread.start()
            
            logger.info("集群同步引擎启动成功")
            return True
            
        except Exception as e:
            logger.error(f"同步引擎启动失败: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """停止同步引擎"""
        self.is_running = False
        
        # 停止所有Watch线程
        for resource_type, thread in self.watch_threads.items():
            if thread and thread.is_alive():
                logger.info(f"停止 {resource_type} Watch线程")
                # 注意：这里需要优雅关闭Watch线程
        
        logger.info("集群同步引擎已停止")
    
    def _run_full_sync(self) -> bool:
        """执行全量同步的包装方法"""
        try:
            return asyncio.run(self.full_sync())
        except Exception as e:
            logger.error(f"全量同步执行失败: {e}")
            return False
    
    async def full_sync(self) -> bool:
        """执行全量同步
        
        Returns:
            bool: 同步是否成功
        """
        if not self.is_running:
            return False
        
        start_time = time.time()
        synced_count = 0
        
        with self._sync_lock:
            try:
                logger.info("开始集群全量同步...")
                
                # 同步各类资源
                for resource_type, config in self.supported_resources.items():
                    try:
                        count = await self._sync_resource_type(resource_type, config)
                        synced_count += count
                        logger.debug(f"同步 {resource_type}: {count} 个资源")
                    except Exception as e:
                        logger.error(f"同步 {resource_type} 失败: {e}")
                        self.stats["sync_errors"] += 1
                
                # 建立资源关系
                await self._build_relationships()
                
                # 清理过期节点
                if self.config:
                    cleaned = self.kg.cleanup_expired_nodes(self.config.graph_ttl)
                    logger.debug(f"清理过期节点: {cleaned} 个")
                
                # 更新统计
                duration = time.time() - start_time
                self.last_full_sync = time.time()
                self.stats["full_syncs"] += 1
                self.stats["resources_synced"] = synced_count
                self.stats["last_sync_duration"] = duration
                
                logger.info(f"全量同步完成，耗时 {duration:.2f}s，同步 {synced_count} 个资源")
                return True
                
            except Exception as e:
                logger.error(f"全量同步失败: {e}")
                self.stats["sync_errors"] += 1
                return False
    
    async def _sync_resource_type(self, resource_type: str, config: Dict) -> int:
        """同步特定类型的资源
        
        Args:
            resource_type: 资源类型
            config: 资源配置
            
        Returns:
            int: 同步的资源数量
        """
        api_name = config["api"]
        method_name = config["method"]
        
        # 获取API客户端
        if api_name == "core_v1":
            api_client = self.k8s_client.core_v1
        elif api_name == "apps_v1":
            api_client = self.k8s_client.apps_v1
        else:
            logger.error(f"不支持的API: {api_name}")
            return 0
        
        # 调用API方法
        api_method = getattr(api_client, method_name)
        
        try:
            result = api_method(limit=1000)  # 限制每次查询的数量
        except ApiException as e:
            logger.error(f"调用 {method_name} 失败: {e}")
            return 0
        
        count = 0
        for item in result.items:
            try:
                await self._sync_single_resource(resource_type, item)
                count += 1
            except Exception as e:
                logger.error(f"同步单个 {resource_type} 失败: {e}")
        
        return count
    
    async def _sync_single_resource(self, resource_type: str, resource_obj):
        """同步单个资源
        
        Args:
            resource_type: 资源类型
            resource_obj: K8s资源对象
        """
        try:
            # 提取基本信息
            metadata = resource_obj.metadata
            if not metadata:
                logger.warning(f"资源 {resource_type} 缺少 metadata")
                return
            
            name = metadata.name
            # 正确处理集群级别资源的命名空间
            if resource_type.lower() in CLUSTER_SCOPED_RESOURCES:
                namespace = None  # 集群级别资源没有命名空间
            else:
                namespace = getattr(metadata, 'namespace', 'default')
            labels = metadata.labels or {}
            
            # 提取状态信息
            status_info = {}
            if hasattr(resource_obj, 'status') and resource_obj.status:
                status = resource_obj.status
                if resource_type == "pod":
                    # 提取容器状态信息
                    container_states = []
                    container_statuses = getattr(status, 'container_statuses', None)
                    if container_statuses:
                        for container_status in container_statuses:
                            container_name = getattr(container_status, 'name', 'unknown')
                            container_state = {
                                "name": container_name,
                                "ready": getattr(container_status, 'ready', False),
                                "restart_count": getattr(container_status, 'restart_count', 0)
                            }
                            
                            # 检查容器状态 (waiting, running, terminated)
                            if hasattr(container_status, 'state') and container_status.state:
                                state = container_status.state
                                if hasattr(state, 'waiting') and state.waiting:
                                    container_state["state"] = "waiting"
                                    container_state["reason"] = getattr(state.waiting, 'reason', 'Unknown')
                                    container_state["message"] = getattr(state.waiting, 'message', '')
                                elif hasattr(state, 'running') and state.running:
                                    container_state["state"] = "running"
                                elif hasattr(state, 'terminated') and state.terminated:
                                    container_state["state"] = "terminated"
                                    container_state["reason"] = getattr(state.terminated, 'reason', 'Unknown')
                                    container_state["exit_code"] = getattr(state.terminated, 'exit_code', 0)
                                else:
                                    container_state["state"] = "unknown"
                            else:
                                container_state["state"] = "unknown"
                            
                            container_states.append(container_state)
                    
                    status_info = {
                        "phase": getattr(status, 'phase', 'Unknown'),
                        "pod_ip": getattr(status, 'pod_ip', None),
                        "host_ip": getattr(status, 'host_ip', None),
                        "node_name": getattr(resource_obj.spec, 'node_name', None) if hasattr(resource_obj, 'spec') else None,
                        "restart_count": sum(
                            getattr(container_status, 'restart_count', 0) 
                            for container_status in (status.container_statuses or [])
                        ),
                        "container_states": container_states
                    }
                elif resource_type == "deployment":
                    status_info = {
                        "replicas": getattr(resource_obj.spec, 'replicas', 0) if hasattr(resource_obj, 'spec') else 0,
                        "ready_replicas": getattr(status, 'ready_replicas', 0),
                        "available_replicas": getattr(status, 'available_replicas', 0),
                        "updated_replicas": getattr(status, 'updated_replicas', 0)
                    }
                elif resource_type == "service":
                    status_info = {
                        "cluster_ip": getattr(resource_obj.spec, 'cluster_ip', None) if hasattr(resource_obj, 'spec') else None,
                        "type": getattr(resource_obj.spec, 'type', 'ClusterIP') if hasattr(resource_obj, 'spec') else 'ClusterIP',
                        "ports": [
                            {
                                "port": getattr(port, 'port', None),
                                "target_port": getattr(port, 'target_port', None),
                                "protocol": getattr(port, 'protocol', 'TCP')
                            }
                            for port in (getattr(resource_obj.spec, 'ports', []) if hasattr(resource_obj, 'spec') else [])
                        ]
                    }
                elif resource_type == "node":
                    # 正确处理节点的就绪状态
                    ready = False
                    if hasattr(status, 'conditions') and status.conditions:
                        for condition in status.conditions:
                            if hasattr(condition, 'type') and condition.type == "Ready":
                                ready = hasattr(condition, 'status') and condition.status == "True"
                                break
                    
                    status_info = {
                        "ready": ready,
                        "kernel_version": getattr(status.node_info, 'kernel_version', None) if hasattr(status, 'node_info') else None,
                        "kubelet_version": getattr(status.node_info, 'kubelet_version', None) if hasattr(status, 'node_info') else None
                    }
            
            # 添加到知识图谱
            node_id = self.kg.add_resource(
                kind=resource_type,
                namespace=namespace,
                name=name,
                metadata=status_info,
                labels=labels
            )
            
            # 处理所有者引用（建立父子关系）
            if hasattr(metadata, 'owner_references') and metadata.owner_references:
                for owner_ref in metadata.owner_references:
                    owner_kind = owner_ref.kind.lower()
                    owner_name = owner_ref.name
                    
                    # 根据所有者资源类型生成正确的ID
                    if owner_kind in CLUSTER_SCOPED_RESOURCES:
                        owner_id = f"{owner_kind}/{owner_name}"
                        owner_namespace = None
                    else:
                        owner_id = f"{owner_kind}/{namespace}/{owner_name}"
                        owner_namespace = namespace
                    
                    # 如果父资源不存在，先创建占位符
                    if not self.kg.graph.has_node(owner_id):
                        self.kg.add_resource(
                            kind=owner_kind,
                            namespace=owner_namespace,
                            name=owner_name,
                            metadata={"placeholder": True}
                        )
                    
                    # 建立所有者关系
                    self.kg.add_relation(node_id, owner_id, "ownedBy")
            
        except Exception as e:
            logger.error(f"处理资源对象失败 {resource_type}/{name if 'name' in locals() else 'unknown'}: {e}")
    
    async def _build_relationships(self):
        """建立资源间的逻辑关系"""
        try:
            logger.debug("开始建立资源关系...")
            
            # 建立Service -> Pod关系（通过标签选择器）
            await self._build_service_pod_relations()
            
            # 建立Node -> Pod关系
            await self._build_node_pod_relations()
            
            # 建立Deployment -> ReplicaSet关系（通过所有者引用已建立，这里可以添加验证）
            await self._build_deployment_replicaset_relations()
            
            self.stats["relationship_builds"] += 1
            logger.debug("资源关系建立完成")
            
        except Exception as e:
            logger.error(f"建立资源关系失败: {e}")
    
    async def _build_service_pod_relations(self):
        """建立Service到Pod的关系"""
        services = [node for node, data in self.kg.graph.nodes(data=True)
                   if data.get("kind") == "service"]
        
        for service_id in services:
            try:
                service_data = self.kg.graph.nodes[service_id]
                service_namespace = service_data.get("namespace", "default")
                
                # 获取Service的标签选择器（需要从K8s API获取完整信息）
                # 这里简化处理，基于命名空间和名称模式进行匹配
                service_name = service_data.get("name", "")
                
                # 查找可能匹配的Pod（基于命名约定）
                pods = [node for node, data in self.kg.graph.nodes(data=True)
                       if (data.get("kind") == "pod" and 
                           data.get("namespace") == service_namespace)]
                
                for pod_id in pods:
                    pod_data = self.kg.graph.nodes[pod_id]
                    pod_labels = pod_data.get("labels", {})
                    
                    # 简化的匹配逻辑：基于app标签
                    if pod_labels.get("app") and service_name:
                        # 如果service名称包含app标签的值，则认为匹配
                        app_name = pod_labels.get("app")
                        if app_name in service_name or service_name in app_name:
                            # 建立路由关系
                            self.kg.add_relation(service_id, pod_id, "routes")
                            
            except Exception as e:
                logger.error(f"建立Service关系失败 {service_id}: {e}")
    
    async def _build_node_pod_relations(self):
        """建立Node到Pod的关系"""
        pods = [node for node, data in self.kg.graph.nodes(data=True)
               if data.get("kind") == "pod"]
        
        for pod_id in pods:
            try:
                pod_data = self.kg.graph.nodes[pod_id]
                node_name = pod_data.get("metadata", {}).get("node_name")
                
                if node_name:
                    node_id = f"node/{node_name}"  # 节点是集群级别资源
                    if self.kg.graph.has_node(node_id):
                        self.kg.add_relation(node_id, pod_id, "hosts")
                        
            except Exception as e:
                logger.error(f"建立Node关系失败 {pod_id}: {e}")
    
    async def _build_deployment_replicaset_relations(self):
        """建立Deployment到ReplicaSet的关系"""
        # 通过所有者引用已经建立，这里可以添加额外的验证逻辑
        deployments = [node for node, data in self.kg.graph.nodes(data=True)
                      if data.get("kind") == "deployment"]
        
        replicasets = [node for node, data in self.kg.graph.nodes(data=True)
                      if data.get("kind") == "replicaset"]
        
        logger.debug(f"验证Deployment-ReplicaSet关系: {len(deployments)} deployments, {len(replicasets)} replicasets")
    
    def _periodic_full_sync(self):
        """定期全量同步线程"""
        while self.is_running:
            try:
                time.sleep(self.sync_interval)
                if self.is_running:
                    asyncio.run(self.full_sync())
            except Exception as e:
                logger.error(f"定期同步线程异常: {e}")
    
    def _start_watch_listeners(self):
        """启动Watch监听器"""
        # 只监听关键资源类型，避免过多的Watch连接
        watch_resources = ["pod", "deployment", "service"]
        
        for resource_type in watch_resources:
            try:
                thread = threading.Thread(
                    target=self._watch_resource_type,
                    args=(resource_type,),
                    name=f"watch-{resource_type}",
                    daemon=True
                )
                thread.start()
                self.watch_threads[resource_type] = thread
                logger.debug(f"启动 {resource_type} Watch监听器")
            except Exception as e:
                logger.error(f"启动 {resource_type} Watch失败: {e}")
    
    def _watch_resource_type(self, resource_type: str):
        """监听特定资源类型的变更
        
        Args:
            resource_type: 资源类型
        """
        retry_count = 0
        
        while self.is_running and retry_count < self.max_retry_count:
            try:
                # 获取Watch API
                w = watch.Watch()
                
                if resource_type == "pod":
                    stream = w.stream(
                        self.k8s_client.core_v1.list_pod_for_all_namespaces,
                        timeout_seconds=self.watch_timeout
                    )
                elif resource_type == "deployment":
                    stream = w.stream(
                        self.k8s_client.apps_v1.list_deployment_for_all_namespaces,
                        timeout_seconds=self.watch_timeout
                    )
                elif resource_type == "service":
                    stream = w.stream(
                        self.k8s_client.core_v1.list_service_for_all_namespaces,
                        timeout_seconds=self.watch_timeout
                    )
                else:
                    logger.error(f"不支持的Watch资源类型: {resource_type}")
                    break
                
                # 重置重试计数
                retry_count = 0
                
                # 处理事件流
                for event in stream:
                    if not self.is_running:
                        break
                    
                    try:
                        event_type = event["type"]  # ADDED, MODIFIED, DELETED
                        obj = event["object"]
                        
                        # 异步处理Watch事件
                        asyncio.run(self._handle_watch_event(resource_type, event_type, obj))
                        self.stats["watch_events"] += 1
                        
                    except Exception as e:
                        logger.error(f"处理Watch事件失败: {e}")
                
            except ApiException as e:
                if e.status == 410:  # Gone - 资源版本过期
                    logger.warning(f"{resource_type} Watch资源版本过期，重新启动")
                    retry_count = 0  # 410错误不计入重试次数
                else:
                    logger.error(f"{resource_type} Watch API异常: {e}")
                    retry_count += 1
                    time.sleep(min(retry_count * 5, 60))  # 指数退避
                    
            except Exception as e:
                logger.error(f"{resource_type} Watch监听异常: {e}")
                retry_count += 1
                time.sleep(min(retry_count * 5, 60))
        
        if retry_count >= self.max_retry_count:
            logger.error(f"{resource_type} Watch监听重试次数超限，停止监听")
    
    async def _handle_watch_event(self, resource_type: str, event_type: str, obj):
        """处理Watch事件
        
        Args:
            resource_type: 资源类型
            event_type: 事件类型（ADDED, MODIFIED, DELETED）
            obj: 资源对象
        """
        try:
            metadata = obj.metadata
            if not metadata:
                return
                
            name = metadata.name
            
            # 根据资源类型生成正确的节点ID
            if resource_type.lower() in CLUSTER_SCOPED_RESOURCES:
                namespace = None
                node_id = f"{resource_type}/{name}"
            else:
                namespace = getattr(metadata, 'namespace', 'default')
                node_id = f"{resource_type}/{namespace}/{name}"
            
            if event_type in ["ADDED", "MODIFIED"]:
                # 添加或更新资源
                await self._sync_single_resource(resource_type, obj)
                logger.debug(f"Watch事件: {event_type} {node_id}")
                
            elif event_type == "DELETED":
                # 删除资源
                if self.kg.graph.has_node(node_id):
                    self.kg.remove_resource(node_id)
                    logger.debug(f"Watch事件: 删除 {node_id}")
            
        except Exception as e:
            logger.error(f"处理Watch事件失败: {e}")
    
    def get_sync_status(self) -> Dict:
        """获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        return {
            "is_running": self.is_running,
            "last_full_sync": self.last_full_sync,
            "last_full_sync_ago": time.time() - self.last_full_sync if self.last_full_sync > 0 else None,
            "sync_interval": self.sync_interval,
            "stats": self.stats.copy(),
            "graph_stats": self.kg.get_statistics(),
            "watch_threads": {
                resource_type: thread.is_alive() if thread else False
                for resource_type, thread in self.watch_threads.items()
            },
            "supported_resources": list(self.supported_resources.keys())
        }
    
    async def force_sync(self) -> bool:
        """强制执行一次全量同步
        
        Returns:
            bool: 同步是否成功
        """
        logger.info("强制执行全量同步...")
        return await self.full_sync()
    
    def get_resource_count_by_type(self) -> Dict[str, int]:
        """获取各类型资源的数量统计
        
        Returns:
            Dict[str, int]: 资源类型到数量的映射
        """
        counts = {}
        for node_id, data in self.kg.graph.nodes(data=True):
            kind = data.get("kind", "unknown")
            counts[kind] = counts.get(kind, 0) + 1
        return counts
    
    def get_sync_health(self) -> Dict[str, Any]:
        """获取同步健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        now = time.time()
        last_sync_ago = now - self.last_full_sync if self.last_full_sync > 0 else float('inf')
        
        # 判断健康状态
        if not self.is_running:
            health = "stopped"
        elif last_sync_ago > self.sync_interval * 2:
            health = "stale"  # 同步数据过期
        elif self.stats["sync_errors"] > 0:
            health = "degraded"  # 有错误但仍在运行
        else:
            health = "healthy"
        
        return {
            "health": health,
            "last_sync_ago_seconds": last_sync_ago,
            "sync_interval_seconds": self.sync_interval,
            "error_count": self.stats["sync_errors"],
            "active_watch_threads": sum(1 for thread in self.watch_threads.values() if thread and thread.is_alive()),
            "total_resources": len(self.kg.graph.nodes),
            "total_relationships": len(self.kg.graph.edges)
        }