"""
Git Integration 模块初始化
"""

try:
    from .git_manager import GitManager
    __all__ = ["GitManager"]
except ImportError:
    try:
        from git_manager import GitManager
        __all__ = ["GitManager"]
    except ImportError:
        __all__ = []

