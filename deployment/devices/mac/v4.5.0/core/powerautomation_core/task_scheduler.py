"""
TaskScheduler - 任务调度器
支持定时任务、事件触发任务和依赖任务的调度
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import heapq
import crontab

class TaskType(Enum):
    """任务类型"""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    EVENT_TRIGGERED = "event_triggered"
    DEPENDENCY = "dependency"

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

@dataclass
class TaskDefinition:
    """任务定义"""
    id: str
    name: str
    type: TaskType
    action: Dict[str, Any]  # 要执行的动作
    schedule: Optional[str] = None  # cron表达式或时间
    dependencies: List[str] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 60
    priority: int = 5  # 1-10, 10最高
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TaskExecution:
    """任务执行实例"""
    id: str
    task_id: str
    status: TaskStatus
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.execution_context is None:
            self.execution_context = {}

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config, workflow_engine, resource_manager):
        self.config = config
        self.workflow_engine = workflow_engine
        self.resource_manager = resource_manager
        self.logger = logging.getLogger(__name__)
        
        # 任务存储
        self.tasks: Dict[str, TaskDefinition] = {}
        self.executions: Dict[str, TaskExecution] = {}
        
        # 调度队列
        self.pending_queue: List[TaskExecution] = []  # 优先级队列
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 调度控制
        self.max_concurrent_tasks = config.max_concurrent_tasks
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # 事件系统
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 统计信息
        self.stats = {
            "total_scheduled": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0
        }
        
        self.logger.info("任务调度器初始化完成")
    
    async def initialize(self):
        """初始化任务调度器"""
        try:
            # 加载已保存的任务
            await self._load_tasks()
            
            # 恢复未完成的执行
            await self._recover_executions()
            
            self.logger.info("任务调度器初始化成功")
            
        except Exception as e:
            self.logger.error(f"任务调度器初始化失败: {e}")
            raise
    
    async def start(self):
        """启动任务调度器"""
        try:
            self.scheduler_running = True
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            self.logger.info("任务调度器启动")
            
        except Exception as e:
            self.logger.error(f"启动任务调度器失败: {e}")
            raise
    
    async def stop(self):
        """停止任务调度器"""
        try:
            self.scheduler_running = False
            
            # 停止调度循环
            if self.scheduler_task:
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有运行中的任务
            for execution_id, task in self.running_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # 更新执行状态
                if execution_id in self.executions:
                    self.executions[execution_id].status = TaskStatus.CANCELLED
            
            self.running_tasks.clear()
            
            # 保存状态
            await self._save_executions()
            
            self.logger.info("任务调度器停止")
            
        except Exception as e:
            self.logger.error(f"停止任务调度器失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查调度器是否运行
            if not self.scheduler_running:
                return False
            
            # 检查运行中的任务数量
            if len(self.running_tasks) > self.max_concurrent_tasks:
                return False
            
            # 检查资源使用情况
            if self.resource_manager:
                resource_status = await self.resource_manager.get_status()
                if resource_status.get("memory_usage", 0) > 90:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    async def get_active_count(self) -> int:
        """获取活跃任务数量"""
        return len(self.running_tasks)
    
    # 任务管理
    async def create_task(self, task_def: Dict[str, Any]) -> str:
        """创建任务"""
        try:
            # 生成任务ID
            task_id = task_def.get("id", str(uuid.uuid4()))
            
            # 创建任务定义
            task = TaskDefinition(
                id=task_id,
                name=task_def["name"],
                type=TaskType(task_def["type"]),
                action=task_def["action"],
                schedule=task_def.get("schedule"),
                dependencies=task_def.get("dependencies", []),
                timeout=task_def.get("timeout", 300),
                max_retries=task_def.get("max_retries", 3),
                retry_delay=task_def.get("retry_delay", 60),
                priority=task_def.get("priority", 5),
                metadata=task_def.get("metadata", {})
            )
            
            # 验证任务
            await self._validate_task(task)
            
            # 保存任务
            self.tasks[task_id] = task
            await self._save_task(task)
            
            # 如果是立即执行任务，直接调度
            if task.type == TaskType.IMMEDIATE:
                await self.schedule_task_execution(task_id)
            
            self.logger.info(f"任务创建成功: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"创建任务失败: {e}")
            raise
    
    async def schedule_task(self, task_def: Dict[str, Any]) -> str:
        """调度任务（创建并调度）"""
        task_id = await self.create_task(task_def)
        
        # 根据任务类型调度执行
        if task_def["type"] != TaskType.IMMEDIATE.value:
            await self.schedule_task_execution(task_id)
        
        return task_id
    
    async def schedule_task_execution(self, task_id: str, scheduled_time: datetime = None) -> str:
        """调度任务执行"""
        try:
            if task_id not in self.tasks:
                raise ValueError(f"任务不存在: {task_id}")
            
            task = self.tasks[task_id]
            
            # 确定调度时间
            if scheduled_time is None:
                scheduled_time = self._calculate_schedule_time(task)
            
            # 创建执行实例
            execution_id = str(uuid.uuid4())
            execution = TaskExecution(
                id=execution_id,
                task_id=task_id,
                status=TaskStatus.PENDING,
                scheduled_time=scheduled_time
            )
            
            self.executions[execution_id] = execution
            
            # 添加到调度队列
            heapq.heappush(self.pending_queue, (
                scheduled_time.timestamp(),
                task.priority,
                execution_id
            ))
            
            self.stats["total_scheduled"] += 1
            
            # 触发调度事件
            await self._emit_event("task_scheduled", {
                "execution_id": execution_id,
                "task_id": task_id,
                "scheduled_time": scheduled_time.isoformat()
            })
            
            self.logger.debug(f"任务执行已调度: {execution_id}")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"调度任务执行失败: {e}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            # 取消运行中的执行
            cancelled_count = 0
            for execution_id, execution in self.executions.items():
                if execution.task_id == task_id and execution.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    if execution_id in self.running_tasks:
                        # 取消运行中的任务
                        self.running_tasks[execution_id].cancel()
                        del self.running_tasks[execution_id]
                    
                    execution.status = TaskStatus.CANCELLED
                    execution.end_time = datetime.now()
                    cancelled_count += 1
            
            # 从调度队列中移除
            self.pending_queue = [
                item for item in self.pending_queue
                if self.executions.get(item[2], {}).task_id != task_id
            ]
            heapq.heapify(self.pending_queue)
            
            self.stats["total_cancelled"] += cancelled_count
            
            # 触发取消事件
            await self._emit_event("task_cancelled", {
                "task_id": task_id,
                "cancelled_executions": cancelled_count
            })
            
            self.logger.info(f"任务取消成功: {task_id}, 取消执行数: {cancelled_count}")
            return cancelled_count > 0
            
        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return False
    
    # 调度循环
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self.scheduler_running:
            try:
                # 处理到期的任务
                await self._process_due_tasks()
                
                # 清理完成的任务
                await self._cleanup_completed_tasks()
                
                # 处理重复任务
                await self._process_recurring_tasks()
                
                # 等待下一次检查
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"调度循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _process_due_tasks(self):
        """处理到期的任务"""
        current_time = datetime.now()
        
        while (self.pending_queue and 
               len(self.running_tasks) < self.max_concurrent_tasks):
            
            # 检查队列顶部的任务
            if not self.pending_queue:
                break
            
            scheduled_time, priority, execution_id = self.pending_queue[0]
            
            # 检查是否到期
            if datetime.fromtimestamp(scheduled_time) > current_time:
                break
            
            # 移除队列顶部
            heapq.heappop(self.pending_queue)
            
            # 检查执行是否仍然有效
            if execution_id not in self.executions:
                continue
            
            execution = self.executions[execution_id]
            if execution.status != TaskStatus.PENDING:
                continue
            
            # 检查依赖
            if not await self._check_dependencies(execution):
                # 重新调度
                heapq.heappush(self.pending_queue, (
                    (current_time + timedelta(seconds=30)).timestamp(),
                    priority,
                    execution_id
                ))
                continue
            
            # 启动任务执行
            await self._start_task_execution(execution)
    
    async def _start_task_execution(self, execution: TaskExecution):
        """启动任务执行"""
        try:
            execution.status = TaskStatus.RUNNING
            execution.start_time = datetime.now()
            
            # 创建执行任务
            task = asyncio.create_task(self._execute_task(execution))
            self.running_tasks[execution.id] = task
            
            # 触发开始事件
            await self._emit_event("task_started", {
                "execution_id": execution.id,
                "task_id": execution.task_id
            })
            
            self.logger.debug(f"任务执行启动: {execution.id}")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            self.logger.error(f"启动任务执行失败: {e}")
    
    async def _execute_task(self, execution: TaskExecution):
        """执行任务"""
        try:
            task = self.tasks[execution.task_id]
            
            # 执行任务动作
            result = await self._execute_action(task.action, execution.execution_context)
            
            # 更新执行结果
            execution.status = TaskStatus.COMPLETED
            execution.result = result
            execution.end_time = datetime.now()
            
            self.stats["total_completed"] += 1
            
            # 触发完成事件
            await self._emit_event("task_completed", {
                "execution_id": execution.id,
                "task_id": execution.task_id,
                "result": result
            })
            
        except Exception as e:
            # 任务执行失败
            execution.error_message = str(e)
            
            # 检查是否需要重试
            if execution.retry_count < task.max_retries:
                execution.retry_count += 1
                execution.status = TaskStatus.PENDING
                
                # 重新调度
                retry_time = datetime.now() + timedelta(seconds=task.retry_delay)
                heapq.heappush(self.pending_queue, (
                    retry_time.timestamp(),
                    task.priority,
                    execution.id
                ))
                
                self.logger.warning(f"任务执行失败，重试 {execution.retry_count}/{task.max_retries}: {e}")
            else:
                execution.status = TaskStatus.FAILED
                execution.end_time = datetime.now()
                
                self.stats["total_failed"] += 1
                
                # 触发失败事件
                await self._emit_event("task_failed", {
                    "execution_id": execution.id,
                    "task_id": execution.task_id,
                    "error": str(e)
                })
                
                self.logger.error(f"任务执行失败: {e}")
                
        finally:
            # 清理运行中的任务
            if execution.id in self.running_tasks:
                del self.running_tasks[execution.id]
    
    async def _execute_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """执行任务动作"""
        action_type = action.get("type")
        
        if action_type == "workflow":
            # 执行工作流
            workflow_id = action.get("workflow_id")
            workflow_context = action.get("context", {})
            workflow_context.update(context)
            
            execution_id = await self.workflow_engine.execute_workflow(workflow_id, workflow_context)
            
            # 等待工作流完成
            while True:
                status = await self.workflow_engine.get_execution_status(execution_id)
                if status["status"] in ["completed", "failed", "cancelled"]:
                    return status
                await asyncio.sleep(1)
                
        elif action_type == "command":
            # 执行命令
            # TODO: 通过MCP调用Command Master
            return {"command_executed": True}
            
        elif action_type == "script":
            # 执行脚本
            # TODO: 实现脚本执行逻辑
            return {"script_executed": True}
            
        elif action_type == "notification":
            # 发送通知
            # TODO: 实现通知逻辑
            return {"notification_sent": True}
            
        else:
            raise ValueError(f"不支持的动作类型: {action_type}")
    
    async def _check_dependencies(self, execution: TaskExecution) -> bool:
        """检查任务依赖"""
        task = self.tasks[execution.task_id]
        
        for dep_task_id in task.dependencies:
            # 检查依赖任务是否完成
            dep_completed = False
            for exec_id, exec_obj in self.executions.items():
                if (exec_obj.task_id == dep_task_id and 
                    exec_obj.status == TaskStatus.COMPLETED):
                    dep_completed = True
                    break
            
            if not dep_completed:
                return False
        
        return True
    
    async def _cleanup_completed_tasks(self):
        """清理完成的任务"""
        # 清理旧的执行记录
        cutoff_time = datetime.now() - timedelta(days=7)
        
        to_remove = []
        for execution_id, execution in self.executions.items():
            if (execution.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                execution.end_time and execution.end_time < cutoff_time):
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.executions[execution_id]
    
    async def _process_recurring_tasks(self):
        """处理重复任务"""
        current_time = datetime.now()
        
        for task in self.tasks.values():
            if task.type == TaskType.RECURRING and task.schedule:
                # 检查是否需要创建新的执行
                last_execution_time = self._get_last_execution_time(task.id)
                next_execution_time = self._calculate_next_execution_time(task.schedule, last_execution_time)
                
                if next_execution_time and next_execution_time <= current_time:
                    await self.schedule_task_execution(task.id, next_execution_time)
    
    def _calculate_schedule_time(self, task: TaskDefinition) -> datetime:
        """计算调度时间"""
        if task.type == TaskType.IMMEDIATE:
            return datetime.now()
        elif task.type == TaskType.SCHEDULED:
            if task.schedule:
                # 解析时间字符串或cron表达式
                return self._parse_schedule_time(task.schedule)
            else:
                return datetime.now()
        elif task.type == TaskType.RECURRING:
            return self._calculate_next_execution_time(task.schedule)
        else:
            return datetime.now()
    
    def _parse_schedule_time(self, schedule: str) -> datetime:
        """解析调度时间"""
        try:
            # 尝试解析ISO时间格式
            return datetime.fromisoformat(schedule)
        except ValueError:
            # 尝试解析cron表达式
            return self._calculate_next_execution_time(schedule)
    
    def _calculate_next_execution_time(self, cron_expr: str, base_time: datetime = None) -> datetime:
        """计算下次执行时间"""
        if base_time is None:
            base_time = datetime.now()
        
        try:
            # 使用crontab库解析cron表达式
            cron = crontab.CronTab(cron_expr)
            next_time = cron.next(base_time)
            return datetime.fromtimestamp(next_time)
        except Exception as e:
            self.logger.error(f"解析cron表达式失败: {e}")
            return base_time + timedelta(hours=1)  # 默认1小时后
    
    def _get_last_execution_time(self, task_id: str) -> Optional[datetime]:
        """获取最后执行时间"""
        last_time = None
        for execution in self.executions.values():
            if (execution.task_id == task_id and 
                execution.status == TaskStatus.COMPLETED and
                execution.end_time):
                if last_time is None or execution.end_time > last_time:
                    last_time = execution.end_time
        return last_time
    
    # 验证和辅助方法
    async def _validate_task(self, task: TaskDefinition):
        """验证任务定义"""
        if not task.name:
            raise ValueError("任务名称不能为空")
        
        if not task.action:
            raise ValueError("任务动作不能为空")
        
        # 验证依赖关系
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                raise ValueError(f"依赖任务不存在: {dep_id}")
        
        # 验证调度表达式
        if task.type == TaskType.RECURRING and task.schedule:
            try:
                crontab.CronTab(task.schedule)
            except Exception as e:
                raise ValueError(f"无效的cron表达式: {e}")
    
    # 状态查询
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        executions = [
            asdict(execution) for execution in self.executions.values()
            if execution.task_id == task_id
        ]
        
        return {
            "task": asdict(task),
            "executions": executions,
            "total_executions": len(executions),
            "last_execution": executions[-1] if executions else None
        }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.scheduler_running,
            "pending_tasks": len(self.pending_queue),
            "running_tasks": len(self.running_tasks),
            "total_tasks": len(self.tasks),
            "total_executions": len(self.executions),
            "statistics": self.stats.copy()
        }
    
    # 事件系统
    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"事件处理器错误: {e}")
    
    # 持久化
    async def _load_tasks(self):
        """加载任务"""
        try:
            tasks_dir = self.data_dir / "tasks"
            if tasks_dir.exists():
                for task_file in tasks_dir.glob("*.json"):
                    try:
                        with open(task_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            task = TaskDefinition(**data)
                            self.tasks[task.id] = task
                    except Exception as e:
                        self.logger.error(f"加载任务失败 {task_file}: {e}")
        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
    
    async def _save_task(self, task: TaskDefinition):
        """保存任务"""
        try:
            tasks_dir = self.data_dir / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            
            task_file = tasks_dir / f"{task.id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存任务失败 {task.id}: {e}")
    
    async def _recover_executions(self):
        """恢复执行"""
        # TODO: 实现执行恢复逻辑
        pass
    
    async def _save_executions(self):
        """保存执行"""
        # TODO: 实现执行保存逻辑
        pass

