"""
Mirror Settings Panel - Mirror设置面板
提供Mirror Code的详细配置选项
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class SyncMode(Enum):
    """同步模式"""
    AUTO = "auto"
    MANUAL = "manual"
    ON_SAVE = "on_save"
    SCHEDULED = "scheduled"

class ConflictResolution(Enum):
    """冲突解决策略"""
    ASK_USER = "ask_user"
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    MERGE_AUTO = "merge_auto"

@dataclass
class MirrorTarget:
    """镜像目标配置"""
    id: str
    name: str
    type: str  # local, remote, cloud
    path: str
    enabled: bool = True
    priority: int = 1
    auth_config: Dict[str, Any] = None

@dataclass
class MirrorSettings:
    """Mirror设置配置"""
    # 基本设置
    enabled: bool = False
    sync_mode: SyncMode = SyncMode.AUTO
    auto_sync_interval: int = 5  # 秒
    
    # 同步选项
    sync_on_save: bool = True
    sync_on_focus_lost: bool = False
    sync_on_startup: bool = True
    
    # 冲突处理
    conflict_resolution: ConflictResolution = ConflictResolution.ASK_USER
    backup_before_merge: bool = True
    max_conflict_backups: int = 10
    
    # 性能设置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    excluded_patterns: List[str] = None
    compression_enabled: bool = True
    
    # 通知设置
    show_sync_notifications: bool = True
    show_error_notifications: bool = True
    notification_timeout: int = 3000  # 毫秒
    
    # 安全设置
    encrypt_remote_data: bool = True
    require_auth: bool = False
    session_timeout: int = 3600  # 秒
    
    # 高级设置
    debug_mode: bool = False
    log_level: str = "INFO"
    max_log_size: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        if self.excluded_patterns is None:
            self.excluded_patterns = [
                "*.tmp", "*.log", "*.cache", 
                ".git/*", "node_modules/*", "__pycache__/*"
            ]

class MirrorSettingsPanel:
    """Mirror设置面板"""
    
    def __init__(self, mirror_toggle=None):
        self.logger = logging.getLogger(__name__)
        self.mirror_toggle = mirror_toggle
        self.settings = MirrorSettings()
        self.mirror_targets: List[MirrorTarget] = []
        
        # UI状态
        self.is_visible = False
        self.active_tab = "general"  # general, targets, advanced, security
        self.has_unsaved_changes = False
        
        # 事件回调
        self.on_settings_change: Optional[Callable] = None
        self.on_target_change: Optional[Callable] = None
        self.on_panel_close: Optional[Callable] = None
        
        # 加载默认镜像目标
        self._load_default_targets()
    
    def _load_default_targets(self):
        """加载默认镜像目标"""
        self.mirror_targets = [
            MirrorTarget(
                id="local_backup",
                name="本地备份",
                type="local",
                path="~/mirror_backup",
                enabled=True,
                priority=1
            ),
            MirrorTarget(
                id="cloud_sync",
                name="云端同步",
                type="cloud",
                path="cloud://mirror",
                enabled=False,
                priority=2,
                auth_config={"provider": "auto"}
            )
        ]
    
    def show_panel(self, tab: str = "general"):
        """显示设置面板"""
        self.is_visible = True
        self.active_tab = tab
        self.has_unsaved_changes = False
        self.logger.info(f"显示Mirror设置面板: {tab}")
    
    def hide_panel(self):
        """隐藏设置面板"""
        if self.has_unsaved_changes:
            # 触发确认对话框
            return False
        
        self.is_visible = False
        if self.on_panel_close:
            self.on_panel_close()
        
        self.logger.info("隐藏Mirror设置面板")
        return True
    
    def switch_tab(self, tab: str):
        """切换标签页"""
        valid_tabs = ["general", "targets", "advanced", "security"]
        if tab in valid_tabs:
            self.active_tab = tab
            self.logger.debug(f"切换到标签页: {tab}")
    
    def get_panel_state(self) -> Dict[str, Any]:
        """获取面板状态"""
        return {
            "is_visible": self.is_visible,
            "active_tab": self.active_tab,
            "has_unsaved_changes": self.has_unsaved_changes,
            "settings": asdict(self.settings),
            "targets": [asdict(target) for target in self.mirror_targets],
            "tabs": self._get_tab_info()
        }
    
    def _get_tab_info(self) -> List[Dict[str, Any]]:
        """获取标签页信息"""
        return [
            {
                "id": "general",
                "name": "常规设置",
                "icon": "⚙️",
                "description": "基本同步设置和选项"
            },
            {
                "id": "targets",
                "name": "镜像目标",
                "icon": "🎯",
                "description": "配置代码镜像存储位置"
            },
            {
                "id": "advanced",
                "name": "高级设置",
                "icon": "🔧",
                "description": "性能和调试选项"
            },
            {
                "id": "security",
                "name": "安全设置",
                "icon": "🔒",
                "description": "加密和认证配置"
            }
        ]
    
    def update_setting(self, key: str, value: Any):
        """更新单个设置"""
        if hasattr(self.settings, key):
            old_value = getattr(self.settings, key)
            setattr(self.settings, key, value)
            
            self.has_unsaved_changes = True
            self.logger.info(f"设置已更新: {key} = {value} (原值: {old_value})")
            
            if self.on_settings_change:
                self.on_settings_change(key, value, old_value)
        else:
            self.logger.warning(f"未知设置项: {key}")
    
    def update_settings(self, settings_dict: Dict[str, Any]):
        """批量更新设置"""
        updated_keys = []
        
        for key, value in settings_dict.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                updated_keys.append(key)
            else:
                self.logger.warning(f"未知设置项: {key}")
        
        if updated_keys:
            self.has_unsaved_changes = True
            self.logger.info(f"批量更新设置: {updated_keys}")
    
    def reset_settings(self):
        """重置设置为默认值"""
        self.settings = MirrorSettings()
        self.has_unsaved_changes = True
        self.logger.info("设置已重置为默认值")
    
    def save_settings(self) -> bool:
        """保存设置"""
        try:
            # 验证设置
            if not self._validate_settings():
                return False
            
            # 应用设置到Mirror Toggle
            if self.mirror_toggle:
                self.mirror_toggle.update_config({
                    "auto_sync": self.settings.sync_mode == SyncMode.AUTO,
                    "sync_interval": self.settings.auto_sync_interval,
                    "sync_on_save": self.settings.sync_on_save,
                    "show_notifications": self.settings.show_sync_notifications
                })
            
            self.has_unsaved_changes = False
            self.logger.info("Mirror设置已保存")
            return True
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            return False
    
    def _validate_settings(self) -> bool:
        """验证设置"""
        # 验证同步间隔
        if self.settings.auto_sync_interval < 1:
            self.logger.error("自动同步间隔不能小于1秒")
            return False
        
        # 验证文件大小限制
        if self.settings.max_file_size < 1024:
            self.logger.error("最大文件大小不能小于1KB")
            return False
        
        # 验证镜像目标
        enabled_targets = [t for t in self.mirror_targets if t.enabled]
        if not enabled_targets:
            self.logger.error("至少需要启用一个镜像目标")
            return False
        
        return True
    
    def add_mirror_target(self, target_config: Dict[str, Any]) -> bool:
        """添加镜像目标"""
        try:
            target = MirrorTarget(**target_config)
            
            # 检查ID唯一性
            if any(t.id == target.id for t in self.mirror_targets):
                self.logger.error(f"镜像目标ID已存在: {target.id}")
                return False
            
            self.mirror_targets.append(target)
            self.has_unsaved_changes = True
            
            self.logger.info(f"添加镜像目标: {target.name}")
            
            if self.on_target_change:
                self.on_target_change("add", target)
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加镜像目标失败: {e}")
            return False
    
    def update_mirror_target(self, target_id: str, updates: Dict[str, Any]) -> bool:
        """更新镜像目标"""
        target = self._find_target(target_id)
        if not target:
            self.logger.error(f"镜像目标不存在: {target_id}")
            return False
        
        try:
            for key, value in updates.items():
                if hasattr(target, key):
                    setattr(target, key, value)
                else:
                    self.logger.warning(f"未知目标属性: {key}")
            
            self.has_unsaved_changes = True
            self.logger.info(f"更新镜像目标: {target.name}")
            
            if self.on_target_change:
                self.on_target_change("update", target)
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新镜像目标失败: {e}")
            return False
    
    def remove_mirror_target(self, target_id: str) -> bool:
        """移除镜像目标"""
        target = self._find_target(target_id)
        if not target:
            self.logger.error(f"镜像目标不存在: {target_id}")
            return False
        
        self.mirror_targets.remove(target)
        self.has_unsaved_changes = True
        
        self.logger.info(f"移除镜像目标: {target.name}")
        
        if self.on_target_change:
            self.on_target_change("remove", target)
        
        return True
    
    def _find_target(self, target_id: str) -> Optional[MirrorTarget]:
        """查找镜像目标"""
        return next((t for t in self.mirror_targets if t.id == target_id), None)
    
    def test_mirror_target(self, target_id: str) -> Dict[str, Any]:
        """测试镜像目标连接"""
        target = self._find_target(target_id)
        if not target:
            return {"success": False, "error": "目标不存在"}
        
        try:
            # 模拟连接测试
            if target.type == "local":
                # 检查本地路径
                import os
                path = os.path.expanduser(target.path)
                if os.path.exists(path) or os.path.exists(os.path.dirname(path)):
                    return {"success": True, "message": "本地路径可访问"}
                else:
                    return {"success": False, "error": "本地路径不存在"}
            
            elif target.type == "remote":
                # 模拟远程连接测试
                return {"success": True, "message": "远程连接正常"}
            
            elif target.type == "cloud":
                # 模拟云端连接测试
                return {"success": True, "message": "云端服务可用"}
            
            else:
                return {"success": False, "error": "未知目标类型"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """获取设置摘要"""
        enabled_targets = [t for t in self.mirror_targets if t.enabled]
        
        return {
            "mirror_enabled": self.settings.enabled,
            "sync_mode": self.settings.sync_mode.value,
            "auto_sync_interval": f"{self.settings.auto_sync_interval}秒",
            "enabled_targets": len(enabled_targets),
            "total_targets": len(self.mirror_targets),
            "conflict_resolution": self.settings.conflict_resolution.value,
            "encryption_enabled": self.settings.encrypt_remote_data,
            "notifications_enabled": self.settings.show_sync_notifications
        }
    
    def export_settings(self) -> Dict[str, Any]:
        """导出设置"""
        return {
            "export_time": "2025-01-09T12:00:00Z",
            "version": "4.5.0",
            "settings": asdict(self.settings),
            "targets": [asdict(target) for target in self.mirror_targets]
        }
    
    def import_settings(self, settings_data: Dict[str, Any]) -> bool:
        """导入设置"""
        try:
            # 验证数据格式
            if "settings" not in settings_data:
                raise ValueError("缺少settings字段")
            
            # 导入基本设置
            settings_dict = settings_data["settings"]
            self.settings = MirrorSettings(**settings_dict)
            
            # 导入镜像目标
            if "targets" in settings_data:
                self.mirror_targets = [
                    MirrorTarget(**target_data) 
                    for target_data in settings_data["targets"]
                ]
            
            self.has_unsaved_changes = True
            self.logger.info("设置导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"导入设置失败: {e}")
            return False
    
    def get_quick_settings(self) -> List[Dict[str, Any]]:
        """获取快速设置选项"""
        return [
            {
                "id": "toggle_auto_sync",
                "name": "自动同步",
                "type": "toggle",
                "value": self.settings.sync_mode == SyncMode.AUTO,
                "description": "启用自动代码同步"
            },
            {
                "id": "sync_on_save",
                "name": "保存时同步",
                "type": "toggle",
                "value": self.settings.sync_on_save,
                "description": "文件保存时自动同步"
            },
            {
                "id": "show_notifications",
                "name": "显示通知",
                "type": "toggle",
                "value": self.settings.show_sync_notifications,
                "description": "显示同步状态通知"
            },
            {
                "id": "sync_interval",
                "name": "同步间隔",
                "type": "slider",
                "value": self.settings.auto_sync_interval,
                "min": 1,
                "max": 60,
                "unit": "秒",
                "description": "自动同步的时间间隔"
            }
        ]
    
    def update_quick_setting(self, setting_id: str, value: Any):
        """更新快速设置"""
        if setting_id == "toggle_auto_sync":
            self.settings.sync_mode = SyncMode.AUTO if value else SyncMode.MANUAL
        elif setting_id == "sync_on_save":
            self.settings.sync_on_save = value
        elif setting_id == "show_notifications":
            self.settings.show_sync_notifications = value
        elif setting_id == "sync_interval":
            self.settings.auto_sync_interval = max(1, min(60, int(value)))
        else:
            self.logger.warning(f"未知快速设置: {setting_id}")
            return
        
        self.has_unsaved_changes = True
        self.logger.info(f"快速设置已更新: {setting_id} = {value}")

