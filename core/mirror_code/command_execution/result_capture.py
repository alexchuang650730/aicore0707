"""
Result Capture - 结果捕获器
实时捕获命令执行结果并格式化输出

支持多种输出格式和实时流式处理
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime
import html
import base64

class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def format_ansi_to_html(text: str) -> str:
        """将ANSI转义序列转换为HTML"""
        # ANSI颜色代码映射
        ansi_colors = {
            '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
            '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
            '90': 'gray', '91': 'lightred', '92': 'lightgreen', '93': 'lightyellow',
            '94': 'lightblue', '95': 'lightmagenta', '96': 'lightcyan', '97': 'lightwhite'
        }
        
        # 转义HTML特殊字符
        text = html.escape(text)
        
        # 处理ANSI转义序列
        # 颜色代码
        for code, color in ansi_colors.items():
            text = re.sub(f'\033\\[{code}m', f'<span style="color: {color}">', text)
        
        # 粗体
        text = re.sub(r'\033\[1m', '<strong>', text)
        text = re.sub(r'\033\[22m', '</strong>', text)
        
        # 斜体
        text = re.sub(r'\033\[3m', '<em>', text)
        text = re.sub(r'\033\[23m', '</em>', text)
        
        # 下划线
        text = re.sub(r'\033\[4m', '<u>', text)
        text = re.sub(r'\033\[24m', '</u>', text)
        
        # 重置所有格式
        text = re.sub(r'\033\[0m', '</span></strong></em></u>', text)
        
        # 清除其他ANSI序列
        text = re.sub(r'\033\[[0-9;]*m', '', text)
        
        return text
    
    @staticmethod
    def format_as_markdown(text: str) -> str:
        """格式化为Markdown"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 检测代码块
            if line.strip().startswith('```'):
                formatted_lines.append(line)
            # 检测命令提示符
            elif re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+.*\$', line):
                formatted_lines.append(f"```bash\n{line}\n```")
            # 检测错误信息
            elif 'error' in line.lower() or 'failed' in line.lower():
                formatted_lines.append(f"**Error:** {line}")
            # 检测警告信息
            elif 'warning' in line.lower() or 'warn' in line.lower():
                formatted_lines.append(f"**Warning:** {line}")
            # 检测成功信息
            elif 'success' in line.lower() or 'completed' in line.lower():
                formatted_lines.append(f"**Success:** {line}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def extract_claude_response(text: str) -> Optional[Dict[str, Any]]:
        """提取Claude响应内容"""
        try:
            # 查找Claude的响应模式
            patterns = [
                r'Claude:\s*(.*?)(?=\n\n|\n$|$)',
                r'Response:\s*(.*?)(?=\n\n|\n$|$)',
                r'Assistant:\s*(.*?)(?=\n\n|\n$|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                if matches:
                    return {
                        "type": "claude_response",
                        "content": matches[-1].strip(),
                        "timestamp": time.time()
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"提取Claude响应失败: {e}")
            return None

class ResultCapture:
    """结果捕获器 - 实时捕获和处理命令输出"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化结果捕获器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 捕获配置
        self.capture_format = self.config.get("capture_format", "both")  # text, html, markdown, both
        self.max_buffer_size = self.config.get("max_buffer_size", 1024 * 1024)  # 1MB
        self.enable_streaming = self.config.get("enable_streaming", True)
        self.chunk_size = self.config.get("chunk_size", 1024)
        
        # 输出缓冲区
        self.output_buffers = {}
        self.formatted_buffers = {}
        
        # 回调函数
        self.stream_callbacks = []
        self.completion_callbacks = []
        
        # 格式化器
        self.formatter = OutputFormatter()
        
        self.logger.info("结果捕获器初始化完成")
    
    async def start_capture(self, session_id: str) -> Dict[str, Any]:
        """
        开始捕获会话输出
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 启动结果
        """
        try:
            if session_id in self.output_buffers:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 已在捕获中"
                }
            
            # 初始化缓冲区
            self.output_buffers[session_id] = {
                "raw_output": [],
                "total_size": 0,
                "start_time": time.time(),
                "last_update": time.time()
            }
            
            self.formatted_buffers[session_id] = {
                "html": "",
                "markdown": "",
                "claude_responses": []
            }
            
            self.logger.info(f"开始捕获会话输出: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "开始捕获输出"
            }
            
        except Exception as e:
            self.logger.error(f"开始捕获失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def capture_output(self, session_id: str, output: str, output_type: str = "stdout") -> Dict[str, Any]:
        """
        捕获输出数据
        
        Args:
            session_id: 会话ID
            output: 输出内容
            output_type: 输出类型 (stdout, stderr)
            
        Returns:
            Dict: 捕获结果
        """
        try:
            if session_id not in self.output_buffers:
                await self.start_capture(session_id)
            
            buffer = self.output_buffers[session_id]
            formatted_buffer = self.formatted_buffers[session_id]
            
            # 检查缓冲区大小
            if buffer["total_size"] + len(output) > self.max_buffer_size:
                # 清理旧数据
                await self._cleanup_buffer(session_id)
            
            # 添加原始输出
            timestamp = time.time()
            output_entry = {
                "timestamp": timestamp,
                "type": output_type,
                "content": output,
                "size": len(output)
            }
            
            buffer["raw_output"].append(output_entry)
            buffer["total_size"] += len(output)
            buffer["last_update"] = timestamp
            
            # 格式化输出
            if self.capture_format in ["html", "both"]:
                html_output = self.formatter.format_ansi_to_html(output)
                formatted_buffer["html"] += html_output
            
            if self.capture_format in ["markdown", "both"]:
                markdown_output = self.formatter.format_as_markdown(output)
                formatted_buffer["markdown"] += markdown_output + "\n"
            
            # 提取Claude响应
            claude_response = self.formatter.extract_claude_response(output)
            if claude_response:
                formatted_buffer["claude_responses"].append(claude_response)
            
            # 流式回调
            if self.enable_streaming:
                await self._notify_stream_callbacks(session_id, output_entry, formatted_buffer)
            
            return {
                "success": True,
                "session_id": session_id,
                "captured_size": len(output),
                "total_size": buffer["total_size"]
            }
            
        except Exception as e:
            self.logger.error(f"捕获输出失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_captured_output(self, session_id: str, format_type: str = "raw") -> Dict[str, Any]:
        """
        获取捕获的输出
        
        Args:
            session_id: 会话ID
            format_type: 格式类型 (raw, html, markdown, claude_only)
            
        Returns:
            Dict: 输出内容
        """
        try:
            if session_id not in self.output_buffers:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 未找到"
                }
            
            buffer = self.output_buffers[session_id]
            formatted_buffer = self.formatted_buffers[session_id]
            
            result = {
                "success": True,
                "session_id": session_id,
                "format_type": format_type,
                "total_size": buffer["total_size"],
                "entry_count": len(buffer["raw_output"]),
                "start_time": buffer["start_time"],
                "last_update": buffer["last_update"]
            }
            
            if format_type == "raw":
                result["output"] = "".join([entry["content"] for entry in buffer["raw_output"]])
            elif format_type == "html":
                result["output"] = formatted_buffer["html"]
            elif format_type == "markdown":
                result["output"] = formatted_buffer["markdown"]
            elif format_type == "claude_only":
                result["output"] = formatted_buffer["claude_responses"]
            elif format_type == "structured":
                result["output"] = {
                    "raw_entries": buffer["raw_output"],
                    "html": formatted_buffer["html"],
                    "markdown": formatted_buffer["markdown"],
                    "claude_responses": formatted_buffer["claude_responses"]
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的格式类型: {format_type}"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取输出失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stream_output(self, session_id: str, format_type: str = "raw") -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式获取输出
        
        Args:
            session_id: 会话ID
            format_type: 格式类型
            
        Yields:
            Dict: 输出块
        """
        try:
            if session_id not in self.output_buffers:
                yield {
                    "success": False,
                    "error": f"会话 {session_id} 未找到"
                }
                return
            
            buffer = self.output_buffers[session_id]
            last_index = 0
            
            while session_id in self.output_buffers:
                current_entries = buffer["raw_output"][last_index:]
                
                for entry in current_entries:
                    if format_type == "raw":
                        content = entry["content"]
                    elif format_type == "html":
                        content = self.formatter.format_ansi_to_html(entry["content"])
                    elif format_type == "markdown":
                        content = self.formatter.format_as_markdown(entry["content"])
                    else:
                        content = entry["content"]
                    
                    yield {
                        "success": True,
                        "session_id": session_id,
                        "timestamp": entry["timestamp"],
                        "type": entry["type"],
                        "content": content,
                        "format_type": format_type
                    }
                
                last_index = len(buffer["raw_output"])
                await asyncio.sleep(0.1)  # 100ms间隔
                
        except Exception as e:
            self.logger.error(f"流式输出失败: {e}")
            yield {
                "success": False,
                "error": str(e)
            }
    
    async def finish_capture(self, session_id: str) -> Dict[str, Any]:
        """
        完成捕获
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 完成结果
        """
        try:
            if session_id not in self.output_buffers:
                return {
                    "success": False,
                    "error": f"会话 {session_id} 未找到"
                }
            
            buffer = self.output_buffers[session_id]
            formatted_buffer = self.formatted_buffers[session_id]
            
            # 生成最终报告
            final_report = {
                "session_id": session_id,
                "total_size": buffer["total_size"],
                "entry_count": len(buffer["raw_output"]),
                "duration": time.time() - buffer["start_time"],
                "claude_responses_count": len(formatted_buffer["claude_responses"]),
                "formats": {
                    "raw": "".join([entry["content"] for entry in buffer["raw_output"]]),
                    "html": formatted_buffer["html"],
                    "markdown": formatted_buffer["markdown"],
                    "claude_responses": formatted_buffer["claude_responses"]
                }
            }
            
            # 通知完成回调
            await self._notify_completion_callbacks(session_id, final_report)
            
            self.logger.info(f"完成捕获会话: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "final_report": final_report
            }
            
        except Exception as e:
            self.logger.error(f"完成捕获失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """
        清理会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 清理结果
        """
        try:
            removed_buffers = 0
            
            if session_id in self.output_buffers:
                del self.output_buffers[session_id]
                removed_buffers += 1
            
            if session_id in self.formatted_buffers:
                del self.formatted_buffers[session_id]
                removed_buffers += 1
            
            self.logger.info(f"清理会话数据: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "removed_buffers": removed_buffers
            }
            
        except Exception as e:
            self.logger.error(f"清理会话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _cleanup_buffer(self, session_id: str):
        """清理缓冲区"""
        buffer = self.output_buffers[session_id]
        
        # 保留最近的50%数据
        keep_count = len(buffer["raw_output"]) // 2
        if keep_count > 0:
            buffer["raw_output"] = buffer["raw_output"][-keep_count:]
            buffer["total_size"] = sum(entry["size"] for entry in buffer["raw_output"])
        
        self.logger.info(f"清理缓冲区: {session_id}, 保留 {keep_count} 条记录")
    
    def add_stream_callback(self, callback: Callable):
        """添加流式回调"""
        self.stream_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable):
        """添加完成回调"""
        self.completion_callbacks.append(callback)
    
    async def _notify_stream_callbacks(self, session_id: str, output_entry: Dict[str, Any], formatted_buffer: Dict[str, Any]):
        """通知流式回调"""
        for callback in self.stream_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session_id, output_entry, formatted_buffer)
                else:
                    callback(session_id, output_entry, formatted_buffer)
            except Exception as e:
                self.logger.error(f"流式回调失败: {e}")
    
    async def _notify_completion_callbacks(self, session_id: str, final_report: Dict[str, Any]):
        """通知完成回调"""
        for callback in self.completion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session_id, final_report)
                else:
                    callback(session_id, final_report)
            except Exception as e:
                self.logger.error(f"完成回调失败: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("ResultCapture")
        
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

