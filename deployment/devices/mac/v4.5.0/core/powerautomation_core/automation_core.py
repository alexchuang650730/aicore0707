"""
AutomationCore - PowerAutomation Core 4.5 主控制器
端侧优化的自动化引擎核心
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .workflow_engine import WorkflowEngine
from .task_scheduler import TaskScheduler
from .resource_manager import ResourceManager
from .mcp_coordinator import MCPCoordinator
from .monitoring_service import MonitoringService

@dataclass
class CoreConfig:
    """核心配置"""
    # 基础配置
    app_name: str = "PowerAutomation Core 4.5"
    version: str = "4.5.0"
    environment: str = "edge"  # edge, cloud, hybrid
    
    # 性能配置
    max_concurrent_workflows: int = 10
    max_concurrent_tasks: int = 50
    resource_check_interval: int = 30
    monitoring_interval: int = 10
    
    # 存储配置
    data_dir: str = "~/.claudeditor/powerautomation"
    log_dir: str = "~/.claudeditor/logs"
    cache_dir: str = "~/.claudeditor/cache"
    
    # 网络配置
    enable_cloud_sync: bool = True
    cloud_endpoint: str = "https://api.powerautomation.ai"
    sync_interval: int = 300
    
    # 安全配置
    enable_encryption: bool = True
    require_auth: bool = True
    audit_enabled: bool = True

@dataclass
class CoreStatus:
    """核心状态"""
    status: str  # starting, running, stopping, stopped, error
    start_time: datetime
    uptime: float
    active_workflows: int
    active_tasks: int
    resource_usage: Dict[str, float]
    last_error: Optional[str] = None

class AutomationCore:
    """PowerAutomation Core 4.5 主控制器"""
    
    def __init__(self, config: CoreConfig = None):
        self.config = config or CoreConfig()
        self.logger = logging.getLogger(__name__)
        
        # 状态管理
        self.status = CoreStatus(
            status="stopped",
            start_time=datetime.now(),
            uptime=0.0,
            active_workflows=0,
            active_tasks=0,
            resource_usage={}
        )
        
        # 核心组件
        self.workflow_engine: Optional[WorkflowEngine] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        self.resource_manager: Optional[ResourceManager] = None
        self.mcp_coordinator: Optional[MCPCoordinator] = None
        self.monitoring_service: Optional[MonitoringService] = None
        
        # 事件系统
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
        # 初始化目录
        self._initialize_directories()
        
        self.logger.info(f"PowerAutomation Core 4.5 初始化完成")
    
    def _initialize_directories(self):
        """初始化目录结构"""
        try:
            dirs = [
                Path(self.config.data_dir).expanduser(),
                Path(self.config.log_dir).expanduser(),
                Path(self.config.cache_dir).expanduser()
            ]
            
            for dir_path in dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                
            self.logger.debug("目录结构初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化目录失败: {e}")
            raise
    
    async def start(self) -> bool:
        """启动核心服务"""
        try:
            self.logger.info("启动 PowerAutomation Core 4.5...")
            self.status.status = "starting"
            
            # 初始化核心组件
            await self._initialize_components()
            
            # 启动组件
            await self._start_components()
            
            # 启动监控循环
            asyncio.create_task(self._monitoring_loop())
            
            self.running = True
            self.status.status = "running"
            self.status.start_time = datetime.now()
            
            # 触发启动事件
            await self._emit_event("core_started", {"timestamp": datetime.now()})
            
            self.logger.info("PowerAutomation Core 4.5 启动成功")
            return True
            
        except Exception as e:
            self.status.status = "error"
            self.status.last_error = str(e)
            self.logger.error(f"启动失败: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止核心服务"""
        try:
            self.logger.info("停止 PowerAutomation Core 4.5...")
            self.status.status = "stopping"
            self.running = False
            
            # 停止组件
            await self._stop_components()
            
            self.status.status = "stopped"
            
            # 触发停止事件
            await self._emit_event("core_stopped", {"timestamp": datetime.now()})
            
            self.logger.info("PowerAutomation Core 4.5 停止成功")
            return True
            
        except Exception as e:
            self.status.status = "error"
            self.status.last_error = str(e)
            self.logger.error(f"停止失败: {e}")
            return False
    
    async def _initialize_components(self):
        """初始化核心组件"""
        try:
            # 初始化资源管理器
            self.resource_manager = ResourceManager(self.config)
            await self.resource_manager.initialize()
            
            # 初始化MCP协调器
            self.mcp_coordinator = MCPCoordinator(self.config)
            await self.mcp_coordinator.initialize()
            
            # 初始化工作流引擎
            self.workflow_engine = WorkflowEngine(
                self.config, 
                self.resource_manager,
                self.mcp_coordinator
            )
            await self.workflow_engine.initialize()
            
            # 初始化任务调度器
            self.task_scheduler = TaskScheduler(
                self.config,
                self.workflow_engine,
                self.resource_manager
            )
            await self.task_scheduler.initialize()
            
            # 初始化监控服务
            self.monitoring_service = MonitoringService(
                self.config,
                self.resource_manager
            )
            await self.monitoring_service.initialize()
            
            self.logger.debug("核心组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    async def _start_components(self):
        """启动核心组件"""
        try:
            # 按依赖顺序启动组件
            await self.resource_manager.start()
            await self.mcp_coordinator.start()
            await self.workflow_engine.start()
            await self.task_scheduler.start()
            await self.monitoring_service.start()
            
            self.logger.debug("核心组件启动完成")
            
        except Exception as e:
            self.logger.error(f"组件启动失败: {e}")
            raise
    
    async def _stop_components(self):
        """停止核心组件"""
        try:
            # 按反向依赖顺序停止组件
            if self.monitoring_service:
                await self.monitoring_service.stop()
            if self.task_scheduler:
                await self.task_scheduler.stop()
            if self.workflow_engine:
                await self.workflow_engine.stop()
            if self.mcp_coordinator:
                await self.mcp_coordinator.stop()
            if self.resource_manager:
                await self.resource_manager.stop()
            
            self.logger.debug("核心组件停止完成")
            
        except Exception as e:
            self.logger.error(f"组件停止失败: {e}")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 更新状态
                await self._update_status()
                
                # 检查组件健康状态
                await self._health_check()
                
                # 等待下一次检查
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.config.monitoring_interval)
    
    async def _update_status(self):
        """更新状态信息"""
        try:
            current_time = datetime.now()
            self.status.uptime = (current_time - self.status.start_time).total_seconds()
            
            # 获取活跃工作流和任务数量
            if self.workflow_engine:
                self.status.active_workflows = await self.workflow_engine.get_active_count()
            if self.task_scheduler:
                self.status.active_tasks = await self.task_scheduler.get_active_count()
            
            # 获取资源使用情况
            if self.resource_manager:
                self.status.resource_usage = await self.resource_manager.get_usage_stats()
                
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
    
    async def _health_check(self):
        """健康检查"""
        try:
            components = [
                ("resource_manager", self.resource_manager),
                ("mcp_coordinator", self.mcp_coordinator),
                ("workflow_engine", self.workflow_engine),
                ("task_scheduler", self.task_scheduler),
                ("monitoring_service", self.monitoring_service)
            ]
            
            for name, component in components:
                if component and hasattr(component, 'health_check'):
                    healthy = await component.health_check()
                    if not healthy:
                        self.logger.warning(f"组件 {name} 健康检查失败")
                        
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    # 工作流管理接口
    async def create_workflow(self, workflow_def: Dict[str, Any]) -> str:
        """创建工作流"""
        if not self.workflow_engine:
            raise RuntimeError("工作流引擎未初始化")
        return await self.workflow_engine.create_workflow(workflow_def)
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """执行工作流"""
        if not self.workflow_engine:
            raise RuntimeError("工作流引擎未初始化")
        return await self.workflow_engine.execute_workflow(workflow_id, context)
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        if not self.workflow_engine:
            raise RuntimeError("工作流引擎未初始化")
        return await self.workflow_engine.get_execution_status(execution_id)
    
    # 任务调度接口
    async def schedule_task(self, task_def: Dict[str, Any]) -> str:
        """调度任务"""
        if not self.task_scheduler:
            raise RuntimeError("任务调度器未初始化")
        return await self.task_scheduler.schedule_task(task_def)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if not self.task_scheduler:
            raise RuntimeError("任务调度器未初始化")
        return await self.task_scheduler.cancel_task(task_id)
    
    # MCP协调接口
    async def register_mcp(self, mcp_info: Dict[str, Any]) -> bool:
        """注册MCP"""
        if not self.mcp_coordinator:
            raise RuntimeError("MCP协调器未初始化")
        return await self.mcp_coordinator.register_mcp(mcp_info)
    
    async def call_mcp(self, mcp_id: str, method: str, params: Dict[str, Any]) -> Any:
        """调用MCP"""
        if not self.mcp_coordinator:
            raise RuntimeError("MCP协调器未初始化")
        return await self.mcp_coordinator.call_mcp(mcp_id, method, params)
    
    # 资源管理接口
    async def get_resource_status(self) -> Dict[str, Any]:
        """获取资源状态"""
        if not self.resource_manager:
            raise RuntimeError("资源管理器未初始化")
        return await self.resource_manager.get_status()
    
    async def allocate_resource(self, resource_type: str, amount: float) -> str:
        """分配资源"""
        if not self.resource_manager:
            raise RuntimeError("资源管理器未初始化")
        return await self.resource_manager.allocate_resource(resource_type, amount)
    
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
    
    # 状态查询接口
    def get_status(self) -> Dict[str, Any]:
        """获取核心状态"""
        return {
            "status": self.status.status,
            "version": self.config.version,
            "uptime": self.status.uptime,
            "active_workflows": self.status.active_workflows,
            "active_tasks": self.status.active_tasks,
            "resource_usage": self.status.resource_usage,
            "last_error": self.status.last_error,
            "components": {
                "workflow_engine": self.workflow_engine is not None,
                "task_scheduler": self.task_scheduler is not None,
                "resource_manager": self.resource_manager is not None,
                "mcp_coordinator": self.mcp_coordinator is not None,
                "monitoring_service": self.monitoring_service is not None
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        return asdict(self.config)
    
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 验证配置
            # TODO: 实现配置验证逻辑
            
            # 应用配置
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # 通知组件配置更新
            await self._emit_event("config_updated", new_config)
            
            self.logger.info("配置更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            return False

