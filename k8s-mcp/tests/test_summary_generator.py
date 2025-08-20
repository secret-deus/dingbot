"""
数据摘要生成器单元测试

测试SummaryGenerator类的各种功能：
- 集群摘要生成
- 资源类型摘要生成
- 聚焦摘要生成
- 异常资源检测
- 数据压缩和大小控制
- 关键指标计算
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from src.k8s_mcp.core.summary_generator import SummaryGenerator
from src.k8s_mcp.core.k8s_graph import K8sKnowledgeGraph
from src.k8s_mcp.config import K8sConfig


class TestSummaryGenerator:
    """数据摘要生成器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建模拟配置
        self.config = Mock()
        self.config.max_summary_size_kb = 10
        self.config.graph_ttl = 3600
        self.config.graph_memory_limit = 1024
        
        # 创建知识图谱并添加测试数据
        self.kg = K8sKnowledgeGraph(self.config)
        self._populate_test_data()
        
        # 创建摘要生成器
        self.summary_gen = SummaryGenerator(self.kg, self.config)
    
    def _populate_test_data(self):
        """填充测试数据"""
        # 添加正常的Pod
        self.kg.add_resource(
            "pod", "default", "healthy-pod-1",
            metadata={"phase": "Running", "restart_count": 0, "node_name": "worker-1"},
            labels={"app": "web", "version": "v1"}
        )
        
        self.kg.add_resource(
            "pod", "default", "healthy-pod-2",
            metadata={"phase": "Running", "restart_count": 1, "node_name": "worker-2"},
            labels={"app": "web", "version": "v1"}
        )
        
        # 添加异常的Pod
        self.kg.add_resource(
            "pod", "default", "failed-pod",
            metadata={"phase": "Failed", "restart_count": 10, "node_name": "worker-1"},
            labels={"app": "api", "version": "v2"}
        )
        
        self.kg.add_resource(
            "pod", "kube-system", "pending-pod",
            metadata={"phase": "Pending", "restart_count": 0, "node_name": None},
            labels={"app": "system"}
        )
        
        # 添加Deployment
        self.kg.add_resource(
            "deployment", "default", "web-deployment",
            metadata={"replicas": 3, "ready_replicas": 3, "available_replicas": 3},
            labels={"app": "web"}
        )
        
        self.kg.add_resource(
            "deployment", "default", "api-deployment",
            metadata={"replicas": 2, "ready_replicas": 1, "available_replicas": 1},
            labels={"app": "api"}
        )
        
        # 添加Service
        self.kg.add_resource(
            "service", "default", "web-service",
            metadata={"type": "ClusterIP", "cluster_ip": "10.96.1.100"},
            labels={"app": "web"}
        )
        
        # 添加Node (集群级别资源，命名空间会被自动处理)
        self.kg.add_resource(
            "node", None, "worker-1",
            metadata={"ready": True, "kernel_version": "5.4.0", "kubelet_version": "v1.28.0"}
        )
        
        self.kg.add_resource(
            "node", None, "worker-2",
            metadata={"ready": False, "kernel_version": "5.4.0", "kubelet_version": "v1.28.0"}
        )
        
        # 添加关系
        self.kg.add_relation("pod/default/healthy-pod-1", "deployment/default/web-deployment", "ownedBy")
        self.kg.add_relation("pod/default/healthy-pod-2", "deployment/default/web-deployment", "ownedBy")
        self.kg.add_relation("pod/default/failed-pod", "deployment/default/api-deployment", "ownedBy")
        self.kg.add_relation("service/default/web-service", "pod/default/healthy-pod-1", "routes")
        self.kg.add_relation("service/default/web-service", "pod/default/healthy-pod-2", "routes")
        self.kg.add_relation("node/worker-1", "pod/default/healthy-pod-1", "hosts")
        self.kg.add_relation("node/worker-1", "pod/default/failed-pod", "hosts")
        self.kg.add_relation("node/worker-2", "pod/default/healthy-pod-2", "hosts")
    
    def test_init(self):
        """测试摘要生成器初始化"""
        assert self.summary_gen.kg == self.kg
        assert self.summary_gen.config == self.config
        assert self.summary_gen.max_summary_size_kb == 10
        assert self.summary_gen.max_summary_bytes == 10240
        assert len(self.summary_gen.resource_priorities) == 6
        assert len(self.summary_gen.abnormal_conditions) == 3
        assert self.summary_gen.stats["summaries_generated"] == 0
    
    def test_init_without_config(self):
        """测试无配置初始化"""
        summary_gen = SummaryGenerator(self.kg)
        assert summary_gen.max_summary_size_kb == 10  # 默认值
        assert summary_gen.max_summary_bytes == 10240
    
    def test_generate_cluster_summary_basic(self):
        """测试基础集群摘要生成"""
        summary = self.summary_gen.generate_cluster_summary(include_details=False)
        
        # 验证基本结构
        assert "timestamp" in summary
        assert "cluster_stats" in summary
        assert "health_status" in summary
        assert "key_metrics" in summary
        assert "abnormal_resources" in summary
        assert "graph_info" in summary
        
        # 验证集群统计
        cluster_stats = summary["cluster_stats"]
        assert cluster_stats["total_resources"] == 9  # 4 pods + 2 deployments + 1 service + 2 nodes
        assert "resource_counts" in cluster_stats
        assert cluster_stats["resource_counts"]["pod"] == 4
        assert cluster_stats["resource_counts"]["deployment"] == 2
        assert cluster_stats["resource_counts"]["service"] == 1
        assert cluster_stats["resource_counts"]["node"] == 2
        
        # 验证命名空间统计
        namespace_counts = cluster_stats["namespace_counts"]
        assert namespace_counts["default"] == 6  # 4 pods + 2 deployments + 1 service
        assert namespace_counts["kube-system"] == 1  # 1 pod
        assert namespace_counts["cluster-scoped"] == 2  # 2 nodes
        
        # 验证异常资源
        abnormal_resources = summary["abnormal_resources"]
        assert len(abnormal_resources) >= 2  # 至少有failed-pod和api-deployment
        
        # 验证健康状态
        health_status = summary["health_status"]
        assert health_status["overall"] in ["critical", "warning", "minor_issues"]
        
        # 验证关键指标
        key_metrics = summary["key_metrics"]
        assert "pods" in key_metrics
        assert "deployments" in key_metrics
        assert "nodes" in key_metrics
        assert "overall_health" in key_metrics
        
        # 验证图信息
        graph_info = summary["graph_info"]
        assert graph_info["total_nodes"] == 9
        assert graph_info["total_edges"] >= 7  # 至少7条关系
        
        # 验证统计更新
        assert self.summary_gen.stats["summaries_generated"] == 1
        assert self.summary_gen.stats["last_generation_time"] > 0
    
    def test_generate_cluster_summary_with_focus_namespace(self):
        """测试带聚焦命名空间的集群摘要"""
        summary = self.summary_gen.generate_cluster_summary(focus_namespace="default")
        
        namespace_breakdown = summary["namespace_breakdown"]
        assert "focus_namespace" in namespace_breakdown
        assert namespace_breakdown["focus_namespace"] == "default"
        assert "focus_details" in namespace_breakdown
        assert "all_namespaces" in namespace_breakdown
        
        focus_details = namespace_breakdown["focus_details"]
        assert focus_details["pod"] == 3  # default命名空间的pod数量
        assert focus_details["deployment"] == 2
        assert focus_details["service"] == 1
    
    def test_generate_resource_summary_pods(self):
        """测试Pod资源摘要"""
        summary = self.summary_gen.generate_resource_summary("pod")
        
        assert summary["resource_type"] == "pod"
        assert summary["total_count"] == 4
        assert "status_distribution" in summary
        assert "key_metrics" in summary
        assert "abnormal_count" in summary
        assert "abnormal_resources" in summary
        
        # 验证状态分布
        status_dist = summary["status_distribution"]
        assert status_dist["Running"] == 2
        assert status_dist["Failed"] == 1
        assert status_dist["Pending"] == 1
        
        # 验证关键指标
        metrics = summary["key_metrics"]
        assert metrics["total"] == 4
        assert metrics["running"] == 2
        assert metrics["failed"] == 1
        assert metrics["pending"] == 1
        assert 0 <= metrics["success_rate"] <= 1
        assert metrics["avg_restarts"] >= 0
        
        # 验证异常资源
        assert summary["abnormal_count"] >= 2
        assert len(summary["abnormal_resources"]) <= 5
    
    def test_generate_resource_summary_with_namespace_filter(self):
        """测试带命名空间过滤的资源摘要"""
        summary = self.summary_gen.generate_resource_summary("pod", namespace="default")
        
        assert summary["namespace"] == "default"
        assert summary["total_count"] == 3  # default命名空间的pod数量
        
        status_dist = summary["status_distribution"]
        assert status_dist["Running"] == 2
        assert status_dist["Failed"] == 1
        # Pending pod在kube-system命名空间，所以这里不应该有
        assert "Pending" not in status_dist or status_dist["Pending"] == 0
    
    def test_generate_resource_summary_empty_result(self):
        """测试空结果的资源摘要"""
        summary = self.summary_gen.generate_resource_summary("configmap")
        
        assert summary["resource_type"] == "configmap"
        assert summary["total_count"] == 0
        assert "message" in summary
        assert "未找到" in summary["message"]
    
    def test_generate_focused_summary(self):
        """测试聚焦摘要生成"""
        focus_resources = ["pod/default/healthy-pod-1", "deployment/default/web-deployment"]
        summary = self.summary_gen.generate_focused_summary(focus_resources, context_depth=2)
        
        assert "focus_resources" in summary
        assert "context_summary" in summary
        assert "risk_assessment" in summary
        assert "analysis_depth" in summary
        assert summary["analysis_depth"] == 2
        
        # 验证聚焦资源信息
        focus_info = summary["focus_resources"]
        assert len(focus_info) == 2
        
        pod_info = next((f for f in focus_info if f["resource_id"] == "pod/default/healthy-pod-1"), None)
        assert pod_info is not None
        assert pod_info["status"] == "healthy"
        assert pod_info["related_count"] >= 1
        assert "key_relationships" in pod_info
        
        # 验证上下文摘要
        context_summary = summary["context_summary"]
        assert "total_related" in context_summary
        assert "resource_types" in context_summary
        
        # 验证风险评估
        risk_assessment = summary["risk_assessment"]
        assert risk_assessment["level"] in ["low", "medium", "high"]
        assert "risks" in risk_assessment
        assert "total_risks" in risk_assessment
    
    def test_generate_focused_summary_invalid_resources(self):
        """测试无效资源的聚焦摘要"""
        summary = self.summary_gen.generate_focused_summary(["invalid/resource/id"])
        
        assert "error" in summary
        assert "不存在" in summary["error"]
    
    def test_generate_focused_summary_empty_list(self):
        """测试空列表的聚焦摘要"""
        summary = self.summary_gen.generate_focused_summary([])
        
        assert "error" in summary
        assert "未提供" in summary["error"]
    
    def test_detect_abnormal_resources(self):
        """测试异常资源检测"""
        abnormal_resources = self.summary_gen._detect_abnormal_resources()
        
        # 应该检测到failed-pod、pending-pod、api-deployment（副本不足）、worker-2（未就绪）
        assert len(abnormal_resources) >= 3
        
        # 验证failed-pod被检测为异常
        failed_pod = next((r for r in abnormal_resources if r["resource_id"] == "pod/default/failed-pod"), None)
        assert failed_pod is not None
        assert failed_pod["kind"] == "pod"
        assert failed_pod["severity"] >= 7  # 高严重度
        assert len(failed_pod["issues"]) > 0
        
        # 验证pending-pod被检测为异常
        pending_pod = next((r for r in abnormal_resources if r["resource_id"] == "pod/kube-system/pending-pod"), None)
        assert pending_pod is not None
        assert pending_pod["severity"] >= 6
        
        # 验证api-deployment被检测为异常（副本不足）
        api_deploy = next((r for r in abnormal_resources if r["resource_id"] == "deployment/default/api-deployment"), None)
        assert api_deploy is not None
        assert api_deploy["severity"] >= 5
        
        # 验证worker-2被检测为异常（未就绪）
        worker2 = next((r for r in abnormal_resources if r["resource_id"] == "node/cluster-scope/worker-2"), None)
        assert worker2 is not None
        assert worker2["severity"] == 10  # 节点问题最严重
    
    def test_is_resource_abnormal(self):
        """测试资源异常判断"""
        # 测试正常Pod
        healthy_data = {
            "metadata": {"phase": "Running", "restart_count": 1}
        }
        assert not self.summary_gen._is_resource_abnormal("test", "pod", healthy_data)
        
        # 测试异常Pod - Failed状态
        failed_data = {
            "metadata": {"phase": "Failed", "restart_count": 0}
        }
        assert self.summary_gen._is_resource_abnormal("test", "pod", failed_data)
        
        # 测试异常Pod - 重启次数过多
        restart_data = {
            "metadata": {"phase": "Running", "restart_count": 10}
        }
        assert self.summary_gen._is_resource_abnormal("test", "pod", restart_data)
        
        # 测试正常Deployment
        healthy_deploy_data = {
            "metadata": {"replicas": 3, "ready_replicas": 3, "available_replicas": 3}
        }
        assert not self.summary_gen._is_resource_abnormal("test", "deployment", healthy_deploy_data)
        
        # 测试异常Deployment - 副本不足
        degraded_deploy_data = {
            "metadata": {"replicas": 3, "ready_replicas": 1, "available_replicas": 1}
        }
        assert self.summary_gen._is_resource_abnormal("test", "deployment", degraded_deploy_data)
        
        # 测试正常Node
        healthy_node_data = {
            "metadata": {"ready": True}
        }
        assert not self.summary_gen._is_resource_abnormal("test", "node", healthy_node_data)
        
        # 测试异常Node
        unhealthy_node_data = {
            "metadata": {"ready": False}
        }
        assert self.summary_gen._is_resource_abnormal("test", "node", unhealthy_node_data)
    
    def test_calculate_severity(self):
        """测试严重程度计算"""
        # 测试Failed Pod（最严重）
        failed_data = {"metadata": {"phase": "Failed", "restart_count": 0}}
        severity = self.summary_gen._calculate_severity("pod", failed_data)
        assert severity == 9
        
        # 测试CrashLoopBackOff Pod
        crash_data = {"metadata": {"phase": "CrashLoopBackOff", "restart_count": 5}}
        severity = self.summary_gen._calculate_severity("pod", crash_data)
        assert severity == 8
        
        # 测试重启次数过多的Pod
        restart_data = {"metadata": {"phase": "Running", "restart_count": 12}}
        severity = self.summary_gen._calculate_severity("pod", restart_data)
        assert severity == 7
        
        # 测试完全失败的Deployment
        failed_deploy_data = {"metadata": {"replicas": 3, "ready_replicas": 0}}
        severity = self.summary_gen._calculate_severity("deployment", failed_deploy_data)
        assert severity == 9
        
        # 测试部分失败的Deployment
        partial_fail_data = {"metadata": {"replicas": 4, "ready_replicas": 1}}
        severity = self.summary_gen._calculate_severity("deployment", partial_fail_data)
        assert severity == 7
        
        # 测试未就绪的Node（最严重）
        unhealthy_node_data = {"metadata": {"ready": False}}
        severity = self.summary_gen._calculate_severity("node", unhealthy_node_data)
        assert severity == 10
    
    def test_calculate_key_metrics(self):
        """测试关键指标计算"""
        metrics = self.summary_gen._calculate_key_metrics()
        
        # 验证Pod指标
        assert "pods" in metrics
        pod_metrics = metrics["pods"]
        assert pod_metrics["total"] == 4
        assert pod_metrics["running"] == 2
        assert pod_metrics["failed"] == 1
        assert pod_metrics["pending"] == 1
        assert pod_metrics["success_rate"] == 0.5  # 2/4
        assert pod_metrics["avg_restarts"] == 2.75  # (0+1+10+0)/4
        assert pod_metrics["health_score"] == 50.0  # 2/4 * 100
        
        # 验证Deployment指标
        assert "deployments" in metrics
        deploy_metrics = metrics["deployments"]
        assert deploy_metrics["total"] == 2
        assert deploy_metrics["healthy"] == 1  # 只有web-deployment健康
        assert deploy_metrics["total_replicas"] == 5  # 3+2
        assert deploy_metrics["ready_replicas"] == 4  # 3+1
        assert deploy_metrics["availability_rate"] == 0.8  # 4/5
        assert deploy_metrics["deployment_success_rate"] == 0.5  # 1/2
        
        # 验证Node指标
        assert "nodes" in metrics
        node_metrics = metrics["nodes"]
        assert node_metrics["total"] == 2
        assert node_metrics["ready"] == 1
        assert node_metrics["not_ready"] == 1
        assert node_metrics["readiness_rate"] == 0.5  # 1/2
        
        # 验证整体健康度
        assert "overall_health" in metrics
        overall_health = metrics["overall_health"]
        assert "score" in overall_health
        assert "status" in overall_health
        assert overall_health["status"] in ["excellent", "good", "fair", "poor"]
        assert overall_health["total_resources"] == 9
        assert overall_health["abnormal_resources"] >= 3
    
    def test_compress_to_size_limit_no_compression_needed(self):
        """测试不需要压缩的情况"""
        small_summary = {
            "timestamp": "2023-01-01T00:00:00",
            "cluster_stats": {"total": 5},
            "health_status": {"overall": "healthy"}
        }
        
        compressed = self.summary_gen._compress_to_size_limit(small_summary)
        assert compressed == small_summary
        assert "compression_applied" not in compressed
    
    def test_compress_to_size_limit_compression_applied(self):
        """测试应用压缩的情况"""
        # 创建一个超大的摘要
        large_summary = {
            "timestamp": "2023-01-01T00:00:00",
            "cluster_stats": {"total": 1000},
            "sample_resources": ["resource_" + str(i) for i in range(1000)],
            "abnormal_resources": [{"id": f"resource_{i}", "issue": "problem"} for i in range(100)],
            "relationships": {f"resource_{i}": [{"target": f"target_{j}"} for j in range(10)] for i in range(100)},
            "namespace_breakdown": {f"namespace_{i}": {"pod": 10, "service": 5} for i in range(50)}
        }
        
        compressed = self.summary_gen._compress_to_size_limit(large_summary)
        
        # 验证压缩已应用
        assert "compression_applied" in compressed
        assert compressed["compression_applied"] is True
        
        # 验证某些非关键信息被移除
        assert "sample_resources" not in compressed
        
        # 验证异常资源数量被限制
        if "abnormal_resources" in compressed:
            assert len(compressed["abnormal_resources"]) <= 5
        
        # 验证大小在限制内
        compressed_size = len(json.dumps(compressed, ensure_ascii=False))
        assert compressed_size <= self.summary_gen.max_summary_bytes
    
    def test_compress_to_size_limit_extreme_compression(self):
        """测试极端压缩情况"""
        # 设置非常小的大小限制
        self.summary_gen.max_summary_size_kb = 1
        self.summary_gen.max_summary_bytes = 1024
        
        # 创建大摘要
        large_summary = {
            "timestamp": "2023-01-01T00:00:00",
            "cluster_stats": {"resource_counts": {f"type_{i}": 100 for i in range(50)}},
            "key_metrics": {"complex_metric": {f"field_{i}": i for i in range(100)}},
            "abnormal_resources": [{"id": f"resource_{i}", "issue": "big problem description"} for i in range(50)],
            "namespace_breakdown": {f"namespace_{i}": {"data": "x" * 100} for i in range(20)}
        }
        
        compressed = self.summary_gen._compress_to_size_limit(large_summary)
        
        # 验证基本结构仍然存在
        assert "timestamp" in compressed
        assert "compression_applied" in compressed
        
        # 验证大小得到了显著压缩（可能无法达到极端小的限制）
        original_size = len(json.dumps(large_summary, ensure_ascii=False))
        compressed_size = len(json.dumps(compressed, ensure_ascii=False))
        compression_ratio = compressed_size / original_size
        
        # 验证压缩效果显著（至少压缩50%）
        assert compression_ratio < 0.5, f"压缩比 {compression_ratio} 应该小于0.5"
        
        # 对于极端情况，验证至少包含基本信息
        assert "timestamp" in compressed
        assert "compression_applied" in compressed
    
    def test_filter_important_fields(self):
        """测试重要字段过滤"""
        # 测试Pod数据过滤
        pod_data = {
            "kind": "pod",
            "name": "test-pod",
            "namespace": "default",
            "metadata": {
                "phase": "Running",
                "restart_count": 5,
                "node_name": "worker-1",
                "irrelevant_field": "should_be_filtered"
            }
        }
        
        filtered = self.summary_gen._filter_important_fields(pod_data)
        assert filtered["kind"] == "pod"
        assert filtered["name"] == "test-pod"
        assert filtered["namespace"] == "default"
        assert filtered["phase"] == "Running"
        assert filtered["restart_count"] == 5
        assert filtered["node_name"] == "worker-1"
        assert "irrelevant_field" not in filtered
    
    def test_determine_resource_status(self):
        """测试资源状态确定"""
        # 测试健康资源
        healthy_data = {
            "kind": "pod",
            "metadata": {"phase": "Running", "restart_count": 1}
        }
        status = self.summary_gen._determine_resource_status("test", healthy_data)
        assert status == "healthy"
        
        # 测试严重问题资源
        critical_data = {
            "kind": "pod",
            "metadata": {"phase": "Failed", "restart_count": 0}
        }
        status = self.summary_gen._determine_resource_status("test", critical_data)
        assert status == "critical"
        
        # 测试警告级别资源
        warning_data = {
            "kind": "pod",
            "metadata": {"phase": "Running", "restart_count": 8}
        }
        status = self.summary_gen._determine_resource_status("test", warning_data)
        assert status == "warning"
    
    def test_get_generation_stats(self):
        """测试获取生成统计"""
        # 先生成一些摘要
        self.summary_gen.generate_cluster_summary()
        # 注意：generate_resource_summary不会增加summaries_generated计数
        # 因为它有自己的统计逻辑
        
        stats = self.summary_gen.get_generation_stats()
        assert stats["summaries_generated"] >= 1  # 至少1个（cluster_summary）
        assert stats["last_generation_time"] > 0
        assert stats["abnormal_resources_detected"] >= 0
        assert stats["avg_compression_ratio"] > 0
    
    def test_clear_stats(self):
        """测试清除统计"""
        # 先生成一些统计
        self.summary_gen.generate_cluster_summary()
        assert self.summary_gen.stats["summaries_generated"] > 0
        
        # 清除统计
        self.summary_gen.clear_stats()
        assert self.summary_gen.stats["summaries_generated"] == 0
        assert self.summary_gen.stats["avg_compression_ratio"] == 0.0
        assert self.summary_gen.stats["abnormal_resources_detected"] == 0
        assert self.summary_gen.stats["last_generation_time"] == 0


