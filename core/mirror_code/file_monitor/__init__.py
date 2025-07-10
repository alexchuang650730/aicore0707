"""
File Monitor 模块初始化
"""

try:
    from .file_watcher import FileWatcher
    __all__ = ["FileWatcher"]
except ImportError:
    try:
        from file_watcher import FileWatcher
        __all__ = ["FileWatcher"]
    except ImportError:
        __all__ = []

