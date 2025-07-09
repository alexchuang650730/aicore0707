"""
Release Trigger MCP - 发布触发器MCP
负责监控代码变更并自动触发发布流程
"""

from .release_trigger_engine import ReleaseTriggerEngine

__all__ = ["ReleaseTriggerEngine"]

__version__ = "1.0.0"
__author__ = "aicore0707"
__description__ = "ClaudeEditor发布触发引擎"

