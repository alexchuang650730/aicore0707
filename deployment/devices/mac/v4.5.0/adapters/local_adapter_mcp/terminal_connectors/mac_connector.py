"""
Mac Terminal Connector - Mac本地终端连接器
支持连接到Mac本地终端和远程SSH
"""

import asyncio
import subprocess
import os
import platform
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .base_connector import BaseTerminalConnector, ConnectionConfig, ConnectionStatus, CommandResult

class MacTerminalConnector(BaseTerminalConnector):
    """Mac终端连接器"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.shell = config.extra_params.get("shell", "zsh")  # zsh, bash, fish
        self.connection_type = config.extra_params.get("type", "local")  # local, ssh
        self.terminal_app = config.extra_params.get("terminal_app", "Terminal")  # Terminal, iTerm2
        self.process = None
        
    async def connect(self) -> bool:
        """建立Mac终端连接"""
        self.logger.info(f"连接到Mac终端: {self.config.name}")
        self._update_status(ConnectionStatus.CONNECTING)
        
        try:
            # 检查是否在macOS环境
            if platform.system() != "Darwin":
                raise Exception("Mac终端连接器仅支持macOS环境")
            
            if self.connection_type == "local":
                return await self._connect_local()
            elif self.connection_type == "ssh":
                return await self._connect_ssh()
            else:
                raise ValueError(f"不支持的连接类型: {self.connection_type}")
                
        except Exception as e:
            self.logger.error(f"Mac终端连接失败: {e}")
            self._update_status(ConnectionStatus.ERROR, str(e))
            return False
    
    async def _connect_local(self) -> bool:
        """连接到本地终端"""
        # 检查shell是否可用
        shell_path = await self._get_shell_path()
        if not shell_path:
            raise Exception(f"Shell不可用: {self.shell}")
        
        # 测试shell连接
        try:
            result = await self._execute_local_command("echo 'connection_test'", timeout=10)
            
            if result["exit_code"] == 0 and "connection_test" in result["stdout"]:
                self.session_id = f"mac_local_{datetime.now().timestamp()}"
                self._update_status(ConnectionStatus.CONNECTED)
                self.logger.info("Mac本地终端连接成功")
                return True
            else:
                raise Exception("本地终端连接测试失败")
                
        except Exception as e:
            raise Exception(f"本地终端连接失败: {e}")
    
    async def _connect_ssh(self) -> bool:
        """SSH连接"""
        if not self.config.host:
            raise ValueError("SSH连接需要指定host")
        
        # 构建SSH命令
        ssh_cmd = ["ssh"]
        
        # 添加SSH选项
        ssh_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=30",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3"
        ])
        
        # 添加密钥文件
        if self.config.key_file:
            key_path = Path(self.config.key_file).expanduser()
            if key_path.exists():
                ssh_cmd.extend(["-i", str(key_path)])
            else:
                raise FileNotFoundError(f"SSH密钥文件不存在: {key_path}")
        
        # 添加端口
        if self.config.port:
            ssh_cmd.extend(["-p", str(self.config.port)])
        
        # 添加用户和主机
        if self.config.user:
            ssh_cmd.append(f"{self.config.user}@{self.config.host}")
        else:
            ssh_cmd.append(self.config.host)
        
        # 测试连接
        test_cmd = ssh_cmd + ["echo", "'connection_test'"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *test_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )
            
            if process.returncode == 0 and b"connection_test" in stdout:
                self.session_id = f"mac_ssh_{self.config.host}_{datetime.now().timestamp()}"
                self._update_status(ConnectionStatus.CONNECTED)
                self.logger.info("Mac SSH连接成功")
                return True
            else:
                raise Exception(f"SSH连接测试失败: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            raise Exception("SSH连接超时")
    
    async def _get_shell_path(self) -> Optional[str]:
        """获取shell路径"""
        shell_paths = {
            "zsh": "/bin/zsh",
            "bash": "/bin/bash", 
            "fish": "/usr/local/bin/fish",
            "sh": "/bin/sh"
        }
        
        shell_path = shell_paths.get(self.shell)
        if shell_path and Path(shell_path).exists():
            return shell_path
        
        # 尝试使用which命令查找
        try:
            process = await asyncio.create_subprocess_exec(
                "which", self.shell,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
                
        except Exception as e:
            self.logger.warning(f"获取系统信息失败: {e}")
            return None
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.logger.info("断开Mac终端连接")
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
            finally:
                self.process = None
        
        self._update_status(ConnectionStatus.DISCONNECTED)
        return True
    
    async def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到Mac终端")
        
        timeout = timeout or self.config.timeout
        start_time = datetime.now()
        
        try:
            if self.connection_type == "local":
                result = await self._execute_local_command(command, timeout)
            elif self.connection_type == "ssh":
                result = await self._execute_ssh_command(command, timeout)
            else:
                raise ValueError(f"不支持的连接类型: {self.connection_type}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            cmd_result = CommandResult(
                command=command,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                execution_time=execution_time
            )
            
            self._add_command_to_history(cmd_result)
            return cmd_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            cmd_result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time
            )
            
            self._add_command_to_history(cmd_result)
            raise
    
    async def _execute_local_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """执行本地命令"""
        shell_path = await self._get_shell_path()
        
        # 设置环境变量
        env = dict(os.environ)
        env.update(self.config.environment)
        
        # 设置工作目录
        cwd = self.config.working_dir or os.getcwd()
        
        # 执行命令
        process = await asyncio.create_subprocess_exec(
            shell_path, "-c", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"命令执行超时: {command}")
    
    async def _execute_ssh_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """通过SSH执行命令"""
        # 构建SSH命令
        ssh_cmd = ["ssh"]
        
        # 添加SSH选项
        ssh_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10"
        ])
        
        # 添加密钥文件
        if self.config.key_file:
            key_path = Path(self.config.key_file).expanduser()
            ssh_cmd.extend(["-i", str(key_path)])
        
        # 添加端口
        if self.config.port:
            ssh_cmd.extend(["-p", str(self.config.port)])
        
        # 添加用户和主机
        if self.config.user:
            ssh_cmd.append(f"{self.config.user}@{self.config.host}")
        else:
            ssh_cmd.append(self.config.host)
        
        # 添加要执行的命令
        ssh_cmd.append(command)
        
        # 执行命令
        process = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"SSH命令执行超时: {command}")
    
    async def execute_interactive_command(self, command: str, input_handler: Optional[Callable] = None) -> CommandResult:
        """执行交互式命令"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到Mac终端")
        
        start_time = datetime.now()
        
        try:
            if self.connection_type == "local":
                return await self._execute_local_interactive(command, input_handler)
            else:
                # SSH交互式命令暂不支持
                raise NotImplementedError("SSH交互式命令暂不支持")
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            cmd_result = CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time
            )
            
            self._add_command_to_history(cmd_result)
            raise
    
    async def _execute_local_interactive(self, command: str, input_handler: Optional[Callable]) -> CommandResult:
        """执行本地交互式命令"""
        shell_path = await self._get_shell_path()
        start_time = datetime.now()
        
        # 设置环境变量
        env = dict(os.environ)
        env.update(self.config.environment)
        
        # 设置工作目录
        cwd = self.config.working_dir or os.getcwd()
        
        # 启动交互式进程
        process = await asyncio.create_subprocess_exec(
            shell_path, "-c", command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd
        )
        
        stdout_data = []
        stderr_data = []
        
        try:
            # 如果有输入处理器，处理交互
            if input_handler:
                while True:
                    try:
                        # 读取输出
                        output = await asyncio.wait_for(
                            process.stdout.read(1024),
                            timeout=1.0
                        )
                        
                        if output:
                            stdout_data.append(output)
                            # 调用输入处理器
                            response = input_handler(output.decode('utf-8', errors='replace'))
                            if response:
                                process.stdin.write(response.encode())
                                await process.stdin.drain()
                        else:
                            break
                            
                    except asyncio.TimeoutError:
                        # 检查进程是否还在运行
                        if process.returncode is not None:
                            break
            
            # 等待进程完成
            remaining_stdout, remaining_stderr = await process.communicate()
            
            if remaining_stdout:
                stdout_data.append(remaining_stdout)
            if remaining_stderr:
                stderr_data.append(remaining_stderr)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            cmd_result = CommandResult(
                command=command,
                exit_code=process.returncode,
                stdout=b''.join(stdout_data).decode('utf-8', errors='replace'),
                stderr=b''.join(stderr_data).decode('utf-8', errors='replace'),
                execution_time=execution_time
            )
            
            self._add_command_to_history(cmd_result)
            return cmd_result
            
        except Exception as e:
            # 清理进程
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        if self.connection_type == "local":
            # 本地文件复制
            try:
                result = await self.execute_command(f"cp '{local_path}' '{remote_path}'")
                if result.exit_code == 0:
                    self.logger.info(f"文件复制成功: {local_path} -> {remote_path}")
                    return True
                else:
                    self.logger.error(f"文件复制失败: {result.stderr}")
                    return False
            except Exception as e:
                self.logger.error(f"文件复制异常: {e}")
                return False
        
        elif self.connection_type == "ssh":
            # SCP上传
            return await self._scp_upload(local_path, remote_path)
        
        else:
            raise NotImplementedError(f"不支持的连接类型: {self.connection_type}")
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        if self.connection_type == "local":
            # 本地文件复制
            try:
                result = await self.execute_command(f"cp '{remote_path}' '{local_path}'")
                if result.exit_code == 0:
                    self.logger.info(f"文件复制成功: {remote_path} -> {local_path}")
                    return True
                else:
                    self.logger.error(f"文件复制失败: {result.stderr}")
                    return False
            except Exception as e:
                self.logger.error(f"文件复制异常: {e}")
                return False
        
        elif self.connection_type == "ssh":
            # SCP下载
            return await self._scp_download(remote_path, local_path)
        
        else:
            raise NotImplementedError(f"不支持的连接类型: {self.connection_type}")
    
    async def _scp_upload(self, local_path: str, remote_path: str) -> bool:
        """SCP上传文件"""
        # 构建SCP命令
        scp_cmd = ["scp"]
        
        # 添加SSH选项
        scp_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null"
        ])
        
        # 添加密钥文件
        if self.config.key_file:
            key_path = Path(self.config.key_file).expanduser()
            scp_cmd.extend(["-i", str(key_path)])
        
        # 添加端口
        if self.config.port:
            scp_cmd.extend(["-P", str(self.config.port)])
        
        # 添加源文件和目标
        scp_cmd.append(local_path)
        
        if self.config.user:
            scp_cmd.append(f"{self.config.user}@{self.config.host}:{remote_path}")
        else:
            scp_cmd.append(f"{self.config.host}:{remote_path}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *scp_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )
            
            if process.returncode == 0:
                self.logger.info(f"SCP上传成功: {local_path} -> {remote_path}")
                return True
            else:
                self.logger.error(f"SCP上传失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"SCP上传异常: {e}")
            return False
    
    async def _scp_download(self, remote_path: str, local_path: str) -> bool:
        """SCP下载文件"""
        # 构建SCP命令
        scp_cmd = ["scp"]
        
        # 添加SSH选项
        scp_cmd.extend([
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null"
        ])
        
        # 添加密钥文件
        if self.config.key_file:
            key_path = Path(self.config.key_file).expanduser()
            scp_cmd.extend(["-i", str(key_path)])
        
        # 添加端口
        if self.config.port:
            scp_cmd.extend(["-P", str(self.config.port)])
        
        # 添加源文件和目标
        if self.config.user:
            scp_cmd.append(f"{self.config.user}@{self.config.host}:{remote_path}")
        else:
            scp_cmd.append(f"{self.config.host}:{remote_path}")
        
        scp_cmd.append(local_path)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *scp_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout
            )
            
            if process.returncode == 0:
                self.logger.info(f"SCP下载成功: {remote_path} -> {local_path}")
                return True
            else:
                self.logger.error(f"SCP下载失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"SCP下载异常: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取Mac系统信息"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到Mac终端")
        
        commands = {
            "hostname": "hostname",
            "os_version": "sw_vers",
            "kernel": "uname -r",
            "architecture": "uname -m",
            "cpu_info": "sysctl -n machdep.cpu.brand_string",
            "memory": "memory_pressure",
            "disk": "df -h",
            "uptime": "uptime",
            "users": "who",
            "shell": f"echo $SHELL",
            "terminal": f"echo $TERM"
        }
        
        system_info = {}
        
        for key, cmd in commands.items():
            try:
                result = await self.execute_command(cmd, timeout=10)
                if result.exit_code == 0:
                    system_info[key] = result.stdout.strip()
                else:
                    system_info[key] = f"Error: {result.stderr}"
            except Exception as e:
                system_info[key] = f"Exception: {e}"
        
        # 添加Mac特有信息
        system_info["connection_type"] = self.connection_type
        system_info["shell_type"] = self.shell
        system_info["terminal_app"] = self.terminal_app
        
        return system_info
    
    async def open_terminal_app(self, command: Optional[str] = None) -> bool:
        """打开终端应用"""
        try:
            if self.terminal_app == "iTerm2":
                applescript = f'''
                tell application "iTerm"
                    create window with default profile
                    tell current session of current window
                        write text "{command or ''}"
                    end tell
                end tell
                '''
            else:  # Terminal
                applescript = f'''
                tell application "Terminal"
                    do script "{command or ''}"
                end tell
                '''
            
            process = await asyncio.create_subprocess_exec(
                "osascript", "-e", applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"终端应用打开成功: {self.terminal_app}")
                return True
            else:
                self.logger.error(f"终端应用打开失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"终端应用打开异常: {e}")
            return False

