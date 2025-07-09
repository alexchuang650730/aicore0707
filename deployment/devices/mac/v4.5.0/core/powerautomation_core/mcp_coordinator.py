"""
MCPCoordinator - MCP协调器
统一管理和协调所有MCP组件的通信
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

class MCPStatus(Enum):
    """MCP状态"""
    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class MCPInfo:
    """MCP信息"""
    id: str
    name: str
    version: str
    description: str
    capabilities: List[str]
    endpoint: str
    status: MCPStatus = MCPStatus.UNKNOWN
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MCPCall:
    """MCP调用记录"""
    id: str
    mcp_id: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    response: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MCPCoordinator:
    """MCP协调器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # MCP注册表
        self.mcps: Dict[str, MCPInfo] = {}
        self.mcp_connections: Dict[str, Any] = {}
        
        # 调用历史
        self.call_history: List[MCPCall] = []
        self.max_history_size = 1000
        
        # 事件系统
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 心跳检查
        self.heartbeat_interval = 30
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 内置MCP注册
        self._register_builtin_mcps()
        
        self.logger.info("MCP协调器初始化完成")
    
    def _register_builtin_mcps(self):
        """注册内置MCP"""
        builtin_mcps = [
            {
                "id": "command_master",
                "name": "Command Master",
                "version": "4.5.0",
                "description": "智能命令执行系统",
                "capabilities": [
                    "execute_command",
                    "get_command_history",
                    "get_command_status",
                    "cancel_command"
                ],
                "endpoint": "internal://command_master"
            },
            {
                "id": "hitl_coordinator",
                "name": "HITL Coordinator", 
                "version": "4.5.0",
                "description": "人机协作决策系统",
                "capabilities": [
                    "request_decision",
                    "get_decision_status",
                    "update_decision",
                    "get_decision_history"
                ],
                "endpoint": "internal://hitl_coordinator"
            },
            {
                "id": "ocr_processor",
                "name": "OCR Processor",
                "version": "4.5.0", 
                "description": "OCR3B_Flux图像处理系统",
                "capabilities": [
                    "process_image",
                    "process_pdf",
                    "batch_process",
                    "get_processing_status"
                ],
                "endpoint": "internal://ocr_processor"
            },
            {
                "id": "repository_manager",
                "name": "Repository Manager",
                "version": "4.5.0",
                "description": "仓库上下文管理系统",
                "capabilities": [
                    "get_current_repository",
                    "switch_repository",
                    "analyze_repository",
                    "get_repository_context"
                ],
                "endpoint": "internal://repository_manager"
            }
        ]
        
        for mcp_data in builtin_mcps:
            mcp_info = MCPInfo(
                id=mcp_data["id"],
                name=mcp_data["name"],
                version=mcp_data["version"],
                description=mcp_data["description"],
                capabilities=mcp_data["capabilities"],
                endpoint=mcp_data["endpoint"],
                status=MCPStatus.CONNECTED
            )
            self.mcps[mcp_info.id] = mcp_info
    
    async def initialize(self):
        """初始化MCP协调器"""
        try:
            # 连接到已注册的MCP
            await self._connect_mcps()
            
            # 启动心跳检查
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info("MCP协调器初始化成功")
            
        except Exception as e:
            self.logger.error(f"MCP协调器初始化失败: {e}")
            raise
    
    async def start(self):
        """启动MCP协调器"""
        self.logger.info("MCP协调器启动")
    
    async def stop(self):
        """停止MCP协调器"""
        try:
            # 停止心跳检查
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 断开MCP连接
            await self._disconnect_mcps()
            
            self.logger.info("MCP协调器停止")
            
        except Exception as e:
            self.logger.error(f"停止MCP协调器失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查关键MCP的连接状态
            critical_mcps = ["command_master", "hitl_coordinator"]
            for mcp_id in critical_mcps:
                if mcp_id in self.mcps:
                    if self.mcps[mcp_id].status != MCPStatus.CONNECTED:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    # MCP注册和管理
    async def register_mcp(self, mcp_info: Dict[str, Any]) -> bool:
        """注册MCP"""
        try:
            mcp = MCPInfo(
                id=mcp_info["id"],
                name=mcp_info["name"],
                version=mcp_info["version"],
                description=mcp_info.get("description", ""),
                capabilities=mcp_info.get("capabilities", []),
                endpoint=mcp_info["endpoint"],
                metadata=mcp_info.get("metadata", {})
            )
            
            # 验证MCP信息
            await self._validate_mcp(mcp)
            
            # 尝试连接MCP
            connected = await self._connect_mcp(mcp)
            if connected:
                self.mcps[mcp.id] = mcp
                
                # 触发注册事件
                await self._emit_event("mcp_registered", {
                    "mcp_id": mcp.id,
                    "mcp_name": mcp.name
                })
                
                self.logger.info(f"MCP注册成功: {mcp.id}")
                return True
            else:
                self.logger.error(f"MCP连接失败: {mcp.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"注册MCP失败: {e}")
            return False
    
    async def unregister_mcp(self, mcp_id: str) -> bool:
        """注销MCP"""
        try:
            if mcp_id not in self.mcps:
                return False
            
            # 断开连接
            await self._disconnect_mcp(mcp_id)
            
            # 移除注册
            del self.mcps[mcp_id]
            if mcp_id in self.mcp_connections:
                del self.mcp_connections[mcp_id]
            
            # 触发注销事件
            await self._emit_event("mcp_unregistered", {
                "mcp_id": mcp_id
            })
            
            self.logger.info(f"MCP注销成功: {mcp_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销MCP失败: {e}")
            return False
    
    async def get_mcp_list(self) -> List[Dict[str, Any]]:
        """获取MCP列表"""
        return [asdict(mcp) for mcp in self.mcps.values()]
    
    async def get_mcp_info(self, mcp_id: str) -> Optional[Dict[str, Any]]:
        """获取MCP信息"""
        if mcp_id in self.mcps:
            return asdict(self.mcps[mcp_id])
        return None
    
    # MCP调用
    async def call_mcp(self, mcp_id: str, method: str, params: Dict[str, Any] = None) -> Any:
        """调用MCP方法"""
        try:
            # 检查MCP是否存在
            if mcp_id not in self.mcps:
                raise ValueError(f"MCP不存在: {mcp_id}")
            
            mcp = self.mcps[mcp_id]
            
            # 检查MCP状态
            if mcp.status != MCPStatus.CONNECTED:
                raise RuntimeError(f"MCP未连接: {mcp_id}")
            
            # 检查方法是否支持
            if method not in mcp.capabilities:
                raise ValueError(f"MCP {mcp_id} 不支持方法: {method}")
            
            # 创建调用记录
            call_id = str(uuid.uuid4())
            call = MCPCall(
                id=call_id,
                mcp_id=mcp_id,
                method=method,
                params=params or {},
                timestamp=datetime.now()
            )
            
            # 执行调用
            start_time = datetime.now()
            try:
                result = await self._execute_mcp_call(mcp, method, params or {})
                call.response = result
                call.duration = (datetime.now() - start_time).total_seconds()
                
                # 记录调用历史
                self._add_call_history(call)
                
                # 触发调用成功事件
                await self._emit_event("mcp_call_success", {
                    "call_id": call_id,
                    "mcp_id": mcp_id,
                    "method": method,
                    "duration": call.duration
                })
                
                return result
                
            except Exception as e:
                call.error = str(e)
                call.duration = (datetime.now() - start_time).total_seconds()
                
                # 记录调用历史
                self._add_call_history(call)
                
                # 触发调用失败事件
                await self._emit_event("mcp_call_error", {
                    "call_id": call_id,
                    "mcp_id": mcp_id,
                    "method": method,
                    "error": str(e)
                })
                
                raise
                
        except Exception as e:
            self.logger.error(f"调用MCP失败: {e}")
            raise
    
    async def _execute_mcp_call(self, mcp: MCPInfo, method: str, params: Dict[str, Any]) -> Any:
        """执行MCP调用"""
        # 根据endpoint类型选择调用方式
        if mcp.endpoint.startswith("internal://"):
            return await self._call_internal_mcp(mcp, method, params)
        elif mcp.endpoint.startswith("http://") or mcp.endpoint.startswith("https://"):
            return await self._call_http_mcp(mcp, method, params)
        elif mcp.endpoint.startswith("ws://") or mcp.endpoint.startswith("wss://"):
            return await self._call_websocket_mcp(mcp, method, params)
        else:
            raise ValueError(f"不支持的endpoint类型: {mcp.endpoint}")
    
    async def _call_internal_mcp(self, mcp: MCPInfo, method: str, params: Dict[str, Any]) -> Any:
        """调用内部MCP"""
        # 获取内部组件引用
        component_name = mcp.endpoint.replace("internal://", "")
        
        if component_name == "command_master":
            return await self._call_command_master(method, params)
        elif component_name == "hitl_coordinator":
            return await self._call_hitl_coordinator(method, params)
        elif component_name == "ocr_processor":
            return await self._call_ocr_processor(method, params)
        elif component_name == "repository_manager":
            return await self._call_repository_manager(method, params)
        else:
            raise ValueError(f"未知的内部组件: {component_name}")
    
    async def _call_command_master(self, method: str, params: Dict[str, Any]) -> Any:
        """调用Command Master"""
        # 这里需要获取Command Master的实际引用
        # 暂时返回模拟结果
        if method == "execute_command":
            return {
                "command_id": str(uuid.uuid4()),
                "status": "completed",
                "result": "Command executed successfully",
                "execution_time": 1.5
            }
        elif method == "get_command_history":
            return {
                "commands": [],
                "total": 0
            }
        else:
            raise ValueError(f"不支持的Command Master方法: {method}")
    
    async def _call_hitl_coordinator(self, method: str, params: Dict[str, Any]) -> Any:
        """调用HITL Coordinator"""
        if method == "request_decision":
            return {
                "decision_id": str(uuid.uuid4()),
                "status": "pending",
                "request_time": datetime.now().isoformat()
            }
        elif method == "get_decision_status":
            return {
                "status": "approved",
                "decision_time": datetime.now().isoformat(),
                "decision_by": "user"
            }
        else:
            raise ValueError(f"不支持的HITL Coordinator方法: {method}")
    
    async def _call_ocr_processor(self, method: str, params: Dict[str, Any]) -> Any:
        """调用OCR Processor"""
        if method == "process_image":
            return {
                "processing_id": str(uuid.uuid4()),
                "status": "completed",
                "text_content": "Extracted text from image",
                "confidence": 0.95
            }
        elif method == "process_pdf":
            return {
                "processing_id": str(uuid.uuid4()),
                "status": "completed",
                "markdown_content": "# PDF Content\n\nExtracted content...",
                "page_count": 5
            }
        else:
            raise ValueError(f"不支持的OCR Processor方法: {method}")
    
    async def _call_repository_manager(self, method: str, params: Dict[str, Any]) -> Any:
        """调用Repository Manager"""
        if method == "get_current_repository":
            return {
                "repository_id": "current_repo",
                "name": "Current Repository",
                "path": "/path/to/repo",
                "type": "git"
            }
        elif method == "switch_repository":
            return {
                "success": True,
                "previous_repo": "old_repo",
                "current_repo": params.get("repository_id", "new_repo")
            }
        else:
            raise ValueError(f"不支持的Repository Manager方法: {method}")
    
    async def _call_http_mcp(self, mcp: MCPInfo, method: str, params: Dict[str, Any]) -> Any:
        """调用HTTP MCP"""
        # TODO: 实现HTTP调用逻辑
        raise NotImplementedError("HTTP MCP调用尚未实现")
    
    async def _call_websocket_mcp(self, mcp: MCPInfo, method: str, params: Dict[str, Any]) -> Any:
        """调用WebSocket MCP"""
        # TODO: 实现WebSocket调用逻辑
        raise NotImplementedError("WebSocket MCP调用尚未实现")
    
    # 连接管理
    async def _connect_mcps(self):
        """连接所有MCP"""
        for mcp in self.mcps.values():
            await self._connect_mcp(mcp)
    
    async def _connect_mcp(self, mcp: MCPInfo) -> bool:
        """连接单个MCP"""
        try:
            mcp.status = MCPStatus.CONNECTING
            
            # 根据endpoint类型建立连接
            if mcp.endpoint.startswith("internal://"):
                # 内部组件，直接标记为已连接
                mcp.status = MCPStatus.CONNECTED
                mcp.last_heartbeat = datetime.now()
                return True
            else:
                # 外部组件，需要实际连接
                # TODO: 实现外部连接逻辑
                mcp.status = MCPStatus.CONNECTED
                mcp.last_heartbeat = datetime.now()
                return True
                
        except Exception as e:
            mcp.status = MCPStatus.ERROR
            self.logger.error(f"连接MCP失败 {mcp.id}: {e}")
            return False
    
    async def _disconnect_mcps(self):
        """断开所有MCP连接"""
        for mcp_id in list(self.mcps.keys()):
            await self._disconnect_mcp(mcp_id)
    
    async def _disconnect_mcp(self, mcp_id: str):
        """断开单个MCP连接"""
        try:
            if mcp_id in self.mcps:
                self.mcps[mcp_id].status = MCPStatus.DISCONNECTED
            
            if mcp_id in self.mcp_connections:
                # TODO: 实际断开连接逻辑
                del self.mcp_connections[mcp_id]
                
        except Exception as e:
            self.logger.error(f"断开MCP连接失败 {mcp_id}: {e}")
    
    # 心跳检查
    async def _heartbeat_loop(self):
        """心跳检查循环"""
        while True:
            try:
                await self._check_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳检查错误: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _check_heartbeats(self):
        """检查心跳"""
        current_time = datetime.now()
        
        for mcp in self.mcps.values():
            if mcp.status == MCPStatus.CONNECTED:
                # 检查心跳超时
                if (mcp.last_heartbeat and 
                    (current_time - mcp.last_heartbeat).total_seconds() > self.heartbeat_interval * 3):
                    
                    self.logger.warning(f"MCP心跳超时: {mcp.id}")
                    mcp.status = MCPStatus.DISCONNECTED
                    
                    # 尝试重连
                    await self._connect_mcp(mcp)
                else:
                    # 发送心跳
                    await self._send_heartbeat(mcp)
    
    async def _send_heartbeat(self, mcp: MCPInfo):
        """发送心跳"""
        try:
            if mcp.endpoint.startswith("internal://"):
                # 内部组件，直接更新心跳时间
                mcp.last_heartbeat = datetime.now()
            else:
                # 外部组件，发送实际心跳
                # TODO: 实现外部心跳逻辑
                mcp.last_heartbeat = datetime.now()
                
        except Exception as e:
            self.logger.error(f"发送心跳失败 {mcp.id}: {e}")
            mcp.status = MCPStatus.ERROR
    
    # 辅助方法
    async def _validate_mcp(self, mcp: MCPInfo):
        """验证MCP信息"""
        if not mcp.id:
            raise ValueError("MCP ID不能为空")
        if not mcp.name:
            raise ValueError("MCP名称不能为空")
        if not mcp.endpoint:
            raise ValueError("MCP endpoint不能为空")
        if mcp.id in self.mcps:
            raise ValueError(f"MCP ID已存在: {mcp.id}")
    
    def _add_call_history(self, call: MCPCall):
        """添加调用历史"""
        self.call_history.append(call)
        
        # 限制历史记录大小
        if len(self.call_history) > self.max_history_size:
            self.call_history = self.call_history[-self.max_history_size:]
    
    # 事件系统
    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"事件处理器错误: {e}")
    
    # 状态查询
    def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            "total_mcps": len(self.mcps),
            "connected_mcps": len([m for m in self.mcps.values() if m.status == MCPStatus.CONNECTED]),
            "total_calls": len(self.call_history),
            "mcps": {mcp_id: mcp.status.value for mcp_id, mcp in self.mcps.items()}
        }
    
    def get_call_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取调用历史"""
        recent_calls = self.call_history[-limit:] if limit > 0 else self.call_history
        return [asdict(call) for call in recent_calls]

