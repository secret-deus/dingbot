"""
K8s MCP服务器集成测试模块

测试K8sMCPServer的智能组件集成：
- 服务器初始化和智能组件集成
- 配置开关控制
- 智能功能API端点
- 服务生命周期管理
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.k8s_mcp.server import K8sMCPServer
from src.k8s_mcp.config import K8sConfig


class TestK8sMCPServerIntelligentIntegration:
    """测试K8sMCPServer智能集成功能"""

    def setup_method(self):
        """测试前设置"""
        self.basic_config = K8sConfig()
        self.basic_config.enable_knowledge_graph = False
        
        self.intelligent_config = K8sConfig()
        self.intelligent_config.enable_knowledge_graph = True
        self.intelligent_config.graph_ttl = 3600
        self.intelligent_config.graph_memory_limit = 1024

    def test_basic_mode_server_initialization(self):
        """测试基础模式服务器初始化"""
        server = K8sMCPServer(self.basic_config)
        
        # 检查服务器基本属性
        assert server.config == self.basic_config
        assert server.app is not None
        assert server.k8s_client is None
        assert server.is_running is False
        
        # 检查智能组件状态
        assert server.knowledge_graph is None
        assert server.cluster_sync_engine is None
        assert server.summary_generator is None
        assert server.intelligent_mode_enabled is False
        
        # 检查智能状态
        status = server.get_intelligent_status()
        assert status["intelligent_mode_enabled"] is False
        assert status["knowledge_graph_available"] is False
        assert status["cluster_sync_running"] is False
        assert status["summary_generator_available"] is False

    @patch('src.k8s_mcp.core.k8s_graph.K8sKnowledgeGraph')
    @patch('src.k8s_mcp.core.summary_generator.SummaryGenerator')
    def test_intelligent_mode_initialization(self, mock_summary_gen, mock_kg):
        """测试智能模式初始化"""
        # 配置模拟对象
        mock_kg_instance = Mock()
        mock_kg_instance.graph.nodes = {}
        mock_kg_instance.graph.edges = {}
        mock_kg.return_value = mock_kg_instance
        
        mock_sg_instance = Mock()
        mock_summary_gen.return_value = mock_sg_instance
        
        server = K8sMCPServer(self.intelligent_config)
        
        # 手动初始化智能组件
        server._initialize_intelligent_components()
        
        # 验证智能组件初始化
        assert server.intelligent_mode_enabled is True
        assert server.knowledge_graph is not None
        assert server.summary_generator is not None
        
        # 验证模拟对象被正确调用
        mock_kg.assert_called_once()
        mock_summary_gen.assert_called_once()
        
        # 检查智能状态
        status = server.get_intelligent_status()
        assert status["intelligent_mode_enabled"] is True
        assert status["knowledge_graph_available"] is True
        assert status["summary_generator_available"] is True

    def test_intelligent_component_failure_graceful_degradation(self):
        """测试智能组件初始化失败时的优雅降级"""
        with patch('src.k8s_mcp.core.k8s_graph.K8sKnowledgeGraph', side_effect=Exception("模拟初始化失败")):
            server = K8sMCPServer(self.intelligent_config)
            server._initialize_intelligent_components()
            
            # 应该降级到基础模式
            assert server.intelligent_mode_enabled is False
            assert server.knowledge_graph is None
            assert server.cluster_sync_engine is None
            assert server.summary_generator is None

    @pytest.mark.asyncio
    async def test_health_check_with_intelligent_status(self):
        """测试包含智能状态的健康检查"""
        server = K8sMCPServer(self.basic_config)
        
        health = await server.health_check()
        
        assert "server_status" in health
        assert "intelligent_mode" in health
        assert health["intelligent_mode"]["intelligent_mode_enabled"] is False

    @pytest.mark.asyncio
    @patch('src.k8s_mcp.server.K8sClient')
    @patch('src.k8s_mcp.server.register_all_tools')
    async def test_server_initialization_flow(self, mock_register_tools, mock_k8s_client):
        """测试服务器完整初始化流程"""
        # 配置模拟对象
        mock_client_instance = AsyncMock()
        mock_k8s_client.return_value = mock_client_instance
        mock_register_tools.return_value = 25  # 模拟注册25个工具
        
        server = K8sMCPServer(self.basic_config)
        
        # 执行初始化
        await server.initialize()
        
        # 验证初始化流程
        assert server.is_running is True
        mock_client_instance.connect.assert_called_once()
        mock_register_tools.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.k8s_mcp.server.K8sClient')
    @patch('src.k8s_mcp.server.register_all_tools')
    @patch('src.k8s_mcp.core.k8s_graph.K8sKnowledgeGraph')
    @patch('src.k8s_mcp.core.summary_generator.SummaryGenerator')
    @patch('src.k8s_mcp.core.cluster_sync.ClusterSyncEngine')
    async def test_intelligent_server_initialization_flow(self, mock_sync_engine, mock_summary_gen, 
                                                         mock_kg, mock_register_tools, mock_k8s_client):
        """测试智能模式服务器完整初始化流程"""
        # 配置模拟对象
        mock_client_instance = AsyncMock()
        mock_k8s_client.return_value = mock_client_instance
        mock_register_tools.return_value = 27  # 模拟注册27个工具（包括智能工具）
        
        mock_kg_instance = Mock()
        mock_kg_instance.graph.nodes = {}
        mock_kg_instance.graph.edges = {}
        mock_kg.return_value = mock_kg_instance
        
        mock_sg_instance = Mock()
        mock_summary_gen.return_value = mock_sg_instance
        
        mock_sync_instance = AsyncMock()
        mock_sync_engine.return_value = mock_sync_instance
        
        server = K8sMCPServer(self.intelligent_config)
        
        # 执行初始化
        await server.initialize()
        
        # 验证智能模式初始化
        assert server.intelligent_mode_enabled is True
        assert server.knowledge_graph is not None
        assert server.summary_generator is not None
        assert server.cluster_sync_engine is not None
        
        # 验证启动流程
        mock_sync_instance.start.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.k8s_mcp.server.K8sClient')
    async def test_server_stop_with_intelligent_services(self, mock_k8s_client):
        """测试服务器停止时智能服务的清理"""
        mock_client_instance = AsyncMock()
        mock_k8s_client.return_value = mock_client_instance
        
        with patch('src.k8s_mcp.core.cluster_sync.ClusterSyncEngine') as mock_sync_engine:
            mock_sync_instance = AsyncMock()
            mock_sync_engine.return_value = mock_sync_instance
            
            server = K8sMCPServer(self.intelligent_config)
            server.cluster_sync_engine = mock_sync_instance
            server.intelligent_mode_enabled = True
            
            # 执行停止
            await server.stop()
            
            # 验证智能服务被正确停止
            mock_sync_instance.stop.assert_called_once()
            
            # 验证组件被清理
            assert server.knowledge_graph is None
            assert server.cluster_sync_engine is None
            assert server.summary_generator is None
            assert server.intelligent_mode_enabled is False

    def test_intelligent_api_endpoints(self):
        """测试智能功能API端点"""
        with patch('src.k8s_mcp.core.k8s_graph.K8sKnowledgeGraph') as mock_kg, \
             patch('src.k8s_mcp.core.summary_generator.SummaryGenerator') as mock_sg:
            
            # 配置模拟对象
            mock_kg_instance = Mock()
            mock_kg_instance.graph.nodes = {"test-pod": {}}
            mock_kg_instance.graph.edges = [("test-pod", "test-service")]
            mock_kg.return_value = mock_kg_instance
            
            mock_sg_instance = Mock()
            mock_sg.return_value = mock_sg_instance
            
            server = K8sMCPServer(self.intelligent_config)
            server._initialize_intelligent_components()
            
            client = TestClient(server.app)
            
            # 测试智能状态端点
            response = client.get("/intelligent/status")
            assert response.status_code == 200
            data = response.json()
            assert data["intelligent_mode_enabled"] is True
            assert data["knowledge_graph_available"] is True
            assert data["graph_nodes_count"] == 1
            assert data["graph_edges_count"] == 1
            
            # 测试智能健康检查端点
            response = client.get("/intelligent/health")
            assert response.status_code == 200
            data = response.json()
            assert data["intelligent_mode"] is True
            assert "components" in data
            assert "knowledge_graph" in data["components"]
            assert "cluster_sync" in data["components"]
            assert "summary_generator" in data["components"]

    def test_api_endpoints_basic_mode(self):
        """测试基础模式下的API端点"""
        server = K8sMCPServer(self.basic_config)
        client = TestClient(server.app)
        
        # 测试根端点
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "K8s MCP Server"
        assert data["version"] == "1.0.0"
        
        # 测试健康检查端点
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["clients"] == 0
        
        # 测试智能状态端点（基础模式）
        response = client.get("/intelligent/status")
        assert response.status_code == 200
        data = response.json()
        assert data["intelligent_mode_enabled"] is False
        assert data["knowledge_graph_available"] is False

    def test_get_server_info(self):
        """测试获取服务器信息"""
        server = K8sMCPServer(self.basic_config)
        
        info = server.get_server_info()
        
        assert info["name"] == "k8s-mcp"
        assert info["version"] == "1.0.0"
        assert info["description"] == "Kubernetes MCP服务器"
        assert "config" in info

    @pytest.mark.asyncio
    async def test_intelligent_services_lifecycle(self):
        """测试智能服务生命周期管理"""
        with patch('src.k8s_mcp.core.cluster_sync.ClusterSyncEngine') as mock_sync_engine:
            mock_sync_instance = AsyncMock()
            mock_sync_engine.return_value = mock_sync_instance
            
            server = K8sMCPServer(self.intelligent_config)
            server.cluster_sync_engine = mock_sync_instance
            server.intelligent_mode_enabled = True
            
            # 测试启动智能服务
            await server._start_intelligent_services()
            mock_sync_instance.start.assert_called_once()
            
            # 测试停止智能服务
            await server._stop_intelligent_services()
            mock_sync_instance.stop.assert_called_once()

    def test_configuration_impact_on_initialization(self):
        """测试配置对初始化的影响"""
        # 测试禁用智能功能的配置
        config_disabled = K8sConfig()
        config_disabled.enable_knowledge_graph = False
        
        server_disabled = K8sMCPServer(config_disabled)
        server_disabled._initialize_intelligent_components()
        
        assert server_disabled.intelligent_mode_enabled is False
        
        # 测试启用智能功能的配置
        config_enabled = K8sConfig()
        config_enabled.enable_knowledge_graph = True
        
        with patch('src.k8s_mcp.core.k8s_graph.K8sKnowledgeGraph'), \
             patch('src.k8s_mcp.core.summary_generator.SummaryGenerator'):
            
            server_enabled = K8sMCPServer(config_enabled)
            server_enabled._initialize_intelligent_components()
            
            assert server_enabled.intelligent_mode_enabled is True


class TestK8sMCPServerErrorHandling:
    """测试K8sMCPServer错误处理"""

    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self):
        """测试初始化失败处理"""
        config = K8sConfig()
        server = K8sMCPServer(config)
        
        with patch.object(server, 'k8s_client', None), \
             patch('src.k8s_mcp.server.K8sClient', side_effect=Exception("连接失败")):
            
            with pytest.raises(Exception):
                await server.initialize()

    @pytest.mark.asyncio
    async def test_intelligent_service_start_failure(self):
        """测试智能服务启动失败处理"""
        config = K8sConfig()
        config.enable_knowledge_graph = True
        
        server = K8sMCPServer(config)
        
        with patch('src.k8s_mcp.core.cluster_sync.ClusterSyncEngine') as mock_sync_engine:
            mock_sync_instance = AsyncMock()
            mock_sync_instance.start.side_effect = Exception("启动失败")
            mock_sync_engine.return_value = mock_sync_instance
            
            server.cluster_sync_engine = mock_sync_instance
            server.intelligent_mode_enabled = True
            
            # 应该优雅处理启动失败
            await server._start_intelligent_services()
            
            # 服务应该降级到基础模式
            assert server.intelligent_mode_enabled is False

    def test_api_endpoint_error_handling(self):
        """测试API端点错误处理"""
        server = K8sMCPServer(K8sConfig())
        client = TestClient(server.app)
        
        # 模拟智能状态获取失败
        with patch.object(server, 'get_intelligent_status', side_effect=Exception("状态获取失败")):
            response = client.get("/intelligent/status")
            assert response.status_code == 500