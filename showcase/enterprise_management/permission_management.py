#!/usr/bin/env python3
"""
企业级权限管理系统
PowerAutomation 4.1 - 完整的RBAC权限控制和安全管理

功能特性:
- 基于角色的访问控制 (RBAC)
- 细粒度权限管理
- 动态权限分配
- 权限继承和委托
- 安全审计和合规
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import jwt
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PermissionType(Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE = "manage"
    APPROVE = "approve"
    AUDIT = "audit"

class ResourceType(Enum):
    """资源类型枚举"""
    PROJECT = "project"
    TOOL = "tool"
    WORKFLOW = "workflow"
    DATA = "data"
    API = "api"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"

class AccessLevel(Enum):
    """访问级别枚举"""
    NONE = 0
    READ_ONLY = 1
    READ_WRITE = 2
    FULL_ACCESS = 3
    ADMIN_ACCESS = 4

@dataclass
class Permission:
    """权限定义"""
    permission_id: str
    name: str
    description: str
    permission_type: PermissionType
    resource_type: ResourceType
    scope: str = "*"  # 权限范围，*表示全部
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Role:
    """角色定义"""
    role_id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    parent_roles: Set[str] = field(default_factory=set)  # 角色继承
    is_system_role: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserRole:
    """用户角色分配"""
    assignment_id: str
    user_id: str
    role_id: str
    resource_scope: str = "*"  # 角色适用的资源范围
    granted_by: str = ""
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceAccess:
    """资源访问记录"""
    access_id: str
    user_id: str
    resource_type: ResourceType
    resource_id: str
    permission_type: PermissionType
    access_level: AccessLevel
    granted: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

@dataclass
class PermissionPolicy:
    """权限策略"""
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    priority: int = 100
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

class EnterprisePermissionManager:
    """企业级权限管理器"""
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[UserRole]] = defaultdict(list)
        self.access_logs: List[ResourceAccess] = []
        self.policies: Dict[str, PermissionPolicy] = {}
        
        # 权限缓存
        self.permission_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 安全配置
        self.security_config = {
            "max_failed_attempts": 5,
            "lockout_duration": 1800,  # 30分钟
            "session_timeout": 3600,   # 1小时
            "require_mfa": False,
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True
            }
        }
        
        # 初始化系统角色和权限
        asyncio.create_task(self._initialize_system_permissions())
        
        logger.info("企业级权限管理器初始化完成")
    
    async def _initialize_system_permissions(self):
        """初始化系统权限和角色"""
        # 创建基础权限
        base_permissions = [
            Permission("perm_read_all", "读取所有", "读取所有资源", PermissionType.READ, ResourceType.SYSTEM),
            Permission("perm_write_all", "写入所有", "写入所有资源", PermissionType.WRITE, ResourceType.SYSTEM),
            Permission("perm_execute_all", "执行所有", "执行所有操作", PermissionType.EXECUTE, ResourceType.SYSTEM),
            Permission("perm_admin_all", "管理所有", "管理所有资源", PermissionType.ADMIN, ResourceType.SYSTEM),
            Permission("perm_audit_all", "审计所有", "审计所有操作", PermissionType.AUDIT, ResourceType.SYSTEM),
            
            # 项目权限
            Permission("perm_project_read", "项目读取", "读取项目信息", PermissionType.READ, ResourceType.PROJECT),
            Permission("perm_project_write", "项目写入", "修改项目信息", PermissionType.WRITE, ResourceType.PROJECT),
            Permission("perm_project_manage", "项目管理", "管理项目", PermissionType.MANAGE, ResourceType.PROJECT),
            
            # 工具权限
            Permission("perm_tool_execute", "工具执行", "执行工具", PermissionType.EXECUTE, ResourceType.TOOL),
            Permission("perm_tool_manage", "工具管理", "管理工具", PermissionType.MANAGE, ResourceType.TOOL),
            
            # 工作流权限
            Permission("perm_workflow_read", "工作流读取", "读取工作流", PermissionType.READ, ResourceType.WORKFLOW),
            Permission("perm_workflow_execute", "工作流执行", "执行工作流", PermissionType.EXECUTE, ResourceType.WORKFLOW),
            Permission("perm_workflow_manage", "工作流管理", "管理工作流", PermissionType.MANAGE, ResourceType.WORKFLOW),
            
            # API权限
            Permission("perm_api_access", "API访问", "访问API", PermissionType.READ, ResourceType.API),
            Permission("perm_api_manage", "API管理", "管理API", PermissionType.MANAGE, ResourceType.API),
            
            # 报告权限
            Permission("perm_report_read", "报告读取", "读取报告", PermissionType.READ, ResourceType.REPORT),
            Permission("perm_report_create", "报告创建", "创建报告", PermissionType.WRITE, ResourceType.REPORT),
            
            # 用户权限
            Permission("perm_user_read", "用户读取", "读取用户信息", PermissionType.READ, ResourceType.USER),
            Permission("perm_user_manage", "用户管理", "管理用户", PermissionType.MANAGE, ResourceType.USER)
        ]
        
        for permission in base_permissions:
            await self.create_permission(permission)
        
        # 创建系统角色
        system_roles = [
            Role("role_super_admin", "超级管理员", "系统超级管理员，拥有所有权限", is_system_role=True),
            Role("role_admin", "管理员", "系统管理员", is_system_role=True),
            Role("role_project_manager", "项目经理", "项目管理员", is_system_role=True),
            Role("role_developer", "开发者", "开发人员", is_system_role=True),
            Role("role_analyst", "分析师", "数据分析师", is_system_role=True),
            Role("role_viewer", "查看者", "只读用户", is_system_role=True),
            Role("role_guest", "访客", "访客用户", is_system_role=True)
        ]
        
        for role in system_roles:
            await self.create_role(role)
        
        # 分配权限给角色
        await self._assign_default_permissions()
    
    async def _assign_default_permissions(self):
        """分配默认权限给系统角色"""
        # 超级管理员 - 所有权限
        super_admin_permissions = list(self.permissions.keys())
        for perm_id in super_admin_permissions:
            await self.assign_permission_to_role("role_super_admin", perm_id)
        
        # 管理员 - 除超级管理员权限外的所有权限
        admin_permissions = [p for p in self.permissions.keys() if "admin_all" not in p]
        for perm_id in admin_permissions:
            await self.assign_permission_to_role("role_admin", perm_id)
        
        # 项目经理 - 项目和工作流管理权限
        pm_permissions = [
            "perm_project_read", "perm_project_write", "perm_project_manage",
            "perm_workflow_read", "perm_workflow_execute", "perm_workflow_manage",
            "perm_tool_execute", "perm_report_read", "perm_report_create",
            "perm_user_read"
        ]
        for perm_id in pm_permissions:
            await self.assign_permission_to_role("role_project_manager", perm_id)
        
        # 开发者 - 开发相关权限
        dev_permissions = [
            "perm_project_read", "perm_project_write",
            "perm_workflow_read", "perm_workflow_execute",
            "perm_tool_execute", "perm_api_access",
            "perm_report_read"
        ]
        for perm_id in dev_permissions:
            await self.assign_permission_to_role("role_developer", perm_id)
        
        # 分析师 - 数据和报告权限
        analyst_permissions = [
            "perm_project_read", "perm_workflow_read",
            "perm_report_read", "perm_report_create",
            "perm_api_access"
        ]
        for perm_id in analyst_permissions:
            await self.assign_permission_to_role("role_analyst", perm_id)
        
        # 查看者 - 只读权限
        viewer_permissions = [
            "perm_project_read", "perm_workflow_read",
            "perm_report_read"
        ]
        for perm_id in viewer_permissions:
            await self.assign_permission_to_role("role_viewer", perm_id)
        
        # 访客 - 最基本的读取权限
        guest_permissions = ["perm_project_read"]
        for perm_id in guest_permissions:
            await self.assign_permission_to_role("role_guest", perm_id)
    
    async def create_permission(self, permission: Permission) -> bool:
        """创建权限"""
        try:
            if permission.permission_id in self.permissions:
                logger.warning(f"权限已存在: {permission.permission_id}")
                return False
            
            self.permissions[permission.permission_id] = permission
            logger.info(f"权限已创建: {permission.name}")
            return True
            
        except Exception as e:
            logger.error(f"创建权限失败: {e}")
            return False
    
    async def create_role(self, role: Role) -> bool:
        """创建角色"""
        try:
            if role.role_id in self.roles:
                logger.warning(f"角色已存在: {role.role_id}")
                return False
            
            self.roles[role.role_id] = role
            logger.info(f"角色已创建: {role.name}")
            return True
            
        except Exception as e:
            logger.error(f"创建角色失败: {e}")
            return False
    
    async def assign_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        try:
            if role_id not in self.roles:
                raise ValueError(f"角色不存在: {role_id}")
            
            if permission_id not in self.permissions:
                raise ValueError(f"权限不存在: {permission_id}")
            
            role = self.roles[role_id]
            role.permissions.add(permission_id)
            
            # 清除相关缓存
            await self._clear_permission_cache(role_id)
            
            logger.info(f"权限已分配: {permission_id} -> {role_id}")
            return True
            
        except Exception as e:
            logger.error(f"分配权限失败: {e}")
            return False
    
    async def assign_role_to_user(self, user_id: str, role_id: str, 
                                granted_by: str, resource_scope: str = "*",
                                expires_at: Optional[datetime] = None) -> str:
        """为用户分配角色"""
        try:
            if role_id not in self.roles:
                raise ValueError(f"角色不存在: {role_id}")
            
            assignment_id = str(uuid.uuid4())
            user_role = UserRole(
                assignment_id=assignment_id,
                user_id=user_id,
                role_id=role_id,
                resource_scope=resource_scope,
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            self.user_roles[user_id].append(user_role)
            
            # 清除用户权限缓存
            await self._clear_user_permission_cache(user_id)
            
            logger.info(f"角色已分配: {role_id} -> {user_id}")
            return assignment_id
            
        except Exception as e:
            logger.error(f"分配角色失败: {e}")
            raise
    
    async def check_permission(self, user_id: str, resource_type: ResourceType,
                             resource_id: str, permission_type: PermissionType,
                             session_id: Optional[str] = None,
                             ip_address: Optional[str] = None) -> bool:
        """检查用户权限"""
        try:
            # 检查缓存
            cache_key = f"{user_id}:{resource_type.value}:{resource_id}:{permission_type.value}"
            cached_result = await self._get_cached_permission(cache_key)
            
            if cached_result is not None:
                granted = cached_result["granted"]
            else:
                # 计算权限
                granted = await self._calculate_permission(user_id, resource_type, resource_id, permission_type)
                
                # 缓存结果
                await self._cache_permission(cache_key, {"granted": granted})
            
            # 记录访问日志
            access_record = ResourceAccess(
                access_id=str(uuid.uuid4()),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_type=permission_type,
                access_level=self._determine_access_level(granted, permission_type),
                granted=granted,
                reason=self._get_permission_reason(granted, user_id, resource_type, permission_type),
                session_id=session_id,
                ip_address=ip_address
            )
            
            self.access_logs.append(access_record)
            
            return granted
            
        except Exception as e:
            logger.error(f"检查权限失败: {e}")
            return False
    
    async def _calculate_permission(self, user_id: str, resource_type: ResourceType,
                                  resource_id: str, permission_type: PermissionType) -> bool:
        """计算用户权限"""
        # 获取用户的所有有效角色
        user_roles = await self._get_effective_user_roles(user_id)
        
        if not user_roles:
            return False
        
        # 检查每个角色的权限
        for user_role in user_roles:
            role = self.roles.get(user_role.role_id)
            if not role or not role.is_active:
                continue
            
            # 检查资源范围
            if not await self._check_resource_scope(user_role.resource_scope, resource_type, resource_id):
                continue
            
            # 获取角色的所有权限（包括继承的权限）
            role_permissions = await self._get_role_permissions(role.role_id)
            
            # 检查权限匹配
            for perm_id in role_permissions:
                permission = self.permissions.get(perm_id)
                if not permission or not permission.is_active:
                    continue
                
                if await self._permission_matches(permission, resource_type, permission_type):
                    return True
        
        return False
    
    async def _get_effective_user_roles(self, user_id: str) -> List[UserRole]:
        """获取用户的有效角色"""
        current_time = datetime.now()
        effective_roles = []
        
        for user_role in self.user_roles.get(user_id, []):
            if not user_role.is_active:
                continue
            
            # 检查过期时间
            if user_role.expires_at and user_role.expires_at <= current_time:
                continue
            
            effective_roles.append(user_role)
        
        return effective_roles
    
    async def _check_resource_scope(self, scope: str, resource_type: ResourceType, resource_id: str) -> bool:
        """检查资源范围"""
        if scope == "*":
            return True
        
        # 支持更复杂的范围匹配逻辑
        if scope.startswith(f"{resource_type.value}:"):
            allowed_resources = scope.split(":")[1].split(",")
            return resource_id in allowed_resources
        
        return scope == resource_id
    
    async def _get_role_permissions(self, role_id: str) -> Set[str]:
        """获取角色的所有权限（包括继承）"""
        permissions = set()
        visited_roles = set()
        
        async def collect_permissions(current_role_id: str):
            if current_role_id in visited_roles:
                return
            
            visited_roles.add(current_role_id)
            role = self.roles.get(current_role_id)
            
            if role and role.is_active:
                permissions.update(role.permissions)
                
                # 递归收集父角色权限
                for parent_role_id in role.parent_roles:
                    await collect_permissions(parent_role_id)
        
        await collect_permissions(role_id)
        return permissions
    
    async def _permission_matches(self, permission: Permission, resource_type: ResourceType,
                                permission_type: PermissionType) -> bool:
        """检查权限是否匹配"""
        # 检查资源类型
        if permission.resource_type != ResourceType.SYSTEM and permission.resource_type != resource_type:
            return False
        
        # 检查权限类型
        if permission.permission_type == PermissionType.ADMIN:
            return True  # 管理员权限包含所有权限
        
        return permission.permission_type == permission_type
    
    def _determine_access_level(self, granted: bool, permission_type: PermissionType) -> AccessLevel:
        """确定访问级别"""
        if not granted:
            return AccessLevel.NONE
        
        access_level_map = {
            PermissionType.READ: AccessLevel.READ_ONLY,
            PermissionType.WRITE: AccessLevel.READ_WRITE,
            PermissionType.EXECUTE: AccessLevel.READ_WRITE,
            PermissionType.DELETE: AccessLevel.FULL_ACCESS,
            PermissionType.ADMIN: AccessLevel.ADMIN_ACCESS,
            PermissionType.MANAGE: AccessLevel.ADMIN_ACCESS,
            PermissionType.APPROVE: AccessLevel.FULL_ACCESS,
            PermissionType.AUDIT: AccessLevel.READ_ONLY
        }
        
        return access_level_map.get(permission_type, AccessLevel.READ_ONLY)
    
    def _get_permission_reason(self, granted: bool, user_id: str, 
                             resource_type: ResourceType, permission_type: PermissionType) -> str:
        """获取权限决策原因"""
        if granted:
            return f"用户 {user_id} 拥有 {resource_type.value} 的 {permission_type.value} 权限"
        else:
            return f"用户 {user_id} 缺少 {resource_type.value} 的 {permission_type.value} 权限"
    
    async def _get_cached_permission(self, cache_key: str) -> Optional[Dict]:
        """获取缓存的权限结果"""
        if cache_key in self.permission_cache:
            cached_data = self.permission_cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=self.cache_ttl):
                return cached_data["data"]
            else:
                del self.permission_cache[cache_key]
        
        return None
    
    async def _cache_permission(self, cache_key: str, data: Dict):
        """缓存权限结果"""
        self.permission_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    async def _clear_permission_cache(self, role_id: str):
        """清除角色相关的权限缓存"""
        # 简化实现：清除所有缓存
        self.permission_cache.clear()
    
    async def _clear_user_permission_cache(self, user_id: str):
        """清除用户权限缓存"""
        keys_to_remove = [key for key in self.permission_cache.keys() if key.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.permission_cache[key]
    
    async def revoke_user_role(self, user_id: str, assignment_id: str) -> bool:
        """撤销用户角色"""
        try:
            user_roles = self.user_roles.get(user_id, [])
            
            for user_role in user_roles:
                if user_role.assignment_id == assignment_id:
                    user_role.is_active = False
                    await self._clear_user_permission_cache(user_id)
                    logger.info(f"角色已撤销: {user_role.role_id} from {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"撤销角色失败: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """获取用户的所有权限"""
        try:
            user_roles = await self._get_effective_user_roles(user_id)
            all_permissions = set()
            role_details = []
            
            for user_role in user_roles:
                role = self.roles.get(user_role.role_id)
                if role and role.is_active:
                    role_permissions = await self._get_role_permissions(role.role_id)
                    all_permissions.update(role_permissions)
                    
                    role_details.append({
                        "role_id": role.role_id,
                        "role_name": role.name,
                        "resource_scope": user_role.resource_scope,
                        "granted_at": user_role.granted_at.isoformat(),
                        "expires_at": user_role.expires_at.isoformat() if user_role.expires_at else None,
                        "permissions": list(role_permissions)
                    })
            
            permission_details = []
            for perm_id in all_permissions:
                permission = self.permissions.get(perm_id)
                if permission:
                    permission_details.append({
                        "permission_id": permission.permission_id,
                        "name": permission.name,
                        "type": permission.permission_type.value,
                        "resource_type": permission.resource_type.value,
                        "scope": permission.scope
                    })
            
            return {
                "user_id": user_id,
                "roles": role_details,
                "permissions": permission_details,
                "total_permissions": len(all_permissions),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return {}
    
    async def get_access_audit_log(self, user_id: Optional[str] = None,
                                 resource_type: Optional[ResourceType] = None,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """获取访问审计日志"""
        try:
            filtered_logs = self.access_logs
            
            # 应用过滤条件
            if user_id:
                filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
            
            if resource_type:
                filtered_logs = [log for log in filtered_logs if log.resource_type == resource_type]
            
            if start_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
            
            if end_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
            
            # 按时间倒序排序
            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 限制结果数量
            filtered_logs = filtered_logs[:limit]
            
            # 转换为字典格式
            audit_logs = []
            for log in filtered_logs:
                audit_logs.append({
                    "access_id": log.access_id,
                    "user_id": log.user_id,
                    "resource_type": log.resource_type.value,
                    "resource_id": log.resource_id,
                    "permission_type": log.permission_type.value,
                    "access_level": log.access_level.value,
                    "granted": log.granted,
                    "reason": log.reason,
                    "timestamp": log.timestamp.isoformat(),
                    "session_id": log.session_id,
                    "ip_address": log.ip_address
                })
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return []
    
    async def get_permission_statistics(self) -> Dict[str, Any]:
        """获取权限统计信息"""
        try:
            # 统计基本信息
            total_permissions = len(self.permissions)
            total_roles = len(self.roles)
            total_users_with_roles = len(self.user_roles)
            
            # 统计角色使用情况
            role_usage = defaultdict(int)
            for user_roles in self.user_roles.values():
                for user_role in user_roles:
                    if user_role.is_active:
                        role_usage[user_role.role_id] += 1
            
            # 统计权限使用情况
            permission_usage = defaultdict(int)
            for role in self.roles.values():
                for perm_id in role.permissions:
                    permission_usage[perm_id] += role_usage[role.role_id]
            
            # 统计访问情况
            recent_accesses = [log for log in self.access_logs 
                             if log.timestamp >= datetime.now() - timedelta(days=7)]
            
            access_stats = {
                "total_accesses": len(recent_accesses),
                "granted_accesses": len([log for log in recent_accesses if log.granted]),
                "denied_accesses": len([log for log in recent_accesses if not log.granted])
            }
            
            return {
                "overview": {
                    "total_permissions": total_permissions,
                    "total_roles": total_roles,
                    "total_users_with_roles": total_users_with_roles,
                    "cache_size": len(self.permission_cache)
                },
                "role_usage": dict(role_usage),
                "permission_usage": dict(permission_usage),
                "access_statistics": access_stats,
                "most_used_roles": sorted(role_usage.items(), key=lambda x: x[1], reverse=True)[:5],
                "most_used_permissions": sorted(permission_usage.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"获取权限统计失败: {e}")
            return {}

# 示例使用
async def main():
    """示例主函数"""
    perm_manager = EnterprisePermissionManager()
    
    # 等待初始化完成
    await asyncio.sleep(1)
    
    # 为用户分配角色
    assignment_id = await perm_manager.assign_role_to_user(
        user_id="user123",
        role_id="role_developer",
        granted_by="admin"
    )
    
    # 检查权限
    has_permission = await perm_manager.check_permission(
        user_id="user123",
        resource_type=ResourceType.PROJECT,
        resource_id="project_001",
        permission_type=PermissionType.READ
    )
    
    print(f"用户权限检查结果: {has_permission}")
    
    # 获取用户权限
    user_permissions = await perm_manager.get_user_permissions("user123")
    print(f"用户权限详情: {json.dumps(user_permissions, indent=2, ensure_ascii=False)}")
    
    # 获取统计信息
    stats = await perm_manager.get_permission_statistics()
    print(f"权限统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())

