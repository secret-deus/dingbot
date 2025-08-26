"""
任务管理API端点
提供定时任务的增删改查、执行历史查询等功能
遵循现有API的设计模式和错误处理方式
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from loguru import logger

from ....scheduler import (
    # 模型
    ScheduledTask, TaskExecution, TaskStatus, TaskType, NotificationLevel,
    TaskCreateRequest, TaskUpdateRequest, TaskListResponse, TaskExecutionListResponse,
    TaskStatsResponse, TaskRunRequest, TaskRunResponse,
    
    # 管理器
    TaskManager, get_task_manager, initialize_task_manager,
    
    # 执行器
    TaskExecutor, get_task_executor,
    
    # 调度器
    get_scheduler,
    
    # 工具函数
    get_default_task_config, validate_task_config, get_cron_template, get_cron_description,
    CRON_TEMPLATES
)

router = APIRouter(prefix="/scheduler", tags=["定时任务"])

# 依赖注入
def get_task_manager_instance() -> TaskManager:
    """获取任务管理器实例"""
    task_manager = get_task_manager()
    if not task_manager:
        task_manager = initialize_task_manager()
    return task_manager

def get_task_executor_instance() -> Optional[TaskExecutor]:
    """获取任务执行器实例"""
    return get_task_executor()

# 响应模型
class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str
    name: str
    description: Optional[str]
    task_type: str
    cron_expression: str
    enabled: bool
    notification_level: str
    timeout_seconds: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    last_execution_id: Optional[str]

class TaskExecutionResponse(BaseModel):
    """任务执行记录响应模型"""
    id: str
    task_id: str
    task_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    retry_count: int
    is_retry: bool
    notification_sent: bool

class CronValidationRequest(BaseModel):
    """Cron表达式验证请求"""
    expression: str = Field(..., description="Cron表达式")

class CronValidationResponse(BaseModel):
    """Cron表达式验证响应"""
    valid: bool
    error_message: Optional[str]
    next_runs: List[datetime]
    description: str

# API端点

@router.get("/tasks", response_model=TaskListResponse, summary="获取任务列表")
async def get_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    enabled_only: bool = Query(False, description="只返回启用的任务"),
    task_type: Optional[TaskType] = Query(None, description="按任务类型过滤"),
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """获取任务列表，支持分页和过滤"""
    try:
        # 获取所有任务
        all_tasks = task_manager.list_tasks(enabled_only=enabled_only)
        
        # 按类型过滤
        if task_type:
            all_tasks = [task for task in all_tasks if task.task_type == task_type]
        
        # 分页
        total = len(all_tasks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        tasks = all_tasks[start_idx:end_idx]
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            has_more=end_idx < total
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/tasks", response_model=TaskResponse, summary="创建新任务")
async def create_task(
    request: TaskCreateRequest,
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """创建新的定时任务"""
    try:
        # 创建任务
        task = task_manager.create_task(request)
        
        logger.info(f"创建任务成功: {task.name} (ID: {task.id})")
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            cron_expression=task.cron_expression,
            enabled=task.enabled,
            notification_level=task.notification_level.value,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            created_at=task.created_at,
            updated_at=task.updated_at,
            next_run_time=task.next_run_time,
            last_run_time=task.last_run_time,
            last_execution_id=task.last_execution_id
        )
        
    except ValueError as e:
        logger.error(f"创建任务参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="获取单个任务")
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """根据ID获取单个任务详情"""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            cron_expression=task.cron_expression,
            enabled=task.enabled,
            notification_level=task.notification_level.value,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            created_at=task.created_at,
            updated_at=task.updated_at,
            next_run_time=task.next_run_time,
            last_run_time=task.last_run_time,
            last_execution_id=task.last_execution_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

@router.put("/tasks/{task_id}", response_model=TaskResponse, summary="更新任务")
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """更新指定任务的配置"""
    try:
        task = task_manager.update_task(task_id, request)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"更新任务成功: {task.name} (ID: {task_id})")
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            cron_expression=task.cron_expression,
            enabled=task.enabled,
            notification_level=task.notification_level.value,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            created_at=task.created_at,
            updated_at=task.updated_at,
            next_run_time=task.next_run_time,
            last_run_time=task.last_run_time,
            last_execution_id=task.last_execution_id
        )
        
    except ValueError as e:
        logger.error(f"更新任务参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")

@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """删除指定的任务"""
    try:
        success = task_manager.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        logger.info(f"删除任务成功: {task_id}")
        
        return {
            "success": True,
            "message": "任务删除成功",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.get("/tasks/{task_id}/executions", response_model=TaskExecutionListResponse, summary="获取任务执行历史")
async def get_task_executions(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """获取指定任务的执行历史记录"""
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取执行历史
        all_executions = task_manager.get_execution_history(task_id, limit=0)  # 获取所有记录
        
        # 分页
        total = len(all_executions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        executions = all_executions[start_idx:end_idx]
        
        # 转换为响应模型
        execution_responses = []
        for execution in executions:
            execution_responses.append(TaskExecutionResponse(
                id=execution.id,
                task_id=execution.task_id,
                task_name=execution.task_name,
                status=execution.status.value,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                duration_seconds=execution.duration_seconds,
                retry_count=execution.retry_count,
                is_retry=execution.is_retry,
                notification_sent=execution.notification_sent
            ))
        
        return TaskExecutionListResponse(
            executions=executions,  # 使用原始的TaskExecution对象列表
            total=total,
            page=page,
            page_size=page_size,
            has_more=end_idx < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")

@router.post("/tasks/{task_id}/run", response_model=TaskRunResponse, summary="手动执行任务")
async def run_task(
    task_id: str,
    request: TaskRunRequest = TaskRunRequest(),
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """手动触发任务执行"""
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取调度器
        scheduler = get_scheduler()
        if not scheduler:
            raise HTTPException(status_code=503, detail="任务调度器未启动")
        
        # 手动执行任务
        execution_id = await scheduler.run_task_manually(task_id, force=request.force)
        if not execution_id:
            raise HTTPException(status_code=400, detail="任务执行失败")
        
        logger.info(f"手动执行任务: {task.name} (ID: {task_id})")
        
        return TaskRunResponse(
            execution_id=execution_id,
            message=f"任务 '{task.name}' 已开始执行",
            started_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动执行任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"手动执行任务失败: {str(e)}")

@router.get("/stats", response_model=TaskStatsResponse, summary="获取任务统计信息")
async def get_task_stats(
    task_manager: TaskManager = Depends(get_task_manager_instance),
    task_executor: Optional[TaskExecutor] = Depends(get_task_executor_instance)
):
    """获取任务统计信息"""
    try:
        # 获取任务统计
        task_stats = task_manager.get_task_stats()
        
        # 获取执行统计
        execution_stats = {}
        if task_executor:
            execution_stats = task_executor.get_execution_stats()
        
        return TaskStatsResponse(
            total_tasks=task_stats.get("total_tasks", 0),
            enabled_tasks=task_stats.get("enabled_tasks", 0),
            running_tasks=len(get_scheduler().get_running_tasks()) if get_scheduler() else 0,
            total_executions=execution_stats.get("total_executions", 0),
            success_executions=execution_stats.get("successful_executions", 0),
            failed_executions=execution_stats.get("failed_executions", 0),
            success_rate=execution_stats.get("success_rate", 0.0),
            average_duration=execution_stats.get("average_execution_time", 0.0)
        )
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务统计失败: {str(e)}")

@router.get("/running", summary="获取正在运行的任务")
async def get_running_tasks():
    """获取当前正在运行的任务列表"""
    try:
        scheduler = get_scheduler()
        if not scheduler:
            return {
                "success": True,
                "running_tasks": {},
                "count": 0,
                "message": "任务调度器未启动"
            }
        
        running_tasks = scheduler.get_running_tasks()
        
        return {
            "success": True,
            "running_tasks": running_tasks,
            "count": len(running_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取运行中任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取运行中任务失败: {str(e)}")

# 工具和配置相关端点

@router.get("/task-types", summary="获取支持的任务类型")
async def get_task_types():
    """获取所有支持的任务类型及其配置模板"""
    try:
        task_types = []
        
        for task_type in TaskType:
            default_config = get_default_task_config(task_type)
            
            task_types.append({
                "type": task_type.value,
                "name": {
                    "cluster_check": "集群巡检",
                    "resource_analysis": "资源分析",
                    "health_monitor": "健康监控",
                    "custom": "自定义任务"
                }.get(task_type.value, task_type.value),
                "description": {
                    "cluster_check": "定期执行Kubernetes集群巡检，生成运维报告",
                    "resource_analysis": "分析集群资源利用率，提供优化建议",
                    "health_monitor": "监控集群健康状态，及时发现问题",
                    "custom": "自定义任务，支持多个MCP工具调用"
                }.get(task_type.value, ""),
                "default_config": default_config
            })
        
        return {
            "success": True,
            "task_types": task_types,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取任务类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务类型失败: {str(e)}")

@router.get("/cron-templates", summary="获取Cron表达式模板")
async def get_cron_templates():
    """获取常用的Cron表达式模板"""
    try:
        templates = []
        
        for template_name, expression in CRON_TEMPLATES.items():
            templates.append({
                "name": template_name,
                "expression": expression,
                "description": get_cron_description(expression)
            })
        
        return {
            "success": True,
            "templates": templates,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取Cron模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Cron模板失败: {str(e)}")

@router.post("/validate-cron", response_model=CronValidationResponse, summary="验证Cron表达式")
async def validate_cron(request: CronValidationRequest):
    """验证Cron表达式的有效性并预览执行时间"""
    try:
        from croniter import croniter
        from datetime import datetime, timedelta
        
        expression = request.expression.strip()
        
        # 验证表达式
        try:
            cron = croniter(expression, datetime.now())
            valid = True
            error_message = None
            
            # 生成接下来的5次执行时间
            next_runs = []
            for _ in range(5):
                next_run = cron.get_next(datetime)
                next_runs.append(next_run)
            
            # 生成描述
            description = get_cron_description(expression)
            
        except Exception as e:
            valid = False
            error_message = str(e)
            next_runs = []
            description = "无效的Cron表达式"
        
        return CronValidationResponse(
            valid=valid,
            error_message=error_message,
            next_runs=next_runs,
            description=description
        )
        
    except Exception as e:
        logger.error(f"验证Cron表达式失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证Cron表达式失败: {str(e)}")

@router.get("/config/validate/{task_type}", summary="验证任务配置")
async def validate_task_config_endpoint(
    task_type: TaskType,
    config: Dict[str, Any],
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """验证指定任务类型的配置是否有效"""
    try:
        valid, errors = task_manager.validate_task_config(task_type, config)
        
        return {
            "success": True,
            "valid": valid,
            "errors": errors,
            "task_type": task_type.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"验证任务配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证任务配置失败: {str(e)}")

@router.get("/config/template/{task_type}", summary="获取任务配置模板")
async def get_task_config_template(
    task_type: TaskType,
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """获取指定任务类型的配置模板"""
    try:
        template = task_manager.get_task_template(task_type)
        
        return {
            "success": True,
            "template": template,
            "task_type": task_type.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取任务模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务模板失败: {str(e)}")

# 系统管理端点

@router.get("/status", summary="获取调度器状态")
async def get_scheduler_status():
    """获取任务调度器的运行状态"""
    try:
        scheduler = get_scheduler()
        task_manager = get_task_manager()
        task_executor = get_task_executor()
        
        return {
            "success": True,
            "scheduler": {
                "running": scheduler is not None and scheduler.is_running if scheduler else False,
                "running_tasks_count": len(scheduler.get_running_tasks()) if scheduler else 0
            },
            "task_manager": {
                "initialized": task_manager is not None,
                "file_watcher": task_manager.get_file_watcher_status() if task_manager else None
            },
            "task_executor": {
                "initialized": task_executor is not None,
                "stats": task_executor.get_execution_stats() if task_executor else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")

@router.post("/maintenance/cleanup", summary="清理旧数据")
async def cleanup_old_data(
    keep_days: int = Query(30, ge=1, le=365, description="保留天数"),
    task_manager: TaskManager = Depends(get_task_manager_instance)
):
    """清理旧的备份文件和执行历史"""
    try:
        # 清理旧备份
        task_manager.cleanup_old_backups(keep_days=keep_days)
        
        # 清理旧历史
        keep_months = max(1, keep_days // 30)
        task_manager.cleanup_old_history(keep_months=keep_months)
        
        logger.info(f"数据清理完成，保留 {keep_days} 天的数据")
        
        return {
            "success": True,
            "message": f"数据清理完成，保留 {keep_days} 天的数据",
            "keep_days": keep_days,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据清理失败: {str(e)}")

@router.post("/maintenance/reset-stats", summary="重置执行统计")
async def reset_execution_stats(
    task_executor: Optional[TaskExecutor] = Depends(get_task_executor_instance)
):
    """重置任务执行统计信息"""
    try:
        if not task_executor:
            raise HTTPException(status_code=503, detail="任务执行器未初始化")
        
        task_executor.reset_stats()
        
        logger.info("执行统计已重置")
        
        return {
            "success": True,
            "message": "执行统计已重置",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置统计失败: {str(e)}")
