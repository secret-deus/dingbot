"""
K8s集群摘要工具测试模块

测试K8sClusterSummaryTool的各种功能：
- 工具初始化和配置
- Schema定义和参数验证
- 智能模式和基础模式执行
- 不同摘要范围的处理
- 异常检测和性能分析
- 数据压缩和输出控制
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# 导入待测试的模块
from src.k8s_mcp.tools.k8s_cluster_summary import K8sClusterSummaryTool
from src.k8s_mcp.core.mcp_protocol import MCPCallToolResult, MCPToolSchema
from src.k8s_mcp.core.k8s_graph import K8sKnowledgeGraph
from src.k8s_mcp.core.summary_generator import SummaryGenerator
from src.k8s_mcp.config import K8sConfig


class TestK8sClusterSummaryTool:
    """测试K8sClusterSummaryTool基础功能"""

    def setup_method(self):
        """测试前设置"""
        # 模拟配置
        self.mock_config = Mock(spec=K8sConfig)
        self.mock_config.enable_knowledge_graph = False
        self.mock_config.graph_ttl = 3600
        self.mock_config.graph_memory_limit = 1024
        self.mock_config.max_summary_size_kb = 10
        
    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_init_basic_mode(self, mock_get_config):
        """测试基础模式初始化"""
        mock_get_config.return_value = self.mock_config
        
        tool = K8sClusterSummaryTool()
        
        assert tool.name == "k8s-cluster-summary"
        assert "集群摘要" in tool.description
        assert not tool.intelligent_mode
        assert tool.kg is None
        assert tool.summary_generator is None
        assert tool.execution_count == 0

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_init_intelligent_mode(self, mock_get_config):
        """测试智能模式初始化"""
        self.mock_config.enable_knowledge_graph = True
        mock_get_config.return_value = self.mock_config
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph') as mock_kg, \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator') as mock_sg:
            
            tool = K8sClusterSummaryTool()
            
            assert tool.intelligent_mode
            assert tool.kg is not None
            assert tool.summary_generator is not None
            mock_kg.assert_called_once()
            mock_sg.assert_called_once()

    def test_get_schema(self):
        """测试工具Schema定义"""
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config') as mock_get_config:
            mock_get_config.return_value = self.mock_config
            tool = K8sClusterSummaryTool()
            
        schema = tool.get_schema()
        
        assert isinstance(schema, MCPToolSchema)
        assert schema.name == "k8s-cluster-summary"
        assert "集群摘要" in schema.description
        
        # 检查Schema属性
        properties = schema.input_schema["properties"]
        assert "scope" in properties
        assert "focus_namespace" in properties
        assert "include_details" in properties
        assert "max_size_kb" in properties
        assert "anomaly_threshold" in properties
        
        # 检查scope枚举值
        scope_enum = properties["scope"]["enum"]
        expected_scopes = ["cluster", "namespace", "health", "resources", "anomalies", "performance"]
        for scope in expected_scopes:
            assert scope in scope_enum

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_basic_mode(self, mock_get_config):
        """测试基础模式执行"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        args = {"scope": "cluster"}
        result = await tool.execute(args)
        
        assert not result.is_error
        assert len(result.content) == 1
        
        response_data = json.loads(result.content[0].text)
        assert response_data["status"] == "basic_mode"
        assert "basic_mode" in response_data["message"]
        assert response_data["scope"] == "cluster"
        assert "recommendations" in response_data
        assert "alternative_tools" in response_data["recommendations"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_intelligent_mode_cluster(self, mock_get_config):
        """测试智能模式集群摘要"""
        self.mock_config.enable_knowledge_graph = True
        mock_get_config.return_value = self.mock_config
        
        # 模拟知识图谱和摘要生成器
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_kg.graph.nodes = {}
        mock_kg.graph.edges = {}
        
        mock_sg = Mock(spec=SummaryGenerator)
        mock_cluster_summary = {
            "cluster_stats": {"total_pods": 10},
            "health_status": {"overall": "healthy"},
            "abnormal_resources": [],
            "namespace_breakdown": {}
        }
        mock_sg.generate_cluster_summary.return_value = mock_cluster_summary
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            args = {"scope": "cluster", "include_details": True}
            result = await tool.execute(args)
            
            assert not result.is_error
            response_data = json.loads(result.content[0].text)
            assert response_data["scope"] == "cluster"
            assert response_data["generation_mode"] == "intelligent"
            assert "features" in response_data
            assert response_data["features"]["knowledge_graph_enabled"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_namespace_scope(self, mock_get_config):
        """测试命名空间范围摘要"""
        self.mock_config.enable_knowledge_graph = True
        mock_get_config.return_value = self.mock_config
        
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_kg.graph.nodes = {}
        mock_kg.graph.edges = {}
        
        mock_sg = Mock(spec=SummaryGenerator)
        mock_cluster_summary = {
            "namespace_breakdown": {
                "default": {
                    "resource_count": 5,
                    "resource_types": {"Pod": 3, "Service": 2},
                    "health_status": "healthy"
                }
            },
            "abnormal_resources": []
        }
        mock_sg.generate_cluster_summary.return_value = mock_cluster_summary
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            args = {"scope": "namespace", "focus_namespace": "default"}
            result = await tool.execute(args)
            
            assert not result.is_error
            response_data = json.loads(result.content[0].text)
            assert response_data["scope"] == "namespace"
            assert response_data["target_namespace"] == "default"
            assert "resource_count" in response_data

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_health_scope(self, mock_get_config):
        """测试健康状态摘要"""
        self.mock_config.enable_knowledge_graph = True
        mock_get_config.return_value = self.mock_config
        
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_kg.graph.nodes = {}
        mock_kg.graph.edges = {}
        
        mock_sg = Mock(spec=SummaryGenerator)
        mock_cluster_summary = {
            "health_status": {
                "overall": "warning",
                "score": 75,
                "breakdown": {"pods": "healthy", "nodes": "warning"}
            },
            "abnormal_resources": [
                {"kind": "Pod", "name": "test-pod", "severity": "critical", "severity_score": 100},
                {"kind": "Node", "name": "test-node", "severity": "warning", "severity_score": 60}
            ]
        }
        mock_sg.generate_cluster_summary.return_value = mock_cluster_summary
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            args = {"scope": "health", "anomaly_threshold": "medium"}
            result = await tool.execute(args)
            
            assert not result.is_error
            response_data = json.loads(result.content[0].text)
            assert response_data["scope"] == "health"
            assert response_data["overall_health"] == "warning"
            assert response_data["health_score"] == 75
            assert "critical_issues" in response_data
            assert "warning_issues" in response_data

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, mock_get_config):
        """测试参数验证失败"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 无效的scope
        args = {"scope": "invalid_scope"}
        result = await tool.execute(args)
        
        assert result.is_error
        response_data = json.loads(result.content[0].text)
        assert "参数验证失败" in response_data["error"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_namespace_validation_failure(self, mock_get_config):
        """测试命名空间参数验证失败"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 命名空间范围但未指定namespace
        args = {"scope": "namespace"}
        result = await tool.execute(args)
        
        assert result.is_error
        response_data = json.loads(result.content[0].text)
        assert "focus_namespace" in response_data["error"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_size_limit_validation(self, mock_get_config):
        """测试大小限制验证"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 无效的大小限制
        args = {"scope": "cluster", "max_size_kb": 100}
        result = await tool.execute(args)
        
        assert result.is_error
        response_data = json.loads(result.content[0].text)
        assert "大小限制" in response_data["error"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, mock_get_config):
        """测试异常处理"""
        self.mock_config.enable_knowledge_graph = True
        mock_get_config.return_value = self.mock_config
        
        # 模拟摘要生成器抛出异常
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_sg = Mock(spec=SummaryGenerator)
        mock_sg.generate_cluster_summary.side_effect = Exception("测试异常")
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            args = {"scope": "cluster"}
            result = await tool.execute(args)
            
            assert result.is_error
            response_data = json.loads(result.content[0].text)
            assert "生成失败" in response_data["error"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_categorize_anomalies(self, mock_get_config):
        """测试异常分类功能"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        anomalies = [
            {"kind": "Pod", "reason": "ImagePullBackOff"},
            {"kind": "Deployment", "reason": "ProgressDeadlineExceeded"},
            {"kind": "Service", "reason": "EndpointsNotReady"},
            {"kind": "Node", "reason": "NetworkUnavailable"},
            {"kind": "PersistentVolume", "reason": "VolumeFailure"}
        ]
        
        categories = tool._categorize_anomalies(anomalies)
        
        assert categories["pod_failures"] == 1
        assert categories["deployment_issues"] == 1
        assert categories["service_problems"] == 1
        assert categories["node_issues"] == 1

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_detect_anomaly_patterns(self, mock_get_config):
        """测试异常模式检测"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 模拟多个镜像拉取失败
        anomalies = [
            {"kind": "Pod", "reason": "ImagePullBackOff", "namespace": "default"},
            {"kind": "Pod", "reason": "ImagePullBackOff", "namespace": "app"},
            {"kind": "Pod", "reason": "ImagePullBackOff", "namespace": "test"}
        ]
        
        patterns = tool._detect_anomaly_patterns(anomalies)
        
        assert len(patterns) > 0
        assert any("镜像拉取失败" in pattern for pattern in patterns)

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_calculate_resource_distribution(self, mock_get_config):
        """测试资源分布计算"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        stats = {"Pod": 10, "Service": 5, "Deployment": 3}
        
        distribution = tool._calculate_resource_distribution(stats)
        
        assert distribution["Pod"]["count"] == 10
        assert distribution["Pod"]["percentage"] == 55.56
        assert distribution["Service"]["count"] == 5
        assert abs(distribution["Service"]["percentage"] - 27.78) < 0.01

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_identify_performance_bottlenecks(self, mock_get_config):
        """测试性能瓶颈识别"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 高CPU利用率场景
        metrics = {
            "node_utilization": {
                "average_cpu_percent": 85,
                "average_memory_percent": 60
            }
        }
        
        bottlenecks = tool._identify_performance_bottlenecks(metrics)
        
        assert len(bottlenecks) > 0
        assert any("CPU利用率过高" in bottleneck for bottleneck in bottlenecks)

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_compress_summary_to_size(self, mock_get_config):
        """测试摘要压缩功能"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 创建一个大的摘要对象
        large_summary = {
            "basic_info": {"key": "value"},
            "detailed_analysis": {"large_data": "x" * 1000},
            "abnormal_resources": [{"resource": f"test-{i}"} for i in range(20)],
            "generation_info": {
                "timestamp": "2023-01-01",
                "detailed_metadata": {"extra": "data"}
            }
        }
        
        compressed = tool._compress_summary_to_size(large_summary, 1)  # 1KB limit
        
        # 检查压缩后的大小
        compressed_size = len(json.dumps(compressed).encode('utf-8'))
        assert compressed_size <= 1024
        
        # 检查关键信息是否保留
        assert "basic_info" in compressed

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_execution_stats(self, mock_get_config):
        """测试执行统计功能"""
        mock_get_config.return_value = self.mock_config
        tool = K8sClusterSummaryTool()
        
        # 更新执行统计
        tool._update_execution_stats(0.5)
        tool._update_execution_stats(0.3)
        
        stats = tool.get_execution_stats()
        
        assert stats["execution_count"] == 2
        assert stats["last_execution_time"] == 0.3
        assert abs(stats["avg_execution_time"] - 0.4) < 0.01
        assert "intelligent_mode_enabled" in stats


class TestK8sClusterSummaryToolIntegration:
    """测试K8sClusterSummaryTool集成功能"""

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_tool_registration(self, mock_get_config):
        """测试工具注册"""
        mock_config = Mock(spec=K8sConfig)
        mock_config.enable_knowledge_graph = False
        mock_get_config.return_value = mock_config
        
        from src.k8s_mcp.core.tool_registry import tool_registry
        
        tool = K8sClusterSummaryTool()
        success = tool_registry.register(tool, "test")
        
        assert success
        
        # 清理注册
        tool_registry._tools.clear()

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    def test_tool_schema_validation(self, mock_get_config):
        """测试工具Schema验证"""
        mock_config = Mock(spec=K8sConfig)
        mock_config.enable_knowledge_graph = False
        mock_get_config.return_value = mock_config
        
        tool = K8sClusterSummaryTool()
        schema = tool.get_schema()
        
        # 验证必需字段
        assert "scope" in schema.input_schema["required"]
        
        # 验证枚举值
        properties = schema.input_schema["properties"]
        assert "cluster" in properties["scope"]["enum"]
        assert "namespace" in properties["scope"]["enum"]
        assert "health" in properties["scope"]["enum"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_end_to_end_basic_mode(self, mock_get_config):
        """测试端到端基础模式执行"""
        mock_config = Mock(spec=K8sConfig)
        mock_config.enable_knowledge_graph = False
        mock_get_config.return_value = mock_config
        
        tool = K8sClusterSummaryTool()
        
        # 测试不同的摘要范围
        test_cases = [
            {"scope": "cluster"},
            {"scope": "health", "anomaly_threshold": "high"},
            {"scope": "resources", "resource_types": ["Pod", "Service"]},
            {"scope": "performance", "time_range": "24h"}
        ]
        
        for args in test_cases:
            result = await tool.execute(args)
            assert not result.is_error
            
            response_data = json.loads(result.content[0].text)
            assert response_data["status"] == "basic_mode"
            assert response_data["scope"] == args["scope"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_end_to_end_intelligent_mode(self, mock_get_config):
        """测试端到端智能模式执行"""
        mock_config = Mock(spec=K8sConfig)
        mock_config.enable_knowledge_graph = True
        mock_config.graph_ttl = 3600
        mock_config.graph_memory_limit = 1024
        mock_config.max_summary_size_kb = 10
        mock_get_config.return_value = mock_config
        
        # 模拟完整的智能组件
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_kg.graph.nodes = {"test-pod": {"kind": "Pod"}}
        mock_kg.graph.edges = []
        
        mock_sg = Mock(spec=SummaryGenerator)
        mock_sg.generate_cluster_summary.return_value = {
            "cluster_stats": {"total_pods": 1},
            "health_status": {"overall": "healthy", "score": 95},
            "abnormal_resources": [],
            "namespace_breakdown": {"default": {"resource_count": 1}},
            "key_metrics": {"node_utilization": {"average_cpu_percent": 30}}
        }
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            # 测试集群摘要
            args = {"scope": "cluster", "include_details": True, "max_size_kb": 5}
            result = await tool.execute(args)
            
            assert not result.is_error
            response_data = json.loads(result.content[0].text)
            assert response_data["generation_mode"] == "intelligent"
            assert "features" in response_data
            assert response_data["features"]["knowledge_graph_enabled"]

    @patch('src.k8s_mcp.tools.k8s_cluster_summary.get_config')
    @pytest.mark.asyncio
    async def test_comprehensive_anomaly_analysis(self, mock_get_config):
        """测试综合异常分析"""
        mock_config = Mock(spec=K8sConfig)
        mock_config.enable_knowledge_graph = True
        mock_config.graph_ttl = 3600
        mock_config.graph_memory_limit = 1024
        mock_get_config.return_value = mock_config
        
        # 模拟复杂的异常场景
        complex_anomalies = [
            {"kind": "Pod", "name": "app-1", "namespace": "prod", "reason": "ImagePullBackOff", "severity": "critical", "severity_score": 90},
            {"kind": "Pod", "name": "app-2", "namespace": "prod", "reason": "CrashLoopBackOff", "severity": "critical", "severity_score": 95},
            {"kind": "Node", "name": "node-1", "reason": "DiskPressure", "severity": "warning", "severity_score": 70},
            {"kind": "Service", "name": "api-svc", "namespace": "prod", "reason": "EndpointsNotReady", "severity": "warning", "severity_score": 60},
            {"kind": "Pod", "name": "sys-pod", "namespace": "kube-system", "reason": "OutOfMemory", "severity": "critical", "severity_score": 100}
        ]
        
        mock_kg = Mock(spec=K8sKnowledgeGraph)
        mock_sg = Mock(spec=SummaryGenerator)
        mock_sg.generate_cluster_summary.return_value = {
            "health_status": {"overall": "critical", "score": 40},
            "abnormal_resources": complex_anomalies
        }
        
        with patch('src.k8s_mcp.tools.k8s_cluster_summary.K8sKnowledgeGraph', return_value=mock_kg), \
             patch('src.k8s_mcp.tools.k8s_cluster_summary.SummaryGenerator', return_value=mock_sg):
            
            tool = K8sClusterSummaryTool()
            
            args = {"scope": "anomalies", "anomaly_threshold": "medium"}
            result = await tool.execute(args)
            
            assert not result.is_error
            response_data = json.loads(result.content[0].text)
            assert response_data["scope"] == "anomalies"
            assert response_data["total_anomalies"] >= 4  # 过滤后的异常数量
            assert "anomaly_categories" in response_data
            assert "patterns" in response_data