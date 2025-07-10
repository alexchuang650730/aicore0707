"""
Git Manager - Git集成管理器
处理版本控制，分支管理，协作功能

真实实现，支持实际的Git操作
"""

import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

class GitRepository:
    """Git仓库操作类"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger("GitRepository")
    
    async def init(self) -> Dict[str, Any]:
        """初始化Git仓库"""
        try:
            if not self.is_git_repo():
                result = await self._run_git_command(["init"])
                if result["success"]:
                    self.logger.info(f"Git仓库初始化成功: {self.repo_path}")
                    return {"success": True, "message": "Git仓库初始化成功"}
                else:
                    return result
            else:
                return {"success": True, "message": "Git仓库已存在"}
                
        except Exception as e:
            self.logger.error(f"初始化Git仓库失败: {e}")
            return {"success": False, "error": str(e)}
    
    def is_git_repo(self) -> bool:
        """检查是否为Git仓库"""
        return (self.repo_path / ".git").exists()
    
    async def add_files(self, files: List[str] = None) -> Dict[str, Any]:
        """添加文件到暂存区"""
        try:
            if files:
                for file in files:
                    result = await self._run_git_command(["add", file])
                    if not result["success"]:
                        return result
            else:
                result = await self._run_git_command(["add", "."])
            
            return result
            
        except Exception as e:
            self.logger.error(f"添加文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def commit(self, message: str, author: Optional[str] = None) -> Dict[str, Any]:
        """提交更改"""
        try:
            cmd = ["commit", "-m", message]
            if author:
                cmd.extend(["--author", author])
            
            result = await self._run_git_command(cmd)
            
            if result["success"]:
                self.logger.info(f"提交成功: {message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"提交失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        try:
            result = await self._run_git_command(["status", "--porcelain"])
            
            if result["success"]:
                status_lines = result["output"].strip().split("\n") if result["output"].strip() else []
                
                modified_files = []
                untracked_files = []
                staged_files = []
                
                for line in status_lines:
                    if len(line) >= 3:
                        status_code = line[:2]
                        file_path = line[3:]
                        
                        if status_code[0] in ["M", "A", "D", "R", "C"]:
                            staged_files.append(file_path)
                        if status_code[1] in ["M", "D"]:
                            modified_files.append(file_path)
                        elif status_code == "??":
                            untracked_files.append(file_path)
                
                return {
                    "success": True,
                    "staged_files": staged_files,
                    "modified_files": modified_files,
                    "untracked_files": untracked_files,
                    "is_clean": len(status_lines) == 0
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"获取Git状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_log(self, limit: int = 10) -> Dict[str, Any]:
        """获取提交日志"""
        try:
            cmd = ["log", f"--max-count={limit}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"]
            result = await self._run_git_command(cmd)
            
            if result["success"]:
                commits = []
                for line in result["output"].strip().split("\n"):
                    if line:
                        parts = line.split("|", 4)
                        if len(parts) == 5:
                            commits.append({
                                "hash": parts[0],
                                "author_name": parts[1],
                                "author_email": parts[2],
                                "date": parts[3],
                                "message": parts[4]
                            })
                
                return {
                    "success": True,
                    "commits": commits
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"获取提交日志失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """创建分支"""
        try:
            result = await self._run_git_command(["checkout", "-b", branch_name])
            
            if result["success"]:
                self.logger.info(f"分支创建成功: {branch_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"创建分支失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """切换分支"""
        try:
            result = await self._run_git_command(["checkout", branch_name])
            
            if result["success"]:
                self.logger.info(f"切换到分支: {branch_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"切换分支失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_branches(self) -> Dict[str, Any]:
        """获取分支列表"""
        try:
            result = await self._run_git_command(["branch", "-a"])
            
            if result["success"]:
                branches = []
                current_branch = None
                
                for line in result["output"].strip().split("\n"):
                    line = line.strip()
                    if line:
                        if line.startswith("* "):
                            current_branch = line[2:]
                            branches.append({"name": current_branch, "is_current": True})
                        else:
                            branches.append({"name": line, "is_current": False})
                
                return {
                    "success": True,
                    "branches": branches,
                    "current_branch": current_branch
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"获取分支列表失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_git_command(self, args: List[str]) -> Dict[str, Any]:
        """运行Git命令"""
        try:
            cmd = ["git"] + args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "output": stdout.decode('utf-8'),
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode('utf-8'),
                    "command": " ".join(cmd),
                    "return_code": process.returncode
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(["git"] + args)
            }

class GitManager:
    """Git管理器 - 处理版本控制和协作"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Git管理器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # Git配置
        self.auto_commit = self.config.get("auto_commit", False)
        self.commit_message_template = self.config.get(
            "commit_message_template", 
            "Mirror sync: {files_count} files at {timestamp}"
        )
        self.author_name = self.config.get("author_name", "Mirror Code")
        self.author_email = self.config.get("author_email", "mirror@example.com")
        
        # 状态管理
        self.repository = None
        self.repo_path = None
        self.is_running = False
        
        # 统计信息
        self.stats = {
            "commits_made": 0,
            "files_tracked": 0,
            "branches_created": 0,
            "last_commit": None
        }
        
        self.logger.info("Git管理器初始化完成")
    
    async def start(self, repo_path: str):
        """
        启动Git管理器
        
        Args:
            repo_path: 仓库路径
        """
        try:
            self.logger.info(f"启动Git管理器: {repo_path}")
            
            self.repo_path = repo_path
            self.repository = GitRepository(repo_path)
            
            # 初始化Git仓库
            init_result = await self.repository.init()
            if not init_result["success"]:
                raise Exception(f"Git仓库初始化失败: {init_result.get('error')}")
            
            # 配置Git用户信息
            await self._configure_git_user()
            
            self.is_running = True
            
            self.logger.info("✅ Git管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动Git管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止Git管理器"""
        try:
            self.logger.info("停止Git管理器...")
            
            self.is_running = False
            
            # 如果启用了自动提交，执行最后一次提交
            if self.auto_commit and self.repository:
                await self._auto_commit("Final commit before stopping")
            
            self.logger.info("✅ Git管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止Git管理器失败: {e}")
    
    async def track_file_changes(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        跟踪文件变化
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            Dict: 跟踪结果
        """
        try:
            if not self.repository:
                return {"success": False, "error": "Git管理器未启动"}
            
            # 添加文件到暂存区
            add_result = await self.repository.add_files(file_paths)
            if not add_result["success"]:
                return add_result
            
            self.stats["files_tracked"] += len(file_paths)
            
            # 如果启用自动提交
            if self.auto_commit:
                commit_message = self.commit_message_template.format(
                    files_count=len(file_paths),
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                commit_result = await self._auto_commit(commit_message)
                if commit_result["success"]:
                    self.stats["commits_made"] += 1
                    self.stats["last_commit"] = time.time()
                
                return commit_result
            else:
                return {
                    "success": True,
                    "message": f"已跟踪 {len(file_paths)} 个文件",
                    "files": file_paths
                }
                
        except Exception as e:
            self.logger.error(f"跟踪文件变化失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        提交更改
        
        Args:
            message: 提交消息
            files: 要提交的文件列表（可选）
            
        Returns:
            Dict: 提交结果
        """
        try:
            if not self.repository:
                return {"success": False, "error": "Git管理器未启动"}
            
            # 如果指定了文件，先添加到暂存区
            if files:
                add_result = await self.repository.add_files(files)
                if not add_result["success"]:
                    return add_result
            
            # 提交更改
            author = f"{self.author_name} <{self.author_email}>"
            commit_result = await self.repository.commit(message, author)
            
            if commit_result["success"]:
                self.stats["commits_made"] += 1
                self.stats["last_commit"] = time.time()
                self.logger.info(f"提交成功: {message}")
            
            return commit_result
            
        except Exception as e:
            self.logger.error(f"提交更改失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_repository_status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        try:
            if not self.repository:
                return {"success": False, "error": "Git管理器未启动"}
            
            # 获取Git状态
            status_result = await self.repository.get_status()
            if not status_result["success"]:
                return status_result
            
            # 获取分支信息
            branches_result = await self.repository.get_branches()
            if not branches_result["success"]:
                return branches_result
            
            # 获取最近提交
            log_result = await self.repository.get_log(5)
            if not log_result["success"]:
                return log_result
            
            return {
                "success": True,
                "repo_path": str(self.repo_path),
                "git_status": status_result,
                "branches": branches_result,
                "recent_commits": log_result["commits"],
                "stats": self.stats
            }
            
        except Exception as e:
            self.logger.error(f"获取仓库状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_mirror_branch(self, session_id: str) -> Dict[str, Any]:
        """
        为Mirror会话创建专用分支
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 创建结果
        """
        try:
            if not self.repository:
                return {"success": False, "error": "Git管理器未启动"}
            
            branch_name = f"mirror-{session_id}"
            
            # 创建分支
            result = await self.repository.create_branch(branch_name)
            
            if result["success"]:
                self.stats["branches_created"] += 1
                self.logger.info(f"Mirror分支创建成功: {branch_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"创建Mirror分支失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def merge_mirror_changes(self, source_branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """
        合并Mirror更改
        
        Args:
            source_branch: 源分支
            target_branch: 目标分支
            
        Returns:
            Dict: 合并结果
        """
        try:
            if not self.repository:
                return {"success": False, "error": "Git管理器未启动"}
            
            # 切换到目标分支
            switch_result = await self.repository.switch_branch(target_branch)
            if not switch_result["success"]:
                return switch_result
            
            # 执行合并
            merge_result = await self.repository._run_git_command(["merge", source_branch])
            
            if merge_result["success"]:
                self.logger.info(f"分支合并成功: {source_branch} -> {target_branch}")
            
            return merge_result
            
        except Exception as e:
            self.logger.error(f"合并分支失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取Git管理器状态"""
        return {
            "is_running": self.is_running,
            "repo_path": str(self.repo_path) if self.repo_path else None,
            "auto_commit": self.auto_commit,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "stats": self.stats
        }
    
    async def _configure_git_user(self):
        """配置Git用户信息"""
        try:
            # 设置用户名
            await self.repository._run_git_command([
                "config", "user.name", self.author_name
            ])
            
            # 设置邮箱
            await self.repository._run_git_command([
                "config", "user.email", self.author_email
            ])
            
            self.logger.info(f"Git用户配置完成: {self.author_name} <{self.author_email}>")
            
        except Exception as e:
            self.logger.warning(f"配置Git用户信息失败: {e}")
    
    async def _auto_commit(self, message: str) -> Dict[str, Any]:
        """自动提交"""
        try:
            # 检查是否有变化
            status_result = await self.repository.get_status()
            if not status_result["success"]:
                return status_result
            
            if status_result["is_clean"]:
                return {
                    "success": True,
                    "message": "没有需要提交的更改"
                }
            
            # 添加所有更改
            add_result = await self.repository.add_files()
            if not add_result["success"]:
                return add_result
            
            # 提交更改
            author = f"{self.author_name} <{self.author_email}>"
            return await self.repository.commit(message, author)
            
        except Exception as e:
            self.logger.error(f"自动提交失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("GitManager")
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

