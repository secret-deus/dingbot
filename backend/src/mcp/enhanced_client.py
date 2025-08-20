"""
增强的MCP客户端
支持多服务器连接、JSON配置和工具路由
"""

import asyncio
import json
import websockets
import aiohttp
import subprocess
import sys
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from datetime import datetime
from loguru import logger

from .types import (
    MCPClientConfig, MCPTool, MCPToolCall, MCPToolResult,
    MCPConnectionStatus, MCPStats, MCPException
)
from .config import (
    MCPServerConfig, MCPToolConfig, 
    get_config_manager
)
from .config_manager import MCPConfigManager


class MCPServerConnection:
    """MCP服务器连接"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = MCPConnectionStatus.DISCONNECTED
        self.websocket = None
        self.session = None
        self.process = None
        self.sse_task = None
        self.stream_task = None
        self.tools: Dict[str, MCPTool] = {}
        self.last_ping = None
        self.message_queue = asyncio.Queue()
        
        # 添加配置管理器引用，用于自动同步
        self.config_manager = None
    
    def set_config_manager(self, config_manager):
        """设置配置管理器，用于自动同步"""
        self.config_manager = config_manager
    
    async def connect(self) -> bool:
        """连接到服务器"""
        try:
            self.status = MCPConnectionStatus.CONNECTING
            logger.info(f"正在连接MCP服务器: {self.config.name} ({self.config.type})")
            
            if self.config.type == "websocket":
                await self._connect_websocket()
            elif self.config.type == "http":
                await self._connect_http()
            elif self.config.type == "sse":
                await self._connect_sse()
            elif self.config.type == "stream_http":
                await self._connect_stream_http()
            elif self.config.type == "subprocess":
                await self._connect_subprocess()
            elif self.config.type == "local":
                await self._connect_local()
            
            # 发现工具
            logger.info(f"开始发现MCP工具: {self.config.name}")
            await self._discover_tools()
            
            # 验证连接状态
            if self.config.type == "sse" and self.sse_task and self.sse_task.done():
                # SSE任务已结束，说明连接失败
                exception = self.sse_task.exception()
                if exception:
                    raise exception
                else:
                    raise MCPException("SSE_CONNECTION_FAILED", "SSE连接意外终止")
            
            self.status = MCPConnectionStatus.CONNECTED
            logger.info(f"✅ MCP服务器连接成功: {self.config.name} (发现 {len(self.tools)} 个工具)")
            return True
            
        except Exception as e:
            self.status = MCPConnectionStatus.ERROR
            logger.error(f"❌ MCP服务器连接失败 {self.config.name}: {type(e).__name__}: {e}")
            # 清理资源
            await self._cleanup_connection()
            return False
    
    async def _cleanup_connection(self):
        """清理连接资源"""
        try:
            if self.sse_task and not self.sse_task.done():
                self.sse_task.cancel()
                try:
                    await self.sse_task
                except asyncio.CancelledError:
                    pass
            
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
                
        except Exception as e:
            logger.warning(f"清理连接资源时出错: {e}")
    
    async def _connect_websocket(self):
        """连接WebSocket服务器"""
        uri = f"ws://{self.config.host}:{self.config.port}{self.config.path}"
        logger.info(f"正在连接WebSocket: {uri}")
        
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        # 设置超时
        import asyncio
        try:
            # 使用websockets.connect的现代API
            connect_kwargs = {}
            if headers:
                logger.debug(f"使用认证头连接WebSocket: {list(headers.keys())}")
                connect_kwargs["additional_headers"] = headers
            
            # 创建连接
            self.websocket = await asyncio.wait_for(
                websockets.connect(uri, **connect_kwargs),
                timeout=self.config.timeout
            )
            logger.info(f"WebSocket连接建立成功: {uri}")
            
        except (TypeError, AttributeError) as e:
            # 如果additional_headers不支持，尝试extra_headers
            logger.debug(f"尝试使用extra_headers: {e}")
            try:
                connect_kwargs = {}
                if headers:
                    connect_kwargs["extra_headers"] = headers
                
                self.websocket = await asyncio.wait_for(
                    websockets.connect(uri, **connect_kwargs),
                    timeout=self.config.timeout
                )
                logger.info(f"WebSocket连接建立成功(extra_headers): {uri}")
            except (TypeError, AttributeError):
                # 最后尝试基础连接
                logger.warning(f"WebSocket库不支持headers参数，使用基础连接")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(uri),
                    timeout=self.config.timeout
                )
                logger.info(f"WebSocket连接建立成功(基础连接): {uri}")
                
        except asyncio.TimeoutError:
            raise MCPException("WEBSOCKET_TIMEOUT", f"WebSocket连接超时: {uri}")
        except Exception as e:
            raise MCPException("WEBSOCKET_CONNECTION_FAILED", f"WebSocket连接失败: {uri}, 错误: {e}")
        
        # 发送初始化消息
        init_message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "client_info": {
                    "name": "dingtalk-k8s-bot",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        logger.info(f"发送MCP初始化请求: {init_message}")
        await self.websocket.send(json.dumps(init_message))
        response = await self.websocket.recv()
        logger.info(f"收到MCP初始化响应: {response}")
        
        # 验证初始化响应
        response_data = json.loads(response)
        if "error" in response_data:
            raise MCPException("INIT_FAILED", f"MCP初始化失败: {response_data['error']}")
        
        logger.info("MCP协议初始化成功")
    
    async def _connect_http(self):
        """连接HTTP服务器"""
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        
        # 测试连接
        async with self.session.get("/health") as response:
            if response.status != 200:
                raise MCPException("HTTP_CONNECTION_FAILED", f"HTTP连接失败: {response.status}")
    
    async def _connect_sse(self):
        """连接SSE服务器"""
        uri = f"http://{self.config.host}:{self.config.port}{self.config.path}"
        logger.info(f"正在连接SSE服务器: {uri}")
        
        # 创建HTTP会话
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        
        # 启动SSE事件监听任务
        self.sse_task = asyncio.create_task(self._sse_event_listener(uri))
        
        # 等待连接建立
        await asyncio.sleep(1)
        logger.info(f"SSE连接已建立: {uri}")
    
    async def _sse_event_listener(self, uri: str):
        """SSE事件监听器"""
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        retry_count = 0
        max_retries = self.config.retry_attempts or 3
        
        while retry_count < max_retries:
            try:
                logger.info(f"正在连接SSE事件流: {uri} (尝试 {retry_count + 1}/{max_retries})")
                async with self.session.get(uri, headers=headers) as response:
                    if response.status != 200:
                        error_msg = f"SSE连接失败: HTTP {response.status}"
                        if response.status == 404:
                            error_msg += " - 端点不存在，请检查服务器配置"
                        elif response.status == 401:
                            error_msg += " - 认证失败，请检查认证配置"
                        elif response.status == 503:
                            error_msg += " - 服务不可用，请检查服务器状态"
                        raise MCPException("SSE_CONNECTION_FAILED", error_msg)
                    
                    logger.info("SSE事件流连接成功，开始监听事件")
                    retry_count = 0  # 重置重试计数器
                    
                    current_event = None
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('event:'):
                            current_event = line[6:].strip()
                        elif line.startswith('data:'):
                            try:
                                data = json.loads(line[5:].strip())
                                await self._handle_sse_event(current_event, data)
                            except json.JSONDecodeError as e:
                                logger.warning(f"解析SSE事件数据失败: {e}, 数据: {line}")
                        elif line == '':
                            # 空行表示事件结束
                            current_event = None
                            
            except asyncio.CancelledError:
                logger.info("SSE事件监听器被取消")
                break
            except aiohttp.ClientConnectorError as e:
                retry_count += 1
                logger.error(f"SSE连接网络错误 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)  # 指数退避，最大30秒
                    logger.info(f"网络连接失败，等待 {wait_time} 秒后重连...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("SSE网络连接重试次数已达上限，放弃连接")
                    raise MCPException("SSE_NETWORK_ERROR", f"网络连接失败，已重试 {max_retries} 次")
            except aiohttp.ServerTimeoutError as e:
                retry_count += 1
                logger.error(f"SSE连接超时 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    logger.info(f"连接超时，等待 {wait_time} 秒后重连...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("SSE连接超时重试次数已达上限，放弃连接")
                    raise MCPException("SSE_TIMEOUT_ERROR", f"连接超时，已重试 {max_retries} 次")
            except Exception as e:
                retry_count += 1
                logger.error(f"SSE连接未知错误 (尝试 {retry_count}/{max_retries}): {type(e).__name__}: {e}")
                
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    logger.info(f"发生未知错误，等待 {wait_time} 秒后重连...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("SSE连接重试次数已达上限，放弃连接")
                    raise MCPException("SSE_CONNECTION_FAILED", f"SSE连接失败，已重试 {max_retries} 次: {e}")
    
    async def _handle_sse_event(self, event_type: str, data: Dict[str, Any]):
        """处理SSE事件"""
        logger.debug(f"收到SSE事件: {event_type}, 数据: {data}")
        
        if event_type == "connected":
            logger.info(f"SSE连接确认: {data.get('client_id')}")
        elif event_type == "tools_list":
            tools_data = data.get('tools', [])
            logger.info(f"收到工具列表: {len(tools_data)} 个工具")
            
            # 🔥 新增：自动同步工具配置
            await self._auto_sync_tools_config(tools_data)
            
        elif event_type == "tool_start":
            logger.info(f"工具开始执行: {data.get('tool')}")
        elif event_type == "tool_complete":
            logger.info(f"工具执行完成: {data.get('tool')}")
            # 将结果放入消息队列供工具调用等待
            await self.message_queue.put({
                "type": "tool_result",
                "id": data.get("id"),
                "result": data.get("result"),
                "success": data.get("success", True)
            })
        elif event_type == "tool_error":
            logger.error(f"工具执行错误: {data.get('tool')}, 错误: {data.get('error')}")
            # 将错误放入消息队列
            await self.message_queue.put({
                "type": "tool_error",
                "id": data.get("id"),
                "error": data.get("error"),
                "success": False
            })
        elif event_type == "heartbeat":
            logger.debug("收到心跳事件")
            self.last_ping = datetime.now()
        else:
            logger.debug(f"未知SSE事件类型: {event_type}")
    
    async def _auto_sync_tools_config(self, tools_data: List[Dict[str, Any]]):
        """自动同步工具配置到MCP配置文件"""
        if not self.config_manager:
            logger.debug("配置管理器未设置，跳过自动同步")
            return
        
        try:
            logger.info(f"🔄 开始自动同步工具配置: {self.config.name}")
            
            # 转换工具数据为配置格式
            tool_configs = []
            tool_names = []
            
            for tool_data in tools_data:
                tool_name = tool_data.get("name")
                if not tool_name:
                    continue
                
                tool_names.append(tool_name)
                
                # 构建工具配置
                tool_config = {
                    "name": tool_name,
                    "description": tool_data.get("description", ""),
                    "category": tool_data.get("category", "kubernetes"),
                    "enabled": True,
                    "server_name": self.config.name,  # 添加服务器名称
                    "input_schema": tool_data.get("input_schema", {}),
                    "default_parameters": None,
                    "timeout": 30,
                    "cache_enabled": True,
                    "cache_ttl": 60,
                    "required_permissions": None,
                    "allowed_users": None,
                    "allowed_roles": None
                }
                
                # 根据工具名称推断风险等级和配置
                if any(x in tool_name for x in ["create", "delete", "patch", "restart", "rollback"]):
                    # 高风险操作
                    tool_config.update({
                        "timeout": 60,
                        "cache_enabled": False,
                        "required_permissions": [f"k8s:{tool_name.split('-')[1]}:{tool_name.split('-')[2]}"]
                    })
                elif any(x in tool_name for x in ["update", "scale"]):
                    # 中等风险操作
                    tool_config.update({
                        "timeout": 60,
                        "cache_enabled": False,
                        "required_permissions": [f"k8s:{tool_name.split('-')[1]}:{tool_name.split('-')[2]}"]
                    })
                else:
                    # 安全操作（查询类）
                    tool_config.update({
                        "timeout": 30,
                        "cache_enabled": True,
                        "cache_ttl": 60
                    })
                
                tool_configs.append(tool_config)
            
            # 更新配置文件
            await self._update_mcp_config_file(tool_names, tool_configs)
            
            logger.info(f"✅ 工具配置自动同步完成: {len(tool_configs)} 个工具")
            
        except Exception as e:
            logger.error(f"❌ 自动同步工具配置失败: {e}")
    
    async def _update_mcp_config_file(self, tool_names: List[str], tool_configs: List[Dict[str, Any]]):
        """更新MCP配置文件"""
        try:
            # 从config_manager获取配置文件路径
            from pathlib import Path
            import os
            
            if hasattr(self.config_manager, 'config_file'):
                config_path = Path(self.config_manager.config_file)  # 确保转换为Path对象
            else:
                # 回退到默认路径，使用绝对路径查找
                
                # 尝试多个可能的路径
                possible_paths = [
                    "backend/config/mcp_config.json",
                    "config/mcp_config.json", 
                    "../backend/config/mcp_config.json",
                    os.path.join(os.getcwd(), "backend", "config", "mcp_config.json")
                ]
                
                config_path = None
                for path in possible_paths:
                    if Path(path).exists():
                        config_path = Path(path)
                        logger.info(f"🔍 找到配置文件: {config_path.absolute()}")
                        break
                
                if not config_path:
                    # 如果都没找到，使用当前工作目录的相对路径
                    config_path = Path("backend/config/mcp_config.json")
                    logger.warning(f"⚠️ 配置文件不存在，将尝试创建: {config_path.absolute()}")
                    
                    # 确保目录存在
                    config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有配置
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                # 创建基础配置
                logger.info(f"📝 创建新的MCP配置文件: {config_path}")
                config = {
                    "version": "1.0",
                    "name": "钉钉K8s运维机器人MCP配置",
                    "description": "支持K8s操作的MCP服务器配置",
                    "global_config": {
                        "timeout": 30000,
                        "retry_attempts": 3,
                        "retry_delay": 1000,
                        "max_concurrent_calls": 5,
                        "enable_cache": True,
                        "cache_timeout": 300000
                    },
                    "servers": [
                        {
                            "name": self.config.name,
                            "type": self.config.type,
                            "enabled": True,
                            "host": getattr(self.config, 'host', 'localhost'),
                            "port": getattr(self.config, 'port', 8766),
                            "path": getattr(self.config, 'path', '/events'),
                            "timeout": self.config.timeout,
                            "retry_attempts": self.config.retry_attempts,
                            "retry_delay": self.config.retry_delay,
                            "enabled_tools": [],
                            "disabled_tools": None
                        }
                    ],
                    "tools": [],
                    "tool_routing": {
                        "k8s-*": self.config.name
                    },
                    "security": {
                        "enable_audit": True,
                        "audit_log_path": "logs/mcp_audit.log",
                        "rate_limit": {
                            "enabled": True,
                            "requests_per_minute": 100
                        }
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                }
            
            # 使用统一的备份机制（通过 MCPConfigManager）
            # 不在这里直接创建备份，让 MCPConfigManager 处理备份
            logger.debug(f"📁 配置将由 MCPConfigManager 统一备份")
            
            # 更新服务器的enabled_tools
            for server in config.get("servers", []):
                if server.get("name") == self.config.name:
                    old_count = len(server.get("enabled_tools", []))
                    server["enabled_tools"] = tool_names
                    logger.info(f"🔧 更新服务器 {server['name']} 工具列表: {old_count} → {len(tool_names)}")
                    break
            
            # 替换所有K8s工具配置
            non_k8s_tools = [tool for tool in config.get("tools", []) if not tool["name"].startswith("k8s-")]
            config["tools"] = non_k8s_tools + tool_configs
            
            logger.info(f"🔧 更新工具配置: {len(tool_configs)} 个K8s工具")
            
            # 写回配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 配置文件已更新: {config_path}")
            
            # 通知配置变更（如果支持热重载）
            if hasattr(self.config_manager, 'reload_config_async'):
                await self.config_manager.reload_config_async()
                logger.info("🔄 配置已热重载")
            elif hasattr(self.config_manager, 'reload_config'):
                self.config_manager.reload_config()
                logger.info("🔄 配置已同步重载")
            
        except Exception as e:
            logger.error(f"❌ 更新配置文件失败: {e}")
            raise
    
    async def _sse_event_source(self, uri: str) -> AsyncGenerator[str, None]:
        """SSE事件源消费者（已弃用，使用_sse_event_listener替代）"""
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(uri, headers=headers, timeout=self.config.timeout) as response:
                if response.status != 200:
                    raise MCPException("SSE_CONNECTION_FAILED", f"SSE连接失败: {response.status}")
                
                async for line in response.content:
                    if line.strip():
                        yield line.decode('utf-8')
    
    async def _connect_stream_http(self):
        """连接Stream HTTP服务器"""
        uri = f"http://{self.config.host}:{self.config.port}{self.config.path}"
        self.stream_task = asyncio.create_task(self._stream_http_event_source(uri))
    
    async def _stream_http_event_source(self, uri: str) -> AsyncGenerator[str, None]:
        """Stream HTTP事件源消费者"""
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(uri, headers=headers, timeout=self.config.timeout) as response:
                if response.status != 200:
                    raise MCPException("STREAM_HTTP_CONNECTION_FAILED", f"Stream HTTP连接失败: {response.status}")
                
                async for line in response.content:
                    if line.strip():
                        yield line.decode('utf-8')
    
    async def _connect_subprocess(self):
        """启动子进程服务器"""
        cmd = [self.config.command]
        if self.config.args:
            cmd.extend(self.config.args)
        
        env = None
        if self.config.env:
            import os
            env = os.environ.copy()
            env.update(self.config.env)
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.config.cwd,
            env=env
        )
        
        # 等待进程启动
        await asyncio.sleep(1)
        
        if self.process.returncode is not None:
            raise MCPException("SUBPROCESS_FAILED", f"子进程启动失败: {self.process.returncode}")
    
    async def _connect_local(self):
        """连接本地服务器"""
        # 本地连接逻辑（可以是导入模块等）
        pass
    
    async def _discover_tools(self):
        """发现工具"""
        try:
            if self.config.type == "websocket":
                await self._discover_tools_websocket()
            elif self.config.type == "http":
                await self._discover_tools_http()
            elif self.config.type == "sse":
                await self._discover_tools_sse()
            elif self.config.type == "stream_http":
                await self._discover_tools_stream_http()
            elif self.config.type in ["subprocess", "local"]:
                await self._discover_tools_rpc()
            
            # 过滤工具
            self._filter_tools()
            
            logger.info(f"服务器 {self.config.name} 发现 {len(self.tools)} 个工具")
            
        except Exception as e:
            logger.error(f"发现工具失败 {self.config.name}: {e}")
    
    async def _discover_tools_websocket(self):
        """通过WebSocket发现工具"""
        message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        if "error" in response_data:
            raise MCPException("TOOL_DISCOVERY_FAILED", f"工具发现失败: {response_data['error']}")
        
        tools_data = response_data.get("result", {}).get("tools", [])
        for tool_data in tools_data:
            tool = MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                category=tool_data.get("category"),
                version=tool_data.get("version"),
                provider=self.config.name
            )
            self.tools[tool.name] = tool
    
    async def _discover_tools_http(self):
        """通过HTTP发现工具"""
        async with self.session.get("/tools") as response:
            if response.status != 200:
                raise MCPException("TOOL_DISCOVERY_FAILED", f"HTTP工具发现失败: {response.status}")
            
            tools_data = await response.json()
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    category=tool_data.get("category"),
                    version=tool_data.get("version"),
                    provider=self.config.name
                )
                self.tools[tool.name] = tool
    
    async def _discover_tools_sse(self):
        """通过SSE发现工具"""
        # SSE工具发现：通过HTTP API获取工具列表
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        async with self.session.get(f"http://{self.config.host}:{self.config.port}/tools", headers=headers) as response:
            if response.status != 200:
                raise MCPException("TOOL_DISCOVERY_FAILED", f"SSE工具发现失败: {response.status}")
            
            response_data = await response.json()
            tools_data = response_data.get("tools", [])
            
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("input_schema", {}),
                    category=tool_data.get("category"),
                    version=tool_data.get("version"),
                    provider=self.config.name
                )
                self.tools[tool.name] = tool
                
            logger.info(f"通过SSE发现 {len(self.tools)} 个工具")
    
    async def _discover_tools_stream_http(self):
        """通过Stream HTTP发现工具"""
        # Stream HTTP通常用于流式响应，工具发现可能需要通过HTTP API
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        
        headers = {}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        async with self.session.get(f"http://{self.config.host}:{self.config.port}/tools", headers=headers) as response:
            if response.status != 200:
                raise MCPException("TOOL_DISCOVERY_FAILED", f"Stream HTTP工具发现失败: {response.status}")
            
            tools_data = await response.json()
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    category=tool_data.get("category"),
                    version=tool_data.get("version"),
                    provider=self.config.name
                )
                self.tools[tool.name] = tool
    
    async def _discover_tools_rpc(self):
        """通过RPC发现工具"""
        # 子进程或本地RPC工具发现
        pass
    
    def _filter_tools(self):
        """过滤工具"""
        if self.config.enabled_tools:
            # 只保留启用的工具
            filtered_tools = {}
            for tool_name in self.config.enabled_tools:
                if tool_name in self.tools:
                    filtered_tools[tool_name] = self.tools[tool_name]
                else:
                    logger.warning(f"启用的工具 {tool_name} 未在发现的工具中找到")
            self.tools = filtered_tools
        
        if self.config.disabled_tools:
            # 移除禁用的工具
            for tool_name in self.config.disabled_tools:
                self.tools.pop(tool_name, None)
    
    async def call_tool(self, name: str, parameters: Dict[str, Any], timeout: float = 30.0) -> Any:
        """调用工具"""
        if name not in self.tools:
            raise MCPException("TOOL_NOT_FOUND", f"工具不存在: {name}")
        
        try:
            if self.config.type == "websocket":
                return await self._call_tool_websocket(name, parameters)
            elif self.config.type == "http":
                return await self._call_tool_http(name, parameters)
            elif self.config.type == "sse":
                return await self._call_tool_sse(name, parameters, timeout)
            elif self.config.type == "stream_http":
                return await self._call_tool_stream_http(name, parameters)
            elif self.config.type in ["subprocess", "local"]:
                return await self._call_tool_rpc(name, parameters)
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            raise
    
    async def _call_tool_websocket(self, name: str, parameters: Dict[str, Any]) -> Any:
        """通过WebSocket调用工具"""
        message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": parameters
            },
            "id": 3
        }
        
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        if "error" in response_data:
            raise MCPException("TOOL_CALL_FAILED", f"工具调用失败: {response_data['error']}")
        
        return response_data.get("result")
    
    async def _call_tool_http(self, name: str, parameters: Dict[str, Any]) -> Any:
        """通过HTTP调用工具"""
        async with self.session.post(
            f"/tools/{name}/call",
            json={"arguments": parameters}
        ) as response:
            if response.status != 200:
                raise MCPException("TOOL_CALL_FAILED", f"HTTP工具调用失败: {response.status}")
            
            return await response.json()
    
    async def _call_tool_sse(self, name: str, parameters: Dict[str, Any], timeout: float = 30.0) -> Any:
        """通过SSE调用工具"""
        # SSE工具调用：通过HTTP POST发送请求，通过SSE接收响应
        
        # 确保SSE连接是活跃的
        if not self.sse_task or self.sse_task.done():
            logger.warning("⚠️ SSE连接未建立或已断开，尝试重新连接...")
            uri = f"http://{self.config.host}:{self.config.port}{self.config.path}"
            self.sse_task = asyncio.create_task(self._sse_event_listener(uri))
            # 等待连接建立
            await asyncio.sleep(2)
            
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        
        # 生成唯一的请求ID
        import uuid
        request_id = str(uuid.uuid4())
        
        headers = {"Content-Type": "application/json"}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        # 发送工具调用请求
        request_data = {
            "id": request_id,
            "name": name,
            "arguments": parameters
        }
        
        logger.info(f"发送SSE工具调用请求: {name}, ID: {request_id}")
        
        async with self.session.post(
            f"http://{self.config.host}:{self.config.port}/tools/call",
            json=request_data,
            headers=headers
        ) as response:
            if response.status != 200:
                raise MCPException("TOOL_CALL_FAILED", f"SSE工具调用失败: {response.status}")
            
            # HTTP响应只是确认请求已接收，实际结果通过SSE返回
            response_data = await response.json()
            logger.info(f"工具调用请求已发送: {response_data}")
        
        # 等待SSE事件中的工具执行结果
        return await self._wait_for_tool_result(request_id, timeout)
    
    async def _wait_for_tool_result(self, request_id: str, timeout: float = 30.0) -> Any:
        """等待工具执行结果"""
        logger.info(f"等待工具执行结果: {request_id}")
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # 等待消息队列中的结果
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0  # 短超时，用于检查总超时
                )
                
                # 检查是否是我们等待的结果
                if message.get("id") == request_id:
                    if message.get("type") == "tool_result":
                        logger.info(f"收到工具执行结果: {request_id}")
                        return message.get("result")
                    elif message.get("type") == "tool_error":
                        logger.error(f"工具执行失败: {request_id}, 错误: {message.get('error')}")
                        raise MCPException("TOOL_EXECUTION_FAILED", message.get("error", "未知错误"))
                else:
                    # 不是我们等待的结果，重新放回队列
                    await self.message_queue.put(message)
                
            except asyncio.TimeoutError:
                # 检查总超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise MCPException("TOOL_CALL_TIMEOUT", f"工具调用超时: {request_id}")
                continue
    
    async def _call_tool_stream_http(self, name: str, parameters: Dict[str, Any]) -> Any:
        """通过Stream HTTP调用工具"""
        # Stream HTTP用于流式响应，可能需要特殊处理
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.config.auth_headers:
            headers.update(self.config.auth_headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        async with self.session.post(
            f"http://{self.config.host}:{self.config.port}/tools/{name}/call",
            json={"arguments": parameters},
            headers=headers
        ) as response:
            if response.status != 200:
                raise MCPException("TOOL_CALL_FAILED", f"Stream HTTP工具调用失败: {response.status}")
            
            # 处理流式响应
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                result = []
                async for line in response.content:
                    if line.strip():
                        result.append(line.decode('utf-8'))
                return {"stream_data": result}
            else:
                return await response.json()
    
    async def _call_tool_rpc(self, name: str, parameters: Dict[str, Any]) -> Any:
        """通过RPC调用工具"""
        # 子进程或本地RPC工具调用
        pass
    
    async def disconnect(self):
        """断开连接"""
        self.status = MCPConnectionStatus.DISCONNECTED
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        
        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass
            self.sse_task = None
        
        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass
            self.stream_task = None
        
        logger.info(f"MCP服务器连接已断开: {self.config.name}")
    
    async def ping(self) -> bool:
        """心跳检测"""
        try:
            if self.config.type == "websocket" and self.websocket:
                await self.websocket.ping()
                self.last_ping = datetime.now()
                return True
            elif self.config.type == "http" and self.session:
                async with self.session.get("/health") as response:
                    self.last_ping = datetime.now()
                    return response.status == 200
            elif self.config.type == "sse" and self.session:
                # SSE连接通过心跳事件检测
                if self.last_ping:
                    # 检查最后一次心跳时间
                    time_since_ping = (datetime.now() - self.last_ping).total_seconds()
                    return time_since_ping < 60  # 60秒内有心跳认为连接正常
                return False
            elif self.config.type == "subprocess" and self.process:
                self.last_ping = datetime.now()
                return self.process.returncode is None
            
            return False
        except Exception as e:
            logger.warning(f"心跳检测失败 {self.config.name}: {e}")
            return False
    
    async def reconnect(self) -> bool:
        """重新连接"""
        logger.info(f"尝试重新连接MCP服务器: {self.config.name}")
        
        try:
            # 先断开现有连接
            await self.disconnect()
            
            # 等待一段时间后重连
            await asyncio.sleep(self.config.retry_delay or 5)
            
            # 重新连接
            return await self.connect()
            
        except Exception as e:
            logger.error(f"重新连接失败 {self.config.name}: {e}")
            return False


class EnhancedMCPClient:
    """增强的MCP客户端"""
    
    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.connections: Dict[str, MCPServerConnection] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.stats = MCPStats()
        self.status = MCPConnectionStatus.DISCONNECTED
        
    async def connect(self) -> None:
        """连接到所有MCP服务器"""
        try:
            self.status = MCPConnectionStatus.CONNECTING
            logger.info("正在连接MCP服务器...")
            
            # 连接所有启用的服务器
            enabled_servers = self.config_manager.get_enabled_servers()
            connection_tasks = []
            
            for server_config in enabled_servers:
                connection = MCPServerConnection(server_config)
                self.connections[server_config.name] = connection
                connection.set_config_manager(self.config_manager) # 设置配置管理器
                connection_tasks.append(connection.connect())
            
            # 等待所有连接完成
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            
            # 收集工具
            self._collect_tools()
            
            # 更新状态
            connected_count = sum(1 for result in results if result is True)
            if connected_count > 0:
                self.status = MCPConnectionStatus.CONNECTED
                logger.info(f"MCP客户端连接成功，已连接 {connected_count}/{len(enabled_servers)} 个服务器")
            else:
                self.status = MCPConnectionStatus.ERROR
                raise MCPException("CONNECTION_FAILED", "所有MCP服务器连接失败")
            
        except Exception as e:
            self.status = MCPConnectionStatus.ERROR
            logger.error(f"MCP连接失败: {e}")
            raise
    
    def _collect_tools(self):
        """收集所有连接的工具"""
        self.tools.clear()
        
        for connection in self.connections.values():
            if connection.status == MCPConnectionStatus.CONNECTED:
                for tool_name, tool in connection.tools.items():
                    # 检查工具配置
                    tool_config = self.config_manager.get_tool_by_name(tool_name)
                    if tool_config:
                        # 如果有配置，检查是否启用
                        if tool_config.enabled:
                            self.tools[tool_name] = tool
                            logger.debug(f"✅ 工具已启用并加载: {tool_name}")
                        else:
                            logger.debug(f"⚠️ 工具已禁用，跳过: {tool_name}")
                    else:
                        # 如果没有配置，默认加载工具（向后兼容）
                        self.tools[tool_name] = tool
                        logger.debug(f"📦 工具无配置，默认加载: {tool_name}")
        
        self.stats.active_tools = len(self.tools)
        logger.info(f"收集到 {len(self.tools)} 个可用工具")
    
    async def list_tools(self) -> List[MCPTool]:
        """列出所有可用工具"""
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self.tools.get(name)
    
    async def call_tool(
        self, 
        name: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """调用工具"""
        if name not in self.tools:
            raise MCPException("TOOL_NOT_FOUND", f"工具不存在: {name}")
        
        # 查找工具对应的服务器
        server_config = self.config_manager.get_server_for_tool(name)
        if not server_config:
            raise MCPException("SERVER_NOT_FOUND", f"找不到工具 {name} 对应的服务器")
        
        connection = self.connections.get(server_config.name)
        if not connection or connection.status != MCPConnectionStatus.CONNECTED:
            raise MCPException("SERVER_NOT_CONNECTED", f"服务器 {server_config.name} 未连接")
        
        # 应用工具配置
        tool_config = self.config_manager.get_tool_by_name(name)
        tool_timeout = 30.0  # 默认超时时间
        if tool_config:
            # 合并默认参数
            if tool_config.default_parameters:
                merged_params = tool_config.default_parameters.copy()
                merged_params.update(parameters)
                parameters = merged_params
            
            # 设置超时
            if hasattr(tool_config, 'timeout') and tool_config.timeout:
                tool_timeout = float(tool_config.timeout)
                logger.info(f"使用工具 {name} 的自定义超时时间: {tool_timeout}秒")
        
        # 执行工具调用
        start_time = datetime.now()
        try:
            result = await connection.call_tool(name, parameters, tool_timeout)
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(True, execution_time, False)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, execution_time, False)
            raise
    
    async def call_tools_batch(
        self, 
        calls: List[Dict[str, Any]]
    ) -> List[MCPToolResult]:
        """批量调用工具"""
        tasks = []
        for call in calls:
            task = self._call_tool_safe(
                call["name"], 
                call.get("parameters", {}),
                call.get("context")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 转换结果
        tool_results = []
        for i, result in enumerate(results):
            call = calls[i]
            if isinstance(result, Exception):
                tool_results.append(MCPToolResult(
                    id=call.get("id", f"call_{i}"),
                    tool_name=call["name"],
                    success=False,
                    error={"code": "EXECUTION_ERROR", "message": str(result)}
                ))
            else:
                tool_results.append(MCPToolResult(
                    id=call.get("id", f"call_{i}"),
                    tool_name=call["name"],
                    success=True,
                    result=result
                ))
        
        return tool_results
    
    async def _call_tool_safe(self, name: str, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """安全调用工具"""
        try:
            return await self.call_tool(name, parameters, context)
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            raise
    
    def get_stats(self) -> MCPStats:
        """获取统计信息"""
        return self.stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = MCPStats()
        self.stats.active_tools = len(self.tools)
    
    async def disconnect(self) -> None:
        """断开所有连接"""
        disconnect_tasks = []
        for connection in self.connections.values():
            disconnect_tasks.append(connection.disconnect())
        
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        self.connections.clear()
        self.tools.clear()
        self.status = MCPConnectionStatus.DISCONNECTED
        logger.info("MCP客户端已断开连接")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        server_status = {}
        
        for name, connection in self.connections.items():
            is_healthy = await connection.ping()
            server_status[name] = {
                "status": connection.status.value,
                "healthy": is_healthy,
                "tools_count": len(connection.tools),
                "last_ping": connection.last_ping.isoformat() if connection.last_ping else None
            }
        
        return {
            "overall_status": self.status.value,
            "total_tools": len(self.tools),
            "servers": server_status,
            "stats": self.stats.dict()
        }
    
    def _update_stats(self, success: bool, execution_time: float, from_cache: bool) -> None:
        """更新统计信息"""
        self.stats.total_calls += 1
        
        if success:
            self.stats.successful_calls += 1
        else:
            self.stats.failed_calls += 1
        
        # 更新平均执行时间
        if self.stats.total_calls > 0:
            total_time = self.stats.average_execution_time * (self.stats.total_calls - 1) + execution_time
            self.stats.average_execution_time = total_time / self.stats.total_calls
        
        # 更新缓存命中率
        if from_cache:
            cache_hits = self.stats.cache_hit_rate * (self.stats.total_calls - 1) + 1
            self.stats.cache_hit_rate = cache_hits / self.stats.total_calls
        else:
            self.stats.cache_hit_rate = (self.stats.cache_hit_rate * (self.stats.total_calls - 1)) / self.stats.total_calls
    
    def reload_config(self):
        """重新加载配置"""
        self.config_manager.reload_config()
        # TODO: 重新连接服务器和更新工具 