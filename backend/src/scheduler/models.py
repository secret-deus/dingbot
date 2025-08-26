"""
定时任务模块数据模型定义
基于现有项目的Pydantic使用模式，确保类型安全和数据验证
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from croniter import croniter


class TaskStatus(str, Enum):
    """任务执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """任务类型"""
    CLUSTER_CHECK = "cluster_check"
    RESOURCE_ANALYSIS = "resource_analysis"
    HEALTH_MONITOR = "health_monitor"
    CUSTOM = "custom"


class NotificationLevel(str, Enum):
    """通知级别"""
    NONE = "none"
    ERROR_ONLY = "error_only"
    ALL = "all"


class ScheduledTask(BaseModel):
    """定时任务配置模型"""
    id: str = Field(..., description="任务唯一标识符")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    
    # 调度配置
    cron_expression: str = Field(..., description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    enabled: bool = Field(default=True, description="是否启用")
    
    # 任务配置
    config: Dict[str, Any] = Field(default_factory=dict, description="任务特定配置")
    
    # 通知配置
    notification_level: NotificationLevel = Field(default=NotificationLevel.ERROR_ONLY, description="通知级别")
    notification_channels: List[str] = Field(default_factory=lambda: ["dingtalk"], description="通知渠道")
    
    # 执行配置
    timeout_seconds: int = Field(default=300, gt=0, le=3600, description="任务超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_delay_seconds: int = Field(default=60, ge=0, le=3600, description="重试延迟(秒)")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    created_by: Optional[str] = Field(default="system", description="创建者")
    
    # 运行时状态
    next_run_time: Optional[datetime] = Field(None, description="下次执行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次执行时间")
    last_execution_id: Optional[str] = Field(None, description="最后执行记录ID")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """验证任务ID格式"""
        if not v or not v.strip():
            raise ValueError("Task ID cannot be empty")
        # 确保ID只包含字母、数字、下划线和连字符
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Task ID can only contain letters, numbers, underscores and hyphens")
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        if len(v.strip()) > 100:
            raise ValueError("Task name cannot exceed 100 characters")
        return v.strip()
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v):
        """验证Cron表达式格式"""
        if not v or not v.strip():
            raise ValueError("Cron expression cannot be empty")
        
        try:
            # 使用croniter验证cron表达式
            croniter(v.strip())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        
        return v.strip()
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        """验证任务配置"""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Task config must be a dictionary")
        return v
    
    def calculate_next_run_time(self, base_time: Optional[datetime] = None) -> datetime:
        """计算下次执行时间"""
        if base_time is None:
            base_time = datetime.now()
        
        cron = croniter(self.cron_expression, base_time)
        return cron.get_next(datetime)
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """检查任务是否到期需要执行"""
        if not self.enabled or self.next_run_time is None:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        return current_time >= self.next_run_time


class TaskExecution(BaseModel):
    """任务执行记录模型"""
    id: str = Field(..., description="执行记录ID")
    task_id: str = Field(..., description="关联的任务ID")
    task_name: str = Field(..., description="任务名称快照")
    
    # 执行状态
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="执行状态")
    
    # 时间信息
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration_seconds: Optional[float] = Field(None, ge=0, description="执行耗时(秒)")
    
    # 执行结果
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 重试信息
    retry_count: int = Field(default=0, ge=0, description="重试次数")
    is_retry: bool = Field(default=False, description="是否为重试执行")
    parent_execution_id: Optional[str] = Field(None, description="父执行记录ID(重试时)")
    
    # 执行环境
    executor_info: Optional[Dict[str, Any]] = Field(None, description="执行器信息")
    
    # 通知状态
    notification_sent: bool = Field(default=False, description="是否已发送通知")
    notification_error: Optional[str] = Field(None, description="通知发送错误")
    
    @field_validator('id', 'task_id')
    @classmethod
    def validate_ids(cls, v):
        """验证ID格式"""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()
    
    def calculate_duration(self):
        """计算执行耗时"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()
    
    def mark_completed(self, success: bool = True, result: Optional[Dict[str, Any]] = None, 
                      error_message: Optional[str] = None):
        """标记执行完成"""
        self.completed_at = datetime.now()
        self.status = TaskStatus.SUCCESS if success else TaskStatus.FAILED
        if result:
            self.result = result
        if error_message:
            self.error_message = error_message
        self.calculate_duration()


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    cron_expression: str = Field(..., description="Cron表达式")
    config: Dict[str, Any] = Field(default_factory=dict, description="任务配置")
    enabled: bool = Field(default=True, description="是否启用")
    notification_level: NotificationLevel = Field(default=NotificationLevel.ERROR_ONLY, description="通知级别")
    timeout_seconds: int = Field(default=300, gt=0, le=3600, description="超时时间")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        if len(v.strip()) > 100:
            raise ValueError("Task name cannot exceed 100 characters")
        return v.strip()
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v):
        """验证Cron表达式"""
        if not v or not v.strip():
            raise ValueError("Cron expression cannot be empty")
        
        try:
            croniter(v.strip())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        
        return v.strip()


class TaskUpdateRequest(BaseModel):
    """更新任务请求模型"""
    name: Optional[str] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_level: Optional[NotificationLevel] = Field(None, description="通知级别")
    timeout_seconds: Optional[int] = Field(None, gt=0, le=3600, description="超时时间")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Task name cannot be empty")
            if len(v.strip()) > 100:
                raise ValueError("Task name cannot exceed 100 characters")
            return v.strip()
        return v
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v):
        """验证Cron表达式"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Cron expression cannot be empty")
            
            try:
                croniter(v.strip())
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
            
            return v.strip()
        return v


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[ScheduledTask] = Field(..., description="任务列表")
    total: int = Field(..., description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    has_more: bool = Field(default=False, description="是否有更多数据")


class TaskExecutionListResponse(BaseModel):
    """任务执行历史列表响应模型"""
    executions: List[TaskExecution] = Field(..., description="执行记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    has_more: bool = Field(default=False, description="是否有更多数据")


class TaskStatsResponse(BaseModel):
    """任务统计响应模型"""
    total_tasks: int = Field(default=0, description="总任务数")
    enabled_tasks: int = Field(default=0, description="启用任务数")
    running_tasks: int = Field(default=0, description="运行中任务数")
    total_executions: int = Field(default=0, description="总执行次数")
    success_executions: int = Field(default=0, description="成功执行次数")
    failed_executions: int = Field(default=0, description="失败执行次数")
    success_rate: float = Field(default=0.0, description="成功率")
    average_duration: float = Field(default=0.0, description="平均执行时间")


class CronValidationRequest(BaseModel):
    """Cron表达式验证请求"""
    expression: str = Field(..., description="Cron表达式")
    
    @field_validator('expression')
    @classmethod
    def validate_expression(cls, v):
        """验证Cron表达式"""
        if not v or not v.strip():
            raise ValueError("Cron expression cannot be empty")
        
        try:
            croniter(v.strip())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        
        return v.strip()


class CronValidationResponse(BaseModel):
    """Cron表达式验证响应"""
    valid: bool = Field(..., description="是否有效")
    error_message: Optional[str] = Field(None, description="错误信息")
    next_runs: List[datetime] = Field(default_factory=list, description="接下来的执行时间")
    description: Optional[str] = Field(None, description="表达式描述")


class TaskRunRequest(BaseModel):
    """手动执行任务请求"""
    force: bool = Field(default=False, description="是否强制执行(忽略enabled状态)")
    config_override: Optional[Dict[str, Any]] = Field(None, description="临时配置覆盖")


class TaskRunResponse(BaseModel):
    """手动执行任务响应"""
    execution_id: str = Field(..., description="执行记录ID")
    message: str = Field(..., description="执行消息")
    started_at: datetime = Field(..., description="开始时间")


# 预定义的任务配置模板
DEFAULT_TASK_CONFIGS = {
    TaskType.CLUSTER_CHECK: {
        "scope": {
            "namespaces": ["default", "kube-system"],
            "include_events": True,
            "include_metrics": True
        },
        "analysis": {
            "check_resource_usage": True,
            "check_pod_status": True,
            "check_node_status": True,
            "generate_summary": True
        }
    },
    TaskType.RESOURCE_ANALYSIS: {
        "prometheus_url": "",
        "days": 14,
        "cpu_threshold": 60.0,
        "memory_threshold": 60.0,
        "analysis_mode": "deployment",
        "namespace_filter": ""
    },
    TaskType.HEALTH_MONITOR: {
        "check_services": True,
        "check_deployments": True,
        "check_pods": True,
        "alert_threshold": 0.8,
        "include_logs": False
    }
}


def get_default_task_config(task_type: TaskType) -> Dict[str, Any]:
    """获取任务类型的默认配置"""
    return DEFAULT_TASK_CONFIGS.get(task_type, {}).copy()


def validate_task_config(task_type: TaskType, config: Dict[str, Any]) -> bool:
    """验证任务配置的有效性"""
    try:
        default_config = get_default_task_config(task_type)
        
        # 基本验证：检查必需的配置项
        if task_type == TaskType.RESOURCE_ANALYSIS:
            # Prometheus资源分析需要URL配置
            if not config.get("prometheus_url") and not config.get("use_env_config", False):
                return False
        
        return True
    except Exception:
        return False


# 常用的Cron表达式模板
CRON_TEMPLATES = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "every_hour": "0 * * * *",
    "every_2_hours": "0 */2 * * *",
    "every_6_hours": "0 */6 * * *",
    "every_12_hours": "0 */12 * * *",
    "daily_at_midnight": "0 0 * * *",
    "daily_at_6am": "0 6 * * *",
    "daily_at_9am": "0 9 * * *",
    "daily_at_6pm": "0 18 * * *",
    "weekly_monday_9am": "0 9 * * 1",
    "monthly_first_day": "0 0 1 * *"
}


def get_cron_template(template_name: str) -> Optional[str]:
    """获取Cron表达式模板"""
    return CRON_TEMPLATES.get(template_name)


def get_cron_description(cron_expression: str) -> str:
    """获取Cron表达式的人类可读描述"""
    try:
        # 这里可以集成cron-descriptor库来生成描述
        # 暂时返回简单的描述
        parts = cron_expression.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            
            if cron_expression == "* * * * *":
                return "每分钟执行"
            elif cron_expression == "0 * * * *":
                return "每小时执行"
            elif cron_expression == "0 0 * * *":
                return "每天午夜执行"
            elif cron_expression == "0 9 * * *":
                return "每天上午9点执行"
            elif cron_expression == "0 9 * * 1":
                return "每周一上午9点执行"
            elif cron_expression == "0 0 1 * *":
                return "每月1号午夜执行"
        
        return f"按表达式 '{cron_expression}' 执行"
    except Exception:
        return f"按表达式 '{cron_expression}' 执行"
