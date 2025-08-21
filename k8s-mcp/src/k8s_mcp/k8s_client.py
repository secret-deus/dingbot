"""
Kubernetes客户端

使用kubernetes python client实现与K8s集群的真实交互
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from loguru import logger
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException

from .config import K8sConfig, get_config


class K8sClientError(Exception):
    """K8s客户端错误"""
    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class K8sClient:
    """Kubernetes客户端"""
    
    def __init__(self, config_obj: Optional[K8sConfig] = None):
        """初始化K8s客户端
        
        Args:
            config_obj: K8s配置对象，如果为None则使用全局配置
        """
        self.config = config_obj or get_config()
        self.core_v1 = None
        self.apps_v1 = None
        self.networking_v1 = None
        self.rbac_v1 = None
        self.connected = False
        
        # 统计信息
        self.connection_time = None
        self.api_calls_count = 0
        
        logger.info("K8s客户端初始化完成")
    
    async def connect(self) -> bool:
        """连接到K8s集群"""
        try:
            # 验证配置
            if not self.config.validate_config():
                raise K8sClientError("K8s配置验证失败")
            
            # 加载配置
            await self._load_k8s_config()
            
            # 初始化客户端
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.version_api = client.VersionApi()
            
            # 测试连接
            await self._test_connection()
            
            self.connected = True
            self.connection_time = time.time()
            logger.info("K8s客户端连接成功")
            return True
            
        except Exception as e:
            logger.error(f"K8s客户端连接失败: {e}")
            self.connected = False
            raise K8sClientError(f"连接失败: {str(e)}")
    
    async def _load_k8s_config(self):
        """加载K8s配置"""
        try:
            # 使用kubeconfig文件
            kubeconfig_path = self.config.get_kubeconfig_path()
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
                logger.info(f"使用kubeconfig: {kubeconfig_path}")
            else:
                raise K8sClientError("未找到kubeconfig文件")
        except ConfigException as e:
            raise K8sClientError(f"加载K8s配置失败: {str(e)}")
    
    async def _test_connection(self):
        """测试连接"""
        try:
            # 获取集群信息
            version = self.version_api.get_code().to_dict()
            logger.info(f"集群版本: {version.get('git_version', 'unknown')}")
            
            # 获取节点信息
            nodes = self.core_v1.list_node(limit=1)
            logger.info(f"集群节点数: {len(nodes.items)}")
            
        except ApiException as e:
            raise K8sClientError(f"连接测试失败: {e.reason}")
    
    async def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info("K8s客户端已断开连接")
    
    def _check_connection(self):
        """检查连接状态"""
        if not self.connected:
            raise K8sClientError("K8s客户端未连接")
    
    def _check_namespace_permission(self, namespace: str):
        """检查命名空间权限"""
        # 简化配置，不再检查命名空间权限
        pass
    
    async def get_pods(self, namespace: str = None, label_selector: str = None) -> Dict[str, Any]:
        """获取Pod列表"""
        self._check_connection()
        
        try:
            # 处理命名空间
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取Pod列表
            if namespace == "all":
                pods = self.core_v1.list_pod_for_all_namespaces(
                    label_selector=label_selector,
                    limit=100000  # 增加限制以获取更多Pod
                )
            else:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector,
                    limit=100000  # 增加限制以获取更多Pod
                )
            
            # 格式化结果
            result = {
                "namespace": namespace,
                "total": len(pods.items),
                "items": []
            }
            
            for pod in pods.items:
                # 安全地访问Pod属性，避免NoneType错误
                metadata = pod.metadata or type('obj', (object,), {'name': 'unknown', 'namespace': 'unknown', 'labels': {}, 'creation_timestamp': None})()
                status = pod.status or type('obj', (object,), {'phase': 'Unknown', 'pod_ip': None, 'container_statuses': None})()
                spec = pod.spec or type('obj', (object,), {'node_name': None, 'containers': None})()
                
                pod_info = {
                    "name": getattr(metadata, 'name', 'unknown'),
                    "namespace": getattr(metadata, 'namespace', 'unknown'),
                    "phase": getattr(status, 'phase', 'Unknown'),
                    "ready": self._get_pod_ready_status(pod),
                    "restarts": self._get_pod_restart_count(pod),
                    "age": self._calculate_age(getattr(metadata, 'creation_timestamp', None)),
                    "node": getattr(spec, 'node_name', None) or 'unknown',
                    "ip": getattr(status, 'pod_ip', None) or 'unknown',
                    "labels": getattr(metadata, 'labels', None) or {},
                    "containers": []
                }
                
                # 容器信息
                containers = getattr(spec, 'containers', None)
                if containers:
                    for container in containers:
                        container_info = {
                            "name": getattr(container, 'name', 'unknown'),
                            "image": getattr(container, 'image', 'unknown'),
                            "ready": False,
                            "restart_count": 0
                        }
                        
                        # 获取容器资源配置
                        resources = getattr(container, 'resources', None)
                        if resources:
                            container_info["resources"] = {}
                            
                            # 获取资源请求
                            requests = getattr(resources, 'requests', None)
                            if requests:
                                container_info["resources"]["requests"] = {}
                                if hasattr(requests, 'get'):
                                    # 如果是字典类型
                                    container_info["resources"]["requests"] = dict(requests)
                                else:
                                    # 如果是Kubernetes对象类型
                                    if hasattr(requests, 'cpu'):
                                        container_info["resources"]["requests"]["cpu"] = str(requests.cpu)
                                    if hasattr(requests, 'memory'):
                                        container_info["resources"]["requests"]["memory"] = str(requests.memory)
                            
                            # 获取资源限制
                            limits = getattr(resources, 'limits', None)
                            if limits:
                                container_info["resources"]["limits"] = {}
                                if hasattr(limits, 'get'):
                                    # 如果是字典类型
                                    container_info["resources"]["limits"] = dict(limits)
                                else:
                                    # 如果是Kubernetes对象类型
                                    if hasattr(limits, 'cpu'):
                                        container_info["resources"]["limits"]["cpu"] = str(limits.cpu)
                                    if hasattr(limits, 'memory'):
                                        container_info["resources"]["limits"]["memory"] = str(limits.memory)
                        
                        # 获取容器状态
                        container_statuses = getattr(status, 'container_statuses', None)
                        if container_statuses:
                            for status_item in container_statuses:
                                if getattr(status_item, 'name', None) == container.name:
                                    container_info["ready"] = getattr(status_item, 'ready', False)
                                    container_info["restart_count"] = getattr(status_item, 'restart_count', 0)
                                    break
                        
                        pod_info["containers"].append(container_info)
                
                result["items"].append(pod_info)
            
            return result
            
        except ApiException as e:
            raise K8sClientError(f"获取Pod列表失败: {e.reason}")
        except Exception as e:
            # 添加更详细的错误信息
            raise K8sClientError(f"获取Pod列表时发生错误: {str(e)}")
    
    async def get_services(self, namespace: str = None, label_selector: str = None, name: str = None) -> Dict[str, Any]:
        """获取Service列表或单个Service"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 如果指定了name，获取单个service
            if name:
                service = self.core_v1.read_namespaced_service(
                    name=name,
                    namespace=namespace
                )
                services_list = [service]
            else:
                # 获取service列表
                if namespace == "all":
                    services = self.core_v1.list_service_for_all_namespaces(
                        label_selector=label_selector,
                        limit=100  # 简化配置，使用固定限制
                    )
                else:
                    services = self.core_v1.list_namespaced_service(
                        namespace=namespace,
                        label_selector=label_selector,
                        limit=100  # 简化配置，使用固定限制
                    )
                services_list = services.items
            
            result = {
                "namespace": namespace,
                "total": len(services_list),
                "items": []
            }
            
            for service in services_list:
                # 安全地访问Service属性
                metadata = service.metadata or type('obj', (object,), {'name': 'unknown', 'namespace': 'unknown', 'creation_timestamp': None})()
                spec = service.spec or type('obj', (object,), {'type': 'Unknown', 'cluster_ip': None, 'external_ips': None, 'ports': None, 'selector': None})()
                
                service_info = {
                    "name": getattr(metadata, 'name', 'unknown'),
                    "namespace": getattr(metadata, 'namespace', 'unknown'),
                    "type": getattr(spec, 'type', 'Unknown'),
                    "cluster_ip": getattr(spec, 'cluster_ip', None) or 'unknown',
                    "external_ips": getattr(spec, 'external_ips', None) or [],
                    "ports": [],
                    "selector": getattr(spec, 'selector', None) or {},
                    "age": self._calculate_age(getattr(metadata, 'creation_timestamp', None))
                }
                
                # 端口信息
                ports = getattr(spec, 'ports', None)
                if ports:
                    for port in ports:
                        port_info = {
                            "name": getattr(port, 'name', None),
                            "port": getattr(port, 'port', 0),
                            "target_port": getattr(port, 'target_port', None),
                            "protocol": getattr(port, 'protocol', 'TCP'),
                            "node_port": getattr(port, 'node_port', None)
                        }
                        service_info["ports"].append(port_info)
                
                result["items"].append(service_info)
            
            return result
            
        except ApiException as e:
            raise K8sClientError(f"获取Service列表失败: {e.reason}")
        except Exception as e:
            raise K8sClientError(f"获取Service列表时发生错误: {str(e)}")
    
    async def get_deployments(self, namespace: str = None, label_selector: str = None, name: str = None) -> Dict[str, Any]:
        """获取Deployment列表或单个Deployment"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 如果指定了name，获取单个deployment
            if name:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=name,
                    namespace=namespace
                )
                deployments_list = [deployment]
            else:
                # 获取deployment列表
                if namespace == "all":
                    deployments = self.apps_v1.list_deployment_for_all_namespaces(
                        label_selector=label_selector,
                        limit=100  # 简化配置，使用固定限制
                    )
                else:
                    deployments = self.apps_v1.list_namespaced_deployment(
                        namespace=namespace,
                        label_selector=label_selector,
                        limit=100  # 简化配置，使用固定限制
                    )
                deployments_list = deployments.items
            
            result = {
                "namespace": namespace,
                "total": len(deployments_list),
                "items": []
            }
            
            for deployment in deployments_list:
                deployment_info = {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": deployment.spec.replicas,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0,
                    "unavailable_replicas": deployment.status.unavailable_replicas or 0,
                    "strategy": deployment.spec.strategy.type,
                    "labels": deployment.metadata.labels or {},
                    "selector": deployment.spec.selector.match_labels or {},
                    "age": self._calculate_age(deployment.metadata.creation_timestamp)
                }
                
                result["items"].append(deployment_info)
            
            return result
            
        except ApiException as e:
            raise K8sClientError(f"获取Deployment列表失败: {e.reason}")
    
    async def get_nodes(self, label_selector: str = None) -> Dict[str, Any]:
        """获取Node列表"""
        self._check_connection()
        
        try:
            nodes = self.core_v1.list_node(
                label_selector=label_selector,
                limit=100  # 简化配置，使用固定限制
            )
            
            result = {
                "total": len(nodes.items),
                "items": []
            }
            
            for node in nodes.items:
                # 安全地访问Node属性
                metadata = node.metadata or type('obj', (object,), {'name': 'unknown', 'labels': {}, 'creation_timestamp': None})()
                status = node.status or type('obj', (object,), {'capacity': None, 'allocatable': None, 'node_info': None})()
                
                node_info = {
                    "name": getattr(metadata, 'name', 'unknown'),
                    "status": "Ready" if self._is_node_ready(node) else "NotReady",
                    "roles": self._get_node_roles(node),
                    "age": self._calculate_age(getattr(metadata, 'creation_timestamp', None)),
                    "version": "unknown",
                    "internal_ip": self._get_node_internal_ip(node),
                    "external_ip": self._get_node_external_ip(node),
                    "os": "unknown",
                    "kernel": "unknown",
                    "container_runtime": "unknown",
                    "labels": getattr(metadata, 'labels', None) or {}
                }
                
                # 安全地获取节点信息
                node_info_obj = getattr(status, 'node_info', None)
                if node_info_obj:
                    node_info["version"] = getattr(node_info_obj, 'kubelet_version', 'unknown')
                    node_info["os"] = getattr(node_info_obj, 'os_image', 'unknown')
                    node_info["kernel"] = getattr(node_info_obj, 'kernel_version', 'unknown')
                    node_info["container_runtime"] = getattr(node_info_obj, 'container_runtime_version', 'unknown')
                
                # 资源信息
                capacity = getattr(status, 'capacity', None)
                if capacity:
                    node_info["capacity"] = {
                        "cpu": capacity.get("cpu", "unknown"),
                        "memory": capacity.get("memory", "unknown"),
                        "pods": capacity.get("pods", "unknown")
                    }
                else:
                    node_info["capacity"] = {"cpu": "unknown", "memory": "unknown", "pods": "unknown"}
                
                allocatable = getattr(status, 'allocatable', None)
                if allocatable:
                    node_info["allocatable"] = {
                        "cpu": allocatable.get("cpu", "unknown"),
                        "memory": allocatable.get("memory", "unknown"),
                        "pods": allocatable.get("pods", "unknown")
                    }
                else:
                    node_info["allocatable"] = {"cpu": "unknown", "memory": "unknown", "pods": "unknown"}
                
                result["items"].append(node_info)
            
            return result
            
        except ApiException as e:
            raise K8sClientError(f"获取Node列表失败: {e.reason}")
        except Exception as e:
            raise K8sClientError(f"获取Node列表时发生错误: {str(e)}")
    
    async def scale_deployment(self, name: str, replicas: int, namespace: str = None) -> Dict[str, Any]:
        """扩缩容Deployment"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取当前Deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            previous_replicas = deployment.spec.replicas
            
            # 更新副本数
            deployment.spec.replicas = replicas
            
            # 应用更新
            updated_deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                "deployment_name": name,
                "namespace": namespace,
                "previous_replicas": previous_replicas,
                "target_replicas": replicas,
                "current_replicas": updated_deployment.spec.replicas,
                "success": True,
                "message": f"成功将 {name} 扩缩容至 {replicas} 个副本"
            }
            
        except ApiException as e:
            raise K8sClientError(f"扩缩容Deployment失败: {e.reason}")

    async def restart_deployment(self, name: str, namespace: str = None) -> Dict[str, Any]:
        """重启Deployment（通过更新Pod模板触发滚动更新）"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取当前时间戳用于重启注解
            import time
            restart_time = time.strftime("%Y-%m-%dT%H:%M:%S")
            
            # 构建patch数据，添加重启注解触发滚动更新
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": restart_time
                            }
                        }
                    }
                }
            }
            
            # 应用patch
            updated_deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=patch_body
            )
            
            return {
                "deployment_name": name,
                "namespace": namespace,
                "restart_time": restart_time,
                "replicas": updated_deployment.spec.replicas,
                "success": True,
                "message": f"成功重启 Deployment {name}，滚动更新已开始"
            }
            
        except ApiException as e:
            raise K8sClientError(f"重启Deployment失败: {e.reason}")

    async def rollback_deployment(self, name: str, revision: int = None, namespace: str = None) -> Dict[str, Any]:
        """回滚Deployment到指定版本"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取Deployment历史
            history = await self.get_deployment_history(name, namespace)
            
            if not history["revisions"]:
                raise K8sClientError("Deployment没有可用的历史版本")
            
            # 如果没有指定版本，回滚到上一个版本
            if revision is None:
                current_revision = history["current_revision"]
                available_revisions = [r["revision"] for r in history["revisions"]]
                available_revisions.sort(reverse=True)
                
                # 找到当前版本之前的版本
                target_revision = None
                for rev in available_revisions:
                    if rev < current_revision:
                        target_revision = rev
                        break
                
                if target_revision is None:
                    raise K8sClientError("没有找到可回滚的历史版本")
                revision = target_revision
            
            # 验证目标版本是否存在
            target_rs = None
            for rev in history["revisions"]:
                if rev["revision"] == revision:
                    target_rs = rev
                    break
            
            if target_rs is None:
                raise K8sClientError(f"版本 {revision} 不存在")
            
            # 执行回滚 - 更新deployment annotation
            patch_body = {
                "metadata": {
                    "annotations": {
                        "deployment.kubernetes.io/revision": str(revision)
                    }
                }
            }
            
            # 实际回滚操作：复制目标版本的template
            target_rs_obj = self.apps_v1.read_namespaced_replica_set(
                name=target_rs["name"],
                namespace=namespace
            )
            
            # 获取当前deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # 更新deployment的template为目标版本
            deployment.spec.template = target_rs_obj.spec.template
            
            # 应用更新
            updated_deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                "deployment_name": name,
                "namespace": namespace,
                "target_revision": revision,
                "current_revision": history["current_revision"],
                "success": True,
                "message": f"成功回滚 Deployment {name} 到版本 {revision}"
            }
            
        except ApiException as e:
            raise K8sClientError(f"回滚Deployment失败: {e.reason}")

    async def get_deployment_history(self, name: str, namespace: str = None) -> Dict[str, Any]:
        """获取Deployment版本历史"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取Deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # 获取相关的ReplicaSet（包含历史版本）
            label_selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
            replica_sets = self.apps_v1.list_namespaced_replica_set(
                namespace=namespace,
                label_selector=label_selector
            )
            
            # 整理版本历史
            revisions = []
            current_revision = int(deployment.metadata.annotations.get("deployment.kubernetes.io/revision", "1"))
            
            for rs in replica_sets.items:
                revision_str = rs.metadata.annotations.get("deployment.kubernetes.io/revision")
                if revision_str:
                    revision = int(revision_str)
                    
                    # 获取变更原因
                    change_cause = rs.metadata.annotations.get("kubernetes.io/change-cause", "Unknown")
                    
                    revisions.append({
                        "revision": revision,
                        "name": rs.metadata.name,
                        "creation_time": rs.metadata.creation_timestamp.isoformat(),
                        "change_cause": change_cause,
                        "replicas": rs.spec.replicas,
                        "ready_replicas": rs.status.ready_replicas or 0,
                        "is_current": revision == current_revision,
                        "age": self._calculate_age(rs.metadata.creation_timestamp)
                    })
            
            # 按版本号排序
            revisions.sort(key=lambda x: x["revision"], reverse=True)
            
            return {
                "deployment_name": name,
                "namespace": namespace,
                "current_revision": current_revision,
                "total_revisions": len(revisions),
                "revisions": revisions
            }
            
        except ApiException as e:
            raise K8sClientError(f"获取Deployment历史失败: {e.reason}")

    async def patch_deployment(self, name: str, patch_data: Dict[str, Any], namespace: str = None) -> Dict[str, Any]:
        """更新Deployment配置"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取当前Deployment信息
            current_deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # 应用patch
            updated_deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=patch_data
            )
            
            return {
                "deployment_name": name,
                "namespace": namespace,
                "patch_applied": patch_data,
                "current_replicas": updated_deployment.spec.replicas,
                "ready_replicas": updated_deployment.status.ready_replicas or 0,
                "success": True,
                "message": f"成功更新 Deployment {name} 配置"
            }
            
        except ApiException as e:
            raise K8sClientError(f"更新Deployment配置失败: {e.reason}")
    
    async def get_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        """获取单个Deployment信息"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            return {
                "metadata": {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "labels": deployment.metadata.labels or {},
                    "created": deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else None
                },
                "spec": {
                    "replicas": deployment.spec.replicas,
                    "selector": deployment.spec.selector.match_labels or {},
                    "strategy": deployment.spec.strategy.type if deployment.spec.strategy else "RollingUpdate"
                },
                "status": {
                    "replicas": deployment.status.replicas or 0,
                    "readyReplicas": deployment.status.ready_replicas or 0,
                    "availableReplicas": deployment.status.available_replicas or 0,
                    "updatedReplicas": deployment.status.updated_replicas or 0,
                    "conditions": [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "lastUpdateTime": condition.last_update_time.isoformat() if condition.last_update_time else None
                        }
                        for condition in (deployment.status.conditions or [])
                    ]
                }
            }
            
        except ApiException as e:
            if e.status == 404:
                raise K8sClientError(f"Deployment {name} 在命名空间 {namespace} 中不存在")
            raise K8sClientError(f"获取Deployment失败: {e.reason}")

    async def create_deployment(self, namespace: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建Deployment"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 确保命名空间在配置中正确设置
            if "metadata" not in deployment_config:
                deployment_config["metadata"] = {}
            deployment_config["metadata"]["namespace"] = namespace
            
            # 创建Deployment
            created_deployment = self.apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment_config
            )
            
            return {
                "deployment_name": created_deployment.metadata.name,
                "namespace": created_deployment.metadata.namespace,
                "replicas": created_deployment.spec.replicas,
                "success": True,
                "message": f"成功创建 Deployment {created_deployment.metadata.name}",
                "creation_timestamp": created_deployment.metadata.creation_timestamp.isoformat() if created_deployment.metadata.creation_timestamp else None
            }
            
        except ApiException as e:
            if e.status == 409:
                raise K8sClientError(f"Deployment {deployment_config.get('metadata', {}).get('name', 'unknown')} 已存在")
            raise K8sClientError(f"创建Deployment失败: {e.reason}")

    async def update_deployment(self, namespace: str, name: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新Deployment"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 确保命名空间在配置中正确设置
            if "metadata" not in deployment_config:
                deployment_config["metadata"] = {}
            deployment_config["metadata"]["namespace"] = namespace
            deployment_config["metadata"]["name"] = name
            
            # 更新Deployment
            updated_deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment_config
            )
            
            return {
                "deployment_name": updated_deployment.metadata.name,
                "namespace": updated_deployment.metadata.namespace,
                "replicas": updated_deployment.spec.replicas,
                "ready_replicas": updated_deployment.status.ready_replicas or 0,
                "success": True,
                "message": f"成功更新 Deployment {updated_deployment.metadata.name}",
                "update_timestamp": datetime.now().isoformat()
            }
            
        except ApiException as e:
            if e.status == 404:
                raise K8sClientError(f"Deployment {name} 在命名空间 {namespace} 中不存在")
            raise K8sClientError(f"更新Deployment失败: {e.reason}")
    
    async def get_pod_logs(self, pod_name: str, namespace: str = None, 
                          lines: int = None, since: str = None) -> Dict[str, Any]:
        """获取Pod日志"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 设置默认行数
            if lines is None:
                lines = self.config.get_tool_default_param("logs_tail_lines", 100)
            
            # 获取日志
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=lines,
                timestamps=True
            )
            
            return {
                "pod_name": pod_name,
                "namespace": namespace,
                "lines": lines,
                "content": logs
            }
            
        except ApiException as e:
            raise K8sClientError(f"获取Pod日志失败: {e.reason}")
    
    async def describe_pod(self, pod_name: str, namespace: str = None) -> Dict[str, Any]:
        """获取Pod详细信息"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 获取Pod详细信息
            pod = self.core_v1.read_namespaced_pod(
                name=pod_name,
                namespace=namespace
            )
            
            # 获取事件
            try:
                events = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=f"involvedObject.name={pod_name}"
                )
            except Exception as e:
                logger.warning(f"获取Pod事件失败: {e}")
                events = type('obj', (object,), {'items': []})()
            
            # 安全地访问Pod属性
            metadata = pod.metadata or type('obj', (object,), {'name': 'unknown', 'namespace': 'unknown', 'labels': {}, 'annotations': {}})()
            status = pod.status or type('obj', (object,), {'phase': 'Unknown', 'pod_ip': None, 'start_time': None, 'conditions': None, 'container_statuses': None})()
            spec = pod.spec or type('obj', (object,), {'node_name': None, 'containers': None, 'volumes': None})()
            
            # 格式化结果
            result = {
                "pod_name": pod_name,
                "namespace": namespace,
                "status": getattr(status, 'phase', 'Unknown'),
                "node": getattr(spec, 'node_name', None) or 'unknown',
                "ip": getattr(status, 'pod_ip', None) or 'unknown',
                "start_time": None,
                "labels": getattr(metadata, 'labels', None) or {},
                "annotations": getattr(metadata, 'annotations', None) or {},
                "containers": [],
                "conditions": [],
                "volumes": [],
                "events": []
            }
            
            # 安全地获取开始时间
            start_time = getattr(status, 'start_time', None)
            if start_time:
                try:
                    result["start_time"] = start_time.isoformat()
                except Exception:
                    result["start_time"] = str(start_time)
            
            # 容器信息
            containers = getattr(spec, 'containers', None)
            if containers:
                for container in containers:
                    container_info = {
                        "name": getattr(container, 'name', 'unknown'),
                        "image": getattr(container, 'image', 'unknown'),
                        "command": getattr(container, 'command', None) or [],
                        "args": getattr(container, 'args', None) or [],
                        "ports": [],
                        "env": [],
                        "resources": {},
                        "status": {}
                    }
                    
                    # 端口信息
                    ports = getattr(container, 'ports', None)
                    if ports:
                        for port in ports:
                            container_info["ports"].append({
                                "name": getattr(port, 'name', None),
                                "port": getattr(port, 'container_port', 0),
                                "protocol": getattr(port, 'protocol', 'TCP')
                            })
                    
                    # 环境变量
                    env_vars = getattr(container, 'env', None)
                    if env_vars:
                        for env in env_vars:
                            container_info["env"].append({
                                "name": getattr(env, 'name', 'unknown'),
                                "value": getattr(env, 'value', None) or ''
                            })
                    
                    # 资源限制
                    resources = getattr(container, 'resources', None)
                    if resources:
                        limits = getattr(resources, 'limits', None)
                        requests = getattr(resources, 'requests', None)
                        
                        if limits:
                            container_info["resources"]["limits"] = dict(limits)
                        if requests:
                            container_info["resources"]["requests"] = dict(requests)
                    
                    # 容器状态
                    container_statuses = getattr(status, 'container_statuses', None)
                    if container_statuses:
                        for status_item in container_statuses:
                            if getattr(status_item, 'name', None) == container.name:
                                container_info["status"] = {
                                    "ready": getattr(status_item, 'ready', False),
                                    "restart_count": getattr(status_item, 'restart_count', 0),
                                    "image": getattr(status_item, 'image', 'unknown'),
                                    "image_id": getattr(status_item, 'image_id', 'unknown')
                                }
                                break
                    
                    result["containers"].append(container_info)
            
            # 条件信息
            conditions = getattr(status, 'conditions', None)
            if conditions:
                for condition in conditions:
                    condition_info = {
                        "type": getattr(condition, 'type', 'Unknown'),
                        "status": getattr(condition, 'status', 'Unknown'),
                        "reason": getattr(condition, 'reason', None),
                        "message": getattr(condition, 'message', None),
                        "last_transition_time": None
                    }
                    
                    last_transition_time = getattr(condition, 'last_transition_time', None)
                    if last_transition_time:
                        try:
                            condition_info["last_transition_time"] = last_transition_time.isoformat()
                        except Exception:
                            condition_info["last_transition_time"] = str(last_transition_time)
                    
                    result["conditions"].append(condition_info)
            
            # 卷信息
            volumes = getattr(spec, 'volumes', None)
            if volumes:
                for volume in volumes:
                    volume_info = {
                        "name": getattr(volume, 'name', 'unknown'),
                        "type": "unknown"
                    }
                    
                    # 判断卷类型
                    config_map = getattr(volume, 'config_map', None)
                    secret = getattr(volume, 'secret', None)
                    pvc = getattr(volume, 'persistent_volume_claim', None)
                    host_path = getattr(volume, 'host_path', None)
                    empty_dir = getattr(volume, 'empty_dir', None)
                    
                    if config_map:
                        volume_info["type"] = "configMap"
                        volume_info["config_map"] = getattr(config_map, 'name', 'unknown')
                    elif secret:
                        volume_info["type"] = "secret"
                        volume_info["secret"] = getattr(secret, 'secret_name', 'unknown')
                    elif pvc:
                        volume_info["type"] = "persistentVolumeClaim"
                        volume_info["pvc"] = getattr(pvc, 'claim_name', 'unknown')
                    elif host_path:
                        volume_info["type"] = "hostPath"
                        volume_info["host_path"] = getattr(host_path, 'path', 'unknown')
                    elif empty_dir:
                        volume_info["type"] = "emptyDir"
                    
                    result["volumes"].append(volume_info)
            
            # 事件信息
            for event in getattr(events, 'items', []):
                event_info = {
                    "type": getattr(event, 'type', 'Unknown'),
                    "reason": getattr(event, 'reason', 'Unknown'),
                    "message": getattr(event, 'message', ''),
                    "first_time": None,
                    "last_time": None,
                    "count": getattr(event, 'count', 0)
                }
                
                # 安全地获取时间
                first_timestamp = getattr(event, 'first_timestamp', None)
                last_timestamp = getattr(event, 'last_timestamp', None)
                
                if first_timestamp:
                    try:
                        event_info["first_time"] = first_timestamp.isoformat()
                    except Exception:
                        event_info["first_time"] = str(first_timestamp)
                
                if last_timestamp:
                    try:
                        event_info["last_time"] = last_timestamp.isoformat()
                    except Exception:
                        event_info["last_time"] = str(last_timestamp)
                
                result["events"].append(event_info)
            
            return result
            
        except ApiException as e:
            if e.status == 404:
                raise K8sClientError(f"Pod {pod_name} 在命名空间 {namespace} 中不存在")
            raise K8sClientError(f"获取Pod详细信息失败: {e.reason}")
        except Exception as e:
            raise K8sClientError(f"获取Pod详细信息时发生错误: {str(e)}")
    
    async def get_events(self, namespace: str = None, limit: int = None) -> Dict[str, Any]:
        """获取集群事件"""
        self._check_connection()
        
        try:
            if namespace is None:
                namespace = self.config.namespace
            
            if limit is None:
                limit = self.config.get_tool_default_param("max_list_items", 50)
            
            if namespace == "all":
                events = self.core_v1.list_event_for_all_namespaces(limit=limit)
            else:
                self._check_namespace_permission(namespace)
                events = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    limit=limit
                )
            
            result = {
                "namespace": namespace,
                "total": len(events.items),
                "items": []
            }
            
            for event in events.items:
                # 安全地提取事件信息，避免属性访问错误
                try:
                    event_info = {
                        "namespace": event.metadata.namespace if event.metadata else None,
                        "type": event.type if hasattr(event, 'type') else None,
                        "reason": event.reason if hasattr(event, 'reason') else None,
                        "message": event.message if hasattr(event, 'message') else None,
                        "object": {
                            "kind": event.involved_object.kind if event.involved_object else None,
                            "name": event.involved_object.name if event.involved_object else None,
                            "namespace": event.involved_object.namespace if event.involved_object else None
                        } if hasattr(event, 'involved_object') and event.involved_object else {},
                        "first_time": event.first_timestamp.isoformat() if event.first_timestamp else None,
                        "last_time": event.last_timestamp.isoformat() if event.last_timestamp else None,
                        "count": event.count if hasattr(event, 'count') else 0
                    }
                except Exception as e:
                    logger.warning(f"处理事件时出错: {e}, 使用基础信息")
                    event_info = {
                        "namespace": str(getattr(event.metadata, 'namespace', 'unknown')) if hasattr(event, 'metadata') else 'unknown',
                        "type": str(getattr(event, 'type', 'unknown')),
                        "reason": str(getattr(event, 'reason', 'unknown')),
                        "message": str(getattr(event, 'message', 'no message')),
                        "object": {"kind": "unknown", "name": "unknown", "namespace": "unknown"},
                        "first_time": None,
                        "last_time": None,
                        "count": 0
                    }
                
                result["items"].append(event_info)
            
            # 按时间排序
            result["items"].sort(key=lambda x: x["last_time"] or x["first_time"], reverse=True)
            
            return result
            
        except ApiException as e:
            raise K8sClientError(f"获取集群事件失败: {e.reason}")
    
    # 辅助方法
    def _get_pod_ready_status(self, pod) -> str:
        """获取Pod就绪状态"""
        try:
            # 安全地访问pod.status和container_statuses
            if not pod or not hasattr(pod, 'status') or not pod.status:
                return "0/0"
            
            container_statuses = getattr(pod.status, 'container_statuses', None)
            if not container_statuses:
                return "0/0"
            
            ready_count = sum(1 for status in container_statuses if getattr(status, 'ready', False))
            total_count = len(container_statuses)
            return f"{ready_count}/{total_count}"
        except Exception as e:
            logger.warning(f"获取Pod就绪状态时出错: {e}")
            return "unknown"
    
    def _get_pod_restart_count(self, pod) -> int:
        """获取Pod重启次数"""
        try:
            # 安全地访问pod.status和container_statuses
            if not pod or not hasattr(pod, 'status') or not pod.status:
                return 0
            
            container_statuses = getattr(pod.status, 'container_statuses', None)
            if not container_statuses:
                return 0
            
            return sum(getattr(status, 'restart_count', 0) for status in container_statuses)
        except Exception as e:
            logger.warning(f"获取Pod重启次数时出错: {e}")
            return 0
    
    def _calculate_age(self, creation_timestamp) -> str:
        """计算资源年龄"""
        try:
            if not creation_timestamp:
                return "unknown"
            
            now = datetime.now(creation_timestamp.tzinfo)
            age = now - creation_timestamp
            
            if age.days > 0:
                return f"{age.days}d"
            elif age.seconds > 3600:
                return f"{age.seconds // 3600}h"
            elif age.seconds > 60:
                return f"{age.seconds // 60}m"
            else:
                return f"{age.seconds}s"
        except Exception as e:
            logger.warning(f"计算资源年龄时出错: {e}")
            return "unknown"
    
    def _is_node_ready(self, node) -> bool:
        """检查节点是否就绪"""
        try:
            if not node or not hasattr(node, 'status') or not node.status:
                return False
            
            conditions = getattr(node.status, 'conditions', None)
            if not conditions:
                return False
            
            for condition in conditions:
                if getattr(condition, 'type', None) == "Ready":
                    return getattr(condition, 'status', None) == "True"
            
            return False
        except Exception as e:
            logger.warning(f"检查节点就绪状态时出错: {e}")
            return False
    
    def _get_node_roles(self, node) -> List[str]:
        """获取节点角色"""
        try:
            roles = []
            if not node or not hasattr(node, 'metadata') or not node.metadata:
                return ["worker"]
            
            labels = getattr(node.metadata, 'labels', None)
            if labels:
                for label in labels:
                    if label.startswith("node-role.kubernetes.io/"):
                        role = label.split("/")[1]
                        if role:
                            roles.append(role)
            
            return roles if roles else ["worker"]
        except Exception as e:
            logger.warning(f"获取节点角色时出错: {e}")
            return ["worker"]
    
    def _get_node_internal_ip(self, node) -> Optional[str]:
        """获取节点内部IP"""
        try:
            if not node or not hasattr(node, 'status') or not node.status:
                return None
            
            addresses = getattr(node.status, 'addresses', None)
            if not addresses:
                return None
            
            for address in addresses:
                if getattr(address, 'type', None) == "InternalIP":
                    return getattr(address, 'address', None)
            
            return None
        except Exception as e:
            logger.warning(f"获取节点内部IP时出错: {e}")
            return None
    
    def _get_node_external_ip(self, node) -> Optional[str]:
        """获取节点外部IP"""
        try:
            if not node or not hasattr(node, 'status') or not node.status:
                return None
            
            addresses = getattr(node.status, 'addresses', None)
            if not addresses:
                return None
            
            for address in addresses:
                if getattr(address, 'type', None) == "ExternalIP":
                    return getattr(address, 'address', None)
            
            return None
        except Exception as e:
            logger.warning(f"获取节点外部IP时出错: {e}")
            return None
    
    async def create_service(self, namespace: str, service_spec: Dict[str, Any]) -> Dict[str, Any]:
        """创建Service
        
        Args:
            namespace: 命名空间
            service_spec: Service规格配置
            
        Returns:
            创建结果
        """
        self._check_connection()
        
        try:
            if not namespace or (isinstance(namespace, str) and namespace.strip() == ""):
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            # 验证必需的字段
            if not service_spec.get("name"):
                raise K8sClientError("Service名称不能为空")
            
            # 构建Service对象
            service_body = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(
                    name=service_spec["name"],
                    namespace=namespace,
                    labels=service_spec.get("labels", {}),
                    annotations=service_spec.get("annotations", {})
                ),
                spec=client.V1ServiceSpec(
                    selector=service_spec.get("selector", {}),
                    ports=[
                        client.V1ServicePort(
                            name=port.get("name"),
                            port=port["port"],
                            target_port=port.get("target_port", port["port"]),
                            protocol=port.get("protocol", "TCP"),
                            node_port=port.get("node_port")
                        ) for port in service_spec.get("ports", [])
                    ],
                    type=service_spec.get("type", "ClusterIP"),
                    cluster_ip=service_spec.get("cluster_ip"),
                    external_ips=service_spec.get("external_ips"),
                    load_balancer_ip=service_spec.get("load_balancer_ip"),
                    session_affinity=service_spec.get("session_affinity", "None")
                )
            )
            
            # 创建Service
            result = self.core_v1.create_namespaced_service(
                namespace=namespace,
                body=service_body
            )
            
            logger.info(f"Service '{service_spec['name']}' 创建成功")
            
            return {
                "success": True,
                "service": {
                    "name": result.metadata.name,
                    "namespace": result.metadata.namespace,
                    "type": result.spec.type,
                    "cluster_ip": result.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                            "node_port": port.node_port
                        } for port in result.spec.ports or []
                    ],
                    "selector": result.spec.selector or {},
                    "creation_timestamp": result.metadata.creation_timestamp.isoformat()
                }
            }
            
        except ApiException as e:
            logger.error(f"创建Service失败: {e.reason}")
            raise K8sClientError(f"创建Service失败: {e.reason}")
        except Exception as e:
            logger.error(f"创建Service时发生未知错误: {str(e)}")
            raise K8sClientError(f"创建Service失败: {str(e)}")
    
    async def update_service(self, namespace: str, name: str, service_spec: Dict[str, Any]) -> Dict[str, Any]:
        """更新Service配置
        
        Args:
            namespace: 命名空间
            name: Service名称
            service_spec: 更新的Service规格
            
        Returns:
            更新结果
        """
        self._check_connection()
        
        try:
            if not namespace or (isinstance(namespace, str) and namespace.strip() == ""):
                namespace = self.config.namespace
            if not name or name.strip() == "":
                raise K8sClientError("Service名称不能为空")
            
            self._check_namespace_permission(namespace)
            
            # 获取现有Service
            existing_service = self.core_v1.read_namespaced_service(
                name=name,
                namespace=namespace
            )
            
            # 更新Service规格
            if "ports" in service_spec:
                existing_service.spec.ports = [
                    client.V1ServicePort(
                        name=port.get("name"),
                        port=port["port"],
                        target_port=port.get("target_port", port["port"]),
                        protocol=port.get("protocol", "TCP"),
                        node_port=port.get("node_port")
                    ) for port in service_spec["ports"]
                ]
            
            if "selector" in service_spec:
                existing_service.spec.selector = service_spec["selector"]
            
            if "type" in service_spec:
                existing_service.spec.type = service_spec["type"]
            
            if "external_ips" in service_spec:
                existing_service.spec.external_ips = service_spec["external_ips"]
            
            if "load_balancer_ip" in service_spec:
                existing_service.spec.load_balancer_ip = service_spec["load_balancer_ip"]
            
            if "session_affinity" in service_spec:
                existing_service.spec.session_affinity = service_spec["session_affinity"]
            
            # 更新标签和注解
            if "labels" in service_spec:
                existing_service.metadata.labels.update(service_spec["labels"])
            
            if "annotations" in service_spec:
                if not existing_service.metadata.annotations:
                    existing_service.metadata.annotations = {}
                existing_service.metadata.annotations.update(service_spec["annotations"])
            
            # 应用更新
            result = self.core_v1.replace_namespaced_service(
                name=name,
                namespace=namespace,
                body=existing_service
            )
            
            logger.info(f"Service '{name}' 更新成功")
            
            return {
                "success": True,
                "service": {
                    "name": result.metadata.name,
                    "namespace": result.metadata.namespace,
                    "type": result.spec.type,
                    "cluster_ip": result.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                            "node_port": port.node_port
                        } for port in result.spec.ports or []
                    ],
                    "selector": result.spec.selector or {}
                }
            }
            
        except ApiException as e:
            logger.error(f"更新Service失败: {e.reason}")
            raise K8sClientError(f"更新Service失败: {e.reason}")
        except Exception as e:
            logger.error(f"更新Service时发生未知错误: {str(e)}")
            raise K8sClientError(f"更新Service失败: {str(e)}")
    
    async def get_endpoints(self, namespace: str = None, name: str = None, label_selector: str = None) -> Dict[str, Any]:
        """获取Service端点信息
        
        Args:
            namespace: 命名空间，为None时使用默认命名空间
            name: Service名称，为None时获取所有端点
            label_selector: 标签选择器，例如 app=med-marketing
            
        Returns:
            端点信息
        """
        self._check_connection()
        
        try:
            if not namespace or (isinstance(namespace, str) and namespace.strip() == ""):
                namespace = self.config.namespace
            
            self._check_namespace_permission(namespace)
            
            if name:
                # 获取特定Service的端点
                endpoints = self.core_v1.read_namespaced_endpoints(
                    name=name,
                    namespace=namespace
                )
                endpoints_list = [endpoints]
            else:
                # 获取命名空间下所有端点
                endpoints_response = self.core_v1.list_namespaced_endpoints(
                    namespace=namespace,
                    label_selector=label_selector,
                    limit=100
                )
                endpoints_list = endpoints_response.items
            
            result = {
                "namespace": namespace,
                "total": len(endpoints_list),
                "items": []
            }
            
            for endpoints in endpoints_list:
                endpoint_info = {
                    "name": endpoints.metadata.name,
                    "namespace": endpoints.metadata.namespace,
                    "subsets": []
                }
                
                if endpoints.subsets:
                    for subset in endpoints.subsets:
                        subset_info = {
                            "addresses": [],
                            "not_ready_addresses": [],
                            "ports": []
                        }
                        
                        # 就绪地址
                        if subset.addresses:
                            for addr in subset.addresses:
                                addr_info = {
                                    "ip": addr.ip,
                                    "hostname": addr.hostname,
                                    "node_name": addr.node_name
                                }
                                if addr.target_ref:
                                    addr_info["target_ref"] = {
                                        "kind": addr.target_ref.kind,
                                        "name": addr.target_ref.name,
                                        "namespace": addr.target_ref.namespace
                                    }
                                subset_info["addresses"].append(addr_info)
                        
                        # 未就绪地址
                        if subset.not_ready_addresses:
                            for addr in subset.not_ready_addresses:
                                addr_info = {
                                    "ip": addr.ip,
                                    "hostname": addr.hostname,
                                    "node_name": addr.node_name
                                }
                                if addr.target_ref:
                                    addr_info["target_ref"] = {
                                        "kind": addr.target_ref.kind,
                                        "name": addr.target_ref.name,
                                        "namespace": addr.target_ref.namespace
                                    }
                                subset_info["not_ready_addresses"].append(addr_info)
                        
                        # 端口信息
                        if subset.ports:
                            for port in subset.ports:
                                port_info = {
                                    "name": port.name,
                                    "port": port.port,
                                    "protocol": port.protocol,
                                    "app_protocol": port.app_protocol
                                }
                                subset_info["ports"].append(port_info)
                        
                        endpoint_info["subsets"].append(subset_info)
                
                result["items"].append(endpoint_info)
            
            return result
            
        except ApiException as e:
            logger.error(f"获取端点失败: {e.reason}")
            raise K8sClientError(f"获取端点失败: {e.reason}")
        except Exception as e:
            logger.error(f"获取端点时发生未知错误: {str(e)}")
            raise K8sClientError(f"获取端点失败: {str(e)}")
    
    async def patch_service(self, namespace: str, name: str, patch_data: Dict[str, Any]) -> Dict[str, Any]:
        """修改Service配置（JSON Patch方式）
        
        Args:
            namespace: 命名空间
            name: Service名称
            patch_data: 补丁数据
            
        Returns:
            修改结果
        """
        self._check_connection()
        
        try:
            if not namespace or (isinstance(namespace, str) and namespace.strip() == ""):
                namespace = self.config.namespace
            if not name or name.strip() == "":
                raise K8sClientError("Service名称不能为空")
            
            self._check_namespace_permission(namespace)
            
            # 应用补丁
            result = self.core_v1.patch_namespaced_service(
                name=name,
                namespace=namespace,
                body=patch_data
            )
            
            logger.info(f"Service '{name}' 补丁应用成功")
            
            return {
                "success": True,
                "service": {
                    "name": result.metadata.name,
                    "namespace": result.metadata.namespace,
                    "type": result.spec.type,
                    "cluster_ip": result.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                            "node_port": port.node_port
                        } for port in result.spec.ports or []
                    ],
                    "selector": result.spec.selector or {}
                }
            }
            
        except ApiException as e:
            logger.error(f"修改Service失败: {e.reason}")
            raise K8sClientError(f"修改Service失败: {e.reason}")
        except Exception as e:
            logger.error(f"修改Service时发生未知错误: {str(e)}")
            raise K8sClientError(f"修改Service失败: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.connected:
                return {
                    "healthy": False,
                    "message": "K8s客户端未连接"
                }
            
            # 测试基本连接
            version = self.version_api.get_code()
            
            return {
                "healthy": True,
                "message": "K8s客户端连接正常",
                "cluster_version": version.git_version,
                "server_version": version.major + "." + version.minor
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"健康检查失败: {str(e)}"
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取客户端统计信息
        
        Returns:
            Dict[str, Any]: 包含连接状态、配置信息和操作统计的字典
        """
        try:
            return {
                "connected": self.connected,
                "kubeconfig_path": self.config.get_kubeconfig_path() if hasattr(self.config, 'get_kubeconfig_path') else getattr(self.config, 'kubeconfig_path', None),
                "namespace": getattr(self.config, 'namespace', 'default'),
                "api_calls_count": self.api_calls_count,
                "connection_time": self.connection_time,
                "last_connection_time": self.connection_time,
                "client_initialized": {
                    "core_v1": self.core_v1 is not None,
                    "apps_v1": self.apps_v1 is not None,
                    "networking_v1": self.networking_v1 is not None,
                    "rbac_v1": self.rbac_v1 is not None
                }
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "connected": self.connected,
                "error": str(e),
                "api_calls_count": getattr(self, 'api_calls_count', 0)
            } 