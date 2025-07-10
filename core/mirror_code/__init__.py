"""
Mirror Code 模块初始化
实时代码镜像和同步功能
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加子模块目录
subdirs = ["engine", "sync", "communication", "git_integration", "file_monitor"]
for subdir in subdirs:
    subdir_path = os.path.join(current_dir, subdir)
    if os.path.exists(subdir_path) and subdir_path not in sys.path:
        sys.path.insert(0, subdir_path)

# 尝试导入主要组件
try:
    from engine.mirror_engine import MirrorEngine
    from sync.sync_manager import SyncManager
    from communication.comm_manager import CommunicationManager
    from git_integration.git_manager import GitManager
    from file_monitor.file_watcher import FileWatcher
    
    __all__ = [
        "MirrorEngine",
        "SyncManager", 
        "CommunicationManager",
        "GitManager",
        "FileWatcher"
    ]
except ImportError as e:
    print(f"Warning: 无法导入Mirror Code组件: {e}")
    __all__ = []

