#!/usr/bin/env python3
"""
团队协作系统
PowerAutomation 4.1 - 企业级团队协作和实时同步

功能特性:
- 团队和项目管理
- 实时协作和同步
- 任务分配和跟踪
- 文档协作编辑
- 通信和通知系统
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque
import websockets
import weakref

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamRole(Enum):
    """团队角色枚举"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    GUEST = "guest"

class ProjectStatus(Enum):
    """项目状态枚举"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    """任务状态枚举"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CollaborationType(Enum):
    """协作类型枚举"""
    DOCUMENT = "document"
    CODE = "code"
    DESIGN = "design"
    MEETING = "meeting"
    DISCUSSION = "discussion"

@dataclass
class Team:
    """团队信息"""
    team_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TeamMember:
    """团队成员"""
    member_id: str
    team_id: str
    user_id: str
    role: TeamRole
    joined_at: datetime = field(default_factory=datetime.now)
    invited_by: Optional[str] = None
    is_active: bool = True
    permissions: Set[str] = field(default_factory=set)

@dataclass
class Project:
    """项目信息"""
    project_id: str
    team_id: str
    name: str
    description: str
    status: ProjectStatus = ProjectStatus.PLANNING
    owner_id: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    progress: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Task:
    """任务信息"""
    task_id: str
    project_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[str] = None
    reporter_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)

@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    project_id: str
    collaboration_type: CollaborationType
    title: str
    participants: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    is_active: bool = False
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RealTimeSync:
    """实时同步数据"""
    sync_id: str
    session_id: str
    user_id: str
    operation_type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False

