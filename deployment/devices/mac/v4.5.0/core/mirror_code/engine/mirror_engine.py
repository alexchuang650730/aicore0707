"""
Mirror Engine - Mirror引擎核心类
负责协调所有Mirror Code功能组件
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from .claude_cli_manager import ClaudeCLIManager

class EngineStatus(Enum):
    """引擎状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class MirrorConfig:
    """Mirror配置"""
    enabled: bool = False
    auto_sync: bool = True
    sync_interval: int = 5
    max_file_size: int = 10 * 1024 * 1024
    compression: bool = True
    encryption: bool = True
    debug: bool = False

class MirrorEngine:
    """Mirror引擎主类"""
    
    def __init__(self, config: MirrorConfig = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or MirrorConfig()
        self.status = EngineStatus.STOPPED
        
        # 组件管理
        self.sync_manager = None
        self.storage_manager = None
        self.comm_manager = None
        self.claude_cli_manager = ClaudeCLIManager()
        
        # 状态管理
        self.start_time = None
        self.last_sync_time = None
        self.sync_count = 0
        self.error_count = 0
        
        # 事件回调
        self.on_sync_start: Optional[Callable] = None
        self.on_sync_complete: Optional[Callable] = None
        self.on_sync_error: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        self.on_claude_cli_ready: Optional[Callable] = None
        
        # 任务管理
        self.sync_task = None
        self.monitor_task = None
        
        # 设置Claude CLI事件回调
        self._setup_claude_cli_callbacks()
        
    async def start(self) -> bool:
        """启动Mirror引擎"""
        if self.status != EngineStatus.STOPPED:
            self.logger.warning(f"引擎已在运行状态: {self.status}")
            return False
        
        try:
            self.logger.info("启动Mirror引擎...")
            await self._set_status(EngineStatus.STARTING)
            
            # 初始化组件
            await self._initialize_components()
            
            # 安装和验证Claude CLI
            await self._setup_claude_cli()
            
            # 启动监控任务
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            # 启动自动同步
            if self.config.auto_sync:
                self.sync_task = asyncio.create_task(self._sync_loop())
            
            self.start_time = datetime.now()
            await self._set_status(EngineStatus.RUNNING)
            
            self.logger.info("Mirror引擎启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动Mirror引擎失败: {e}")
            await self._set_status(EngineStatus.ERROR)
            return False
    
    async def stop(self) -> bool:
        """停止Mirror引擎"""
        if self.status == EngineStatus.STOPPED:
            return True
        
        try:
            self.logger.info("停止Mirror引擎...")
            await self._set_status(EngineStatus.STOPPING)
            
            # 停止任务
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 清理组件
            await self._cleanup_components()
            
            await self._set_status(EngineStatus.STOPPED)
            self.logger.info("Mirror引擎已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止Mirror引擎失败: {e}")
            return False
    
    async def sync_now(self) -> bool:
        """立即执行同步"""
        if self.status != EngineStatus.RUNNING:
            self.logger.warning("引擎未运行，无法同步")
            return False
        
        try:
            self.logger.info("开始手动同步...")
            
            if self.on_sync_start:
                await self._safe_callback(self.on_sync_start)
            
            # 执行同步逻辑
            result = await self._perform_sync()
            
            if result:
                self.sync_count += 1
                self.last_sync_time = datetime.now()
                
                if self.on_sync_complete:
                    await self._safe_callback(self.on_sync_complete, {
                        "type": "manual",
                        "timestamp": self.last_sync_time,
                        "files_synced": result.get("files_synced", 0)
                    })
                
                self.logger.info("手动同步完成")
                return True
            else:
                raise Exception("同步操作失败")
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"手动同步失败: {e}")
            
            if self.on_sync_error:
                await self._safe_callback(self.on_sync_error, str(e))
            
            return False
    
    async def _initialize_components(self):
        """初始化组件"""
        # 这里会初始化SyncManager、StorageManager等
        # 暂时使用模拟实现
        self.logger.info("初始化Mirror组件...")
        
        # 模拟组件初始化
        await asyncio.sleep(0.1)
        
        self.logger.info("Mirror组件初始化完成")
    
    async def _cleanup_components(self):
        """清理组件"""
        self.logger.info("清理Mirror组件...")
        
        # 模拟组件清理
        await asyncio.sleep(0.1)
        
        self.sync_manager = None
        self.storage_manager = None
        self.comm_manager = None
        
        self.logger.info("Mirror组件清理完成")
    
    async def _sync_loop(self):
        """自动同步循环"""
        while self.status == EngineStatus.RUNNING:
            try:
                await asyncio.sleep(self.config.sync_interval)
                
                if self.status == EngineStatus.RUNNING:
                    await self.sync_now()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"自动同步循环异常: {e}")
                await asyncio.sleep(self.config.sync_interval * 2)
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.status in [EngineStatus.RUNNING, EngineStatus.STARTING]:
            try:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                # 执行健康检查
                await self._health_check()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
    
    async def _health_check(self):
        """健康检查"""
        # 检查组件状态
        # 检查网络连接
        # 检查存储空间
        pass
    
    async def _perform_sync(self) -> Dict[str, Any]:
        """执行同步操作"""
        # 模拟同步过程
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "files_synced": 5,
            "bytes_transferred": 1024 * 50,
            "duration": 0.5
        }
    
    async def _set_status(self, status: EngineStatus):
        """设置引擎状态"""
        old_status = self.status
        self.status = status
        
        if self.on_status_change and old_status != status:
            await self._safe_callback(self.on_status_change, status.value)
        
        self.logger.debug(f"引擎状态变更: {old_status.value} -> {status.value}")
    
    async def _safe_callback(self, callback, *args, **kwargs):
        """安全执行回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"回调执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": self.status.value,
            "config": {
                "enabled": self.config.enabled,
                "auto_sync": self.config.auto_sync,
                "sync_interval": self.config.sync_interval
            },
            "statistics": {
                "uptime": uptime,
                "sync_count": self.sync_count,
                "error_count": self.error_count,
                "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None
            },
            "components": {
                "sync_manager": self.sync_manager is not None,
                "storage_manager": self.storage_manager is not None,
                "comm_manager": self.comm_manager is not None,
                "claude_cli": self.claude_cli_manager.get_status()
            }
        }
    
    def update_config(self, config_updates: Dict[str, Any]):
        """更新配置"""
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"配置已更新: {key} = {value}")
            else:
                self.logger.warning(f"未知配置项: {key}")
    
    async def restart(self) -> bool:
        """重启引擎"""
        self.logger.info("重启Mirror引擎...")
        
        if await self.stop():
            await asyncio.sleep(1)  # 等待清理完成
            return await self.start()
        
        return False


    
    def _setup_claude_cli_callbacks(self):
        """设置Claude CLI事件回调"""
        self.claude_cli_manager.on_installation_start = self._on_claude_installation_start
        self.claude_cli_manager.on_installation_complete = self._on_claude_installation_complete
        self.claude_cli_manager.on_installation_error = self._on_claude_installation_error
        self.claude_cli_manager.on_verification_complete = self._on_claude_verification_complete
    
    async def _setup_claude_cli(self):
        """设置Claude CLI"""
        self.logger.info("检查Claude CLI状态...")
        
        # 检查当前安装状态
        status = await self.claude_cli_manager.check_installation_status()
        
        if not status["installed"]:
            self.logger.info("Claude CLI未安装，开始自动安装...")
            success = await self.claude_cli_manager.install_claude_cli()
            
            if not success:
                self.logger.warning("Claude CLI安装失败，Mirror Code将在有限功能模式下运行")
            else:
                self.logger.info("Claude CLI安装成功")
        else:
            self.logger.info(f"Claude CLI已安装，版本: {status['version']}")
    
    async def _on_claude_installation_start(self):
        """Claude CLI安装开始事件"""
        self.logger.info("开始安装Claude CLI...")
    
    async def _on_claude_installation_complete(self, data):
        """Claude CLI安装完成事件"""
        self.logger.info(f"Claude CLI安装完成，版本: {data['version']}")
        
        if self.on_claude_cli_ready:
            await self._safe_callback(self.on_claude_cli_ready, data)
    
    async def _on_claude_installation_error(self, data):
        """Claude CLI安装错误事件"""
        self.logger.error(f"Claude CLI安装失败: {data['error']}")
    
    async def _on_claude_verification_complete(self, data):
        """Claude CLI验证完成事件"""
        self.logger.info(f"Claude CLI验证完成，版本: {data['version']}")
    
    async def execute_claude_command(self, command: str) -> Dict[str, Any]:
        """执行Claude命令"""
        if self.status != EngineStatus.RUNNING:
            return {
                "success": False,
                "error": "Mirror引擎未运行"
            }
        
        return await self.claude_cli_manager.execute_claude_command(command)
    
    def get_claude_cli_status(self) -> Dict[str, Any]:
        """获取Claude CLI状态"""
        return self.claude_cli_manager.get_status()
    
    async def test_claude_cli(self) -> Dict[str, Any]:
        """测试Claude CLI功能"""
        return await self.claude_cli_manager.test_claude_functionality()
    
    async def reinstall_claude_cli(self) -> bool:
        """重新安装Claude CLI"""
        self.logger.info("重新安装Claude CLI...")
        
        # 先卸载
        await self.claude_cli_manager.uninstall_claude_cli()
        
        # 再安装
        return await self.claude_cli_manager.install_claude_cli()

