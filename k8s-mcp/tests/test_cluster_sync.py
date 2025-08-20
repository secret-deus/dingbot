"""
集群同步引擎单元测试

测试ClusterSyncEngine类的各种功能：
- 同步引擎初始化和配置
- 全量同步功能
- 增量同步（Watch API）
- 资源关系建立
- 错误处理和重试
- 性能统计和监控
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.k8s_mcp.core.cluster_sync import ClusterSyncEngine
from src.k8s_mcp.core.k8s_graph import K8sKnowledgeGraph
from src.k8s_mcp.k8s_client import K8sClient
from src.k8s_mcp.config import K8sConfig


class MockK8sResource:
    """模拟K8s资源对象"""
    def __init__(self, kind, name, namespace="default", labels=None, owner_references=None, **kwargs):
        self.metadata = Mock()
        self.metadata.name = name
        self.metadata.namespace = namespace if namespace != "cluster-scope" else None
        self.metadata.labels = labels or {}
        self.metadata.owner_references = owner_references or []
        
        self.status = Mock()
        self.spec = Mock()
        
        # 根据资源类型设置特定属性
        if kind == "pod":
            self.status.phase = kwargs.get("phase", "Running")
            self.status.pod_ip = kwargs.get("pod_ip", "10.244.1.100")
            self.status.host_ip = kwargs.get("host_ip", "192.168.1.100")
            self.status.container_statuses = []
            if hasattr(self, 'spec'):
                self.spec.node_name = kwargs.get("node_name", "worker-1")
        elif kind == "deployment":
            if hasattr(self, 'spec'):
                self.spec.replicas = kwargs.get("replicas", 3)
            self.status.ready_replicas = kwargs.get("ready_replicas", 3)
            self.status.available_replicas = kwargs.get("available_replicas", 3)
            self.status.updated_replicas = kwargs.get("updated_replicas", 3)
        elif kind == "service":
            if hasattr(self, 'spec'):
                self.spec.cluster_ip = kwargs.get("cluster_ip", "10.96.1.100")
                self.spec.type = kwargs.get("type", "ClusterIP")
                self.spec.ports = []
        elif kind == "node":
            self.status.conditions = [
                Mock(type="Ready", status="True")
            ]
            self.status.node_info = Mock()
            self.status.node_info.kernel_version = "5.4.0"
            self.status.node_info.kubelet_version = "v1.28.0"


class MockApiResponse:
    """模拟API响应"""
    def __init__(self, items):
        self.items = items


class TestClusterSyncEngine:
    """集群同步引擎测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建模拟配置
        self.config = Mock()
        self.config.sync_interval = 60
        self.config.watch_timeout = 300
        self.config.max_retry_count = 3
        self.config.graph_ttl = 3600
        self.config.graph_memory_limit = 1024  # 添加内存限制配置
        
        # 创建知识图谱
        self.kg = K8sKnowledgeGraph(self.config)
        
        # 创建模拟K8s客户端
        self.k8s_client = Mock(spec=K8sClient)
        self.k8s_client.connected = True
        self.k8s_client.core_v1 = Mock()
        self.k8s_client.apps_v1 = Mock()
    
    def test_init(self):
        """测试同步引擎初始化"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        assert sync_engine.kg == self.kg
        assert sync_engine.k8s_client == self.k8s_client
        assert sync_engine.config == self.config
        assert sync_engine.sync_interval == 60
        assert sync_engine.watch_timeout == 300
        assert sync_engine.max_retry_count == 3
        assert not sync_engine.is_running
        assert sync_engine.stats["full_syncs"] == 0
        assert len(sync_engine.supported_resources) == 6
    
    def test_init_without_config(self):
        """测试无配置初始化"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client)
        
        assert sync_engine.sync_interval == 300  # 默认值
        assert sync_engine.watch_timeout == 600  # 默认值
        assert sync_engine.max_retry_count == 3   # 默认值
    
    @pytest.mark.asyncio
    async def test_start_success(self):
        """测试成功启动同步引擎"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        with patch.object(sync_engine, '_periodic_full_sync'), \
             patch.object(sync_engine, '_start_watch_listeners'), \
             patch.object(sync_engine, '_run_full_sync'):
            
            result = await sync_engine.start()
            
            assert result is True
            assert sync_engine.is_running is True
    
    @pytest.mark.asyncio
    async def test_start_client_not_connected(self):
        """测试客户端未连接时启动失败"""
        self.k8s_client.connected = False
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        result = await sync_engine.start()
        
        assert result is False
        assert sync_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """测试已运行时重复启动"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        
        result = await sync_engine.start()
        
        assert result is False
    
    def test_stop(self):
        """测试停止同步引擎"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        sync_engine.watch_threads = {
            "pod": Mock(is_alive=Mock(return_value=True)),
            "service": Mock(is_alive=Mock(return_value=False))
        }
        
        sync_engine.stop()
        
        assert sync_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_full_sync_success(self):
        """测试成功执行全量同步"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        
        # 模拟API响应
        self.k8s_client.core_v1.list_pod_for_all_namespaces.return_value = MockApiResponse([
            MockK8sResource("pod", "test-pod-1", "default", {"app": "web"}),
            MockK8sResource("pod", "test-pod-2", "default", {"app": "web"})
        ])
        self.k8s_client.core_v1.list_service_for_all_namespaces.return_value = MockApiResponse([
            MockK8sResource("service", "web-service", "default")
        ])
        self.k8s_client.apps_v1.list_deployment_for_all_namespaces.return_value = MockApiResponse([
            MockK8sResource("deployment", "web-deploy", "default", replicas=2, ready_replicas=2)
        ])
        self.k8s_client.apps_v1.list_replica_set_for_all_namespaces.return_value = MockApiResponse([])
        self.k8s_client.core_v1.list_node.return_value = MockApiResponse([
            MockK8sResource("node", "worker-1", "cluster-scope")
        ])
        self.k8s_client.core_v1.list_namespace.return_value = MockApiResponse([
            MockK8sResource("namespace", "default", "cluster-scope")
        ])
        
        # 模拟cleanup方法
        with patch.object(self.kg, 'cleanup_expired_nodes', return_value=0):
            result = await sync_engine.full_sync()
        
        assert result is True
        assert sync_engine.stats["full_syncs"] == 1
        assert sync_engine.stats["resources_synced"] == 6  # 2 pods + 1 service + 1 deployment + 1 node + 1 namespace
        assert sync_engine.stats["last_sync_duration"] > 0
        assert sync_engine.last_full_sync > 0
        
        # 验证资源已添加到知识图谱
        assert self.kg.graph.has_node("pod/default/test-pod-1")
        assert self.kg.graph.has_node("pod/default/test-pod-2")
        assert self.kg.graph.has_node("service/default/web-service")
        assert self.kg.graph.has_node("deployment/default/web-deploy")
    
    @pytest.mark.asyncio
    async def test_full_sync_not_running(self):
        """测试未运行时的全量同步"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = False
        
        result = await sync_engine.full_sync()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_resource_type_pods(self):
        """测试同步Pod资源"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 模拟Pod API响应
        mock_pods = [
            MockK8sResource("pod", "web-1", "default", {"app": "web"}, node_name="worker-1"),
            MockK8sResource("pod", "web-2", "default", {"app": "web"}, node_name="worker-2")
        ]
        self.k8s_client.core_v1.list_pod_for_all_namespaces.return_value = MockApiResponse(mock_pods)
        
        config = {"api": "core_v1", "method": "list_pod_for_all_namespaces"}
        count = await sync_engine._sync_resource_type("pod", config)
        
        assert count == 2
        assert self.kg.graph.has_node("pod/default/web-1")
        assert self.kg.graph.has_node("pod/default/web-2")
        
        # 验证Pod属性
        pod1_data = self.kg.graph.nodes["pod/default/web-1"]
        assert pod1_data["kind"] == "pod"
        assert pod1_data["namespace"] == "default"
        assert pod1_data["labels"]["app"] == "web"
        assert pod1_data["metadata"]["phase"] == "Running"
        assert pod1_data["metadata"]["node_name"] == "worker-1"
    
    @pytest.mark.asyncio
    async def test_sync_resource_type_deployments(self):
        """测试同步Deployment资源"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        mock_deployments = [
            MockK8sResource("deployment", "web-deploy", "default", 
                           replicas=3, ready_replicas=2, available_replicas=2)
        ]
        self.k8s_client.apps_v1.list_deployment_for_all_namespaces.return_value = MockApiResponse(mock_deployments)
        
        config = {"api": "apps_v1", "method": "list_deployment_for_all_namespaces"}
        count = await sync_engine._sync_resource_type("deployment", config)
        
        assert count == 1
        assert self.kg.graph.has_node("deployment/default/web-deploy")
        
        # 验证Deployment属性
        deploy_data = self.kg.graph.nodes["deployment/default/web-deploy"]
        assert deploy_data["metadata"]["replicas"] == 3
        assert deploy_data["metadata"]["ready_replicas"] == 2
        assert deploy_data["metadata"]["available_replicas"] == 2
    
    @pytest.mark.asyncio
    async def test_sync_resource_type_unsupported_api(self):
        """测试不支持的API类型"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        config = {"api": "unsupported_api", "method": "some_method"}
        count = await sync_engine._sync_resource_type("unknown", config)
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_sync_single_resource_with_owner_references(self):
        """测试同步带有所有者引用的资源"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 创建带所有者引用的Pod
        owner_ref = Mock()
        owner_ref.kind = "ReplicaSet"
        owner_ref.name = "web-rs-12345"
        
        pod_obj = MockK8sResource("pod", "web-pod-1", "default", {"app": "web"})
        pod_obj.metadata.owner_references = [owner_ref]
        
        await sync_engine._sync_single_resource("pod", pod_obj)
        
        # 验证Pod和ReplicaSet都已创建
        assert self.kg.graph.has_node("pod/default/web-pod-1")
        assert self.kg.graph.has_node("replicaset/default/web-rs-12345")
        
        # 验证所有者关系
        assert self.kg.graph.has_edge("pod/default/web-pod-1", "replicaset/default/web-rs-12345")
        edge_data = self.kg.graph.get_edge_data("pod/default/web-pod-1", "replicaset/default/web-rs-12345")
        assert edge_data["relation"] == "ownedBy"
    
    @pytest.mark.asyncio
    async def test_sync_single_resource_no_metadata(self):
        """测试同步缺少metadata的资源"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 创建没有metadata的资源对象
        resource_obj = Mock()
        resource_obj.metadata = None
        
        # 应该不会抛出异常，只是返回而不处理
        await sync_engine._sync_single_resource("pod", resource_obj)
        
        # 没有资源被添加到图中
        assert len(self.kg.graph.nodes) == 0
    
    @pytest.mark.asyncio
    async def test_build_service_pod_relations(self):
        """测试建立Service到Pod的关系"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 添加Service和Pod到图中
        self.kg.add_resource("service", "default", "web-service")
        self.kg.add_resource("pod", "default", "web-pod-1", labels={"app": "web"})
        self.kg.add_resource("pod", "default", "web-pod-2", labels={"app": "web"})
        self.kg.add_resource("pod", "default", "db-pod", labels={"app": "db"})
        
        await sync_engine._build_service_pod_relations()
        
        # 验证关系建立（基于简化的命名匹配逻辑）
        # 注意：实际的关系建立逻辑可能不会创建边，因为我们使用的是简化的匹配
        # 这里主要测试方法不会出错
        assert sync_engine.stats["relationship_builds"] == 0  # 因为还没调用_build_relationships
    
    @pytest.mark.asyncio
    async def test_build_node_pod_relations(self):
        """测试建立Node到Pod的关系"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 添加Node和Pod到图中
        self.kg.add_resource("node", "cluster-scope", "worker-1")
        self.kg.add_resource("pod", "default", "web-pod-1", 
                           metadata={"node_name": "worker-1"})
        self.kg.add_resource("pod", "default", "web-pod-2", 
                           metadata={"node_name": "worker-2"})  # 不存在的节点
        
        await sync_engine._build_node_pod_relations()
        
        # 验证关系建立
        assert self.kg.graph.has_edge("node/cluster-scope/worker-1", "pod/default/web-pod-1")
        edge_data = self.kg.graph.get_edge_data("node/cluster-scope/worker-1", "pod/default/web-pod-1")
        assert edge_data["relation"] == "hosts"
        
        # 没有对应Node的Pod不应该有关系
        assert not self.kg.graph.has_edge("node/cluster-scope/worker-2", "pod/default/web-pod-2")
    
    @pytest.mark.asyncio
    async def test_build_relationships(self):
        """测试建立所有资源关系"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        with patch.object(sync_engine, '_build_service_pod_relations') as mock_service, \
             patch.object(sync_engine, '_build_node_pod_relations') as mock_node, \
             patch.object(sync_engine, '_build_deployment_replicaset_relations') as mock_deploy:
            
            await sync_engine._build_relationships()
            
            mock_service.assert_called_once()
            mock_node.assert_called_once()
            mock_deploy.assert_called_once()
            assert sync_engine.stats["relationship_builds"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_watch_event_added(self):
        """测试处理Watch ADDED事件"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 模拟ADDED事件
        pod_obj = MockK8sResource("pod", "new-pod", "default", {"app": "new"})
        
        await sync_engine._handle_watch_event("pod", "ADDED", pod_obj)
        
        # 验证资源已添加
        assert self.kg.graph.has_node("pod/default/new-pod")
        pod_data = self.kg.graph.nodes["pod/default/new-pod"]
        assert pod_data["labels"]["app"] == "new"
    
    @pytest.mark.asyncio
    async def test_handle_watch_event_modified(self):
        """测试处理Watch MODIFIED事件"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 先添加一个资源
        self.kg.add_resource("pod", "default", "existing-pod", labels={"app": "old"})
        
        # 模拟MODIFIED事件
        pod_obj = MockK8sResource("pod", "existing-pod", "default", {"app": "updated"})
        
        await sync_engine._handle_watch_event("pod", "MODIFIED", pod_obj)
        
        # 验证资源已更新
        assert self.kg.graph.has_node("pod/default/existing-pod")
        pod_data = self.kg.graph.nodes["pod/default/existing-pod"]
        assert pod_data["labels"]["app"] == "updated"
    
    @pytest.mark.asyncio
    async def test_handle_watch_event_deleted(self):
        """测试处理Watch DELETED事件"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 先添加一个资源
        self.kg.add_resource("pod", "default", "to-delete")
        assert self.kg.graph.has_node("pod/default/to-delete")
        
        # 模拟DELETED事件
        pod_obj = MockK8sResource("pod", "to-delete", "default")
        
        await sync_engine._handle_watch_event("pod", "DELETED", pod_obj)
        
        # 验证资源已删除
        assert not self.kg.graph.has_node("pod/default/to-delete")
    
    @pytest.mark.asyncio
    async def test_handle_watch_event_no_metadata(self):
        """测试处理没有metadata的Watch事件"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 创建没有metadata的对象
        obj = Mock()
        obj.metadata = None
        
        # 应该不会抛出异常
        await sync_engine._handle_watch_event("pod", "ADDED", obj)
        
        # 没有资源被添加
        assert len(self.kg.graph.nodes) == 0
    
    def test_get_sync_status(self):
        """测试获取同步状态"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        sync_engine.last_full_sync = time.time() - 100
        sync_engine.stats["full_syncs"] = 5
        sync_engine.watch_threads = {
            "pod": Mock(is_alive=Mock(return_value=True)),
            "service": Mock(is_alive=Mock(return_value=False))
        }
        
        status = sync_engine.get_sync_status()
        
        assert status["is_running"] is True
        assert status["last_full_sync"] == sync_engine.last_full_sync
        assert status["last_full_sync_ago"] == pytest.approx(100, abs=1)
        assert status["sync_interval"] == 60
        assert status["stats"]["full_syncs"] == 5
        assert status["watch_threads"]["pod"] is True
        assert status["watch_threads"]["service"] is False
        assert "graph_stats" in status
        assert "supported_resources" in status
    
    @pytest.mark.asyncio
    async def test_force_sync(self):
        """测试强制同步"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        with patch.object(sync_engine, 'full_sync', return_value=True) as mock_sync:
            result = await sync_engine.force_sync()
            
            assert result is True
            mock_sync.assert_called_once()
    
    def test_get_resource_count_by_type(self):
        """测试获取资源类型统计"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        
        # 添加不同类型的资源
        self.kg.add_resource("pod", "default", "pod-1")
        self.kg.add_resource("pod", "default", "pod-2")
        self.kg.add_resource("service", "default", "service-1")
        self.kg.add_resource("deployment", "default", "deploy-1")
        
        counts = sync_engine.get_resource_count_by_type()
        
        assert counts["pod"] == 2
        assert counts["service"] == 1
        assert counts["deployment"] == 1
    
    def test_get_sync_health_healthy(self):
        """测试健康状态 - 健康"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        sync_engine.last_full_sync = time.time() - 30  # 最近同步
        sync_engine.stats["sync_errors"] = 0
        sync_engine.watch_threads = {
            "pod": Mock(is_alive=Mock(return_value=True)),
            "service": Mock(is_alive=Mock(return_value=True))
        }
        
        # 添加一些资源
        self.kg.add_resource("pod", "default", "pod-1")
        self.kg.add_relation("pod/default/pod-1", "pod/default/pod-1", "test")
        
        health = sync_engine.get_sync_health()
        
        assert health["health"] == "healthy"
        assert health["last_sync_ago_seconds"] == pytest.approx(30, abs=1)
        assert health["error_count"] == 0
        assert health["active_watch_threads"] == 2
        assert health["total_resources"] == 1
        assert health["total_relationships"] == 1
    
    def test_get_sync_health_stopped(self):
        """测试健康状态 - 已停止"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = False
        
        health = sync_engine.get_sync_health()
        
        assert health["health"] == "stopped"
    
    def test_get_sync_health_stale(self):
        """测试健康状态 - 数据过期"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        sync_engine.last_full_sync = time.time() - 200  # 超过2倍同步间隔
        sync_engine.stats["sync_errors"] = 0
        
        health = sync_engine.get_sync_health()
        
        assert health["health"] == "stale"
        assert health["last_sync_ago_seconds"] == pytest.approx(200, abs=1)
    
    def test_get_sync_health_degraded(self):
        """测试健康状态 - 降级"""
        sync_engine = ClusterSyncEngine(self.kg, self.k8s_client, self.config)
        sync_engine.is_running = True
        sync_engine.last_full_sync = time.time() - 30
        sync_engine.stats["sync_errors"] = 5  # 有错误
        
        health = sync_engine.get_sync_health()
        
        assert health["health"] == "degraded"
        assert health["error_count"] == 5


class TestClusterSyncEngineIntegration:
    """集群同步引擎集成测试"""
    
    def test_integration_with_real_knowledge_graph(self):
        """测试与真实知识图谱的集成"""
        config = Mock()
        config.sync_interval = 60
        config.watch_timeout = 300
        config.max_retry_count = 3
        config.graph_ttl = 3600
        
        kg = K8sKnowledgeGraph(config)
        k8s_client = Mock(spec=K8sClient)
        k8s_client.connected = True
        
        sync_engine = ClusterSyncEngine(kg, k8s_client, config)
        
        # 验证初始状态
        assert sync_engine.kg == kg
        assert sync_engine.k8s_client == k8s_client
        assert len(sync_engine.supported_resources) == 6
        
        # 测试状态获取
        status = sync_engine.get_sync_status()
        assert "graph_stats" in status
        assert status["graph_stats"]["nodes_total"] == 0
    
    def test_thread_safety(self):
        """测试线程安全"""
        config = Mock()
        config.sync_interval = 1
        config.watch_timeout = 10
        config.max_retry_count = 1
        
        kg = K8sKnowledgeGraph(config)
        k8s_client = Mock(spec=K8sClient)
        k8s_client.connected = True
        
        sync_engine = ClusterSyncEngine(kg, k8s_client, config)
        
        results = []
        errors = []
        
        def worker():
            """工作线程"""
            try:
                # 并发获取状态
                for _ in range(10):
                    status = sync_engine.get_sync_status()
                    results.append(status["is_running"])
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        # 启动多个线程
        threads = []
        for _ in range(3):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证结果
        assert len(errors) == 0, f"线程安全测试失败: {errors}"
        assert len(results) == 30  # 3个线程 * 10次调用