"""
Terminal Selector - 终端选择器UI组件
ClaudeEditor 4.5快速区域的终端连接选择器
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from adapters.local_adapter_mcp import (
    TerminalManager, 
    ConnectionConfig,
    SUPPORTED_PLATFORMS,
    QUICK_CONNECT_PRESETS
)

class TerminalSelector:
    """终端选择器"""
    
    def __init__(self, terminal_manager: TerminalManager):
        self.terminal_manager = terminal_manager
        self.logger = logging.getLogger(__name__)
        self.current_connection = None
        self.connection_presets = QUICK_CONNECT_PRESETS.copy()
        self.custom_connections = {}
        self.ui_callbacks = {}
        
    def register_ui_callback(self, event: str, callback: Callable):
        """注册UI回调函数"""
        if event not in self.ui_callbacks:
            self.ui_callbacks[event] = []
        self.ui_callbacks[event].append(callback)
    
    async def _emit_ui_event(self, event: str, data: Any):
        """触发UI事件"""
        if event in self.ui_callbacks:
            for callback in self.ui_callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"UI回调错误 ({event}): {e}")
    
    def get_available_platforms(self) -> Dict[str, Dict[str, Any]]:
        """获取可用平台"""
        return SUPPORTED_PLATFORMS
    
    def get_connection_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取连接预设"""
        all_presets = {}
        all_presets.update(self.connection_presets)
        all_presets.update(self.custom_connections)
        return all_presets
    
    def add_custom_connection(self, name: str, config: Dict[str, Any]):
        """添加自定义连接"""
        self.custom_connections[name] = config
        self.logger.info(f"添加自定义连接: {name}")
        
        # 触发UI更新事件
        asyncio.create_task(self._emit_ui_event("connections_updated", {
            "action": "added",
            "name": name,
            "config": config
        }))
    
    def remove_custom_connection(self, name: str) -> bool:
        """移除自定义连接"""
        if name in self.custom_connections:
            del self.custom_connections[name]
            self.logger.info(f"移除自定义连接: {name}")
            
            # 触发UI更新事件
            asyncio.create_task(self._emit_ui_event("connections_updated", {
                "action": "removed",
                "name": name
            }))
            return True
        return False
    
    async def quick_connect(self, preset_name: str) -> str:
        """快速连接到预设"""
        preset = self.get_connection_presets().get(preset_name)
        if not preset:
            raise ValueError(f"连接预设不存在: {preset_name}")
        
        # 创建连接配置
        config = self._create_connection_config(preset)
        
        # 创建连接
        connection_id = await self.terminal_manager.create_connection(config)
        
        # 建立连接
        success = await self.terminal_manager.connect(connection_id)
        
        if success:
            self.current_connection = connection_id
            self.logger.info(f"快速连接成功: {preset_name} -> {connection_id}")
            
            # 触发UI事件
            await self._emit_ui_event("connection_established", {
                "connection_id": connection_id,
                "preset_name": preset_name,
                "platform": preset["platform"]
            })
            
            return connection_id
        else:
            # 连接失败，清理
            await self.terminal_manager.remove_connection(connection_id)
            raise Exception(f"快速连接失败: {preset_name}")
    
    async def connect_with_config(self, config_dict: Dict[str, Any]) -> str:
        """使用自定义配置连接"""
        # 创建连接配置
        config = ConnectionConfig(**config_dict)
        
        # 创建连接
        connection_id = await self.terminal_manager.create_connection(config)
        
        # 建立连接
        success = await self.terminal_manager.connect(connection_id)
        
        if success:
            self.current_connection = connection_id
            self.logger.info(f"自定义连接成功: {connection_id}")
            
            # 触发UI事件
            await self._emit_ui_event("connection_established", {
                "connection_id": connection_id,
                "platform": config.platform,
                "custom": True
            })
            
            return connection_id
        else:
            # 连接失败，清理
            await self.terminal_manager.remove_connection(connection_id)
            raise Exception("自定义连接失败")
    
    async def disconnect_current(self) -> bool:
        """断开当前连接"""
        if not self.current_connection:
            return True
        
        try:
            success = await self.terminal_manager.disconnect(self.current_connection)
            
            if success:
                old_connection = self.current_connection
                self.current_connection = None
                
                # 触发UI事件
                await self._emit_ui_event("connection_disconnected", {
                    "connection_id": old_connection
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
            return False
    
    async def switch_connection(self, connection_id: str) -> bool:
        """切换到指定连接"""
        # 检查连接是否存在且已连接
        status = self.terminal_manager.get_connection_status(connection_id)
        if not status or status.get("status") != "connected":
            return False
        
        # 断开当前连接
        if self.current_connection and self.current_connection != connection_id:
            await self.disconnect_current()
        
        # 设置新的当前连接
        self.current_connection = connection_id
        
        # 触发UI事件
        await self._emit_ui_event("connection_switched", {
            "connection_id": connection_id
        })
        
        return True
    
    async def execute_quick_command(self, command: str, timeout: Optional[int] = None) -> Any:
        """在当前连接上执行快速命令"""
        if not self.current_connection:
            raise Exception("没有活跃的连接")
        
        result = await self.terminal_manager.execute_command(
            self.current_connection, 
            command, 
            timeout
        )
        
        # 触发UI事件
        await self._emit_ui_event("command_executed", {
            "connection_id": self.current_connection,
            "command": command,
            "result": {
                "exit_code": result.exit_code,
                "stdout": result.stdout[:1000],  # 限制输出长度
                "stderr": result.stderr[:1000],
                "execution_time": result.execution_time
            }
        })
        
        return result
    
    def get_current_connection_info(self) -> Optional[Dict[str, Any]]:
        """获取当前连接信息"""
        if not self.current_connection:
            return None
        
        return self.terminal_manager.get_connection_status(self.current_connection)
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接状态"""
        return self.terminal_manager.get_connection_status()
    
    def get_active_connections(self) -> List[str]:
        """获取活跃连接列表"""
        return self.terminal_manager.get_active_connections()
    
    async def health_check_current(self) -> bool:
        """检查当前连接健康状态"""
        if not self.current_connection:
            return False
        
        try:
            results = await self.terminal_manager.health_check(self.current_connection)
            return results.get(self.current_connection, False)
        except Exception:
            return False
    
    async def get_system_info_current(self) -> Optional[Dict[str, Any]]:
        """获取当前连接的系统信息"""
        if not self.current_connection:
            return None
        
        try:
            return await self.terminal_manager.get_system_info(self.current_connection)
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return None
    
    def _create_connection_config(self, preset: Dict[str, Any]) -> ConnectionConfig:
        """从预设创建连接配置"""
        platform = preset["platform"]
        
        # 基础配置
        config_dict = {
            "platform": platform,
            "name": preset["name"]
        }
        
        # 平台特定配置
        if platform == "linux_ec2":
            config_dict.update({
                "host": preset.get("host"),
                "user": preset.get("user", "ubuntu"),
                "key_file": preset.get("key_file"),
                "port": preset.get("port", 22),
                "extra_params": {
                    "method": preset.get("method", "ssh"),
                    "instance_id": preset.get("instance_id"),
                    "region": preset.get("region", "us-east-1")
                }
            })
        
        elif platform == "wsl":
            config_dict.update({
                "user": preset.get("user"),
                "working_dir": preset.get("working_dir"),
                "extra_params": {
                    "distribution": preset.get("distribution", "Ubuntu"),
                    "version": preset.get("version", "2")
                }
            })
        
        elif platform == "mac_terminal":
            config_dict.update({
                "host": preset.get("host"),
                "user": preset.get("user"),
                "key_file": preset.get("key_file"),
                "port": preset.get("port"),
                "working_dir": preset.get("working_dir"),
                "extra_params": {
                    "shell": preset.get("shell", "zsh"),
                    "type": preset.get("type", "local"),
                    "terminal_app": preset.get("terminal_app", "Terminal")
                }
            })
        
        return ConnectionConfig(**config_dict)
    
    def get_quick_actions(self) -> List[Dict[str, Any]]:
        """获取快速操作列表"""
        actions = [
            {
                "id": "connect_ec2",
                "name": "连接EC2",
                "description": "快速连接到EC2实例",
                "icon": "cloud",
                "platform": "linux_ec2",
                "action": "quick_connect",
                "preset": "dev_ec2"
            },
            {
                "id": "connect_wsl",
                "name": "连接WSL",
                "description": "连接到Windows子系统Linux",
                "icon": "terminal",
                "platform": "wsl",
                "action": "quick_connect",
                "preset": "local_wsl"
            },
            {
                "id": "connect_mac",
                "name": "Mac终端",
                "description": "打开Mac本地终端",
                "icon": "laptop",
                "platform": "mac_terminal",
                "action": "quick_connect",
                "preset": "local_mac"
            },
            {
                "id": "system_info",
                "name": "系统信息",
                "description": "获取当前系统信息",
                "icon": "info",
                "action": "get_system_info",
                "requires_connection": True
            },
            {
                "id": "health_check",
                "name": "健康检查",
                "description": "检查连接健康状态",
                "icon": "heart",
                "action": "health_check",
                "requires_connection": True
            },
            {
                "id": "disconnect",
                "name": "断开连接",
                "description": "断开当前连接",
                "icon": "disconnect",
                "action": "disconnect",
                "requires_connection": True
            }
        ]
        
        return actions
    
    def get_common_commands(self) -> Dict[str, List[Dict[str, str]]]:
        """获取常用命令"""
        return {
            "system": [
                {"name": "系统信息", "command": "uname -a", "description": "显示系统信息"},
                {"name": "磁盘使用", "command": "df -h", "description": "显示磁盘使用情况"},
                {"name": "内存使用", "command": "free -h", "description": "显示内存使用情况"},
                {"name": "进程列表", "command": "ps aux", "description": "显示进程列表"},
                {"name": "网络连接", "command": "netstat -tuln", "description": "显示网络连接"}
            ],
            "files": [
                {"name": "列出文件", "command": "ls -la", "description": "列出当前目录文件"},
                {"name": "当前目录", "command": "pwd", "description": "显示当前目录"},
                {"name": "磁盘使用", "command": "du -sh *", "description": "显示目录大小"},
                {"name": "查找文件", "command": "find . -name '*.txt'", "description": "查找文本文件"},
                {"name": "文件权限", "command": "ls -l", "description": "显示文件权限"}
            ],
            "network": [
                {"name": "网络配置", "command": "ifconfig", "description": "显示网络配置"},
                {"name": "路由表", "command": "route -n", "description": "显示路由表"},
                {"name": "DNS查询", "command": "nslookup google.com", "description": "DNS查询"},
                {"name": "网络测试", "command": "ping -c 4 google.com", "description": "网络连通性测试"},
                {"name": "端口扫描", "command": "nmap localhost", "description": "端口扫描"}
            ],
            "development": [
                {"name": "Git状态", "command": "git status", "description": "Git仓库状态"},
                {"name": "Python版本", "command": "python --version", "description": "Python版本"},
                {"name": "Node版本", "command": "node --version", "description": "Node.js版本"},
                {"name": "Docker状态", "command": "docker ps", "description": "Docker容器状态"},
                {"name": "环境变量", "command": "env", "description": "显示环境变量"}
            ]
        }
    
    async def execute_common_command(self, category: str, command_name: str) -> Any:
        """执行常用命令"""
        commands = self.get_common_commands()
        
        if category not in commands:
            raise ValueError(f"命令分类不存在: {category}")
        
        command_info = None
        for cmd in commands[category]:
            if cmd["name"] == command_name:
                command_info = cmd
                break
        
        if not command_info:
            raise ValueError(f"命令不存在: {command_name}")
        
        return await self.execute_quick_command(command_info["command"])
    
    def get_selector_status(self) -> Dict[str, Any]:
        """获取选择器状态"""
        return {
            "current_connection": self.current_connection,
            "current_connection_info": self.get_current_connection_info(),
            "total_connections": len(self.get_all_connections()),
            "active_connections": len(self.get_active_connections()),
            "available_platforms": list(SUPPORTED_PLATFORMS.keys()),
            "connection_presets": len(self.get_connection_presets()),
            "custom_connections": len(self.custom_connections)
        }

