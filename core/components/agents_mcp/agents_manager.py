"""
Agents Manager - 智能体管理器
负责智能体的创建、管理和协调
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class AgentsManager:
    """智能体管理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session_id = f"agents_mgr_{int(datetime.now().timestamp())}"
        self.logger = self._setup_logger()
        self.agents = {}
        self.agent_groups = {}
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(f"AgentsManager_{self.session_id}")
        logger.setLevel(logging.INFO)
        return logger
    
    async def create_agent(self, agent_config: Dict) -> str:
        """创建智能体"""
        try:
            agent_id = agent_config.get('id', f"agent_{len(self.agents)}")
            
            agent = {
                'id': agent_id,
                'name': agent_config.get('name', f'Agent_{agent_id}'),
                'type': agent_config.get('type', 'general'),
                'capabilities': agent_config.get('capabilities', []),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'metadata': agent_config.get('metadata', {})
            }
            
            self.agents[agent_id] = agent
            self.logger.info(f"智能体已创建: {agent_id}")
            
            return agent_id
            
        except Exception as e:
            self.logger.error(f"创建智能体失败: {e}")
            raise
    
    async def create_agent_group(self, group_config: Dict) -> str:
        """创建智能体组"""
        try:
            group_id = group_config.get('id', f"group_{len(self.agent_groups)}")
            
            group = {
                'id': group_id,
                'name': group_config.get('name', f'Group_{group_id}'),
                'agents': group_config.get('agents', []),
                'coordination_strategy': group_config.get('strategy', 'round_robin'),
                'created_at': datetime.now().isoformat()
            }
            
            self.agent_groups[group_id] = group
            self.logger.info(f"智能体组已创建: {group_id}")
            
            return group_id
            
        except Exception as e:
            self.logger.error(f"创建智能体组失败: {e}")
            raise
    
    async def assign_task(self, task: Dict) -> Dict:
        """分配任务给智能体"""
        try:
            task_id = f"task_{int(datetime.now().timestamp())}"
            
            # 简单的任务分配逻辑
            available_agents = [a for a in self.agents.values() if a['status'] == 'active']
            
            if not available_agents:
                raise ValueError("没有可用的智能体")
            
            # 选择第一个可用智能体
            selected_agent = available_agents[0]
            
            result = {
                'task_id': task_id,
                'assigned_agent': selected_agent['id'],
                'task': task,
                'status': 'assigned',
                'assigned_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"任务已分配: {task_id} -> {selected_agent['id']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"任务分配失败: {e}")
            raise
    
    async def get_agent_status(self, agent_id: str) -> Dict:
        """获取智能体状态"""
        if agent_id not in self.agents:
            raise ValueError(f"智能体不存在: {agent_id}")
        
        return self.agents[agent_id]
    
    async def list_agents(self) -> List[Dict]:
        """列出所有智能体"""
        return list(self.agents.values())

# CLI接口
async def main():
    """智能体管理器命令行接口"""
    manager = AgentsManager()
    
    try:
        # 创建智能体
        agent_config = {
            'name': 'TestAgent',
            'type': 'assistant',
            'capabilities': ['reasoning', 'planning']
        }
        
        agent_id = await manager.create_agent(agent_config)
        print(f"✅ 智能体已创建: {agent_id}")
        
        # 分配任务
        task = {
            'description': '分析数据',
            'priority': 'high'
        }
        
        result = await manager.assign_task(task)
        print(f"✅ 任务已分配: {result}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())

