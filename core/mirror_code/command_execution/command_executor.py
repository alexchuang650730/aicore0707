"""
Command Executor - 命令执行器
在Mac本地执行claude命令并捕获结果

支持实时输出捕获和结果同步
"""

import asyncio
import json
import logging
import os
import sys
import time
import pty
import select
import termios
import tty
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime
import subprocess
import threading
import queue

class CommandSession:
    """命令会话"""
    
    def __init__(self, session_id: str, command: str, working_dir: str):
        self.session_id = session_id
        self.command = command
        self.working_dir = working_dir
        self.start_time = time.time()
        self.end_time = None
        self.status = "running"  # running, completed, failed, terminated
        self.return_code = None
        self.output_buffer = []
        self.error_buffer = []
        self.process = None
        self.pty_master = None
        self.pty_slave = None
        
    def add_output(self, data: str, is_error: bool = False):
        """添加输出数据"""
        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "data": data,
            "type": "stderr" if is_error else "stdout"
        }
        
        if is_error:
            self.error_buffer.append(entry)
        else:
            self.output_buffer.append(entry)
    
    def get_full_output(self) -> str:
        """获取完整输出"""
        all_output = self.output_buffer + self.error_buffer
        all_output.sort(key=lambda x: x["timestamp"])
        return "".join([entry["data"] for entry in all_output])
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "session_id": self.session_id,
            "command": self.command,
            "working_dir": self.working_dir,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time or time.time()) - self.start_time,
            "return_code": self.return_code,
            "output_lines": len(self.output_buffer),
            "error_lines": len(self.error_buffer)
        }

