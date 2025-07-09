"""
WorkflowEngine - 工作流执行引擎
支持复杂工作流的定义、执行和管理
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    type: str  # command, mcp_call, condition, loop, parallel
    config: Dict[str, Any]
    dependencies: List[str] = None
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = None
    timeout: int = 3600
    created_at: datetime = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    id: str
    workflow_id: str
    status: WorkflowStatus
    context: Dict[str, Any]
    step_results: Dict[str, Any] = None
    current_step: Optional[str] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.step_results is None:
            self.step_results = {}
        if self.start_time is None:
            self.start_time = datetime.now()

class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, config, resource_manager, mcp_coordinator):
        self.config = config
        self.resource_manager = resource_manager
        self.mcp_coordinator = mcp_coordinator
        self.logger = logging.getLogger(__name__)
        
        # 工作流存储
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # 执行控制
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.max_concurrent_executions = config.max_concurrent_workflows
        
        # 步骤处理器
        self.step_handlers: Dict[str, Callable] = {
            "command": self._handle_command_step,
            "mcp_call": self._handle_mcp_call_step,
            "condition": self._handle_condition_step,
            "loop": self._handle_loop_step,
            "parallel": self._handle_parallel_step,
            "delay": self._handle_delay_step,
            "script": self._handle_script_step
        }
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        self.logger.info("工作流引擎初始化完成")
    
    async def initialize(self):
        """初始化工作流引擎"""
        try:
            # 加载已保存的工作流
            await self._load_workflows()
            
            # 恢复未完成的执行
            await self._recover_executions()
            
            self.logger.info("工作流引擎初始化成功")
            
        except Exception as e:
            self.logger.error(f"工作流引擎初始化失败: {e}")
            raise
    
    async def start(self):
        """启动工作流引擎"""
        self.logger.info("工作流引擎启动")
    
    async def stop(self):
        """停止工作流引擎"""
        try:
            # 停止所有运行中的执行
            for execution_id, task in self.running_executions.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # 更新执行状态
                if execution_id in self.executions:
                    self.executions[execution_id].status = WorkflowStatus.CANCELLED
            
            self.running_executions.clear()
            
            # 保存状态
            await self._save_executions()
            
            self.logger.info("工作流引擎停止")
            
        except Exception as e:
            self.logger.error(f"停止工作流引擎失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查运行中的执行数量
            if len(self.running_executions) > self.max_concurrent_executions:
                return False
            
            # 检查资源使用情况
            if self.resource_manager:
                resource_status = await self.resource_manager.get_status()
                if resource_status.get("cpu_usage", 0) > 90:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    async def get_active_count(self) -> int:
        """获取活跃执行数量"""
        return len(self.running_executions)
    
    # 工作流管理
    async def create_workflow(self, workflow_def: Dict[str, Any]) -> str:
        """创建工作流"""
        try:
            # 生成工作流ID
            workflow_id = workflow_def.get("id", str(uuid.uuid4()))
            
            # 解析步骤
            steps = []
            for step_data in workflow_def.get("steps", []):
                step = WorkflowStep(
                    id=step_data["id"],
                    name=step_data["name"],
                    type=step_data["type"],
                    config=step_data.get("config", {}),
                    dependencies=step_data.get("dependencies", []),
                    timeout=step_data.get("timeout", 300),
                    max_retries=step_data.get("max_retries", 3)
                )
                steps.append(step)
            
            # 创建工作流定义
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=workflow_def["name"],
                description=workflow_def.get("description", ""),
                version=workflow_def.get("version", "1.0"),
                steps=steps,
                variables=workflow_def.get("variables", {}),
                timeout=workflow_def.get("timeout", 3600)
            )
            
            # 验证工作流
            await self._validate_workflow(workflow)
            
            # 保存工作流
            self.workflows[workflow_id] = workflow
            await self._save_workflow(workflow)
            
            self.logger.info(f"工作流创建成功: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"创建工作流失败: {e}")
            raise
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """执行工作流"""
        try:
            # 检查工作流是否存在
            if workflow_id not in self.workflows:
                raise ValueError(f"工作流不存在: {workflow_id}")
            
            # 检查并发限制
            if len(self.running_executions) >= self.max_concurrent_executions:
                raise RuntimeError("达到最大并发执行限制")
            
            # 创建执行实例
            execution_id = str(uuid.uuid4())
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.PENDING,
                context=context or {}
            )
            
            self.executions[execution_id] = execution
            
            # 启动执行任务
            task = asyncio.create_task(self._execute_workflow_task(execution))
            self.running_executions[execution_id] = task
            
            self.logger.info(f"工作流执行启动: {execution_id}")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"执行工作流失败: {e}")
            raise
    
    async def _execute_workflow_task(self, execution: WorkflowExecution):
        """执行工作流任务"""
        try:
            execution.status = WorkflowStatus.RUNNING
            workflow = self.workflows[execution.workflow_id]
            
            # 触发开始事件
            await self._emit_event("workflow_started", {
                "execution_id": execution.id,
                "workflow_id": execution.workflow_id
            })
            
            # 构建步骤依赖图
            step_graph = self._build_step_graph(workflow.steps)
            
            # 执行步骤
            await self._execute_steps(execution, workflow, step_graph)
            
            # 检查执行结果
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.end_time = datetime.now()
            
            # 触发完成事件
            await self._emit_event("workflow_completed", {
                "execution_id": execution.id,
                "status": execution.status.value
            })
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            
            # 触发失败事件
            await self._emit_event("workflow_failed", {
                "execution_id": execution.id,
                "error": str(e)
            })
            
            self.logger.error(f"工作流执行失败: {e}")
            
        finally:
            # 清理运行中的执行
            if execution.id in self.running_executions:
                del self.running_executions[execution.id]
            
            # 保存执行结果
            await self._save_execution(execution)
    
    async def _execute_steps(self, execution: WorkflowExecution, workflow: WorkflowDefinition, step_graph: Dict[str, List[str]]):
        """执行工作流步骤"""
        completed_steps = set()
        step_map = {step.id: step for step in workflow.steps}
        
        while len(completed_steps) < len(workflow.steps):
            # 找到可以执行的步骤
            ready_steps = []
            for step in workflow.steps:
                if (step.id not in completed_steps and 
                    all(dep in completed_steps for dep in step.dependencies)):
                    ready_steps.append(step)
            
            if not ready_steps:
                # 检查是否有循环依赖或其他问题
                remaining_steps = [s.id for s in workflow.steps if s.id not in completed_steps]
                raise RuntimeError(f"无法继续执行，剩余步骤: {remaining_steps}")
            
            # 执行准备好的步骤
            tasks = []
            for step in ready_steps:
                task = asyncio.create_task(self._execute_step(execution, step))
                tasks.append((step.id, task))
            
            # 等待步骤完成
            for step_id, task in tasks:
                try:
                    result = await task
                    execution.step_results[step_id] = result
                    completed_steps.add(step_id)
                    
                    # 触发步骤完成事件
                    await self._emit_event("step_completed", {
                        "execution_id": execution.id,
                        "step_id": step_id,
                        "result": result
                    })
                    
                except Exception as e:
                    # 步骤执行失败
                    execution.step_results[step_id] = {"error": str(e)}
                    
                    # 检查是否需要重试
                    step = step_map[step_id]
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        self.logger.warning(f"步骤 {step_id} 执行失败，重试 {step.retry_count}/{step.max_retries}")
                        continue
                    
                    # 触发步骤失败事件
                    await self._emit_event("step_failed", {
                        "execution_id": execution.id,
                        "step_id": step_id,
                        "error": str(e)
                    })
                    
                    # 检查是否为关键步骤
                    if step.config.get("critical", True):
                        raise RuntimeError(f"关键步骤 {step_id} 执行失败: {e}")
                    
                    # 非关键步骤，标记为跳过
                    completed_steps.add(step_id)
    
    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """执行单个步骤"""
        try:
            execution.current_step = step.id
            
            # 触发步骤开始事件
            await self._emit_event("step_started", {
                "execution_id": execution.id,
                "step_id": step.id,
                "step_type": step.type
            })
            
            # 获取步骤处理器
            if step.type not in self.step_handlers:
                raise ValueError(f"不支持的步骤类型: {step.type}")
            
            handler = self.step_handlers[step.type]
            
            # 执行步骤（带超时）
            result = await asyncio.wait_for(
                handler(execution, step),
                timeout=step.timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"步骤 {step.id} 执行超时")
        except Exception as e:
            self.logger.error(f"步骤 {step.id} 执行失败: {e}")
            raise
    
    # 步骤处理器
    async def _handle_command_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理命令步骤"""
        command = step.config.get("command")
        if not command:
            raise ValueError("命令步骤缺少command配置")
        
        # 替换变量
        command = self._replace_variables(command, execution.context)
        
        # 通过MCP调用Command Master
        result = await self.mcp_coordinator.call_mcp(
            "command_master",
            "execute_command",
            {
                "command": command,
                "context": execution.context,
                "step_config": step.config
            }
        )
        
        return result
    
    async def _handle_mcp_call_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理MCP调用步骤"""
        mcp_id = step.config.get("mcp_id")
        method = step.config.get("method")
        params = step.config.get("params", {})
        
        if not mcp_id or not method:
            raise ValueError("MCP调用步骤缺少mcp_id或method配置")
        
        # 替换参数中的变量
        params = self._replace_variables(params, execution.context)
        
        # 调用MCP
        result = await self.mcp_coordinator.call_mcp(mcp_id, method, params)
        
        return result
    
    async def _handle_condition_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理条件步骤"""
        condition = step.config.get("condition")
        if not condition:
            raise ValueError("条件步骤缺少condition配置")
        
        # 评估条件
        result = self._evaluate_condition(condition, execution.context)
        
        return {"condition_result": result}
    
    async def _handle_loop_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理循环步骤"""
        # TODO: 实现循环逻辑
        return {"loop_completed": True}
    
    async def _handle_parallel_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理并行步骤"""
        # TODO: 实现并行执行逻辑
        return {"parallel_completed": True}
    
    async def _handle_delay_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理延迟步骤"""
        delay = step.config.get("delay", 1)
        await asyncio.sleep(delay)
        return {"delayed": delay}
    
    async def _handle_script_step(self, execution: WorkflowExecution, step: WorkflowStep) -> Any:
        """处理脚本步骤"""
        script = step.config.get("script")
        if not script:
            raise ValueError("脚本步骤缺少script配置")
        
        # TODO: 实现脚本执行逻辑
        return {"script_executed": True}
    
    # 辅助方法
    def _build_step_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """构建步骤依赖图"""
        graph = {}
        for step in steps:
            graph[step.id] = step.dependencies.copy()
        return graph
    
    def _replace_variables(self, text: Any, context: Dict[str, Any]) -> Any:
        """替换变量"""
        if isinstance(text, str):
            # 简单的变量替换实现
            for key, value in context.items():
                text = text.replace(f"${{{key}}}", str(value))
            return text
        elif isinstance(text, dict):
            return {k: self._replace_variables(v, context) for k, v in text.items()}
        elif isinstance(text, list):
            return [self._replace_variables(item, context) for item in text]
        else:
            return text
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        # 简单的条件评估实现
        # TODO: 实现更复杂的条件评估逻辑
        try:
            # 替换变量
            condition = self._replace_variables(condition, context)
            # 安全的表达式评估
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            self.logger.error(f"条件评估失败: {e}")
            return False
    
    async def _validate_workflow(self, workflow: WorkflowDefinition):
        """验证工作流定义"""
        # 检查步骤ID唯一性
        step_ids = [step.id for step in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("步骤ID不唯一")
        
        # 检查依赖关系
        for step in workflow.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"步骤 {step.id} 依赖的步骤 {dep} 不存在")
        
        # 检查循环依赖
        # TODO: 实现循环依赖检测
    
    # 状态查询
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态"""
        if execution_id not in self.executions:
            raise ValueError(f"执行不存在: {execution_id}")
        
        execution = self.executions[execution_id]
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "step_results": execution.step_results,
            "error_message": execution.error_message
        }
    
    # 事件系统
    def on(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"事件回调错误: {e}")
    
    # 持久化
    async def _load_workflows(self):
        """加载工作流"""
        try:
            workflows_dir = self.data_dir / "workflows"
            if workflows_dir.exists():
                for workflow_file in workflows_dir.glob("*.json"):
                    workflow = await self._load_workflow(workflow_file.stem)
                    if workflow:
                        self.workflows[workflow.id] = workflow
        except Exception as e:
            self.logger.error(f"加载工作流失败: {e}")
    
    async def _load_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """加载工作流"""
        try:
            workflow_file = self.data_dir / f"workflows/{workflow_id}.json"
            if workflow_file.exists():
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return WorkflowDefinition(**data)
            return None
        except Exception as e:
            self.logger.error(f"加载工作流失败 {workflow_id}: {e}")
            return None
    
    async def _save_workflow(self, workflow: WorkflowDefinition):
        """保存工作流"""
        try:
            workflows_dir = self.data_dir / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_file = workflows_dir / f"{workflow.id}.json"
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存工作流失败 {workflow.id}: {e}")
    
    async def _recover_executions(self):
        """恢复执行"""
        try:
            executions_dir = self.data_dir / "executions"
            if executions_dir.exists():
                for execution_file in executions_dir.glob("*.json"):
                    try:
                        with open(execution_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            execution = WorkflowExecution(**data)
                            self.executions[execution.id] = execution
                            
                            # 如果是运行中的执行，标记为失败
                            if execution.status == ExecutionStatus.RUNNING:
                                execution.status = ExecutionStatus.FAILED
                                execution.error = "系统重启导致执行中断"
                                await self._save_execution(execution)
                    except Exception as e:
                        self.logger.error(f"恢复执行失败 {execution_file}: {e}")
        except Exception as e:
            self.logger.error(f"恢复执行失败: {e}")
    
    async def _save_execution(self, execution: WorkflowExecution):
        """保存执行"""
        try:
            executions_dir = self.data_dir / "executions"
            executions_dir.mkdir(parents=True, exist_ok=True)
            
            execution_file = executions_dir / f"{execution.id}.json"
            with open(execution_file, 'w', encoding='utf-8') as f:
                json.dump(execution.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存执行失败 {execution.id}: {e}")
    
    async def _save_executions(self):
        """保存所有执行"""
        try:
            for execution in self.executions.values():
                await self._save_execution(execution)
        except Exception as e:
            self.logger.error(f"批量保存执行失败: {e}")

