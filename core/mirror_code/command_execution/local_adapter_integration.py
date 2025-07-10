"""
Local Adapter Integration - Local Adapter集成组件
通过Local Adapter MCP执行命令，避免重复实现

整合Mirror Code和Local Adapter MCP的功能
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

# 添加Local Adapter MCP路径
current_dir = os.path.dirname(os.path.abspath(__file__))
local_adapter_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 
                                 "components", "local_adapter_mcp")
if local_adapter_path not in sys.path:
    sys.path.insert(0, local_adapter_path)

try:
    from local_adapter_engine import LocalAdapterEngine
    from platform.macos_terminal_mcp import MacOSTerminalMCP
    from platform.command_adapter import CrossPlatformCommandAdapter
    from platform.platform_detector import PlatformDetector
except ImportError as e:
    logging.warning(f"无法导入Local Adapter组件: {e}")
    LocalAdapterEngine = None
    MacOSTerminalMCP = None
    CrossPlatformCommandAdapter = None
    PlatformDetector = None

class LocalAdapterCommandSession:
    """通过Local Adapter的命令会话"""
    
    def __init__(self, session_id: str, command: str, working_dir: str, platform: str):
        self.session_id = session_id
        self.command = command
        self.working_dir = working_dir
        self.platform = platform
        self.start_time = time.time()
        self.end_time = None
        self.status = "created"  # created, running, completed, failed, terminated
        self.result = None
        self.output_callbacks = []
        
    def add_output_callback(self, callback: Callable):
        """添加输出回调"""
        self.output_callbacks.append(callback)
    
    async def notify_output(self, output: str, output_type: str = "stdout"):
        """通知输出回调"""
        for callback in self.output_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self, output, output_type)
                else:
                    callback(self, output, output_type)
            except Exception as e:
                logging.error(f"输出回调失败: {e}")
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "session_id": self.session_id,
            "command": self.command,
            "working_dir": self.working_dir,
            "platform": self.platform,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time or time.time()) - self.start_time,
            "has_result": self.result is not None
        }

class LocalAdapterIntegration:
    """Local Adapter集成器 - 通过Local Adapter MCP执行命令"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Local Adapter集成器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 检查Local Adapter可用性
        if LocalAdapterEngine is None:
            self.logger.error("Local Adapter MCP不可用")
            self.available = False
            # 即使不可用，也要完成基本初始化
            self.local_adapter = None
            self.platform_detector = None
            self.current_platform = "unknown"
            self.terminal_mcp = None
        else:
            # 初始化组件
            self.local_adapter = LocalAdapterEngine()
            self.platform_detector = PlatformDetector() if PlatformDetector else None
            self.current_platform = self._detect_platform()
            
            # 初始化平台特定的终端MCP
            self.terminal_mcp = self._init_terminal_mcp()
            self.available = True
        
        # 会话管理
        self.active_sessions = {}
        self.session_counter = 0
        
        # 全局回调函数
        self.global_output_callbacks = []
        self.global_status_callbacks = []
        
        # 默认配置
        self.default_working_dir = self.config.get("default_working_dir", "/Users/alexchuang/Desktop/alex/tests/package")
        self.command_timeout = self.config.get("command_timeout", 300)  # 5分钟
        
        self.logger.info(f"Local Adapter集成器初始化完成 - 平台: {self.current_platform}, 可用: {self.available}")
    
    def _detect_platform(self) -> str:
        """检测当前平台"""
        try:
            if self.platform_detector:
                platform_info = self.platform_detector.detect_platform()
                return platform_info.get("platform", "unknown")
            else:
                # 简单的平台检测
                import platform
                system = platform.system().lower()
                if system == "darwin":
                    return "macos"
                elif system == "linux":
                    return "linux"
                elif system == "windows":
                    return "windows"
                else:
                    return "unknown"
        except Exception as e:
            self.logger.error(f"平台检测失败: {e}")
            return "unknown"
    
    def _init_terminal_mcp(self):
        """初始化平台特定的终端MCP"""
        try:
            if self.current_platform == "macos" and MacOSTerminalMCP:
                return MacOSTerminalMCP()
            else:
                # 对于其他平台，使用通用的Local Adapter
                return self.local_adapter
        except Exception as e:
            self.logger.error(f"初始化终端MCP失败: {e}")
            return self.local_adapter
    
    async def execute_claude_command(self, 
                                   model: str = "claude-sonnet-4-20250514",
                                   working_dir: Optional[str] = None,
                                   additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        通过Local Adapter执行Claude命令
        
        Args:
            model: Claude模型名称
            working_dir: 工作目录
            additional_args: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        if not self.available:
            return {
                "success": False,
                "error": "Local Adapter不可用"
            }
        
        try:
            # 构建命令
            command = "claude"
            args = ["--model", model]
            if additional_args:
                args.extend(additional_args)
            
            work_dir = working_dir or self.default_working_dir
            
            self.logger.info(f"通过Local Adapter执行Claude命令: {command} {' '.join(args)} (工作目录: {work_dir})")
            
            # 创建会话
            session = await self.create_session(f"{command} {' '.join(args)}", work_dir)
            
            # 执行命令
            result = await self.execute_session(session.session_id, command, args, work_dir)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Claude命令失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_command(self, 
                            command: str,
                            args: Optional[List[str]] = None,
                            working_dir: Optional[str] = None,
                            env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        通过Local Adapter执行任意命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        if not self.available:
            return {
                "success": False,
                "error": "Local Adapter不可用"
            }
        
        try:
            args = args or []
            work_dir = working_dir or self.default_working_dir
            
            full_command = f"{command} {' '.join(args)}"
            self.logger.info(f"通过Local Adapter执行命令: {full_command} (工作目录: {work_dir})")
            
            # 创建会话
            session = await self.create_session(full_command, work_dir)
            
            # 执行命令
            result = await self.execute_session(session.session_id, command, args, work_dir, env)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_session(self, command: str, working_dir: str) -> LocalAdapterCommandSession:
        """
        创建命令会话
        
        Args:
            command: 要执行的命令
            working_dir: 工作目录
            
        Returns:
            LocalAdapterCommandSession: 命令会话
        """
        self.session_counter += 1
        session_id = f"la_cmd_{int(time.time())}_{self.session_counter}"
        
        session = LocalAdapterCommandSession(session_id, command, working_dir, self.current_platform)
        self.active_sessions[session_id] = session
        
        self.logger.info(f"创建Local Adapter命令会话: {session_id}")
        
        return session
    
    async def execute_session(self, 
                            session_id: str, 
                            command: str, 
                            args: List[str], 
                            working_dir: str,
                            env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        执行命令会话
        
        Args:
            session_id: 会话ID
            command: 命令
            args: 参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": f"会话不存在: {session_id}"
                }
            
            session = self.active_sessions[session_id]
            session.status = "running"
            
            # 验证工作目录
            if not os.path.exists(working_dir):
                session.status = "failed"
                return {
                    "success": False,
                    "error": f"工作目录不存在: {working_dir}",
                    "session_id": session_id
                }
            
            # 通过终端MCP执行命令
            if hasattr(self.terminal_mcp, 'execute_command'):
                # 使用平台特定的终端MCP
                result = await self.terminal_mcp.execute_command(
                    command=command,
                    args=args,
                    working_dir=working_dir,
                    env=env
                )
            else:
                # 使用通用的Local Adapter
                result = await self._execute_via_local_adapter(command, args, working_dir, env)
            
            session.result = result
            session.end_time = time.time()
            
            if result.get("success"):
                session.status = "completed"
                
                # 通知输出回调
                if result.get("stdout"):
                    await session.notify_output(result["stdout"], "stdout")
                    # 调用全局输出回调
                    await self._notify_global_output_callbacks(session, result["stdout"], "stdout")
                if result.get("stderr"):
                    await session.notify_output(result["stderr"], "stderr")
                    # 调用全局输出回调
                    await self._notify_global_output_callbacks(session, result["stderr"], "stderr")
                
                # 调用全局状态回调
                await self._notify_global_status_callbacks(session, "completed")
            else:
                session.status = "failed"
                # 调用全局状态回调
                await self._notify_global_status_callbacks(session, "failed")
            
            # 构建返回结果
            execution_result = {
                "success": result.get("success", False),
                "session_id": session_id,
                "status": session.status,
                "return_code": result.get("returncode", -1),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "duration": session.end_time - session.start_time,
                "command": session.command,
                "working_dir": working_dir,
                "platform": self.current_platform
            }
            
            if not result.get("success"):
                execution_result["error"] = result.get("error", "命令执行失败")
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"执行会话失败: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = "failed"
                self.active_sessions[session_id].end_time = time.time()
            
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_via_local_adapter(self, 
                                       command: str, 
                                       args: List[str], 
                                       working_dir: str,
                                       env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        通过Local Adapter执行命令
        
        Args:
            command: 命令
            args: 参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 构建完整命令
            full_command = [command] + args
            
            # 设置环境变量
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=exec_env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.command_timeout
                )
            except asyncio.TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                
                return {
                    "success": False,
                    "error": "命令执行超时",
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "命令执行超时"
                }
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 会话状态
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "success": True,
                "session": session.get_status_info(),
                "result": session.result
            }
        else:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}"
            }
    
    async def list_sessions(self) -> Dict[str, Any]:
        """
        列出所有会话
        
        Returns:
            Dict: 会话列表
        """
        sessions = []
        for session in self.active_sessions.values():
            sessions.append(session.get_status_info())
        
        return {
            "success": True,
            "sessions": sessions,
            "total_count": len(sessions),
            "platform": self.current_platform,
            "local_adapter_available": self.available
        }
    
    async def cleanup_completed_sessions(self):
        """清理已完成的会话"""
        completed_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.status in ["completed", "failed", "terminated"]:
                completed_sessions.append(session_id)
        
        for session_id in completed_sessions:
            del self.active_sessions[session_id]
        
        self.logger.info(f"清理了 {len(completed_sessions)} 个已完成的会话")
    
    def add_output_callback(self, callback: Callable):
        """添加全局输出回调"""
        self.global_output_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable):
        """添加全局状态回调"""
        self.global_status_callbacks.append(callback)
    
    def add_session_output_callback(self, session_id: str, callback: Callable):
        """为特定会话添加输出回调"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].add_output_callback(callback)
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            "current_platform": self.current_platform,
            "local_adapter_available": self.available,
            "terminal_mcp_type": type(self.terminal_mcp).__name__ if self.terminal_mcp else None,
            "default_working_dir": self.default_working_dir
        }
    
    async def _notify_global_output_callbacks(self, session: LocalAdapterCommandSession, output: str, output_type: str = "stdout"):
        """通知全局输出回调"""
        for callback in self.global_output_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session, output, output_type)
                else:
                    callback(session, output, output_type)
            except Exception as e:
                self.logger.error(f"全局输出回调失败: {e}")
    
    async def _notify_global_status_callbacks(self, session: LocalAdapterCommandSession, event: str):
        """通知全局状态回调"""
        for callback in self.global_status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session, event)
                else:
                    callback(session, event)
            except Exception as e:
                self.logger.error(f"全局状态回调失败: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("LocalAdapterIntegration")
        
        if logger.handlers:
            return logger
        
        level = self.config.get("logging", {}).get("level", "INFO")
        logger.setLevel(getattr(logging, level))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

# 便捷函数
async def execute_claude_via_local_adapter(model: str = "claude-sonnet-4-20250514",
                                         working_dir: Optional[str] = None,
                                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    通过Local Adapter执行Claude命令的便捷函数
    
    Args:
        model: Claude模型名称
        working_dir: 工作目录
        config: 配置信息
        
    Returns:
        Dict: 执行结果
    """
    integration = LocalAdapterIntegration(config)
    return await integration.execute_claude_command(model, working_dir)

