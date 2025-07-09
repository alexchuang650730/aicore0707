"""
Mirror Status Indicator - Mirror状态指示器组件
显示Mirror Code的实时状态和同步信息
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class SyncEvent:
    """同步事件数据类"""
    timestamp: datetime
    event_type: str  # start, complete, error
    message: str
    details: Dict[str, Any] = None

class MirrorStatusIndicator:
    """Mirror状态指示器"""
    
    def __init__(self, mirror_toggle=None):
        self.logger = logging.getLogger(__name__)
        self.mirror_toggle = mirror_toggle
        self.sync_history: List[SyncEvent] = []
        self.max_history = 100
        
        # 状态统计
        self.total_syncs = 0
        self.successful_syncs = 0
        self.failed_syncs = 0
        self.last_error = None
        
        # UI配置
        self.show_detailed_status = True
        self.show_sync_animation = True
        self.auto_hide_notifications = True
        self.notification_timeout = 3000  # 毫秒
        
        # 动画状态
        self.is_animating = False
        self.animation_frame = 0
        
        if mirror_toggle:
            self._register_toggle_events()
    
    def _register_toggle_events(self):
        """注册Toggle事件"""
        self.mirror_toggle.on_status_change = self._on_status_change
        self.mirror_toggle.on_sync_complete = self._on_sync_complete
        self.mirror_toggle.on_error = self._on_error
    
    async def _on_status_change(self, data: Dict[str, Any]):
        """状态变更事件处理"""
        event = SyncEvent(
            timestamp=datetime.now(),
            event_type="status_change",
            message=f"状态变更: {data['old_status']} -> {data['new_status']}",
            details=data
        )
        self._add_sync_event(event)
        
        # 开始/停止动画
        if data['new_status'] == 'syncing':
            await self._start_sync_animation()
        else:
            await self._stop_sync_animation()
    
    async def _on_sync_complete(self, data: Dict[str, Any]):
        """同步完成事件处理"""
        self.total_syncs += 1
        self.successful_syncs += 1
        
        event = SyncEvent(
            timestamp=datetime.now(),
            event_type="sync_complete",
            message=f"同步完成 (第{data['count']}次)",
            details=data
        )
        self._add_sync_event(event)
    
    async def _on_error(self, data: Dict[str, Any]):
        """错误事件处理"""
        self.total_syncs += 1
        self.failed_syncs += 1
        self.last_error = data['message']
        
        event = SyncEvent(
            timestamp=datetime.now(),
            event_type="error",
            message=f"同步失败: {data['message']}",
            details=data
        )
        self._add_sync_event(event)
    
    def _add_sync_event(self, event: SyncEvent):
        """添加同步事件"""
        self.sync_history.append(event)
        
        # 限制历史记录数量
        if len(self.sync_history) > self.max_history:
            self.sync_history = self.sync_history[-self.max_history:]
        
        self.logger.debug(f"添加同步事件: {event.event_type} - {event.message}")
    
    async def _start_sync_animation(self):
        """开始同步动画"""
        if not self.show_sync_animation or self.is_animating:
            return
        
        self.is_animating = True
        self.animation_frame = 0
        
        # 启动动画循环
        asyncio.create_task(self._animation_loop())
    
    async def _stop_sync_animation(self):
        """停止同步动画"""
        self.is_animating = False
        self.animation_frame = 0
    
    async def _animation_loop(self):
        """动画循环"""
        while self.is_animating:
            self.animation_frame = (self.animation_frame + 1) % 8
            await asyncio.sleep(0.2)  # 200ms间隔
    
    def get_status_display(self) -> Dict[str, Any]:
        """获取状态显示信息"""
        if not self.mirror_toggle:
            return self._get_default_display()
        
        toggle_state = self.mirror_toggle.get_ui_state()
        
        return {
            "main_status": {
                "text": toggle_state["status_text"],
                "color": toggle_state["status_color"],
                "icon": self._get_animated_icon(toggle_state["status"]),
                "is_active": toggle_state["is_enabled"]
            },
            "sync_info": {
                "last_sync": self._format_last_sync_time(toggle_state["last_sync_time"]),
                "sync_count": toggle_state["sync_count"],
                "success_rate": self._calculate_success_rate(),
                "is_syncing": toggle_state["is_syncing"]
            },
            "statistics": {
                "total_syncs": self.total_syncs,
                "successful_syncs": self.successful_syncs,
                "failed_syncs": self.failed_syncs,
                "uptime": self._calculate_uptime()
            },
            "recent_events": self._get_recent_events(5),
            "animation": {
                "is_animating": self.is_animating,
                "frame": self.animation_frame
            }
        }
    
    def _get_default_display(self) -> Dict[str, Any]:
        """获取默认显示信息"""
        return {
            "main_status": {
                "text": "Mirror Code未初始化",
                "color": "#6b7280",
                "icon": "❓",
                "is_active": False
            },
            "sync_info": {
                "last_sync": "从未同步",
                "sync_count": 0,
                "success_rate": 0,
                "is_syncing": False
            },
            "statistics": {
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "uptime": "0分钟"
            },
            "recent_events": [],
            "animation": {
                "is_animating": False,
                "frame": 0
            }
        }
    
    def _get_animated_icon(self, status: str) -> str:
        """获取动画图标"""
        if status == "syncing" and self.is_animating:
            # 旋转动画图标
            frames = ["🔄", "🔃", "🔄", "🔃"]
            return frames[self.animation_frame % len(frames)]
        
        # 静态图标
        status_icons = {
            "disabled": "⭕",
            "enabled": "✅",
            "syncing": "🔄",
            "error": "❌",
            "offline": "📴"
        }
        return status_icons.get(status, "❓")
    
    def _format_last_sync_time(self, last_sync_time: Optional[str]) -> str:
        """格式化最后同步时间"""
        if not last_sync_time:
            return "从未同步"
        
        try:
            sync_time = datetime.fromisoformat(last_sync_time.replace('Z', '+00:00'))
            now = datetime.now()
            
            # 计算时间差
            diff = now - sync_time.replace(tzinfo=None)
            
            if diff.total_seconds() < 60:
                return f"{int(diff.total_seconds())}秒前"
            elif diff.total_seconds() < 3600:
                return f"{int(diff.total_seconds() // 60)}分钟前"
            elif diff.total_seconds() < 86400:
                return f"{int(diff.total_seconds() // 3600)}小时前"
            else:
                return sync_time.strftime("%m-%d %H:%M")
                
        except Exception:
            return "时间解析错误"
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_syncs == 0:
            return 0.0
        return round((self.successful_syncs / self.total_syncs) * 100, 1)
    
    def _calculate_uptime(self) -> str:
        """计算运行时间"""
        if not self.sync_history:
            return "0分钟"
        
        # 找到第一个启用事件
        first_enable = None
        for event in self.sync_history:
            if (event.event_type == "status_change" and 
                event.details and 
                event.details.get("new_status") == "enabled"):
                first_enable = event.timestamp
                break
        
        if not first_enable:
            return "0分钟"
        
        uptime = datetime.now() - first_enable
        
        if uptime.total_seconds() < 60:
            return f"{int(uptime.total_seconds())}秒"
        elif uptime.total_seconds() < 3600:
            return f"{int(uptime.total_seconds() // 60)}分钟"
        elif uptime.total_seconds() < 86400:
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            return f"{hours}小时{minutes}分钟"
        else:
            days = uptime.days
            hours = int((uptime.total_seconds() % 86400) // 3600)
            return f"{days}天{hours}小时"
    
    def _get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近事件"""
        recent = self.sync_history[-limit:] if self.sync_history else []
        
        return [
            {
                "timestamp": event.timestamp.strftime("%H:%M:%S"),
                "type": event.event_type,
                "message": event.message,
                "icon": self._get_event_icon(event.event_type),
                "color": self._get_event_color(event.event_type)
            }
            for event in reversed(recent)
        ]
    
    def _get_event_icon(self, event_type: str) -> str:
        """获取事件图标"""
        icons = {
            "status_change": "🔄",
            "sync_complete": "✅",
            "error": "❌",
            "sync_start": "🚀"
        }
        return icons.get(event_type, "ℹ️")
    
    def _get_event_color(self, event_type: str) -> str:
        """获取事件颜色"""
        colors = {
            "status_change": "#3b82f6",
            "sync_complete": "#10b981",
            "error": "#ef4444",
            "sync_start": "#8b5cf6"
        }
        return colors.get(event_type, "#6b7280")
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """获取详细状态信息"""
        return {
            "overview": self.get_status_display(),
            "sync_history": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type,
                    "message": event.message,
                    "details": event.details
                }
                for event in self.sync_history
            ],
            "performance": {
                "average_sync_time": self._calculate_average_sync_time(),
                "sync_frequency": self._calculate_sync_frequency(),
                "error_patterns": self._analyze_error_patterns()
            },
            "health": {
                "status": self._get_health_status(),
                "recommendations": self._get_health_recommendations()
            }
        }
    
    def _calculate_average_sync_time(self) -> float:
        """计算平均同步时间"""
        # 简化实现，实际需要记录同步开始和结束时间
        return 2.5  # 秒
    
    def _calculate_sync_frequency(self) -> str:
        """计算同步频率"""
        if len(self.sync_history) < 2:
            return "数据不足"
        
        # 计算最近10次同步的平均间隔
        recent_syncs = [e for e in self.sync_history if e.event_type == "sync_complete"][-10:]
        
        if len(recent_syncs) < 2:
            return "数据不足"
        
        intervals = []
        for i in range(1, len(recent_syncs)):
            interval = (recent_syncs[i].timestamp - recent_syncs[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 60:
            return f"每{int(avg_interval)}秒"
        elif avg_interval < 3600:
            return f"每{int(avg_interval // 60)}分钟"
        else:
            return f"每{int(avg_interval // 3600)}小时"
    
    def _analyze_error_patterns(self) -> List[str]:
        """分析错误模式"""
        error_events = [e for e in self.sync_history if e.event_type == "error"]
        
        if not error_events:
            return ["无错误记录"]
        
        patterns = []
        
        # 检查错误频率
        if len(error_events) > self.total_syncs * 0.1:
            patterns.append("错误率较高，建议检查网络连接")
        
        # 检查最近错误
        recent_errors = [e for e in error_events if 
                        (datetime.now() - e.timestamp).total_seconds() < 3600]
        
        if len(recent_errors) > 3:
            patterns.append("最近1小时内错误频繁")
        
        if not patterns:
            patterns.append("错误模式正常")
        
        return patterns
    
    def _get_health_status(self) -> str:
        """获取健康状态"""
        success_rate = self._calculate_success_rate()
        
        if success_rate >= 95:
            return "优秀"
        elif success_rate >= 85:
            return "良好"
        elif success_rate >= 70:
            return "一般"
        else:
            return "需要关注"
    
    def _get_health_recommendations(self) -> List[str]:
        """获取健康建议"""
        recommendations = []
        success_rate = self._calculate_success_rate()
        
        if success_rate < 85:
            recommendations.append("同步成功率偏低，建议检查网络连接")
        
        if self.failed_syncs > 5:
            recommendations.append("失败次数较多，建议查看错误日志")
        
        if not self.sync_history:
            recommendations.append("暂无同步记录，建议启用Mirror Code")
        
        if not recommendations:
            recommendations.append("Mirror Code运行状态良好")
        
        return recommendations
    
    def clear_history(self):
        """清空历史记录"""
        self.sync_history.clear()
        self.total_syncs = 0
        self.successful_syncs = 0
        self.failed_syncs = 0
        self.last_error = None
        self.logger.info("Mirror状态历史已清空")
    
    def export_history(self) -> Dict[str, Any]:
        """导出历史记录"""
        return {
            "export_time": datetime.now().isoformat(),
            "statistics": {
                "total_syncs": self.total_syncs,
                "successful_syncs": self.successful_syncs,
                "failed_syncs": self.failed_syncs,
                "success_rate": self._calculate_success_rate()
            },
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type,
                    "message": event.message,
                    "details": event.details
                }
                for event in self.sync_history
            ]
        }

