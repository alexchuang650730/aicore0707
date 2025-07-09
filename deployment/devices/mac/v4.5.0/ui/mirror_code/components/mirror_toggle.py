"""
Mirror Toggle Component - Mirror Code开关UI组件
提供用户友好的Mirror Code功能开关控制
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

class MirrorStatus(Enum):
    """Mirror状态枚举"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    SYNCING = "syncing"
    ERROR = "error"
    OFFLINE = "offline"

class MirrorToggle:
    """Mirror Code开关组件"""
    
    def __init__(self, mirror_engine=None):
        self.logger = logging.getLogger(__name__)
        self.mirror_engine = mirror_engine
        self.status = MirrorStatus.DISABLED
        self.last_sync_time = None
        self.sync_count = 0
        self.error_message = None
        
        # UI状态
        self.is_enabled = False
        self.is_syncing = False
        self.show_settings = False
        
        # 事件回调
        self.on_status_change = None
        self.on_toggle_change = None
        self.on_sync_complete = None
        self.on_error = None
        
        # 配置选项
        self.auto_sync = True
        self.sync_interval = 5  # 秒
        self.show_notifications = True
        self.sync_on_save = True
        
    def set_mirror_engine(self, engine):
        """设置Mirror引擎"""
        self.mirror_engine = engine
        if engine:
            # 注册引擎事件
            engine.on_sync_start = self._on_sync_start
            engine.on_sync_complete = self._on_sync_complete
            engine.on_sync_error = self._on_sync_error
            engine.on_status_change = self._on_engine_status_change
    
    async def toggle_mirror(self) -> bool:
        """切换Mirror状态"""
        try:
            if self.is_enabled:
                return await self.disable_mirror()
            else:
                return await self.enable_mirror()
        except Exception as e:
            self.logger.error(f"切换Mirror状态失败: {e}")
            await self._set_error_status(str(e))
            return False
    
    async def enable_mirror(self) -> bool:
        """启用Mirror Code"""
        self.logger.info("启用Mirror Code...")
        
        try:
            if not self.mirror_engine:
                raise Exception("Mirror引擎未初始化")
            
            # 启用引擎
            success = await self.mirror_engine.start()
            
            if success:
                self.is_enabled = True
                await self._set_status(MirrorStatus.ENABLED)
                
                # 触发回调
                if self.on_toggle_change:
                    await self._safe_callback(self.on_toggle_change, True)
                
                # 开始自动同步
                if self.auto_sync:
                    asyncio.create_task(self._start_auto_sync())
                
                self.logger.info("Mirror Code已启用")
                return True
            else:
                raise Exception("Mirror引擎启动失败")
                
        except Exception as e:
            self.logger.error(f"启用Mirror Code失败: {e}")
            await self._set_error_status(str(e))
            return False
    
    async def disable_mirror(self) -> bool:
        """禁用Mirror Code"""
        self.logger.info("禁用Mirror Code...")
        
        try:
            if self.mirror_engine:
                await self.mirror_engine.stop()
            
            self.is_enabled = False
            self.is_syncing = False
            await self._set_status(MirrorStatus.DISABLED)
            
            # 触发回调
            if self.on_toggle_change:
                await self._safe_callback(self.on_toggle_change, False)
            
            self.logger.info("Mirror Code已禁用")
            return True
            
        except Exception as e:
            self.logger.error(f"禁用Mirror Code失败: {e}")
            await self._set_error_status(str(e))
            return False
    
    async def force_sync(self) -> bool:
        """强制同步"""
        if not self.is_enabled:
            self.logger.warning("Mirror Code未启用，无法同步")
            return False
        
        try:
            self.logger.info("开始强制同步...")
            await self._set_status(MirrorStatus.SYNCING)
            
            if self.mirror_engine:
                success = await self.mirror_engine.sync_now()
                
                if success:
                    self.sync_count += 1
                    self.last_sync_time = datetime.now()
                    await self._set_status(MirrorStatus.ENABLED)
                    
                    if self.on_sync_complete:
                        await self._safe_callback(self.on_sync_complete, {
                            "type": "manual",
                            "timestamp": self.last_sync_time,
                            "count": self.sync_count
                        })
                    
                    return True
                else:
                    raise Exception("同步操作失败")
            else:
                raise Exception("Mirror引擎不可用")
                
        except Exception as e:
            self.logger.error(f"强制同步失败: {e}")
            await self._set_error_status(str(e))
            return False
    
    async def _start_auto_sync(self):
        """开始自动同步"""
        while self.is_enabled and self.auto_sync:
            try:
                await asyncio.sleep(self.sync_interval)
                
                if self.is_enabled and not self.is_syncing:
                    await self.force_sync()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"自动同步异常: {e}")
                await asyncio.sleep(self.sync_interval * 2)  # 错误时延长间隔
    
    async def _set_status(self, status: MirrorStatus):
        """设置状态"""
        old_status = self.status
        self.status = status
        self.error_message = None
        
        # 更新UI状态
        self.is_syncing = (status == MirrorStatus.SYNCING)
        
        # 触发状态变更回调
        if self.on_status_change and old_status != status:
            await self._safe_callback(self.on_status_change, {
                "old_status": old_status.value,
                "new_status": status.value,
                "timestamp": datetime.now().isoformat()
            })
        
        self.logger.debug(f"Mirror状态变更: {old_status.value} -> {status.value}")
    
    async def _set_error_status(self, error_message: str):
        """设置错误状态"""
        self.error_message = error_message
        await self._set_status(MirrorStatus.ERROR)
        
        if self.on_error:
            await self._safe_callback(self.on_error, {
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _on_sync_start(self):
        """同步开始事件处理"""
        await self._set_status(MirrorStatus.SYNCING)
    
    async def _on_sync_complete(self, result):
        """同步完成事件处理"""
        self.sync_count += 1
        self.last_sync_time = datetime.now()
        await self._set_status(MirrorStatus.ENABLED)
        
        if self.on_sync_complete:
            await self._safe_callback(self.on_sync_complete, {
                "type": "auto",
                "timestamp": self.last_sync_time,
                "count": self.sync_count,
                "result": result
            })
    
    async def _on_sync_error(self, error):
        """同步错误事件处理"""
        await self._set_error_status(f"同步失败: {error}")
    
    async def _on_engine_status_change(self, status):
        """引擎状态变更事件处理"""
        if status == "offline":
            await self._set_status(MirrorStatus.OFFLINE)
        elif status == "online" and self.is_enabled:
            await self._set_status(MirrorStatus.ENABLED)
    
    async def _safe_callback(self, callback, *args, **kwargs):
        """安全执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"回调函数执行失败: {e}")
    
    def get_ui_state(self) -> Dict[str, Any]:
        """获取UI状态"""
        return {
            "is_enabled": self.is_enabled,
            "is_syncing": self.is_syncing,
            "status": self.status.value,
            "status_text": self._get_status_text(),
            "status_color": self._get_status_color(),
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_count": self.sync_count,
            "error_message": self.error_message,
            "show_settings": self.show_settings,
            "config": {
                "auto_sync": self.auto_sync,
                "sync_interval": self.sync_interval,
                "show_notifications": self.show_notifications,
                "sync_on_save": self.sync_on_save
            }
        }
    
    def _get_status_text(self) -> str:
        """获取状态文本"""
        status_texts = {
            MirrorStatus.DISABLED: "Mirror Code已禁用",
            MirrorStatus.ENABLED: f"Mirror Code已启用 (已同步{self.sync_count}次)",
            MirrorStatus.SYNCING: "正在同步...",
            MirrorStatus.ERROR: f"错误: {self.error_message}",
            MirrorStatus.OFFLINE: "离线模式"
        }
        return status_texts.get(self.status, "未知状态")
    
    def _get_status_color(self) -> str:
        """获取状态颜色"""
        status_colors = {
            MirrorStatus.DISABLED: "#6b7280",  # 灰色
            MirrorStatus.ENABLED: "#10b981",   # 绿色
            MirrorStatus.SYNCING: "#3b82f6",   # 蓝色
            MirrorStatus.ERROR: "#ef4444",     # 红色
            MirrorStatus.OFFLINE: "#f59e0b"    # 橙色
        }
        return status_colors.get(self.status, "#6b7280")
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if "auto_sync" in config:
            self.auto_sync = config["auto_sync"]
        if "sync_interval" in config:
            self.sync_interval = max(1, config["sync_interval"])
        if "show_notifications" in config:
            self.show_notifications = config["show_notifications"]
        if "sync_on_save" in config:
            self.sync_on_save = config["sync_on_save"]
        
        self.logger.info(f"Mirror配置已更新: {config}")
    
    def toggle_settings(self):
        """切换设置面板显示"""
        self.show_settings = not self.show_settings
        return self.show_settings
    
    def get_status_icon(self) -> str:
        """获取状态图标"""
        status_icons = {
            MirrorStatus.DISABLED: "⭕",
            MirrorStatus.ENABLED: "✅",
            MirrorStatus.SYNCING: "🔄",
            MirrorStatus.ERROR: "❌",
            MirrorStatus.OFFLINE: "📴"
        }
        return status_icons.get(self.status, "❓")
    
    def get_tooltip_text(self) -> str:
        """获取工具提示文本"""
        base_text = self._get_status_text()
        
        if self.last_sync_time:
            time_str = self.last_sync_time.strftime("%H:%M:%S")
            base_text += f"\n最后同步: {time_str}"
        
        if self.is_enabled:
            base_text += f"\n自动同步: {'开启' if self.auto_sync else '关闭'}"
            if self.auto_sync:
                base_text += f" (间隔: {self.sync_interval}秒)"
        
        return base_text
    
    async def handle_file_save(self, file_path: str):
        """处理文件保存事件"""
        if self.is_enabled and self.sync_on_save and not self.is_syncing:
            self.logger.info(f"文件保存触发同步: {file_path}")
            await self.force_sync()
    
    def get_quick_actions(self) -> list:
        """获取快速操作列表"""
        actions = []
        
        if self.is_enabled:
            actions.extend([
                {
                    "id": "force_sync",
                    "text": "立即同步",
                    "icon": "🔄",
                    "enabled": not self.is_syncing
                },
                {
                    "id": "disable_mirror",
                    "text": "禁用Mirror",
                    "icon": "⭕",
                    "enabled": True
                }
            ])
        else:
            actions.append({
                "id": "enable_mirror",
                "text": "启用Mirror",
                "icon": "✅",
                "enabled": True
            })
        
        actions.extend([
            {
                "id": "toggle_settings",
                "text": "设置",
                "icon": "⚙️",
                "enabled": True
            },
            {
                "id": "view_history",
                "text": "同步历史",
                "icon": "📋",
                "enabled": True
            }
        ])
        
        return actions
    
    async def execute_quick_action(self, action_id: str) -> bool:
        """执行快速操作"""
        try:
            if action_id == "force_sync":
                return await self.force_sync()
            elif action_id == "enable_mirror":
                return await self.enable_mirror()
            elif action_id == "disable_mirror":
                return await self.disable_mirror()
            elif action_id == "toggle_settings":
                self.toggle_settings()
                return True
            elif action_id == "view_history":
                # 触发显示历史面板
                return True
            else:
                self.logger.warning(f"未知的快速操作: {action_id}")
                return False
        except Exception as e:
            self.logger.error(f"执行快速操作失败 {action_id}: {e}")
            return False

