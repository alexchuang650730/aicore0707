"""
PowerAutomation 4.0 - 录制即测试 MCP

录制即测试(Record-as-Test)模块提供零代码测试生成能力，
通过录制用户操作自动生成测试用例，支持AI优化和智能回放。

核心功能：
- 🎬 浏览器操作录制
- 🤖 AI驱动测试生成
- 📹 视频录制和回放
- 🔍 智能验证点生成
- 🚀 Stagewise测试集成
- 💡 AI优化建议

作者: PowerAutomation 4.0 Team
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PowerAutomation 4.0 Team"

from .record_as_test_service import RecordAsTestService
from .browser_recorder import BrowserRecorder
from .test_generator import TestGenerator
from .playback_engine import PlaybackEngine
from .ai_optimizer import AIOptimizer

__all__ = [
    "RecordAsTestService",
    "BrowserRecorder", 
    "TestGenerator",
    "PlaybackEngine",
    "AIOptimizer"
]

