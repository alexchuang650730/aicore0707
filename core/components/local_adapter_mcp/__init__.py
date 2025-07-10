"""
Local Adapter MCP 模块初始化
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 尝试导入主要组件
try:
    from .local_adapter_engine import LocalAdapterEngine
    __all__ = ["LocalAdapterEngine"]
except ImportError:
    try:
        from local_adapter_engine import LocalAdapterEngine
        __all__ = ["LocalAdapterEngine"]
    except ImportError:
        __all__ = []

