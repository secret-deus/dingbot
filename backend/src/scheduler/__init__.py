"""
定时任务调度模块

该模块提供完整的定时任务调度功能，包括：
- 任务配置管理
- 任务调度执行
- 执行历史记录
- 通知系统集成

基于现有的钉钉K8s运维机器人架构，复用MCP客户端和LLM处理器。
"""

from .models import (
    # 枚举类型
    TaskStatus,
    TaskType,
    NotificationLevel,
    
    # 核心模型
    ScheduledTask,
    TaskExecution,
    
    # API请求/响应模型
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskListResponse,
    TaskExecutionListResponse,
    TaskStatsResponse,
    TaskRunRequest,
    TaskRunResponse,
    
    # 工具函数
    get_default_task_config,
    validate_task_config,
    get_cron_template,
    get_cron_description,
    
    # 常量
    DEFAULT_TASK_CONFIGS,
    CRON_TEMPLATES
)

from .task_manager import (
    # 任务管理器
    TaskManager,
    
    # 全局实例管理
    get_task_manager,
    initialize_task_manager,
    cleanup_task_manager
)

from .task_executor import (
    # 任务执行器
    TaskExecutor,
    
    # 全局实例管理
    get_task_executor,
    initialize_task_executor,
    cleanup_task_executor
)

from .task_scheduler import (
    # 任务调度器
    EnhancedTaskScheduler,
    
    # 全局实例管理
    get_scheduler,
    initialize_scheduler,
    cleanup_scheduler
)

__all__ = [
    # 枚举类型
    "TaskStatus",
    "TaskType", 
    "NotificationLevel",
    
    # 核心模型
    "ScheduledTask",
    "TaskExecution",
    
    # API模型
    "TaskCreateRequest",
    "TaskUpdateRequest", 
    "TaskListResponse",
    "TaskExecutionListResponse",
    "TaskStatsResponse",
    "TaskRunRequest",
    "TaskRunResponse",
    
    # 工具函数
    "get_default_task_config",
    "validate_task_config",
    "get_cron_template",
    "get_cron_description",
    
    # 常量
    "DEFAULT_TASK_CONFIGS",
    "CRON_TEMPLATES",
    
    # 任务管理器
    "TaskManager",
    "get_task_manager",
    "initialize_task_manager",
    "cleanup_task_manager",
    
    # 任务执行器
    "TaskExecutor",
    "get_task_executor",
    "initialize_task_executor",
    "cleanup_task_executor",
    
    # 任务调度器
    "EnhancedTaskScheduler",
    "get_scheduler",
    "initialize_scheduler",
    "cleanup_scheduler"
]
