"""
K8s MCP服务器 - 基于SSE协议

实现基于SSE (Server-Sent Events) 协议的K8s MCP服务器
为钉钉K8s运维机器人提供真实的K8s集群操作支持
"""

import asyncio
import json
import time
import uuid
import sys
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from .core.tool_registry import tool_registry
from .tools import register_all_tools
from .config import get_config, K8sConfig
from .k8s_client import K8sClient
from .core.monitoring_middleware import MonitoringMiddleware, performance_monitor, monitor_intelligent_components
from .core.metrics_collector import metrics_collector


class ToolCallRequest(BaseModel):
    """工具调用请求"""
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    status: str
    message: str


class SSEEvent(BaseModel):
    """SSE事件"""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


class K8sMCPServer:
    """基于SSE的K8s MCP服务器
    
    基于MCP协议标准实现K8s功能服务器，提供：
    - K8s Pod管理
    - K8s Service管理
    - K8s Deployment管理
    - K8s集群监控
    - 企业级安全控制
    """
    
    def __init__(self, config: Optional[K8sConfig] = None):
        """初始化MCP服务器"""
        self.config = config or get_config()
        self.app = FastAPI(title="K8s MCP Server", version="1.0.0")
        self.k8s_client = None
        self.clients: Set[str] = set()
        self.event_queues: Dict[str, asyncio.Queue] = {}
        self.is_running = False
        
        # 智能组件（条件初始化）
        self.knowledge_graph = None
        self.cluster_sync_engine = None
        self.summary_generator = None
        self.intelligent_mode_enabled = False
        
        # 监控组件
        self.monitoring_enabled = self.config.monitoring_enabled
        self.intelligent_metrics_collector = None
        
        # 设置日志
        self._setup_logging()
        
        # 设置路由
        self._setup_routes()
        
        # 初始化监控
        self._setup_monitoring()
        
        logger.info("K8s MCP服务器初始化完成")
    
    def _setup_monitoring(self):
        """设置监控功能"""
        if not self.monitoring_enabled:
            logger.info("监控功能已禁用")
            return
        
        try:
            # 配置指标收集器
            metrics_collector.max_history_size = self.config.metrics_history_size
            metrics_collector.collection_interval = self.config.metrics_collection_interval
            
            # 配置性能监控器的阈值
            alert_thresholds = {
                "api.response_time.max": self.config.alert_api_response_time_max,
                "system.cpu_percent.max": self.config.alert_cpu_percent_max,
                "system.memory_percent.max": self.config.alert_memory_percent_max,
                "error_rate.max": self.config.alert_error_rate_max,
                "sync.last_sync_ago.max": self.config.alert_sync_delay_max
            }
            performance_monitor.alert_thresholds = alert_thresholds
            
            # 添加监控中间件
            self.app.add_middleware(MonitoringMiddleware)
            
            logger.info("监控功能初始化完成")
            
        except Exception as e:
            logger.warning(f"监控功能初始化失败: {e}")
            self.monitoring_enabled = False
    
    def _initialize_intelligent_components(self):
        """初始化智能组件（条件启用）"""
        try:
            if not self.config.enable_knowledge_graph:
                logger.info("知识图谱功能未启用，跳过智能组件初始化")
                return
            
            logger.info("开始初始化智能组件...")
            
            # 导入智能组件
            from .core.k8s_graph import K8sKnowledgeGraph, get_shared_knowledge_graph
            from .core.cluster_sync import ClusterSyncEngine
            from .core.summary_generator import SummaryGenerator
            
            # 使用共享的知识图谱实例
            self.knowledge_graph = get_shared_knowledge_graph(self.config)
            logger.info("使用共享知识图谱实例")
            
            # 初始化摘要生成器
            self.summary_generator = SummaryGenerator(self.knowledge_graph, self.config)
            logger.info("摘要生成器初始化完成")
            
            # 初始化集群同步引擎（需要在K8s客户端连接后启动）
            if self.k8s_client:
                self.cluster_sync_engine = ClusterSyncEngine(
                    self.knowledge_graph, 
                    self.k8s_client, 
                    self.config
                )
                logger.info("集群同步引擎初始化完成")
            
            self.intelligent_mode_enabled = True
            logger.info("✅ 智能组件初始化完成，智能模式已启用")
            
        except Exception as e:
            logger.warning(f"智能组件初始化失败，将继续使用基础模式: {e}")
            self.intelligent_mode_enabled = False
            # 清理部分初始化的组件
            self.knowledge_graph = None
            self.cluster_sync_engine = None
            self.summary_generator = None
    
    async def _start_intelligent_services(self):
        """启动智能服务（异步）"""
        try:
            if not self.intelligent_mode_enabled or not self.cluster_sync_engine:
                return
            
            logger.info("启动集群同步引擎...")
            await self.cluster_sync_engine.start()
            logger.info("✅ 集群同步引擎已启动")
            
        except Exception as e:
            logger.error(f"智能服务启动失败: {e}")
            # 降级到基础模式
            self.intelligent_mode_enabled = False
    
    async def _stop_intelligent_services(self):
        """停止智能服务"""
        try:
            if self.cluster_sync_engine:
                logger.info("正在停止集群同步引擎...")
                await self.cluster_sync_engine.stop()
                logger.info("集群同步引擎已停止")
                
        except Exception as e:
            logger.error(f"停止智能服务失败: {e}")
    
    async def _start_monitoring_services(self):
        """启动监控服务"""
        try:
            if not self.monitoring_enabled:
                return
            
            # 启动指标收集器
            metrics_collector.start()
            logger.info("✅ 指标收集器已启动")
            
            # 设置智能组件监控
            if self.intelligent_mode_enabled:
                self.intelligent_metrics_collector = monitor_intelligent_components(
                    self.knowledge_graph,
                    self.cluster_sync_engine,
                    self.summary_generator
                )
                
                # 启动智能组件指标收集
                import threading
                def periodic_intelligent_metrics():
                    import time
                    while self.is_running and self.monitoring_enabled:
                        try:
                            self.intelligent_metrics_collector()
                            time.sleep(self.config.health_check_interval)
                        except Exception as e:
                            logger.error(f"智能组件指标收集失败: {e}")
                            time.sleep(self.config.health_check_interval)
                
                threading.Thread(target=periodic_intelligent_metrics, daemon=True).start()
                logger.info("✅ 智能组件监控已启动")
            
        except Exception as e:
            logger.error(f"监控服务启动失败: {e}")
    
    async def _stop_monitoring_services(self):
        """停止监控服务"""
        try:
            if metrics_collector.is_running:
                metrics_collector.stop()
                logger.info("指标收集器已停止")
                
        except Exception as e:
            logger.error(f"停止监控服务失败: {e}")
    
    def get_intelligent_status(self) -> Dict[str, Any]:
        """获取智能功能状态"""
        return {
            "intelligent_mode_enabled": self.intelligent_mode_enabled,
            "knowledge_graph_available": self.knowledge_graph is not None,
            "cluster_sync_running": self.cluster_sync_engine is not None and getattr(self.cluster_sync_engine, 'running', False),
            "summary_generator_available": self.summary_generator is not None,
            "graph_nodes_count": len(self.knowledge_graph.graph.nodes) if self.knowledge_graph else 0,
            "graph_edges_count": len(self.knowledge_graph.graph.edges) if self.knowledge_graph else 0,
            "sync_status": self.cluster_sync_engine.get_sync_status() if self.cluster_sync_engine else None
        }
    
    def _get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        if not self.monitoring_enabled:
            return {"enabled": False}
        
        try:
            return {
                "enabled": True,
                "metrics_collector": metrics_collector.get_health_status(),
                "performance_monitor": {
                    "alert_count": len(performance_monitor.alert_history),
                    "recent_alerts": len(performance_monitor.get_alert_history(1)),  # 最近1小时
                    "thresholds": performance_monitor.alert_thresholds
                }
            }
        except Exception as e:
            logger.error(f"获取监控状态失败: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _setup_logging(self):
        """设置日志配置"""
        logger.remove()  # 移除默认handler
        
        # 控制台日志
        logger.add(
            sys.stdout,
            level="DEBUG" if self.config.debug else "INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            colorize=True
        )
        
        # 文件日志
        logger.add(
            "logs/k8s-mcp.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8"
        )
    
    def _serialize_result(self, result: Any) -> Any:
        """序列化结果为JSON兼容格式"""
        try:
            if result is None:
                return None
            elif isinstance(result, (str, int, float, bool)):
                return result
            elif isinstance(result, (list, tuple)):
                return [self._serialize_result(item) for item in result]
            elif isinstance(result, dict):
                return {key: self._serialize_result(value) for key, value in result.items()}
            elif hasattr(result, 'model_dump'):
                # Pydantic模型
                return result.model_dump()
            elif hasattr(result, 'dict'):
                # 旧版Pydantic模型
                return result.dict()
            elif hasattr(result, '__dict__'):
                # 普通对象
                return {
                    key: self._serialize_result(value) 
                    for key, value in result.__dict__.items()
                    if not key.startswith('_') and not callable(value)
                }
            else:
                # 其他类型转为字符串
                return str(result)
        except Exception as e:
            logger.warning(f"序列化结果失败: {e}, 使用字符串表示")
            return str(result)
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.get("/")
        async def root():
            """根路径"""
            return {
                "name": "K8s MCP Server",
                "version": "1.0.0",
                "protocol": "SSE",
                "status": "running" if self.is_running else "stopped"
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "clients": len(self.clients),
                "k8s_connected": self.k8s_client is not None
            }
        
        @self.app.get("/intelligent/status")
        async def intelligent_status():
            """获取智能功能状态"""
            try:
                return self.get_intelligent_status()
            except Exception as e:
                logger.error(f"获取智能状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/intelligent/health")
        async def intelligent_health():
            """智能功能详细健康检查"""
            try:
                status = self.get_intelligent_status()
                health = {
                    "intelligent_mode": status["intelligent_mode_enabled"],
                    "components": {
                        "knowledge_graph": {
                            "available": status["knowledge_graph_available"],
                            "nodes": status["graph_nodes_count"],
                            "edges": status["graph_edges_count"]
                        },
                        "cluster_sync": {
                            "running": status["cluster_sync_running"],
                            "status": status["sync_status"]
                        },
                        "summary_generator": {
                            "available": status["summary_generator_available"]
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                return health
            except Exception as e:
                logger.error(f"智能健康检查失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics():
            """获取性能指标"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                return metrics_collector.get_current_metrics()
            except HTTPException:
                # 重新抛出HTTP异常
                raise
            except Exception as e:
                logger.error(f"获取指标失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics/history")
        async def get_metrics_history(metric_name: str = None, last_minutes: int = 60):
            """获取指标历史"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                return {
                    "history": metrics_collector.get_metrics_history(metric_name, last_minutes),
                    "total_count": len(metrics_collector.metrics_history)
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取指标历史失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics/summary")
        async def get_metrics_summary():
            """获取指标汇总"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                return metrics_collector.get_summary_stats()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取指标汇总失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/performance")
        async def get_performance_report():
            """获取性能报告"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                return performance_monitor.get_performance_summary()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取性能报告失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts")
        async def get_alerts(last_hours: int = 24):
            """获取报警历史"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                return {
                    "alerts": performance_monitor.get_alert_history(last_hours),
                    "total_count": len(performance_monitor.alert_history)
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取报警历史失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics/prometheus")
        async def get_prometheus_metrics():
            """获取Prometheus格式的指标"""
            try:
                if not self.monitoring_enabled:
                    raise HTTPException(status_code=503, detail="监控功能未启用")
                
                from fastapi.responses import PlainTextResponse
                prometheus_data = metrics_collector.export_prometheus_format()
                return PlainTextResponse(prometheus_data, media_type="text/plain")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"导出Prometheus指标失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/events")
        async def sse_events(request: Request):
            """SSE事件流端点"""
            return StreamingResponse(
                self._event_stream(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
        
        @self.app.get("/tools")
        async def list_tools():
            """获取工具列表"""
            try:
                tools = tool_registry.list_tools("kubernetes", enabled_only=True)
                return {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "category": getattr(tool, 'category', 'kubernetes'),
                            "input_schema": tool.get_schema().input_schema
                        }
                        for tool in tools
                    ]
                }
            except Exception as e:
                logger.error(f"获取工具列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            """调用工具"""
            start_time = time.time()
            try:
                logger.info(f"📥 收到工具调用请求: {request.name}")
                logger.debug(f"🔧 工具参数: {request.arguments}")
                
                # 广播工具开始执行事件
                await self._broadcast_event("tool_start", {
                    "id": request.id,
                    "tool": request.name,
                    "arguments": request.arguments,
                    "timestamp": start_time
                })
                
                # 执行工具
                logger.info(f"🚀 开始执行工具: {request.name}")
                result = await tool_registry.execute_tool(request.name, request.arguments)
                execution_time = time.time() - start_time
                
                # 记录执行结果详情
                if hasattr(result, 'is_error') and result.is_error:
                    logger.error(f"❌ 工具执行失败: {request.name}, 错误: {result.content}")
                    error_detail = str(result.content) if hasattr(result, 'content') else "未知错误"
                    
                    # 广播工具执行错误事件
                    await self._broadcast_event("tool_error", {
                        "id": request.id,
                        "tool": request.name,
                        "error": error_detail,
                        "success": False,
                        "execution_time": execution_time,
                        "timestamp": time.time()
                    })
                    
                    raise HTTPException(status_code=500, detail=error_detail)
                
                # 序列化结果
                result_data = self._serialize_result(result)
                
                # 记录成功执行的详细日志
                result_size = len(str(result_data)) if result_data else 0
                result_type = type(result).__name__ if result else "None"
                
                logger.info(f"✅ 工具执行成功: {request.name}")
                logger.info(f"📊 执行统计: 耗时={execution_time:.3f}s, 结果大小={result_size}字节, 类型={result_type}")
                
                # 记录结果摘要（如果结果是字典且有特定字段）
                if isinstance(result_data, dict):
                    if 'total' in result_data:
                        logger.info(f"📋 结果摘要: 总数={result_data.get('total', 0)}")
                    if 'items' in result_data and isinstance(result_data['items'], list):
                        logger.info(f"📋 结果摘要: 返回项目数={len(result_data['items'])}")
                    if 'namespace' in result_data:
                        logger.info(f"📋 结果摘要: 命名空间={result_data.get('namespace', 'unknown')}")
                
                # 广播工具执行完成事件
                await self._broadcast_event("tool_complete", {
                    "id": request.id,
                    "tool": request.name,
                    "result": result_data,
                    "success": True,
                    "execution_time": execution_time,
                    "result_size": result_size,
                    "timestamp": time.time()
                })
                
                return ToolCallResponse(status="success", message="工具执行完成")
                
            except HTTPException:
                # 重新抛出HTTP异常
                raise
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)
                logger.error(f"❌ 工具调用异常: {request.name}, 错误: {error_msg}, 耗时: {execution_time:.3f}s")
                logger.exception(f"🔍 工具调用异常堆栈: {request.name}")
                
                # 广播工具执行错误事件
                await self._broadcast_event("tool_error", {
                    "id": request.id,
                    "tool": request.name,
                    "error": error_msg,
                    "success": False,
                    "execution_time": execution_time,
                    "timestamp": time.time()
                })
                
                raise HTTPException(status_code=500, detail=error_msg)
    
    async def _event_stream(self, request: Request):
        """SSE事件流生成器"""
        client_id = str(uuid.uuid4())
        self.clients.add(client_id)
        self.event_queues[client_id] = asyncio.Queue()
        
        logger.info(f"新的SSE客户端连接: {client_id}")
        
        try:
            # 发送连接确认事件
            yield self._format_sse_event("connected", {
                "client_id": client_id,
                "timestamp": time.time(),
                "server": "K8s MCP Server"
            })
            
            # 发送工具列表事件
            tools = tool_registry.list_tools("kubernetes", enabled_only=True)
            yield self._format_sse_event("tools_list", {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "category": getattr(tool, 'category', 'kubernetes')
                    }
                    for tool in tools
                ]
            })
            
            # 事件循环
            while True:
                try:
                    # 等待事件或超时
                    event = await asyncio.wait_for(
                        self.event_queues[client_id].get(),
                        timeout=30.0
                    )
                    
                    try:
                        yield self._format_sse_event(event["event"], event["data"])
                    except Exception as format_error:
                        logger.error(f"格式化SSE事件失败: {format_error}")
                        yield self._format_sse_event(event["event"], {
                            "error": str(format_error),
                            "original_data": str(event["data"])
                        })
                    
                except asyncio.TimeoutError:
                    # 发送心跳事件
                    yield self._format_sse_event("heartbeat", {
                        "timestamp": time.time()
                    })
                    
        except asyncio.CancelledError:
            logger.info(f"SSE客户端连接取消: {client_id}")
        except Exception as e:
            logger.error(f"SSE事件流错误: {e}")
        finally:
            # 清理客户端
            self.clients.discard(client_id)
            self.event_queues.pop(client_id, None)
            logger.info(f"SSE客户端断开连接: {client_id}")
    
    def _format_sse_event(self, event: str, data: Dict[str, Any]) -> str:
        """格式化SSE事件"""
        try:
            # 尝试直接序列化，如果失败则使用自定义序列化器
            json_data = json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError):
            # 使用自定义序列化器处理复杂对象
            serialized_data = self._serialize_result(data)
            json_data = json.dumps(serialized_data, ensure_ascii=False)
        
        return f"event: {event}\ndata: {json_data}\n\n"
    
    async def _broadcast_event(self, event: str, data: Dict[str, Any]):
        """广播事件到所有客户端"""
        logger.debug(f"🔊 准备广播事件: {event}, 当前客户端数: {len(self.clients)}")
        
        if not self.clients:
            logger.warning(f"⚠️ 无客户端连接，跳过事件广播: {event}")
            return
        
        # 预先序列化数据以避免JSON序列化问题
        serialized_data = self._serialize_result(data)
        
        event_data = {
            "event": event,
            "data": serialized_data
        }
        
        # 将事件添加到所有客户端队列
        sent_count = 0
        for client_id in list(self.clients):
            try:
                if client_id in self.event_queues:
                    await self.event_queues[client_id].put(event_data)
                    sent_count += 1
                else:
                    logger.warning(f"⚠️ 客户端 {client_id} 队列不存在")
            except Exception as e:
                logger.error(f"❌ 向客户端 {client_id} 发送事件失败: {e}")
        
        logger.info(f"📡 事件广播完成: {event}, 发送给 {sent_count}/{len(self.clients)} 个客户端")
    
    async def initialize(self):
        """初始化服务器组件"""
        try:
            # 初始化K8s客户端
            self.k8s_client = K8sClient(self.config)
            await self.k8s_client.connect()
            logger.info("K8s客户端连接成功")
            
            # 初始化智能组件（条件启用）
            self._initialize_intelligent_components()
            
            # 完成集群同步引擎初始化（需要在K8s客户端连接后）
            if self.config.enable_knowledge_graph and self.intelligent_mode_enabled and not self.cluster_sync_engine:
                try:
                    from .core.cluster_sync import ClusterSyncEngine
                    self.cluster_sync_engine = ClusterSyncEngine(
                        self.knowledge_graph, 
                        self.k8s_client, 
                        self.config
                    )
                    logger.info("集群同步引擎延迟初始化完成")
                except Exception as e:
                    logger.warning(f"集群同步引擎初始化失败: {e}")
            
            # 注册所有工具
            tool_count = register_all_tools()
            logger.info(f"成功注册 {tool_count} 个K8s工具")
            
            # 启动智能服务
            await self._start_intelligent_services()
            
            # 启动监控服务
            await self._start_monitoring_services()
            
            self.is_running = True
            
            # 输出启动状态
            if self.intelligent_mode_enabled:
                status = self.get_intelligent_status()
                logger.info("🧠 智能模式已启用")
                logger.info(f"   - 知识图谱: {'✅' if status['knowledge_graph_available'] else '❌'}")
                logger.info(f"   - 集群同步: {'✅' if status['cluster_sync_running'] else '❌'}")
                logger.info(f"   - 摘要生成: {'✅' if status['summary_generator_available'] else '❌'}")
            else:
                logger.info("🔧 基础模式运行（智能功能未启用）")
            
            logger.info("K8s MCP服务器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def start(self):
        """启动服务器"""
        try:
            # 初始化服务器
            await self.initialize()
            
            # 启动HTTP服务器
            import uvicorn
            config = uvicorn.Config(
                self.app,
                host=self.config.host,
                port=self.config.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            logger.info(f"K8s MCP服务器已启动: http://{self.config.host}:{self.config.port}")
            logger.info("SSE端点: /events")
            logger.info("工具调用端点: /tools/call")
            logger.info("等待客户端连接...")
            
            await server.serve()
            
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
            raise
    
    async def stop(self):
        """停止服务器"""
        try:
            self.is_running = False
            
            # 停止智能服务
            await self._stop_intelligent_services()
            
            # 停止监控服务
            await self._stop_monitoring_services()
            
            # 断开K8s客户端
            if self.k8s_client:
                await self.k8s_client.disconnect()
            
            # 清理智能组件
            self.knowledge_graph = None
            self.cluster_sync_engine = None
            self.summary_generator = None
            self.intelligent_mode_enabled = False
            
            # 清理所有客户端连接
            self.clients.clear()
            self.event_queues.clear()
            
            logger.info("K8s MCP服务器已停止")
            
        except Exception as e:
            logger.error(f"停止服务器失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_info = {
                "server_status": "running" if self.is_running else "stopped",
                "tools_count": len(tool_registry.list_tools("kubernetes", enabled_only=True)),
                "clients_count": len(self.clients),
                "k8s_client": await self.k8s_client.health_check() if self.k8s_client else {"healthy": False},
                "intelligent_mode": self.get_intelligent_status(),
                "monitoring": self._get_monitoring_status()
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "server_status": "error",
                "error": str(e)
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "name": "k8s-mcp",
            "version": "1.0.0",
            "description": "Kubernetes MCP服务器",
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "debug": self.config.debug
            },
            "running": self.is_running
        }


# 为了保持向后兼容性，创建别名
K8sSSEMCPServer = K8sMCPServer


async def main():
    """主函数"""
    try:
        # 创建服务器实例
        server = K8sMCPServer()
        
        # 启动服务器
        await server.start()
        
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止服务器...")
        if 'server' in locals():
            await server.stop()
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 