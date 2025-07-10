"""
Mac ClaudeEditor v4.5 - 全局初始化模块
配置Python路径和模块导入
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 添加所有必要的路径到sys.path
paths_to_add = [
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "core"),
    str(PROJECT_ROOT / "core" / "components"),
    str(PROJECT_ROOT / "core" / "mirror_code"),
    str(PROJECT_ROOT / "deployment"),
    str(PROJECT_ROOT / "deployment" / "devices" / "mac" / "v4.5.0"),
    str(PROJECT_ROOT / "deployment" / "devices" / "mac" / "v4.5.0" / "core"),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# 版本信息
__version__ = "4.5.0"
__author__ = "Manus AI"

def setup_environment():
    """设置环境变量和路径"""
    # 设置项目根目录环境变量
    os.environ["AICORE_ROOT"] = str(PROJECT_ROOT)
    os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)
    
    return True

# 自动设置环境
setup_environment()

