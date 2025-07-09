"""
PowerAutomation + ClaudEditor 测试框架

集成stagewise MCP + ag-ui MCP的完整UI自动化测试系统
"""

from .ui_automation_test_template import UIAutomationTestTemplate
from .stagewise_ui_tester import StagewiseUITester
from .ag_ui_controller import AGUIController
from .test_coordinator import TestCoordinator

__all__ = [
    'UIAutomationTestTemplate',
    'StagewiseUITester', 
    'AGUIController',
    'TestCoordinator'
]

# 测试配置
TEST_CONFIG = {
    'browser': {
        'headless': False,
        'window_size': (1920, 1080),
        'timeout': 30
    },
    'api': {
        'base_url': 'http://localhost:5000',
        'timeout': 10
    },
    'ui': {
        'wait_time': 2,
        'retry_count': 3,
        'screenshot_on_failure': True
    },
    'stages': {
        'setup': ['启动服务', '初始化环境', '验证连接'],
        'ui_tests': ['界面加载', '组件交互', '功能验证'],
        'api_tests': ['端点测试', '数据验证', '错误处理'],
        'integration': ['端到端流程', '性能测试', '压力测试'],
        'cleanup': ['清理数据', '关闭服务', '生成报告']
    }
}

