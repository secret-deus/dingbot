"""
任务配置管理系统
基于现有的MCPConfigManager和LLMConfigManager模式
实现任务配置的文件存储、热重载和备份机制
"""

import json
import os
import shutil
import asyncio
import threading
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
from loguru import logger

# 文件监控相关导入
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("⚠️ watchdog未安装，文件热重载功能将被禁用")

from .models import (
    ScheduledTask, TaskExecution, TaskStatus, TaskType,
    TaskCreateRequest, TaskUpdateRequest,
    get_default_task_config, validate_task_config
)


class TaskConfigFileHandler(FileSystemEventHandler):
    """任务配置文件变更监控处理器"""
    
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager
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
            logger.debug(f"任务配置文件变更过于频繁，跳过重载: {event.src_path}")
            return
            
        self.last_reload_time = current_time
        logger.info(f"🔄 检测到任务配置文件变更: {event.src_path}")
        
        # 延迟重载，确保文件写入完成
        threading.Timer(0.2, self._reload_config).start()
        
    def _is_config_file(self, file_path: str) -> bool:
        """检查是否是配置文件"""
        path = Path(file_path)
        config_file_path = Path(self.task_manager.config_file)
        
        try:
            return path.resolve() == config_file_path.resolve()
        except (OSError, ValueError):
            return False
            
    def _reload_config(self):
        """重载配置文件"""
        try:
            logger.info("🔄 开始热重载任务配置...")
            
            old_tasks = self.task_manager.tasks.copy()
            self.task_manager._load_config()
            
            if self.task_manager.tasks is not None:
                logger.info("✅ 任务配置热重载成功")
                
                # 记录主要变更
                self._log_config_changes(old_tasks, self.task_manager.tasks)
                    
                # 通知配置变更（如果有监听器）
                self.task_manager._notify_config_changed()
            else:
                logger.error("❌ 任务配置热重载失败，配置对象为空")
                
        except Exception as e:
            logger.error(f"❌ 任务配置热重载过程中发生错误: {e}")
            
    def _log_config_changes(self, old_tasks: Dict[str, ScheduledTask], new_tasks: Dict[str, ScheduledTask]):
        """记录配置变更信息"""
        try:
            changes = []
            
            # 检查任务数量变更
            old_count = len(old_tasks)
            new_count = len(new_tasks)
            if old_count != new_count:
                changes.append(f"任务数量: {old_count} → {new_count}")
                
            # 检查启用的任务变更
            old_enabled = {task_id for task_id, task in old_tasks.items() if task.enabled}
            new_enabled = {task_id for task_id, task in new_tasks.items() if task.enabled}
            if old_enabled != new_enabled:
                changes.append(f"启用任务数: {len(old_enabled)} → {len(new_enabled)}")
                
            # 检查新增任务
            added_tasks = set(new_tasks.keys()) - set(old_tasks.keys())
            if added_tasks:
                changes.append(f"新增任务: {len(added_tasks)}个")
                
            # 检查删除任务
            removed_tasks = set(old_tasks.keys()) - set(new_tasks.keys())
            if removed_tasks:
                changes.append(f"删除任务: {len(removed_tasks)}个")
                
            if changes:
                logger.info(f"📋 检测到任务配置变更: {'; '.join(changes)}")
            else:
                logger.info("📋 任务配置内容无明显变更")
                
        except Exception as e:
            logger.debug(f"记录任务配置变更失败: {e}")


