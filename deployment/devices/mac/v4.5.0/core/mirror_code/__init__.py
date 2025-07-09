"""
Mirror Code Core Module - Mirror Code核心模块
提供代码镜像、同步和协作编辑的核心功能
"""

from .engine.mirror_engine import MirrorEngine
from .sync.sync_manager import SyncManager
from .storage.storage_manager import StorageManager
from .communication.comm_manager import CommunicationManager

# 版本信息
__version__ = "1.0.0"
__author__ = "ClaudeEditor Team"

# 导出主要类
__all__ = [
    "MirrorEngine",
    "SyncManager", 
    "StorageManager",
    "CommunicationManager"
]

# 模块级配置
DEFAULT_CONFIG = {
    "sync_interval": 5,
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "compression_enabled": True,
    "encryption_enabled": True,
    "debug_mode": False
}

