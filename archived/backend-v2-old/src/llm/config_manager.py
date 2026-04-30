"""
LLM配置管理器
基于MCPConfigManager的成熟架构，提供LLM配置的文件管理功能
支持环境变量初始化、文件读写、备份和热重载
"""

import json
import os
import shutil
import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# 文件监控相关导入
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("⚠️ watchdog未安装，文件热重载功能将被禁用")

from .config import (
    LLMConfiguration, 
    LLMProviderConfig, 
    DEFAULT_PROVIDER_TEMPLATES,
    create_default_configuration,
    load_configuration_from_file,
    save_configuration_to_file
)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更监控处理器"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.last_reload_time = 0
        self.debounce_delay = 1.0  # 防抖延迟1秒
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        # 检查是否是我们关心的配置文件
        if not self._is_config_file(event.src_path):
            return
            
        current_time = time.time()
        # 防抖机制：如果距离上次重载不足延迟时间，则忽略
        if current_time - self.last_reload_time < self.debounce_delay:
            logger.debug(f"文件变更过于频繁，跳过重载: {event.src_path}")
            return
            
        self.last_reload_time = current_time
        logger.info(f"🔄 检测到配置文件变更: {event.src_path}")
        
        # 延迟重载，确保文件写入完成
        threading.Timer(0.2, self._reload_config).start()
        
    def _is_config_file(self, file_path: str) -> bool:
        """检查是否是配置文件"""
        path = Path(file_path)
        config_file_path = Path(self.config_manager.config_file)
        
        try:
            return path.resolve() == config_file_path.resolve()
        except (OSError, ValueError):
            return False
            
    def _reload_config(self):
        """重载配置文件"""
        try:
            logger.info("🔄 开始热重载配置...")
            
            # 验证文件是否存在且可读
            if not os.path.exists(self.config_manager.config_file):
                logger.warning(f"⚠️ 配置文件不存在，跳过重载: {self.config_manager.config_file}")
                return
                
            # 尝试解析JSON文件，确保格式正确
            try:
                with open(self.config_manager.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"❌ 配置文件JSON格式错误，跳过重载: {e}")
                return
            except Exception as e:
                logger.error(f"❌ 读取配置文件失败，跳过重载: {e}")
                return
                
            # 重新加载配置
            old_config = self.config_manager.current_config
            self.config_manager._load_config()
            
            if self.config_manager.current_config:
                logger.info("✅ 配置热重载成功")
                
                # 记录主要变更
                if old_config:
                    self._log_config_changes(old_config, self.config_manager.current_config)
                else:
                    logger.info("📝 首次加载配置")
                    
                # 通知配置变更（如果有监听器）
                self.config_manager._notify_config_changed()
            else:
                logger.error("❌ 配置热重载失败，配置对象为空")
                
        except Exception as e:
            logger.error(f"❌ 配置热重载过程中发生错误: {e}")
            
    def _log_config_changes(self, old_config: LLMConfiguration, new_config: LLMConfiguration):
        """记录配置变更信息"""
        try:
            changes = []
            
            # 检查默认提供商变更
            if old_config.default_provider != new_config.default_provider:
                changes.append(f"默认提供商: {old_config.default_provider} → {new_config.default_provider}")
                
            # 检查提供商数量变更
            old_count = len(old_config.providers)
            new_count = len(new_config.providers)
            if old_count != new_count:
                changes.append(f"提供商数量: {old_count} → {new_count}")
                
            # 检查启用的提供商变更
            old_enabled = {p.id for p in old_config.providers if p.enabled}
            new_enabled = {p.id for p in new_config.providers if p.enabled}
            if old_enabled != new_enabled:
                changes.append(f"启用的提供商: {old_enabled} → {new_enabled}")
                
            if changes:
                logger.info(f"📋 检测到配置变更: {'; '.join(changes)}")
            else:
                logger.info("📋 配置内容无明显变更")
                
        except Exception as e:
            logger.debug(f"记录配置变更失败: {e}")


