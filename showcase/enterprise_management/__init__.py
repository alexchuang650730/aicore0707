"""
PowerAutomation 4.1 企业级管理模块
Enterprise Management Components

包含企业级功能组件:
- 权限管理系统 (Permission Management)
- 用户管理系统 (User Management)
- 团队协作系统 (Team Collaboration)
- 数据分析报告 (Analytics & Reporting)
- 集成API管理 (Integration & API Management)
- 审计日志系统 (Audit Logging)
"""

from .permission_management import (
    EnterprisePermissionManager,
    Role,
    Permission,
    UserRole,
    ResourceAccess
)

from .user_management import (
    EnterpriseUserManager,
    User,
    UserProfile,
    UserSession,
    UserActivity
)

from .team_collaboration import (
    TeamCollaborationManager,
    Team,
    Project,
    CollaborationSession,
    RealTimeSync
)

from .analytics_reporting import (
    AnalyticsReportingEngine,
    Report,
    Dashboard,
    Metric,
    KPI
)

from .integration_api_management import (
    IntegrationAPIManager,
    APIEndpoint,
    Integration,
    APIKey,
    RateLimiting
)

__all__ = [
    # Permission Management
    "EnterprisePermissionManager",
    "Role",
    "Permission", 
    "UserRole",
    "ResourceAccess",
    
    # User Management
    "EnterpriseUserManager",
    "User",
    "UserProfile",
    "UserSession",
    "UserActivity",
    
    # Team Collaboration
    "TeamCollaborationManager",
    "Team",
    "Project",
    "CollaborationSession",
    "RealTimeSync",
    
    # Analytics & Reporting
    "AnalyticsReportingEngine",
    "Report",
    "Dashboard",
    "Metric",
    "KPI",
    
    # Integration & API Management
    "IntegrationAPIManager",
    "APIEndpoint",
    "Integration",
    "APIKey",
    "RateLimiting"
]

__version__ = "4.1.0"
__author__ = "PowerAutomation Team"
__description__ = "Enterprise-grade management components for PowerAutomation 4.1"

