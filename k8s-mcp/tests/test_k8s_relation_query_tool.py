"""
K8s关联查询工具单元测试

测试K8sRelationQueryTool类的各种功能：
- 工具初始化和配置
- 智能模式和基础模式
- 各种查询类型的执行
- 参数验证
- 结果格式化
- 错误处理
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.k8s_mcp.tools.k8s_relation_query import K8sRelationQueryTool
from src.k8s_mcp.core.mcp_protocol import MCPCallToolResult
from src.k8s_mcp.core.relation_query_handler import QueryResult, QueryType
from src.k8s_mcp.core.k8s_graph import K8sKnowledgeGraph
from src.k8s_mcp.core.summary_generator import SummaryGenerator


class TestK8sRelationQueryTool:
    """K8s关联查询工具测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock配置
        self.mock_config = Mock()
        self.mock_config.enable_knowledge_graph = True
        self.mock_config.namespace = "default"
        self.mock_config.graph_max_depth = 3
        self.mock_config.graph_ttl = 3600
        self.mock_config.graph_memory_limit = 1024
        self.mock_config.max_summary_size_kb = 10
        
        # Patch get_config
        self.get_config_patcher = patch('src.k8s_mcp.tools.k8s_relation_query.get_config')
        self.mock_get_config = self.get_config_patcher.start()
        self.mock_get_config.return_value = self.mock_config
        
    def teardown_method(self):
        """测试后清理"""
        self.get_config_patcher.stop()
    
    def test_init_with_intelligent_mode(self):
        """测试智能模式初始化"""
        tool = K8sRelationQueryTool()
        
        assert tool.name == "k8s-relation-query"
        assert "关联关系" in tool.description
        assert tool.config == self.mock_config
        assert tool.query_handler is not None
        assert tool.knowledge_graph is not None
        assert tool.summary_generator is not None
    
    def test_init_without_intelligent_mode(self):
        """测试基础模式初始化"""
        # 禁用知识图谱
        self.mock_config.enable_knowledge_graph = False
        
        tool = K8sRelationQueryTool()
        
        assert tool.name == "k8s-relation-query"
        assert tool.query_handler is None
        assert tool.knowledge_graph is None
        assert tool.summary_generator is None
    
    def test_init_with_component_failure(self):
        """测试组件初始化失败的情况"""
        # Mock K8sKnowledgeGraph构造函数抛出异常
        with patch('src.k8s_mcp.tools.k8s_relation_query.K8sKnowledgeGraph', side_effect=Exception("初始化失败")):
            tool = K8sRelationQueryTool()
            
            # 初始化失败时应该回退到基础模式
            assert tool.query_handler is None
    
    def test_get_schema(self):
        """测试获取工具Schema"""
        tool = K8sRelationQueryTool()
        schema = tool.get_schema()
        
        assert schema.name == "k8s-relation-query"
        assert schema.description is not None
        assert "query_type" in schema.input_schema["properties"]
        assert "target_resources" in schema.input_schema["properties"]
        assert "max_depth" in schema.input_schema["properties"]
        
        # 验证查询类型枚举
        query_type_enum = schema.input_schema["properties"]["query_type"]["enum"]
        expected_types = [
            "related_resources", "impact_analysis", "dependency_trace",
            "failure_propagation", "cluster_topology", "anomaly_correlation"
        ]
        for expected_type in expected_types:
            assert expected_type in query_type_enum
    
    def test_validate_arguments_valid(self):
        """测试有效参数验证"""
        tool = K8sRelationQueryTool()
        
        # 测试关联资源查询
        assert tool._validate_arguments("related_resources", ["pod/default/test-pod"])
        
        # 测试集群拓扑查询（不需要目标资源）
        assert tool._validate_arguments("cluster_topology", [])
        
        # 测试多个目标资源
        assert tool._validate_arguments("impact_analysis", [
            "pod/default/test-pod", "deployment/default/test-deploy"
        ])
    
    def test_validate_arguments_invalid(self):
        """测试无效参数验证"""
        tool = K8sRelationQueryTool()
        
        # 测试无效查询类型
        assert not tool._validate_arguments("invalid_type", ["pod/default/test-pod"])
        
        # 测试需要目标资源但未提供
        assert not tool._validate_arguments("related_resources", [])
        
        # 测试无效资源ID格式
        assert not tool._validate_arguments("related_resources", ["invalid-resource-id"])
        assert not tool._validate_arguments("related_resources", ["pod/default"])  # 缺少名称
        assert not tool._validate_arguments("related_resources", ["pod//test"])  # 空命名空间
    
    def test_is_valid_resource_id(self):
        """测试资源ID格式验证"""
        tool = K8sRelationQueryTool()
        
        # 有效格式
        assert tool._is_valid_resource_id("pod/default/test-pod")
        assert tool._is_valid_resource_id("deployment/kube-system/coredns")
        assert tool._is_valid_resource_id("service/frontend/web-service")
        
        # 无效格式
        assert not tool._is_valid_resource_id("pod/default")  # 缺少名称
        assert not tool._is_valid_resource_id("pod/default/test/extra")  # 多余部分
        assert not tool._is_valid_resource_id("pod//test")  # 空命名空间
        assert not tool._is_valid_resource_id("/default/test")  # 空类型
        assert not tool._is_valid_resource_id("pod/default/")  # 空名称
    
    @pytest.mark.asyncio
    async def test_execute_basic_mode(self):
        """测试基础模式执行"""
        # 禁用知识图谱
        self.mock_config.enable_knowledge_graph = False
        tool = K8sRelationQueryTool()
        
        arguments = {
            "query_type": "related_resources",
            "target_resources": ["pod/default/test-pod"]
        }
        
        result = await tool.execute(arguments)
        
        assert isinstance(result, MCPCallToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        assert "basic_mode" in result.content[0]["text"]
        assert "ENABLE_KNOWLEDGE_GRAPH=true" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_execute_intelligent_mode_related_resources(self):
        """测试智能模式关联资源查询"""
        tool = K8sRelationQueryTool()
        
        # Mock查询处理器
        mock_result = QueryResult(
            query_id="test123",
            query_type=QueryType.RELATED_RESOURCES,
            target_resources=["pod/default/test-pod"],
            results=[
                {
                    "resource_id": "deployment/default/test-deploy",
                    "kind": "deployment",
                    "namespace": "default",
                    "name": "test-deploy",
                    "relation": "ownedBy",
                    "relation_direction": "outgoing",
                    "depth": 1
                }
            ],
            metadata={"total_nodes": 10, "total_edges": 15},
            execution_time=0.05,
            timestamp="2023-01-01T00:00:00",
            success=True
        )
        
        tool.query_handler.query_related_resources = Mock(return_value=mock_result)
        
        arguments = {
            "query_type": "related_resources",
            "target_resources": ["pod/default/test-pod"],
            "max_depth": 2,
            "include_metadata": True
        }
        
        result = await tool.execute(arguments)
        
        assert isinstance(result, MCPCallToolResult)
        assert not result.is_error
        assert len(result.content) == 1
        
        # 验证查询处理器被调用
        tool.query_handler.query_related_resources.assert_called_once()
        
        # 验证结果格式
        import json
        result_data = json.loads(result.content[0]["text"])
        assert result_data["success"] is True
        assert result_data["query_type"] == "related_resources"
        assert result_data["results_count"] == 1
        assert "summary" in result_data
    
    @pytest.mark.asyncio
    async def test_execute_intelligent_mode_impact_analysis(self):
        """测试智能模式影响分析"""
        tool = K8sRelationQueryTool()
        
        # Mock查询处理器
        mock_result = QueryResult(
            query_id="test456",
            query_type=QueryType.IMPACT_ANALYSIS,
            target_resources=["deployment/default/test-deploy"],
            results=[
                {
                    "source_resource": "deployment/default/test-deploy",
                    "affected_resource": "pod/default/test-pod-1",
                    "impact_level": 1,
                    "risk_score": 75.0
                }
            ],
            metadata={},
            execution_time=0.03,
            timestamp="2023-01-01T00:00:00",
            success=True
        )
        
        tool.query_handler.analyze_impact = Mock(return_value=mock_result)
        
        arguments = {
            "query_type": "impact_analysis",
            "target_resources": ["deployment/default/test-deploy"],
            "include_health_info": True
        }
        
        result = await tool.execute(arguments)
        
        assert not result.is_error
        tool.query_handler.analyze_impact.assert_called_once()
        
        # 验证结果包含影响分析摘要
        import json
        result_data = json.loads(result.content[0]["text"])
        assert "summary" in result_data
        assert "risk_assessment" in result_data["summary"]
    
    @pytest.mark.asyncio
    async def test_execute_intelligent_mode_cluster_topology(self):
        """测试智能模式集群拓扑发现"""
        tool = K8sRelationQueryTool()
        
        # Mock查询处理器
        mock_result = QueryResult(
            query_id="test789",
            query_type=QueryType.CLUSTER_TOPOLOGY,
            target_resources=[],
            results=[
                {
                    "level": "node",
                    "resource_id": "node/cluster-scope/worker-1",
                    "name": "worker-1",
                    "hosted_resources": 5,
                    "health_status": "healthy"
                },
                {
                    "level": "namespace",
                    "resource_id": "namespace/default",
                    "name": "default",
                    "total_resources": 10
                }
            ],
            metadata={},
            execution_time=0.02,
            timestamp="2023-01-01T00:00:00",
            success=True
        )
        
        tool.query_handler.discover_cluster_topology = Mock(return_value=mock_result)
        
        arguments = {
            "query_type": "cluster_topology",
            "focus_namespace": "default",
            "resource_types": ["pod", "service"]
        }
        
        result = await tool.execute(arguments)
        
        assert not result.is_error
        tool.query_handler.discover_cluster_topology.assert_called_once_with("default", ["pod", "service"])
        
        # 验证结果包含拓扑摘要
        import json
        result_data = json.loads(result.content[0]["text"])
        assert "summary" in result_data
        assert "cluster_overview" in result_data["summary"]
    
    @pytest.mark.asyncio
    async def test_execute_validation_failure(self):
        """测试参数验证失败"""
        tool = K8sRelationQueryTool()
        
        arguments = {
            "query_type": "invalid_type",
            "target_resources": ["pod/default/test-pod"]
        }
        
        result = await tool.execute(arguments)
        
        assert isinstance(result, MCPCallToolResult)
        assert result.is_error
        assert "参数验证失败" in result.content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_execute_query_handler_exception(self):
        """测试查询处理器异常"""
        tool = K8sRelationQueryTool()
        
        # Mock查询处理器抛出异常
        tool.query_handler.query_related_resources = Mock(side_effect=Exception("查询失败"))
        
        arguments = {
            "query_type": "related_resources",
            "target_resources": ["pod/default/test-pod"]
        }
        
        result = await tool.execute(arguments)
        
        assert isinstance(result, MCPCallToolResult)
        assert result.is_error
        assert "关联查询执行失败" in result.content[0]["text"]
    
    def test_convert_query_type(self):
        """测试查询类型转换"""
        tool = K8sRelationQueryTool()
        
        # 测试所有有效的查询类型转换
        assert tool._convert_query_type("related_resources") == QueryType.RELATED_RESOURCES
        assert tool._convert_query_type("impact_analysis") == QueryType.IMPACT_ANALYSIS
        assert tool._convert_query_type("dependency_trace") == QueryType.DEPENDENCY_TRACE
        assert tool._convert_query_type("failure_propagation") == QueryType.FAILURE_PROPAGATION
        assert tool._convert_query_type("cluster_topology") == QueryType.CLUSTER_TOPOLOGY
        assert tool._convert_query_type("anomaly_correlation") == QueryType.ANOMALY_CORRELATION
        
        # 测试无效类型（应返回默认值）
        assert tool._convert_query_type("invalid_type") == QueryType.RELATED_RESOURCES
    
    def test_format_query_result_success(self):
        """测试成功结果格式化"""
        tool = K8sRelationQueryTool()
        
        mock_result = QueryResult(
            query_id="test123",
            query_type=QueryType.RELATED_RESOURCES,
            target_resources=["pod/default/test-pod"],
            results=[
                {"resource_id": "deployment/default/test-deploy", "relation": "ownedBy", "depth": 1}
            ],
            metadata={"total_nodes": 10},
            execution_time=0.05,
            timestamp="2023-01-01T00:00:00",
            success=True
        )
        
        formatted = tool._format_query_result(mock_result, 0.05)
        
        import json
        result_data = json.loads(formatted)
        
        assert result_data["success"] is True
        assert result_data["query_id"] == "test123"
        assert result_data["query_type"] == "related_resources"
        assert result_data["results_count"] == 1
        assert "summary" in result_data
    
    def test_format_query_result_failure(self):
        """测试失败结果格式化"""
        tool = K8sRelationQueryTool()
        
        mock_result = QueryResult(
            query_id="test456",
            query_type=QueryType.RELATED_RESOURCES,
            target_resources=["pod/default/test-pod"],
            results=[],
            metadata={},
            execution_time=0.01,
            timestamp="2023-01-01T00:00:00",
            success=False,
            error_message="查询失败"
        )
        
        formatted = tool._format_query_result(mock_result, 0.01)
        
        import json
        result_data = json.loads(formatted)
        
        assert result_data["success"] is False
        assert result_data["error"] == "查询失败"
        assert result_data["execution_time"] == 0.01
    
    def test_summarize_related_resources(self):
        """测试关联资源结果汇总"""
        tool = K8sRelationQueryTool()
        
        results = [
            {"resource_id": "deploy1", "relation": "ownedBy", "depth": 1},
            {"resource_id": "deploy2", "relation": "ownedBy", "depth": 1},
            {"resource_id": "service1", "relation": "routes", "depth": 2},
        ]
        
        summary = tool._summarize_related_resources(results)
        
        assert summary["total_related"] == 3
        assert summary["by_relation_type"]["ownedBy"] == 2
        assert summary["by_relation_type"]["routes"] == 1
        assert summary["by_depth"][1] == 2
        assert summary["by_depth"][2] == 1
        assert summary["max_depth"] == 2
    
    def test_summarize_related_resources_empty(self):
        """测试空关联资源结果汇总"""
        tool = K8sRelationQueryTool()
        
        summary = tool._summarize_related_resources([])
        
        assert "message" in summary
        assert "未找到关联资源" in summary["message"]
    
    def test_summarize_impact_analysis(self):
        """测试影响分析结果汇总"""
        tool = K8sRelationQueryTool()
        
        results = [
            {"impact_level": 1, "risk_score": 80.0},
            {"impact_level": 2, "risk_score": 60.0},
            {"impact_level": 1, "risk_score": 90.0},
        ]
        
        summary = tool._summarize_impact_analysis(results)
        
        assert summary["total_affected"] == 3
        assert summary["by_impact_level"][1] == 2
        assert summary["by_impact_level"][2] == 1
        assert summary["risk_assessment"]["max_risk_score"] == 90.0
        assert abs(summary["risk_assessment"]["avg_risk_score"] - 76.67) < 0.01  # (80+60+90)/3
        assert summary["risk_assessment"]["high_risk_count"] == 2  # >= 70
    
    def test_summarize_dependency_trace(self):
        """测试依赖追踪结果汇总"""
        tool = K8sRelationQueryTool()
        
        results = [
            {"dependency_level": 1, "criticality": 85.0},
            {"dependency_level": 2, "criticality": 75.0},
            {"dependency_level": 1, "criticality": 95.0},
        ]
        
        summary = tool._summarize_dependency_trace(results)
        
        assert summary["total_dependencies"] == 3
        assert summary["by_dependency_level"][1] == 2
        assert summary["by_dependency_level"][2] == 1
        assert summary["criticality_assessment"]["max_criticality"] == 95.0
        assert summary["criticality_assessment"]["critical_dependencies"] == 2  # >= 80
    
    def test_summarize_failure_propagation(self):
        """测试故障传播结果汇总"""
        tool = K8sRelationQueryTool()
        
        results = [
            {"propagation_probability": 0.8, "severity": "high"},
            {"propagation_probability": 0.6, "severity": "medium"},
            {"propagation_probability": 0.9, "severity": "high"},
        ]
        
        summary = tool._summarize_failure_propagation(results)
        
        assert summary["total_propagation_paths"] == 3
        assert summary["probability_assessment"]["max_probability"] == 0.9
        assert summary["probability_assessment"]["high_probability_paths"] == 2  # >= 0.7
        assert summary["severity_distribution"]["high"] == 2
        assert summary["severity_distribution"]["medium"] == 1
    
    def test_summarize_cluster_topology(self):
        """测试集群拓扑结果汇总"""
        tool = K8sRelationQueryTool()
        
        results = [
            {"level": "node", "health_status": "healthy", "hosted_resources": 5},
            {"level": "node", "health_status": "critical", "hosted_resources": 3},
            {"level": "namespace", "total_resources": 10},
            {"level": "namespace", "total_resources": 8},
        ]
        
        summary = tool._summarize_cluster_topology(results)
        
        node_summary = summary["cluster_overview"]["nodes"]
        assert node_summary["total_nodes"] == 2
        assert node_summary["healthy_nodes"] == 1
        assert node_summary["total_hosted_resources"] == 8  # 5 + 3
        
        namespace_summary = summary["cluster_overview"]["namespaces"]
        assert namespace_summary["total_namespaces"] == 2
        assert namespace_summary["total_namespace_resources"] == 18  # 10 + 8
    
    def test_get_execution_stats_with_handler(self):
        """测试获取执行统计（有查询处理器）"""
        tool = K8sRelationQueryTool()
        tool.execution_count = 5
        tool.last_execution_time = "2023-01-01T00:00:00"
        
        # Mock查询处理器统计
        tool.query_handler.get_query_stats = Mock(return_value={
            "queries_executed": 10,
            "avg_execution_time": 0.05
        })
        
        stats = tool.get_execution_stats()
        
        assert stats["tool_name"] == "k8s-relation-query"
        assert stats["execution_count"] == 5
        assert stats["intelligent_mode_enabled"] is True
        assert "query_handler_stats" in stats
        assert stats["query_handler_stats"]["queries_executed"] == 10
    
    def test_get_execution_stats_without_handler(self):
        """测试获取执行统计（无查询处理器）"""
        # 禁用知识图谱
        self.mock_config.enable_knowledge_graph = False
        tool = K8sRelationQueryTool()
        
        stats = tool.get_execution_stats()
        
        assert stats["tool_name"] == "k8s-relation-query"
        assert stats["intelligent_mode_enabled"] is False
        assert "query_handler_stats" not in stats


class TestK8sRelationQueryToolIntegration:
    """K8s关联查询工具集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock配置
        self.mock_config = Mock()
        self.mock_config.enable_knowledge_graph = True
        self.mock_config.namespace = "default"
        self.mock_config.graph_max_depth = 3
        self.mock_config.graph_ttl = 3600
        self.mock_config.graph_memory_limit = 1024
        self.mock_config.max_summary_size_kb = 10
        
        # Patch get_config
        self.get_config_patcher = patch('src.k8s_mcp.tools.k8s_relation_query.get_config')
        self.mock_get_config = self.get_config_patcher.start()
        self.mock_get_config.return_value = self.mock_config
    
    def teardown_method(self):
        """测试后清理"""
        self.get_config_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_tool_registration_and_execution(self):
        """测试工具注册和执行流程"""
        from src.k8s_mcp.core.tool_registry import tool_registry
        
        # 创建工具并注册
        tool = K8sRelationQueryTool()
        success = tool_registry.register(tool, "test")
        
        assert success is True
        
        # 获取工具Schema
        schema = tool.get_schema()
        assert schema.name == "k8s-relation-query"
        
        # 模拟工具执行
        arguments = {
            "query_type": "cluster_topology"
        }
        
        result = await tool.execute(arguments)
        assert isinstance(result, MCPCallToolResult)
        
        # 清理注册
        tool_registry._tools.clear()
    
    @pytest.mark.asyncio
    async def test_multiple_query_types_execution(self):
        """测试多种查询类型的执行"""
        tool = K8sRelationQueryTool()
        
        # 测试查询类型列表
        test_cases = [
            {
                "query_type": "related_resources",
                "target_resources": ["pod/default/test-pod"]
            },
            {
                "query_type": "impact_analysis",
                "target_resources": ["deployment/default/test-deploy"]
            },
            {
                "query_type": "dependency_trace",
                "target_resources": ["service/default/test-service"]
            },
            {
                "query_type": "cluster_topology"
            }
        ]
        
        for test_case in test_cases:
            result = await tool.execute(test_case)
            assert isinstance(result, MCPCallToolResult)
            # 在智能模式下，所有查询都应该成功或返回基础模式响应
            # 在基础模式下，应该返回提示信息
    
    def test_tool_schema_validation(self):
        """测试工具Schema验证"""
        tool = K8sRelationQueryTool()
        schema = tool.get_schema()
        
        # 验证必需字段
        assert "type" in schema.input_schema
        assert "properties" in schema.input_schema
        assert "required" in schema.input_schema
        
        # 验证查询类型枚举的完整性
        query_type_prop = schema.input_schema["properties"]["query_type"]
        assert len(query_type_prop["enum"]) == 6  # 6种查询类型
        
        # 验证资源ID格式限制
        target_resources_prop = schema.input_schema["properties"]["target_resources"]
        assert "pattern" in target_resources_prop["items"]
        
        # 验证数值范围限制
        max_depth_prop = schema.input_schema["properties"]["max_depth"]
        assert max_depth_prop["minimum"] == 1
        assert max_depth_prop["maximum"] == 5
        
        max_results_prop = schema.input_schema["properties"]["max_results"]
        assert max_results_prop["minimum"] == 1
        assert max_results_prop["maximum"] == 500