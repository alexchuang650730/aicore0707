"""
Communication Manager 模块初始化
"""

try:
    from .comm_manager import CommunicationManager
    __all__ = ["CommunicationManager"]
except ImportError:
    try:
        from comm_manager import CommunicationManager
        __all__ = ["CommunicationManager"]
    except ImportError:
        __all__ = []

