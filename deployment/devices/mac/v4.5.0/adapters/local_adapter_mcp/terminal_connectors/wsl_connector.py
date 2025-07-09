"""
WSL Connector - Windows子系统Linux连接器
支持连接到WSL发行版
"""

import asyncio
import subprocess
import json
import platform
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from .base_connector import BaseTerminalConnector, ConnectionConfig, ConnectionStatus, CommandResult

class WSLConnector(BaseTerminalConnector):
    """WSL连接器"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.distribution = config.extra_params.get("distribution", "Ubuntu")
        self.wsl_version = config.extra_params.get("version", "2")
        self.available_distributions = []
        
    async def connect(self) -> bool:
        """建立WSL连接"""
        self.logger.info(f"连接到WSL发行版: {self.distribution}")
        self._update_status(ConnectionStatus.CONNECTING)
        
        try:
            # 检查是否在Windows环境
            if platform.system() != "Windows":
                raise Exception("WSL连接器仅支持Windows环境")
            
            # 检查WSL是否可用
            if not await self._check_wsl_available():
                raise Exception("WSL不可用或未安装")
            
            # 获取可用的发行版
            await self._get_available_distributions()
            
            # 检查指定的发行版是否存在
            if self.distribution not in self.available_distributions:
                raise Exception(f"WSL发行版不存在: {self.distribution}")
            
            # 测试连接
            if await self._test_connection():
                self.session_id = f"wsl_{self.distribution}_{datetime.now().timestamp()}"
                self._update_status(ConnectionStatus.CONNECTED)
                self.logger.info("WSL连接成功")
                return True
            else:
                raise Exception("WSL连接测试失败")
                
        except Exception as e:
            self.logger.error(f"WSL连接失败: {e}")
            self._update_status(ConnectionStatus.ERROR, str(e))
            return False
    
    async def _check_wsl_available(self) -> bool:
        """检查WSL是否可用"""
        try:
            process = await asyncio.create_subprocess_exec(
                "wsl", "--status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            return process.returncode == 0
            
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    async def _get_available_distributions(self) -> List[str]:
        """获取可用的WSL发行版"""
        try:
            process = await asyncio.create_subprocess_exec(
                "wsl", "--list", "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 解析输出，获取发行版列表
                distributions = []
                for line in stdout.decode('utf-8', errors='replace').strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('Windows Subsystem'):
                        # 移除可能的特殊字符
                        clean_name = ''.join(c for c in line if c.isprintable()).strip()
                        if clean_name:
                            distributions.append(clean_name)
                
                self.available_distributions = distributions
                self.logger.info(f"可用的WSL发行版: {distributions}")
                return distributions
            else:
                self.logger.warning(f"获取WSL发行版失败: {stderr.decode()}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取WSL发行版异常: {e}")
            return []
    
    async def _test_connection(self) -> bool:
        """测试WSL连接"""
        try:
            result = await self._execute_wsl_command("echo 'connection_test'", timeout=10)
            return result["exit_code"] == 0 and "connection_test" in result["stdout"]
        except Exception:
            return False
    
    async def disconnect(self) -> bool:
        """断开WSL连接"""
        self.logger.info("断开WSL连接")
        self._update_status(ConnectionStatus.DISCONNECTED)
        return True
    
    async def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到WSL")
        
        timeout = timeout or self.config.timeout
        start_time = datetime.now()
        
        try:
            result = await self._execute_wsl_command(command, timeout)
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
    
    async def _execute_wsl_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """执行WSL命令"""
        # 构建WSL命令
        wsl_cmd = ["wsl", "-d", self.distribution]
        
        # 设置用户
        if self.config.user:
            wsl_cmd.extend(["-u", self.config.user])
        
        # 设置工作目录
        if self.config.working_dir:
            wsl_cmd.extend(["--cd", self.config.working_dir])
        
        # 添加要执行的命令
        wsl_cmd.extend(["--", "bash", "-c", command])
        
        # 执行命令
        process = await asyncio.create_subprocess_exec(
            *wsl_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=dict(os.environ, **self.config.environment) if self.config.environment else None
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
            raise Exception(f"WSL命令执行超时: {command}")
    
    async def execute_interactive_command(self, command: str, input_handler: Optional[Callable] = None) -> CommandResult:
        """执行交互式命令"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到WSL")
        
        start_time = datetime.now()
        
        try:
            # 构建WSL命令
            wsl_cmd = ["wsl", "-d", self.distribution]
            
            if self.config.user:
                wsl_cmd.extend(["-u", self.config.user])
            
            if self.config.working_dir:
                wsl_cmd.extend(["--cd", self.config.working_dir])
            
            wsl_cmd.extend(["--", "bash", "-c", command])
            
            # 启动交互式进程
            process = await asyncio.create_subprocess_exec(
                *wsl_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_data = []
            stderr_data = []
            
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
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到WSL"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到WSL")
        
        try:
            # 将Windows路径转换为WSL路径
            wsl_remote_path = await self._convert_to_wsl_path(remote_path)
            
            # 使用cp命令复制文件
            copy_cmd = f"cp '{local_path}' '{wsl_remote_path}'"
            result = await self.execute_command(copy_cmd)
            
            if result.exit_code == 0:
                self.logger.info(f"文件上传成功: {local_path} -> {wsl_remote_path}")
                return True
            else:
                self.logger.error(f"文件上传失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件上传异常: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """从WSL下载文件"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到WSL")
        
        try:
            # 将WSL路径转换为Windows路径
            windows_remote_path = await self._convert_to_windows_path(remote_path)
            
            # 使用copy命令复制文件
            copy_cmd = f"copy '{windows_remote_path}' '{local_path}'"
            
            process = await asyncio.create_subprocess_shell(
                copy_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"文件下载成功: {remote_path} -> {local_path}")
                return True
            else:
                self.logger.error(f"文件下载失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件下载异常: {e}")
            return False
    
    async def _convert_to_wsl_path(self, windows_path: str) -> str:
        """将Windows路径转换为WSL路径"""
        try:
            result = await self._execute_wsl_command(f"wslpath '{windows_path}'", timeout=5)
            if result["exit_code"] == 0:
                return result["stdout"].strip()
            else:
                return windows_path
        except Exception:
            return windows_path
    
    async def _convert_to_windows_path(self, wsl_path: str) -> str:
        """将WSL路径转换为Windows路径"""
        try:
            result = await self._execute_wsl_command(f"wslpath -w '{wsl_path}'", timeout=5)
            if result["exit_code"] == 0:
                return result["stdout"].strip()
            else:
                return wsl_path
        except Exception:
            return wsl_path
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取WSL系统信息"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到WSL")
        
        commands = {
            "distribution": f"echo '{self.distribution}'",
            "wsl_version": "cat /proc/version",
            "hostname": "hostname",
            "os_release": "cat /etc/os-release",
            "kernel": "uname -r",
            "architecture": "uname -m",
            "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1",
            "memory": "free -h",
            "disk": "df -h",
            "uptime": "uptime",
            "users": "who",
            "wsl_interop": "echo $WSL_INTEROP"
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
        
        # 添加WSL特有信息
        system_info["available_distributions"] = self.available_distributions
        system_info["current_distribution"] = self.distribution
        
        return system_info
    
    async def get_wsl_info(self) -> Dict[str, Any]:
        """获取WSL特有信息"""
        try:
            # 获取WSL版本信息
            process = await asyncio.create_subprocess_exec(
                "wsl", "--status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            wsl_status = stdout.decode('utf-8', errors='replace') if process.returncode == 0 else stderr.decode('utf-8', errors='replace')
            
            # 获取发行版详细信息
            process = await asyncio.create_subprocess_exec(
                "wsl", "--list", "--verbose",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            distributions_info = stdout.decode('utf-8', errors='replace') if process.returncode == 0 else stderr.decode('utf-8', errors='replace')
            
            return {
                "wsl_status": wsl_status,
                "distributions_info": distributions_info,
                "current_distribution": self.distribution,
                "available_distributions": self.available_distributions
            }
            
        except Exception as e:
            return {"error": str(e)}