class CommandExecutor:
    """命令执行器 - 处理Mac本地命令执行"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化命令执行器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 会话管理
        self.active_sessions = {}
        self.session_counter = 0
        
        # 回调函数
        self.output_callbacks = []
        self.status_callbacks = []
        
        # 默认配置
        self.default_working_dir = self.config.get("default_working_dir", "/Users/alexchuang/Desktop/alex/tests/package")
        self.max_output_buffer = self.config.get("max_output_buffer", 10000)
        self.command_timeout = self.config.get("command_timeout", 300)  # 5分钟
        
        self.logger.info("命令执行器初始化完成")
    
    async def execute_claude_command(self, 
                                   model: str = "claude-sonnet-4-20250514",
                                   working_dir: Optional[str] = None,
                                   additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行claude命令
        
        Args:
            model: Claude模型名称
            working_dir: 工作目录
            additional_args: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 构建命令
            command_parts = ["claude", "--model", model]
            if additional_args:
                command_parts.extend(additional_args)
            
            command = " ".join(command_parts)
            work_dir = working_dir or self.default_working_dir
            
            self.logger.info(f"执行Claude命令: {command} (工作目录: {work_dir})")
            
            # 创建会话
            session = await self.create_session(command, work_dir)
            
            # 执行命令
            result = await self.execute_session(session.session_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Claude命令失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_session(self, command: str, working_dir: str) -> CommandSession:
        """
        创建命令会话
        
        Args:
            command: 要执行的命令
            working_dir: 工作目录
            
        Returns:
            CommandSession: 命令会话
        """
        self.session_counter += 1
        session_id = f"cmd_{int(time.time())}_{self.session_counter}"
        
        session = CommandSession(session_id, command, working_dir)
        self.active_sessions[session_id] = session
        
        self.logger.info(f"创建命令会话: {session_id}")
        
        # 通知状态回调
        await self._notify_status_callbacks(session, "created")
        
        return session
    
    async def execute_session(self, session_id: str) -> Dict[str, Any]:
        """
        执行命令会话
        
        Args:
            session_id: 会话ID
            
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
            
            # 验证工作目录
            if not os.path.exists(session.working_dir):
                session.status = "failed"
                return {
                    "success": False,
                    "error": f"工作目录不存在: {session.working_dir}",
                    "session_id": session_id
                }
            
            # 使用PTY执行命令以获得更好的交互性
            result = await self._execute_with_pty(session)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行会话失败: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].status = "failed"
            
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_with_pty(self, session: CommandSession) -> Dict[str, Any]:
        """
        使用PTY执行命令
        
        Args:
            session: 命令会话
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 创建PTY
            master, slave = pty.openpty()
            session.pty_master = master
            session.pty_slave = slave
            
            # 启动进程
            process = await asyncio.create_subprocess_exec(
                *session.command.split(),
                cwd=session.working_dir,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                preexec_fn=os.setsid
            )
            
            session.process = process
            session.status = "running"
            
            # 通知状态回调
            await self._notify_status_callbacks(session, "started")
            
            # 关闭slave端（子进程会使用它）
            os.close(slave)
            
            # 异步读取输出
            output_task = asyncio.create_task(self._read_pty_output(session))
            
            # 等待进程完成
            try:
                return_code = await asyncio.wait_for(
                    process.wait(), 
                    timeout=self.command_timeout
                )
                session.return_code = return_code
                session.status = "completed" if return_code == 0 else "failed"
                
            except asyncio.TimeoutError:
                # 超时，终止进程
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                
                session.status = "terminated"
                session.return_code = -1
            
            # 等待输出读取完成
            await output_task
            
            session.end_time = time.time()
            
            # 关闭PTY
            os.close(master)
            
            # 通知状态回调
            await self._notify_status_callbacks(session, "completed")
            
            result = {
                "success": session.status == "completed",
                "session_id": session.session_id,
                "status": session.status,
                "return_code": session.return_code,
                "output": session.get_full_output(),
                "duration": session.end_time - session.start_time,
                "command": session.command,
                "working_dir": session.working_dir
            }
            
            if session.status != "completed":
                result["error"] = f"命令执行失败，状态: {session.status}"
            
            return result
            
        except Exception as e:
            session.status = "failed"
            session.end_time = time.time()
            
            if session.pty_master:
                try:
                    os.close(session.pty_master)
                except:
                    pass
            
            raise e
    
    async def _read_pty_output(self, session: CommandSession):
        """
        异步读取PTY输出
        
        Args:
            session: 命令会话
        """
        try:
            loop = asyncio.get_event_loop()
            
            while session.process and session.process.returncode is None:
                try:
                    # 使用select检查是否有数据可读
                    ready, _, _ = select.select([session.pty_master], [], [], 0.1)
                    
                    if ready:
                        data = os.read(session.pty_master, 1024)
                        if data:
                            text = data.decode('utf-8', errors='replace')
                            session.add_output(text)
                            
                            # 通知输出回调
                            await self._notify_output_callbacks(session, text)
                        else:
                            break
                    else:
                        # 短暂休眠避免CPU占用过高
                        await asyncio.sleep(0.01)
                        
                except OSError:
                    # PTY已关闭
                    break
                except Exception as e:
                    self.logger.error(f"读取PTY输出失败: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"PTY输出读取异常: {e}")
    
    def add_output_callback(self, callback: Callable):
        """添加输出回调"""
        self.output_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable):
        """添加状态回调"""
        self.status_callbacks.append(callback)
    
    async def _notify_output_callbacks(self, session: CommandSession, output: str):
        """通知输出回调"""
        for callback in self.output_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session, output)
                else:
                    callback(session, output)
            except Exception as e:
                self.logger.error(f"输出回调失败: {e}")
    
    async def _notify_status_callbacks(self, session: CommandSession, event: str):
        """通知状态回调"""
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session, event)
                else:
                    callback(session, event)
            except Exception as e:
                self.logger.error(f"状态回调失败: {e}")
    
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
                "session": session.get_status_info()
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
            "total_count": len(sessions)
        }
    
    async def terminate_session(self, session_id: str) -> Dict[str, Any]:
        """
        终止会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 终止结果
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": f"会话不存在: {session_id}"
                }
            
            session = self.active_sessions[session_id]
            
            if session.process and session.process.returncode is None:
                session.process.terminate()
                try:
                    await asyncio.wait_for(session.process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    session.process.kill()
                    await session.process.wait()
            
            session.status = "terminated"
            session.end_time = time.time()
            
            # 通知状态回调
            await self._notify_status_callbacks(session, "terminated")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "会话已终止"
            }
            
        except Exception as e:
            self.logger.error(f"终止会话失败: {e}")
            return {
                "success": False,
                "error": str(e)
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
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("CommandExecutor")
        
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
async def execute_claude_command(model: str = "claude-sonnet-4-20250514",
                               working_dir: Optional[str] = None,
                               config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行Claude命令的便捷函数
    
    Args:
        model: Claude模型名称
        working_dir: 工作目录
        config: 配置信息
        
    Returns:
        Dict: 执行结果
    """
    executor = CommandExecutor(config)
    return await executor.execute_claude_command(model, working_dir)

