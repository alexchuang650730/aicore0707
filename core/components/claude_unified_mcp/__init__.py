"""
Claude Unified MCP - 极简版本

专注做一件事：调用Claude API
不做复杂的路由、协调、管理等功能

使用方式：
    from claude_unified_mcp import ClaudeMCP
    
    claude = ClaudeMCP(api_key="your-key")
    response = await claude.call_claude("Hello, Claude!")
"""

from .claude_mcp import ClaudeMCP

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"
__description__ = "Simple Claude API MCP - 专注Claude API调用"

__all__ = ["ClaudeMCP"]

