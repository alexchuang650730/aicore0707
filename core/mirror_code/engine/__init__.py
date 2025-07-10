"""
Mirror Engine 模块初始化
"""

try:
    from .mirror_engine import MirrorEngine, launch_mirror
    __all__ = ["MirrorEngine", "launch_mirror"]
except ImportError:
    try:
        from mirror_engine import MirrorEngine, launch_mirror
        __all__ = ["MirrorEngine", "launch_mirror"]
    except ImportError:
        __all__ = []

