"""
Repository Selector UI Component for ClaudeEditor 4.5
仓库选择器UI组件 - 支持快速仓库切换和上下文管理
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from ..core.repository_manager.repository_context import (
    RepositoryContextManager, 
    RepositoryInfo,
    ClaudeEditorRepositoryIntegration
)

logger = logging.getLogger(__name__)

@dataclass
class UIAction:
    """UI操作定义"""
    id: str
    label: str
    icon: str
    action: Callable
    enabled: bool = True
    tooltip: str = ""

class RepositorySelector:
    """仓库选择器"""
    
    def __init__(self, claudeditor_context=None):
        self.context = claudeditor_context
        self.integration = ClaudeEditorRepositoryIntegration(claudeditor_context)
        self.manager = self.integration.get_manager()
        
        # UI状态
        self.is_visible = False
        self.selected_index = 0
        self.filter_text = ""
        
        # 回调函数
        self.on_repository_selected: Optional[Callable] = None
        self.on_context_updated: Optional[Callable] = None
        
        logger.info("仓库选择器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化选择器"""
        try:
            success = await self.integration.initialize()
            if success:
                logger.info("仓库选择器初始化成功")
            return success
        except Exception as e:
            logger.error(f"仓库选择器初始化失败: {e}")
            return False
    
    async def show_repository_selector(self) -> Dict[str, Any]:
        """显示仓库选择器"""
        try:
            repositories = self.manager.get_repository_list()
            current_repo = self.manager.get_current_repository()
            recent_repos = self.manager.get_recent_repositories()
            
            # 构建UI数据
            ui_data = {
                "type": "repository_selector",
                "visible": True,
                "repositories": [self._format_repository_for_ui(repo) for repo in repositories],
                "current_repository": self._format_repository_for_ui(current_repo) if current_repo else None,
                "recent_repositories": [self._format_repository_for_ui(repo) for repo in recent_repos],
                "actions": self._get_quick_actions(),
                "filter_placeholder": "搜索仓库...",
                "title": "选择仓库"
            }
            
            self.is_visible = True
            return ui_data
            
        except Exception as e:
            logger.error(f"显示仓库选择器失败: {e}")
            return {"type": "error", "message": str(e)}
    
    def _format_repository_for_ui(self, repo: RepositoryInfo) -> Dict[str, Any]:
        """格式化仓库信息用于UI显示"""
        if not repo:
            return None
        
        return {
            "name": repo.name,
            "path": repo.path,
            "type": repo.type,
            "status": repo.status,
            "project_type": repo.metadata.get("project_type", "general"),
            "last_accessed": repo.last_accessed.isoformat(),
            "icon": self._get_repository_icon(repo),
            "description": self._get_repository_description(repo),
            "is_selected": repo.status == "selected",
            "is_git": repo.type == "git",
            "display_path": self._format_path_for_display(repo.path)
        }
    
    def _get_repository_icon(self, repo: RepositoryInfo) -> str:
        """获取仓库图标"""
        project_type = repo.metadata.get("project_type", "general")
        
        icon_map = {
            "powerautomation": "🤖",
            "claudeditor": "🎯", 
            "deployment": "🚀",
            "integration": "🔗",
            "general": "📁"
        }
        
        base_icon = icon_map.get(project_type, "📁")
        
        if repo.type == "git":
            return f"{base_icon} 🌿"
        
        return base_icon
    
    def _get_repository_description(self, repo: RepositoryInfo) -> str:
        """获取仓库描述"""
        project_type = repo.metadata.get("project_type", "general")
        
        descriptions = {
            "powerautomation": "PowerAutomation 项目",
            "claudeditor": "ClaudeEditor 项目",
            "deployment": "部署项目",
            "integration": "集成项目",
            "general": "通用项目"
        }
        
        base_desc = descriptions.get(project_type, "项目")
        
        if repo.type == "git":
            base_desc += " (Git仓库)"
        
        return base_desc
    
    def _format_path_for_display(self, path: str) -> str:
        """格式化路径用于显示"""
        # 简化路径显示
        if path.startswith("/home/ubuntu/"):
            return f"~/{path[13:]}"
        elif path.startswith("/Users/"):
            return f"~/{'/'.join(path.split('/')[3:])}"
        else:
            return path
    
    def _get_quick_actions(self) -> List[Dict[str, Any]]:
        """获取快速操作"""
        actions = [
            {
                "id": "refresh",
                "label": "刷新",
                "icon": "🔄",
                "tooltip": "刷新仓库列表",
                "enabled": True
            },
            {
                "id": "scan_workspace",
                "label": "扫描工作空间",
                "icon": "🔍",
                "tooltip": "扫描工作空间中的项目",
                "enabled": True
            },
            {
                "id": "import_from_vscode",
                "label": "从VS Code导入",
                "icon": "📥",
                "tooltip": "从VS Code界面截图导入项目",
                "enabled": True
            },
            {
                "id": "open_in_explorer",
                "label": "在文件管理器中打开",
                "icon": "📂",
                "tooltip": "在文件管理器中打开当前仓库",
                "enabled": self.manager.get_current_repository() is not None
            }
        ]
        
        return actions
    
    async def handle_repository_selection(self, repo_name: str) -> Dict[str, Any]:
        """处理仓库选择"""
        try:
            success = await self.manager.set_current_repository(repo_name)
            
            if success:
                current_repo = self.manager.get_current_repository()
                
                # 触发回调
                if self.on_repository_selected:
                    await self.on_repository_selected(current_repo)
                
                # 获取项目上下文
                context = await self.manager.get_project_context()
                
                return {
                    "type": "repository_selected",
                    "success": True,
                    "repository": self._format_repository_for_ui(current_repo),
                    "context": {
                        "project_type": context.project_type,
                        "active_files_count": len(context.active_files),
                        "workspace_path": context.workspace_path
                    },
                    "message": f"已切换到仓库: {repo_name}"
                }
            else:
                return {
                    "type": "repository_selection_error",
                    "success": False,
                    "message": f"切换仓库失败: {repo_name}"
                }
                
        except Exception as e:
            logger.error(f"处理仓库选择失败: {e}")
            return {
                "type": "error",
                "success": False,
                "message": str(e)
            }
    
    async def handle_quick_action(self, action_id: str, **kwargs) -> Dict[str, Any]:
        """处理快速操作"""
        try:
            if action_id == "refresh":
                return await self._handle_refresh()
            elif action_id == "scan_workspace":
                return await self._handle_scan_workspace()
            elif action_id == "import_from_vscode":
                return await self._handle_import_from_vscode(**kwargs)
            elif action_id == "open_in_explorer":
                return await self._handle_open_in_explorer()
            else:
                return {
                    "type": "error",
                    "message": f"未知操作: {action_id}"
                }
                
        except Exception as e:
            logger.error(f"处理快速操作失败: {e}")
            return {
                "type": "error",
                "message": str(e)
            }
    
    async def _handle_refresh(self) -> Dict[str, Any]:
        """处理刷新操作"""
        await self.manager._scan_workspace()
        repositories = self.manager.get_repository_list()
        
        return {
            "type": "refresh_complete",
            "success": True,
            "repositories": [self._format_repository_for_ui(repo) for repo in repositories],
            "message": f"已刷新，发现 {len(repositories)} 个仓库"
        }
    
    async def _handle_scan_workspace(self) -> Dict[str, Any]:
        """处理扫描工作空间操作"""
        await self.manager._scan_workspace()
        repositories = self.manager.get_repository_list()
        
        return {
            "type": "scan_complete",
            "success": True,
            "repositories": [self._format_repository_for_ui(repo) for repo in repositories],
            "message": f"工作空间扫描完成，发现 {len(repositories)} 个项目"
        }
    
    async def _handle_import_from_vscode(self, **kwargs) -> Dict[str, Any]:
        """处理从VS Code导入操作"""
        image_path = kwargs.get("image_path")
        
        if not image_path:
            return {
                "type": "error",
                "message": "请提供VS Code界面截图"
            }
        
        # 使用集成功能处理截图
        result = await self.integration.process_vscode_screenshot(image_path)
        
        if result.get("success"):
            # 刷新UI
            repositories = self.manager.get_repository_list()
            current_repo = self.manager.get_current_repository()
            
            return {
                "type": "import_complete",
                "success": True,
                "repositories": [self._format_repository_for_ui(repo) for repo in repositories],
                "current_repository": self._format_repository_for_ui(current_repo),
                "imported_projects": result.get("available_projects", []),
                "selected_repository": result.get("selected_repository"),
                "message": f"成功导入 {len(result.get('available_projects', []))} 个项目"
            }
        else:
            return {
                "type": "import_error",
                "success": False,
                "message": result.get("error", "导入失败")
            }
    
    async def _handle_open_in_explorer(self) -> Dict[str, Any]:
        """处理在文件管理器中打开操作"""
        current_repo = self.manager.get_current_repository()
        
        if not current_repo:
            return {
                "type": "error",
                "message": "没有选中的仓库"
            }
        
        import subprocess
        import platform
        
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", current_repo.path])
            elif system == "Windows":
                subprocess.run(["explorer", current_repo.path])
            else:  # Linux
                subprocess.run(["xdg-open", current_repo.path])
            
            return {
                "type": "explorer_opened",
                "success": True,
                "message": f"已在文件管理器中打开: {current_repo.name}"
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"打开文件管理器失败: {e}"
            }
    
    async def filter_repositories(self, filter_text: str) -> Dict[str, Any]:
        """过滤仓库"""
        self.filter_text = filter_text.lower()
        repositories = self.manager.get_repository_list()
        
        if not filter_text:
            filtered_repos = repositories
        else:
            filtered_repos = [
                repo for repo in repositories
                if (filter_text in repo.name.lower() or 
                    filter_text in repo.metadata.get("project_type", "").lower())
            ]
        
        return {
            "type": "filter_result",
            "repositories": [self._format_repository_for_ui(repo) for repo in filtered_repos],
            "total_count": len(repositories),
            "filtered_count": len(filtered_repos),
            "filter_text": filter_text
        }
    
    def hide_selector(self):
        """隐藏选择器"""
        self.is_visible = False
        self.filter_text = ""
        self.selected_index = 0
    
    def get_current_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        current_repo = self.manager.get_current_repository()
        statistics = self.manager.get_statistics()
        
        return {
            "current_repository": self._format_repository_for_ui(current_repo) if current_repo else None,
            "statistics": statistics,
            "is_selector_visible": self.is_visible
        }

