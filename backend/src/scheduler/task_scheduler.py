"""
增强任务调度器核心实现
基于现有的_periodic_inspection_task扩展，支持多任务类型的调度
复用现有的asyncio模式，避免引入APScheduler等新依赖
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from loguru import logger

from .models import (
    ScheduledTask, TaskExecution, TaskStatus, TaskType,
    get_default_task_config, validate_task_config
)
from .task_manager import TaskManager, get_task_manager, initialize_task_manager
from .task_executor import TaskExecutor, get_task_executor, initialize_task_executor


class EnhancedTaskScheduler:
    """
    增强任务调度器
    基于现有的asyncio定时巡检逻辑扩展，支持多任务类型调度
    """
    
    def __init__(self, task_manager: Optional[TaskManager] = None, task_executor: Optional[TaskExecutor] = None):
        """
        初始化任务调度器
        
        Args:
            task_manager: 任务管理器实例，如果为None则使用全局实例
            task_executor: 任务执行器实例，如果为None则使用全局实例
        """
        self.task_manager = task_manager or get_task_manager()
        if self.task_manager is None:
            raise RuntimeError("TaskManager未初始化，请先调用initialize_task_manager()")
        
        self.task_executor = task_executor or get_task_executor()
        if self.task_executor is None:
            raise RuntimeError("TaskExecutor未初始化，请先调用initialize_task_executor()")
        
        # 运行时状态
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 调度器状态
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.check_interval = 60  # 每分钟检查一次，与现有逻辑保持一致
        
        # 并发控制
        self.max_concurrent_tasks = 5
        self.task_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        logger.info(f"✅ EnhancedTaskScheduler初始化完成")
    
    async def start(self):
        """启动任务调度器"""
        if self.is_running:
            logger.warning("任务调度器已在运行中")
            return
        
        try:
            # 启动主调度循环 (复用现有的asyncio.create_task模式)
            self.is_running = True
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            logger.info("⏰ 增强任务调度器已启动")
            
        except Exception as e:
            logger.error(f"❌ 任务调度器启动失败: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """停止任务调度器"""
        if not self.is_running:
            return
        
        logger.info("🛑 正在停止任务调度器...")
        
        self.is_running = False
        
        # 取消主调度任务
        if self.scheduler_task and not self.scheduler_task.done():
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 等待正在运行的任务完成或取消
        if self.running_tasks:
            logger.info(f"等待 {len(self.running_tasks)} 个运行中的任务...")
            for task_id, task in list(self.running_tasks.items()):
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            self.running_tasks.clear()
        
        logger.info("✅ 任务调度器已停止")
    
    async def _scheduler_loop(self):
        """
        主调度循环
        基于现有的_periodic_inspection_task模式实现
        """
        logger.info("🔄 任务调度循环已启动")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查需要执行的任务
                due_tasks = self.task_manager.get_due_tasks(current_time)
                
                # 执行到期任务
                if due_tasks:
                    logger.info(f"⏳ 发现 {len(due_tasks)} 个到期任务")
                    for task in due_tasks:
                        if task.id not in self.running_tasks:
                            # 创建任务执行协程 (复用现有模式)
                            task_coroutine = self._execute_task_with_semaphore(task)
                            execution_task = asyncio.create_task(task_coroutine)
                            self.running_tasks[task.id] = execution_task
                        else:
                            logger.warning(f"任务 {task.name} 仍在运行中，跳过本次执行")
                
                # 清理已完成的任务
                completed_task_ids = []
                for task_id, execution_task in self.running_tasks.items():
                    if execution_task.done():
                        completed_task_ids.append(task_id)
                
                for task_id in completed_task_ids:
                    del self.running_tasks[task_id]
                
                # 每分钟检查一次 (与现有逻辑保持一致)
                await asyncio.sleep(max(60, self.check_interval))
                
            except Exception as e:
                logger.error(f"❌ 调度循环错误: {e}")
                # 出错后等待一段时间再继续，避免快速失败循环
                await asyncio.sleep(60)
    
    async def _execute_task_with_semaphore(self, task: ScheduledTask):
        """
        使用信号量控制并发执行任务
        """
        async with self.task_semaphore:
            await self._execute_single_task(task)
    
    async def _execute_single_task(self, task: ScheduledTask):
        """
        执行单个任务
        基于现有的perform_inspection逻辑模式
        """
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            id=execution_id,
            task_id=task.id,
            task_name=task.name,
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # 记录执行开始
        self.task_manager.add_execution_record(execution)
        
        logger.info(f"🚀 开始执行任务: {task.name} (ID: {task.id})")
        
        try:
            # 使用TaskExecutor执行任务
            result = await self.task_executor.execute_task(task, execution)
            
            # 标记执行成功
            execution.mark_completed(success=True, result=result)
            
            # 更新任务的下次执行时间
            task.last_run_time = execution.started_at
            task.next_run_time = task.calculate_next_run_time(execution.completed_at)
            task.last_execution_id = execution_id
            
            logger.info(f"✅ 任务执行成功: {task.name}, 耗时: {execution.duration_seconds:.2f}秒")
            
            # 发送成功通知 (如果配置了)
            await self._send_notification(task, execution, success=True)
            
        except Exception as e:
            # 标记执行失败
            execution.mark_completed(success=False, error_message=str(e))
            
            logger.error(f"❌ 任务执行失败: {task.name}, 错误: {e}")
            
            # 处理重试逻辑
            if execution.retry_count < task.max_retries:
                await self._schedule_retry(task, execution)
            else:
                # 更新任务状态
                task.last_run_time = execution.started_at
                task.next_run_time = task.calculate_next_run_time(execution.completed_at)
                task.last_execution_id = execution_id
                
                # 发送失败通知
                await self._send_notification(task, execution, success=False)
        
        finally:
            # 执行历史已通过task_manager保存
            pass
    

    
    async def _schedule_retry(self, task: ScheduledTask, failed_execution: TaskExecution):
        """
        安排任务重试
        """
        retry_delay = task.retry_delay_seconds
        retry_count = failed_execution.retry_count + 1
        
        logger.info(f"⏳ 安排任务重试: {task.name}, 第{retry_count}次重试, {retry_delay}秒后执行")
        
        # 创建重试任务
        async def retry_task():
            await asyncio.sleep(retry_delay)
            
            # 创建新的执行记录
            retry_execution = TaskExecution(
                id=str(uuid.uuid4()),
                task_id=task.id,
                task_name=task.name,
                status=TaskStatus.RUNNING,
                started_at=datetime.now(),
                retry_count=retry_count,
                is_retry=True,
                parent_execution_id=failed_execution.id
            )
            
            # 执行重试
            await self._execute_single_task_retry(task, retry_execution)
        
        # 启动重试任务
        asyncio.create_task(retry_task())
    
    async def _execute_single_task_retry(self, task: ScheduledTask, execution: TaskExecution):
        """
        执行单个任务的重试逻辑
        """
        # 记录重试执行
        self.task_manager.add_execution_record(execution)
        
        try:
            # 使用TaskExecutor执行任务
            result = await self.task_executor.execute_task(task, execution)
            
            # 标记重试成功
            execution.mark_completed(success=True, result=result)
            
            logger.info(f"✅ 任务重试成功: {task.name}, 第{execution.retry_count}次重试")
            
            # 发送成功通知
            await self._send_notification(task, execution, success=True)
            
        except Exception as e:
            # 标记重试失败
            execution.mark_completed(success=False, error_message=str(e))
            
            logger.error(f"❌ 任务重试失败: {task.name}, 第{execution.retry_count}次重试, 错误: {e}")
            
            # 如果还有重试次数，继续重试
            if execution.retry_count < task.max_retries:
                await self._schedule_retry(task, execution)
            else:
                # 所有重试都失败，发送失败通知
                await self._send_notification(task, execution, success=False)
        
        finally:
            # 执行历史已通过task_manager保存
            pass
    
    async def _send_notification(self, task: ScheduledTask, execution: TaskExecution, success: bool):
        """
        发送任务执行通知
        复用现有的钉钉机器人
        """
        try:
            from main import dingtalk_bot
            
            # 检查通知级别
            if task.notification_level.value == "none":
                return
            
            if task.notification_level.value == "error_only" and success:
                return
            
            # 检查钉钉机器人是否可用
            if not dingtalk_bot or not getattr(dingtalk_bot, "webhook_url", None):
                logger.warning("钉钉机器人未配置，跳过通知发送")
                return
            
            # 构建通知消息
            status_emoji = "✅" if success else "❌"
            status_text = "成功" if success else "失败"
            
            title = f"定时任务{status_text}通知"
            
            markdown_lines = [
                f"# {status_emoji} 定时任务执行{status_text}",
                "",
                f"**任务名称**: {task.name}",
                f"**任务类型**: {task.task_type.value}",
                f"**执行时间**: {execution.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            
            if execution.duration_seconds:
                markdown_lines.append(f"**执行耗时**: {execution.duration_seconds:.2f}秒")
            
            if execution.retry_count > 0:
                markdown_lines.append(f"**重试次数**: {execution.retry_count}")
            
            if not success and execution.error_message:
                markdown_lines.extend([
                    "",
                    "**错误信息**:",
                    f"```",
                    execution.error_message[:500],  # 限制错误信息长度
                    f"```"
                ])
            
            if success and execution.result:
                # 添加详细结果信息
                result_type = execution.result.get("type", "unknown")
                result_summary = execution.result.get("summary", "")
                
                markdown_lines.extend([
                    "",
                    f"**执行结果**: {result_type}任务执行完成"
                ])
                
                # 添加结果摘要
                if result_summary:
                    markdown_lines.extend([
                        "",
                        f"**结果摘要**: {result_summary}"
                    ])
                
                # 根据任务类型添加特定信息
                if result_type == "cluster_check" and execution.result.get("analysis_id"):
                    markdown_lines.extend([
                        "",
                        f"**分析ID**: {execution.result.get('analysis_id')}"
                    ])
                elif result_type == "resource_analysis" and execution.result.get("parameters"):
                    params = execution.result.get("parameters", {})
                    markdown_lines.extend([
                        "",
                        f"**分析参数**: CPU阈值 {params.get('cpu_threshold', 'N/A')}%, 内存阈值 {params.get('memory_threshold', 'N/A')}%"
                    ])
                elif result_type == "health_monitor" and execution.result.get("health_issues"):
                    issues_count = len(execution.result.get("health_issues", []))
                    markdown_lines.extend([
                        "",
                        f"**健康检查**: 发现 {issues_count} 个问题"
                    ])
            
            markdown_text = "\n".join(markdown_lines)
            
            # 发送通知
            sent_ok = await dingtalk_bot.send_markdown_message(
                dingtalk_bot.webhook_url,
                title=title,
                markdown_text=markdown_text
            )
            
            execution.notification_sent = bool(sent_ok)
            
            if sent_ok:
                logger.info(f"📢 任务通知发送成功: {task.name}")
            else:
                logger.warning(f"📢 任务通知发送失败: {task.name}")
                
        except Exception as e:
            logger.error(f"发送任务通知失败: {e}")
            execution.notification_error = str(e)
    
    # 任务管理方法（委托给TaskManager）
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.task_manager.get_task(task_id)
    
    def list_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        return self.task_manager.list_tasks()
    
    def get_running_tasks(self) -> Dict[str, str]:
        """获取正在运行的任务"""
        tasks = {task_id: self.task_manager.get_task(task_id).name 
                for task_id in self.running_tasks.keys()}
        return {k: v for k, v in tasks.items() if v is not None}
    
    async def run_task_manually(self, task_id: str, force: bool = False) -> Optional[str]:
        """手动执行任务"""
        try:
            task = self.task_manager.get_task(task_id)
            if not task:
                return None
            
            if not task.enabled and not force:
                raise ValueError("任务未启用，使用force=True强制执行")
            
            if task_id in self.running_tasks:
                raise ValueError("任务正在运行中")
            
            # 创建执行任务
            execution_coroutine = self._execute_task_with_semaphore(task)
            execution_task = asyncio.create_task(execution_coroutine)
            self.running_tasks[task_id] = execution_task
            
            # 生成执行ID
            execution_id = str(uuid.uuid4())
            
            logger.info(f"🚀 手动执行任务: {task.name}")
            return execution_id
            
        except Exception as e:
            logger.error(f"手动执行任务失败: {e}")
            raise


# 全局调度器实例
_scheduler_instance: Optional[EnhancedTaskScheduler] = None


def get_scheduler() -> Optional[EnhancedTaskScheduler]:
    """获取全局调度器实例"""
    return _scheduler_instance


async def initialize_scheduler() -> EnhancedTaskScheduler:
    """初始化全局调度器"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        # 确保TaskManager已初始化
        task_manager = get_task_manager()
        if task_manager is None:
            task_manager = initialize_task_manager()
        
        # 确保TaskExecutor已初始化
        task_executor = get_task_executor()
        if task_executor is None:
            # 从全局变量获取MCP客户端和LLM处理器
            import main
            mcp_client = getattr(main, 'mcp_client', None)
            llm_processor = getattr(main, 'llm_processor', None)
            
            if not mcp_client or not llm_processor:
                raise RuntimeError("MCP客户端或LLM处理器未初始化")
            
            task_executor = initialize_task_executor(mcp_client, llm_processor)
        
        _scheduler_instance = EnhancedTaskScheduler(task_manager, task_executor)
        await _scheduler_instance.start()
    
    return _scheduler_instance


async def cleanup_scheduler():
    """清理全局调度器"""
    global _scheduler_instance
    
    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None
    
    # 清理TaskExecutor
    from .task_executor import cleanup_task_executor
    cleanup_task_executor()
