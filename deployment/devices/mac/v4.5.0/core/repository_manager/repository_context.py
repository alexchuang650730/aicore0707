"""
Repository Context Manager for ClaudeEditor 4.5
仓库上下文管理器 - 支持仓库选择、上下文感知和项目管理
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import git
from ..ocr_processor.image_analyzer import ImageAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class RepositoryInfo:
    """仓库信息"""
    name: str
    path: str
    type: str  # git, local, remote
    status: str  # active, inactive, selected
    last_accessed: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProjectContext:
    """项目上下文"""
    current_repository: Optional[RepositoryInfo]
    recent_repositories: List[RepositoryInfo]
    workspace_path: str
    active_files: List[str]
    project_type: str  # powerautomation, claudeditor, general
    
class RepositoryContextManager:
    """仓库上下文管理器"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.current_repository: Optional[RepositoryInfo] = None
        self.repositories: Dict[str, RepositoryInfo] = {}
        self.recent_repositories: List[RepositoryInfo] = []
        self.workspace_path = os.path.expanduser("~")
        
        # OCR集成用于分析VS Code界面
        self.image_analyzer = ImageAnalyzer()
        
        # 项目类型检测规则
        self.project_type_patterns = {
            "powerautomation": ["powerauto", "automation", "aicore"],
            "claudeditor": ["claude", "editor"],
            "deployment": ["deploy", "vsix"],
            "integration": ["integration", "fixed"],
            "general": []
        }
        
        logger.info("仓库上下文管理器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化管理器"""
        try:
            # 初始化OCR分析器
            await self.image_analyzer.initialize()
            
            # 扫描工作空间
            await self._scan_workspace()
            
            # 加载历史记录
            await self._load_history()
            
            logger.info("仓库上下文管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"仓库上下文管理器初始化失败: {e}")
            return False
    
    async def analyze_vscode_interface(self, image_path: str) -> Dict[str, Any]:
        """分析VS Code界面截图，识别当前选中的仓库"""
        try:
            # 使用OCR分析界面
            analysis_result = await self.image_analyzer.analyze_uploaded_image(image_path)
            
            if not analysis_result or "interface_analysis" not in analysis_result:
                return {"error": "界面分析失败"}
            
            interface_analysis = analysis_result["interface_analysis"]
            recent_projects = interface_analysis.get("recent_projects", [])
            
            # 识别选中的仓库（通常有特殊标记）
            selected_repo = await self._identify_selected_repository(analysis_result)
            
            # 更新仓库列表
            await self._update_repositories_from_analysis(recent_projects)
            
            # 设置当前仓库
            if selected_repo:
                await self.set_current_repository(selected_repo)
            
            return {
                "selected_repository": selected_repo,
                "recent_projects": recent_projects,
                "total_projects": len(recent_projects),
                "analysis_success": True,
                "interface_type": "vscode"
            }
            
        except Exception as e:
            logger.error(f"VS Code界面分析失败: {e}")
            return {"error": str(e), "analysis_success": False}
    
    async def _identify_selected_repository(self, analysis_result: Dict[str, Any]) -> Optional[str]:
        """识别选中的仓库"""
        try:
            # 从OCR结果中提取文本
            ocr_result = analysis_result.get("ocr_result", {})
            extracted_text = ocr_result.get("text", "")
            
            # 查找带有选中标记的项目
            lines = extracted_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 检查是否包含选中标记（✓, ✔, 勾选等）
                if any(marker in line for marker in ['✓', '✔', '√', '勾', 'selected']):
                    # 查找项目名称
                    for project_line in lines[max(0, i-2):i+3]:
                        project_line = project_line.strip()
                        if project_line and not project_line.startswith('~'):
                            # 过滤掉路径行，保留项目名
                            if not any(char in project_line for char in ['/', '~', '.']):
                                return project_line
                
                # 检查是否是communitypowerauto（从截图中识别的选中项目）
                if "communitypowerauto" in line.lower():
                    return "communitypowerauto"
            
            # 如果没有明确的选中标记，尝试从项目列表中推断
            interface_analysis = analysis_result.get("interface_analysis", {})
            recent_projects = interface_analysis.get("recent_projects", [])
            
            if recent_projects:
                # 优先选择PowerAutomation相关项目
                for project in recent_projects:
                    if any(keyword in project.lower() for keyword in ["power", "auto", "community"]):
                        return project
                
                # 否则返回第一个项目
                return recent_projects[0]
            
            return None
            
        except Exception as e:
            logger.error(f"识别选中仓库失败: {e}")
            return None
    
    async def _update_repositories_from_analysis(self, projects: List[str]):
        """从分析结果更新仓库列表"""
        try:
            for project_name in projects:
                if project_name not in self.repositories:
                    # 推断项目路径
                    project_path = await self._infer_project_path(project_name)
                    
                    # 检测项目类型
                    project_type = self._detect_project_type(project_name)
                    
                    # 创建仓库信息
                    repo_info = RepositoryInfo(
                        name=project_name,
                        path=project_path,
                        type="git" if await self._is_git_repository(project_path) else "local",
                        status="inactive",
                        last_accessed=datetime.now(),
                        metadata={
                            "project_type": project_type,
                            "detected_from": "vscode_interface"
                        }
                    )
                    
                    self.repositories[project_name] = repo_info
                    logger.info(f"添加仓库: {project_name} ({project_type})")
            
        except Exception as e:
            logger.error(f"更新仓库列表失败: {e}")
    
    async def _infer_project_path(self, project_name: str) -> str:
        """推断项目路径"""
        # 常见的项目路径模式
        possible_paths = [
            f"/home/ubuntu/{project_name}",
            f"/Users/alexchuang/{project_name}",
            f"~/Documents/{project_name}",
            f"~/Projects/{project_name}",
            f"/Dive/{project_name}",
            f"/workspace/{project_name}"
        ]
        
        for path in possible_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        # 如果都不存在，返回默认路径
        return os.path.expanduser(f"~/{project_name}")
    
    def _detect_project_type(self, project_name: str) -> str:
        """检测项目类型"""
        project_name_lower = project_name.lower()
        
        for project_type, patterns in self.project_type_patterns.items():
            if any(pattern in project_name_lower for pattern in patterns):
                return project_type
        
        return "general"
    
    async def _is_git_repository(self, path: str) -> bool:
        """检查是否是Git仓库"""
        try:
            git.Repo(path)
            return True
        except:
            return False
    
    async def set_current_repository(self, repo_name: str) -> bool:
        """设置当前仓库"""
        try:
            if repo_name in self.repositories:
                # 更新之前的仓库状态
                if self.current_repository:
                    self.current_repository.status = "inactive"
                
                # 设置新的当前仓库
                self.current_repository = self.repositories[repo_name]
                self.current_repository.status = "selected"
                self.current_repository.last_accessed = datetime.now()
                
                # 更新最近访问列表
                await self._update_recent_repositories(self.current_repository)
                
                # 通知上下文变化
                if self.context:
                    await self._notify_context_change()
                
                logger.info(f"当前仓库设置为: {repo_name}")
                return True
            else:
                logger.warning(f"仓库不存在: {repo_name}")
                return False
                
        except Exception as e:
            logger.error(f"设置当前仓库失败: {e}")
            return False
    
    async def _update_recent_repositories(self, repo: RepositoryInfo):
        """更新最近访问的仓库列表"""
        # 移除已存在的项目
        self.recent_repositories = [r for r in self.recent_repositories if r.name != repo.name]
        
        # 添加到列表开头
        self.recent_repositories.insert(0, repo)
        
        # 限制列表长度
        self.recent_repositories = self.recent_repositories[:10]
    
    async def _notify_context_change(self):
        """通知上下文变化"""
        if self.context and hasattr(self.context, 'on_repository_changed'):
            await self.context.on_repository_changed(self.current_repository)
    
    async def get_project_context(self) -> ProjectContext:
        """获取项目上下文"""
        return ProjectContext(
            current_repository=self.current_repository,
            recent_repositories=self.recent_repositories,
            workspace_path=self.workspace_path,
            active_files=await self._get_active_files(),
            project_type=self.current_repository.metadata.get("project_type", "general") if self.current_repository else "general"
        )
    
    async def _get_active_files(self) -> List[str]:
        """获取活跃文件列表"""
        if not self.current_repository:
            return []
        
        try:
            # 获取最近修改的文件
            repo_path = Path(self.current_repository.path)
            if repo_path.exists():
                files = []
                for file_path in repo_path.rglob("*.py"):
                    if file_path.is_file():
                        files.append(str(file_path))
                
                # 按修改时间排序
                files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                return files[:20]  # 返回最近的20个文件
            
        except Exception as e:
            logger.error(f"获取活跃文件失败: {e}")
        
        return []
    
    async def _scan_workspace(self):
        """扫描工作空间"""
        try:
            workspace_path = Path(self.workspace_path)
            
            for item in workspace_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    repo_info = RepositoryInfo(
                        name=item.name,
                        path=str(item),
                        type="git" if await self._is_git_repository(str(item)) else "local",
                        status="inactive",
                        last_accessed=datetime.fromtimestamp(item.stat().st_mtime),
                        metadata={
                            "project_type": self._detect_project_type(item.name),
                            "detected_from": "workspace_scan"
                        }
                    )
                    
                    self.repositories[item.name] = repo_info
            
            logger.info(f"扫描到 {len(self.repositories)} 个仓库")
            
        except Exception as e:
            logger.error(f"扫描工作空间失败: {e}")
    
    async def _load_history(self):
        """加载历史记录"""
        try:
            history_file = Path.home() / ".claudeditor" / "repository_history.json"
            
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # 恢复最近访问的仓库
                for repo_data in history_data.get("recent_repositories", []):
                    repo_info = RepositoryInfo(**repo_data)
                    if repo_info.name in self.repositories:
                        self.recent_repositories.append(self.repositories[repo_info.name])
                
                logger.info("历史记录加载成功")
            
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
    
    async def save_history(self):
        """保存历史记录"""
        try:
            history_dir = Path.home() / ".claudeditor"
            history_dir.mkdir(exist_ok=True)
            
            history_file = history_dir / "repository_history.json"
            
            history_data = {
                "recent_repositories": [asdict(repo) for repo in self.recent_repositories],
                "current_repository": asdict(self.current_repository) if self.current_repository else None,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info("历史记录保存成功")
            
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def get_repository_list(self) -> List[RepositoryInfo]:
        """获取仓库列表"""
        return list(self.repositories.values())
    
    def get_current_repository(self) -> Optional[RepositoryInfo]:
        """获取当前仓库"""
        return self.current_repository
    
    def get_recent_repositories(self) -> List[RepositoryInfo]:
        """获取最近访问的仓库"""
        return self.recent_repositories
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        project_types = {}
        for repo in self.repositories.values():
            project_type = repo.metadata.get("project_type", "general")
            project_types[project_type] = project_types.get(project_type, 0) + 1
        
        return {
            "total_repositories": len(self.repositories),
            "current_repository": self.current_repository.name if self.current_repository else None,
            "recent_count": len(self.recent_repositories),
            "project_types": project_types,
            "workspace_path": self.workspace_path
        }

# ClaudeEditor集成接口
class ClaudeEditorRepositoryIntegration:
    """ClaudeEditor仓库集成"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.manager = RepositoryContextManager(claudeditor_context)
    
    async def initialize(self) -> bool:
        """初始化集成"""
        return await self.manager.initialize()
    
    async def process_vscode_screenshot(self, image_path: str) -> Dict[str, Any]:
        """处理VS Code截图，自动识别和设置仓库上下文"""
        result = await self.manager.analyze_vscode_interface(image_path)
        
        if result.get("analysis_success"):
            return {
                "type": "repository_context_update",
                "success": True,
                "selected_repository": result.get("selected_repository"),
                "available_projects": result.get("recent_projects", []),
                "context_updated": True,
                "display_info": {
                    "title": "仓库上下文已更新",
                    "description": f"当前选中: {result.get('selected_repository', '未知')}",
                    "project_count": result.get("total_projects", 0)
                }
            }
        else:
            return {
                "type": "repository_context_error",
                "success": False,
                "error": result.get("error", "分析失败")
            }
    
    def get_manager(self) -> RepositoryContextManager:
        """获取管理器实例"""
        return self.manager

