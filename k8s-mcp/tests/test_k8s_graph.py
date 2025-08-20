"""
K8s知识图谱单元测试

测试K8sKnowledgeGraph类的各种功能：
- 资源节点管理
- 关系建立和查询
- 深度遍历和分析
- 内存管理和清理
- 线程安全
"""

import pytest
import time
import threading
from unittest.mock import Mock
from src.k8s_mcp.core.k8s_graph import K8sKnowledgeGraph
from src.k8s_mcp.config import K8sConfig


class TestK8sKnowledgeGraph:
    """K8s知识图谱测试类"""
    
    def test_add_resource(self):
        """测试添加资源节点"""
        kg = K8sKnowledgeGraph()
        
        # 添加Pod资源
        pod_id = kg.add_resource(
            "pod", "default", "test-pod", 
            metadata={"status": "Running"},
            labels={"app": "test"}
        )
        
        assert pod_id == "pod/default/test-pod"
        assert kg.graph.has_node(pod_id)
        
        # 验证节点数据
        node_data = kg.graph.nodes[pod_id]
        assert node_data["kind"] == "pod"
        assert node_data["namespace"] == "default"
        assert node_data["name"] == "test-pod"
        assert node_data["metadata"]["status"] == "Running"
        assert node_data["labels"]["app"] == "test"
        
        # 验证统计更新
        assert kg.stats["nodes_total"] == 1
    
    def test_add_relation(self):
        """测试添加资源关系"""
        kg = K8sKnowledgeGraph()
        
        # 添加资源
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        
        # 添加关系
        result = kg.add_relation(pod_id, deploy_id, "ownedBy", {"controller": True})
        
        assert result is True
        assert kg.graph.has_edge(pod_id, deploy_id)
        
        # 验证边数据
        edge_data = kg.graph.get_edge_data(pod_id, deploy_id)
        assert edge_data["relation"] == "ownedBy"
        assert edge_data["metadata"]["controller"] is True
        
        # 验证统计更新
        assert kg.stats["edges_total"] == 1
    
    def test_add_relation_nonexistent_nodes(self):
        """测试添加不存在节点的关系"""
        kg = K8sKnowledgeGraph()
        
        # 尝试添加不存在节点的关系
        result = kg.add_relation("nonexistent1", "nonexistent2", "test")
        
        assert result is False
        assert kg.stats["edges_total"] == 0
    
    def test_get_related_resources(self):
        """测试获取关联资源"""
        kg = K8sKnowledgeGraph()
        
        # 构建测试图
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        service_id = kg.add_resource("service", "default", "test-service")
        
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        kg.add_relation(deploy_id, service_id, "exposes")
        
        # 测试关联查询
        related = kg.get_related_resources(pod_id, max_depth=2)
        
        # 应该找到3个关联：pod->deployment, deployment->service, deployment->pod(入边)
        assert len(related) == 3
        
        # 验证直接关系（pod -> deployment）
        direct_relations = [r for r in related if r["depth"] == 1]
        assert len(direct_relations) == 1
        assert direct_relations[0]["resource_id"] == deploy_id
        assert direct_relations[0]["relation"] == "ownedBy"
        assert direct_relations[0]["relation_direction"] == "outgoing"
        
        # 验证间接关系
        indirect_relations = [r for r in related if r["depth"] == 2]
        assert len(indirect_relations) == 2
        
        # 应该包含service（通过deployment的出边）
        service_relation = next((r for r in indirect_relations if r["resource_id"] == service_id), None)
        assert service_relation is not None
        assert service_relation["relation"] == "exposes"
        
        # 应该包含pod自身（通过deployment的入边，即deployment -> pod关系的反向）
        pod_relation = next((r for r in indirect_relations if r["resource_id"] == pod_id), None)
        assert pod_relation is not None
        assert pod_relation["relation"] == "ownedBy"
        assert pod_relation["relation_direction"] == "incoming"
    
    def test_get_related_resources_nonexistent(self):
        """测试查询不存在资源的关联"""
        kg = K8sKnowledgeGraph()
        
        related = kg.get_related_resources("nonexistent")
        assert len(related) == 0
    
    def test_relation_filter(self):
        """测试关系类型过滤"""
        kg = K8sKnowledgeGraph()
        
        # 构建测试图
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        service_id = kg.add_resource("service", "default", "test-service")
        
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        kg.add_relation(pod_id, service_id, "routes")
        
        # 只查询ownedBy关系
        related = kg.get_related_resources(pod_id, relation_filter={"ownedBy"})
        
        # 应该找到2个关联：pod->deployment (出边) 和 deployment->pod (入边，反向关系)
        assert len(related) == 2
        
        # 验证出边关系
        outgoing_relation = next((r for r in related if r["relation_direction"] == "outgoing"), None)
        assert outgoing_relation is not None
        assert outgoing_relation["resource_id"] == deploy_id
        assert outgoing_relation["relation"] == "ownedBy"
        
        # 验证入边关系
        incoming_relation = next((r for r in related if r["relation_direction"] == "incoming"), None)
        assert incoming_relation is not None
        assert incoming_relation["resource_id"] == pod_id
        assert incoming_relation["relation"] == "ownedBy"
    
    def test_analyze_impact_scope(self):
        """测试影响范围分析"""
        kg = K8sKnowledgeGraph()
        
        # 构建测试图：deployment -> pod1, pod2
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        pod1_id = kg.add_resource("pod", "default", "test-pod-1")
        pod2_id = kg.add_resource("pod", "default", "test-pod-2")
        
        kg.add_relation(deploy_id, pod1_id, "manages")
        kg.add_relation(deploy_id, pod2_id, "manages")
        
        # 分析影响范围
        impact = kg.analyze_impact_scope(deploy_id)
        
        assert impact["total_affected"] == 2
        assert len(impact["impact_levels"][1]) == 2
        assert impact["max_depth_reached"] == 1
        
        # 验证受影响的资源
        affected_resources = impact["impact_levels"][1]
        affected_ids = [r["resource_id"] for r in affected_resources]
        assert pod1_id in affected_ids
        assert pod2_id in affected_ids
    
    def test_trace_dependency_chain(self):
        """测试依赖链追踪"""
        kg = K8sKnowledgeGraph()
        
        # 构建测试图：node -> pod -> deployment
        node_id = kg.add_resource("node", "cluster-scope", "worker-1")
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        kg.add_relation(node_id, pod_id, "hosts")
        
        # 追踪依赖链
        dependencies = kg.trace_dependency_chain(deploy_id)
        
        assert dependencies["total_dependencies"] == 2
        assert len(dependencies["dependency_levels"]) == 2
        
        # 验证第一级依赖
        level1_deps = dependencies["dependency_levels"][1]
        assert len(level1_deps) == 1
        assert level1_deps[0]["resource_id"] == pod_id
        
        # 验证第二级依赖
        level2_deps = dependencies["dependency_levels"][2]
        assert len(level2_deps) == 1
        assert level2_deps[0]["resource_id"] == node_id
    
    def test_find_resources_by_labels(self):
        """测试标签查询"""
        kg = K8sKnowledgeGraph()
        
        # 添加带标签的资源
        pod1_id = kg.add_resource("pod", "default", "web-1", labels={"app": "web", "env": "prod"})
        pod2_id = kg.add_resource("pod", "default", "web-2", labels={"app": "web", "env": "dev"})
        pod3_id = kg.add_resource("pod", "test", "db-1", labels={"app": "db", "env": "prod"})
        
        # 查询app=web的资源
        web_pods = kg.find_resources_by_labels({"app": "web"})
        assert len(web_pods) == 2
        assert pod1_id in web_pods
        assert pod2_id in web_pods
        
        # 查询env=prod的资源
        prod_pods = kg.find_resources_by_labels({"env": "prod"})
        assert len(prod_pods) == 2
        assert pod1_id in prod_pods
        assert pod3_id in prod_pods
        
        # 查询特定命名空间中的资源
        default_web_pods = kg.find_resources_by_labels({"app": "web"}, namespace="default")
        assert len(default_web_pods) == 2
        
        test_web_pods = kg.find_resources_by_labels({"app": "web"}, namespace="test")
        assert len(test_web_pods) == 0
    
    def test_cleanup_expired_nodes(self):
        """测试过期节点清理"""
        kg = K8sKnowledgeGraph()
        
        # 添加资源
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        
        # 模拟过期：将pod的时间戳设为2小时前
        kg._node_timestamps[pod_id] = time.time() - 7200
        
        # 清理过期节点（TTL为1小时）
        cleaned = kg.cleanup_expired_nodes(ttl_seconds=3600)
        
        assert cleaned == 1
        assert not kg.graph.has_node(pod_id)
        assert kg.graph.has_node(deploy_id)  # 未过期的节点仍然存在
        assert kg.stats["nodes_total"] == 1
    
    def test_get_resource_details(self):
        """测试获取资源详细信息"""
        kg = K8sKnowledgeGraph()
        
        # 添加资源和关系
        pod_id = kg.add_resource("pod", "default", "test-pod", 
                                metadata={"status": "Running"},
                                labels={"app": "test"})
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        service_id = kg.add_resource("service", "default", "test-service")
        
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        kg.add_relation(service_id, pod_id, "routes")
        
        # 获取资源详情
        details = kg.get_resource_details(pod_id)
        
        assert details is not None
        assert details["resource_id"] == pod_id
        assert details["kind"] == "pod"
        assert details["namespace"] == "default"
        assert details["name"] == "test-pod"
        assert details["metadata"]["status"] == "Running"
        assert details["labels"]["app"] == "test"
        assert details["in_degree"] == 1  # service -> pod
        assert details["out_degree"] == 1  # pod -> deployment
        assert details["total_relations"] == 2
    
    def test_get_resource_details_nonexistent(self):
        """测试获取不存在资源的详情"""
        kg = K8sKnowledgeGraph()
        
        details = kg.get_resource_details("nonexistent")
        assert details is None
    
    def test_remove_resource(self):
        """测试移除资源"""
        kg = K8sKnowledgeGraph()
        
        # 添加资源和关系
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        
        # 移除pod资源
        result = kg.remove_resource(pod_id)
        
        assert result is True
        assert not kg.graph.has_node(pod_id)
        assert kg.graph.has_node(deploy_id)  # deployment仍然存在
        assert len(kg.graph.edges) == 0  # 相关边也被移除
        assert kg.stats["nodes_total"] == 1
        assert kg.stats["edges_total"] == 0
    
    def test_remove_nonexistent_resource(self):
        """测试移除不存在的资源"""
        kg = K8sKnowledgeGraph()
        
        result = kg.remove_resource("nonexistent")
        assert result is False
    
    def test_get_namespace_summary(self):
        """测试命名空间摘要统计"""
        kg = K8sKnowledgeGraph()
        
        # 添加不同命名空间的资源
        kg.add_resource("pod", "default", "web-1")
        kg.add_resource("pod", "default", "web-2")
        kg.add_resource("service", "default", "web-svc")
        kg.add_resource("pod", "kube-system", "coredns")
        kg.add_resource("deployment", "production", "app")
        
        summary = kg.get_namespace_summary()
        
        assert len(summary) == 3
        
        # 验证default命名空间
        assert summary["default"]["total"] == 3
        assert summary["default"]["by_kind"]["pod"] == 2
        assert summary["default"]["by_kind"]["service"] == 1
        
        # 验证kube-system命名空间
        assert summary["kube-system"]["total"] == 1
        assert summary["kube-system"]["by_kind"]["pod"] == 1
        
        # 验证production命名空间
        assert summary["production"]["total"] == 1
        assert summary["production"]["by_kind"]["deployment"] == 1
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        kg = K8sKnowledgeGraph()
        
        # 添加一些资源和关系
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        
        # 执行一次查询
        kg.get_related_resources(pod_id)
        
        stats = kg.get_statistics()
        
        assert stats["nodes_total"] == 2
        assert stats["edges_total"] == 1
        assert stats["queries_total"] == 1
        assert stats["memory_estimate_mb"] > 0
        assert "last_updated" in stats
    
    def test_clear(self):
        """测试清空图数据"""
        kg = K8sKnowledgeGraph()
        
        # 添加一些数据
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        kg.add_relation(pod_id, deploy_id, "ownedBy")
        
        # 执行查询增加统计
        kg.get_related_resources(pod_id)
        
        # 清空数据
        kg.clear()
        
        assert len(kg.graph.nodes) == 0
        assert len(kg.graph.edges) == 0
        assert len(kg._node_timestamps) == 0
        assert kg.stats["nodes_total"] == 0
        assert kg.stats["edges_total"] == 0
        assert kg.stats["queries_total"] == 0
    
    def test_export_graph_data(self):
        """测试导出图数据"""
        kg = K8sKnowledgeGraph()
        
        # 添加测试数据
        pod_id = kg.add_resource("pod", "default", "test-pod", 
                                metadata={"status": "Running"},
                                labels={"app": "test"})
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        kg.add_relation(pod_id, deploy_id, "ownedBy", {"controller": True})
        
        # 导出数据
        exported = kg.export_graph_data()
        
        assert "nodes" in exported
        assert "edges" in exported
        assert "statistics" in exported
        assert "timestamp" in exported
        
        # 验证节点数据
        assert len(exported["nodes"]) == 2
        pod_node = next(n for n in exported["nodes"] if n["id"] == pod_id)
        assert pod_node["kind"] == "pod"
        assert pod_node["namespace"] == "default"
        assert pod_node["name"] == "test-pod"
        assert pod_node["metadata"]["status"] == "Running"
        assert pod_node["labels"]["app"] == "test"
        
        # 验证边数据
        assert len(exported["edges"]) == 1
        edge = exported["edges"][0]
        assert edge["source"] == pod_id
        assert edge["target"] == deploy_id
        assert edge["relation"] == "ownedBy"
        assert edge["metadata"]["controller"] is True
    
    def test_thread_safety(self):
        """测试线程安全"""
        kg = K8sKnowledgeGraph()
        results = []
        errors = []
        
        def worker_add_resources(worker_id):
            """工作线程：添加资源"""
            try:
                for i in range(10):
                    pod_id = kg.add_resource("pod", "default", f"worker-{worker_id}-pod-{i}")
                    results.append(pod_id)
            except Exception as e:
                errors.append(e)
        
        def worker_query_resources():
            """工作线程：查询资源"""
            try:
                time.sleep(0.1)  # 等待一些资源被添加
                for _ in range(5):
                    if kg.graph.nodes:
                        node_id = list(kg.graph.nodes)[0]
                        kg.get_related_resources(node_id)
            except Exception as e:
                errors.append(e)
        
        # 启动多个线程
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker_add_resources, args=(i,))
            threads.append(t)
            t.start()
        
        query_thread = threading.Thread(target=worker_query_resources)
        threads.append(query_thread)
        query_thread.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证结果
        assert len(errors) == 0, f"线程安全测试失败: {errors}"
        assert len(results) == 30  # 3个worker * 10个资源
        assert kg.stats["nodes_total"] == 30
    
    def test_config_integration(self):
        """测试配置集成"""
        # 创建测试配置
        config = Mock()
        config.graph_ttl = 1800
        config.graph_memory_limit = 512
        
        kg = K8sKnowledgeGraph(config)
        
        # 验证配置使用
        assert kg.config == config
        
        # 测试TTL使用
        pod_id = kg.add_resource("pod", "default", "test-pod")
        kg._node_timestamps[pod_id] = time.time() - 2000  # 过期
        
        cleaned = kg.cleanup_expired_nodes()
        assert cleaned == 1
    
    def test_memory_limit_check(self):
        """测试内存限制检查"""
        config = Mock()
        config.graph_memory_limit = 0.001  # 很小的限制，强制触发清理
        config.graph_ttl = 3600  # 设置TTL值
        
        kg = K8sKnowledgeGraph(config)
        
        # 添加足够多的资源触发内存限制
        for i in range(10):
            kg.add_resource("pod", "default", f"pod-{i}")
        
        # 内存检查应该触发清理
        assert kg.stats["cleanup_runs"] > 0


