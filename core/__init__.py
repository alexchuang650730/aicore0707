"""
Core 模块初始化
包含所有核心组件
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加组件目录
components_dir = os.path.join(current_dir, "components")
if components_dir not in sys.path:
    sys.path.insert(0, components_dir)

# 添加mirror_code目录
mirror_code_dir = os.path.join(current_dir, "mirror_code")
if mirror_code_dir not in sys.path:
    sys.path.insert(0, mirror_code_dir)

