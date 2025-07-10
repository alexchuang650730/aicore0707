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

import os
import sys

# 添加当前目录到Python路径以支持导入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 尝试导入核心组件
try:
    from .workflow_engine import WorkflowEngine
except ImportError:
    try:
        from workflow_engine import WorkflowEngine
    except ImportError:
        WorkflowEngine = None

try:
    from .task_scheduler import TaskScheduler
except ImportError:
    try:
        from task_scheduler import TaskScheduler
    except ImportError:
        TaskScheduler = None

try:
    from .resource_manager import ResourceManager
except ImportError:
    try:
        from resource_manager import ResourceManager
    except ImportError:
        ResourceManager = None

try:
    from .mcp_coordinator import MCPCoordinator
except ImportError:
    try:
        from mcp_coordinator import MCPCoordinator
    except ImportError:
        MCPCoordinator = None

try:
    from .monitoring_service import MonitoringService
except ImportError:
    try:
        from monitoring_service import MonitoringService
    except ImportError:
        MonitoringService = None

try:
    from .automation_core import AutomationCore, CoreConfig, CoreStatus
except ImportError:
    try:
        from automation_core import AutomationCore, CoreConfig, CoreStatus
    except ImportError:
        AutomationCore = None
        CoreConfig = None
        CoreStatus = None

__version__ = "4.5.0"
__author__ = "Manus AI"

# 导出主要类（只导出成功导入的类）
__all__ = []
if WorkflowEngine:
    __all__.append("WorkflowEngine")
if TaskScheduler:
    __all__.append("TaskScheduler")
if ResourceManager:
    __all__.append("ResourceManager")
if MCPCoordinator:
    __all__.append("MCPCoordinator")
if MonitoringService:
    __all__.append("MonitoringService")
if AutomationCore:
    __all__.extend(["AutomationCore", "CoreConfig", "CoreStatus"])

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
    ],
    "imported_components": __all__
}

def get_version_info():
    """获取版本信息"""
    return VERSION_INFO

def initialize_core(config=None):
    """初始化PowerAutomation Core"""
    if AutomationCore:
        return AutomationCore(config)
    else:
        raise ImportError("AutomationCore 无法导入，请检查依赖")

def check_components():
    """检查组件导入状态"""
    components = {
        "WorkflowEngine": WorkflowEngine is not None,
        "TaskScheduler": TaskScheduler is not None,
        "ResourceManager": ResourceManager is not None,
        "MCPCoordinator": MCPCoordinator is not None,
        "MonitoringService": MonitoringService is not None,
        "AutomationCore": AutomationCore is not None
    }
    
    available_count = sum(components.values())
    total_count = len(components)
    
    return {
        "components": components,
        "available": available_count,
        "total": total_count,
        "success_rate": available_count / total_count * 100
    }

