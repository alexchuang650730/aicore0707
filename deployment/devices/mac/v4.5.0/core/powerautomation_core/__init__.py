"""
PowerAutomation Core 4.5 - 端侧集成版本
为ClaudeEditor 4.5优化的自动化引擎

主要功能:
- 工作流引擎
- 任务调度器
- 资源管理器
- MCP协调器
- 监控服务
"""

from .workflow_engine import WorkflowEngine
from .task_scheduler import TaskScheduler
from .resource_manager import ResourceManager
from .mcp_coordinator import MCPCoordinator
from .monitoring_service import MonitoringService
from .automation_core import AutomationCore, CoreConfig, CoreStatus

__version__ = "4.5.0"
__author__ = "Manus AI"

# 导出主要类
__all__ = [
    "WorkflowEngine",
    "TaskScheduler", 
    "ResourceManager",
    "MCPCoordinator",
    "MonitoringService",
    "AutomationCore",
    "CoreConfig",
    "CoreStatus"
]

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "build_type": "edge_optimized",
    "target_platform": "macos",
    "integration_target": "claudeditor_4.5",
    "features": [
        "workflow_execution",
        "task_scheduling",
        "resource_management", 
        "mcp_coordination",
        "real_time_monitoring",
        "edge_cloud_sync"
    ]
}

def get_version_info():
    """获取版本信息"""
    return VERSION_INFO

def initialize_core(config=None):
    """初始化PowerAutomation Core"""
    return AutomationCore(config)