class TaskManager:
    """
    任务配置管理器
    基于现有的MCPConfigManager和LLMConfigManager模式
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化任务配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 config/scheduled_tasks.json
        """
        # 统一使用config/scheduled_tasks.json作为默认配置文件路径
        self.config_file = config_file or "config/scheduled_tasks.json"
        self.config_dir = Path(self.config_file).parent
        self.backup_dir = self.config_dir / "backups"
        self.history_dir = self.config_dir / "task_history"
        
        # 创建必要目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 验证配置路径一致性
        self._validate_config_path_consistency()
        
        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: Dict[str, List[TaskExecution]] = {}
        
        # 文件监控相关属性
        self.file_observer: Optional[Observer] = None
        self.file_handler: Optional[TaskConfigFileHandler] = None
        self.file_watcher_enabled = True  # 默认启用文件监控
        self.config_change_callbacks: List[Callable] = []  # 配置变更回调列表
        
        # 加载配置
        self._load_config()
        
        # 启动文件监控
        self.start_file_watcher()
        
        logger.info(f"✅ TaskManager初始化完成: {self.config_file}")
    
    def _validate_config_path_consistency(self):
        """验证配置路径一致性"""
        expected_path = Path("config/scheduled_tasks.json")
        current_path = Path(self.config_file)
        
        if current_path.resolve() != expected_path.resolve():
            logger.warning(
                f"任务配置路径不一致 - "
                f"当前: {current_path}, 期望: {expected_path}"
            )
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载任务配置
                self.tasks = {}
                for task_data in config_data.get("tasks", []):
                    try:
                        task = ScheduledTask(**task_data)
                        # 计算下次执行时间
                        if task.enabled:
                            task.next_run_time = task.calculate_next_run_time()
                        self.tasks[task.id] = task
                    except Exception as e:
                        logger.error(f"加载任务配置失败 {task_data.get('id', 'unknown')}: {e}")
                
                logger.info(f"✅ 任务配置加载成功: {self.config_file}, 共{len(self.tasks)}个任务")
            else:
                # 创建默认配置
                self.tasks = {}
                self._save_config()
                logger.info("✅ 创建默认任务配置")
                
        except Exception as e:
            logger.error(f"❌ 任务配置加载失败: {e}")
            self.tasks = {}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            # 创建备份
            self._create_backup()
            
            # 准备配置数据
            config_data = {
                "version": "1.0",
                "name": "定时任务配置",
                "description": "钉钉K8s运维机器人定时任务配置",
                "updated_at": datetime.now().isoformat(),
                "tasks": [task.model_dump(mode='json') for task in self.tasks.values()]
            }
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 任务配置保存成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"❌ 任务配置保存失败: {e}")
            raise
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"scheduled_tasks_{timestamp}.json"
                
                shutil.copy2(self.config_file, backup_file)
                
                # 只保留最近10个备份
                backups = sorted(self.backup_dir.glob("scheduled_tasks_*.json"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                        
                logger.debug(f"创建任务配置备份: {backup_file}")
        except Exception as e:
            logger.warning(f"创建任务配置备份失败: {e}")
    
    def start_file_watcher(self):
        """启动文件监控"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("⚠️ 文件监控功能不可用，watchdog未安装")
            return
            
        if not self.file_watcher_enabled:
            logger.info("📁 任务配置文件监控已禁用")
            return
            
        try:
            if self.file_observer is not None:
                self.stop_file_watcher()
                
            self.file_handler = TaskConfigFileHandler(self)
            self.file_observer = Observer()
            
            # 监控配置文件所在目录
            watch_path = str(self.config_dir)
            self.file_observer.schedule(self.file_handler, watch_path, recursive=False)
            self.file_observer.start()
            
            logger.info(f"📁 任务配置文件监控已启动: {watch_path}")
            
        except Exception as e:
            logger.error(f"❌ 启动任务配置文件监控失败: {e}")
            self.file_observer = None
            self.file_handler = None
    
    def stop_file_watcher(self):
        """停止文件监控"""
        try:
            if self.file_observer is not None:
                self.file_observer.stop()
                self.file_observer.join(timeout=2.0)
                self.file_observer = None
                self.file_handler = None
                logger.info("📁 任务配置文件监控已停止")
        except Exception as e:
            logger.error(f"❌ 停止任务配置文件监控失败: {e}")
    
    def get_file_watcher_status(self) -> Dict[str, Any]:
        """获取文件监控状态"""
        return {
            "enabled": self.file_watcher_enabled,
            "available": WATCHDOG_AVAILABLE,
            "running": self.file_observer is not None and self.file_observer.is_alive() if self.file_observer else False,
            "config_file": str(self.config_file),
            "watch_directory": str(self.config_dir)
        }
    
    def add_config_change_callback(self, callback: Callable):
        """添加配置变更回调"""
        if callback not in self.config_change_callbacks:
            self.config_change_callbacks.append(callback)
    
    def remove_config_change_callback(self, callback: Callable):
        """移除配置变更回调"""
        if callback in self.config_change_callbacks:
            self.config_change_callbacks.remove(callback)
    
    def _notify_config_changed(self):
        """通知配置变更"""
        for callback in self.config_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # 异步回调需要在事件循环中执行
                    asyncio.create_task(callback())
                else:
                    callback()
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {e}")
    
    # 任务CRUD操作
    
    def create_task(self, request: TaskCreateRequest) -> ScheduledTask:
        """创建新任务配置"""
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 获取默认配置
            default_config = get_default_task_config(request.task_type)
            
            # 合并用户配置
            merged_config = {**default_config, **request.config}
            
            # 验证配置
            if not validate_task_config(request.task_type, merged_config):
                raise ValueError(f"任务配置验证失败: {request.task_type}")
            
            # 创建任务对象
            task = ScheduledTask(
                id=task_id,
                name=request.name,
                description=request.description,
                task_type=request.task_type,
                cron_expression=request.cron_expression,
                config=merged_config,
                enabled=request.enabled,
                notification_level=request.notification_level,
                timeout_seconds=request.timeout_seconds,
                max_retries=request.max_retries,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 计算下次执行时间
            if task.enabled:
                task.next_run_time = task.calculate_next_run_time()
            
            # 保存任务
            self.tasks[task_id] = task
            self._save_config()
            
            logger.info(f"✅ 创建任务成功: {task.name} (ID: {task_id})")
            return task
            
        except Exception as e:
            logger.error(f"❌ 创建任务失败: {e}")
            raise
    
    def update_task(self, task_id: str, request: TaskUpdateRequest) -> Optional[ScheduledTask]:
        """更新任务配置"""
        try:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            
            # 更新字段
            if request.name is not None:
                task.name = request.name
            if request.description is not None:
                task.description = request.description
            if request.cron_expression is not None:
                task.cron_expression = request.cron_expression
            if request.config is not None:
                # 验证新配置
                if not validate_task_config(task.task_type, request.config):
                    raise ValueError(f"任务配置验证失败: {task.task_type}")
                task.config = request.config
            if request.enabled is not None:
                task.enabled = request.enabled
            if request.notification_level is not None:
                task.notification_level = request.notification_level
            if request.timeout_seconds is not None:
                task.timeout_seconds = request.timeout_seconds
            if request.max_retries is not None:
                task.max_retries = request.max_retries
            
            # 更新时间戳
            task.updated_at = datetime.now()
            
            # 重新计算下次执行时间
            if task.enabled:
                task.next_run_time = task.calculate_next_run_time()
            
            # 保存配置
            self._save_config()
            
            logger.info(f"✅ 更新任务成功: {task.name} (ID: {task_id})")
            return task
            
        except Exception as e:
            logger.error(f"❌ 更新任务失败: {e}")
            raise
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务配置"""
        try:
            if task_id not in self.tasks:
                return False
            
            task_name = self.tasks[task_id].name
            del self.tasks[task_id]
            
            # 删除执行历史
            if task_id in self.execution_history:
                del self.execution_history[task_id]
            
            # 保存配置
            self._save_config()
            
            logger.info(f"✅ 删除任务成功: {task_name} (ID: {task_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除任务失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取单个任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """获取任务列表"""
        tasks = list(self.tasks.values())
        if enabled_only:
            tasks = [task for task in tasks if task.enabled]
        return tasks
    
    def get_tasks_by_type(self, task_type: TaskType) -> List[ScheduledTask]:
        """根据类型获取任务列表"""
        return [task for task in self.tasks.values() if task.task_type == task_type]
    
    def get_due_tasks(self, current_time: Optional[datetime] = None) -> List[ScheduledTask]:
        """获取到期需要执行的任务"""
        if current_time is None:
            current_time = datetime.now()
        
        return [task for task in self.tasks.values() if task.is_due(current_time)]
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = len(self.tasks)
        enabled_tasks = len([task for task in self.tasks.values() if task.enabled])
        
        # 按类型统计
        type_stats = {}
        for task in self.tasks.values():
            task_type = task.task_type.value
            if task_type not in type_stats:
                type_stats[task_type] = {"total": 0, "enabled": 0}
            type_stats[task_type]["total"] += 1
            if task.enabled:
                type_stats[task_type]["enabled"] += 1
        
        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "disabled_tasks": total_tasks - enabled_tasks,
            "type_stats": type_stats,
            "config_file": str(self.config_file),
            "last_updated": max([task.updated_at for task in self.tasks.values()]) if self.tasks else None
        }
    
    # 执行历史管理
    
    def add_execution_record(self, execution: TaskExecution):
        """添加执行记录"""
        if execution.task_id not in self.execution_history:
            self.execution_history[execution.task_id] = []
        
        self.execution_history[execution.task_id].append(execution)
        
        # 保留最近100条记录
        if len(self.execution_history[execution.task_id]) > 100:
            self.execution_history[execution.task_id] = self.execution_history[execution.task_id][-100:]
        
        # 异步保存到文件
        asyncio.create_task(self._save_execution_history(execution.task_id, execution))
    
    def get_execution_history(self, task_id: str, limit: int = 50) -> List[TaskExecution]:
        """获取任务执行历史"""
        history = self.execution_history.get(task_id, [])
        return history[-limit:] if limit > 0 else history
    
    def get_latest_execution(self, task_id: str) -> Optional[TaskExecution]:
        """获取最新的执行记录"""
        history = self.execution_history.get(task_id, [])
        return history[-1] if history else None
    
    async def _save_execution_history(self, task_id: str, execution: TaskExecution):
        """保存执行历史到文件"""
        try:
            # 按月分组保存历史记录
            month_dir = self.history_dir / execution.started_at.strftime('%Y-%m')
            month_dir.mkdir(exist_ok=True)
            
            history_file = month_dir / f"{task_id}.json"
            
            # 加载现有历史
            history_data = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            
            # 添加新记录
            history_data.append(execution.model_dump(mode='json'))
            
            # 保存历史 (保留最近100条记录)
            history_data = history_data[-100:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"保存执行历史失败: {e}")
    
    # 配置验证和模板
    
    def validate_task_config(self, task_type: TaskType, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证任务配置"""
        errors = []
        
        try:
            # 基本验证
            if not validate_task_config(task_type, config):
                errors.append("任务配置基本验证失败")
            
            # 类型特定验证
            if task_type == TaskType.RESOURCE_ANALYSIS:
                if not config.get("prometheus_url") and not config.get("use_env_config", False):
                    errors.append("资源分析任务需要配置prometheus_url或启用use_env_config")
            
            elif task_type == TaskType.CLUSTER_CHECK:
                scope_config = config.get("scope", {})
                if "namespaces" in scope_config and not isinstance(scope_config["namespaces"], list):
                    errors.append("scope.namespaces必须是数组类型")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"配置验证异常: {str(e)}")
            return False, errors
    
    def get_task_template(self, task_type: TaskType) -> Dict[str, Any]:
        """获取任务配置模板"""
        return {
            "name": f"新{task_type.value}任务",
            "description": f"自动生成的{task_type.value}任务",
            "task_type": task_type.value,
            "cron_expression": "0 9 * * *",  # 每天上午9点
            "config": get_default_task_config(task_type),
            "enabled": False,
            "notification_level": "error_only",
            "timeout_seconds": 300,
            "max_retries": 3
        }
    
    # 清理和维护
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """清理旧备份文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for backup_file in self.backup_dir.glob("scheduled_tasks_*.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.debug(f"删除旧备份文件: {backup_file}")
                    
        except Exception as e:
            logger.error(f"清理旧备份文件失败: {e}")
    
    def cleanup_old_history(self, keep_months: int = 6):
        """清理旧执行历史"""
        try:
            cutoff_date = datetime.now().replace(day=1) - timedelta(days=keep_months * 30)
            cutoff_month = cutoff_date.strftime('%Y-%m')
            
            for month_dir in self.history_dir.iterdir():
                if month_dir.is_dir() and month_dir.name < cutoff_month:
                    shutil.rmtree(month_dir)
                    logger.debug(f"删除旧历史目录: {month_dir}")
                    
        except Exception as e:
            logger.error(f"清理旧执行历史失败: {e}")
    
    def __del__(self):
        """析构函数，确保文件监控被正确停止"""
        try:
            self.stop_file_watcher()
        except:
            pass


# 全局任务管理器实例
_task_manager_instance: Optional[TaskManager] = None


def get_task_manager() -> Optional[TaskManager]:
    """获取全局任务管理器实例"""
    return _task_manager_instance


def initialize_task_manager(config_file: Optional[str] = None) -> TaskManager:
    """初始化全局任务管理器"""
    global _task_manager_instance
    
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager(config_file)
    
    return _task_manager_instance


def cleanup_task_manager():
    """清理全局任务管理器"""
    global _task_manager_instance
    
    if _task_manager_instance:
        _task_manager_instance.stop_file_watcher()
        _task_manager_instance = None
