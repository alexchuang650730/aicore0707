"""
PowerAutomation MCP协调器

统一管理和协调所有MCP组件：
- 集成现有的5大MCP系统
- 统一消息路由和通信协议
- 负载均衡和故障转移
- 性能监控和优化
- 配置管理和服务发现

基于现有的MCP架构，提供统一的协调层。
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict
import uuid

# 导入现有MCP组件
from ..components.local_adapter_mcp.local_adapter_engine import LocalAdapterEngine
from ..components.trae_agent_mcp.trae_agent_engine import TraeAgentEngine
from ..components.stagewise_mcp.visual_programming_engine import VisualProgrammingEngine
from ..routing.intelligent_router import IntelligentRouter
from ..command.unified_command_system import UnifiedCommandSystem


class MCPType(Enum):
    """MCP类型枚举"""
    LOCAL_ADAPTER = "local_adapter"
    TRAE_AGENT = "trae_agent"
    STAGEWISE = "stagewise"
    MEMORYOS = "memoryos"
    WEB_UI = "web_ui"


class MCPStatus(Enum):
    """MCP状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class MCPInstance:
    """MCP实例信息"""
    mcp_id: str
    mcp_type: MCPType
    name: str
    version: str
    status: MCPStatus
    capabilities: List[str]
    endpoint: str
    priority: int
    load_factor: float
    last_heartbeat: datetime
    error_count: int
    total_requests: int
    successful_requests: int
    average_response_time: float
    metadata: Dict[str, Any]


@dataclass
class MCPMessage:
    """MCP消息"""
    message_id: str
    source_mcp: str
    target_mcp: Optional[str]
    message_type: MessageType
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 5
    timeout: float = 30.0


@dataclass
class MCPResponse:
    """MCP响应"""
    message_id: str
    correlation_id: str
    source_mcp: str
    success: bool
    result: Any
    error: Optional[str]
    timestamp: datetime
    processing_time: float


