"""
MCP配置管理器
提供类似Cursor的MCP工具配置体验
支持动态配置、热重载、连接测试等功能
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from loguru import logger

from .config import MCPConfiguration, MCPServerConfig, MCPToolConfig
from .types import MCPConnectionStatus, MCPException


class MCPConfigTemplate(BaseModel):
    """MCP配置模板"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    icon: Optional[str] = Field(None, description="图标")
    config: Dict[str, Any] = Field(..., description="配置内容")
    tags: List[str] = Field(default_factory=list, description="标签")
    author: Optional[str] = Field(None, description="作者")
    version: str = Field("1.0.0", description="版本")


class MCPConfigValidationResult(BaseModel):
    """配置验证结果"""
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    server_status: Dict[str, str] = Field(default_factory=dict, description="服务器状态")
    tool_status: Dict[str, str] = Field(default_factory=dict, description="工具状态")


class MCPConfigManager:
    """MCP配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        # 统一使用config/mcp_config.json作为默认配置文件路径
        self.config_file = config_file or "config/mcp_config.json"
        self.config_dir = Path(self.config_file).parent
        self.templates_dir = self.config_dir / "templates"
        self.backup_dir = self.config_dir / "backups"
        
        # 创建必要目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行配置文件迁移（如果需要）
        self.migrate_config_if_needed()
        
        # 验证配置路径一致性
        self._validate_config_path_consistency()
        
        self.current_config: Optional[MCPConfiguration] = None
        self.templates: Dict[str, MCPConfigTemplate] = {}
        
        # 加载配置和模板
        self._load_config()
        self._load_templates()
    
    def _validate_config_path_consistency(self):
        """验证配置路径一致性"""
        expected_path = Path("config/mcp_config.json")
        current_path = Path(self.config_file)
        
        if current_path.resolve() != expected_path.resolve():
            logger.warning(
                f"MCP配置路径不一致 - "
                f"当前: {current_path}, 期望: {expected_path}"
            )
            
            # 检查是否存在其他位置的配置文件
            other_paths = [
                "backend/config/mcp_config.json",
                "mcp_config.json",
                "../config/mcp_config.json"
            ]
            
            for other_path in other_paths:
                if Path(other_path).exists():
                    logger.warning(f"发现其他位置的配置文件: {other_path}")
                    logger.info(f"建议使用统一路径: {expected_path}")
        else:
            logger.debug(f"MCP配置路径一致性检查通过: {current_path}")
    
    def migrate_config_if_needed(self) -> bool:
        """如果需要，迁移配置文件到标准路径"""
        expected_path = Path("config/mcp_config.json")
        
        # 如果标准路径已存在，无需迁移
        if expected_path.exists():
            return False
            
        # 查找可能的旧配置文件路径（按优先级排序）
        old_paths = [
            "backend/config/mcp_config.json",
            "mcp_config.json",
            "../config/mcp_config.json"
        ]
        
        for old_path in old_paths:
            old_file = Path(old_path)
            if old_file.exists():
                try:
                    # 确保目标目录存在
                    expected_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制配置文件
                    import shutil
                    shutil.copy2(old_file, expected_path)
                    
                    logger.info(f"✅ 已迁移MCP配置文件: {old_path} -> {expected_path}")
                    
                    # 创建迁移备份
                    backup_dir = expected_path.parent / "backups"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup_filename = f"migrated_from_{old_path.replace('/', '_').replace('..', 'parent')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = backup_dir / backup_filename
                    shutil.copy2(old_file, backup_path)
                    logger.info(f"✅ 已创建迁移备份: {backup_path}")
                    
                    # 可选：删除旧文件（出于安全考虑，先不删除，只是警告）
                    logger.warning(f"⚠️ 请手动删除旧配置文件: {old_path}")
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ 迁移配置文件失败: {old_path} -> {expected_path}, 错误: {e}")
                    continue
                    
        return False
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # 调试：检查原始JSON数据中的 enabled 字段
                    if 'servers' in config_data:
                        logger.info(f"🔍 原始JSON中的服务器数量: {len(config_data['servers'])}")
                        for srv_data in config_data['servers'][:2]:
                            logger.info(f"🔍   原始JSON - {srv_data.get('name')}: enabled={srv_data.get('enabled')}")
                    self.current_config = MCPConfiguration(**config_data)
                logger.info(f"✅ MCP配置加载成功: {self.config_file}")
            else:
                # 创建默认配置
                self.current_config = self._create_default_config()
                self._save_config()
                logger.info("✅ 创建默认MCP配置")
        except Exception as e:
            logger.error(f"❌ MCP配置加载失败: {e}")
            self.current_config = self._create_default_config()
    
    def _load_templates(self):
        """加载配置模板"""
        try:
            # 内置模板
            self.templates.update(self._get_builtin_templates())
            
            # 从文件加载用户模板
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template = MCPConfigTemplate(**template_data)
                        self.templates[template.name] = template
                except Exception as e:
                    logger.warning(f"加载模板失败 {template_file}: {e}")
                    
            logger.info(f"✅ 加载 {len(self.templates)} 个MCP配置模板")
        except Exception as e:
            logger.error(f"❌ 模板加载失败: {e}")
    
    def _create_default_config(self) -> MCPConfiguration:
        """创建默认配置"""
        return MCPConfiguration(
            name="钉钉K8s运维机器人MCP配置",
            description="支持K8s和SSH操作的MCP服务器配置",
            servers=[],
            tools=[]
        )
    
    def _get_builtin_templates(self) -> Dict[str, MCPConfigTemplate]:
        """获取内置模板"""
        templates = {}
        
        
        # Kubernetes MCP模板 - SSE
        templates["k8s-sse"] = MCPConfigTemplate(
            name="Kubernetes SSE",
            description="通过Server-Sent Events连接的Kubernetes MCP服务器",
            category="kubernetes",
            icon="📡",
            config={
                "type": "sse",
                "host": "localhost",
                "port": 8766,
                "path": "/events",
                "timeout": 30,
                "enabled_tools": [
                    "k8s-watch-pods",
                    "k8s-watch-services",
                    "k8s-watch-events",
                    "k8s-get-logs"
                ]
            },
            tags=["kubernetes", "sse", "events", "streaming"]
        )
        
        # SSH MCP模板 - stdio
        templates["ssh-stdio"] = MCPConfigTemplate(
            name="SSH stdio",
            description="通过stdio进行SSH连接的MCP服务器",
            category="ssh",
            icon="🔗",
            config={
                "type": "stdio",
                "command": "python",
                "args": ["-m", "ssh_jumpserver_mcp"],
                "timeout": 30,
                "enabled_tools": [
                    "ssh-execute",
                    "ssh-asset-list",
                    "ssh-session-manager"
                ]
            },
            tags=["ssh", "stdio", "remote"]
        )
        
        # 文件系统MCP模板
        templates["filesystem"] = MCPConfigTemplate(
            name="File System",
            description="本地文件系统操作MCP服务器",
            category="filesystem",
            icon="📁",
            config={
                "type": "local",
                "enabled_tools": [
                    "fs-read-file",
                    "fs-write-file",
                    "fs-list-directory",
                    "fs-search-files"
                ]
            },
            tags=["filesystem", "local", "files"]
        )
        
        return templates
    
    def _save_config(self):
        """保存配置文件"""
        try:
            # 创建备份
            self._create_backup()
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.current_config.dict(),
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            logger.info(f"✅ MCP配置保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"❌ MCP配置保存失败: {e}")
            raise
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"mcp_config_{timestamp}.json"
                
                import shutil
                shutil.copy2(self.config_file, backup_file)
                
                # 只保留最近5个备份
                backups = sorted(self.backup_dir.glob("mcp_config_*.json"))
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        old_backup.unlink()
                        
                logger.debug(f"创建配置备份: {backup_file}")
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")
    
    # 公共API
    
    def get_config(self) -> MCPConfiguration:
        """获取配置"""
        return self.current_config
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """获取所有启用的服务器配置"""
        if not self.current_config:
            return []
        
        return [
            server for server in self.current_config.servers 
            if server.enabled
        ]
    
    def get_templates(self) -> Dict[str, MCPConfigTemplate]:
        """获取所有模板"""
        return self.templates
    
    def get_template(self, name: str) -> Optional[MCPConfigTemplate]:
        """获取指定模板"""
        return self.templates.get(name)
    
    def add_server(self, server_config: MCPServerConfig) -> bool:
        """添加服务器"""
        try:
            # 检查名称是否已存在
            if any(s.name == server_config.name for s in self.current_config.servers):
                raise ValueError(f"服务器名称已存在: {server_config.name}")
            
            self.current_config.servers.append(server_config)
            self._save_config()
            logger.info(f"✅ 添加MCP服务器: {server_config.name}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加服务器失败: {e}")
            return False
    
    def update_server(self, name: str, server_config: MCPServerConfig) -> bool:
        """更新服务器"""
        try:
            for i, server in enumerate(self.current_config.servers):
                if server.name == name:
                    self.current_config.servers[i] = server_config
                    self._save_config()
                    logger.info(f"✅ 更新MCP服务器: {name}")
                    return True
            
            raise ValueError(f"服务器不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 更新服务器失败: {e}")
            return False
    
    def remove_server(self, name: str) -> bool:
        """删除服务器"""
        try:
            original_count = len(self.current_config.servers)
            self.current_config.servers = [
                s for s in self.current_config.servers if s.name != name
            ]
            
            if len(self.current_config.servers) < original_count:
                self._save_config()
                logger.info(f"✅ 删除MCP服务器: {name}")
                return True
            else:
                raise ValueError(f"服务器不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 删除服务器失败: {e}")
            return False
    
    def toggle_server(self, name: str) -> bool:
        """切换服务器启用状态"""
        try:
            for server in self.current_config.servers:
                if server.name == name:
                    server.enabled = not server.enabled
                    self._save_config()
                    status = "启用" if server.enabled else "禁用"
                    logger.info(f"✅ {status}MCP服务器: {name}")
                    return True
            
            raise ValueError(f"服务器不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 切换服务器状态失败: {e}")
            return False
    
    def add_tool(self, tool_config: MCPToolConfig) -> bool:
        """添加工具"""
        try:
            # 检查名称是否已存在
            if any(t.name == tool_config.name for t in self.current_config.tools):
                raise ValueError(f"工具名称已存在: {tool_config.name}")
            
            self.current_config.tools.append(tool_config)
            self._save_config()
            logger.info(f"✅ 添加MCP工具: {tool_config.name}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加工具失败: {e}")
            return False
    
    def update_tool(self, name: str, tool_config: MCPToolConfig) -> bool:
        """更新工具"""
        try:
            for i, tool in enumerate(self.current_config.tools):
                if tool.name == name:
                    self.current_config.tools[i] = tool_config
                    self._save_config()
                    logger.info(f"✅ 更新MCP工具: {name}")
                    return True
            
            raise ValueError(f"工具不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 更新工具失败: {e}")
            return False
    
    def remove_tool(self, name: str) -> bool:
        """删除工具"""
        try:
            original_count = len(self.current_config.tools)
            self.current_config.tools = [
                t for t in self.current_config.tools if t.name != name
            ]
            
            if len(self.current_config.tools) < original_count:
                self._save_config()
                logger.info(f"✅ 删除MCP工具: {name}")
                return True
            else:
                raise ValueError(f"工具不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 删除工具失败: {e}")
            return False
    
    def toggle_tool(self, name: str) -> bool:
        """切换工具启用状态"""
        try:
            for tool in self.current_config.tools:
                if tool.name == name:
                    tool.enabled = not tool.enabled
                    self._save_config()
                    status = "启用" if tool.enabled else "禁用"
                    logger.info(f"✅ {status}MCP工具: {name}")
                    return True
            
            raise ValueError(f"工具不存在: {name}")
        except Exception as e:
            logger.error(f"❌ 切换工具状态失败: {e}")
            return False
    
    def create_from_template(self, template_name: str, server_name: str, custom_config: Optional[Dict[str, Any]] = None) -> bool:
        """从模板创建服务器"""
        try:
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"模板不存在: {template_name}")
            
            # 合并配置
            config = template.config.copy()
            if custom_config:
                config.update(custom_config)
            
            # 创建服务器配置
            server_config = MCPServerConfig(
                name=server_name,
                **config
            )
            
            return self.add_server(server_config)
        except Exception as e:
            logger.error(f"❌ 从模板创建服务器失败: {e}")
            return False
    
    async def validate_config(self) -> MCPConfigValidationResult:
        """验证配置"""
        result = MCPConfigValidationResult(valid=True)
        
        try:
            # 验证服务器配置
            for server in self.current_config.servers:
                if not server.enabled:
                    continue
                    
                try:
                    # 基本配置验证
                    if server.type == "websocket":
                        if not server.host or not server.port:
                            result.errors.append(f"WebSocket服务器 {server.name} 缺少host或port配置")
                            result.valid = False
                            continue
                    elif server.type == "http":
                        if not server.base_url:
                            result.errors.append(f"HTTP服务器 {server.name} 缺少base_url配置")
                            result.valid = False
                            continue
                    
                    # 连接测试
                    status = await self._test_server_connection(server)
                    result.server_status[server.name] = status
                    
                    if status != "connected":
                        result.warnings.append(f"服务器 {server.name} 连接失败")
                        
                except Exception as e:
                    result.errors.append(f"服务器 {server.name} 验证失败: {str(e)}")
                    result.valid = False
            
            # 验证工具配置
            for tool in self.current_config.tools:
                if not tool.enabled:
                    continue
                    
                try:
                    # 验证工具是否有对应的服务器
                    server_found = False
                    for server in self.current_config.servers:
                        if server.enabled and server.enabled_tools and tool.name in server.enabled_tools:
                            server_found = True
                            break
                    
                    if not server_found:
                        result.warnings.append(f"工具 {tool.name} 没有对应的启用服务器")
                    
                    result.tool_status[tool.name] = "configured" if server_found else "no_server"
                    
                except Exception as e:
                    result.errors.append(f"工具 {tool.name} 验证失败: {str(e)}")
                    result.valid = False
            
        except Exception as e:
            result.errors.append(f"配置验证失败: {str(e)}")
            result.valid = False
        
        return result
    
    async def _test_server_connection(self, server: MCPServerConfig) -> str:
        """测试服务器连接"""
        try:
            logger.info(f"开始测试MCP服务器连接: {server.name} ({server.type})")
            
            # 使用服务器配置的超时时间，或默认30秒
            timeout = server.timeout or 30
            
            if server.type == "websocket":
                import websockets
                uri = f"ws://{server.host}:{server.port}{server.path or '/'}"
                logger.debug(f"WebSocket连接URI: {uri}")
                
                try:
                    async with websockets.connect(uri, timeout=timeout) as websocket:
                        # 发送MCP初始化消息进行协议验证
                        init_message = {
                            "jsonrpc": "2.0",
                            "method": "initialize",
                            "params": {
                                "protocol_version": "2024-11-05",
                                "client_info": {
                                    "name": "mcp-config-test",
                                    "version": "1.0.0"
                                }
                            },
                            "id": 1
                        }
                        
                        await websocket.send(json.dumps(init_message))
                        
                        # 等待响应，使用较短的超时时间
                        import asyncio
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        response_data = json.loads(response)
                        
                        if "error" in response_data:
                            logger.warning(f"MCP协议初始化失败: {response_data['error']}")
                            return "protocol_error"
                        
                        logger.info(f"WebSocket MCP服务器连接成功: {server.name}")
                        return "connected"
                        
                except websockets.exceptions.ConnectionClosed as e:
                    logger.warning(f"WebSocket连接被关闭: {e}")
                    return "connection_closed"
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket连接超时: {uri}")
                    return "timeout"
                    
            elif server.type == "http":
                import aiohttp
                base_url = server.base_url
                if not base_url:
                    logger.error(f"HTTP服务器 {server.name} 缺少base_url配置")
                    return "config_error"
                
                logger.debug(f"HTTP连接URL: {base_url}")
                
                try:
                    timeout_config = aiohttp.ClientTimeout(total=timeout)
                    async with aiohttp.ClientSession(timeout=timeout_config) as session:
                        # 先尝试health检查
                        health_url = f"{base_url.rstrip('/')}/health"
                        async with session.get(health_url) as response:
                            if response.status == 200:
                                logger.info(f"HTTP MCP服务器连接成功: {server.name}")
                                return "connected"
                            else:
                                logger.warning(f"HTTP健康检查失败: {response.status}")
                                return "health_check_failed"
                                
                except aiohttp.ClientConnectorError as e:
                    logger.warning(f"HTTP连接失败: {e}")
                    return "connection_refused"
                except asyncio.TimeoutError:
                    logger.warning(f"HTTP连接超时: {base_url}")
                    return "timeout"
                    
            elif server.type == "sse":
                import aiohttp
                uri = f"http://{server.host}:{server.port}{server.path or '/'}"
                logger.debug(f"SSE连接URI: {uri}")
                
                try:
                    timeout_config = aiohttp.ClientTimeout(total=timeout)
                    async with aiohttp.ClientSession(timeout=timeout_config) as session:
                        headers = {"Accept": "text/event-stream"}
                        if server.auth_token:
                            headers["Authorization"] = f"Bearer {server.auth_token}"
                            
                        async with session.get(uri, headers=headers) as response:
                            if response.status == 200:
                                logger.info(f"SSE MCP服务器连接成功: {server.name}")
                                return "connected"
                            else:
                                logger.warning(f"SSE连接失败: {response.status}")
                                return "sse_connection_failed"
                                
                except aiohttp.ClientConnectorError as e:
                    logger.warning(f"SSE连接失败: {e}")
                    return "connection_refused"
                except asyncio.TimeoutError:
                    logger.warning(f"SSE连接超时: {uri}")
                    return "timeout"
                    
            elif server.type == "subprocess":
                import subprocess
                command = server.command
                args = server.args or []
                
                if not command:
                    logger.error(f"子进程服务器 {server.name} 缺少command配置")
                    return "config_error"
                
                logger.debug(f"子进程命令: {command} {args}")
                
                try:
                    # 尝试启动进程并快速检查
                    process = subprocess.Popen(
                        [command] + args,
                        cwd=server.cwd,
                        env=server.env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    
                    # 等待短时间检查进程是否正常启动
                    import time
                    time.sleep(2)
                    
                    if process.poll() is None:  # 进程仍在运行
                        process.terminate()
                        process.wait()
                        logger.info(f"子进程MCP服务器测试成功: {server.name}")
                        return "connected"
                    else:
                        stderr_output = process.stderr.read().decode() if process.stderr else ""
                        logger.warning(f"子进程启动失败: {stderr_output}")
                        return "subprocess_failed"
                        
                except FileNotFoundError:
                    logger.warning(f"子进程命令未找到: {command}")
                    return "command_not_found"
                except Exception as e:
                    logger.warning(f"子进程测试失败: {e}")
                    return "subprocess_error"
                    
            else:
                logger.warning(f"不支持的服务器类型: {server.type}")
                return "unsupported_type"
                
        except Exception as e:
            logger.error(f"测试服务器连接时发生未知错误 {server.name}: {type(e).__name__}: {e}")
            return "unknown_error"
    
    def export_config(self, file_path: str) -> bool:
        """导出配置"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.current_config.dict(),
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            logger.info(f"✅ 配置导出成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置导出失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                config = MCPConfiguration(**config_data)
                
            self.current_config = config
            self._save_config()
            logger.info(f"✅ 配置导入成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置导入失败: {e}")
            return False
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表"""
        backups = []
        try:
            for backup_file in sorted(self.backup_dir.glob("mcp_config_*.json"), reverse=True):
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
        
        return backups
    
    def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        try:
            backup_file = self.backup_dir / backup_name
            if not backup_file.exists():
                raise ValueError(f"备份文件不存在: {backup_name}")
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                config = MCPConfiguration(**config_data)
            
            self.current_config = config
            self._save_config()
            logger.info(f"✅ 恢复备份成功: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 恢复备份失败: {e}")
            return False
    
    def reload_config(self):
        """重新加载配置"""
        try:
            self._load_config()
            logger.info("配置已重新加载")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
    
    async def reload_config_async(self):
        """异步重新加载配置"""
        self.reload_config()
    
    def get_tool_by_name(self, tool_name: str) -> Optional[MCPToolConfig]:
        """根据名称获取工具配置"""
        if not self.current_config:
            return None
        
        for tool in self.current_config.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def get_server_by_name(self, server_name: str) -> Optional[MCPServerConfig]:
        """根据名称获取服务器配置"""
        if not self.current_config:
            return None
        
        for server in self.current_config.servers:
            if server.name == server_name:
                return server
        return None
    
    def get_all_servers(self) -> List[MCPServerConfig]:
        """获取所有服务器配置"""
        if not self.current_config:
            return []
        return self.current_config.servers
    
    def toggle_server(self, server_name: str) -> bool:
        """切换服务器启用状态"""
        server = self.get_server_by_name(server_name)
        if server:
            server.enabled = not server.enabled
            self.save_config()
            return True
        return False
    
    def save_config(self):
        """保存配置到文件"""
        if not self.current_config or not self.config_file:
            logger.warning("无法保存配置：配置或文件路径为空")
            return
        
        try:
            # 转换为字典格式
            config_dict = self.current_config.model_dump()
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ MCP配置已保存: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存MCP配置失败: {e}")
            raise
    
    def get_server_for_tool(self, tool_name: str) -> Optional[MCPServerConfig]:
        """获取工具所属的服务器配置"""
        if not self.current_config:
            return None
        
        # 查找工具配置
        tool_config = self.get_tool_by_name(tool_name)
        if tool_config:
            # 根据server_name查找服务器配置
            for server in self.current_config.servers:
                if server.name == tool_config.server_name:
                    return server
            return None
        
        # 如果工具没有配置，尝试根据工具名称前缀自动分配服务器
        logger.debug(f"工具 {tool_name} 没有配置，尝试自动分配服务器")
        
        # 根据工具名称前缀自动分配服务器
        if tool_name.startswith("k8s-"):
            # K8s工具分配到k8s-mcp服务器
            for server in self.current_config.servers:
                if server.name == "k8s-mcp" and server.enabled:
                    logger.info(f"🔧 自动分配工具 {tool_name} 到服务器 {server.name}")
                    return server
        elif tool_name.startswith("ecs-"):
            # ECS工具分配到ecs-sse-server服务器
            for server in self.current_config.servers:
                if server.name == "ecs-sse-server" and server.enabled:
                    logger.info(f"🔧 自动分配工具 {tool_name} 到服务器 {server.name}")
                    return server
        elif tool_name.startswith("ssh-"):
            # SSH工具分配到ssh服务器（如果存在）
            for server in self.current_config.servers:
                if "ssh" in server.name.lower() and server.enabled:
                    logger.info(f"🔧 自动分配工具 {tool_name} 到服务器 {server.name}")
                    return server
        
        # 如果没有匹配的前缀，尝试分配到第一个启用的服务器
        for server in self.current_config.servers:
            if server.enabled:
                logger.warning(f"⚠️ 工具 {tool_name} 无法自动分配，使用默认服务器 {server.name}")
                return server
        
        logger.error(f"❌ 无法为工具 {tool_name} 找到合适的服务器")
        return None


# 全局配置管理器实例
_config_manager = None

def get_mcp_config_manager() -> MCPConfigManager:
    """获取全局MCP配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MCPConfigManager()
    return _config_manager 