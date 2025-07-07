"""
PowerAutomation 4.0 Agent Registry
智能体注册表
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: str
    last_heartbeat: datetime
    metadata: Dict[str, Any]

class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, AgentInfo] = {}
        
    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """注册智能体"""
        try:
            self.agents[agent_info.agent_id] = agent_info
            self.logger.info(f"智能体已注册: {agent_info.agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"智能体注册失败: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id in self.agents:
                del self.agents[agent_id]
                self.logger.info(f"智能体已注销: {agent_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"智能体注销失败: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取智能体信息"""
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[AgentInfo]:
        """列出所有智能体"""
        return list(self.agents.values())

