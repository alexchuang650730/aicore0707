"""
PowerAutomation 主控制器

统一管理和协调所有PowerAutomation组件，包括:
- 6大专业智能体的协调
- Local Adapter MCP的集成
- 任务分发和执行监控
- 结果整合和反馈

基于已完成的core/架构，实现统一的控制中心。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 导入已完成的核心组件
from ..agents.coordination.agent_coordinator import AgentCoordinator
from ..agents.shared.agent_registry import AgentRegistry
from ..components.local_adapter_mcp.local_adapter_engine import LocalAdapterEngine
from ..routing.smart_router.smart_router import SmartRouter
from ..mcp_coordinator.legacy.mcp_coordinator import MCPCoordinator
from .task_analyzer import TaskAnalyzer
from .intelligent_router import IntelligentRouter
from .result_integrator import ResultIntegrator
from .performance_monitor import PerformanceMonitor


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    ROUTING = "routing"
    EXECUTING = "executing"
    INTEGRATING = "integrating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class Task:
    """任务数据结构"""
    id: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error_info: Optional[str] = None


class MainController:
    """
    PowerAutomation 主控制器
    
    负责统一管理和协调所有PowerAutomation组件，
    实现任务的智能分析、路由、执行和结果整合。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化主控制器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self._init_components()
        
        # 任务管理
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # 状态管理
        self.is_running = False
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0
        }
        
        self.logger.info("PowerAutomation主控制器初始化完成")
    
    def _init_components(self):
        """初始化核心组件"""
        try:
            # 智能体协调器
            self.agent_coordinator = AgentCoordinator()
            
            # 智能体注册表
            self.agent_registry = AgentRegistry()
            
            # Local Adapter MCP引擎
            self.local_adapter = LocalAdapterEngine()
            
            # 智能路由器
            self.smart_router = SmartRouter()
            
            # MCP协调器
            self.mcp_coordinator = MCPCoordinator()
            
            # 任务分析器
            self.task_analyzer = TaskAnalyzer()
            
            # 智能路由器
            self.intelligent_router = IntelligentRouter()
            
            # 结果整合器
            self.result_integrator = ResultIntegrator()
            
            # 性能监控器
            self.performance_monitor = PerformanceMonitor()
            
            self.logger.info("所有核心组件初始化成功")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    async def start(self):
        """启动主控制器"""
        if self.is_running:
            self.logger.warning("主控制器已在运行中")
            return
        
        self.is_running = True
        self.logger.info("启动PowerAutomation主控制器")
        
        # 启动核心组件
        await self._start_components()
        
        # 启动任务处理循环
        asyncio.create_task(self._task_processing_loop())
        
        # 启动性能监控
        asyncio.create_task(self._performance_monitoring_loop())
        
        self.logger.info("PowerAutomation主控制器启动完成")
    
    async def stop(self):
        """停止主控制器"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("停止PowerAutomation主控制器")
        
        # 停止核心组件
        await self._stop_components()
        
        self.logger.info("PowerAutomation主控制器已停止")
    
    async def _start_components(self):
        """启动核心组件"""
        try:
            # 启动Local Adapter MCP
            await self.local_adapter.start()
            
            # 启动智能体协调器
            await self.agent_coordinator.start()
            
            # 启动MCP协调器
            await self.mcp_coordinator.start()
            
            # 启动性能监控器
            await self.performance_monitor.start()
            
            self.logger.info("所有核心组件启动成功")
            
        except Exception as e:
            self.logger.error(f"组件启动失败: {e}")
            raise
    
    async def _stop_components(self):
        """停止核心组件"""
        try:
            # 停止性能监控器
            await self.performance_monitor.stop()
            
            # 停止MCP协调器
            await self.mcp_coordinator.stop()
            
            # 停止智能体协调器
            await self.agent_coordinator.stop()
            
            # 停止Local Adapter MCP
            await self.local_adapter.stop()
            
            self.logger.info("所有核心组件停止成功")
            
        except Exception as e:
            self.logger.error(f"组件停止失败: {e}")
    
    async def submit_task(self, 
                         description: str, 
                         task_type: str = "general",
                         priority: TaskPriority = TaskPriority.NORMAL,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        提交任务
        
        Args:
            description: 任务描述
            task_type: 任务类型
            priority: 任务优先级
            metadata: 任务元数据
            
        Returns:
            任务ID
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task = Task(
            id=task_id,
            description=description,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put(task)
        
        self.stats["total_tasks"] += 1
        
        self.logger.info(f"任务已提交: {task_id} - {description}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "results": task.results,
            "error_info": task.error_info
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now()
        
        self.logger.info(f"任务已取消: {task_id}")
        return True
    
    async def _task_processing_loop(self):
        """任务处理循环"""
        self.logger.info("启动任务处理循环")
        
        while self.is_running:
            try:
                # 获取任务（带超时）
                task = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # 处理任务
                await self._process_task(task)
                
            except asyncio.TimeoutError:
                # 超时继续循环
                continue
            except Exception as e:
                self.logger.error(f"任务处理循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task: Task):
        """
        处理单个任务
        
        Args:
            task: 任务对象
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"开始处理任务: {task.id}")
            
            # 1. 任务分析
            task.status = TaskStatus.ANALYZING
            task.updated_at = datetime.now()
            
            analysis_result = await self.task_analyzer.analyze_task(
                task.description, 
                task.task_type, 
                task.metadata
            )
            
            # 2. 智能路由
            task.status = TaskStatus.ROUTING
            task.updated_at = datetime.now()
            
            routing_plan = await self.intelligent_router.route_task(
                task, 
                analysis_result
            )
            
            # 3. 任务执行
            task.status = TaskStatus.EXECUTING
            task.updated_at = datetime.now()
            
            execution_results = await self._execute_task(task, routing_plan)
            
            # 4. 结果整合
            task.status = TaskStatus.INTEGRATING
            task.updated_at = datetime.now()
            
            final_results = await self.result_integrator.integrate_results(
                task, 
                execution_results
            )
            
            # 5. 任务完成
            task.status = TaskStatus.COMPLETED
            task.results = final_results
            task.updated_at = datetime.now()
            
            self.stats["completed_tasks"] += 1
            
            # 更新平均执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_average_execution_time(execution_time)
            
            self.logger.info(f"任务完成: {task.id} (耗时: {execution_time:.2f}秒)")
            
        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.error_info = str(e)
            task.updated_at = datetime.now()
            
            self.stats["failed_tasks"] += 1
            
            self.logger.error(f"任务失败: {task.id} - {e}")
    
    async def _execute_task(self, task: Task, routing_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务对象
            routing_plan: 路由计划
            
        Returns:
            执行结果
        """
        execution_results = {}
        
        # 根据路由计划执行任务
        for step in routing_plan.get("steps", []):
            step_type = step.get("type")
            step_config = step.get("config", {})
            
            if step_type == "agent":
                # 智能体执行
                agent_name = step_config.get("agent_name")
                result = await self.agent_coordinator.execute_agent_task(
                    agent_name, 
                    task.description, 
                    step_config
                )
                execution_results[f"agent_{agent_name}"] = result
                
            elif step_type == "mcp":
                # MCP执行
                mcp_name = step_config.get("mcp_name")
                result = await self.mcp_coordinator.execute_mcp_task(
                    mcp_name, 
                    task.description, 
                    step_config
                )
                execution_results[f"mcp_{mcp_name}"] = result
                
            elif step_type == "local_adapter":
                # Local Adapter执行
                result = await self.local_adapter.execute_task(
                    task.description, 
                    step_config
                )
                execution_results["local_adapter"] = result
        
        return execution_results
    
    def _update_average_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        current_avg = self.stats["average_execution_time"]
        completed_tasks = self.stats["completed_tasks"]
        
        if completed_tasks == 1:
            self.stats["average_execution_time"] = execution_time
        else:
            # 计算新的平均值
            self.stats["average_execution_time"] = (
                (current_avg * (completed_tasks - 1) + execution_time) / completed_tasks
            )
    
    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        self.logger.info("启动性能监控循环")
        
        while self.is_running:
            try:
                # 收集性能指标
                await self.performance_monitor.collect_metrics({
                    "controller_stats": self.stats,
                    "task_count": len(self.tasks),
                    "queue_size": self.task_queue.qsize()
                })
                
                # 每30秒监控一次
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"性能监控错误: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_tasks": len([t for t in self.tasks.values() 
                               if t.status not in [TaskStatus.COMPLETED, 
                                                 TaskStatus.FAILED, 
                                                 TaskStatus.CANCELLED]]),
            "queue_size": self.task_queue.qsize(),
            "is_running": self.is_running
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy" if self.is_running else "stopped",
            "components": {},
            "stats": self.get_stats()
        }
        
        # 检查各组件健康状态
        try:
            health_status["components"]["local_adapter"] = await self.local_adapter.health_check()
            health_status["components"]["agent_coordinator"] = await self.agent_coordinator.health_check()
            health_status["components"]["mcp_coordinator"] = await self.mcp_coordinator.health_check()
            health_status["components"]["performance_monitor"] = await self.performance_monitor.health_check()
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status


# 全局主控制器实例
_main_controller_instance: Optional[MainController] = None


def get_main_controller(config: Optional[Dict[str, Any]] = None) -> MainController:
    """
    获取主控制器单例实例
    
    Args:
        config: 配置参数
        
    Returns:
        主控制器实例
    """
    global _main_controller_instance
    
    if _main_controller_instance is None:
        _main_controller_instance = MainController(config)
    
    return _main_controller_instance


async def initialize_powerautomation(config: Optional[Dict[str, Any]] = None) -> MainController:
    """
    初始化PowerAutomation系统
    
    Args:
        config: 配置参数
        
    Returns:
        主控制器实例
    """
    controller = get_main_controller(config)
    await controller.start()
    return controller


if __name__ == "__main__":
    # 测试主控制器
    async def test_main_controller():
        # 初始化
        controller = await initialize_powerautomation()
        
        # 提交测试任务
        task_id = await controller.submit_task(
            description="测试任务：创建一个简单的Python脚本",
            task_type="development",
            priority=TaskPriority.NORMAL
        )
        
        print(f"任务已提交: {task_id}")
        
        # 等待任务完成
        while True:
            status = await controller.get_task_status(task_id)
            print(f"任务状态: {status['status']}")
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
            
            await asyncio.sleep(1)
        
        # 显示最终结果
        final_status = await controller.get_task_status(task_id)
        print(f"最终结果: {final_status}")
        
        # 显示统计信息
        stats = controller.get_stats()
        print(f"统计信息: {stats}")
        
        # 停止控制器
        await controller.stop()
    
    # 运行测试
    asyncio.run(test_main_controller())