class TestK8sKnowledgeGraphEdgeCases:
    """边界情况和错误处理测试"""
    
    def test_empty_graph_operations(self):
        """测试空图的各种操作"""
        kg = K8sKnowledgeGraph()
        
        # 空图查询
        assert kg.get_related_resources("nonexistent") == []
        assert kg.analyze_impact_scope("nonexistent")["error"] is not None
        assert kg.trace_dependency_chain("nonexistent")["error"] is not None
        assert kg.get_resource_details("nonexistent") is None
        assert kg.remove_resource("nonexistent") is False
        
        # 空图统计
        stats = kg.get_statistics()
        assert stats["nodes_total"] == 0
        assert stats["edges_total"] == 0
        
        # 空图导出
        exported = kg.export_graph_data()
        assert len(exported["nodes"]) == 0
        assert len(exported["edges"]) == 0
    
    def test_invalid_relation_data(self):
        """测试无效关系数据"""
        kg = K8sKnowledgeGraph()
        
        pod_id = kg.add_resource("pod", "default", "test-pod")
        deploy_id = kg.add_resource("deployment", "default", "test-deploy")
        
        # 添加空关系类型
        result = kg.add_relation(pod_id, deploy_id, "")
        assert result is True  # 应该允许空关系类型
        
        # 添加None元数据
        result = kg.add_relation(pod_id, deploy_id, "test", None)
        assert result is True
    
    def test_large_depth_query(self):
        """测试大深度查询"""
        kg = K8sKnowledgeGraph()
        
        # 构建长链：node1 -> node2 -> node3 -> ... -> node10
        node_ids = []
        for i in range(10):
            node_id = kg.add_resource("pod", "default", f"pod-{i}")
            node_ids.append(node_id)
            
            if i > 0:
                kg.add_relation(node_ids[i-1], node_ids[i], "connects")
        
        # 测试超大深度查询
        related = kg.get_related_resources(node_ids[0], max_depth=20)
        
        # 由于双向遍历，会找到更多的关联资源（包括反向关系）
        # 在链式结构中：每个节点都可以通过多条路径到达
        assert len(related) > 9  # 至少会找到直接的9个节点，加上反向关系会更多
        
        # 验证确实能找到最远的节点
        resource_ids = [r["resource_id"] for r in related]
        assert node_ids[9] in resource_ids  # 最远的节点应该在结果中
        
        # 验证链的完整性：应该能找到所有中间节点
        for i in range(1, 10):
            assert node_ids[i] in resource_ids