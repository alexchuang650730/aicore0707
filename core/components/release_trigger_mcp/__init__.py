"""
Release Trigger MCP - PowerAutomation发布触发器组件
负责监控和触发ClaudEditor的自动化发布流程

主要功能:
- Git标签监控
- 发布条件检查
- 自动化测试触发
- 部署流程控制
- 通知和报告

版本: 1.0.0
作者: PowerAutomation Team
"""

from .release_trigger_engine import ReleaseTriggerEngine
from .git_monitor import GitMonitor
from .deployment_controller import DeploymentController
from .notification_manager import NotificationManager

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

# 导出主要类
__all__ = [
    'ReleaseTriggerEngine',
    'GitMonitor',
    'DeploymentController',
    'NotificationManager'
]

# 组件信息
COMPONENT_INFO = {
    "name": "release_trigger_mcp",
    "version": __version__,
    "description": "ClaudEditor发布触发器和部署控制组件",
    "capabilities": [
        "git_monitoring",
        "release_triggering",
        "deployment_control",
        "quality_gating",
        "notification_management"
    ],
    "dependencies": [
        "GitPython>=3.1.0",
        "PyYAML>=6.0",
        "requests>=2.28.0",
        "schedule>=1.2.0"
    ]
}

def get_component_info():
    """获取组件信息"""
    return COMPONENT_INFO

def initialize_release_trigger_mcp():
    """初始化Release Trigger MCP组件"""
    print(f"🚀 初始化Release Trigger MCP v{__version__}")
    print(f"📋 支持的功能: {', '.join(COMPONENT_INFO['capabilities'])}")
    
    # 创建发布触发引擎实例
    engine = ReleaseTriggerEngine()
    
    print("✅ Release Trigger MCP初始化完成")
    return engine

