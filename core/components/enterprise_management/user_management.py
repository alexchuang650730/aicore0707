#!/usr/bin/env python3
"""
企业级用户管理系统
PowerAutomation 4.1 - 完整的用户生命周期管理和身份认证

功能特性:
- 用户生命周期管理
- 身份认证和授权
- 用户画像和行为分析
- 会话管理和安全
- 多因素认证 (MFA)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import jwt
import secrets
import pyotp
from collections import defaultdict, deque

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserStatus(Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING = "pending"
    DELETED = "deleted"

class AuthenticationMethod(Enum):
    """认证方式枚举"""
    PASSWORD = "password"
    MFA = "mfa"
    SSO = "sso"
    API_KEY = "api_key"
    OAUTH = "oauth"
    LDAP = "ldap"

class SessionStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"

@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    email: str
    full_name: str
    password_hash: str = ""
    status: UserStatus = UserStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    email_verified: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    department: Optional[str] = None
    job_title: Optional[str] = None
    manager_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    activity_score: float = 0.0
    collaboration_score: float = 0.0
    productivity_score: float = 0.0
    learning_progress: Dict[str, float] = field(default_factory=dict)
    usage_patterns: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    authentication_method: AuthenticationMethod = AuthenticationMethod.PASSWORD
    mfa_verified: bool = False
    device_fingerprint: Optional[str] = None
    location: Optional[str] = None

@dataclass
class UserActivity:
    """用户活动记录"""
    activity_id: str
    user_id: str
    activity_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MFAConfig:
    """多因素认证配置"""
    user_id: str
    enabled: bool = False
    secret_key: str = ""
    backup_codes: List[str] = field(default_factory=list)
    recovery_email: Optional[str] = None
    recovery_phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

class EnterpriseUserManager:
    """企业级用户管理器"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.activities: List[UserActivity] = []
        self.mfa_configs: Dict[str, MFAConfig] = {}
        
        # 用户索引
        self.username_index: Dict[str, str] = {}  # username -> user_id
        self.email_index: Dict[str, str] = {}     # email -> user_id
        
        # 安全配置
        self.security_config = {
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_numbers": True,
            "password_require_symbols": True,
            "max_failed_attempts": 5,
            "lockout_duration": 1800,  # 30分钟
            "session_timeout": 3600,   # 1小时
            "password_expiry_days": 90,
            "require_mfa": False,
            "allowed_domains": [],
            "password_history_count": 5
        }
        
        # JWT配置
        self.jwt_secret = secrets.token_urlsafe(32)
        self.jwt_algorithm = "HS256"
        
        # 活动统计
        self.user_stats = {
            "total_users": 0,
            "active_users": 0,
            "total_sessions": 0,
            "active_sessions": 0,
            "total_activities": 0,
            "failed_logins": 0
        }
        
        # 启动后台任务
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("企业级用户管理器初始化完成")
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        # 会话清理任务
        asyncio.create_task(self._session_cleanup_task())
        
        # 用户画像更新任务
        asyncio.create_task(self._profile_update_task())
        
        # 统计更新任务
        asyncio.create_task(self._stats_update_task())
    
    async def _session_cleanup_task(self):
        """会话清理任务"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if session.expires_at <= current_time or session.status != SessionStatus.ACTIVE:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    session = self.sessions[session_id]
                    session.status = SessionStatus.EXPIRED
                    await self._log_activity(
                        session.user_id, "session_expired", 
                        f"会话已过期: {session_id}",
                        session_id=session_id
                    )
                
                if expired_sessions:
                    logger.info(f"清理过期会话: {len(expired_sessions)} 个")
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"会话清理任务失败: {e}")
                await asyncio.sleep(300)
    
    async def _profile_update_task(self):
        """用户画像更新任务"""
        while True:
            try:
                # 更新用户画像
                for user_id in self.users.keys():
                    await self._update_user_profile(user_id)
                
                await asyncio.sleep(3600)  # 每小时更新一次
                
            except Exception as e:
                logger.error(f"用户画像更新任务失败: {e}")
                await asyncio.sleep(3600)
    
    async def _stats_update_task(self):
        """统计更新任务"""
        while True:
            try:
                await self._update_user_statistics()
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except Exception as e:
                logger.error(f"统计更新任务失败: {e}")
                await asyncio.sleep(60)
    
    async def create_user(self, username: str, email: str, full_name: str,
                         password: str, department: Optional[str] = None,
                         job_title: Optional[str] = None,
                         manager_id: Optional[str] = None) -> str:
        """创建用户"""
        try:
            # 验证输入
            if not await self._validate_username(username):
                raise ValueError("用户名不符合要求或已存在")
            
            if not await self._validate_email(email):
                raise ValueError("邮箱不符合要求或已存在")
            
            if not await self._validate_password(password):
                raise ValueError("密码不符合安全要求")
            
            # 生成用户ID
            user_id = str(uuid.uuid4())
            
            # 创建用户
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=await self._hash_password(password),
                department=department,
                job_title=job_title,
                manager_id=manager_id
            )
            
            # 存储用户
            self.users[user_id] = user
            self.username_index[username] = user_id
            self.email_index[email] = user_id
            
            # 创建用户画像
            profile = UserProfile(user_id=user_id)
            self.user_profiles[user_id] = profile
            
            # 记录活动
            await self._log_activity(user_id, "user_created", f"用户已创建: {username}")
            
            logger.info(f"用户已创建: {username} ({user_id})")
            return user_id
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str,
                              ip_address: Optional[str] = None,
                              user_agent: Optional[str] = None) -> Optional[str]:
        """用户认证"""
        try:
            # 查找用户
            user_id = self.username_index.get(username) or self.email_index.get(username)
            if not user_id:
                await self._log_failed_login(username, "用户不存在", ip_address)
                return None
            
            user = self.users[user_id]
            
            # 检查用户状态
            if user.status != UserStatus.ACTIVE:
                await self._log_failed_login(username, f"用户状态: {user.status.value}", ip_address)
                return None
            
            # 检查账户锁定
            if user.locked_until and user.locked_until > datetime.now():
                await self._log_failed_login(username, "账户已锁定", ip_address)
                return None
            
            # 验证密码
            if not await self._verify_password(password, user.password_hash):
                user.failed_login_attempts += 1
                
                # 检查是否需要锁定账户
                if user.failed_login_attempts >= self.security_config["max_failed_attempts"]:
                    user.locked_until = datetime.now() + timedelta(seconds=self.security_config["lockout_duration"])
                    await self._log_activity(user_id, "account_locked", "账户因多次失败登录被锁定")
                
                await self._log_failed_login(username, "密码错误", ip_address)
                return None
            
            # 认证成功
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()
            
            # 创建会话
            session_id = await self._create_session(user_id, ip_address, user_agent)
            
            # 记录活动
            await self._log_activity(user_id, "login_success", "用户登录成功", session_id=session_id, ip_address=ip_address)
            
            logger.info(f"用户认证成功: {username}")
            return session_id
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    async def _create_session(self, user_id: str, ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> str:
        """创建用户会话"""
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(seconds=self.security_config["session_timeout"])
        )
        
        self.sessions[session_id] = session
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[str]:
        """验证会话"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            current_time = datetime.now()
            
            # 检查会话状态和过期时间
            if session.status != SessionStatus.ACTIVE or session.expires_at <= current_time:
                session.status = SessionStatus.EXPIRED
                return None
            
            # 更新最后活动时间
            session.last_activity = current_time
            
            # 检查用户状态
            user = self.users.get(session.user_id)
            if not user or user.status != UserStatus.ACTIVE:
                session.status = SessionStatus.INVALID
                return None
            
            return session.user_id
            
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return None
    
    async def logout_user(self, session_id: str) -> bool:
        """用户登出"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.TERMINATED
            
            # 记录活动
            await self._log_activity(
                session.user_id, "logout", "用户登出",
                session_id=session_id, ip_address=session.ip_address
            )
            
            logger.info(f"用户已登出: {session.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return False
    
    async def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """设置多因素认证"""
        try:
            user = self.users.get(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 生成MFA密钥
            secret_key = pyotp.random_base32()
            
            # 生成备份码
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            
            # 创建MFA配置
            mfa_config = MFAConfig(
                user_id=user_id,
                secret_key=secret_key,
                backup_codes=backup_codes,
                recovery_email=user.email
            )
            
            self.mfa_configs[user_id] = mfa_config
            
            # 生成QR码URL
            totp = pyotp.TOTP(secret_key)
            qr_url = totp.provisioning_uri(
                name=user.email,
                issuer_name="PowerAutomation 4.1"
            )
            
            # 记录活动
            await self._log_activity(user_id, "mfa_setup", "多因素认证设置")
            
            return {
                "secret_key": secret_key,
                "qr_url": qr_url,
                "backup_codes": backup_codes
            }
            
        except Exception as e:
            logger.error(f"设置MFA失败: {e}")
            raise
    
    async def verify_mfa(self, user_id: str, token: str) -> bool:
        """验证MFA令牌"""
        try:
            mfa_config = self.mfa_configs.get(user_id)
            if not mfa_config or not mfa_config.enabled:
                return False
            
            # 验证TOTP令牌
            totp = pyotp.TOTP(mfa_config.secret_key)
            if totp.verify(token):
                mfa_config.last_used = datetime.now()
                await self._log_activity(user_id, "mfa_verified", "MFA验证成功")
                return True
            
            # 验证备份码
            if token.upper() in mfa_config.backup_codes:
                mfa_config.backup_codes.remove(token.upper())
                mfa_config.last_used = datetime.now()
                await self._log_activity(user_id, "mfa_backup_used", "使用MFA备份码")
                return True
            
            await self._log_activity(user_id, "mfa_failed", "MFA验证失败")
            return False
            
        except Exception as e:
            logger.error(f"验证MFA失败: {e}")
            return False
    
    async def update_user_profile(self, user_id: str, **kwargs) -> bool:
        """更新用户信息"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            # 更新允许的字段
            allowed_fields = ["full_name", "email", "phone", "department", "job_title", "manager_id"]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == "email" and value != user.email:
                        # 验证新邮箱
                        if not await self._validate_email(value):
                            raise ValueError("邮箱不符合要求或已存在")
                        
                        # 更新邮箱索引
                        del self.email_index[user.email]
                        self.email_index[value] = user_id
                        user.email_verified = False
                    
                    setattr(user, field, value)
            
            user.updated_at = datetime.now()
            
            # 记录活动
            await self._log_activity(user_id, "profile_updated", "用户信息已更新")
            
            return True
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            # 验证旧密码
            if not await self._verify_password(old_password, user.password_hash):
                await self._log_activity(user_id, "password_change_failed", "旧密码验证失败")
                return False
            
            # 验证新密码
            if not await self._validate_password(new_password):
                raise ValueError("新密码不符合安全要求")
            
            # 更新密码
            user.password_hash = await self._hash_password(new_password)
            user.updated_at = datetime.now()
            
            # 记录活动
            await self._log_activity(user_id, "password_changed", "密码已修改")
            
            # 终止其他会话
            await self._terminate_other_sessions(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            return False
    
    async def _update_user_profile(self, user_id: str):
        """更新用户画像"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return
            
            # 获取用户最近活动
            recent_activities = [
                activity for activity in self.activities[-1000:]  # 最近1000条活动
                if activity.user_id == user_id and 
                   activity.timestamp >= datetime.now() - timedelta(days=30)
            ]
            
            # 计算活动分数
            profile.activity_score = len(recent_activities) / 30.0  # 每天平均活动数
            
            # 分析使用模式
            activity_types = defaultdict(int)
            for activity in recent_activities:
                activity_types[activity.activity_type] += 1
            
            profile.usage_patterns = {
                "activity_distribution": dict(activity_types),
                "peak_hours": await self._calculate_peak_hours(recent_activities),
                "most_used_resources": await self._get_most_used_resources(recent_activities)
            }
            
            profile.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"更新用户画像失败: {e}")
    
    async def _calculate_peak_hours(self, activities: List[UserActivity]) -> List[int]:
        """计算用户活跃时段"""
        hour_counts = defaultdict(int)
        
        for activity in activities:
            hour = activity.timestamp.hour
            hour_counts[hour] += 1
        
        # 返回活动最多的3个小时
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    async def _get_most_used_resources(self, activities: List[UserActivity]) -> List[str]:
        """获取最常用的资源"""
        resource_counts = defaultdict(int)
        
        for activity in activities:
            if activity.resource_id:
                resource_counts[activity.resource_id] += 1
        
        # 返回使用最多的5个资源
        sorted_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)
        return [resource for resource, count in sorted_resources[:5]]
    
    async def _terminate_other_sessions(self, user_id: str, exclude_session_id: Optional[str] = None):
        """终止用户的其他会话"""
        for session_id, session in self.sessions.items():
            if session.user_id == user_id and session_id != exclude_session_id:
                session.status = SessionStatus.TERMINATED
    
    async def _log_activity(self, user_id: str, activity_type: str, description: str,
                          session_id: Optional[str] = None, ip_address: Optional[str] = None,
                          resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """记录用户活动"""
        activity = UserActivity(
            activity_id=str(uuid.uuid4()),
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            session_id=session_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {}
        )
        
        self.activities.append(activity)
        
        # 保持活动日志在合理范围内
        if len(self.activities) > 10000:
            self.activities = self.activities[-5000:]
    
    async def _log_failed_login(self, username: str, reason: str, ip_address: Optional[str] = None):
        """记录失败登录"""
        self.user_stats["failed_logins"] += 1
        
        # 这里可以添加更多的安全监控逻辑
        logger.warning(f"登录失败: {username} - {reason} (IP: {ip_address})")
    
    async def _validate_username(self, username: str) -> bool:
        """验证用户名"""
        if len(username) < 3 or len(username) > 50:
            return False
        
        if username in self.username_index:
            return False
        
        # 可以添加更多验证规则
        return True
    
    async def _validate_email(self, email: str) -> bool:
        """验证邮箱"""
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        if email in self.email_index:
            return False
        
        # 检查允许的域名
        if self.security_config["allowed_domains"]:
            domain = email.split("@")[1]
            if domain not in self.security_config["allowed_domains"]:
                return False
        
        return True
    
    async def _validate_password(self, password: str) -> bool:
        """验证密码强度"""
        config = self.security_config
        
        if len(password) < config["password_min_length"]:
            return False
        
        if config["password_require_uppercase"] and not any(c.isupper() for c in password):
            return False
        
        if config["password_require_lowercase"] and not any(c.islower() for c in password):
            return False
        
        if config["password_require_numbers"] and not any(c.isdigit() for c in password):
            return False
        
        if config["password_require_symbols"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        return True
    
    async def _hash_password(self, password: str) -> str:
        """密码哈希"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    async def _update_user_statistics(self):
        """更新用户统计"""
        current_time = datetime.now()
        
        self.user_stats["total_users"] = len(self.users)
        self.user_stats["active_users"] = len([
            user for user in self.users.values() 
            if user.status == UserStatus.ACTIVE
        ])
        
        self.user_stats["total_sessions"] = len(self.sessions)
        self.user_stats["active_sessions"] = len([
            session for session in self.sessions.values()
            if session.status == SessionStatus.ACTIVE and session.expires_at > current_time
        ])
        
        self.user_stats["total_activities"] = len(self.activities)
    
    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """获取用户仪表板数据"""
        try:
            user = self.users.get(user_id)
            if not user:
                return {}
            
            profile = self.user_profiles.get(user_id, UserProfile(user_id=user_id))
            
            # 获取用户会话
            user_sessions = [
                session for session in self.sessions.values()
                if session.user_id == user_id and session.status == SessionStatus.ACTIVE
            ]
            
            # 获取最近活动
            recent_activities = [
                activity for activity in self.activities[-100:]
                if activity.user_id == user_id
            ]
            
            return {
                "user_info": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "status": user.status.value,
                    "department": user.department,
                    "job_title": user.job_title,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "created_at": user.created_at.isoformat()
                },
                "profile": {
                    "activity_score": profile.activity_score,
                    "collaboration_score": profile.collaboration_score,
                    "productivity_score": profile.productivity_score,
                    "skills": profile.skills,
                    "interests": profile.interests,
                    "usage_patterns": profile.usage_patterns
                },
                "sessions": [
                    {
                        "session_id": session.session_id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "ip_address": session.ip_address,
                        "user_agent": session.user_agent
                    }
                    for session in user_sessions
                ],
                "recent_activities": [
                    {
                        "activity_type": activity.activity_type,
                        "description": activity.description,
                        "timestamp": activity.timestamp.isoformat(),
                        "resource_type": activity.resource_type,
                        "resource_id": activity.resource_id
                    }
                    for activity in recent_activities[-10:]
                ],
                "security": {
                    "mfa_enabled": user_id in self.mfa_configs and self.mfa_configs[user_id].enabled,
                    "email_verified": user.email_verified,
                    "phone_verified": user.phone_verified,
                    "failed_login_attempts": user.failed_login_attempts,
                    "locked_until": user.locked_until.isoformat() if user.locked_until else None
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户仪表板失败: {e}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            current_time = datetime.now()
            
            # 用户状态分布
            status_distribution = defaultdict(int)
            for user in self.users.values():
                status_distribution[user.status.value] += 1
            
            # 部门分布
            department_distribution = defaultdict(int)
            for user in self.users.values():
                dept = user.department or "未分配"
                department_distribution[dept] += 1
            
            # 最近活动统计
            recent_activities = [
                activity for activity in self.activities
                if activity.timestamp >= current_time - timedelta(days=7)
            ]
            
            activity_by_day = defaultdict(int)
            for activity in recent_activities:
                day = activity.timestamp.date().isoformat()
                activity_by_day[day] += 1
            
            return {
                "overview": self.user_stats,
                "user_status_distribution": dict(status_distribution),
                "department_distribution": dict(department_distribution),
                "activity_trends": dict(activity_by_day),
                "security_metrics": {
                    "mfa_enabled_users": len([
                        config for config in self.mfa_configs.values() 
                        if config.enabled
                    ]),
                    "locked_accounts": len([
                        user for user in self.users.values()
                        if user.locked_until and user.locked_until > current_time
                    ]),
                    "unverified_emails": len([
                        user for user in self.users.values()
                        if not user.email_verified
                    ])
                },
                "session_metrics": {
                    "average_session_duration": await self._calculate_average_session_duration(),
                    "concurrent_sessions": len([
                        session for session in self.sessions.values()
                        if session.status == SessionStatus.ACTIVE
                    ])
                }
            }
            
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}
    
    async def _calculate_average_session_duration(self) -> float:
        """计算平均会话时长"""
        terminated_sessions = [
            session for session in self.sessions.values()
            if session.status == SessionStatus.TERMINATED
        ]
        
        if not terminated_sessions:
            return 0.0
        
        total_duration = sum(
            (session.last_activity - session.created_at).total_seconds()
            for session in terminated_sessions
        )
        
        return total_duration / len(terminated_sessions)

# 示例使用
async def main():
    """示例主函数"""
    user_manager = EnterpriseUserManager()
    
    # 创建用户
    user_id = await user_manager.create_user(
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        password="SecurePass123!",
        department="Engineering",
        job_title="Senior Developer"
    )
    
    # 用户认证
    session_id = await user_manager.authenticate_user("john_doe", "SecurePass123!")
    print(f"认证成功，会话ID: {session_id}")
    
    # 设置MFA
    mfa_setup = await user_manager.setup_mfa(user_id)
    print(f"MFA设置: {mfa_setup['qr_url']}")
    
    # 获取用户仪表板
    dashboard = await user_manager.get_user_dashboard(user_id)
    print(f"用户仪表板: {json.dumps(dashboard, indent=2, ensure_ascii=False)}")
    
    # 获取系统统计
    stats = await user_manager.get_system_statistics()
    print(f"系统统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())

