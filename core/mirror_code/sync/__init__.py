"""
Sync Manager 模块初始化
"""

try:
    from .sync_manager import SyncManager
    __all__ = ["SyncManager"]
except ImportError:
    try:
        from sync_manager import SyncManager
        __all__ = ["SyncManager"]
    except ImportError:
        __all__ = []