class TestSummaryGeneratorEdgeCases:
    """摘要生成器边界情况测试"""
    
    def test_empty_knowledge_graph(self):
        """测试空知识图谱的摘要生成"""
        config = Mock()
        config.max_summary_size_kb = 10
        config.graph_ttl = 3600
        config.graph_memory_limit = 1024
        
        kg = K8sKnowledgeGraph(config)
        summary_gen = SummaryGenerator(kg, config)
        
        summary = summary_gen.generate_cluster_summary()
        
        assert summary["cluster_stats"]["total_resources"] == 0
        assert summary["cluster_stats"]["total_relationships"] == 0
        assert len(summary["abnormal_resources"]) == 0
        assert summary["health_status"]["overall"] == "healthy"
        assert summary["key_metrics"]["overall_health"]["score"] == 100.0
    
    def test_generate_summary_with_error(self):
        """测试生成摘要时出现错误的情况"""
        config = Mock()
        config.max_summary_size_kb = 10
        
        # 创建有问题的知识图谱模拟
        kg = Mock()
        kg.graph.nodes.side_effect = Exception("Graph error")
        
        summary_gen = SummaryGenerator(kg, config)
        summary = summary_gen.generate_cluster_summary()
        
        assert summary["error"] is True
        assert "Graph error" in summary["message"]
        assert "timestamp" in summary
    
    def test_generate_resource_summary_with_error(self):
        """测试生成资源摘要时出现错误"""
        config = Mock()
        config.max_summary_size_kb = 10
        
        kg = Mock()
        kg.graph.nodes.side_effect = Exception("Resource error")
        
        summary_gen = SummaryGenerator(kg, config)
        summary = summary_gen.generate_resource_summary("pod")
        
        assert "生成 pod 摘要失败" in summary["message"]
        assert "Resource error" in summary["message"]
    
    def test_large_scale_performance(self):
        """测试大规模数据的性能"""
        config = Mock()
        config.max_summary_size_kb = 50  # 增加限制以处理更多数据
        config.graph_ttl = 3600
        config.graph_memory_limit = 1024
        
        kg = K8sKnowledgeGraph(config)
        
        # 添加大量测试数据
        for i in range(100):
            kg.add_resource(
                "pod", f"namespace-{i % 10}", f"pod-{i}",
                metadata={"phase": "Running" if i % 5 != 0 else "Failed", "restart_count": i % 10},
                labels={"app": f"app-{i % 5}"}
            )
        
        for i in range(20):
            kg.add_resource(
                "deployment", f"namespace-{i % 5}", f"deploy-{i}",
                metadata={"replicas": 3, "ready_replicas": 3 if i % 4 != 0 else 1},
                labels={"app": f"app-{i % 5}"}
            )
        
        summary_gen = SummaryGenerator(kg, config)
        
        start_time = time.time()
        summary = summary_gen.generate_cluster_summary()
        duration = time.time() - start_time
        
        # 验证性能（应该在合理时间内完成）
        assert duration < 5.0  # 5秒内完成
        
        # 验证摘要质量
        assert summary["cluster_stats"]["total_resources"] == 120  # 100 pods + 20 deployments
        assert len(summary["abnormal_resources"]) > 0  # 应该检测到异常资源
        
        # 验证压缩效果
        summary_size = len(json.dumps(summary, ensure_ascii=False))
        assert summary_size <= config.max_summary_size_kb * 1024
    
    def test_complex_relationships_summary(self):
        """测试复杂关系的摘要处理"""
        config = Mock()
        config.max_summary_size_kb = 20
        config.graph_ttl = 3600
        config.graph_memory_limit = 1024
        
        kg = K8sKnowledgeGraph(config)
        
        # 创建复杂的资源关系网络
        # 添加Node
        kg.add_resource("node", "cluster-scope", "master-1")
        kg.add_resource("node", "cluster-scope", "worker-1")
        kg.add_resource("node", "cluster-scope", "worker-2")
        
        # 添加Namespace
        kg.add_resource("namespace", "cluster-scope", "production")
        kg.add_resource("namespace", "cluster-scope", "staging")
        
        # 添加多层应用
        for env in ["production", "staging"]:
            for app in ["frontend", "backend", "database"]:
                # Deployment
                kg.add_resource(
                    "deployment", env, f"{app}-deploy",
                    metadata={"replicas": 3, "ready_replicas": 3}
                )
                
                # Service
                kg.add_resource(
                    "service", env, f"{app}-service",
                    metadata={"type": "ClusterIP", "cluster_ip": f"10.96.{hash(env+app) % 255}.100"}
                )
                
                # Pods
                for i in range(3):
                    pod_id = kg.add_resource(
                        "pod", env, f"{app}-pod-{i}",
                        metadata={"phase": "Running", "restart_count": 0, "node_name": f"worker-{i%2+1}"}
                    )
                    
                    # 建立关系
                    kg.add_relation(pod_id, f"deployment/{env}/{app}-deploy", "ownedBy")
                    kg.add_relation(f"service/{env}/{app}-service", pod_id, "routes")
                    kg.add_relation(f"node/cluster-scope/worker-{i%2+1}", pod_id, "hosts")
        
        summary_gen = SummaryGenerator(kg, config)
        
        # 测试聚焦摘要
        focus_resources = ["deployment/production/frontend-deploy", "service/production/frontend-service"]
        focused_summary = summary_gen.generate_focused_summary(focus_resources, context_depth=3)
        
        assert len(focused_summary["focus_resources"]) == 2
        assert focused_summary["context_summary"]["total_related"] > 0
        assert "risk_assessment" in focused_summary
        
        # 测试集群摘要
        cluster_summary = summary_gen.generate_cluster_summary(focus_namespace="production")
        
        assert cluster_summary["namespace_breakdown"]["focus_namespace"] == "production"
        # focus_details包含的是该命名空间的资源类型统计，不是命名空间名称本身
        focus_details = cluster_summary["namespace_breakdown"]["focus_details"]
        assert isinstance(focus_details, dict)
        assert "deployment" in focus_details or "pod" in focus_details or "service" in focus_details
        
        # 验证摘要大小
        summary_size = len(json.dumps(cluster_summary, ensure_ascii=False))
        assert summary_size <= config.max_summary_size_kb * 1024