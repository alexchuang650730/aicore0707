"""
PowerAutomation 核心模块

基于已完成的Local Adapter MCP和6大专业智能体，
实现统一的主控制器和智能任务分析系统。

核心组件:
- MainController: 统一主控制器
- TaskAnalyzer: 智能任务分析器  
- IntelligentRouter: 智能路由器
- ResultIntegrator: 结果整合器
- PerformanceMonitor: 性能监控器
- MCPCoordinatorUnified: 统一MCP协调器
"""

__version__ = "2.0.0"
__author__ = "PowerAutomation Team"

from .main_controller import MainController
from .task_analyzer import TaskAnalyzer
from .result_integrator import ResultIntegrator
from .performance_monitor import PerformanceMonitor

__all__ = [
    "MainController",
    "TaskAnalyzer", 
    "ResultIntegrator",
    "PerformanceMonitor"
]

