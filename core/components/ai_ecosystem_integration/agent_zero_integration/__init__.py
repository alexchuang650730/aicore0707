"""
Agent Zero有机智能体框架集成模块

提供与Agent Zero有机智能体框架的深度集成功能，包括：
- 有机智能体管理
- 自适应学习
- 智能决策
- 协作网络
"""

from .agent_zero_deep_integration import AgentZeroDeepIntegration
from .organic_agent_manager import OrganicAgentManager
from .adaptive_learning_engine import AdaptiveLearningEngine
from .intelligent_decision_engine import IntelligentDecisionEngine
from .collaboration_network import CollaborationNetwork

__all__ = [
    'AgentZeroDeepIntegration',
    'OrganicAgentManager',
    'AdaptiveLearningEngine', 
    'IntelligentDecisionEngine',
    'CollaborationNetwork'
]

__version__ = "1.0.0"

