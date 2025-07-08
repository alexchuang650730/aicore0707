"""
插件系统模块

提供插件的管理、加载和执行功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PluginStatus(Enum):
    """插件状态枚举"""
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class Plugin:
    """插件数据结构"""
    id: str
    name: str
    version: str
    description: str
    author: str
    status: PluginStatus
    entry_point: str
    dependencies: List[str]
    metadata: Dict[str, Any]

class PluginSystem:
    """插件系统管理器"""
    
    def __init__(self):
        """初始化插件系统"""
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_hooks: Dict[str, List[Callable]] = {}
        self._initialize_default_plugins()
        logger.info("插件系统初始化完成")
    
    def _initialize_default_plugins(self):
        """初始化默认插件"""
        default_plugins = [
            Plugin(
                id="automation_plugin",
                name="自动化插件",
                version="1.0.0",
                description="提供基础自动化功能",
                author="PowerAutomation Team",
                status=PluginStatus.ACTIVE,
                entry_point="automation.main",
                dependencies=[],
                metadata={"category": "automation"}
            ),
            Plugin(
                id="integration_plugin",
                name="集成插件",
                version="1.0.0",
                description="提供第三方集成功能",
                author="PowerAutomation Team",
                status=PluginStatus.ACTIVE,
                entry_point="integration.main",
                dependencies=[],
                metadata={"category": "integration"}
            )
        ]
        
        for plugin in default_plugins:
            self.plugins[plugin.id] = plugin
    
    async def install_plugin(self, plugin_data: Dict[str, Any]) -> bool:
        """
        安装插件
        
        Args:
            plugin_data: 插件数据
            
        Returns:
            安装是否成功
        """
        try:
            plugin = Plugin(
                id=plugin_data["id"],
                name=plugin_data["name"],
                version=plugin_data["version"],
                description=plugin_data["description"],
                author=plugin_data["author"],
                status=PluginStatus.INSTALLED,
                entry_point=plugin_data["entry_point"],
                dependencies=plugin_data.get("dependencies", []),
                metadata=plugin_data.get("metadata", {})
            )
            
            self.plugins[plugin.id] = plugin
            logger.info(f"插件安装成功: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"插件安装失败: {e}")
            return False
    
    async def activate_plugin(self, plugin_id: str) -> bool:
        """
        激活插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            激活是否成功
        """
        try:
            if plugin_id not in self.plugins:
                return False
            
            plugin = self.plugins[plugin_id]
            plugin.status = PluginStatus.ACTIVE
            
            logger.info(f"插件激活成功: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"插件激活失败: {e}")
            return False
    
    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        停用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            停用是否成功
        """
        try:
            if plugin_id not in self.plugins:
                return False
            
            plugin = self.plugins[plugin_id]
            plugin.status = PluginStatus.INACTIVE
            
            logger.info(f"插件停用成功: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"插件停用失败: {e}")
            return False
    
    async def list_plugins(self) -> List[Plugin]:
        """
        列出所有插件
        
        Returns:
            插件列表
        """
        return list(self.plugins.values())
    
    async def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        获取插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件对象
        """
        return self.plugins.get(plugin_id)
    
    def register_hook(self, hook_name: str, callback: Callable):
        """
        注册插件钩子
        
        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name not in self.plugin_hooks:
            self.plugin_hooks[hook_name] = []
        
        self.plugin_hooks[hook_name].append(callback)
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        执行插件钩子
        
        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果列表
        """
        results = []
        
        if hook_name in self.plugin_hooks:
            for callback in self.plugin_hooks[hook_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        result = await callback(*args, **kwargs)
                    else:
                        result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"执行钩子失败: {e}")
        
        return results

