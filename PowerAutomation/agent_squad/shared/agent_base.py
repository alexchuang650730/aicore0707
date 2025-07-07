"""
PowerAutomation 4.0 Agent Base
智能体基类 - 所有专业智能体的基础类
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import time
from datetime import datetime
import uuid

# 导入核心模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.parallel_executor import get_executor
from core.event_bus import EventType, get_event_bus
from core.config import get_config
from core.exceptions import AgentError, handle_exception
from core.logging_config import get_agent_logger

class AgentStatus(Enum):
    """智能体状态枚举"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    COLLABORATING = "collaborating"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    CRITICAL = 9

@dataclass
class AgentCapability:
    """智能体能力数据结构"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    complexity_level: int  # 1-10
    estimated_time: int    # 秒
    dependencies: List[str] = None

@dataclass
class AgentTask:
    """智能体任务数据结构"""
    task_id: str
    task_type: str
    priority: TaskPriority
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    requester: str
    deadline: Optional[datetime] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    # 执行状态
    status: str = "pending"
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class AgentMessage:
    """智能体消息数据结构"""
    message_id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL

class AgentBase(ABC):
    """智能体基类 - 所有专业智能体的基础"""
    
    def __init__(self, agent_id: str, agent_name: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        
        # 基础组件
        self.logger = get_agent_logger()
        self.config = get_config()
        self.event_bus = get_event_bus()
        
        # 智能体状态
        self.status = AgentStatus.INACTIVE
        self.capabilities: List[AgentCapability] = []
        self.current_tasks: Dict[str, AgentTask] = {}
        self.task_history: List[AgentTask] = []
        
        # 性能指标
        self.performance_metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_completion_time": 0.0,
            "success_rate": 0.0,
            "current_load": 0.0
        }
        
        # 协作相关
        self.collaboration_partners: Dict[str, Any] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # 学习和优化
        self.learning_data: Dict[str, Any] = {}
        self.optimization_rules: List[Dict[str, Any]] = []
        
        # 初始化标志
        self._is_initialized = False
        self._task_processor_running = False
        
        self.logger.info(f"智能体初始化: {agent_name} ({agent_id})")
    
    async def initialize(self) -> bool:
        """
        初始化智能体
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._is_initialized:
                return True
                
            self.status = AgentStatus.INITIALIZING
            self.logger.info(f"开始初始化智能体: {self.agent_name}")
            
            # 注册能力
            await self._register_capabilities()
            
            # 注册消息处理器
            await self._register_message_handlers()
            
            # 启动任务处理器
            await self._start_task_processor()
            
            # 启动性能监控
            await self._start_performance_monitoring()
            
            # 注册到MCP系统
            await self._register_to_mcp()
            
            self.status = AgentStatus.IDLE
            self._is_initialized = True
            
            self.logger.info(f"智能体初始化完成: {self.agent_name}")
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"智能体初始化失败: {self.agent_name}, 错误: {e}")
            return False
    
    async def _register_to_mcp(self):
        """注册到MCP系统"""
        try:
            # 这里应该与MCP协调器通信，注册智能体
            # 暂时使用事件总线发送注册事件
            await self.event_bus.emit(EventType.AGENT_REGISTERED, {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'agent_type': self.agent_type,
                'capabilities': [asdict(cap) for cap in self.capabilities],
                'status': self.status.value
            })
            
            self.logger.info(f"智能体已注册到MCP系统: {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"注册到MCP系统失败: {e}")
            raise AgentError(f"MCP注册失败: {str(e)}", agent_id=self.agent_id)
            
            # 加载学习数据
            await self._load_learning_data()
            
            # 子类特定初始化
            await self._agent_specific_initialization()
            
            self.status = AgentStatus.IDLE
            self.logger.info(f"智能体初始化成功: {self.agent_name}")
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"智能体初始化失败: {self.agent_name}, 错误: {e}")
            return False
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 智能体任务
            
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        start_time = time.time()
        
        try:
            # 验证任务
            if not await self._validate_task(task):
                raise ValueError(f"任务验证失败: {task.task_id}")
            
            # 更新状态
            task.status = "running"
            task.assigned_agent = self.agent_id
            task.started_at = datetime.now()
            self.current_tasks[task.task_id] = task
            self.status = AgentStatus.BUSY
            
            # 更新负载
            self._update_current_load()
            
            self.logger.info(f"开始执行任务: {task.task_id} ({task.task_type})")
            
            # 执行具体任务逻辑
            result = await self._execute_task_logic(task)
            
            # 更新任务状态
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result
            
            # 更新性能指标
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True)
            
            # 学习和优化
            await self._learn_from_task(task, execution_time)
            
            self.logger.info(f"任务执行成功: {task.task_id}, 耗时: {execution_time:.2f}秒")
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "result": result,
                "execution_time": execution_time,
                "agent": self.agent_id
            }
            
        except Exception as e:
            # 更新任务状态
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            # 更新性能指标
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False)
            
            self.logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
            
            return {
                "status": "failed",
                "task_id": task.task_id,
                "error": str(e),
                "execution_time": execution_time,
                "agent": self.agent_id
            }
            
        finally:
            # 清理任务
            if task.task_id in self.current_tasks:
                completed_task = self.current_tasks.pop(task.task_id)
                self.task_history.append(completed_task)
                
                # 保持历史记录在合理范围内
                if len(self.task_history) > 100:
                    self.task_history = self.task_history[-80:]
            
            # 更新状态
            if not self.current_tasks:
                self.status = AgentStatus.IDLE
            
            self._update_current_load()
    
    async def send_message(self, receiver: str, message_type: str, content: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> bool:
        """
        发送消息给其他智能体
        
        Args:
            receiver: 接收者智能体ID
            message_type: 消息类型
            content: 消息内容
            priority: 消息优先级
            
        Returns:
            bool: 发送是否成功
        """
        try:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender=self.agent_id,
                receiver=receiver,
                message_type=message_type,
                content=content,
                timestamp=datetime.now(),
                priority=priority
            )
            
            # 通过事件总线发送消息
            await self.event_bus.publish(EventType.AGENT_MESSAGE, asdict(message))
            
            self.logger.debug(f"消息发送成功: {message.message_id} -> {receiver}")
            return True
            
        except Exception as e:
            self.logger.error(f"消息发送失败: {e}")
            return False
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """
        处理接收到的消息
        
        Args:
            message: 智能体消息
            
        Returns:
            Optional[Dict[str, Any]]: 处理结果
        """
        try:
            message_type = message.message_type
            
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                result = await handler(message)
                
                self.logger.debug(f"消息处理成功: {message.message_id} ({message_type})")
                return result
            else:
                self.logger.warning(f"未知消息类型: {message_type}")
                return {"status": "unknown_message_type"}
                
        except Exception as e:
            self.logger.error(f"消息处理失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def collaborate_with(self, partner_agent: str, collaboration_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        与其他智能体协作
        
        Args:
            partner_agent: 协作伙伴智能体ID
            collaboration_type: 协作类型
            data: 协作数据
            
        Returns:
            Dict[str, Any]: 协作结果
        """
        try:
            self.status = AgentStatus.COLLABORATING
            
            # 发送协作请求
            collaboration_request = {
                "collaboration_id": str(uuid.uuid4()),
                "type": collaboration_type,
                "data": data,
                "requester": self.agent_id
            }
            
            success = await self.send_message(
                partner_agent, 
                "collaboration_request", 
                collaboration_request,
                TaskPriority.HIGH
            )
            
            if success:
                # 记录协作伙伴
                self.collaboration_partners[partner_agent] = {
                    "last_collaboration": datetime.now(),
                    "collaboration_count": self.collaboration_partners.get(partner_agent, {}).get("collaboration_count", 0) + 1
                }
                
                self.logger.info(f"协作请求发送成功: {collaboration_type} -> {partner_agent}")
                return {"status": "collaboration_initiated", "collaboration_id": collaboration_request["collaboration_id"]}
            else:
                return {"status": "collaboration_failed", "error": "消息发送失败"}
                
        except Exception as e:
            self.logger.error(f"协作失败: {e}")
            return {"status": "collaboration_failed", "error": str(e)}
        finally:
            if not self.current_tasks:
                self.status = AgentStatus.IDLE
    
    @abstractmethod
    async def _register_capabilities(self):
        """注册智能体能力（子类实现）"""
        pass
    
    @abstractmethod
    async def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """执行具体任务逻辑（子类实现）"""
        pass
    
    async def _agent_specific_initialization(self):
        """智能体特定初始化（子类可重写）"""
        pass
    
    async def _validate_task(self, task: AgentTask) -> bool:
        """验证任务"""
        # 检查任务类型是否支持
        supported_types = [cap.name for cap in self.capabilities]
        if task.task_type not in supported_types:
            return False
        
        # 检查必要的输入数据
        if not task.input_data:
            return False
        
        return True
    
    async def _register_message_handlers(self):
        """注册消息处理器"""
        self.message_handlers.update({
            "collaboration_request": self._handle_collaboration_request,
            "collaboration_response": self._handle_collaboration_response,
            "task_delegation": self._handle_task_delegation,
            "status_inquiry": self._handle_status_inquiry,
            "capability_inquiry": self._handle_capability_inquiry
        })
    
    async def _handle_collaboration_request(self, message: AgentMessage) -> Dict[str, Any]:
        """处理协作请求"""
        try:
            content = message.content
            collaboration_type = content.get("type")
            
            # 评估是否能够协作
            can_collaborate = await self._evaluate_collaboration_capability(collaboration_type, content)
            
            if can_collaborate:
                # 执行协作逻辑
                result = await self._execute_collaboration(collaboration_type, content)
                
                # 发送协作响应
                await self.send_message(
                    message.sender,
                    "collaboration_response",
                    {
                        "collaboration_id": content.get("collaboration_id"),
                        "status": "success",
                        "result": result
                    }
                )
                
                return {"status": "collaboration_accepted"}
            else:
                # 拒绝协作
                await self.send_message(
                    message.sender,
                    "collaboration_response", 
                    {
                        "collaboration_id": content.get("collaboration_id"),
                        "status": "rejected",
                        "reason": "无法处理此类型的协作"
                    }
                )
                
                return {"status": "collaboration_rejected"}
                
        except Exception as e:
            self.logger.error(f"处理协作请求失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_collaboration_response(self, message: AgentMessage) -> Dict[str, Any]:
        """处理协作响应"""
        # 处理协作响应逻辑
        return {"status": "response_received"}
    
    async def _handle_task_delegation(self, message: AgentMessage) -> Dict[str, Any]:
        """处理任务委托"""
        # 处理任务委托逻辑
        return {"status": "delegation_received"}
    
    async def _handle_status_inquiry(self, message: AgentMessage) -> Dict[str, Any]:
        """处理状态查询"""
        status_info = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "current_tasks": len(self.current_tasks),
            "performance_metrics": self.performance_metrics
        }
        
        await self.send_message(
            message.sender,
            "status_response",
            status_info
        )
        
        return {"status": "status_sent"}
    
    async def _handle_capability_inquiry(self, message: AgentMessage) -> Dict[str, Any]:
        """处理能力查询"""
        capability_info = {
            "agent_id": self.agent_id,
            "capabilities": [asdict(cap) for cap in self.capabilities]
        }
        
        await self.send_message(
            message.sender,
            "capability_response",
            capability_info
        )
        
        return {"status": "capabilities_sent"}
    
    async def _evaluate_collaboration_capability(self, collaboration_type: str, data: Dict[str, Any]) -> bool:
        """评估协作能力"""
        # 简化的协作能力评估
        return True
    
    async def _execute_collaboration(self, collaboration_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行协作"""
        # 基础协作逻辑
        return {"collaboration_result": "基础协作完成"}
    
    async def _start_task_processor(self):
        """启动任务处理器"""
        # 任务处理器逻辑
        pass
    
    async def _start_performance_monitoring(self):
        """启动性能监控"""
        async def monitor_performance():
            while True:
                try:
                    await asyncio.sleep(60)  # 每分钟监控一次
                    await self._collect_performance_data()
                except Exception as e:
                    self.logger.error(f"性能监控错误: {e}")
        
        # 启动监控任务
        asyncio.create_task(monitor_performance())
    
    async def _collect_performance_data(self):
        """收集性能数据"""
        # 收集性能数据逻辑
        pass
    
    async def _load_learning_data(self):
        """加载学习数据"""
        # 加载学习数据逻辑
        pass
    
    async def _learn_from_task(self, task: AgentTask, execution_time: float):
        """从任务中学习"""
        # 学习逻辑
        learning_record = {
            "task_type": task.task_type,
            "execution_time": execution_time,
            "success": task.status == "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        # 存储学习数据
        if task.task_type not in self.learning_data:
            self.learning_data[task.task_type] = []
        
        self.learning_data[task.task_type].append(learning_record)
        
        # 保持学习数据在合理范围内
        if len(self.learning_data[task.task_type]) > 50:
            self.learning_data[task.task_type] = self.learning_data[task.task_type][-40:]
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """更新性能指标"""
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["completed_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
        
        # 更新平均完成时间
        total_completed = self.performance_metrics["completed_tasks"]
        if total_completed > 0:
            current_avg = self.performance_metrics["average_completion_time"]
            new_avg = ((current_avg * (total_completed - 1)) + execution_time) / total_completed
            self.performance_metrics["average_completion_time"] = new_avg
        
        # 更新成功率
        total_tasks = self.performance_metrics["total_tasks"]
        self.performance_metrics["success_rate"] = self.performance_metrics["completed_tasks"] / total_tasks
    
    def _update_current_load(self):
        """更新当前负载"""
        # 基于当前任务数量计算负载
        max_concurrent_tasks = 5  # 最大并发任务数
        current_load = len(self.current_tasks) / max_concurrent_tasks
        self.performance_metrics["current_load"] = min(current_load, 1.0)
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "current_tasks": len(self.current_tasks),
            "performance_metrics": self.performance_metrics,
            "collaboration_partners": len(self.collaboration_partners)
        }
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """获取智能体能力"""
        return [asdict(cap) for cap in self.capabilities]


    
    # 抽象方法 - 子类必须实现
    @abstractmethod
    async def _register_capabilities(self):
        """注册智能体能力 - 子类必须实现"""
        pass
    
    @abstractmethod
    async def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """执行任务逻辑 - 子类必须实现"""
        pass
    
    # 可选重写的方法
    async def _register_message_handlers(self):
        """注册消息处理器"""
        self.message_handlers.update({
            "task_assignment": self._handle_task_assignment,
            "collaboration_request": self._handle_collaboration_request,
            "status_inquiry": self._handle_status_inquiry,
            "performance_report": self._handle_performance_report
        })
    
    async def _start_task_processor(self):
        """启动任务处理器"""
        if not self._task_processor_running:
            self._task_processor_running = True
            # 这里可以启动后台任务处理循环
            self.logger.info(f"任务处理器已启动: {self.agent_name}")
    
    async def _start_performance_monitoring(self):
        """启动性能监控"""
        # 这里可以启动性能监控任务
        self.logger.info(f"性能监控已启动: {self.agent_name}")
    
    async def _agent_specific_initialization(self):
        """智能体特定初始化 - 子类可重写"""
        pass
    
    async def _validate_task(self, task: AgentTask) -> bool:
        """验证任务"""
        try:
            # 基础验证
            if not task.task_id or not task.task_type:
                return False
            
            # 检查能力匹配
            required_capabilities = task.metadata.get("required_capabilities", [])
            if required_capabilities:
                agent_capabilities = {cap.name for cap in self.capabilities}
                if not all(cap in agent_capabilities for cap in required_capabilities):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"任务验证异常: {e}")
            return False
    
    def _update_current_load(self):
        """更新当前负载"""
        max_concurrent_tasks = getattr(self.config, 'max_concurrent_tasks', 5)
        self.performance_metrics["current_load"] = len(self.current_tasks) / max_concurrent_tasks
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """更新性能指标"""
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["completed_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
        
        # 更新平均完成时间
        total_completed = self.performance_metrics["completed_tasks"]
        if total_completed > 0:
            current_avg = self.performance_metrics["average_completion_time"]
            new_avg = (current_avg * (total_completed - 1) + execution_time) / total_completed
            self.performance_metrics["average_completion_time"] = new_avg
        
        # 更新成功率
        total_tasks = self.performance_metrics["total_tasks"]
        if total_tasks > 0:
            self.performance_metrics["success_rate"] = self.performance_metrics["completed_tasks"] / total_tasks
    
    async def _learn_from_task(self, task: AgentTask, execution_time: float):
        """从任务中学习"""
        # 记录学习数据
        learning_entry = {
            "task_type": task.task_type,
            "execution_time": execution_time,
            "success": task.status == "completed",
            "timestamp": datetime.now().isoformat(),
            "complexity": task.metadata.get("complexity", 1)
        }
        
        task_type = task.task_type
        if task_type not in self.learning_data:
            self.learning_data[task_type] = []
        
        self.learning_data[task_type].append(learning_entry)
        
        # 保持学习数据在合理范围内
        if len(self.learning_data[task_type]) > 50:
            self.learning_data[task_type] = self.learning_data[task_type][-30:]
    
    async def _load_learning_data(self):
        """加载学习数据"""
        # 这里可以从持久化存储加载学习数据
        self.logger.info(f"学习数据已加载: {self.agent_name}")
    
    # 消息处理器
    async def _handle_task_assignment(self, message: AgentMessage):
        """处理任务分配消息"""
        try:
            task_data = message.content.get("task")
            if task_data:
                task = AgentTask(**task_data)
                result = await self.execute_task(task)
                
                # 发送结果回复
                await self.send_message(
                    message.sender,
                    "task_result",
                    {"task_id": task.task_id, "result": result}
                )
        except Exception as e:
            self.logger.error(f"处理任务分配消息失败: {e}")
    
    async def _handle_collaboration_request(self, message: AgentMessage):
        """处理协作请求消息"""
        try:
            collaboration_type = message.content.get("type")
            self.logger.info(f"收到协作请求: {collaboration_type} from {message.sender}")
            
            # 这里可以实现具体的协作逻辑
            response = {
                "status": "accepted",
                "agent_id": self.agent_id,
                "capabilities": [asdict(cap) for cap in self.capabilities]
            }
            
            await self.send_message(
                message.sender,
                "collaboration_response",
                response
            )
        except Exception as e:
            self.logger.error(f"处理协作请求失败: {e}")
    
    async def _handle_status_inquiry(self, message: AgentMessage):
        """处理状态查询消息"""
        try:
            status_info = {
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "status": self.status.value,
                "current_tasks": len(self.current_tasks),
                "performance_metrics": self.performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.send_message(
                message.sender,
                "status_response",
                status_info
            )
        except Exception as e:
            self.logger.error(f"处理状态查询失败: {e}")
    
    async def _handle_performance_report(self, message: AgentMessage):
        """处理性能报告消息"""
        try:
            report = {
                "agent_id": self.agent_id,
                "performance_metrics": self.performance_metrics,
                "learning_data_summary": {
                    task_type: len(data) for task_type, data in self.learning_data.items()
                },
                "optimization_rules_count": len(self.optimization_rules),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.send_message(
                message.sender,
                "performance_report_response",
                report
            )
        except Exception as e:
            self.logger.error(f"处理性能报告失败: {e}")
    
    # 工具方法
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "performance_metrics": self.performance_metrics,
            "current_tasks_count": len(self.current_tasks),
            "collaboration_partners_count": len(self.collaboration_partners)
        }
    
    def is_available_for_task(self, task_type: str = None) -> bool:
        """检查是否可以接受新任务"""
        if self.status not in [AgentStatus.IDLE, AgentStatus.BUSY]:
            return False
        
        max_concurrent_tasks = getattr(self.config, 'max_concurrent_tasks', 5)
        if len(self.current_tasks) >= max_concurrent_tasks:
            return False
        
        if task_type:
            # 检查是否有处理该类型任务的能力
            task_capabilities = {cap.name for cap in self.capabilities}
            # 这里可以添加更复杂的能力匹配逻辑
        
        return True
    
    async def shutdown(self):
        """关闭智能体"""
        try:
            self.logger.info(f"开始关闭智能体: {self.agent_name}")
            
            self.status = AgentStatus.MAINTENANCE
            self._task_processor_running = False
            
            # 等待当前任务完成
            while self.current_tasks:
                await asyncio.sleep(0.1)
            
            # 发送注销事件
            await self.event_bus.emit(EventType.AGENT_UNREGISTERED, {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name
            })
            
            self.status = AgentStatus.INACTIVE
            self.logger.info(f"智能体已关闭: {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"关闭智能体失败: {e}")


# 智能体工厂函数
def create_agent(agent_type: str, agent_id: str = None, **kwargs) -> AgentBase:
    """创建智能体实例"""
    if agent_id is None:
        agent_id = f"{agent_type}_{str(uuid.uuid4())[:8]}"
    
    # 这里可以根据agent_type创建不同类型的智能体
    # 暂时返回None，具体实现在各个智能体模块中
    raise NotImplementedError(f"智能体类型 {agent_type} 尚未实现")

