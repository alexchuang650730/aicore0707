"""
Claude Integration - Claude集成组件
处理与ClaudEditor的集成和实时同步

支持命令执行结果同步到ClaudEditor界面
"""

import asyncio
import json
import logging
import time
import websockets
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

from .local_adapter_integration import LocalAdapterIntegration, LocalAdapterCommandSession
from .result_capture import ResultCapture

class ClaudeEditorSync:
    """ClaudEditor同步器"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8081/socket.io/"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.is_connected = False
        self.sync_id = str(uuid.uuid4())
        self.logger = logging.getLogger("ClaudeEditorSync")
    
    async def connect(self) -> bool:
        """连接到ClaudEditor"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            
            # 发送连接确认
            await self.send_message({
                "type": "connection",
                "sync_id": self.sync_id,
                "timestamp": time.time(),
                "message": "Mirror Code命令执行器已连接"
            })
            
            self.logger.info(f"已连接到ClaudEditor: {self.websocket_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"连接ClaudEditor失败: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self.websocket and self.is_connected:
                await self.websocket.close()
            self.is_connected = False
            self.logger.info("已断开ClaudEditor连接")
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息到ClaudEditor"""
        try:
            if not self.is_connected or not self.websocket:
                return False
            
            message["sync_id"] = self.sync_id
            message["timestamp"] = message.get("timestamp", time.time())
            
            await self.websocket.send(json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.is_connected = False
            return False
    
    async def sync_command_start(self, session: LocalAdapterCommandSession) -> bool:
        """同步命令开始"""
        return await self.send_message({
            "type": "command_start",
            "session_id": session.session_id,
            "command": session.command,
            "working_dir": session.working_dir,
            "start_time": session.start_time
        })
    
    async def sync_command_output(self, session_id: str, output: str, output_type: str = "stdout") -> bool:
        """同步命令输出"""
        return await self.send_message({
            "type": "command_output",
            "session_id": session_id,
            "output": output,
            "output_type": output_type,
            "timestamp": time.time()
        })
    
    async def sync_command_complete(self, session: LocalAdapterCommandSession, final_output: str) -> bool:
        """同步命令完成"""
        return await self.send_message({
            "type": "command_complete",
            "session_id": session.session_id,
            "status": session.status,
            "return_code": session.return_code,
            "duration": (session.end_time or time.time()) - session.start_time,
            "final_output": final_output
        })

class ClaudeIntegration:
    """Claude集成管理器 - 统一管理命令执行和结果同步"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Claude集成管理器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 核心组件
        self.command_executor = LocalAdapterIntegration(self.config.get("local_adapter_integration", {}))
        self.result_capture = ResultCapture(self.config.get("result_capture", {}))
        
        # ClaudEditor同步
        websocket_url = self.config.get("claudeditor_websocket", "ws://localhost:8081/socket.io/")
        self.claudeditor_sync = ClaudeEditorSync(websocket_url)
        
        # 状态管理
        self.active_integrations = {}
        self.sync_enabled = self.config.get("sync_enabled", True)
        
        # 设置回调
        self._setup_callbacks()
        
        self.logger.info("Claude集成管理器初始化完成")
    
    async def start(self) -> Dict[str, Any]:
        """启动集成服务"""
        try:
            # 连接到ClaudEditor
            if self.sync_enabled:
                connected = await self.claudeditor_sync.connect()
                if not connected:
                    self.logger.warning("无法连接到ClaudEditor，将在本地模式运行")
            
            self.logger.info("Claude集成服务已启动")
            
            return {
                "success": True,
                "sync_enabled": self.sync_enabled,
                "claudeditor_connected": self.claudeditor_sync.is_connected,
                "message": "集成服务已启动"
            }
            
        except Exception as e:
            self.logger.error(f"启动集成服务失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop(self) -> Dict[str, Any]:
        """停止集成服务"""
        try:
            # 断开ClaudEditor连接
            await self.claudeditor_sync.disconnect()
            
            # 清理活跃集成
            for integration_id in list(self.active_integrations.keys()):
                await self.cleanup_integration(integration_id)
            
            self.logger.info("Claude集成服务已停止")
            
            return {
                "success": True,
                "message": "集成服务已停止"
            }
            
        except Exception as e:
            self.logger.error(f"停止集成服务失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_claude_with_sync(self, 
                                     model: str = "claude-sonnet-4-20250514",
                                     working_dir: Optional[str] = None,
                                     additional_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行Claude命令并同步到ClaudEditor
        
        Args:
            model: Claude模型名称
            working_dir: 工作目录
            additional_args: 额外参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            self.logger.info(f"执行Claude命令并同步: {model}")
            
            # 创建集成会话
            integration_id = f"integration_{int(time.time())}_{len(self.active_integrations)}"
            
            # 执行命令
            result = await self.command_executor.execute_claude_command(
                model=model,
                working_dir=working_dir,
                additional_args=additional_args
            )
            
            if result.get("success"):
                session_id = result["session_id"]
                
                # 记录集成信息
                self.active_integrations[integration_id] = {
                    "session_id": session_id,
                    "start_time": time.time(),
                    "model": model,
                    "working_dir": working_dir or self.command_executor.default_working_dir,
                    "status": "running"
                }
                
                # 开始结果捕获
                await self.result_capture.start_capture(session_id)
                
                result["integration_id"] = integration_id
                result["sync_enabled"] = self.sync_enabled
                result["claudeditor_connected"] = self.claudeditor_sync.is_connected
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Claude命令失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_integration_status(self, integration_id: str) -> Dict[str, Any]:
        """
        获取集成状态
        
        Args:
            integration_id: 集成ID
            
        Returns:
            Dict: 状态信息
        """
        try:
            if integration_id not in self.active_integrations:
                return {
                    "success": False,
                    "error": f"集成不存在: {integration_id}"
                }
            
            integration = self.active_integrations[integration_id]
            session_id = integration["session_id"]
            
            # 获取命令状态
            command_status = await self.command_executor.get_session_status(session_id)
            
            # 获取捕获的输出
            captured_output = await self.result_capture.get_captured_output(session_id, "structured")
            
            return {
                "success": True,
                "integration_id": integration_id,
                "integration_info": integration,
                "command_status": command_status,
                "captured_output": captured_output,
                "sync_status": {
                    "enabled": self.sync_enabled,
                    "connected": self.claudeditor_sync.is_connected
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取集成状态失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_live_output(self, integration_id: str, format_type: str = "html"):
        """
        获取实时输出流
        
        Args:
            integration_id: 集成ID
            format_type: 格式类型
            
        Yields:
            Dict: 输出数据
        """
        try:
            if integration_id not in self.active_integrations:
                yield {
                    "success": False,
                    "error": f"集成不存在: {integration_id}"
                }
                return
            
            session_id = self.active_integrations[integration_id]["session_id"]
            
            async for output_chunk in self.result_capture.stream_output(session_id, format_type):
                yield {
                    "success": True,
                    "integration_id": integration_id,
                    "output_chunk": output_chunk
                }
                
        except Exception as e:
            self.logger.error(f"获取实时输出失败: {e}")
            yield {
                "success": False,
                "error": str(e)
            }
    
    async def terminate_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        终止集成
        
        Args:
            integration_id: 集成ID
            
        Returns:
            Dict: 终止结果
        """
        try:
            if integration_id not in self.active_integrations:
                return {
                    "success": False,
                    "error": f"集成不存在: {integration_id}"
                }
            
            integration = self.active_integrations[integration_id]
            session_id = integration["session_id"]
            
            # 终止命令执行
            terminate_result = await self.command_executor.terminate_session(session_id)
            
            # 完成结果捕获
            capture_result = await self.result_capture.finish_capture(session_id)
            
            # 更新集成状态
            integration["status"] = "terminated"
            integration["end_time"] = time.time()
            
            # 同步到ClaudEditor
            if self.sync_enabled and self.claudeditor_sync.is_connected:
                session = self.command_executor.active_sessions.get(session_id)
                if session:
                    await self.claudeditor_sync.sync_command_complete(
                        session, 
                        capture_result.get("final_report", {}).get("formats", {}).get("html", "")
                    )
            
            return {
                "success": True,
                "integration_id": integration_id,
                "terminate_result": terminate_result,
                "capture_result": capture_result
            }
            
        except Exception as e:
            self.logger.error(f"终止集成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        清理集成数据
        
        Args:
            integration_id: 集成ID
            
        Returns:
            Dict: 清理结果
        """
        try:
            if integration_id not in self.active_integrations:
                return {
                    "success": False,
                    "error": f"集成不存在: {integration_id}"
                }
            
            integration = self.active_integrations[integration_id]
            session_id = integration["session_id"]
            
            # 清理结果捕获数据
            await self.result_capture.cleanup_session(session_id)
            
            # 移除集成记录
            del self.active_integrations[integration_id]
            
            self.logger.info(f"清理集成数据: {integration_id}")
            
            return {
                "success": True,
                "integration_id": integration_id,
                "message": "集成数据已清理"
            }
            
        except Exception as e:
            self.logger.error(f"清理集成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _setup_callbacks(self):
        """设置回调函数"""
        # 命令执行回调
        self.command_executor.add_output_callback(self._on_command_output)
        self.command_executor.add_status_callback(self._on_command_status)
        
        # 结果捕获回调
        self.result_capture.add_stream_callback(self._on_capture_stream)
        self.result_capture.add_completion_callback(self._on_capture_completion)
    
    async def _on_command_output(self, session: LocalAdapterCommandSession, output: str, output_type: str = "stdout"):
        """命令输出回调"""
        try:
            # 捕获输出
            await self.result_capture.capture_output(session.session_id, output)
            
            # 同步到ClaudEditor
            if self.sync_enabled and self.claudeditor_sync.is_connected:
                await self.claudeditor_sync.sync_command_output(session.session_id, output)
                
        except Exception as e:
            self.logger.error(f"处理命令输出失败: {e}")
    
    async def _on_command_status(self, session: LocalAdapterCommandSession, event: str):
        """命令状态回调"""
        try:
            if event == "started" and self.sync_enabled and self.claudeditor_sync.is_connected:
                await self.claudeditor_sync.sync_command_start(session)
            elif event == "completed" and self.sync_enabled and self.claudeditor_sync.is_connected:
                # 获取最终输出
                final_output_result = await self.result_capture.get_captured_output(session.session_id, "html")
                final_output = final_output_result.get("output", "") if final_output_result.get("success") else ""
                
                await self.claudeditor_sync.sync_command_complete(session, final_output)
                
        except Exception as e:
            self.logger.error(f"处理命令状态失败: {e}")
    
    async def _on_capture_stream(self, session_id: str, output_entry: Dict[str, Any], formatted_buffer: Dict[str, Any]):
        """捕获流回调"""
        # 这里可以添加额外的流处理逻辑
        pass
    
    async def _on_capture_completion(self, session_id: str, final_report: Dict[str, Any]):
        """捕获完成回调"""
        # 这里可以添加完成后的处理逻辑
        self.logger.info(f"会话 {session_id} 捕获完成，共 {final_report['entry_count']} 条记录")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("ClaudeIntegration")
        
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
async def execute_claude_with_sync(model: str = "claude-sonnet-4-20250514",
                                 working_dir: Optional[str] = None,
                                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行Claude命令并同步到ClaudEditor的便捷函数
    
    Args:
        model: Claude模型名称
        working_dir: 工作目录
        config: 配置信息
        
    Returns:
        Dict: 执行结果
    """
    integration = ClaudeIntegration(config)
    await integration.start()
    
    try:
        result = await integration.execute_claude_with_sync(model, working_dir)
        return result
    finally:
        await integration.stop()

