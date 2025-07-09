"""
Mac Integration - PowerAutomation v4.3.0
为ClaudEditor 4.3提供macOS平台特定的集成功能
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import platform

@dataclass
class MacNotification:
    """Mac通知数据结构"""
    title: str
    message: str
    subtitle: Optional[str] = None
    sound: Optional[str] = None
    action_button: Optional[str] = None

@dataclass
class MacShortcut:
    """Mac快捷键数据结构"""
    key_combination: str
    description: str
    action: str
    enabled: bool = True

class MacClaudeIntegration:
    """
    Mac平台Claude集成
    提供macOS特定的系统集成功能
    """
    
    def __init__(self):
        """初始化Mac集成组件"""
        self.logger = logging.getLogger(__name__)
        
        # 检查是否在macOS上运行
        self.is_macos = platform.system() == 'Darwin'
        if not self.is_macos:
            self.logger.warning("Mac integration initialized on non-macOS system")
        
        # 配置
        self.config = {
            'notifications_enabled': True,
            'dock_integration_enabled': True,
            'menu_bar_enabled': True,
            'shortcuts_enabled': True,
            'file_associations_enabled': True,
            'app_name': 'ClaudEditor 4.3',
            'bundle_id': 'com.powerautomation.claudeditor',
            'notification_sound': 'default'
        }
        
        # 快捷键映射
        self.shortcuts = {
            'cmd+shift+r': MacShortcut(
                key_combination='cmd+shift+r',
                description='Toggle recording',
                action='toggle_recording'
            ),
            'cmd+t': MacShortcut(
                key_combination='cmd+t',
                description='Quick test',
                action='quick_test'
            ),
            'cmd+shift+a': MacShortcut(
                key_combination='cmd+shift+a',
                description='Open AI chat',
                action='open_ai_chat'
            ),
            'cmd+shift+c': MacShortcut(
                key_combination='cmd+shift+c',
                description='Code completion',
                action='code_completion'
            ),
            'cmd+shift+e': MacShortcut(
                key_combination='cmd+shift+e',
                description='Explain code',
                action='explain_code'
            )
        }
        
        # 回调函数
        self.shortcut_callbacks: Dict[str, Callable] = {}
        self.notification_callbacks: Dict[str, Callable] = {}
        
        # 状态
        self.dock_badge_count = 0
        self.menu_bar_status = "Ready"
        
        # 统计信息
        self.stats = {
            'notifications_sent': 0,
            'shortcuts_triggered': 0,
            'dock_updates': 0,
            'menu_bar_updates': 0
        }
    
    def configure(self, config: Dict[str, Any]):
        """
        配置Mac集成
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        self.logger.info(f"Mac integration configured: {config}")
    
    def register_shortcut_callback(self, action: str, callback: Callable):
        """
        注册快捷键回调
        
        Args:
            action: 动作名称
            callback: 回调函数
        """
        self.shortcut_callbacks[action] = callback
        self.logger.debug(f"Registered shortcut callback for action: {action}")
    
    def register_notification_callback(self, notification_type: str, callback: Callable):
        """
        注册通知回调
        
        Args:
            notification_type: 通知类型
            callback: 回调函数
        """
        self.notification_callbacks[notification_type] = callback
        self.logger.debug(f"Registered notification callback for type: {notification_type}")
    
    async def send_notification(self, notification: MacNotification) -> bool:
        """
        发送macOS通知
        
        Args:
            notification: 通知对象
            
        Returns:
            是否发送成功
        """
        if not self.config['notifications_enabled'] or not self.is_macos:
            return False
        
        try:
            # 构建osascript命令
            script_parts = [
                'osascript', '-e',
                f'display notification "{notification.message}" '
                f'with title "{notification.title}"'
            ]
            
            if notification.subtitle:
                script_parts[-1] += f' subtitle "{notification.subtitle}"'
            
            if notification.sound:
                script_parts[-1] += f' sound name "{notification.sound}"'
            elif self.config['notification_sound'] != 'none':
                script_parts[-1] += f' sound name "{self.config["notification_sound"]}"'
            
            # 执行通知命令
            result = await asyncio.create_subprocess_exec(
                *script_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.stats['notifications_sent'] += 1
                self.logger.debug(f"Notification sent: {notification.title}")
                return True
            else:
                self.logger.error(f"Notification failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    async def update_dock_badge(self, count: int) -> bool:
        """
        更新Dock图标徽章
        
        Args:
            count: 徽章数字
            
        Returns:
            是否更新成功
        """
        if not self.config['dock_integration_enabled'] or not self.is_macos:
            return False
        
        try:
            self.dock_badge_count = count
            
            # 使用osascript更新Dock徽章
            script = f'''
            tell application "System Events"
                tell application process "{self.config['app_name']}"
                    set badge of dock item 1 to "{count if count > 0 else ""}"
                end tell
            end tell
            '''
            
            result = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.stats['dock_updates'] += 1
                self.logger.debug(f"Dock badge updated: {count}")
                return True
            else:
                self.logger.error(f"Dock badge update failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update dock badge: {e}")
            return False
    
    async def update_menu_bar_status(self, status: str) -> bool:
        """
        更新菜单栏状态
        
        Args:
            status: 状态文本
            
        Returns:
            是否更新成功
        """
        if not self.config['menu_bar_enabled'] or not self.is_macos:
            return False
        
        try:
            self.menu_bar_status = status
            self.stats['menu_bar_updates'] += 1
            
            # 这里可以实现实际的菜单栏更新逻辑
            # 例如通过NSStatusBar或其他方式
            self.logger.debug(f"Menu bar status updated: {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update menu bar status: {e}")
            return False
    
    def setup_file_associations(self) -> bool:
        """
        设置文件关联
        
        Returns:
            是否设置成功
        """
        if not self.config['file_associations_enabled'] or not self.is_macos:
            return False
        
        try:
            # 支持的文件类型
            file_types = [
                '.py', '.pyw',      # Python
                '.js', '.jsx',      # JavaScript
                '.ts', '.tsx',      # TypeScript
                '.md',              # Markdown
                '.json',            # JSON
                '.yaml', '.yml',    # YAML
                '.txt',             # Text
                '.log'              # Log files
            ]
            
            # 这里可以实现文件关联的设置
            # 在实际应用中，这通常通过Info.plist文件配置
            self.logger.info(f"File associations configured for: {', '.join(file_types)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup file associations: {e}")
            return False
    
    async def handle_shortcut(self, key_combination: str) -> bool:
        """
        处理快捷键
        
        Args:
            key_combination: 快捷键组合
            
        Returns:
            是否处理成功
        """
        if not self.config['shortcuts_enabled']:
            return False
        
        try:
            shortcut = self.shortcuts.get(key_combination.lower())
            if not shortcut or not shortcut.enabled:
                return False
            
            # 执行回调
            callback = self.shortcut_callbacks.get(shortcut.action)
            if callback:
                await callback()
                self.stats['shortcuts_triggered'] += 1
                self.logger.debug(f"Shortcut triggered: {key_combination} -> {shortcut.action}")
                return True
            else:
                self.logger.warning(f"No callback registered for action: {shortcut.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to handle shortcut {key_combination}: {e}")
            return False
    
    async def show_ai_progress(self, message: str, progress: float = -1) -> bool:
        """
        显示AI处理进度
        
        Args:
            message: 进度消息
            progress: 进度百分比 (-1表示不确定进度)
            
        Returns:
            是否显示成功
        """
        try:
            # 更新菜单栏状态
            await self.update_menu_bar_status(f"AI: {message}")
            
            # 如果有具体进度，可以显示进度通知
            if progress >= 0:
                notification = MacNotification(
                    title="Claude AI",
                    message=f"{message} ({progress:.0f}%)",
                    sound=None  # 静默通知
                )
                await self.send_notification(notification)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to show AI progress: {e}")
            return False
    
    async def notify_ai_completion(self, task: str, result: str) -> bool:
        """
        通知AI任务完成
        
        Args:
            task: 任务名称
            result: 结果摘要
            
        Returns:
            是否通知成功
        """
        try:
            notification = MacNotification(
                title="Claude AI Complete",
                message=f"{task} finished",
                subtitle=result[:50] + "..." if len(result) > 50 else result,
                sound="Glass"  # 完成音效
            )
            
            success = await self.send_notification(notification)
            
            # 重置菜单栏状态
            await self.update_menu_bar_status("Ready")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to notify AI completion: {e}")
            return False
    
    async def handle_file_open(self, file_path: str) -> bool:
        """
        处理文件打开事件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否处理成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                await self.send_notification(MacNotification(
                    title="File Not Found",
                    message=f"Cannot open {os.path.basename(file_path)}",
                    sound="Basso"
                ))
                return False
            
            # 触发文件打开回调
            callback = self.notification_callbacks.get('file_open')
            if callback:
                await callback(file_path)
            
            # 发送成功通知
            await self.send_notification(MacNotification(
                title="File Opened",
                message=f"Opened {os.path.basename(file_path)}",
                sound=None
            ))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle file open: {e}")
            return False
    
    def create_menu_bar_menu(self) -> Dict[str, Any]:
        """
        创建菜单栏菜单结构
        
        Returns:
            菜单结构字典
        """
        return {
            'title': self.config['app_name'],
            'items': [
                {
                    'title': f'Status: {self.menu_bar_status}',
                    'enabled': False
                },
                {'separator': True},
                {
                    'title': 'Open ClaudEditor',
                    'action': 'open_main_window',
                    'shortcut': 'cmd+o'
                },
                {
                    'title': 'New File',
                    'action': 'new_file',
                    'shortcut': 'cmd+n'
                },
                {'separator': True},
                {
                    'title': 'AI Assistant',
                    'submenu': [
                        {
                            'title': 'Open AI Chat',
                            'action': 'open_ai_chat',
                            'shortcut': 'cmd+shift+a'
                        },
                        {
                            'title': 'Code Completion',
                            'action': 'code_completion',
                            'shortcut': 'cmd+shift+c'
                        },
                        {
                            'title': 'Explain Code',
                            'action': 'explain_code',
                            'shortcut': 'cmd+shift+e'
                        }
                    ]
                },
                {
                    'title': 'Recording',
                    'submenu': [
                        {
                            'title': 'Toggle Recording',
                            'action': 'toggle_recording',
                            'shortcut': 'cmd+shift+r'
                        },
                        {
                            'title': 'Quick Test',
                            'action': 'quick_test',
                            'shortcut': 'cmd+t'
                        }
                    ]
                },
                {'separator': True},
                {
                    'title': 'Preferences...',
                    'action': 'open_preferences',
                    'shortcut': 'cmd+,'
                },
                {'separator': True},
                {
                    'title': 'Quit ClaudEditor',
                    'action': 'quit_application',
                    'shortcut': 'cmd+q'
                }
            ]
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        info = {
            'platform': platform.system(),
            'version': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'is_macos': self.is_macos
        }
        
        if self.is_macos:
            try:
                # 获取macOS版本信息
                result = subprocess.run(
                    ['sw_vers', '-productVersion'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info['macos_version'] = result.stdout.strip()
                
                # 获取硬件信息
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.model'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info['hardware_model'] = result.stdout.strip()
                
            except Exception as e:
                self.logger.error(f"Failed to get system info: {e}")
        
        return info
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Mac集成统计信息"""
        return {
            **self.stats,
            'dock_badge_count': self.dock_badge_count,
            'menu_bar_status': self.menu_bar_status,
            'shortcuts_count': len(self.shortcuts),
            'enabled_shortcuts': len([s for s in self.shortcuts.values() if s.enabled]),
            'system_info': self.get_system_info(),
            'config': self.config
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清除Dock徽章
            await self.update_dock_badge(0)
            
            # 重置菜单栏状态
            await self.update_menu_bar_status("Stopped")
            
            self.logger.info("Mac integration cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

# 使用示例
async def main():
    """使用示例"""
    mac_integration = MacClaudeIntegration()
    
    # 配置
    mac_integration.configure({
        'notifications_enabled': True,
        'app_name': 'ClaudEditor 4.3 Test'
    })
    
    # 注册回调
    async def handle_ai_chat():
        print("AI Chat opened!")
    
    async def handle_recording():
        print("Recording toggled!")
    
    mac_integration.register_shortcut_callback('open_ai_chat', handle_ai_chat)
    mac_integration.register_shortcut_callback('toggle_recording', handle_recording)
    
    # 发送测试通知
    notification = MacNotification(
        title="ClaudEditor 4.3",
        message="Mac integration test",
        subtitle="Testing notification system"
    )
    await mac_integration.send_notification(notification)
    
    # 更新Dock徽章
    await mac_integration.update_dock_badge(5)
    
    # 显示AI进度
    await mac_integration.show_ai_progress("Analyzing code", 50)
    
    # 模拟快捷键
    await mac_integration.handle_shortcut('cmd+shift+a')
    
    # 获取统计信息
    stats = mac_integration.get_stats()
    print(f"Mac integration stats: {json.dumps(stats, indent=2)}")
    
    # 清理
    await mac_integration.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

