"""
EC2 Connector - Amazon EC2 Linux实例连接器
支持SSH和SSM连接方式
"""

import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .base_connector import BaseTerminalConnector, ConnectionConfig, ConnectionStatus, CommandResult

class EC2Connector(BaseTerminalConnector):
    """EC2连接器"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.ssh_process = None
        self.connection_method = config.extra_params.get("method", "ssh")  # ssh, ssm
        self.instance_id = config.extra_params.get("instance_id")
        self.region = config.extra_params.get("region", "us-east-1")
        self.profile = config.extra_params.get("profile", "default")
        
    async def connect(self) -> bool:
        """建立EC2连接"""
        self.logger.info(f"连接到EC2实例: {self.config.name}")
        self._update_status(ConnectionStatus.CONNECTING)
        
        try:
            if self.connection_method == "ssh":
                return await self._connect_ssh()
            elif self.connection_method == "ssm":
                return await self._connect_ssm()
            else:
                raise ValueError(f"不支持的连接方法: {self.connection_method}")
                
        except Exception as e:
            self.logger.error(f"EC2连接失败: {e}")
            self._update_status(ConnectionStatus.ERROR, str(e))
            return False
    
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
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *test_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=self.config.timeout
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and b"connection_test" in stdout:
                self.session_id = f"ssh_{self.config.host}_{datetime.now().timestamp()}"
                self._update_status(ConnectionStatus.CONNECTED)
                self.logger.info("SSH连接成功")
                return True
            else:
                raise Exception(f"SSH连接测试失败: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            raise Exception("SSH连接超时")
    
    async def _connect_ssm(self) -> bool:
        """SSM连接"""
        if not self.instance_id:
            raise ValueError("SSM连接需要指定instance_id")
        
        # 检查AWS CLI
        try:
            result = await asyncio.create_subprocess_exec(
                "aws", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode != 0:
                raise Exception("AWS CLI不可用")
                
        except FileNotFoundError:
            raise Exception("AWS CLI未安装")
        
        # 测试SSM连接
        test_cmd = [
            "aws", "ssm", "send-command",
            "--instance-ids", self.instance_id,
            "--document-name", "AWS-RunShellScript",
            "--parameters", "commands=['echo connection_test']",
            "--region", self.region,
            "--profile", self.profile,
            "--output", "json"
        ]
        
        try:
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *test_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=self.config.timeout
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                response = json.loads(stdout.decode())
                command_id = response["Command"]["CommandId"]
                
                # 等待命令完成并检查结果
                if await self._wait_ssm_command(command_id):
                    self.session_id = f"ssm_{self.instance_id}_{datetime.now().timestamp()}"
                    self._update_status(ConnectionStatus.CONNECTED)
                    self.logger.info("SSM连接成功")
                    return True
                else:
                    raise Exception("SSM连接测试失败")
            else:
                raise Exception(f"SSM连接失败: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            raise Exception("SSM连接超时")
    
    async def _wait_ssm_command(self, command_id: str, timeout: int = 30) -> bool:
        """等待SSM命令完成"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            cmd = [
                "aws", "ssm", "get-command-invocation",
                "--command-id", command_id,
                "--instance-id", self.instance_id,
                "--region", self.region,
                "--profile", self.profile,
                "--output", "json"
            ]
            
            try:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    response = json.loads(stdout.decode())
                    status = response.get("Status")
                    
                    if status == "Success":
                        output = response.get("StandardOutputContent", "")
                        return "connection_test" in output
                    elif status in ["Failed", "Cancelled", "TimedOut"]:
                        return False
                    # 如果是InProgress，继续等待
                
            except Exception as e:
                self.logger.warning(f"检查SSM命令状态失败: {e}")
            
            await asyncio.sleep(2)
        
        return False
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.logger.info("断开EC2连接")
        
        if self.ssh_process:
            try:
                self.ssh_process.terminate()
                await asyncio.wait_for(self.ssh_process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.ssh_process.kill()
            finally:
                self.ssh_process = None
        
        self._update_status(ConnectionStatus.DISCONNECTED)
        return True
    
    async def execute_command(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到EC2实例")
        
        timeout = timeout or self.config.timeout
        start_time = datetime.now()
        
        try:
            if self.connection_method == "ssh":
                result = await self._execute_ssh_command(command, timeout)
            elif self.connection_method == "ssm":
                result = await self._execute_ssm_command(command, timeout)
            else:
                raise ValueError(f"不支持的连接方法: {self.connection_method}")
            
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
            raise Exception(f"命令执行超时: {command}")
    
    async def _execute_ssm_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """通过SSM执行命令"""
        # 发送SSM命令
        send_cmd = [
            "aws", "ssm", "send-command",
            "--instance-ids", self.instance_id,
            "--document-name", "AWS-RunShellScript",
            "--parameters", f"commands=['{command}']",
            "--region", self.region,
            "--profile", self.profile,
            "--output", "json"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *send_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"SSM命令发送失败: {stderr.decode()}")
        
        response = json.loads(stdout.decode())
        command_id = response["Command"]["CommandId"]
        
        # 等待命令完成并获取结果
        return await self._get_ssm_command_result(command_id, timeout)
    
    async def _get_ssm_command_result(self, command_id: str, timeout: int) -> Dict[str, Any]:
        """获取SSM命令结果"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            cmd = [
                "aws", "ssm", "get-command-invocation",
                "--command-id", command_id,
                "--instance-id", self.instance_id,
                "--region", self.region,
                "--profile", self.profile,
                "--output", "json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                response = json.loads(stdout.decode())
                status = response.get("Status")
                
                if status == "Success":
                    return {
                        "exit_code": 0,
                        "stdout": response.get("StandardOutputContent", ""),
                        "stderr": response.get("StandardErrorContent", "")
                    }
                elif status == "Failed":
                    return {
                        "exit_code": 1,
                        "stdout": response.get("StandardOutputContent", ""),
                        "stderr": response.get("StandardErrorContent", "")
                    }
                elif status in ["Cancelled", "TimedOut"]:
                    raise Exception(f"SSM命令{status}")
                # 如果是InProgress，继续等待
            
            await asyncio.sleep(2)
        
        raise Exception("SSM命令执行超时")
    
    async def execute_interactive_command(self, command: str, input_handler: Optional[Callable] = None) -> CommandResult:
        """执行交互式命令"""
        # EC2连接器暂不支持交互式命令
        raise NotImplementedError("EC2连接器暂不支持交互式命令")
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        if self.connection_method != "ssh":
            raise NotImplementedError("文件上传仅支持SSH连接")
        
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到EC2实例")
        
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
                self.logger.info(f"文件上传成功: {local_path} -> {remote_path}")
                return True
            else:
                self.logger.error(f"文件上传失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件上传异常: {e}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        if self.connection_method != "ssh":
            raise NotImplementedError("文件下载仅支持SSH连接")
        
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到EC2实例")
        
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
                self.logger.info(f"文件下载成功: {remote_path} -> {local_path}")
                return True
            else:
                self.logger.error(f"文件下载失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件下载异常: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        if self.status != ConnectionStatus.CONNECTED:
            raise Exception("未连接到EC2实例")
        
        commands = {
            "hostname": "hostname",
            "os_release": "cat /etc/os-release",
            "kernel": "uname -r",
            "architecture": "uname -m",
            "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1",
            "memory": "free -h",
            "disk": "df -h",
            "uptime": "uptime",
            "users": "who"
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
        
        return system_info

