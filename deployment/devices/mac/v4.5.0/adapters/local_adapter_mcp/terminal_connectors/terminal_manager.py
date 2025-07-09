"""
Terminal Manager - 终端管理器
统一管理多个终端连接
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from .base_connector import BaseTerminalConnector, ConnectionConfig, ConnectionStatus
from .ec2_connector import EC2Connector
from .wsl_connector import WSLConnector
from .mac_connector import MacTerminalConnector

class TerminalManager:
    """终端管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connectors: Dict[str, BaseTerminalConnector] = {}
        self.connector_classes: Dict[str, Type[BaseTerminalConnector]] = {
            "linux_ec2": EC2Connector,
            "wsl": WSLConnector,
            "mac_terminal": MacTerminalConnector
        }
        self.active_connections = 0
        self.max_connections = 50
        self.connection_history = []
        
    async def create_connection(self, config: ConnectionConfig) -> str:
        """创建新连接"""
        if self.active_connections >= self.max_connections:
            raise Exception(f"达到最大连接数限制: {self.max_connections}")
        
        # 生成连接ID
        connection_id = f"{config.platform}_{config.name}_{datetime.now().timestamp()}"
        
        # 获取连接器类
        connector_class = self.connector_classes.get(config.platform)
        if not connector_class:
            raise ValueError(f"不支持的平台: {config.platform}")
        
        # 创建连接器实例
        connector = connector_class(config)
        
        # 注册事件处理器
        connector.on("status_changed", self._on_connection_status_changed)
        connector.on("command_executed", self._on_command_executed)
        
        # 保存连接器
        self.connectors[connection_id] = connector
        
        self.logger.info(f"创建连接: {connection_id} ({config.platform})")
        return connection_id
    
    async def connect(self, connection_id: str) -> bool:
        """建立连接"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        try:
            success = await connector.connect()
            if success:
                self.active_connections += 1
                self._add_to_history("connect", connection_id, True)
            else:
                self._add_to_history("connect", connection_id, False)
            
            return success
            
        except Exception as e:
            self.logger.error(f"连接失败 {connection_id}: {e}")
            self._add_to_history("connect", connection_id, False, str(e))
            raise
    
    async def disconnect(self, connection_id: str) -> bool:
        """断开连接"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        try:
            success = await connector.disconnect()
            if success and connector.status == ConnectionStatus.CONNECTED:
                self.active_connections -= 1
            
            self._add_to_history("disconnect", connection_id, success)
            return success
            
        except Exception as e:
            self.logger.error(f"断开连接失败 {connection_id}: {e}")
            self._add_to_history("disconnect", connection_id, False, str(e))
            raise
    
    async def remove_connection(self, connection_id: str) -> bool:
        """移除连接"""
        connector = self.connectors.get(connection_id)
        if not connector:
            return True
        
        # 先断开连接
        if connector.status == ConnectionStatus.CONNECTED:
            await self.disconnect(connection_id)
        
        # 移除连接器
        del self.connectors[connection_id]
        self.logger.info(f"移除连接: {connection_id}")
        
        return True
    
    async def execute_command(self, connection_id: str, command: str, timeout: Optional[int] = None) -> Any:
        """在指定连接上执行命令"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connector.status != ConnectionStatus.CONNECTED:
            raise Exception(f"连接未建立: {connection_id}")
        
        return await connector.execute_command(command, timeout)
    
    async def execute_interactive_command(self, connection_id: str, command: str, input_handler=None) -> Any:
        """在指定连接上执行交互式命令"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connector.status != ConnectionStatus.CONNECTED:
            raise Exception(f"连接未建立: {connection_id}")
        
        return await connector.execute_interactive_command(command, input_handler)
    
    async def upload_file(self, connection_id: str, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connector.status != ConnectionStatus.CONNECTED:
            raise Exception(f"连接未建立: {connection_id}")
        
        return await connector.upload_file(local_path, remote_path)
    
    async def download_file(self, connection_id: str, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connector.status != ConnectionStatus.CONNECTED:
            raise Exception(f"连接未建立: {connection_id}")
        
        return await connector.download_file(remote_path, local_path)
    
    async def get_system_info(self, connection_id: str) -> Dict[str, Any]:
        """获取系统信息"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        if connector.status != ConnectionStatus.CONNECTED:
            raise Exception(f"连接未建立: {connection_id}")
        
        return await connector.get_system_info()
    
    async def health_check(self, connection_id: Optional[str] = None) -> Dict[str, bool]:
        """健康检查"""
        if connection_id:
            # 检查单个连接
            connector = self.connectors.get(connection_id)
            if not connector:
                return {connection_id: False}
            
            try:
                healthy = await connector.health_check()
                return {connection_id: healthy}
            except Exception:
                return {connection_id: False}
        
        else:
            # 检查所有连接
            results = {}
            
            for conn_id, connector in self.connectors.items():
                try:
                    healthy = await connector.health_check()
                    results[conn_id] = healthy
                except Exception:
                    results[conn_id] = False
            
            return results
    
    async def reconnect(self, connection_id: str) -> bool:
        """重新连接"""
        connector = self.connectors.get(connection_id)
        if not connector:
            raise ValueError(f"连接不存在: {connection_id}")
        
        try:
            success = await connector.reconnect()
            self._add_to_history("reconnect", connection_id, success)
            return success
            
        except Exception as e:
            self.logger.error(f"重新连接失败 {connection_id}: {e}")
            self._add_to_history("reconnect", connection_id, False, str(e))
            raise
    
    def get_connection_status(self, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """获取连接状态"""
        if connection_id:
            # 获取单个连接状态
            connector = self.connectors.get(connection_id)
            if not connector:
                return {}
            
            return connector.get_status()
        
        else:
            # 获取所有连接状态
            status = {}
            
            for conn_id, connector in self.connectors.items():
                status[conn_id] = connector.get_status()
            
            return status
    
    def get_connections_by_platform(self, platform: str) -> List[str]:
        """按平台获取连接列表"""
        connections = []
        
        for conn_id, connector in self.connectors.items():
            if connector.config.platform == platform:
                connections.append(conn_id)
        
        return connections
    
    def get_active_connections(self) -> List[str]:
        """获取活跃连接列表"""
        active = []
        
        for conn_id, connector in self.connectors.items():
            if connector.status == ConnectionStatus.CONNECTED:
                active.append(conn_id)
        
        return active
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        status_counts = {
            "connected": 0,
            "connecting": 0,
            "disconnected": 0,
            "error": 0
        }
        
        platform_counts = {}
        
        for connector in self.connectors.values():
            # 统计状态
            status_counts[connector.status.value] += 1
            
            # 统计平台
            platform = connector.config.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "total_connections": len(self.connectors),
            "active_connections": self.active_connections,
            "max_connections": self.max_connections,
            "status_counts": status_counts,
            "platform_counts": platform_counts,
            "supported_platforms": list(self.connector_classes.keys()),
            "history_count": len(self.connection_history)
        }
    
    def get_command_history(self, connection_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取命令历史"""
        connector = self.connectors.get(connection_id)
        if not connector:
            return []
        
        return connector.get_command_history(limit)
    
    def get_connection_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取连接历史"""
        return self.connection_history[-limit:]
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30) -> int:
        """清理非活跃连接"""
        cleanup_count = 0
        current_time = datetime.now()
        
        connections_to_remove = []
        
        for conn_id, connector in self.connectors.items():
            # 检查连接是否超时
            if connector.connected_at:
                inactive_time = (current_time - connector.connected_at).total_seconds() / 60
                
                if inactive_time > timeout_minutes and connector.status == ConnectionStatus.CONNECTED:
                    # 检查连接是否还活跃
                    try:
                        healthy = await connector.health_check()
                        if not healthy:
                            connections_to_remove.append(conn_id)
                    except Exception:
                        connections_to_remove.append(conn_id)
            
            elif connector.status == ConnectionStatus.ERROR:
                # 移除错误状态的连接
                connections_to_remove.append(conn_id)
        
        # 移除非活跃连接
        for conn_id in connections_to_remove:
            try:
                await self.remove_connection(conn_id)
                cleanup_count += 1
                self.logger.info(f"清理非活跃连接: {conn_id}")
            except Exception as e:
                self.logger.error(f"清理连接失败 {conn_id}: {e}")
        
        return cleanup_count
    
    async def shutdown(self):
        """关闭管理器"""
        self.logger.info("关闭终端管理器...")
        
        # 断开所有连接
        for conn_id in list(self.connectors.keys()):
            try:
                await self.remove_connection(conn_id)
            except Exception as e:
                self.logger.error(f"关闭连接失败 {conn_id}: {e}")
        
        self.connectors.clear()
        self.active_connections = 0
        
        self.logger.info("终端管理器已关闭")
    
    def _on_connection_status_changed(self, data: Dict[str, Any]):
        """连接状态变更事件处理"""
        self.logger.debug(f"连接状态变更: {data}")
        
        # 更新活跃连接计数
        if data["old_status"] == "connected" and data["new_status"] != "connected":
            self.active_connections = max(0, self.active_connections - 1)
        elif data["old_status"] != "connected" and data["new_status"] == "connected":
            self.active_connections += 1
    
    def _on_command_executed(self, data: Dict[str, Any]):
        """命令执行事件处理"""
        self.logger.debug(f"命令执行: {data['command']} (退出码: {data['exit_code']})")
    
    def _add_to_history(self, action: str, connection_id: str, success: bool, error: Optional[str] = None):
        """添加到历史记录"""
        self.connection_history.append({
            "action": action,
            "connection_id": connection_id,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录数量
        if len(self.connection_history) > 1000:
            self.connection_history = self.connection_history[-500:]

