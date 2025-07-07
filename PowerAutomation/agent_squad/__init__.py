"""
PowerAutomation 4.0 Agent Squad
智能体协同系统 - 多智能体协作框架
"""

from .coordination.agent_coordinator import AgentCoordinator
from .coordination.task_distributor import TaskDistributor
from .coordination.collaboration_engine import CollaborationEngine
from .communication.agent_messenger import AgentMessenger
from .shared.agent_base import AgentBase
from .shared.agent_registry import AgentRegistry

# 导入所有智能体
from .agents.architect_agent.architect_agent import ArchitectAgent
from .agents.developer_agent.developer_agent import DeveloperAgent
from .agents.test_agent.test_agent import TestAgent
from .agents.deploy_agent.deploy_agent import DeployAgent
from .agents.security_agent.security_agent import SecurityAgent
from .agents.monitor_agent.monitor_agent import MonitorAgent

__version__ = "4.0.0"
__all__ = [
    # 协调组件
    "AgentCoordinator",
    "TaskDistributor", 
    "CollaborationEngine",
    "AgentMessenger",
    "AgentBase",
    "AgentRegistry",
    
    # 专业智能体
    "ArchitectAgent",
    "DeveloperAgent",
    "TestAgent", 
    "DeployAgent",
    "SecurityAgent",
    "MonitorAgent"
]

