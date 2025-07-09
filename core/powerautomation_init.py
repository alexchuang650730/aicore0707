"""
PowerAutomation 4.0 Main Module
"""

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"
__description__ = "智能自动化开发平台"

# 导入主要组件
from .smart_router_mcp import SmartRouter
from .mcp_coordinator import MCPCoordinator
from .agent_squad import AgentSquad

__all__ = [
    "SmartRouter",
    "MCPCoordinator", 
    "AgentSquad"
]

