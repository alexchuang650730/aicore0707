"""
Claude Integration MCP - PowerAutomation v4.3.0
为ClaudEditor 4.3提供完整的Claude Code集成支持

这个MCP组件提供：
- Claude API客户端
- 代码智能分析
- AI驱动的代码补全
- 实时代码建议
- Mac平台优化集成
"""

__version__ = "4.3.0"
__author__ = "PowerAutomation Team"
__description__ = "Claude Integration MCP for ClaudEditor 4.3"

from .claude_api_client import ClaudeAPIClient
from .code_intelligence_engine import CodeIntelligenceEngine
from .monaco_claude_plugin import MonacoClaudePlugin
from .mac_integration import MacClaudeIntegration

__all__ = [
    'ClaudeAPIClient',
    'CodeIntelligenceEngine', 
    'MonacoClaudePlugin',
    'MacClaudeIntegration'
]