class MCPCoordinator:
    """
    MCP协调器
    
    统一管理和协调所有MCP组件，提供：
    - 服务注册和发现
    - 消息路由和通信
    - 负载均衡和故障转移
    - 性能监控和优化
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化MCP协调器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # MCP实例管理
        self.mcp_instances: Dict[str, MCPInstance] = {}
        self.mcp_engines: Dict[str, Any] = {}
        
        # 消息管理
        self.pending_messages: Dict[str, MCPMessage] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.response_callbacks: Dict[str, Callable] = {}
        
        # 路由和负载均衡
        self.intelligent_router = IntelligentRouter()
        self.load_balancer = self._init_load_balancer()
        
        # 统一命令系统集成
        self.command_system = UnifiedCommandSystem()
        
        # 协调器状态
        self.is_running = False
        self.coordinator_tasks: List[asyncio.Task] = []
        
        # 统计信息
        self.stats = {
            "total_messages": 0,
            "successful_messages": 0,
            "failed_messages": 0,
            "active_mcps": 0,
            "total_mcps": 0,
            "average_response_time": 0.0,
            "start_time": None
        }
        
        # 初始化消息处理器
        self._init_message_handlers()
        
        self.logger.info("MCP协调器初始化完成")
    
    def _init_load_balancer(self):
        """初始化负载均衡器"""
        return {
            "strategy": self.config.get("load_balance_strategy", "round_robin"),
            "health_check_interval": self.config.get("health_check_interval", 30),
            "max_retries": self.config.get("max_retries", 3),
            "timeout": self.config.get("default_timeout", 30.0)
        }
    
    def _init_message_handlers(self):
        """初始化消息处理器"""
        self.message_handlers = {
            "register_mcp": self._handle_register_mcp,
            "unregister_mcp": self._handle_unregister_mcp,
            "execute_task": self._handle_execute_task,
            "get_capabilities": self._handle_get_capabilities,
            "health_check": self._handle_health_check,
            "get_status": self._handle_get_status,
            "route_message": self._handle_route_message
        }
    
    async def start(self):
        """启动MCP协调器"""
        if self.is_running:
            self.logger.warning("MCP协调器已在运行中")
            return
        
        self.is_running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        self.logger.info("启动MCP协调器")
        
        # 启动智能路由器
        await self.intelligent_router.start()
        
        # 启动统一命令系统
        await self.command_system.start()
        
        # 注册内置MCP实例
        await self._register_builtin_mcps()
        
        # 启动协调器任务
        self.coordinator_tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._message_processing_loop()),
            asyncio.create_task(self._load_balancing_loop())
        ]
        
        self.logger.info("MCP协调器启动完成")
    
    async def stop(self):
        """停止MCP协调器"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("停止MCP协调器")
        
        # 停止协调器任务
        for task in self.coordinator_tasks:
            task.cancel()
        
        await asyncio.gather(*self.coordinator_tasks, return_exceptions=True)
        self.coordinator_tasks.clear()
        
        # 停止所有MCP引擎
        for mcp_id, engine in self.mcp_engines.items():
            try:
                if hasattr(engine, 'stop'):
                    await engine.stop()
            except Exception as e:
                self.logger.warning(f"停止MCP引擎失败 {mcp_id}: {e}")
        
        # 停止统一命令系统
        await self.command_system.stop()
        
        # 停止智能路由器
        await self.intelligent_router.stop()
        
        self.logger.info("MCP协调器已停止")
    
    async def _register_builtin_mcps(self):
        """注册内置MCP实例"""
        # 注册Local Adapter MCP
        try:
            local_adapter = LocalAdapterEngine()
            await self.register_mcp(
                mcp_type=MCPType.LOCAL_ADAPTER,
                name="Local Adapter MCP",
                version="1.0.0",
                capabilities=["local_execution", "cross_platform", "ai_enhanced", "monitoring"],
                endpoint="local://local_adapter",
                engine=local_adapter
            )
        except Exception as e:
            self.logger.warning(f"注册Local Adapter MCP失败: {e}")
        
        # 注册Trae Agent MCP
        try:
            trae_agent = TraeAgentEngine()
            await self.register_mcp(
                mcp_type=MCPType.TRAE_AGENT,
                name="Trae Agent MCP",
                version="1.0.0",
                capabilities=["software_engineering", "code_generation", "architecture_design"],
                endpoint="local://trae_agent",
                engine=trae_agent
            )
        except Exception as e:
            self.logger.warning(f"注册Trae Agent MCP失败: {e}")
        
        # 注册Stagewise MCP
        try:
            stagewise = VisualProgrammingEngine()
            await self.register_mcp(
                mcp_type=MCPType.STAGEWISE,
                name="Stagewise MCP",
                version="1.0.0",
                capabilities=["visual_programming", "workflow_design", "stage_execution"],
                endpoint="local://stagewise",
                engine=stagewise
            )
        except Exception as e:
            self.logger.warning(f"注册Stagewise MCP失败: {e}")
        
        # 注册MemoryOS MCP（占位符）
        await self.register_mcp(
            mcp_type=MCPType.MEMORYOS,
            name="MemoryOS MCP",
            version="1.0.0",
            capabilities=["memory_management", "context_storage", "knowledge_graph"],
            endpoint="local://memoryos",
            engine=None  # 待实现
        )
        
        # 注册Web UI MCP（占位符）
        await self.register_mcp(
            mcp_type=MCPType.WEB_UI,
            name="Web UI MCP",
            version="1.0.0",
            capabilities=["web_interface", "user_interaction", "visualization"],
            endpoint="local://web_ui",
            engine=None  # 待实现
        )
    
    async def register_mcp(self, mcp_type: MCPType, name: str, version: str,
                          capabilities: List[str], endpoint: str, 
                          engine: Any = None, priority: int = 5) -> str:
        """
        注册MCP实例
        
        Args:
            mcp_type: MCP类型
            name: MCP名称
            version: 版本号
            capabilities: 能力列表
            endpoint: 端点地址
            engine: MCP引擎实例
            priority: 优先级
            
        Returns:
            MCP实例ID
        """
        mcp_id = f"{mcp_type.value}_{uuid.uuid4().hex[:8]}"
        
        instance = MCPInstance(
            mcp_id=mcp_id,
            mcp_type=mcp_type,
            name=name,
            version=version,
            status=MCPStatus.INITIALIZING,
            capabilities=capabilities,
            endpoint=endpoint,
            priority=priority,
            load_factor=0.0,
            last_heartbeat=datetime.now(),
            error_count=0,
            total_requests=0,
            successful_requests=0,
            average_response_time=0.0,
            metadata={}
        )
        
        self.mcp_instances[mcp_id] = instance
        
        if engine:
            self.mcp_engines[mcp_id] = engine
            # 启动MCP引擎
            try:
                if hasattr(engine, 'start'):
                    await engine.start()
                instance.status = MCPStatus.RUNNING
            except Exception as e:
                self.logger.error(f"启动MCP引擎失败 {mcp_id}: {e}")
                instance.status = MCPStatus.ERROR
                instance.error_count += 1
        else:
            instance.status = MCPStatus.RUNNING  # 占位符MCP
        
        self.stats["total_mcps"] = len(self.mcp_instances)
        self.stats["active_mcps"] = len([i for i in self.mcp_instances.values() 
                                       if i.status == MCPStatus.RUNNING])
        
        self.logger.info(f"注册MCP实例: {name} ({mcp_id})")
        
        return mcp_id
    
    async def unregister_mcp(self, mcp_id: str):
        """注销MCP实例"""
        if mcp_id not in self.mcp_instances:
            self.logger.warning(f"MCP实例不存在: {mcp_id}")
            return
        
        instance = self.mcp_instances[mcp_id]
        
        # 停止MCP引擎
        if mcp_id in self.mcp_engines:
            engine = self.mcp_engines[mcp_id]
            try:
                if hasattr(engine, 'stop'):
                    await engine.stop()
            except Exception as e:
                self.logger.warning(f"停止MCP引擎失败 {mcp_id}: {e}")
            
            del self.mcp_engines[mcp_id]
        
        # 移除实例
        del self.mcp_instances[mcp_id]
        
        self.stats["total_mcps"] = len(self.mcp_instances)
        self.stats["active_mcps"] = len([i for i in self.mcp_instances.values() 
                                       if i.status == MCPStatus.RUNNING])
        
        self.logger.info(f"注销MCP实例: {instance.name} ({mcp_id})")
    
    async def send_message(self, target_mcp: Optional[str], method: str, 
                          params: Dict[str, Any], priority: int = 5,
                          timeout: float = 30.0) -> MCPResponse:
        """
        发送消息到MCP
        
        Args:
            target_mcp: 目标MCP ID，None表示自动路由
            method: 方法名
            params: 参数
            priority: 优先级
            timeout: 超时时间
            
        Returns:
            MCP响应
        """
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        correlation_id = f"corr_{uuid.uuid4().hex[:8]}"
        
        message = MCPMessage(
            message_id=message_id,
            source_mcp="coordinator",
            target_mcp=target_mcp,
            message_type=MessageType.REQUEST,
            method=method,
            params=params,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            priority=priority,
            timeout=timeout
        )
        
        # 如果没有指定目标MCP，使用智能路由
        if not target_mcp:
            target_mcp = await self._route_message(message)
            message.target_mcp = target_mcp
        
        if not target_mcp:
            return MCPResponse(
                message_id=message_id,
                correlation_id=correlation_id,
                source_mcp="coordinator",
                success=False,
                result=None,
                error="无法找到合适的MCP处理请求",
                timestamp=datetime.now(),
                processing_time=0.0
            )
        
        # 发送消息
        self.pending_messages[correlation_id] = message
        
        try:
            response = await self._execute_message(message)
            self.stats["successful_messages"] += 1
            return response
            
        except Exception as e:
            self.stats["failed_messages"] += 1
            return MCPResponse(
                message_id=message_id,
                correlation_id=correlation_id,
                source_mcp=target_mcp,
                success=False,
                result=None,
                error=str(e),
                timestamp=datetime.now(),
                processing_time=0.0
            )
        finally:
            self.stats["total_messages"] += 1
            if correlation_id in self.pending_messages:
                del self.pending_messages[correlation_id]
    
    async def _route_message(self, message: MCPMessage) -> Optional[str]:
        """路由消息到合适的MCP"""
        # 根据方法名和能力匹配MCP
        method = message.method
        params = message.params
        
        # 能力映射
        capability_mapping = {
            "execute_local_command": ["local_execution"],
            "generate_code": ["code_generation", "software_engineering"],
            "design_architecture": ["architecture_design"],
            "create_workflow": ["visual_programming", "workflow_design"],
            "manage_memory": ["memory_management", "context_storage"],
            "render_ui": ["web_interface", "user_interaction"]
        }
        
        required_capabilities = capability_mapping.get(method, [])
        
        # 查找匹配的MCP
        candidates = []
        for mcp_id, instance in self.mcp_instances.items():
            if instance.status != MCPStatus.RUNNING:
                continue
            
            # 检查能力匹配
            if required_capabilities:
                if not any(cap in instance.capabilities for cap in required_capabilities):
                    continue
            
            candidates.append((mcp_id, instance))
        
        if not candidates:
            return None
        
        # 负载均衡选择
        return await self._select_mcp_by_load_balance(candidates)
    
    async def _select_mcp_by_load_balance(self, candidates: List[tuple]) -> str:
        """根据负载均衡策略选择MCP"""
        strategy = self.load_balancer["strategy"]
        
        if strategy == "round_robin":
            # 简单轮询
            return candidates[self.stats["total_messages"] % len(candidates)][0]
        
        elif strategy == "least_loaded":
            # 选择负载最低的
            return min(candidates, key=lambda x: x[1].load_factor)[0]
        
        elif strategy == "priority":
            # 选择优先级最高的
            return max(candidates, key=lambda x: x[1].priority)[0]
        
        elif strategy == "response_time":
            # 选择响应时间最短的
            return min(candidates, key=lambda x: x[1].average_response_time)[0]
        
        else:
            # 默认选择第一个
            return candidates[0][0]
    
    async def _execute_message(self, message: MCPMessage) -> MCPResponse:
        """执行消息"""
        start_time = datetime.now()
        target_mcp = message.target_mcp
        
        if target_mcp not in self.mcp_instances:
            raise ValueError(f"MCP实例不存在: {target_mcp}")
        
        instance = self.mcp_instances[target_mcp]
        instance.total_requests += 1
        
        try:
            # 检查是否有对应的消息处理器
            if message.method in self.message_handlers:
                result = await self.message_handlers[message.method](message)
            else:
                # 转发到MCP引擎
                if target_mcp in self.mcp_engines:
                    engine = self.mcp_engines[target_mcp]
                    result = await self._forward_to_engine(engine, message)
                else:
                    raise ValueError(f"MCP引擎不存在: {target_mcp}")
            
            # 更新统计信息
            instance.successful_requests += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新平均响应时间
            if instance.average_response_time == 0:
                instance.average_response_time = processing_time
            else:
                instance.average_response_time = (
                    instance.average_response_time * 0.8 + processing_time * 0.2
                )
            
            return MCPResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id,
                source_mcp=target_mcp,
                success=True,
                result=result,
                error=None,
                timestamp=datetime.now(),
                processing_time=processing_time
            )
            
        except Exception as e:
            instance.error_count += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return MCPResponse(
                message_id=message.message_id,
                correlation_id=message.correlation_id,
                source_mcp=target_mcp,
                success=False,
                result=None,
                error=str(e),
                timestamp=datetime.now(),
                processing_time=processing_time
            )
    
    async def _forward_to_engine(self, engine: Any, message: MCPMessage) -> Any:
        """转发消息到MCP引擎"""
        method = message.method
        params = message.params
        
        # 根据引擎类型调用相应方法
        if hasattr(engine, method):
            method_func = getattr(engine, method)
            if asyncio.iscoroutinefunction(method_func):
                return await method_func(**params)
            else:
                return method_func(**params)
        else:
            # 通用执行方法
            if hasattr(engine, 'execute'):
                return await engine.execute(method, params)
            else:
                raise ValueError(f"引擎不支持方法: {method}")
    
    async def _handle_register_mcp(self, message: MCPMessage) -> Dict[str, Any]:
        """处理MCP注册"""
        params = message.params
        
        mcp_id = await self.register_mcp(
            mcp_type=MCPType(params["mcp_type"]),
            name=params["name"],
            version=params["version"],
            capabilities=params["capabilities"],
            endpoint=params["endpoint"],
            priority=params.get("priority", 5)
        )
        
        return {"mcp_id": mcp_id, "status": "registered"}
    
    async def _handle_unregister_mcp(self, message: MCPMessage) -> Dict[str, Any]:
        """处理MCP注销"""
        mcp_id = message.params["mcp_id"]
        await self.unregister_mcp(mcp_id)
        return {"mcp_id": mcp_id, "status": "unregistered"}
    
    async def _handle_execute_task(self, message: MCPMessage) -> Dict[str, Any]:
        """处理任务执行"""
        params = message.params
        task_type = params.get("task_type", "general")
        task_data = params.get("task_data", {})
        
        # 使用统一命令系统执行任务
        result = await self.command_system.execute_command(
            command=task_type,
            params=task_data
        )
        
        return result
    
    async def _handle_get_capabilities(self, message: MCPMessage) -> Dict[str, Any]:
        """处理获取能力"""
        mcp_id = message.params.get("mcp_id")
        
        if mcp_id:
            if mcp_id in self.mcp_instances:
                instance = self.mcp_instances[mcp_id]
                return {
                    "mcp_id": mcp_id,
                    "capabilities": instance.capabilities
                }
            else:
                return {"error": f"MCP实例不存在: {mcp_id}"}
        else:
            # 返回所有MCP的能力
            capabilities = {}
            for mcp_id, instance in self.mcp_instances.items():
                capabilities[mcp_id] = {
                    "name": instance.name,
                    "type": instance.mcp_type.value,
                    "capabilities": instance.capabilities,
                    "status": instance.status.value
                }
            return {"all_capabilities": capabilities}
    
    async def _handle_health_check(self, message: MCPMessage) -> Dict[str, Any]:
        """处理健康检查"""
        mcp_id = message.params.get("mcp_id")
        
        if mcp_id:
            if mcp_id in self.mcp_instances:
                instance = self.mcp_instances[mcp_id]
                return {
                    "mcp_id": mcp_id,
                    "status": instance.status.value,
                    "last_heartbeat": instance.last_heartbeat.isoformat(),
                    "error_count": instance.error_count
                }
            else:
                return {"error": f"MCP实例不存在: {mcp_id}"}
        else:
            # 返回所有MCP的健康状态
            health_status = {}
            for mcp_id, instance in self.mcp_instances.items():
                health_status[mcp_id] = {
                    "name": instance.name,
                    "status": instance.status.value,
                    "last_heartbeat": instance.last_heartbeat.isoformat(),
                    "error_count": instance.error_count,
                    "success_rate": (
                        instance.successful_requests / instance.total_requests
                        if instance.total_requests > 0 else 0.0
                    )
                }
            return {"health_status": health_status}
    
    async def _handle_get_status(self, message: MCPMessage) -> Dict[str, Any]:
        """处理获取状态"""
        return {
            "coordinator_status": "running" if self.is_running else "stopped",
            "stats": self.stats,
            "mcp_count": len(self.mcp_instances),
            "active_mcp_count": len([i for i in self.mcp_instances.values() 
                                   if i.status == MCPStatus.RUNNING]),
            "pending_messages": len(self.pending_messages)
        }
    
    async def _handle_route_message(self, message: MCPMessage) -> Dict[str, Any]:
        """处理消息路由"""
        target_mcp = await self._route_message(message)
        return {"target_mcp": target_mcp}
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                # 更新所有MCP的心跳
                for mcp_id, instance in self.mcp_instances.items():
                    if instance.status == MCPStatus.RUNNING:
                        instance.last_heartbeat = datetime.now()
                
                await asyncio.sleep(30)  # 每30秒心跳一次
                
            except Exception as e:
                self.logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for mcp_id, instance in self.mcp_instances.items():
                    # 检查心跳超时
                    time_since_heartbeat = (current_time - instance.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > 120:  # 2分钟无心跳
                        if instance.status == MCPStatus.RUNNING:
                            instance.status = MCPStatus.ERROR
                            instance.error_count += 1
                            self.logger.warning(f"MCP心跳超时: {instance.name} ({mcp_id})")
                    
                    # 检查错误率
                    if instance.total_requests > 10:
                        error_rate = instance.error_count / instance.total_requests
                        if error_rate > 0.5:  # 错误率超过50%
                            if instance.status == MCPStatus.RUNNING:
                                instance.status = MCPStatus.ERROR
                                self.logger.warning(f"MCP错误率过高: {instance.name} ({mcp_id})")
                
                # 更新活跃MCP数量
                self.stats["active_mcps"] = len([i for i in self.mcp_instances.values() 
                                               if i.status == MCPStatus.RUNNING])
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _message_processing_loop(self):
        """消息处理循环"""
        while self.is_running:
            try:
                # 清理超时的待处理消息
                current_time = datetime.now()
                expired_messages = []
                
                for correlation_id, message in self.pending_messages.items():
                    time_elapsed = (current_time - message.timestamp).total_seconds()
                    if time_elapsed > message.timeout:
                        expired_messages.append(correlation_id)
                
                for correlation_id in expired_messages:
                    del self.pending_messages[correlation_id]
                    self.stats["failed_messages"] += 1
                
                await asyncio.sleep(10)  # 每10秒清理一次
                
            except Exception as e:
                self.logger.error(f"消息处理循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _load_balancing_loop(self):
        """负载均衡循环"""
        while self.is_running:
            try:
                # 更新负载因子
                for mcp_id, instance in self.mcp_instances.items():
                    if instance.status == MCPStatus.RUNNING:
                        # 简单的负载因子计算：响应时间 + 错误率
                        error_rate = (instance.error_count / instance.total_requests 
                                    if instance.total_requests > 0 else 0.0)
                        instance.load_factor = instance.average_response_time + error_rate * 10
                
                await asyncio.sleep(30)  # 每30秒更新一次
                
            except Exception as e:
                self.logger.error(f"负载均衡循环错误: {e}")
                await asyncio.sleep(10)
    
    def get_mcp_instances(self) -> Dict[str, Dict[str, Any]]:
        """获取MCP实例信息"""
        instances = {}
        for mcp_id, instance in self.mcp_instances.items():
            instance_dict = asdict(instance)
            instance_dict["mcp_type"] = instance_dict["mcp_type"].value
            instance_dict["status"] = instance_dict["status"].value
            instance_dict["last_heartbeat"] = instance_dict["last_heartbeat"].isoformat()
            instances[mcp_id] = instance_dict
        return instances
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "coordinator_running": self.is_running,
            "stats": self.get_stats(),
            "mcp_instances": len(self.mcp_instances),
            "active_mcps": len([i for i in self.mcp_instances.values() 
                              if i.status == MCPStatus.RUNNING]),
            "pending_messages": len(self.pending_messages),
            "components": {
                "intelligent_router": await self.intelligent_router.health_check(),
                "command_system": await self.command_system.health_check()
            }
        }


if __name__ == "__main__":
    # 测试MCP协调器
    import asyncio
    
    async def test_mcp_coordinator():
        coordinator = MCPCoordinator()
        
        print("启动MCP协调器...")
        await coordinator.start()
        
        # 测试获取能力
        response = await coordinator.send_message(
            target_mcp=None,
            method="get_capabilities",
            params={}
        )
        print(f"获取能力: {response.success}")
        if response.success:
            print(f"能力列表: {list(response.result.get('all_capabilities', {}).keys())}")
        
        # 测试健康检查
        response = await coordinator.send_message(
            target_mcp=None,
            method="health_check",
            params={}
        )
        print(f"健康检查: {response.success}")
        
        # 等待一些处理时间
        await asyncio.sleep(5)
        
        # 获取统计信息
        stats = coordinator.get_stats()
        print(f"统计信息: {stats}")
        
        # 健康检查
        health = await coordinator.health_check()
        print(f"协调器健康状态: {health['status']}")
        
        print("停止MCP协调器...")
        await coordinator.stop()
    
    # 运行测试
    asyncio.run(test_mcp_coordinator())

