"""
Test MCP - PowerAutomation测试组件
专门用于ClaudEditor的自动化测试和质量保证

主要功能:
- 自动化测试套件执行
- 性能基准测试
- 兼容性测试
- 安全测试
- 测试报告生成
- CI/CD集成

版本: 1.0.0
作者: PowerAutomation Team
"""

from .test_mcp_engine import TestMCPEngine
from .test_suites import *
from .reports import TestReportGenerator
from .config import TestConfig

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

# 导出主要类
__all__ = [
    'TestMCPEngine',
    'TestReportGenerator', 
    'TestConfig',
    'CoreFunctionalityTests',
    'AIFunctionalityTests',
    'UIIntegrationTests',
    'PerformanceTests',
    'CompatibilityTests',
    'SecurityTests'
]

# 组件信息
COMPONENT_INFO = {
    "name": "test_mcp",
    "version": __version__,
    "description": "ClaudEditor自动化测试组件",
    "capabilities": [
        "automated_testing",
        "performance_benchmarking", 
        "compatibility_testing",
        "security_scanning",
        "report_generation",
        "ci_cd_integration"
    ],
    "dependencies": [
        "pytest>=7.0.0",
        "playwright>=1.30.0",
        "locust>=2.0.0",
        "bandit>=1.7.0",
        "coverage>=6.0.0"
    ]
}

def get_component_info():
    """获取组件信息"""
    return COMPONENT_INFO

def initialize_test_mcp():
    """初始化Test MCP组件"""
    print(f"🧪 初始化Test MCP v{__version__}")
    print(f"📋 支持的测试能力: {', '.join(COMPONENT_INFO['capabilities'])}")
    
    # 创建测试引擎实例
    engine = TestMCPEngine()
    
    print("✅ Test MCP初始化完成")
    return engine

