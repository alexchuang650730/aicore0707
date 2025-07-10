"""
Communication Manager - 通信管理器
处理WebSocket连接，消息传递，端云通信

真实实现，支持实际的网络通信
"""

import asyncio
import json
import logging
import time
import websockets
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime
import ssl
import uuid

class Connection:
    """连接对象"""
    
    def __init__(self, websocket, connection_id: str, endpoint: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.endpoint = endpoint
        self.connected_at = time.time()
        self.last_ping = time.time()
        self.is_active = True
        self.session_info = {}
    
    async def send(self, message: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logging.error(f"发送消息失败: {e}")
            self.is_active = False
            return False
    
    async def close(self):
        """关闭连接"""
        try:
            self.is_active = False
            await self.websocket.close()
        except Exception as e:
            logging.error(f"关闭连接失败: {e}")

class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        self.handlers = {}
        self.middleware = []
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.handlers[message_type] = handler
    
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)
    
    async def handle_message(self, connection: Connection, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息"""
        try:
            # 应用中间件
            for middleware in self.middleware:
                message = await middleware(connection, message)
                if message is None:
                    return {"success": False, "error": "消息被中间件拦截"}
            
            message_type = message.get("type")
            if message_type in self.handlers:
                handler = self.handlers[message_type]
                return await handler(connection, message)
            else:
                return {
                    "success": False,
                    "error": f"未知消息类型: {message_type}"
                }
                
        except Exception as e:
            logging.error(f"处理消息失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class CommunicationManager:
    """通信管理器 - 处理所有网络通信"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化通信管理器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 连接管理
        self.connections = {}  # connection_id -> Connection
        self.server = None
        self.client_connections = {}  # endpoint -> Connection
        
        # 消息处理
        self.message_handler = MessageHandler()
        self._setup_default_handlers()
        
        # 配置
        self.server_host = self.config.get("server_host", "0.0.0.0")
        self.server_port = self.config.get("server_port", 8080)
        self.reconnect_interval = self.config.get("reconnect_interval", 5.0)
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30.0)
        
        # 状态管理
        self.is_running = False
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "connections_established": 0,
            "connections_lost": 0,
            "errors": 0
        }
        
        # 后台任务
        self.heartbeat_task = None
        self.reconnect_tasks = {}
        
        self.logger.info("通信管理器初始化完成")
    
    async def start(self):
        """启动通信管理器"""
        try:
            self.logger.info("启动通信管理器...")
            
            self.is_running = True
            
            # 启动WebSocket服务器
            await self._start_server()
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info("✅ 通信管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动通信管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止通信管理器"""
        try:
            self.logger.info("停止通信管理器...")
            
            self.is_running = False
            
            # 停止心跳任务
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 停止重连任务
            for task in self.reconnect_tasks.values():
                task.cancel()
            
            # 关闭所有连接
            await self.disconnect_all()
            
            # 停止服务器
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            self.logger.info("✅ 通信管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止通信管理器失败: {e}")
    
    async def connect(self, endpoint: str, retry: bool = True) -> Optional[Connection]:
        """
        连接到远程端点
        
        Args:
            endpoint: 远程端点URL
            retry: 是否自动重连
            
        Returns:
            Connection: 连接对象
        """
        try:
            self.logger.info(f"连接到: {endpoint}")
            
            # 解析WebSocket URL
            if not endpoint.startswith(("ws://", "wss://")):
                endpoint = f"ws://{endpoint}"
            
            # 建立WebSocket连接
            websocket = await websockets.connect(
                endpoint,
                ping_interval=self.heartbeat_interval,
                ping_timeout=10
            )
            
            # 创建连接对象
            connection_id = str(uuid.uuid4())
            connection = Connection(websocket, connection_id, endpoint)
            
            # 保存连接
            self.connections[connection_id] = connection
            self.client_connections[endpoint] = connection
            
            # 启动消息监听
            asyncio.create_task(self._handle_connection(connection))
            
            # 设置自动重连
            if retry:
                self.reconnect_tasks[endpoint] = asyncio.create_task(
                    self._auto_reconnect(endpoint)
                )
            
            self.stats["connections_established"] += 1
            self.logger.info(f"✅ 连接成功: {endpoint}")
            
            return connection
            
        except Exception as e:
            self.logger.error(f"连接失败: {endpoint} - {e}")
            self.stats["errors"] += 1
            return None
    
    async def disconnect(self, endpoint: str):
        """断开连接"""
        try:
            connection = self.client_connections.get(endpoint)
            if connection:
                await connection.close()
                del self.client_connections[endpoint]
                if connection.connection_id in self.connections:
                    del self.connections[connection.connection_id]
                
                # 停止重连任务
                if endpoint in self.reconnect_tasks:
                    self.reconnect_tasks[endpoint].cancel()
                    del self.reconnect_tasks[endpoint]
                
                self.logger.info(f"断开连接: {endpoint}")
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
    
    async def disconnect_all(self):
        """断开所有连接"""
        endpoints = list(self.client_connections.keys())
        for endpoint in endpoints:
            await self.disconnect(endpoint)
        
        # 关闭服务器连接
        connections = list(self.connections.values())
        for connection in connections:
            await connection.close()
        
        self.connections.clear()
        self.client_connections.clear()
    
    async def send_message(self, endpoint: str, message: Dict[str, Any]) -> bool:
        """
        发送消息到指定端点
        
        Args:
            endpoint: 目标端点
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        try:
            connection = self.client_connections.get(endpoint)
            if not connection or not connection.is_active:
                self.logger.warning(f"连接不可用: {endpoint}")
                return False
            
            # 添加消息元数据
            message.update({
                "timestamp": time.time(),
                "message_id": str(uuid.uuid4())
            })
            
            success = await connection.send(message)
            if success:
                self.stats["messages_sent"] += 1
                self.logger.debug(f"消息发送成功: {endpoint}")
            else:
                self.stats["errors"] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.stats["errors"] += 1
            return False
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None) -> int:
        """
        广播消息到所有连接
        
        Args:
            message: 消息内容
            exclude: 排除的连接ID集合
            
        Returns:
            int: 成功发送的连接数
        """
        exclude = exclude or set()
        success_count = 0
        
        # 添加消息元数据
        message.update({
            "timestamp": time.time(),
            "message_id": str(uuid.uuid4())
        })
        
        for connection in self.connections.values():
            if connection.connection_id not in exclude and connection.is_active:
                if await connection.send(message):
                    success_count += 1
                    self.stats["messages_sent"] += 1
        
        self.logger.debug(f"广播消息: {success_count}/{len(self.connections)} 连接")
        return success_count
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handler.register_handler(message_type, handler)
        self.logger.info(f"注册消息处理器: {message_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取通信管理器状态"""
        active_connections = sum(1 for conn in self.connections.values() if conn.is_active)
        
        return {
            "is_running": self.is_running,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "total_connections": len(self.connections),
            "active_connections": active_connections,
            "client_connections": len(self.client_connections),
            "stats": self.stats,
            "endpoints": list(self.client_connections.keys())
        }
    
    async def _start_server(self):
        """启动WebSocket服务器"""
        try:
            self.server = await websockets.serve(
                self._handle_server_connection,
                self.server_host,
                self.server_port,
                ping_interval=self.heartbeat_interval,
                ping_timeout=10
            )
            
            self.logger.info(f"WebSocket服务器启动: {self.server_host}:{self.server_port}")
            
        except Exception as e:
            self.logger.error(f"启动WebSocket服务器失败: {e}")
            raise
    
    async def _handle_server_connection(self, websocket, path):
        """处理服务器连接"""
        connection_id = str(uuid.uuid4())
        endpoint = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        connection = Connection(websocket, connection_id, endpoint)
        
        self.connections[connection_id] = connection
        self.stats["connections_established"] += 1
        
        self.logger.info(f"新连接: {endpoint} ({connection_id})")
        
        try:
            await self._handle_connection(connection)
        finally:
            if connection_id in self.connections:
                del self.connections[connection_id]
            self.stats["connections_lost"] += 1
            self.logger.info(f"连接断开: {endpoint} ({connection_id})")
    
    async def _handle_connection(self, connection: Connection):
        """处理连接消息"""
        try:
            async for message_data in connection.websocket:
                try:
                    message = json.loads(message_data)
                    self.stats["messages_received"] += 1
                    
                    # 更新连接活跃时间
                    connection.last_ping = time.time()
                    
                    # 处理消息
                    response = await self.message_handler.handle_message(connection, message)
                    
                    # 发送响应（如果需要）
                    if response and message.get("require_response", False):
                        await connection.send(response)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {e}")
                    self.stats["errors"] += 1
                except Exception as e:
                    self.logger.error(f"处理消息失败: {e}")
                    self.stats["errors"] += 1
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"连接正常关闭: {connection.endpoint}")
        except Exception as e:
            self.logger.error(f"连接处理失败: {e}")
        finally:
            connection.is_active = False
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        self.logger.info("启动心跳循环")
        
        while self.is_running:
            try:
                current_time = time.time()
                inactive_connections = []
                
                # 检查连接活跃状态
                for connection in self.connections.values():
                    if current_time - connection.last_ping > self.heartbeat_interval * 2:
                        inactive_connections.append(connection)
                
                # 清理非活跃连接
                for connection in inactive_connections:
                    self.logger.warning(f"清理非活跃连接: {connection.endpoint}")
                    await connection.close()
                    if connection.connection_id in self.connections:
                        del self.connections[connection.connection_id]
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _auto_reconnect(self, endpoint: str):
        """自动重连"""
        while self.is_running:
            try:
                await asyncio.sleep(self.reconnect_interval)
                
                connection = self.client_connections.get(endpoint)
                if not connection or not connection.is_active:
                    self.logger.info(f"尝试重连: {endpoint}")
                    new_connection = await self.connect(endpoint, retry=False)
                    if new_connection:
                        self.logger.info(f"重连成功: {endpoint}")
                    else:
                        self.logger.warning(f"重连失败: {endpoint}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"自动重连错误: {e}")
    
    def _setup_default_handlers(self):
        """设置默认消息处理器"""
        
        async def handle_ping(connection: Connection, message: Dict[str, Any]) -> Dict[str, Any]:
            """处理ping消息"""
            return {
                "type": "pong",
                "timestamp": time.time()
            }
        
        async def handle_file_sync(connection: Connection, message: Dict[str, Any]) -> Dict[str, Any]:
            """处理文件同步消息"""
            # 这里可以集成到同步管理器
            self.logger.info(f"收到文件同步: {message.get('file_path')}")
            return {
                "type": "sync_ack",
                "success": True
            }
        
        async def handle_session_info(connection: Connection, message: Dict[str, Any]) -> Dict[str, Any]:
            """处理会话信息"""
            connection.session_info = message.get("session_info", {})
            self.logger.info(f"更新会话信息: {connection.endpoint}")
            return {
                "type": "session_ack",
                "success": True
            }
        
        # 注册默认处理器
        self.message_handler.register_handler("ping", handle_ping)
        self.message_handler.register_handler("file_sync", handle_file_sync)
        self.message_handler.register_handler("session_info", handle_session_info)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("CommunicationManager")
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

