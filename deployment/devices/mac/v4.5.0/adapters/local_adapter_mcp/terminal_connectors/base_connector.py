"""
Base Terminal Connector - 基础终端连接器
定义所有终端连接器的统一接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime

class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class ConnectionConfig:
    """连接配置"""
    platform: str
    name: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    key_file: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    keep_alive: bool = True
    working_dir: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CommandResult:
    """命令执行结果"""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class BaseTerminalConnector(ABC):
    """基础终端连接器抽象类"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.session_id = None
        self.last_error = None
        self.connected_at = None
        self.command_history = []
        self.event_handlers = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令"""
        pass
    
    @abstractmethod
    async def execute_interactive_command(self, command: str, input_handler: Optional[Callable] = None) -> CommandResult:
        """执行交互式命令"""
        pass
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if self.status != ConnectionStatus.CONNECTED:
                return False
            
            # 执行简单命令测试连接
            result = await self.execute_command("echo 'health_check'", timeout=5)
            return result.exit_code == 0 and "health_check" in result.stdout
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    async def reconnect(self) -> bool:
        """重新连接"""
        self.logger.info("尝试重新连接...")
        
        # 先断开现有连接
        await self.disconnect()
        
        # 重新连接
        for attempt in range(self.config.retry_count):
            try:
                if await self.connect():
                    self.logger.info(f"重新连接成功 (尝试 {attempt + 1})")
                    return True
            except Exception as e:
                self.logger.warning(f"重新连接失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
        
        self.logger.error("重新连接失败")
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "platform": self.config.platform,
            "name": self.config.name,
            "status": self.status.value,
            "session_id": self.session_id,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_error": self.last_error,
            "command_count": len(self.command_history),
            "config": {
                "host": self.config.host,
                "user": self.config.user,
                "timeout": self.config.timeout,
                "keep_alive": self.config.keep_alive
            }
        }
    
    def get_command_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取命令历史"""
        return [
            {
                "command": cmd.command,
                "exit_code": cmd.exit_code,
                "execution_time": cmd.execution_time,
                "timestamp": cmd.timestamp.isoformat(),
                "success": cmd.exit_code == 0
            }
            for cmd in self.command_history[-limit:]
        ]
    
    def on(self, event: str, handler: Callable):
        """注册事件处理器"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Any):
        """触发事件"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"事件处理器错误 ({event}): {e}")
    
    def _update_status(self, status: ConnectionStatus, error: Optional[str] = None):
        """更新连接状态"""
        old_status = self.status
        self.status = status
        self.last_error = error
        
        if status == ConnectionStatus.CONNECTED and old_status != ConnectionStatus.CONNECTED:
            self.connected_at = datetime.now()
        elif status == ConnectionStatus.DISCONNECTED:
            self.connected_at = None
        
        # 触发状态变更事件
        asyncio.create_task(self._emit_event("status_changed", {
            "old_status": old_status.value,
            "new_status": status.value,
            "error": error
        }))
    
    def _add_command_to_history(self, result: CommandResult):
        """添加命令到历史记录"""
        self.command_history.append(result)
        
        # 限制历史记录数量
        if len(self.command_history) > 1000:
            self.command_history = self.command_history[-500:]
        
        # 触发命令执行事件
        asyncio.create_task(self._emit_event("command_executed", {
            "command": result.command,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "success": result.exit_code == 0
        }))
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()

