"""
Test Suites - ClaudEditor测试套件集合
包含所有专业化的测试套件
"""

from .core_functionality_tests import CoreFunctionalityTests
from .ai_functionality_tests import AIFunctionalityTests
from .ui_integration_tests import UIIntegrationTests
from .performance_tests import PerformanceTests
from .compatibility_tests import CompatibilityTests
from .security_tests import SecurityTests

__all__ = [
    'CoreFunctionalityTests',
    'AIFunctionalityTests', 
    'UIIntegrationTests',
    'PerformanceTests',
    'CompatibilityTests',
    'SecurityTests'
]