# VS Code集成快速操作
class VSCodeIntegrationActions:
    """VS Code集成快速操作"""
    
    def __init__(self, repository_selector: RepositorySelector):
        self.selector = repository_selector
        self.manager = repository_selector.manager
    
    async def process_uploaded_screenshot(self, image_path: str) -> Dict[str, Any]:
        """处理上传的VS Code截图"""
        try:
            # 使用仓库选择器的导入功能
            result = await self.selector._handle_import_from_vscode(image_path=image_path)
            
            if result.get("success"):
                # 自动显示仓库选择器
                selector_ui = await self.selector.show_repository_selector()
                
                return {
                    "type": "screenshot_processed",
                    "success": True,
                    "import_result": result,
                    "selector_ui": selector_ui,
                    "auto_actions": [
                        {
                            "type": "show_notification",
                            "message": f"成功识别 {len(result.get('imported_projects', []))} 个项目",
                            "duration": 3000
                        },
                        {
                            "type": "highlight_selected",
                            "repository": result.get("selected_repository")
                        }
                    ]
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"处理VS Code截图失败: {e}")
            return {
                "type": "error",
                "success": False,
                "message": str(e)
            }
    
    async def get_context_aware_suggestions(self) -> Dict[str, Any]:
        """获取上下文感知的建议"""
        current_repo = self.manager.get_current_repository()
        
        if not current_repo:
            return {
                "type": "suggestions",
                "suggestions": [
                    {
                        "action": "upload_screenshot",
                        "title": "上传VS Code截图",
                        "description": "上传VS Code界面截图以自动识别项目",
                        "icon": "📷"
                    }
                ]
            }
        
        project_type = current_repo.metadata.get("project_type", "general")
        suggestions = []
        
        if project_type == "powerautomation":
            suggestions.extend([
                {
                    "action": "run_command_master",
                    "title": "运行Command Master",
                    "description": "执行PowerAutomation命令",
                    "icon": "⚡"
                },
                {
                    "action": "trigger_hitl",
                    "title": "触发HITL流程",
                    "description": "启动人机协作决策",
                    "icon": "🤝"
                }
            ])
        
        if project_type == "claudeditor":
            suggestions.extend([
                {
                    "action": "analyze_code",
                    "title": "分析代码",
                    "description": "使用OCR3B_Flux分析代码文档",
                    "icon": "🔍"
                }
            ])
        
        # 通用建议
        suggestions.extend([
            {
                "action": "open_recent_files",
                "title": "打开最近文件",
                "description": "查看最近修改的文件",
                "icon": "📄"
            },
            {
                "action": "switch_repository",
                "title": "切换仓库",
                "description": "切换到其他项目",
                "icon": "🔄"
            }
        ])
        
        return {
            "type": "suggestions",
            "current_repository": current_repo.name,
            "project_type": project_type,
            "suggestions": suggestions
        }

