"""
PowerAutomation 4.0 Command Master MCP Interface
命令系统MCP接口，实现命令执行的MCP协议通信
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .command_executor import CommandExecutor, CommandResult, get_command_executor
from .command_registry import CommandRegistry, get_command_registry
from core.exceptions import MCPCommunicationError, CommandError, handle_exception
from core.logging_config import get_mcp_logger


@dataclass
class MCPMessage:
    """MCP消息数据结构"""
    id: str
    type: str
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


@dataclass
class MCPCapability:
    """MCP能力描述"""
    name: str
    description: str
    methods: List[str]
    version: str


class CommandMasterMCPInterface:
    """命令系统MCP接口"""
    
    def __init__(self):
        self.logger = get_mcp_logger()
        self.command_executor = get_command_executor()
        self.command_registry = get_command_registry()
        
        # MCP状态
        self.is_initialized = False
        self.session_id = str(uuid.uuid4())
        self.capabilities = self._define_capabilities()
        
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "execute_command": self._handle_execute_command,
            "execute_parallel_commands": self._handle_execute_parallel_commands,
            "get_command_list": self._handle_get_command_list,
            "get_command_info": self._handle_get_command_info,
            "get_command_suggestions": self._handle_get_command_suggestions,
            "get_execution_history": self._handle_get_execution_history,
            "get_stats": self._handle_get_stats,
            "register_command": self._handle_register_command,
            "unregister_command": self._handle_unregister_command,
            "get_capabilities": self._handle_get_capabilities,
            "get_status": self._handle_get_status,
            "shutdown": self._handle_shutdown
        }
        
        # 统计信息
        self.stats = {
            "messages_processed": 0,
            "commands_executed": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "parallel_executions": 0,
            "uptime_start": datetime.now()
        }
    
    def _define_capabilities(self) -> List[MCPCapability]:
        """定义MCP能力"""
        return [
            MCPCapability(
                name="command_execution",
                description="命令执行和管理",
                methods=["execute_command", "execute_parallel_commands", "get_execution_history"],
                version="4.0.0"
            ),
            MCPCapability(
                name="command_registry",
                description="命令注册和发现",
                methods=["get_command_list", "get_command_info", "register_command", "unregister_command"],
                version="4.0.0"
            ),
            MCPCapability(
                name="command_assistance",
                description="命令建议和帮助",
                methods=["get_command_suggestions", "get_command_info"],
                version="4.0.0"
            ),
            MCPCapability(
                name="system_management",
                description="系统管理和监控",
                methods=["get_status", "get_stats", "shutdown"],
                version="4.0.0"
            )
        ]
    
    async def initialize(self) -> bool:
        """初始化命令系统MCP接口"""
        try:
            # 初始化命令注册表
            await self.command_registry.initialize()
            
            self.is_initialized = True
            self.logger.info(f"命令系统MCP接口初始化成功，会话ID: {self.session_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"命令系统MCP接口初始化失败: {e}")
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP消息"""
        try:
            # 解析消息
            mcp_message = self._parse_message(message)
            
            # 更新统计
            self.stats["messages_processed"] += 1
            
            # 路由到处理器
            if mcp_message.method in self.message_handlers:
                handler = self.message_handlers[mcp_message.method]
                result = await handler(mcp_message.params or {})
                
                # 创建响应消息
                response = MCPMessage(
                    id=mcp_message.id,
                    type="response",
                    result=result,
                    timestamp=datetime.now().isoformat()
                )
                
                return asdict(response)
            else:
                # 未知方法
                error_response = MCPMessage(
                    id=mcp_message.id,
                    type="error",
                    error={
                        "code": -32601,
                        "message": f"未知方法: {mcp_message.method}"
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                return asdict(error_response)
                
        except Exception as e:
            self.logger.error(f"处理MCP消息失败: {e}")
            
            # 创建错误响应
            error_response = MCPMessage(
                id=message.get("id", "unknown"),
                type="error",
                error={
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                },
                timestamp=datetime.now().isoformat()
            )
            
            return asdict(error_response)
    
    def _parse_message(self, message: Dict[str, Any]) -> MCPMessage:
        """解析MCP消息"""
        return MCPMessage(
            id=message.get("id", str(uuid.uuid4())),
            type=message.get("type", "request"),
            method=message.get("method"),
            params=message.get("params"),
            result=message.get("result"),
            error=message.get("error"),
            timestamp=message.get("timestamp", datetime.now().isoformat())
        )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        if not self.is_initialized:
            success = await self.initialize()
        else:
            success = True
        
        return {
            "success": success,
            "session_id": self.session_id,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "version": "4.0.0",
            "available_commands": len(self.command_registry.commands)
        }
    
    async def _handle_execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理命令执行请求"""
        try:
            command_line = params.get("command_line", "")
            context = params.get("context", {})
            
            if not command_line:
                return {
                    "success": False,
                    "error": "命令行不能为空"
                }
            
            # 执行命令
            result = await self.command_executor.execute_command(command_line, context)
            
            # 更新统计
            self.stats["commands_executed"] += 1
            if result.success:
                self.stats["successful_commands"] += 1
            else:
                self.stats["failed_commands"] += 1
            
            return {
                "success": True,
                "command_result": {
                    "command": result.command,
                    "args": result.args,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "task_id": result.task_id,
                    "retry_count": result.retry_count
                }
            }
            
        except Exception as e:
            self.stats["failed_commands"] += 1
            self.logger.error(f"命令执行失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_execute_parallel_commands(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理并行命令执行请求"""
        try:
            commands = params.get("commands", [])
            context = params.get("context", {})
            
            if not commands:
                return {
                    "success": False,
                    "error": "命令列表不能为空"
                }
            
            # 执行并行命令
            results = await self.command_executor.execute_parallel_commands(commands, context)
            
            # 更新统计
            self.stats["parallel_executions"] += 1
            self.stats["commands_executed"] += len(results)
            
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            
            self.stats["successful_commands"] += successful_count
            self.stats["failed_commands"] += failed_count
            
            return {
                "success": True,
                "parallel_results": [
                    {
                        "command": r.command,
                        "args": r.args,
                        "success": r.success,
                        "result": r.result,
                        "error": r.error,
                        "execution_time": r.execution_time,
                        "task_id": r.task_id,
                        "retry_count": r.retry_count
                    } for r in results
                ],
                "summary": {
                    "total_commands": len(results),
                    "successful": successful_count,
                    "failed": failed_count,
                    "success_rate": successful_count / len(results) if results else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"并行命令执行失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_command_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取命令列表请求"""
        try:
            category = params.get("category")
            
            commands = self.command_registry.get_commands_by_category(category) if category else self.command_registry.get_all_commands()
            
            command_list = []
            for cmd_name, cmd_info in commands.items():
                command_list.append({
                    "name": cmd_name,
                    "description": cmd_info.get("description", ""),
                    "category": cmd_info.get("category", "unknown"),
                    "usage": cmd_info.get("usage", ""),
                    "examples": cmd_info.get("examples", [])
                })
            
            return {
                "success": True,
                "commands": command_list,
                "total_count": len(command_list),
                "category": category
            }
            
        except Exception as e:
            self.logger.error(f"获取命令列表失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_command_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取命令信息请求"""
        try:
            command_name = params.get("command_name", "")
            
            if not command_name:
                return {
                    "success": False,
                    "error": "命令名称不能为空"
                }
            
            command_info = self.command_registry.get_command(command_name)
            
            if not command_info:
                return {
                    "success": False,
                    "error": f"命令不存在: {command_name}"
                }
            
            return {
                "success": True,
                "command_info": {
                    "name": command_name,
                    "description": command_info.get("description", ""),
                    "category": command_info.get("category", "unknown"),
                    "usage": command_info.get("usage", ""),
                    "examples": command_info.get("examples", []),
                    "parameters": command_info.get("parameters", []),
                    "return_type": command_info.get("return_type", "unknown")
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取命令信息失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_command_suggestions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取命令建议请求"""
        try:
            partial_command = params.get("partial_command", "")
            
            suggestions = await self.command_executor.get_command_suggestions(partial_command)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "partial_command": partial_command,
                "suggestion_count": len(suggestions)
            }
            
        except Exception as e:
            self.logger.error(f"获取命令建议失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_execution_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取执行历史请求"""
        try:
            limit = params.get("limit", 100)
            
            history = await self.command_executor.get_execution_history(limit)
            
            history_data = []
            for result in history:
                history_data.append({
                    "command": result.command,
                    "args": result.args,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "task_id": result.task_id,
                    "error": result.error,
                    "retry_count": result.retry_count
                })
            
            return {
                "success": True,
                "execution_history": history_data,
                "history_count": len(history_data),
                "limit": limit
            }
            
        except Exception as e:
            self.logger.error(f"获取执行历史失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取统计信息请求"""
        try:
            # 获取命令执行器统计
            executor_stats = await self.command_executor.get_stats()
            
            # 计算成功率
            total_commands = self.stats["successful_commands"] + self.stats["failed_commands"]
            success_rate = (self.stats["successful_commands"] / total_commands * 100) if total_commands > 0 else 0
            
            # 计算运行时间
            uptime = datetime.now() - self.stats["uptime_start"]
            
            return {
                "success": True,
                "mcp_stats": self.stats.copy(),
                "executor_stats": executor_stats,
                "success_rate": success_rate,
                "uptime_seconds": uptime.total_seconds(),
                "available_commands": len(self.command_registry.commands),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_register_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理注册命令请求"""
        try:
            command_name = params.get("command_name", "")
            command_info = params.get("command_info", {})
            
            if not command_name or not command_info:
                return {
                    "success": False,
                    "error": "命令名称和命令信息不能为空"
                }
            
            # 注册命令
            success = self.command_registry.register_command(command_name, command_info)
            
            return {
                "success": success,
                "command_name": command_name,
                "message": f"命令 {command_name} 注册{'成功' if success else '失败'}"
            }
            
        except Exception as e:
            self.logger.error(f"注册命令失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_unregister_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理注销命令请求"""
        try:
            command_name = params.get("command_name", "")
            
            if not command_name:
                return {
                    "success": False,
                    "error": "命令名称不能为空"
                }
            
            # 注销命令
            success = self.command_registry.unregister_command(command_name)
            
            return {
                "success": success,
                "command_name": command_name,
                "message": f"命令 {command_name} 注销{'成功' if success else '失败'}"
            }
            
        except Exception as e:
            self.logger.error(f"注销命令失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取能力请求"""
        return {
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "session_id": self.session_id,
            "version": "4.0.0"
        }
    
    async def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取状态请求"""
        uptime = datetime.now() - self.stats["uptime_start"]
        
        return {
            "status": "active" if self.is_initialized else "inactive",
            "session_id": self.session_id,
            "uptime_seconds": uptime.total_seconds(),
            "is_initialized": self.is_initialized,
            "capabilities_count": len(self.capabilities),
            "available_commands": len(self.command_registry.commands),
            "current_load": len(self.command_executor.execution_history) / 1000  # 简单的负载指标
        }
    
    async def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理关闭请求"""
        try:
            # 清理资源
            # 这里可以添加具体的清理逻辑
            
            self.is_initialized = False
            self.logger.info("命令系统MCP接口已关闭")
            
            return {
                "success": True,
                "message": "命令系统MCP接口已成功关闭"
            }
            
        except Exception as e:
            self.logger.error(f"关闭MCP接口失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_notification(self, notification_type: str, data: Dict[str, Any]) -> None:
        """发送通知消息"""
        notification = MCPMessage(
            id=str(uuid.uuid4()),
            type="notification",
            method=notification_type,
            params=data,
            timestamp=datetime.now().isoformat()
        )
        
        # 这里应该发送到MCP协调器或其他订阅者
        self.logger.info(f"发送通知: {notification_type}")
    
    def get_interface_info(self) -> Dict[str, Any]:
        """获取接口信息"""
        return {
            "name": "CommandMasterMCP",
            "version": "4.0.0",
            "description": "命令系统MCP - 负责命令执行、注册和管理",
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "session_id": self.session_id,
            "is_initialized": self.is_initialized,
            "stats": self.stats
        }


# 全局命令系统MCP接口实例
_command_master_mcp = None


def get_command_master_mcp() -> CommandMasterMCPInterface:
    """获取全局命令系统MCP接口实例"""
    global _command_master_mcp
    if _command_master_mcp is None:
        _command_master_mcp = CommandMasterMCPInterface()
    return _command_master_mcp

