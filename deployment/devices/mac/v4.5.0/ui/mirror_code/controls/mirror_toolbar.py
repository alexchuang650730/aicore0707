"""
Mirror Toolbar - Mirror工具栏控件
在编辑器顶部提供Mirror Code的快速控制选项
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

class MirrorToolbar:
    """Mirror工具栏控件"""
    
    def __init__(self, mirror_toggle=None, status_indicator=None):
        self.logger = logging.getLogger(__name__)
        self.mirror_toggle = mirror_toggle
        self.status_indicator = status_indicator
        
        # UI状态
        self.is_visible = True
        self.is_compact = False
        self.position = "top"  # top, bottom, left, right
        
        # 工具栏配置
        self.show_toggle = True
        self.show_status = True
        self.show_quick_actions = True
        self.show_settings_button = True
        
        # 事件回调
        self.on_action_click: Optional[Callable] = None
        self.on_toolbar_config_change: Optional[Callable] = None
    
    def get_toolbar_state(self) -> Dict[str, Any]:
        """获取工具栏状态"""
        # 获取Mirror状态
        mirror_state = {}
        if self.mirror_toggle:
            mirror_state = self.mirror_toggle.get_ui_state()
        
        # 获取状态指示器信息
        status_display = {}
        if self.status_indicator:
            status_display = self.status_indicator.get_status_display()
        
        return {
            "toolbar": {
                "is_visible": self.is_visible,
                "is_compact": self.is_compact,
                "position": self.position,
                "config": {
                    "show_toggle": self.show_toggle,
                    "show_status": self.show_status,
                    "show_quick_actions": self.show_quick_actions,
                    "show_settings_button": self.show_settings_button
                }
            },
            "mirror_state": mirror_state,
            "status_display": status_display,
            "controls": self._get_toolbar_controls(),
            "quick_actions": self._get_quick_actions(),
            "layout": self._get_layout_config()
        }
    
    def _get_toolbar_controls(self) -> List[Dict[str, Any]]:
        """获取工具栏控件列表"""
        controls = []
        
        # Mirror开关控件
        if self.show_toggle and self.mirror_toggle:
            toggle_state = self.mirror_toggle.get_ui_state()
            controls.append({
                "type": "toggle",
                "id": "mirror_toggle",
                "label": "Mirror Code",
                "enabled": toggle_state["is_enabled"],
                "status": toggle_state["status"],
                "color": toggle_state["status_color"],
                "icon": self.mirror_toggle.get_status_icon(),
                "tooltip": self.mirror_toggle.get_tooltip_text(),
                "loading": toggle_state["is_syncing"]
            })
        
        # 状态指示器
        if self.show_status and self.status_indicator:
            status_display = self.status_indicator.get_status_display()
            controls.append({
                "type": "status",
                "id": "status_indicator",
                "text": status_display["main_status"]["text"],
                "color": status_display["main_status"]["color"],
                "icon": status_display["main_status"]["icon"],
                "details": {
                    "last_sync": status_display["sync_info"]["last_sync"],
                    "sync_count": status_display["sync_info"]["sync_count"],
                    "success_rate": status_display["sync_info"]["success_rate"]
                },
                "animation": status_display["animation"]
            })
        
        # 快速操作按钮
        if self.show_quick_actions:
            controls.extend(self._get_action_buttons())
        
        # 设置按钮
        if self.show_settings_button:
            controls.append({
                "type": "button",
                "id": "settings",
                "label": "设置",
                "icon": "⚙️",
                "tooltip": "Mirror Code设置",
                "style": "secondary"
            })
        
        return controls
    
    def _get_action_buttons(self) -> List[Dict[str, Any]]:
        """获取快速操作按钮"""
        buttons = []
        
        if self.mirror_toggle:
            quick_actions = self.mirror_toggle.get_quick_actions()
            
            for action in quick_actions:
                buttons.append({
                    "type": "button",
                    "id": action["id"],
                    "label": action["text"],
                    "icon": action["icon"],
                    "enabled": action["enabled"],
                    "tooltip": f"{action['text']} - {action.get('description', '')}",
                    "style": "primary" if action["id"] == "force_sync" else "secondary"
                })
        
        return buttons
    
    def _get_quick_actions(self) -> List[Dict[str, Any]]:
        """获取快速操作列表"""
        actions = []
        
        # 基本操作
        actions.extend([
            {
                "id": "toggle_mirror",
                "name": "切换Mirror",
                "icon": "🔄",
                "shortcut": "Ctrl+Shift+M",
                "description": "启用或禁用Mirror Code"
            },
            {
                "id": "force_sync",
                "name": "立即同步",
                "icon": "⚡",
                "shortcut": "Ctrl+Shift+S",
                "description": "强制执行代码同步"
            },
            {
                "id": "view_history",
                "name": "同步历史",
                "icon": "📋",
                "shortcut": "Ctrl+Shift+H",
                "description": "查看同步历史记录"
            }
        ])
        
        # 高级操作
        if self.mirror_toggle and self.mirror_toggle.is_enabled:
            actions.extend([
                {
                    "id": "resolve_conflicts",
                    "name": "解决冲突",
                    "icon": "⚔️",
                    "shortcut": "Ctrl+Shift+R",
                    "description": "手动解决同步冲突"
                },
                {
                    "id": "backup_now",
                    "name": "立即备份",
                    "icon": "💾",
                    "shortcut": "Ctrl+Shift+B",
                    "description": "创建当前代码备份"
                }
            ])
        
        return actions
    
    def _get_layout_config(self) -> Dict[str, Any]:
        """获取布局配置"""
        return {
            "compact_mode": self.is_compact,
            "position": self.position,
            "auto_hide": False,
            "responsive": True,
            "theme": "auto",  # auto, light, dark
            "animation": True,
            "spacing": "normal"  # compact, normal, spacious
        }
    
    async def handle_control_action(self, control_id: str, action: str = "click") -> bool:
        """处理控件操作"""
        try:
            self.logger.info(f"处理工具栏操作: {control_id}.{action}")
            
            if control_id == "mirror_toggle":
                if self.mirror_toggle:
                    return await self.mirror_toggle.toggle_mirror()
            
            elif control_id == "settings":
                # 触发设置面板显示
                if self.on_action_click:
                    await self._safe_callback(self.on_action_click, "show_settings")
                return True
            
            elif control_id.startswith("action_"):
                # 处理快速操作
                action_id = control_id.replace("action_", "")
                if self.mirror_toggle:
                    return await self.mirror_toggle.execute_quick_action(action_id)
            
            else:
                # 处理其他操作
                return await self._handle_custom_action(control_id, action)
            
        except Exception as e:
            self.logger.error(f"处理工具栏操作失败 {control_id}: {e}")
            return False
    
    async def _handle_custom_action(self, control_id: str, action: str) -> bool:
        """处理自定义操作"""
        custom_actions = {
            "force_sync": self._force_sync,
            "view_history": self._view_history,
            "resolve_conflicts": self._resolve_conflicts,
            "backup_now": self._backup_now,
            "toggle_compact": self._toggle_compact_mode
        }
        
        if control_id in custom_actions:
            return await custom_actions[control_id]()
        
        self.logger.warning(f"未知的工具栏操作: {control_id}")
        return False
    
    async def _force_sync(self) -> bool:
        """强制同步"""
        if self.mirror_toggle:
            return await self.mirror_toggle.force_sync()
        return False
    
    async def _view_history(self) -> bool:
        """查看历史"""
        if self.on_action_click:
            await self._safe_callback(self.on_action_click, "show_history")
        return True
    
    async def _resolve_conflicts(self) -> bool:
        """解决冲突"""
        if self.on_action_click:
            await self._safe_callback(self.on_action_click, "show_conflicts")
        return True
    
    async def _backup_now(self) -> bool:
        """立即备份"""
        # 模拟备份操作
        self.logger.info("执行立即备份...")
        return True
    
    async def _toggle_compact_mode(self) -> bool:
        """切换紧凑模式"""
        self.is_compact = not self.is_compact
        
        if self.on_toolbar_config_change:
            await self._safe_callback(self.on_toolbar_config_change, {
                "compact_mode": self.is_compact
            })
        
        self.logger.info(f"工具栏紧凑模式: {self.is_compact}")
        return True
    
    async def _safe_callback(self, callback, *args, **kwargs):
        """安全执行回调"""
        try:
            if callback:
                if hasattr(callback, '__call__'):
                    if hasattr(callback, '__await__'):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"回调执行失败: {e}")
    
    def update_config(self, config: Dict[str, Any]):
        """更新工具栏配置"""
        if "show_toggle" in config:
            self.show_toggle = config["show_toggle"]
        if "show_status" in config:
            self.show_status = config["show_status"]
        if "show_quick_actions" in config:
            self.show_quick_actions = config["show_quick_actions"]
        if "show_settings_button" in config:
            self.show_settings_button = config["show_settings_button"]
        if "is_compact" in config:
            self.is_compact = config["is_compact"]
        if "position" in config:
            self.position = config["position"]
        
        self.logger.info(f"工具栏配置已更新: {config}")
    
    def set_visibility(self, visible: bool):
        """设置工具栏可见性"""
        self.is_visible = visible
        self.logger.info(f"工具栏可见性: {visible}")
    
    def get_keyboard_shortcuts(self) -> List[Dict[str, Any]]:
        """获取键盘快捷键"""
        return [
            {
                "key": "Ctrl+Shift+M",
                "action": "toggle_mirror",
                "description": "切换Mirror Code开关"
            },
            {
                "key": "Ctrl+Shift+S",
                "action": "force_sync",
                "description": "强制同步代码"
            },
            {
                "key": "Ctrl+Shift+H",
                "action": "view_history",
                "description": "查看同步历史"
            },
            {
                "key": "Ctrl+Shift+R",
                "action": "resolve_conflicts",
                "description": "解决同步冲突"
            },
            {
                "key": "Ctrl+Shift+B",
                "action": "backup_now",
                "description": "立即备份代码"
            },
            {
                "key": "Ctrl+Shift+T",
                "action": "toggle_compact",
                "description": "切换紧凑模式"
            }
        ]
    
    async def handle_keyboard_shortcut(self, shortcut: str) -> bool:
        """处理键盘快捷键"""
        shortcut_map = {
            "Ctrl+Shift+M": "toggle_mirror",
            "Ctrl+Shift+S": "force_sync",
            "Ctrl+Shift+H": "view_history",
            "Ctrl+Shift+R": "resolve_conflicts",
            "Ctrl+Shift+B": "backup_now",
            "Ctrl+Shift+T": "toggle_compact"
        }
        
        action = shortcut_map.get(shortcut)
        if action:
            return await self.handle_control_action(action)
        
        return False
    
    def get_context_menu(self) -> List[Dict[str, Any]]:
        """获取右键菜单"""
        menu_items = []
        
        # Mirror状态相关
        if self.mirror_toggle:
            if self.mirror_toggle.is_enabled:
                menu_items.extend([
                    {
                        "id": "disable_mirror",
                        "text": "禁用Mirror Code",
                        "icon": "⭕"
                    },
                    {
                        "id": "force_sync",
                        "text": "立即同步",
                        "icon": "⚡"
                    },
                    {"type": "separator"}
                ])
            else:
                menu_items.append({
                    "id": "enable_mirror",
                    "text": "启用Mirror Code",
                    "icon": "✅"
                })
        
        # 工具栏配置
        menu_items.extend([
            {
                "id": "toolbar_settings",
                "text": "工具栏设置",
                "icon": "⚙️",
                "submenu": [
                    {
                        "id": "toggle_compact",
                        "text": "紧凑模式",
                        "type": "checkbox",
                        "checked": self.is_compact
                    },
                    {
                        "id": "toggle_status",
                        "text": "显示状态",
                        "type": "checkbox",
                        "checked": self.show_status
                    },
                    {
                        "id": "toggle_quick_actions",
                        "text": "显示快速操作",
                        "type": "checkbox",
                        "checked": self.show_quick_actions
                    }
                ]
            },
            {"type": "separator"},
            {
                "id": "hide_toolbar",
                "text": "隐藏工具栏",
                "icon": "👁️"
            }
        ])
        
        return menu_items

