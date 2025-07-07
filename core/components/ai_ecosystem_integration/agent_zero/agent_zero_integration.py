#!/usr/bin/env python3
"""
PowerAutomation 4.1 Agent Zero集成组件

Agent Zero是一个有机智能体框架，具有自学习能力和动态适应性。
本模块实现了Agent Zero与PowerAutomation + ClaudEditor的深度集成。

Agent Zero核心特性：
1. 有机智能体架构 - 自然演化的智能体系统
2. 自学习能力 - 从交互中持续学习和改进
3. 动态适应性 - 根据环境变化自动调整行为
4. 多智能体协作 - 支持智能体间的协作和通信
5. 知识图谱构建 - 自动构建和维护知识网络

作者: PowerAutomation Team
版本: 4.1
日期: 2025-01-07
"""

import asyncio
import json
import time
import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path
import networkx as nx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    """智能体状态"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    LEARNING = "learning"
    ADAPTING = "adapting"
    COLLABORATING = "collaborating"
    DORMANT = "dormant"
    ERROR = "error"

class LearningMode(Enum):
    """学习模式"""
    SUPERVISED = "supervised"        # 监督学习
    UNSUPERVISED = "unsupervised"   # 无监督学习
    REINFORCEMENT = "reinforcement" # 强化学习
    IMITATION = "imitation"         # 模仿学习
    SELF_SUPERVISED = "self_supervised" # 自监督学习

class AdaptationStrategy(Enum):
    """适应策略"""
    CONSERVATIVE = "conservative"    # 保守策略
    AGGRESSIVE = "aggressive"       # 激进策略
    BALANCED = "balanced"           # 平衡策略
    EXPLORATORY = "exploratory"     # 探索策略
    EXPLOITATIVE = "exploitative"   # 利用策略

@dataclass
class AgentCapability:
    """智能体能力"""
    capability_id: str
    name: str
    description: str
    proficiency_level: float  # 0.0 - 1.0
    learning_rate: float
    adaptation_speed: float
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_proficiency(self, success: bool, learning_rate: float = None):
        """更新能力熟练度"""
        if learning_rate is None:
            learning_rate = self.learning_rate
        
        self.usage_count += 1
        
        # 更新成功率
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            self.success_rate = ((self.success_rate * (self.usage_count - 1)) + 
                               (1.0 if success else 0.0)) / self.usage_count
        
        # 更新熟练度
        if success:
            improvement = learning_rate * (1.0 - self.proficiency_level)
            self.proficiency_level = min(1.0, self.proficiency_level + improvement)
        else:
            degradation = learning_rate * 0.1  # 失败时轻微降低
            self.proficiency_level = max(0.0, self.proficiency_level - degradation)
        
        self.last_used = datetime.now()

@dataclass
class LearningExperience:
    """学习经验"""
    experience_id: str
    agent_id: str
    context: Dict[str, Any]
    action_taken: str
    outcome: Dict[str, Any]
    success: bool
    reward: float
    learning_mode: LearningMode
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeNode:
    """知识节点"""
    node_id: str
    content: Dict[str, Any]
    node_type: str  # concept, fact, rule, pattern
    confidence: float
    connections: List[str] = field(default_factory=list)
    creation_time: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

class OrganicAgent:
    """有机智能体"""
    
    def __init__(self, agent_id: str, agent_type: str = "general", 
                 initial_capabilities: List[str] = None):
        """初始化有机智能体"""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState.INITIALIZING
        self.learning_mode = LearningMode.SELF_SUPERVISED
        self.adaptation_strategy = AdaptationStrategy.BALANCED
        
        # 智能体能力
        self.capabilities: Dict[str, AgentCapability] = {}
        self._initialize_capabilities(initial_capabilities or [])
        
        # 学习系统
        self.experiences: List[LearningExperience] = []
        self.knowledge_graph = nx.DiGraph()
        self.learning_rate = 0.1
        self.adaptation_threshold = 0.7
        
        # 协作系统
        self.collaborators: Dict[str, 'OrganicAgent'] = {}
        self.communication_history: List[Dict[str, Any]] = []
        
        # 性能指标
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "learning_episodes": 0,
            "adaptation_events": 0,
            "collaboration_sessions": 0,
            "knowledge_nodes": 0
        }
        
        # 自我评估
        self.self_assessment = {
            "overall_competence": 0.5,
            "learning_efficiency": 0.5,
            "adaptation_speed": 0.5,
            "collaboration_ability": 0.5
        }
        
        self.state = AgentState.ACTIVE
        logger.info(f"有机智能体 {agent_id} 初始化完成")
    
    def _initialize_capabilities(self, capability_names: List[str]):
        """初始化智能体能力"""
        default_capabilities = [
            "problem_solving", "pattern_recognition", "decision_making",
            "communication", "learning", "adaptation"
        ]
        
        all_capabilities = list(set(default_capabilities + capability_names))
        
        for cap_name in all_capabilities:
            capability = AgentCapability(
                capability_id=str(uuid.uuid4()),
                name=cap_name,
                description=f"智能体的{cap_name}能力",
                proficiency_level=random.uniform(0.3, 0.7),  # 随机初始熟练度
                learning_rate=random.uniform(0.05, 0.15),
                adaptation_speed=random.uniform(0.1, 0.3)
            )
            self.capabilities[cap_name] = capability
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.state = AgentState.ACTIVE
        start_time = time.time()
        
        # 分析任务需求
        required_capabilities = self._analyze_task_requirements(task)
        
        # 评估自身能力
        capability_assessment = self._assess_capabilities(required_capabilities)
        
        # 决定执行策略
        execution_strategy = self._determine_execution_strategy(
            task, capability_assessment
        )
        
        # 执行任务
        try:
            result = await self._execute_with_strategy(task, execution_strategy)
            success = result.get("success", False)
            
            # 记录学习经验
            await self._record_experience(task, result, success)
            
            # 更新能力
            self._update_capabilities(required_capabilities, success)
            
            # 更新性能指标
            self.performance_metrics["total_tasks"] += 1
            if success:
                self.performance_metrics["successful_tasks"] += 1
            
            # 触发自适应
            if self._should_adapt():
                await self._trigger_adaptation()
            
            execution_time = time.time() - start_time
            
            return {
                "success": success,
                "result": result,
                "execution_time": execution_time,
                "capabilities_used": required_capabilities,
                "learning_occurred": True,
                "agent_state": self.state.value
            }
            
        except Exception as e:
            logger.error(f"智能体 {self.agent_id} 执行任务失败: {e}")
            await self._record_experience(task, {"error": str(e)}, False)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "agent_state": AgentState.ERROR.value
            }
    
    def _analyze_task_requirements(self, task: Dict[str, Any]) -> List[str]:
        """分析任务需求"""
        task_type = task.get("type", "general")
        task_complexity = task.get("complexity", "medium")
        
        # 基于任务类型映射所需能力
        capability_mapping = {
            "code_analysis": ["problem_solving", "pattern_recognition"],
            "code_generation": ["problem_solving", "decision_making"],
            "debugging": ["problem_solving", "pattern_recognition", "decision_making"],
            "optimization": ["problem_solving", "pattern_recognition"],
            "collaboration": ["communication", "decision_making"],
            "learning": ["learning", "adaptation"],
            "general": ["problem_solving", "decision_making"]
        }
        
        required_caps = capability_mapping.get(task_type, ["problem_solving"])
        
        # 根据复杂度调整
        if task_complexity == "high":
            required_caps.extend(["adaptation", "learning"])
        
        return list(set(required_caps))
    
    def _assess_capabilities(self, required_capabilities: List[str]) -> Dict[str, float]:
        """评估能力匹配度"""
        assessment = {}
        
        for cap_name in required_capabilities:
            if cap_name in self.capabilities:
                capability = self.capabilities[cap_name]
                # 综合考虑熟练度和成功率
                score = (capability.proficiency_level * 0.7 + 
                        capability.success_rate * 0.3)
                assessment[cap_name] = score
            else:
                # 缺失能力，需要学习
                assessment[cap_name] = 0.0
        
        return assessment
    
    def _determine_execution_strategy(self, task: Dict[str, Any], 
                                    assessment: Dict[str, float]) -> Dict[str, Any]:
        """确定执行策略"""
        avg_capability = sum(assessment.values()) / len(assessment) if assessment else 0.0
        
        strategy = {
            "approach": "direct",
            "confidence": avg_capability,
            "need_collaboration": False,
            "need_learning": False
        }
        
        # 如果能力不足，考虑协作或学习
        if avg_capability < 0.5:
            strategy["need_collaboration"] = True
            strategy["approach"] = "collaborative"
        
        if avg_capability < 0.3:
            strategy["need_learning"] = True
            strategy["approach"] = "learning_based"
        
        # 根据适应策略调整
        if self.adaptation_strategy == AdaptationStrategy.EXPLORATORY:
            strategy["exploration_factor"] = 0.3
        elif self.adaptation_strategy == AdaptationStrategy.CONSERVATIVE:
            strategy["risk_tolerance"] = 0.2
        
        return strategy
    
    async def _execute_with_strategy(self, task: Dict[str, Any], 
                                   strategy: Dict[str, Any]) -> Dict[str, Any]:
        """根据策略执行任务"""
        approach = strategy["approach"]
        
        if approach == "collaborative" and strategy.get("need_collaboration"):
            return await self._execute_collaboratively(task)
        elif approach == "learning_based" and strategy.get("need_learning"):
            return await self._execute_with_learning(task)
        else:
            return await self._execute_directly(task)
    
    async def _execute_directly(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行任务"""
        # 模拟任务执行
        task_complexity = task.get("complexity", "medium")
        
        # 基于能力计算成功概率
        required_caps = self._analyze_task_requirements(task)
        capability_scores = [
            self.capabilities[cap].proficiency_level 
            for cap in required_caps if cap in self.capabilities
        ]
        
        avg_capability = sum(capability_scores) / len(capability_scores) if capability_scores else 0.5
        
        # 复杂度影响成功率
        complexity_factor = {"low": 1.2, "medium": 1.0, "high": 0.8}.get(task_complexity, 1.0)
        success_probability = min(1.0, avg_capability * complexity_factor)
        
        success = random.random() < success_probability
        
        # 模拟执行时间
        execution_time = random.uniform(1.0, 5.0)
        await asyncio.sleep(0.1)  # 模拟异步执行
        
        result = {
            "success": success,
            "output": f"任务执行{'成功' if success else '失败'}",
            "execution_method": "direct",
            "capability_utilization": avg_capability,
            "execution_time": execution_time
        }
        
        return result
    
    async def _execute_collaboratively(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """协作执行任务"""
        # 寻找合适的协作者
        collaborator = self._find_best_collaborator(task)
        
        if collaborator:
            # 与协作者共同执行
            self.performance_metrics["collaboration_sessions"] += 1
            
            # 模拟协作执行
            my_contribution = await self._execute_directly(task)
            collaborator_contribution = await collaborator._execute_directly(task)
            
            # 合并结果
            combined_success_rate = (
                (my_contribution.get("capability_utilization", 0.5) + 
                 collaborator_contribution.get("capability_utilization", 0.5)) / 2
            )
            
            success = random.random() < min(1.0, combined_success_rate * 1.3)  # 协作加成
            
            result = {
                "success": success,
                "output": f"协作任务执行{'成功' if success else '失败'}",
                "execution_method": "collaborative",
                "collaborator": collaborator.agent_id,
                "my_contribution": my_contribution,
                "collaborator_contribution": collaborator_contribution,
                "collaboration_bonus": 0.3
            }
            
            # 记录协作历史
            self.communication_history.append({
                "type": "collaboration",
                "partner": collaborator.agent_id,
                "task": task,
                "result": result,
                "timestamp": datetime.now()
            })
            
            return result
        else:
            # 没有合适的协作者，降级为直接执行
            return await self._execute_directly(task)
    
    async def _execute_with_learning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """带学习的执行任务"""
        self.state = AgentState.LEARNING
        
        # 先尝试直接执行
        initial_result = await self._execute_directly(task)
        
        # 如果失败，进行学习
        if not initial_result.get("success", False):
            learning_result = await self._learn_from_failure(task, initial_result)
            
            # 再次尝试执行
            if learning_result.get("learning_success", False):
                retry_result = await self._execute_directly(task)
                
                result = {
                    "success": retry_result.get("success", False),
                    "output": f"学习后任务执行{'成功' if retry_result.get('success') else '失败'}",
                    "execution_method": "learning_based",
                    "initial_attempt": initial_result,
                    "learning_phase": learning_result,
                    "retry_attempt": retry_result,
                    "learning_improvement": True
                }
                
                self.performance_metrics["learning_episodes"] += 1
                return result
        
        return initial_result
    
    def _find_best_collaborator(self, task: Dict[str, Any]) -> Optional['OrganicAgent']:
        """寻找最佳协作者"""
        if not self.collaborators:
            return None
        
        required_capabilities = self._analyze_task_requirements(task)
        best_collaborator = None
        best_score = 0.0
        
        for collaborator in self.collaborators.values():
            # 评估协作者的能力匹配度
            score = 0.0
            for cap_name in required_capabilities:
                if cap_name in collaborator.capabilities:
                    score += collaborator.capabilities[cap_name].proficiency_level
            
            avg_score = score / len(required_capabilities) if required_capabilities else 0.0
            
            if avg_score > best_score:
                best_score = avg_score
                best_collaborator = collaborator
        
        return best_collaborator if best_score > 0.6 else None
    
    async def _learn_from_failure(self, task: Dict[str, Any], 
                                failure_result: Dict[str, Any]) -> Dict[str, Any]:
        """从失败中学习"""
        required_capabilities = self._analyze_task_requirements(task)
        
        # 分析失败原因
        failure_analysis = self._analyze_failure(task, failure_result, required_capabilities)
        
        # 更新学习率
        learning_improvements = {}
        for cap_name in required_capabilities:
            if cap_name in self.capabilities:
                capability = self.capabilities[cap_name]
                # 增加学习率以快速改进
                old_proficiency = capability.proficiency_level
                capability.learning_rate *= 1.2  # 增加学习率
                capability.proficiency_level = min(1.0, capability.proficiency_level + 0.1)
                
                learning_improvements[cap_name] = {
                    "old_proficiency": old_proficiency,
                    "new_proficiency": capability.proficiency_level,
                    "learning_rate_boost": 1.2
                }
            else:
                # 创建新能力
                new_capability = AgentCapability(
                    capability_id=str(uuid.uuid4()),
                    name=cap_name,
                    description=f"从失败中学习的{cap_name}能力",
                    proficiency_level=0.2,  # 从低水平开始
                    learning_rate=0.2,     # 高学习率
                    adaptation_speed=0.3
                )
                self.capabilities[cap_name] = new_capability
                
                learning_improvements[cap_name] = {
                    "new_capability": True,
                    "initial_proficiency": 0.2
                }
        
        # 更新知识图谱
        await self._update_knowledge_graph(task, failure_result, failure_analysis)
        
        return {
            "learning_success": True,
            "failure_analysis": failure_analysis,
            "capability_improvements": learning_improvements,
            "knowledge_updated": True
        }
    
    def _analyze_failure(self, task: Dict[str, Any], failure_result: Dict[str, Any], 
                        required_capabilities: List[str]) -> Dict[str, Any]:
        """分析失败原因"""
        analysis = {
            "primary_cause": "capability_insufficient",
            "capability_gaps": [],
            "complexity_mismatch": False,
            "resource_constraints": False
        }
        
        # 分析能力缺口
        for cap_name in required_capabilities:
            if cap_name not in self.capabilities:
                analysis["capability_gaps"].append({
                    "capability": cap_name,
                    "status": "missing"
                })
            elif self.capabilities[cap_name].proficiency_level < 0.5:
                analysis["capability_gaps"].append({
                    "capability": cap_name,
                    "status": "insufficient",
                    "current_level": self.capabilities[cap_name].proficiency_level
                })
        
        # 分析复杂度匹配
        task_complexity = task.get("complexity", "medium")
        if task_complexity == "high" and self.self_assessment["overall_competence"] < 0.7:
            analysis["complexity_mismatch"] = True
        
        return analysis
    
    async def _update_knowledge_graph(self, task: Dict[str, Any], 
                                    result: Dict[str, Any], 
                                    analysis: Dict[str, Any]):
        """更新知识图谱"""
        # 创建任务节点
        task_node = KnowledgeNode(
            node_id=f"task_{uuid.uuid4()}",
            content={
                "task_type": task.get("type", "general"),
                "complexity": task.get("complexity", "medium"),
                "requirements": task
            },
            node_type="task",
            confidence=0.8
        )
        
        # 创建结果节点
        result_node = KnowledgeNode(
            node_id=f"result_{uuid.uuid4()}",
            content={
                "success": result.get("success", False),
                "execution_method": result.get("execution_method", "direct"),
                "analysis": analysis
            },
            node_type="outcome",
            confidence=0.9
        )
        
        # 添加到知识图谱
        self.knowledge_graph.add_node(task_node.node_id, **asdict(task_node))
        self.knowledge_graph.add_node(result_node.node_id, **asdict(result_node))
        self.knowledge_graph.add_edge(task_node.node_id, result_node.node_id, 
                                    relation="produces")
        
        self.performance_metrics["knowledge_nodes"] += 2
    
    async def _record_experience(self, task: Dict[str, Any], 
                               result: Dict[str, Any], success: bool):
        """记录学习经验"""
        experience = LearningExperience(
            experience_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            context=task,
            action_taken=result.get("execution_method", "direct"),
            outcome=result,
            success=success,
            reward=1.0 if success else -0.5,
            learning_mode=self.learning_mode,
            timestamp=datetime.now()
        )
        
        self.experiences.append(experience)
        
        # 限制经验数量
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-800:]  # 保留最近800个经验
    
    def _update_capabilities(self, required_capabilities: List[str], success: bool):
        """更新能力"""
        for cap_name in required_capabilities:
            if cap_name in self.capabilities:
                self.capabilities[cap_name].update_proficiency(success)
    
    def _should_adapt(self) -> bool:
        """判断是否需要适应"""
        # 基于最近的成功率决定是否适应
        recent_experiences = self.experiences[-10:] if len(self.experiences) >= 10 else self.experiences
        
        if not recent_experiences:
            return False
        
        recent_success_rate = sum(1 for exp in recent_experiences if exp.success) / len(recent_experiences)
        
        return recent_success_rate < self.adaptation_threshold
    
    async def _trigger_adaptation(self):
        """触发适应"""
        self.state = AgentState.ADAPTING
        
        # 分析最近的表现
        performance_analysis = self._analyze_recent_performance()
        
        # 调整学习策略
        if performance_analysis["success_rate"] < 0.3:
            self.learning_mode = LearningMode.REINFORCEMENT
            self.adaptation_strategy = AdaptationStrategy.EXPLORATORY
        elif performance_analysis["success_rate"] < 0.6:
            self.learning_mode = LearningMode.SELF_SUPERVISED
            self.adaptation_strategy = AdaptationStrategy.BALANCED
        else:
            self.adaptation_strategy = AdaptationStrategy.EXPLOITATIVE
        
        # 调整能力参数
        for capability in self.capabilities.values():
            if capability.success_rate < 0.5:
                capability.learning_rate *= 1.1  # 增加学习率
            capability.adaptation_speed *= 1.05
        
        # 更新自我评估
        self._update_self_assessment()
        
        self.performance_metrics["adaptation_events"] += 1
        self.state = AgentState.ACTIVE
        
        logger.info(f"智能体 {self.agent_id} 完成适应调整")
    
    def _analyze_recent_performance(self) -> Dict[str, Any]:
        """分析最近表现"""
        recent_experiences = self.experiences[-20:] if len(self.experiences) >= 20 else self.experiences
        
        if not recent_experiences:
            return {"success_rate": 0.5, "trend": "stable"}
        
        success_rate = sum(1 for exp in recent_experiences if exp.success) / len(recent_experiences)
        
        # 分析趋势
        if len(recent_experiences) >= 10:
            first_half = recent_experiences[:len(recent_experiences)//2]
            second_half = recent_experiences[len(recent_experiences)//2:]
            
            first_half_rate = sum(1 for exp in first_half if exp.success) / len(first_half)
            second_half_rate = sum(1 for exp in second_half if exp.success) / len(second_half)
            
            if second_half_rate > first_half_rate + 0.1:
                trend = "improving"
            elif second_half_rate < first_half_rate - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "success_rate": success_rate,
            "trend": trend,
            "total_experiences": len(recent_experiences)
        }
    
    def _update_self_assessment(self):
        """更新自我评估"""
        # 计算整体能力
        if self.capabilities:
            avg_proficiency = sum(cap.proficiency_level for cap in self.capabilities.values()) / len(self.capabilities)
            self.self_assessment["overall_competence"] = avg_proficiency
        
        # 计算学习效率
        if self.experiences:
            recent_learning = [exp for exp in self.experiences[-50:] if exp.learning_mode != LearningMode.SUPERVISED]
            if recent_learning:
                learning_success_rate = sum(1 for exp in recent_learning if exp.success) / len(recent_learning)
                self.self_assessment["learning_efficiency"] = learning_success_rate
        
        # 计算适应速度
        adaptation_score = min(1.0, self.performance_metrics["adaptation_events"] / max(1, self.performance_metrics["total_tasks"]))
        self.self_assessment["adaptation_speed"] = adaptation_score
        
        # 计算协作能力
        if self.performance_metrics["collaboration_sessions"] > 0:
            collaboration_score = self.performance_metrics["collaboration_sessions"] / max(1, self.performance_metrics["total_tasks"])
            self.self_assessment["collaboration_ability"] = min(1.0, collaboration_score)
    
    async def add_collaborator(self, collaborator: 'OrganicAgent'):
        """添加协作者"""
        self.collaborators[collaborator.agent_id] = collaborator
        collaborator.collaborators[self.agent_id] = self
        
        logger.info(f"智能体 {self.agent_id} 与 {collaborator.agent_id} 建立协作关系")
    
    async def communicate(self, target_agent_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """与其他智能体通信"""
        if target_agent_id in self.collaborators:
            target_agent = self.collaborators[target_agent_id]
            
            # 记录通信
            communication_record = {
                "type": "message",
                "from": self.agent_id,
                "to": target_agent_id,
                "message": message,
                "timestamp": datetime.now()
            }
            
            self.communication_history.append(communication_record)
            target_agent.communication_history.append(communication_record)
            
            # 模拟响应
            response = await target_agent._process_communication(self.agent_id, message)
            
            return response
        else:
            return {"error": "目标智能体不在协作列表中"}
    
    async def _process_communication(self, sender_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的通信"""
        message_type = message.get("type", "general")
        
        if message_type == "capability_inquiry":
            # 返回能力信息
            return {
                "type": "capability_response",
                "capabilities": {
                    name: {
                        "proficiency": cap.proficiency_level,
                        "success_rate": cap.success_rate
                    }
                    for name, cap in self.capabilities.items()
                }
            }
        elif message_type == "collaboration_request":
            # 评估是否接受协作请求
            task = message.get("task", {})
            my_assessment = self._assess_capabilities(self._analyze_task_requirements(task))
            avg_capability = sum(my_assessment.values()) / len(my_assessment) if my_assessment else 0.0
            
            accept = avg_capability > 0.4  # 如果有一定能力就接受
            
            return {
                "type": "collaboration_response",
                "accept": accept,
                "capability_assessment": my_assessment
            }
        else:
            return {
                "type": "general_response",
                "message": f"收到来自 {sender_id} 的消息"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "learning_mode": self.learning_mode.value,
            "adaptation_strategy": self.adaptation_strategy.value,
            "capabilities": {
                name: {
                    "proficiency": cap.proficiency_level,
                    "success_rate": cap.success_rate,
                    "usage_count": cap.usage_count
                }
                for name, cap in self.capabilities.items()
            },
            "performance_metrics": self.performance_metrics,
            "self_assessment": self.self_assessment,
            "collaborators": list(self.collaborators.keys()),
            "knowledge_graph_size": self.knowledge_graph.number_of_nodes(),
            "experience_count": len(self.experiences)
        }

class AgentZeroIntegration:
    """Agent Zero与PowerAutomation集成"""
    
    def __init__(self):
        """初始化Agent Zero集成"""
        self.agents: Dict[str, OrganicAgent] = {}
        self.agent_registry = {}
        self.task_queue = asyncio.Queue()
        self.integration_stats = {
            "total_agents": 0,
            "active_agents": 0,
            "completed_tasks": 0,
            "collaboration_events": 0,
            "learning_events": 0,
            "adaptation_events": 0
        }
        
        # 创建默认智能体
        asyncio.create_task(self._initialize_default_agents())
        
        logger.info("Agent Zero集成初始化完成")
    
    async def _initialize_default_agents(self):
        """初始化默认智能体"""
        # 创建专业智能体
        agents_config = [
            {
                "agent_id": "code_analyst",
                "agent_type": "code_analysis",
                "capabilities": ["code_analysis", "pattern_recognition", "problem_solving"]
            },
            {
                "agent_id": "code_generator",
                "agent_type": "code_generation",
                "capabilities": ["code_generation", "problem_solving", "decision_making"]
            },
            {
                "agent_id": "debugger",
                "agent_type": "debugging",
                "capabilities": ["debugging", "problem_solving", "pattern_recognition"]
            },
            {
                "agent_id": "optimizer",
                "agent_type": "optimization",
                "capabilities": ["optimization", "performance_analysis", "problem_solving"]
            },
            {
                "agent_id": "collaborator",
                "agent_type": "collaboration",
                "capabilities": ["communication", "coordination", "decision_making"]
            }
        ]
        
        for config in agents_config:
            agent = OrganicAgent(
                agent_id=config["agent_id"],
                agent_type=config["agent_type"],
                initial_capabilities=config["capabilities"]
            )
            
            await self.register_agent(agent)
        
        # 建立协作关系
        await self._establish_collaborations()
    
    async def _establish_collaborations(self):
        """建立智能体间的协作关系"""
        agent_list = list(self.agents.values())
        
        # 每个智能体与其他智能体建立协作关系
        for i, agent1 in enumerate(agent_list):
            for j, agent2 in enumerate(agent_list):
                if i != j:
                    await agent1.add_collaborator(agent2)
    
    async def register_agent(self, agent: OrganicAgent):
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        self.agent_registry[agent.agent_id] = {
            "agent_type": agent.agent_type,
            "capabilities": list(agent.capabilities.keys()),
            "registration_time": datetime.now()
        }
        
        self.integration_stats["total_agents"] += 1
        self.integration_stats["active_agents"] += 1
        
        logger.info(f"智能体 {agent.agent_id} 注册成功")
    
    async def assign_task(self, task: Dict[str, Any], 
                         preferred_agent: str = None) -> Dict[str, Any]:
        """分配任务给智能体"""
        # 选择最适合的智能体
        if preferred_agent and preferred_agent in self.agents:
            selected_agent = self.agents[preferred_agent]
        else:
            selected_agent = await self._select_best_agent(task)
        
        if not selected_agent:
            return {
                "success": False,
                "error": "没有找到合适的智能体执行任务"
            }
        
        # 执行任务
        result = await selected_agent.execute_task(task)
        
        # 更新统计
        self.integration_stats["completed_tasks"] += 1
        if result.get("learning_occurred"):
            self.integration_stats["learning_events"] += 1
        
        # 记录协作事件
        if result.get("execution_method") == "collaborative":
            self.integration_stats["collaboration_events"] += 1
        
        return {
            "task_result": result,
            "assigned_agent": selected_agent.agent_id,
            "agent_status": selected_agent.get_agent_status()
        }
    
    async def _select_best_agent(self, task: Dict[str, Any]) -> Optional[OrganicAgent]:
        """选择最适合的智能体"""
        task_type = task.get("type", "general")
        required_capabilities = self._analyze_task_requirements(task)
        
        best_agent = None
        best_score = 0.0
        
        for agent in self.agents.values():
            if agent.state == AgentState.ERROR:
                continue
            
            # 计算匹配分数
            score = 0.0
            capability_count = 0
            
            for cap_name in required_capabilities:
                if cap_name in agent.capabilities:
                    capability = agent.capabilities[cap_name]
                    score += capability.proficiency_level * capability.success_rate
                    capability_count += 1
            
            # 平均分数
            if capability_count > 0:
                avg_score = score / capability_count
                
                # 考虑智能体类型匹配
                if agent.agent_type == task_type:
                    avg_score *= 1.2  # 类型匹配加成
                
                # 考虑当前状态
                if agent.state == AgentState.ACTIVE:
                    avg_score *= 1.1
                elif agent.state == AgentState.LEARNING:
                    avg_score *= 0.9
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_agent = agent
        
        return best_agent
    
    def _analyze_task_requirements(self, task: Dict[str, Any]) -> List[str]:
        """分析任务需求（复用OrganicAgent的方法）"""
        task_type = task.get("type", "general")
        
        capability_mapping = {
            "code_analysis": ["code_analysis", "pattern_recognition"],
            "code_generation": ["code_generation", "problem_solving"],
            "debugging": ["debugging", "problem_solving"],
            "optimization": ["optimization", "performance_analysis"],
            "collaboration": ["communication", "coordination"],
            "general": ["problem_solving", "decision_making"]
        }
        
        return capability_mapping.get(task_type, ["problem_solving"])
    
    async def trigger_collective_learning(self, learning_data: Dict[str, Any]):
        """触发集体学习"""
        learning_task = {
            "type": "learning",
            "data": learning_data,
            "complexity": "medium"
        }
        
        # 所有智能体参与学习
        learning_results = []
        for agent in self.agents.values():
            if agent.state != AgentState.ERROR:
                result = await agent.execute_task(learning_task)
                learning_results.append({
                    "agent_id": agent.agent_id,
                    "learning_result": result
                })
        
        self.integration_stats["learning_events"] += len(learning_results)
        
        return {
            "collective_learning_completed": True,
            "participating_agents": len(learning_results),
            "results": learning_results
        }
    
    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """获取生态系统状态"""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = agent.get_agent_status()
        
        # 计算生态系统指标
        total_capabilities = sum(len(agent.capabilities) for agent in self.agents.values())
        total_experiences = sum(len(agent.experiences) for agent in self.agents.values())
        total_knowledge_nodes = sum(agent.knowledge_graph.number_of_nodes() for agent in self.agents.values())
        
        avg_competence = sum(agent.self_assessment["overall_competence"] for agent in self.agents.values()) / len(self.agents) if self.agents else 0.0
        
        return {
            "ecosystem_overview": {
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a.state == AgentState.ACTIVE]),
                "total_capabilities": total_capabilities,
                "total_experiences": total_experiences,
                "total_knowledge_nodes": total_knowledge_nodes,
                "average_competence": avg_competence
            },
            "integration_stats": self.integration_stats,
            "agent_details": agent_statuses,
            "collaboration_network": self._analyze_collaboration_network()
        }
    
    def _analyze_collaboration_network(self) -> Dict[str, Any]:
        """分析协作网络"""
        network_stats = {
            "total_connections": 0,
            "collaboration_density": 0.0,
            "most_collaborative_agent": None,
            "collaboration_patterns": {}
        }
        
        if not self.agents:
            return network_stats
        
        # 计算连接数
        total_connections = sum(len(agent.collaborators) for agent in self.agents.values())
        network_stats["total_connections"] = total_connections
        
        # 计算协作密度
        max_possible_connections = len(self.agents) * (len(self.agents) - 1)
        if max_possible_connections > 0:
            network_stats["collaboration_density"] = total_connections / max_possible_connections
        
        # 找出最具协作性的智能体
        max_collaborations = 0
        most_collaborative = None
        
        for agent in self.agents.values():
            collaboration_count = agent.performance_metrics["collaboration_sessions"]
            if collaboration_count > max_collaborations:
                max_collaborations = collaboration_count
                most_collaborative = agent.agent_id
        
        network_stats["most_collaborative_agent"] = most_collaborative
        
        return network_stats

# 使用示例
async def main():
    """Agent Zero集成使用示例"""
    print("🤖 Agent Zero集成演示")
    print("=" * 50)
    
    # 初始化Agent Zero集成
    agent_zero = AgentZeroIntegration()
    
    # 等待默认智能体初始化
    await asyncio.sleep(1)
    
    # 分配代码分析任务
    code_analysis_task = {
        "type": "code_analysis",
        "complexity": "medium",
        "content": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        "requirements": ["性能分析", "优化建议"]
    }
    
    result1 = await agent_zero.assign_task(code_analysis_task)
    print(f"✅ 代码分析任务完成")
    print(f"   执行智能体: {result1['assigned_agent']}")
    print(f"   任务成功: {result1['task_result']['success']}")
    
    # 分配代码生成任务
    code_generation_task = {
        "type": "code_generation",
        "complexity": "high",
        "requirements": ["生成优化的斐波那契函数", "包含注释和测试"]
    }
    
    result2 = await agent_zero.assign_task(code_generation_task)
    print(f"✅ 代码生成任务完成")
    print(f"   执行智能体: {result2['assigned_agent']}")
    print(f"   执行方法: {result2['task_result']['result']['execution_method']}")
    
    # 触发集体学习
    learning_data = {
        "topic": "Python性能优化",
        "examples": ["动态规划", "缓存机制", "算法复杂度分析"],
        "best_practices": ["避免重复计算", "使用内置函数", "选择合适的数据结构"]
    }
    
    learning_result = await agent_zero.trigger_collective_learning(learning_data)
    print(f"✅ 集体学习完成")
    print(f"   参与智能体: {learning_result['participating_agents']} 个")
    
    # 获取生态系统状态
    ecosystem_status = await agent_zero.get_ecosystem_status()
    
    print(f"\n📊 Agent Zero生态系统状态:")
    print(f"   总智能体数: {ecosystem_status['ecosystem_overview']['total_agents']}")
    print(f"   活跃智能体: {ecosystem_status['ecosystem_overview']['active_agents']}")
    print(f"   总能力数: {ecosystem_status['ecosystem_overview']['total_capabilities']}")
    print(f"   总经验数: {ecosystem_status['ecosystem_overview']['total_experiences']}")
    print(f"   平均能力: {ecosystem_status['ecosystem_overview']['average_competence']:.2f}")
    print(f"   协作密度: {ecosystem_status['collaboration_network']['collaboration_density']:.2f}")
    
    print(f"\n🎯 集成统计:")
    print(f"   完成任务: {ecosystem_status['integration_stats']['completed_tasks']}")
    print(f"   协作事件: {ecosystem_status['integration_stats']['collaboration_events']}")
    print(f"   学习事件: {ecosystem_status['integration_stats']['learning_events']}")

if __name__ == "__main__":
    asyncio.run(main())

