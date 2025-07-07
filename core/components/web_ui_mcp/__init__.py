"""
PowerAutomation 4.0 Web UI MCP Module

This module provides web-based user interface components integrated with MCP architecture,
including Monaco Editor, GitHub File Explorer, and authentication systems.

Components:
- SmartUI Adapter: Core web UI integration
- Monaco Integration: Professional code editor
- GitHub Explorer: Repository file browsing
- Permission Manager: Three-role permission system
- Realtime Sync: Real-time collaboration
"""

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

from .smartui_adapter import SmartUIAdapter
from .monaco_integration import MonacoIntegration
from .github_explorer import GitHubExplorer
from .permission_manager import PermissionManager
from .realtime_sync import RealtimeSync

__all__ = [
    "SmartUIAdapter",
    "MonacoIntegration", 
    "GitHubExplorer",
    "PermissionManager",
    "RealtimeSync"
]

