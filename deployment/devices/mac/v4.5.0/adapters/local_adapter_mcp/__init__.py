"""
Local Adapter MCP - 本地适配器MCP
支持连接Linux EC2、WSL、Mac终端的跨平台适配器
"""

import os

from .terminal_connectors import (
    EC2Connector,
    WSLConnector, 
    MacTerminalConnector,
    TerminalManager
)

from .quick_actions import (
    QuickTerminalActions,
    TerminalQuickSelector
)

__version__ = "4.5.0"
__author__ = "Manus AI"

# 导出主要类
__all__ = [
    "EC2Connector",
    "WSLConnector",
    "MacTerminalConnector", 
    "TerminalManager",
    "QuickTerminalActions",
    "TerminalQuickSelector"
]

# 支持的平台
SUPPORTED_PLATFORMS = {
    "linux_ec2": {
        "name": "Linux EC2",
        "description": "Amazon EC2 Linux实例",
        "connector": "EC2Connector",
        "protocols": ["ssh", "ssm"],
        "auth_methods": ["key", "password", "iam"]
    },
    "wsl": {
        "name": "Windows WSL",
        "description": "Windows子系统Linux",
        "connector": "WSLConnector", 
        "protocols": ["wsl", "local"],
        "auth_methods": ["local", "sudo"]
    },
    "mac_terminal": {
        "name": "Mac Terminal",
        "description": "Mac本地终端",
        "connector": "MacTerminalConnector",
        "protocols": ["local", "ssh"],
        "auth_methods": ["local", "sudo", "key"]
    }
}

# 快速连接配置
QUICK_CONNECT_PRESETS = {
    "dev_ec2": {
        "platform": "linux_ec2",
        "name": "开发环境EC2",
        "host": os.getenv("DEV_EC2_HOST", "localhost"),
        "user": "ubuntu",
        "key_file": "~/.ssh/dev-key.pem"
    },
    "local_wsl": {
        "platform": "wsl",
        "name": "本地WSL Ubuntu",
        "distribution": "Ubuntu",
        "user": "ubuntu"
    },
    "local_mac": {
        "platform": "mac_terminal",
        "name": "本地Mac终端",
        "shell": "zsh"
    }
}