class LLMConfigManager:
    """LLM配置管理器 - 基于MCPConfigManager的成熟架构"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化LLM配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 config/llm_config.json
        """
        # 统一使用config/llm_config.json作为默认配置文件路径
        self.config_file = config_file or "config/llm_config.json"
        self.config_dir = Path(self.config_file).parent
        self.backup_dir = self.config_dir / "backups"
        
        # 创建必要目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 找到环境变量文件
        self.env_file_path = self._find_env_file()
        
        # 执行配置文件迁移（如果需要）
        self.migrate_config_if_needed()
        
        # 验证配置路径一致性
        self._validate_config_path_consistency()
        
        self.current_config: Optional[LLMConfiguration] = None
        
        # 文件监控相关属性
        self.file_observer: Optional[Observer] = None
        self.file_handler: Optional[ConfigFileHandler] = None
        self.file_watcher_enabled = True  # 默认启用文件监控
        self.config_change_callbacks = []  # 配置变更回调列表
        
        # 加载配置
        self._load_config()
        
        # 启动文件监控
        self.start_file_watcher()
        
        logger.info(f"✅ LLMConfigManager初始化完成: {self.config_file}")
    
    def _find_env_file(self) -> str:
        """查找环境变量文件"""
        possible_paths = [
            "config.env",
            ".env", 
            "backend/config.env",
            "backend/.env"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 如果都不存在，使用config.env作为默认
        return "config.env"
    
    def _validate_config_path_consistency(self):
        """验证配置路径一致性"""
        expected_path = Path("config/llm_config.json")
        current_path = Path(self.config_file)
        
        if current_path.resolve() != expected_path.resolve():
            logger.warning(
                f"LLM配置路径不一致 - "
                f"当前: {current_path}, 期望: {expected_path}"
            )
            
            # 检查是否存在其他位置的配置文件
            other_paths = [
                "backend/config/llm_config.json",
                "llm_config.json",
                "../config/llm_config.json"
            ]
            
            for other_path in other_paths:
                if Path(other_path).exists():
                    logger.warning(f"发现其他位置的配置文件: {other_path}")
                    logger.info(f"建议使用统一路径: {expected_path}")
        else:
            logger.debug(f"LLM配置路径一致性检查通过: {current_path}")
    
    def migrate_config_if_needed(self) -> bool:
        """如果需要，迁移配置文件到标准路径"""
        expected_path = Path("config/llm_config.json")
        
        # 如果标准路径已存在，无需迁移
        if expected_path.exists():
            return False
            
        # 查找可能的旧配置文件路径（按优先级排序）
        old_paths = [
            "backend/config/llm_config.json",
            "llm_config.json",
            "../config/llm_config.json"
        ]
        
        for old_path in old_paths:
            old_file = Path(old_path)
            if old_file.exists():
                try:
                    # 确保目标目录存在
                    expected_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制配置文件
                    shutil.copy2(old_file, expected_path)
                    
                    logger.info(f"✅ 已迁移LLM配置文件: {old_path} -> {expected_path}")
                    
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
    
    def migrate_from_env(self) -> bool:
        """从环境变量初始化配置文件"""
        try:
            # 如果配置文件已存在，不进行迁移
            if Path(self.config_file).exists():
                logger.info(f"配置文件已存在，跳过环境变量迁移: {self.config_file}")
                return False
            
            logger.info("开始从环境变量迁移LLM配置...")
            
            # 读取环境变量配置
            env_config = self._read_env_config()
            
            # 创建配置对象
            config = LLMConfiguration(
                name="从环境变量迁移的LLM配置",
                description=f"从环境变量自动迁移生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                enabled=env_config.get("enabled", True),
                providers=[self._create_provider_from_env(env_config)],
                default_provider=env_config.get("provider", "openai")
            )
            
            # 保存配置文件
            self._save_config(config)
            self.current_config = config
            
            logger.info(f"✅ 成功从环境变量迁移LLM配置到: {self.config_file}")
            logger.info(f"提供商: {env_config.get('provider', 'openai')}, 模型: {env_config.get('model', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 从环境变量迁移配置失败: {e}")
            return False
    
    def _read_env_config(self) -> Dict[str, Any]:
        """读取环境变量配置"""
        try:
            # 重新加载环境变量确保最新
            load_dotenv(self.env_file_path, override=True)
            
            config_data = {
                "enabled": os.getenv("LLM_ENABLED", "true").lower() == "true",
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                "api_key": os.getenv("LLM_API_KEY", ""),
                "base_url": os.getenv("LLM_BASE_URL"),
                "organization": os.getenv("LLM_ORGANIZATION"),
                "api_version": os.getenv("LLM_API_VERSION"),
                "deployment_name": os.getenv("LLM_DEPLOYMENT_NAME"),
                "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
                "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2000")),
                "stream": os.getenv("LLM_STREAM", "false").lower() == "true"
            }
            
            # 移除空值但保留重要字段
            filtered_config = {}
            important_fields = {"enabled", "provider", "model", "timeout", "max_retries", "temperature", "max_tokens", "stream"}
            
            for key, value in config_data.items():
                if key in important_fields:
                    filtered_config[key] = value
                elif value is not None and value != "":
                    filtered_config[key] = value
            
            return filtered_config
            
        except Exception as e:
            logger.error(f"读取环境变量配置失败: {e}")
            # 返回默认配置
            return {
                "enabled": True,
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "timeout": 30,
                "max_retries": 3,
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
    
    def _create_provider_from_env(self, env_config: Dict[str, Any]) -> LLMProviderConfig:
        """从环境变量配置创建提供商配置"""
        provider_id = env_config.get("provider", "openai")
        
        # 从预定义模板开始
        if provider_id in DEFAULT_PROVIDER_TEMPLATES:
            template = DEFAULT_PROVIDER_TEMPLATES[provider_id]
            provider = LLMProviderConfig(
                id=template.id,
                name=template.name,
                model=env_config.get("model", template.model),
                enabled=env_config.get("enabled", True),
                api_key=env_config.get("api_key", template.api_key),
                base_url=env_config.get("base_url", template.base_url),
                deployment_name=env_config.get("deployment_name"),
                api_version=env_config.get("api_version"),
                organization=env_config.get("organization"),
                temperature=env_config.get("temperature", template.temperature),
                max_tokens=env_config.get("max_tokens", template.max_tokens),
                timeout=env_config.get("timeout", template.timeout),
                max_retries=env_config.get("max_retries", template.max_retries),
                stream=env_config.get("stream", template.stream),
                supports_functions=template.supports_functions,
                supports_vision=template.supports_vision,
                supports_streaming=template.supports_streaming
            )
        else:
            # 创建自定义提供商
            provider = LLMProviderConfig(
                id=provider_id,
                name=f"自定义{provider_id}",
                model=env_config.get("model", "gpt-3.5-turbo"),
                enabled=env_config.get("enabled", True),
                api_key=env_config.get("api_key"),
                base_url=env_config.get("base_url"),
                deployment_name=env_config.get("deployment_name"),
                api_version=env_config.get("api_version"),
                organization=env_config.get("organization"),
                temperature=env_config.get("temperature", 0.7),
                max_tokens=env_config.get("max_tokens", 2000),
                timeout=env_config.get("timeout", 30),
                max_retries=env_config.get("max_retries", 3),
                stream=env_config.get("stream", False)
            )
        
        return provider
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.current_config = LLMConfiguration(**config_data)
                logger.info(f"✅ LLM配置加载成功: {self.config_file}")
            else:
                # 尝试从环境变量迁移
                if self.migrate_from_env():
                    logger.info("✅ 已从环境变量创建初始LLM配置")
                else:
                    # 创建默认配置
                    self.current_config = create_default_configuration()
                    self._save_config()
                    logger.info("✅ 创建默认LLM配置")
        except Exception as e:
            logger.error(f"❌ LLM配置加载失败: {e}")
            self.current_config = create_default_configuration()
    
    def _save_config(self, config: Optional[LLMConfiguration] = None):
        """保存配置文件"""
        try:
            if config is None:
                config = self.current_config
            
            if config is None:
                raise ValueError("没有配置可保存")
            
            # 创建备份
            self._create_backup()
            
            # 保存配置
            save_configuration_to_file(config, self.config_file)
            
            logger.info(f"✅ LLM配置保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"❌ LLM配置保存失败: {e}")
            raise
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"llm_config_{timestamp}.json"
                
                shutil.copy2(self.config_file, backup_file)
                
                # 只保留最近5个备份
                backups = sorted(self.backup_dir.glob("llm_config_*.json"))
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        old_backup.unlink()
                        
                logger.debug(f"创建配置备份: {backup_file}")
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")
    
    # 公共API
    
    def get_config(self) -> LLMConfiguration:
        """获取当前配置"""
        if self.current_config is None:
            self.current_config = create_default_configuration()
        return self.current_config
    
    def get_enabled_providers(self) -> List[LLMProviderConfig]:
        """获取所有启用的提供商配置"""
        config = self.get_config()
        return config.get_enabled_providers()
    
    def get_default_provider(self) -> Optional[LLMProviderConfig]:
        """获取默认提供商配置"""
        config = self.get_config()
        return config.get_default_provider_config()
    
    def get_provider(self, provider_id: str) -> Optional[LLMProviderConfig]:
        """根据ID获取提供商配置"""
        config = self.get_config()
        return config.get_provider(provider_id)
    
    def add_provider(self, provider: LLMProviderConfig) -> bool:
        """添加提供商配置"""
        try:
            config = self.get_config()
            if config.add_provider(provider):
                self._save_config(config)
                logger.info(f"✅ 添加LLM提供商: {provider.name}")
                return True
            else:
                logger.warning(f"提供商ID已存在: {provider.id}")
                return False
        except Exception as e:
            logger.error(f"❌ 添加提供商失败: {e}")
            return False
    
    def update_provider(self, provider_id: str, provider: LLMProviderConfig) -> bool:
        """更新提供商配置"""
        try:
            config = self.get_config()
            if config.update_provider(provider_id, provider):
                self._save_config(config)
                logger.info(f"✅ 更新LLM提供商: {provider.name}")
                return True
            else:
                logger.warning(f"提供商不存在: {provider_id}")
                return False
        except Exception as e:
            logger.error(f"❌ 更新提供商失败: {e}")
            return False
    
    def remove_provider(self, provider_id: str) -> bool:
        """删除提供商配置"""
        try:
            config = self.get_config()
            if config.remove_provider(provider_id):
                self._save_config(config)
                logger.info(f"✅ 删除LLM提供商: {provider_id}")
                return True
            else:
                logger.warning(f"提供商不存在: {provider_id}")
                return False
        except Exception as e:
            logger.error(f"❌ 删除提供商失败: {e}")
            return False
    
    def update_config(self, config: LLMConfiguration) -> bool:
        """更新完整配置"""
        try:
            # 验证配置
            config.model_validate(config.model_dump())
            
            self.current_config = config
            self._save_config(config)
            logger.info("✅ LLM配置更新成功")
            return True
        except Exception as e:
            logger.error(f"❌ 更新配置失败: {e}")
            return False
    
    def reload_config(self):
        """重新加载配置"""
        try:
            self._load_config()
            logger.info("LLM配置已重新加载")
        except Exception as e:
            logger.error(f"重新加载LLM配置失败: {e}")
    
    async def reload_config_async(self):
        """异步重新加载配置"""
        self.reload_config()
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表"""
        backups = []
        try:
            for backup_file in sorted(self.backup_dir.glob("llm_config_*.json"), reverse=True):
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
            
            # 加载备份配置
            config = load_configuration_from_file(str(backup_file))
            
            # 更新当前配置
            self.current_config = config
            self._save_config(config)
            
            logger.info(f"✅ 恢复备份成功: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 恢复备份失败: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置"""
        try:
            config = self.get_config()
            save_configuration_to_file(config, file_path)
            logger.info(f"✅ 配置导出成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置导出失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            config = load_configuration_from_file(file_path)
            self.current_config = config
            self._save_config(config)
            logger.info(f"✅ 配置导入成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 配置导入失败: {e}")
            return False
            
    # 文件监控和热重载相关方法
    
    def start_file_watcher(self) -> bool:
        """启动文件监控"""
        if not WATCHDOG_AVAILABLE:
            logger.info("📁 watchdog不可用，跳过文件监控启动")
            return False
            
        if not self.file_watcher_enabled:
            logger.info("📁 文件监控已禁用")
            return False
            
        if self.file_observer and self.file_observer.is_alive():
            logger.info("📁 文件监控已在运行")
            return True
            
        try:
            # 确保配置目录存在
            if not self.config_dir.exists():
                logger.warning(f"⚠️ 配置目录不存在，无法启动文件监控: {self.config_dir}")
                return False
                
            # 创建文件监控处理器
            self.file_handler = ConfigFileHandler(self)
            
            # 创建监控器
            self.file_observer = Observer()
            self.file_observer.schedule(
                self.file_handler, 
                str(self.config_dir), 
                recursive=False
            )
            
            # 启动监控
            self.file_observer.start()
            
            logger.info(f"📁 文件监控启动成功，监控目录: {self.config_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动文件监控失败: {e}")
            return False
    
    def stop_file_watcher(self) -> bool:
        """停止文件监控"""
        try:
            if self.file_observer and self.file_observer.is_alive():
                self.file_observer.stop()
                self.file_observer.join(timeout=2.0)
                logger.info("📁 文件监控已停止")
                
            self.file_observer = None
            self.file_handler = None
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止文件监控失败: {e}")
            return False
    
    def restart_file_watcher(self) -> bool:
        """重启文件监控"""
        logger.info("🔄 重启文件监控...")
        self.stop_file_watcher()
        return self.start_file_watcher()
    
    def set_file_watcher_enabled(self, enabled: bool):
        """设置文件监控启用状态"""
        if self.file_watcher_enabled == enabled:
            return
            
        self.file_watcher_enabled = enabled
        
        if enabled:
            self.start_file_watcher()
        else:
            self.stop_file_watcher()
            
        logger.info(f"📁 文件监控状态设置为: {'启用' if enabled else '禁用'}")
    
    def is_file_watcher_running(self) -> bool:
        """检查文件监控是否正在运行"""
        return (
            self.file_observer is not None and 
            self.file_observer.is_alive() and 
            self.file_watcher_enabled
        )
    
    def add_config_change_callback(self, callback):
        """添加配置变更回调"""
        if callback not in self.config_change_callbacks:
            self.config_change_callbacks.append(callback)
            logger.debug(f"添加配置变更回调: {callback}")
    
    def remove_config_change_callback(self, callback):
        """移除配置变更回调"""
        if callback in self.config_change_callbacks:
            self.config_change_callbacks.remove(callback)
            logger.debug(f"移除配置变更回调: {callback}")
    
    def _notify_config_changed(self):
        """通知配置变更"""
        for callback in self.config_change_callbacks:
            try:
                callback(self.current_config)
            except Exception as e:
                logger.error(f"❌ 执行配置变更回调失败: {e}")
    
    def get_file_watcher_status(self) -> Dict[str, Any]:
        """获取文件监控状态信息"""
        return {
            "watchdog_available": WATCHDOG_AVAILABLE,
            "enabled": self.file_watcher_enabled,
            "running": self.is_file_watcher_running(),
            "config_file": str(self.config_file),
            "config_dir": str(self.config_dir),
            "callbacks_count": len(self.config_change_callbacks)
        }
    
    def __del__(self):
        """析构函数，确保文件监控正确停止"""
        try:
            self.stop_file_watcher()
        except Exception:
            pass  # 析构函数中忽略异常


# 全局配置管理器实例
_llm_config_manager = None

def get_llm_config_manager() -> LLMConfigManager:
    """获取全局LLM配置管理器"""
    global _llm_config_manager
    if _llm_config_manager is None:
        _llm_config_manager = LLMConfigManager()
    return _llm_config_manager 