@dataclass
class Notification:
    """通知信息"""
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    is_read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class TeamCollaborationManager:
    """团队协作管理器"""
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.team_members: Dict[str, List[TeamMember]] = defaultdict(list)
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        self.notifications: Dict[str, List[Notification]] = defaultdict(list)
        
        # 实时同步
        self.sync_operations: deque = deque(maxlen=10000)
        self.active_connections: Dict[str, Set[Any]] = defaultdict(set)
        
        # 索引
        self.user_teams: Dict[str, Set[str]] = defaultdict(set)
        self.team_projects: Dict[str, Set[str]] = defaultdict(set)
        self.project_tasks: Dict[str, Set[str]] = defaultdict(set)
        self.user_tasks: Dict[str, Set[str]] = defaultdict(set)
        
        # 协作统计
        self.collaboration_stats = {
            "total_teams": 0,
            "total_projects": 0,
            "total_tasks": 0,
            "active_sessions": 0,
            "total_notifications": 0,
            "collaboration_hours": 0.0
        }
        
        # 启动后台任务
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("团队协作管理器初始化完成")
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        # 统计更新任务
        asyncio.create_task(self._stats_update_task())
        
        # 通知清理任务
        asyncio.create_task(self._notification_cleanup_task())
        
        # 会话管理任务
        asyncio.create_task(self._session_management_task())
    
    async def _stats_update_task(self):
        """统计更新任务"""
        while True:
            try:
                await self._update_collaboration_statistics()
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except Exception as e:
                logger.error(f"统计更新任务失败: {e}")
                await asyncio.sleep(60)
    
    async def _notification_cleanup_task(self):
        """通知清理任务"""
        while True:
            try:
                # 清理30天前的已读通知
                cutoff_time = datetime.now() - timedelta(days=30)
                
                for user_id, notifications in self.notifications.items():
                    self.notifications[user_id] = [
                        notif for notif in notifications
                        if not notif.is_read or notif.created_at >= cutoff_time
                    ]
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                logger.error(f"通知清理任务失败: {e}")
                await asyncio.sleep(3600)
    
    async def _session_management_task(self):
        """会话管理任务"""
        while True:
            try:
                current_time = datetime.now()
                
                # 检查超时的协作会话
                for session in self.collaboration_sessions.values():
                    if (session.is_active and 
                        session.started_at and 
                        current_time - session.started_at > timedelta(hours=8)):
                        
                        await self.end_collaboration_session(session.session_id)
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"会话管理任务失败: {e}")
                await asyncio.sleep(300)
    
    async def create_team(self, name: str, description: str, owner_id: str,
                         settings: Optional[Dict[str, Any]] = None) -> str:
        """创建团队"""
        try:
            team_id = str(uuid.uuid4())
            
            team = Team(
                team_id=team_id,
                name=name,
                description=description,
                owner_id=owner_id,
                settings=settings or {}
            )
            
            self.teams[team_id] = team
            
            # 添加创建者为团队所有者
            await self.add_team_member(team_id, owner_id, TeamRole.OWNER, owner_id)
            
            logger.info(f"团队已创建: {name} ({team_id})")
            return team_id
            
        except Exception as e:
            logger.error(f"创建团队失败: {e}")
            raise
    
    async def add_team_member(self, team_id: str, user_id: str, role: TeamRole,
                            invited_by: str) -> str:
        """添加团队成员"""
        try:
            if team_id not in self.teams:
                raise ValueError("团队不存在")
            
            # 检查用户是否已是团队成员
            existing_members = self.team_members.get(team_id, [])
            for member in existing_members:
                if member.user_id == user_id and member.is_active:
                    raise ValueError("用户已是团队成员")
            
            member_id = str(uuid.uuid4())
            
            member = TeamMember(
                member_id=member_id,
                team_id=team_id,
                user_id=user_id,
                role=role,
                invited_by=invited_by
            )
            
            self.team_members[team_id].append(member)
            self.user_teams[user_id].add(team_id)
            
            # 发送通知
            await self._send_notification(
                user_id, "团队邀请", 
                f"您已被邀请加入团队: {self.teams[team_id].name}",
                "team_invitation"
            )
            
            logger.info(f"团队成员已添加: {user_id} -> {team_id}")
            return member_id
            
        except Exception as e:
            logger.error(f"添加团队成员失败: {e}")
            raise
    
    async def create_project(self, team_id: str, name: str, description: str,
                           owner_id: str, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           tags: Optional[List[str]] = None) -> str:
        """创建项目"""
        try:
            if team_id not in self.teams:
                raise ValueError("团队不存在")
            
            # 验证用户是否有权限创建项目
            if not await self._check_team_permission(team_id, owner_id, "create_project"):
                raise ValueError("用户无权限创建项目")
            
            project_id = str(uuid.uuid4())
            
            project = Project(
                project_id=project_id,
                team_id=team_id,
                name=name,
                description=description,
                owner_id=owner_id,
                start_date=start_date,
                end_date=end_date,
                tags=tags or []
            )
            
            self.projects[project_id] = project
            self.team_projects[team_id].add(project_id)
            
            # 通知团队成员
            await self._notify_team_members(
                team_id, "新项目创建", 
                f"项目 '{name}' 已创建",
                "project_created",
                exclude_user=owner_id
            )
            
            logger.info(f"项目已创建: {name} ({project_id})")
            return project_id
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            raise
    
    async def create_task(self, project_id: str, title: str, description: str,
                         reporter_id: str, assignee_id: Optional[str] = None,
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         due_date: Optional[datetime] = None,
                         estimated_hours: Optional[float] = None,
                         tags: Optional[List[str]] = None) -> str:
        """创建任务"""
        try:
            if project_id not in self.projects:
                raise ValueError("项目不存在")
            
            project = self.projects[project_id]
            
            # 验证用户权限
            if not await self._check_team_permission(project.team_id, reporter_id, "create_task"):
                raise ValueError("用户无权限创建任务")
            
            task_id = str(uuid.uuid4())
            
            task = Task(
                task_id=task_id,
                project_id=project_id,
                title=title,
                description=description,
                priority=priority,
                assignee_id=assignee_id,
                reporter_id=reporter_id,
                due_date=due_date,
                estimated_hours=estimated_hours,
                tags=tags or []
            )
            
            self.tasks[task_id] = task
            self.project_tasks[project_id].add(task_id)
            
            if assignee_id:
                self.user_tasks[assignee_id].add(task_id)
                
                # 通知被分配者
                await self._send_notification(
                    assignee_id, "任务分配", 
                    f"您被分配了新任务: {title}",
                    "task_assigned"
                )
            
            logger.info(f"任务已创建: {title} ({task_id})")
            return task_id
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise
    
    async def start_collaboration_session(self, project_id: str, collaboration_type: CollaborationType,
                                        title: str, initiator_id: str,
                                        participants: Optional[List[str]] = None) -> str:
        """开始协作会话"""
        try:
            if project_id not in self.projects:
                raise ValueError("项目不存在")
            
            project = self.projects[project_id]
            
            # 验证用户权限
            if not await self._check_team_permission(project.team_id, initiator_id, "start_collaboration"):
                raise ValueError("用户无权限开始协作")
            
            session_id = str(uuid.uuid4())
            
            session = CollaborationSession(
                session_id=session_id,
                project_id=project_id,
                collaboration_type=collaboration_type,
                title=title,
                participants=set(participants or []) | {initiator_id},
                is_active=True,
                started_at=datetime.now()
            )
            
            self.collaboration_sessions[session_id] = session
            
            # 通知参与者
            for participant_id in session.participants:
                if participant_id != initiator_id:
                    await self._send_notification(
                        participant_id, "协作邀请", 
                        f"您被邀请参与协作: {title}",
                        "collaboration_invitation"
                    )
            
            logger.info(f"协作会话已开始: {title} ({session_id})")
            return session_id
            
        except Exception as e:
            logger.error(f"开始协作会话失败: {e}")
            raise
    
    async def sync_real_time_operation(self, session_id: str, user_id: str,
                                     operation_type: str, data: Dict[str, Any]) -> str:
        """同步实时操作"""
        try:
            if session_id not in self.collaboration_sessions:
                raise ValueError("协作会话不存在")
            
            session = self.collaboration_sessions[session_id]
            
            if not session.is_active:
                raise ValueError("协作会话未激活")
            
            if user_id not in session.participants:
                raise ValueError("用户不是协作参与者")
            
            sync_id = str(uuid.uuid4())
            
            sync_operation = RealTimeSync(
                sync_id=sync_id,
                session_id=session_id,
                user_id=user_id,
                operation_type=operation_type,
                data=data
            )
            
            self.sync_operations.append(sync_operation)
            
            # 广播给其他参与者
            await self._broadcast_sync_operation(session_id, sync_operation, exclude_user=user_id)
            
            return sync_id
            
        except Exception as e:
            logger.error(f"同步实时操作失败: {e}")
            raise
    
    async def _broadcast_sync_operation(self, session_id: str, sync_operation: RealTimeSync,
                                      exclude_user: Optional[str] = None):
        """广播同步操作"""
        try:
            session = self.collaboration_sessions[session_id]
            
            broadcast_data = {
                "type": "sync_operation",
                "sync_id": sync_operation.sync_id,
                "session_id": session_id,
                "user_id": sync_operation.user_id,
                "operation_type": sync_operation.operation_type,
                "data": sync_operation.data,
                "timestamp": sync_operation.timestamp.isoformat()
            }
            
            # 发送给所有连接的参与者
            for participant_id in session.participants:
                if participant_id != exclude_user:
                    await self._send_to_user_connections(participant_id, broadcast_data)
            
        except Exception as e:
            logger.error(f"广播同步操作失败: {e}")
    
    async def _send_to_user_connections(self, user_id: str, data: Dict[str, Any]):
        """发送数据给用户的所有连接"""
        connections = self.active_connections.get(user_id, set())
        
        # 清理无效连接
        valid_connections = set()
        
        for connection in connections:
            try:
                if hasattr(connection, 'send'):
                    await connection.send(json.dumps(data))
                    valid_connections.add(connection)
            except Exception:
                # 连接已断开，忽略
                pass
        
        self.active_connections[user_id] = valid_connections
    
    async def end_collaboration_session(self, session_id: str) -> bool:
        """结束协作会话"""
        try:
            if session_id not in self.collaboration_sessions:
                return False
            
            session = self.collaboration_sessions[session_id]
            session.is_active = False
            session.ended_at = datetime.now()
            
            # 计算协作时长
            if session.started_at:
                duration = (session.ended_at - session.started_at).total_seconds() / 3600
                self.collaboration_stats["collaboration_hours"] += duration
            
            # 通知参与者
            for participant_id in session.participants:
                await self._send_notification(
                    participant_id, "协作结束", 
                    f"协作会话 '{session.title}' 已结束",
                    "collaboration_ended"
                )
            
            logger.info(f"协作会话已结束: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"结束协作会话失败: {e}")
            return False
    
    async def update_task_status(self, task_id: str, new_status: TaskStatus,
                               user_id: str, comment: Optional[str] = None) -> bool:
        """更新任务状态"""
        try:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            project = self.projects[task.project_id]
            
            # 验证用户权限
            if not await self._check_task_permission(task_id, user_id, "update_status"):
                raise ValueError("用户无权限更新任务状态")
            
            old_status = task.status
            task.status = new_status
            task.updated_at = datetime.now()
            
            # 更新项目进度
            await self._update_project_progress(task.project_id)
            
            # 通知相关人员
            notification_users = {task.assignee_id, task.reporter_id} - {user_id}
            notification_users = {uid for uid in notification_users if uid}
            
            for user_id_to_notify in notification_users:
                await self._send_notification(
                    user_id_to_notify, "任务状态更新", 
                    f"任务 '{task.title}' 状态从 {old_status.value} 更新为 {new_status.value}",
                    "task_status_updated"
                )
            
            logger.info(f"任务状态已更新: {task_id} -> {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def _update_project_progress(self, project_id: str):
        """更新项目进度"""
        try:
            project_task_ids = self.project_tasks.get(project_id, set())
            
            if not project_task_ids:
                return
            
            total_tasks = len(project_task_ids)
            completed_tasks = 0
            
            for task_id in project_task_ids:
                task = self.tasks.get(task_id)
                if task and task.status == TaskStatus.DONE:
                    completed_tasks += 1
            
            progress = (completed_tasks / total_tasks) * 100
            self.projects[project_id].progress = progress
            self.projects[project_id].updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"更新项目进度失败: {e}")
    
    async def _check_team_permission(self, team_id: str, user_id: str, permission: str) -> bool:
        """检查团队权限"""
        try:
            team_members_list = self.team_members.get(team_id, [])
            
            for member in team_members_list:
                if member.user_id == user_id and member.is_active:
                    # 简化的权限检查逻辑
                    if member.role in [TeamRole.OWNER, TeamRole.ADMIN]:
                        return True
                    elif member.role == TeamRole.MANAGER and permission in ["create_project", "create_task", "start_collaboration"]:
                        return True
                    elif member.role == TeamRole.MEMBER and permission in ["create_task", "start_collaboration"]:
                        return True
                    
                    return permission in member.permissions
            
            return False
            
        except Exception as e:
            logger.error(f"检查团队权限失败: {e}")
            return False
    
    async def _check_task_permission(self, task_id: str, user_id: str, permission: str) -> bool:
        """检查任务权限"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            project = self.projects.get(task.project_id)
            if not project:
                return False
            
            # 任务分配者和报告者有权限
            if user_id in [task.assignee_id, task.reporter_id]:
                return True
            
            # 检查团队权限
            return await self._check_team_permission(project.team_id, user_id, permission)
            
        except Exception as e:
            logger.error(f"检查任务权限失败: {e}")
            return False
    
    async def _send_notification(self, user_id: str, title: str, message: str,
                               notification_type: str, metadata: Optional[Dict[str, Any]] = None):
        """发送通知"""
        try:
            notification_id = str(uuid.uuid4())
            
            notification = Notification(
                notification_id=notification_id,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                metadata=metadata or {}
            )
            
            self.notifications[user_id].append(notification)
            
            # 实时推送通知
            notification_data = {
                "type": "notification",
                "notification_id": notification_id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "created_at": notification.created_at.isoformat()
            }
            
            await self._send_to_user_connections(user_id, notification_data)
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def _notify_team_members(self, team_id: str, title: str, message: str,
                                 notification_type: str, exclude_user: Optional[str] = None):
        """通知团队成员"""
        try:
            team_members_list = self.team_members.get(team_id, [])
            
            for member in team_members_list:
                if member.is_active and member.user_id != exclude_user:
                    await self._send_notification(
                        member.user_id, title, message, notification_type
                    )
            
        except Exception as e:
            logger.error(f"通知团队成员失败: {e}")
    
    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """获取用户协作仪表板"""
        try:
            # 获取用户的团队
            user_team_ids = self.user_teams.get(user_id, set())
            user_teams = [self.teams[team_id] for team_id in user_team_ids if team_id in self.teams]
            
            # 获取用户的项目
            user_projects = []
            for team_id in user_team_ids:
                project_ids = self.team_projects.get(team_id, set())
                for project_id in project_ids:
                    if project_id in self.projects:
                        user_projects.append(self.projects[project_id])
            
            # 获取用户的任务
            user_task_ids = self.user_tasks.get(user_id, set())
            user_tasks = [self.tasks[task_id] for task_id in user_task_ids if task_id in self.tasks]
            
            # 获取用户的通知
            user_notifications = self.notifications.get(user_id, [])
            unread_notifications = [notif for notif in user_notifications if not notif.is_read]
            
            # 获取活跃的协作会话
            active_sessions = [
                session for session in self.collaboration_sessions.values()
                if session.is_active and user_id in session.participants
            ]
            
            return {
                "user_id": user_id,
                "teams": [
                    {
                        "team_id": team.team_id,
                        "name": team.name,
                        "description": team.description,
                        "member_count": len(self.team_members.get(team.team_id, [])),
                        "project_count": len(self.team_projects.get(team.team_id, set()))
                    }
                    for team in user_teams
                ],
                "projects": [
                    {
                        "project_id": project.project_id,
                        "name": project.name,
                        "status": project.status.value,
                        "progress": project.progress,
                        "task_count": len(self.project_tasks.get(project.project_id, set()))
                    }
                    for project in user_projects
                ],
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "project_name": self.projects.get(task.project_id, {}).name if task.project_id in self.projects else "Unknown"
                    }
                    for task in user_tasks
                ],
                "notifications": {
                    "total": len(user_notifications),
                    "unread": len(unread_notifications),
                    "recent": [
                        {
                            "notification_id": notif.notification_id,
                            "title": notif.title,
                            "message": notif.message,
                            "type": notif.notification_type,
                            "created_at": notif.created_at.isoformat(),
                            "is_read": notif.is_read
                        }
                        for notif in user_notifications[-10:]
                    ]
                },
                "active_collaborations": [
                    {
                        "session_id": session.session_id,
                        "title": session.title,
                        "type": session.collaboration_type.value,
                        "participant_count": len(session.participants),
                        "started_at": session.started_at.isoformat() if session.started_at else None
                    }
                    for session in active_sessions
                ]
            }
            
        except Exception as e:
            logger.error(f"获取用户仪表板失败: {e}")
            return {}
    
    async def get_team_analytics(self, team_id: str) -> Dict[str, Any]:
        """获取团队分析数据"""
        try:
            if team_id not in self.teams:
                return {}
            
            team = self.teams[team_id]
            team_members_list = self.team_members.get(team_id, [])
            project_ids = self.team_projects.get(team_id, set())
            
            # 项目统计
            projects = [self.projects[pid] for pid in project_ids if pid in self.projects]
            project_stats = {
                "total": len(projects),
                "active": len([p for p in projects if p.status == ProjectStatus.ACTIVE]),
                "completed": len([p for p in projects if p.status == ProjectStatus.COMPLETED]),
                "average_progress": sum(p.progress for p in projects) / len(projects) if projects else 0
            }
            
            # 任务统计
            all_task_ids = set()
            for project_id in project_ids:
                all_task_ids.update(self.project_tasks.get(project_id, set()))
            
            all_tasks = [self.tasks[tid] for tid in all_task_ids if tid in self.tasks]
            task_stats = {
                "total": len(all_tasks),
                "todo": len([t for t in all_tasks if t.status == TaskStatus.TODO]),
                "in_progress": len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]),
                "done": len([t for t in all_tasks if t.status == TaskStatus.DONE]),
                "blocked": len([t for t in all_tasks if t.status == TaskStatus.BLOCKED])
            }
            
            # 协作统计
            team_sessions = [
                session for session in self.collaboration_sessions.values()
                if self.projects.get(session.project_id, {}).team_id == team_id
            ]
            
            collaboration_stats = {
                "total_sessions": len(team_sessions),
                "active_sessions": len([s for s in team_sessions if s.is_active]),
                "total_hours": sum(
                    (s.ended_at - s.started_at).total_seconds() / 3600
                    for s in team_sessions
                    if s.started_at and s.ended_at
                )
            }
            
            return {
                "team_info": {
                    "team_id": team.team_id,
                    "name": team.name,
                    "member_count": len([m for m in team_members_list if m.is_active]),
                    "created_at": team.created_at.isoformat()
                },
                "project_statistics": project_stats,
                "task_statistics": task_stats,
                "collaboration_statistics": collaboration_stats,
                "member_activity": await self._calculate_member_activity(team_id),
                "productivity_trends": await self._calculate_productivity_trends(team_id)
            }
            
        except Exception as e:
            logger.error(f"获取团队分析失败: {e}")
            return {}
    
    async def _calculate_member_activity(self, team_id: str) -> Dict[str, Any]:
        """计算成员活动度"""
        try:
            team_members_list = self.team_members.get(team_id, [])
            activity_data = {}
            
            for member in team_members_list:
                if not member.is_active:
                    continue
                
                user_id = member.user_id
                
                # 计算用户的任务完成情况
                user_task_ids = self.user_tasks.get(user_id, set())
                user_tasks = [self.tasks[tid] for tid in user_task_ids if tid in self.tasks]
                
                completed_tasks = len([t for t in user_tasks if t.status == TaskStatus.DONE])
                total_tasks = len(user_tasks)
                
                # 计算协作参与度
                user_sessions = [
                    session for session in self.collaboration_sessions.values()
                    if user_id in session.participants
                ]
                
                activity_data[user_id] = {
                    "role": member.role.value,
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
                    "collaboration_sessions": len(user_sessions),
                    "active_collaborations": len([s for s in user_sessions if s.is_active])
                }
            
            return activity_data
            
        except Exception as e:
            logger.error(f"计算成员活动度失败: {e}")
            return {}
    
    async def _calculate_productivity_trends(self, team_id: str) -> Dict[str, Any]:
        """计算生产力趋势"""
        try:
            # 获取最近30天的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            project_ids = self.team_projects.get(team_id, set())
            
            # 按天统计任务完成情况
            daily_completions = defaultdict(int)
            daily_creations = defaultdict(int)
            
            for project_id in project_ids:
                task_ids = self.project_tasks.get(project_id, set())
                
                for task_id in task_ids:
                    task = self.tasks.get(task_id)
                    if not task:
                        continue
                    
                    # 任务创建统计
                    if start_date <= task.created_at <= end_date:
                        day_key = task.created_at.date().isoformat()
                        daily_creations[day_key] += 1
                    
                    # 任务完成统计（基于更新时间和状态）
                    if (task.status == TaskStatus.DONE and 
                        start_date <= task.updated_at <= end_date):
                        day_key = task.updated_at.date().isoformat()
                        daily_completions[day_key] += 1
            
            return {
                "daily_task_creations": dict(daily_creations),
                "daily_task_completions": dict(daily_completions),
                "trend_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"计算生产力趋势失败: {e}")
            return {}
    
    async def _update_collaboration_statistics(self):
        """更新协作统计"""
        try:
            self.collaboration_stats["total_teams"] = len(self.teams)
            self.collaboration_stats["total_projects"] = len(self.projects)
            self.collaboration_stats["total_tasks"] = len(self.tasks)
            self.collaboration_stats["active_sessions"] = len([
                session for session in self.collaboration_sessions.values()
                if session.is_active
            ])
            self.collaboration_stats["total_notifications"] = sum(
                len(notifications) for notifications in self.notifications.values()
            )
            
        except Exception as e:
            logger.error(f"更新协作统计失败: {e}")

# 示例使用
async def main():
    """示例主函数"""
    collab_manager = TeamCollaborationManager()
    
    # 创建团队
    team_id = await collab_manager.create_team(
        name="AI开发团队",
        description="PowerAutomation AI功能开发团队",
        owner_id="user123"
    )
    
    # 添加团队成员
    await collab_manager.add_team_member(team_id, "user456", TeamRole.DEVELOPER, "user123")
    
    # 创建项目
    project_id = await collab_manager.create_project(
        team_id=team_id,
        name="AI助手优化",
        description="优化AI助手的响应速度和准确性",
        owner_id="user123"
    )
    
    # 创建任务
    task_id = await collab_manager.create_task(
        project_id=project_id,
        title="实现智能缓存机制",
        description="为AI助手实现智能缓存以提高响应速度",
        reporter_id="user123",
        assignee_id="user456",
        priority=TaskPriority.HIGH
    )
    
    # 开始协作会话
    session_id = await collab_manager.start_collaboration_session(
        project_id=project_id,
        collaboration_type=CollaborationType.CODE,
        title="代码审查会议",
        initiator_id="user123",
        participants=["user456"]
    )
    
    # 获取用户仪表板
    dashboard = await collab_manager.get_user_dashboard("user123")
    print(f"用户仪表板: {json.dumps(dashboard, indent=2, ensure_ascii=False)}")
    
    # 获取团队分析
    analytics = await collab_manager.get_team_analytics(team_id)
    print(f"团队分析: {json.dumps(analytics, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())

