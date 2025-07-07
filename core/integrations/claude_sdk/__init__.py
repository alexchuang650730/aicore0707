"""
PowerAutomation 4.0 Claude SDK Module
Claude Code SDK通信模块，支持并行对话和文本交互
"""

from .claude_client import ClaudeClient
from .conversation_manager import ConversationManager
from .message_processor import MessageProcessor

__version__ = "4.0.0"
__all__ = ["ClaudeClient", "ConversationManager", "MessageProcessor"]

