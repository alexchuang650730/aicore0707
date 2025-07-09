"""
PowerAutomation 智能路由器

基于现有smart_router扩展，实现智能的任务路由决策：
- 多引擎路由决策算法
- 性能历史分析和优化
- 负载均衡和故障转移
- 与TaskAnalyzer集成的智能路由

支持动态路由策略和自适应优化。
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque

# 导入现有的智能路由组件
from ..routing.smart_router.smart_router import SmartRouter
from ..routing.smart_router.route_optimizer import RouteOptimizer
from ..routing.smart_router.semantic_analyzer import SemanticAnalyzer

# 导入任务分析器
from .task_analyzer import TaskAnalysisResult, TaskType, TaskComplexity, TaskDomain


class RouteStrategy(Enum):
    """路由策略枚举"""
    PERFORMANCE = "performance"      # 性能优先
    LOAD_BALANCE = "load_balance"    # 负载均衡
    COST_OPTIMIZE = "cost_optimize"  # 成本优化
    RELIABILITY = "reliability"      # 可靠性优先
    ADAPTIVE = "adaptive"            # 自适应


class ExecutionEngine(Enum):
    """执行引擎枚举"""
    LOCAL_ADAPTER = "local_adapter"
    TRAE_AGENT = "trae_agent"
    STAGEWISE = "stagewise"
    MEMORYOS = "memoryos"
    WEB_UI = "web_ui"
    AG_UI = "ag_ui"


@dataclass
class RouteStep:
    """路由步骤"""
    step_id: str
    engine: ExecutionEngine
    agent: Optional[str]
    mcp: Optional[str]
    config: Dict[str, Any]
    estimated_time: float
    priority: int
    dependencies: List[str]


@dataclass
class RoutePlan:
    """路由计划"""
    plan_id: str
    task_id: str
    strategy: RouteStrategy
    steps: List[RouteStep]
    total_estimated_time: float
    confidence_score: float
    fallback_plans: List['RoutePlan']
    metadata: Dict[str, Any]


@dataclass
class ExecutionMetrics:
    """执行指标"""
    engine: ExecutionEngine
    agent: Optional[str]
    mcp: Optional[str]
    success_rate: float
    average_time: float
    load_factor: float
    last_used: datetime
    error_count: int
    total_executions: int


class IntelligentRouter:
    """
    智能路由器
    
    基于任务分析结果和历史性能数据，
    智能选择最优的执行路径和资源分配。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能路由器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化基础组件
        self.smart_router = SmartRouter()
        self.route_optimizer = RouteOptimizer()
        self.semantic_analyzer = SemanticAnalyzer()
        
        # 性能指标存储
        self.metrics: Dict[str, ExecutionMetrics] = {}
        self.execution_history: deque = deque(maxlen=1000)
        
        # 负载监控
        self.current_loads: Dict[str, float] = defaultdict(float)
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        
        # 路由策略配置
        self.default_strategy = RouteStrategy(
            self.config.get("default_strategy", "adaptive")
        )
        
        # 引擎能力映射
        self._init_engine_capabilities()
        
        # 统计信息
        self.stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "average_planning_time": 0.0,
            "strategy_usage": defaultdict(int)
        }
        
        self.logger.info("智能路由器初始化完成")
    
    def _init_engine_capabilities(self):
        """初始化引擎能力映射"""
        self.engine_capabilities = {
            ExecutionEngine.LOCAL_ADAPTER: {
                "task_types": [TaskType.DEPLOYMENT, TaskType.MONITORING, TaskType.AUTOMATION],
                "domains": [TaskDomain.DEVOPS, TaskDomain.CLOUD, TaskDomain.BACKEND],
                "max_complexity": TaskComplexity.EXPERT,
                "parallel_support": True,
                "cost_factor": 0.3,
                "reliability_score": 0.9
            },
            ExecutionEngine.TRAE_AGENT: {
                "task_types": [TaskType.DEVELOPMENT, TaskType.ARCHITECTURE, TaskType.ANALYSIS],
                "domains": [TaskDomain.FULLSTACK, TaskDomain.BACKEND, TaskDomain.FRONTEND],
                "max_complexity": TaskComplexity.EXPERT,
                "parallel_support": True,
                "cost_factor": 0.8,
                "reliability_score": 0.85
            },
            ExecutionEngine.STAGEWISE: {
                "task_types": [TaskType.DEVELOPMENT, TaskType.TESTING, TaskType.DOCUMENTATION],
                "domains": [TaskDomain.FRONTEND, TaskDomain.WEB, TaskDomain.MOBILE],
                "max_complexity": TaskComplexity.COMPLEX,
                "parallel_support": False,
                "cost_factor": 0.5,
                "reliability_score": 0.8
            },
            ExecutionEngine.MEMORYOS: {
                "task_types": [TaskType.ANALYSIS, TaskType.DOCUMENTATION],
                "domains": [TaskDomain.DATA_SCIENCE, TaskDomain.GENERAL],
                "max_complexity": TaskComplexity.MODERATE,
                "parallel_support": False,
                "cost_factor": 0.2,
                "reliability_score": 0.7
            },
            ExecutionEngine.WEB_UI: {
                "task_types": [TaskType.DEVELOPMENT],
                "domains": [TaskDomain.FRONTEND, TaskDomain.WEB],
                "max_complexity": TaskComplexity.COMPLEX,
                "parallel_support": False,
                "cost_factor": 0.4,
                "reliability_score": 0.75
            },
            ExecutionEngine.AG_UI: {
                "task_types": [TaskType.DEVELOPMENT],
                "domains": [TaskDomain.FRONTEND, TaskDomain.WEB],
                "max_complexity": TaskComplexity.MODERATE,
                "parallel_support": False,
                "cost_factor": 0.3,
                "reliability_score": 0.7
            }
        }
        
        # 智能体能力映射
        self.agent_capabilities = {
            "architect_agent": {
                "task_types": [TaskType.ARCHITECTURE, TaskType.ANALYSIS],
                "complexity_bonus": 0.2,
                "reliability_score": 0.9
            },
            "developer_agent": {
                "task_types": [TaskType.DEVELOPMENT, TaskType.DOCUMENTATION],
                "complexity_bonus": 0.1,
                "reliability_score": 0.85
            },
            "deploy_agent": {
                "task_types": [TaskType.DEPLOYMENT, TaskType.AUTOMATION],
                "complexity_bonus": 0.15,
                "reliability_score": 0.9
            },
            "test_agent": {
                "task_types": [TaskType.TESTING],
                "complexity_bonus": 0.1,
                "reliability_score": 0.8
            },
            "monitor_agent": {
                "task_types": [TaskType.MONITORING, TaskType.ANALYSIS],
                "complexity_bonus": 0.05,
                "reliability_score": 0.85
            },
            "security_agent": {
                "task_types": [TaskType.SECURITY],
                "complexity_bonus": 0.25,
                "reliability_score": 0.95
            }
        }
    
    async def route_task(self, task: Any, analysis_result: TaskAnalysisResult, 
                        strategy: Optional[RouteStrategy] = None) -> RoutePlan:
        """
        路由任务
        
        Args:
            task: 任务对象
            analysis_result: 任务分析结果
            strategy: 路由策略
            
        Returns:
            路由计划
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"开始路由任务: {task.id}")
            
            # 确定路由策略
            route_strategy = strategy or self._determine_strategy(analysis_result)
            
            # 生成候选路由方案
            candidate_plans = await self._generate_candidate_plans(
                task, analysis_result, route_strategy
            )
            
            # 评估和选择最优方案
            best_plan = await self._select_best_plan(
                candidate_plans, analysis_result, route_strategy
            )
            
            # 生成备用方案
            fallback_plans = await self._generate_fallback_plans(
                task, analysis_result, best_plan
            )
            
            best_plan.fallback_plans = fallback_plans
            
            # 更新统计信息
            planning_time = (datetime.now() - start_time).total_seconds()
            self._update_routing_stats(route_strategy, planning_time, True)
            
            self.logger.info(f"任务路由完成: {task.id}, 策略: {route_strategy.value}")
            
            return best_plan
            
        except Exception as e:
            planning_time = (datetime.now() - start_time).total_seconds()
            self._update_routing_stats(strategy or self.default_strategy, planning_time, False)
            
            self.logger.error(f"任务路由失败: {task.id} - {e}")
            
            # 返回默认路由计划
            return await self._create_default_plan(task, analysis_result)
    
    def _determine_strategy(self, analysis_result: TaskAnalysisResult) -> RouteStrategy:
        """确定路由策略"""
        # 基于任务特征确定策略
        if analysis_result.complexity in [TaskComplexity.EXPERT, TaskComplexity.ADVANCED]:
            return RouteStrategy.RELIABILITY
        
        if analysis_result.task_type == TaskType.DEPLOYMENT:
            return RouteStrategy.PERFORMANCE
        
        if analysis_result.estimated_time > 10:  # 长时间任务
            return RouteStrategy.LOAD_BALANCE
        
        return RouteStrategy.ADAPTIVE
    
    async def _generate_candidate_plans(self, task: Any, analysis_result: TaskAnalysisResult, 
                                      strategy: RouteStrategy) -> List[RoutePlan]:
        """生成候选路由方案"""
        candidate_plans = []
        
        # 获取适合的引擎
        suitable_engines = self._get_suitable_engines(analysis_result)
        
        for engine in suitable_engines:
            try:
                # 为每个引擎生成路由计划
                plan = await self._create_engine_plan(
                    task, analysis_result, engine, strategy
                )
                
                if plan:
                    candidate_plans.append(plan)
                    
            except Exception as e:
                self.logger.warning(f"引擎 {engine.value} 路由计划生成失败: {e}")
        
        # 生成混合方案（多引擎协作）
        if len(suitable_engines) > 1 and analysis_result.complexity.value >= 3:
            hybrid_plans = await self._create_hybrid_plans(
                task, analysis_result, suitable_engines, strategy
            )
            candidate_plans.extend(hybrid_plans)
        
        return candidate_plans
    
    def _get_suitable_engines(self, analysis_result: TaskAnalysisResult) -> List[ExecutionEngine]:
        """获取适合的执行引擎"""
        suitable_engines = []
        
        for engine, capabilities in self.engine_capabilities.items():
            # 检查任务类型匹配
            if analysis_result.task_type in capabilities["task_types"]:
                suitable_engines.append(engine)
                continue
            
            # 检查领域匹配
            if analysis_result.domain in capabilities["domains"]:
                suitable_engines.append(engine)
                continue
            
            # 检查复杂度支持
            if analysis_result.complexity.value <= capabilities["max_complexity"].value:
                suitable_engines.append(engine)
        
        # 如果没有完全匹配的，选择通用引擎
        if not suitable_engines:
            suitable_engines = [ExecutionEngine.LOCAL_ADAPTER, ExecutionEngine.TRAE_AGENT]
        
        # 根据当前负载过滤
        available_engines = []
        for engine in suitable_engines:
            if self.current_loads[engine.value] < 0.8:  # 负载阈值
                available_engines.append(engine)
        
        return available_engines or suitable_engines[:1]  # 至少返回一个
    
    async def _create_engine_plan(self, task: Any, analysis_result: TaskAnalysisResult,
                                engine: ExecutionEngine, strategy: RouteStrategy) -> Optional[RoutePlan]:
        """为特定引擎创建路由计划"""
        try:
            plan_id = f"plan_{task.id}_{engine.value}_{datetime.now().strftime('%H%M%S')}"
            
            # 选择最佳智能体
            best_agent = self._select_best_agent(analysis_result, engine)
            
            # 选择最佳MCP
            best_mcp = self._select_best_mcp(analysis_result, engine)
            
            # 创建执行步骤
            steps = []
            
            # 主执行步骤
            main_step = RouteStep(
                step_id=f"step_main_{engine.value}",
                engine=engine,
                agent=best_agent,
                mcp=best_mcp,
                config=self._create_step_config(analysis_result, engine, best_agent, best_mcp),
                estimated_time=analysis_result.estimated_time,
                priority=1,
                dependencies=[]
            )
            steps.append(main_step)
            
            # 添加前置步骤（如果需要）
            if analysis_result.complexity.value >= 3:
                prep_step = RouteStep(
                    step_id=f"step_prep_{engine.value}",
                    engine=ExecutionEngine.LOCAL_ADAPTER,
                    agent="architect_agent",
                    mcp="local_adapter_mcp",
                    config={"action": "prepare_environment", "task_type": analysis_result.task_type.value},
                    estimated_time=0.2,
                    priority=0,
                    dependencies=[]
                )
                steps.insert(0, prep_step)
                main_step.dependencies.append(prep_step.step_id)
            
            # 添加后置步骤（如果需要）
            if analysis_result.task_type in [TaskType.DEVELOPMENT, TaskType.DEPLOYMENT]:
                verify_step = RouteStep(
                    step_id=f"step_verify_{engine.value}",
                    engine=ExecutionEngine.LOCAL_ADAPTER,
                    agent="test_agent",
                    mcp="local_adapter_mcp",
                    config={"action": "verify_result", "task_type": analysis_result.task_type.value},
                    estimated_time=0.3,
                    priority=2,
                    dependencies=[main_step.step_id]
                )
                steps.append(verify_step)
            
            # 计算总预估时间
            total_time = sum(step.estimated_time for step in steps)
            
            # 计算置信度
            confidence = self._calculate_plan_confidence(
                engine, best_agent, best_mcp, analysis_result
            )
            
            plan = RoutePlan(
                plan_id=plan_id,
                task_id=task.id,
                strategy=strategy,
                steps=steps,
                total_estimated_time=total_time,
                confidence_score=confidence,
                fallback_plans=[],
                metadata={
                    "primary_engine": engine.value,
                    "primary_agent": best_agent,
                    "primary_mcp": best_mcp,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"创建引擎计划失败 {engine.value}: {e}")
            return None
    
    def _select_best_agent(self, analysis_result: TaskAnalysisResult, 
                          engine: ExecutionEngine) -> Optional[str]:
        """选择最佳智能体"""
        # 从分析结果的建议中选择
        suggested_agents = analysis_result.suggested_agents
        
        # 根据任务类型和引擎能力筛选
        suitable_agents = []
        for agent in suggested_agents:
            if agent in self.agent_capabilities:
                agent_caps = self.agent_capabilities[agent]
                if analysis_result.task_type in agent_caps["task_types"]:
                    suitable_agents.append(agent)
        
        if not suitable_agents:
            suitable_agents = suggested_agents
        
        # 根据性能指标选择最佳
        if suitable_agents:
            best_agent = suitable_agents[0]
            best_score = 0
            
            for agent in suitable_agents:
                score = self._calculate_agent_score(agent, analysis_result)
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            return best_agent
        
        return None
    
    def _select_best_mcp(self, analysis_result: TaskAnalysisResult, 
                        engine: ExecutionEngine) -> Optional[str]:
        """选择最佳MCP"""
        # 从分析结果的建议中选择
        suggested_mcps = analysis_result.suggested_mcps
        
        # 根据引擎类型映射MCP
        engine_mcp_mapping = {
            ExecutionEngine.LOCAL_ADAPTER: "local_adapter_mcp",
            ExecutionEngine.TRAE_AGENT: "trae_agent_mcp",
            ExecutionEngine.STAGEWISE: "stagewise_mcp",
            ExecutionEngine.MEMORYOS: "memoryos_mcp",
            ExecutionEngine.WEB_UI: "web_ui_mcp",
            ExecutionEngine.AG_UI: "ag_ui_mcp"
        }
        
        # 优先使用引擎对应的MCP
        preferred_mcp = engine_mcp_mapping.get(engine)
        if preferred_mcp and preferred_mcp in suggested_mcps:
            return preferred_mcp
        
        # 否则选择第一个建议的MCP
        return suggested_mcps[0] if suggested_mcps else preferred_mcp
    
    def _create_step_config(self, analysis_result: TaskAnalysisResult, 
                           engine: ExecutionEngine, agent: Optional[str], 
                           mcp: Optional[str]) -> Dict[str, Any]:
        """创建步骤配置"""
        config = {
            "task_type": analysis_result.task_type.value,
            "complexity": analysis_result.complexity.value,
            "domain": analysis_result.domain.value,
            "estimated_time": analysis_result.estimated_time,
            "required_skills": analysis_result.required_skills,
            "keywords": analysis_result.keywords,
            "entities": analysis_result.entities
        }
        
        # 引擎特定配置
        if engine == ExecutionEngine.LOCAL_ADAPTER:
            config.update({
                "platform_detection": True,
                "cross_platform": True,
                "ai_enhanced": True
            })
        elif engine == ExecutionEngine.TRAE_AGENT:
            config.update({
                "multi_model": True,
                "collaborative": True,
                "result_integration": True
            })
        elif engine == ExecutionEngine.STAGEWISE:
            config.update({
                "visual_programming": True,
                "step_by_step": True,
                "ui_integration": True
            })
        
        # 智能体特定配置
        if agent:
            config["agent_config"] = {
                "agent_name": agent,
                "specialization": self.agent_capabilities.get(agent, {}).get("task_types", [])
            }
        
        # MCP特定配置
        if mcp:
            config["mcp_config"] = {
                "mcp_name": mcp,
                "communication_protocol": "async",
                "timeout": 300
            }
        
        return config
    
    def _calculate_plan_confidence(self, engine: ExecutionEngine, agent: Optional[str],
                                 mcp: Optional[str], analysis_result: TaskAnalysisResult) -> float:
        """计算计划置信度"""
        confidence = 0.5  # 基础置信度
        
        # 引擎匹配度
        engine_caps = self.engine_capabilities.get(engine, {})
        if analysis_result.task_type in engine_caps.get("task_types", []):
            confidence += 0.2
        if analysis_result.domain in engine_caps.get("domains", []):
            confidence += 0.1
        
        # 智能体匹配度
        if agent and agent in self.agent_capabilities:
            agent_caps = self.agent_capabilities[agent]
            if analysis_result.task_type in agent_caps.get("task_types", []):
                confidence += 0.1
        
        # 历史性能
        metrics_key = f"{engine.value}_{agent}_{mcp}"
        if metrics_key in self.metrics:
            metrics = self.metrics[metrics_key]
            confidence += metrics.success_rate * 0.1
        
        # 负载因子
        load_factor = self.current_loads.get(engine.value, 0)
        confidence -= load_factor * 0.1
        
        return max(0.0, min(confidence, 1.0))
    
    def _calculate_agent_score(self, agent: str, analysis_result: TaskAnalysisResult) -> float:
        """计算智能体评分"""
        score = 0.5
        
        if agent in self.agent_capabilities:
            agent_caps = self.agent_capabilities[agent]
            
            # 任务类型匹配
            if analysis_result.task_type in agent_caps.get("task_types", []):
                score += 0.3
            
            # 复杂度奖励
            complexity_bonus = agent_caps.get("complexity_bonus", 0)
            score += complexity_bonus * (analysis_result.complexity.value / 5)
            
            # 可靠性评分
            reliability = agent_caps.get("reliability_score", 0.5)
            score += reliability * 0.2
        
        # 历史性能
        metrics_key = f"agent_{agent}"
        if metrics_key in self.metrics:
            metrics = self.metrics[metrics_key]
            score += metrics.success_rate * 0.2
        
        return score
    
    async def _create_hybrid_plans(self, task: Any, analysis_result: TaskAnalysisResult,
                                 engines: List[ExecutionEngine], 
                                 strategy: RouteStrategy) -> List[RoutePlan]:
        """创建混合执行计划"""
        hybrid_plans = []
        
        try:
            # 创建并行执行计划
            if len(engines) >= 2 and analysis_result.complexity.value >= 4:
                parallel_plan = await self._create_parallel_plan(
                    task, analysis_result, engines[:2], strategy
                )
                if parallel_plan:
                    hybrid_plans.append(parallel_plan)
            
            # 创建流水线执行计划
            if len(engines) >= 3:
                pipeline_plan = await self._create_pipeline_plan(
                    task, analysis_result, engines[:3], strategy
                )
                if pipeline_plan:
                    hybrid_plans.append(pipeline_plan)
            
        except Exception as e:
            self.logger.warning(f"创建混合计划失败: {e}")
        
        return hybrid_plans
    
    async def _create_parallel_plan(self, task: Any, analysis_result: TaskAnalysisResult,
                                  engines: List[ExecutionEngine], 
                                  strategy: RouteStrategy) -> Optional[RoutePlan]:
        """创建并行执行计划"""
        try:
            plan_id = f"plan_{task.id}_parallel_{datetime.now().strftime('%H%M%S')}"
            steps = []
            
            # 为每个引擎创建并行步骤
            for i, engine in enumerate(engines):
                agent = self._select_best_agent(analysis_result, engine)
                mcp = self._select_best_mcp(analysis_result, engine)
                
                step = RouteStep(
                    step_id=f"step_parallel_{i}_{engine.value}",
                    engine=engine,
                    agent=agent,
                    mcp=mcp,
                    config=self._create_step_config(analysis_result, engine, agent, mcp),
                    estimated_time=analysis_result.estimated_time * 0.7,  # 并行执行时间减少
                    priority=1,
                    dependencies=[]
                )
                steps.append(step)
            
            # 添加结果整合步骤
            integration_step = RouteStep(
                step_id="step_integration",
                engine=ExecutionEngine.LOCAL_ADAPTER,
                agent="architect_agent",
                mcp="local_adapter_mcp",
                config={"action": "integrate_parallel_results"},
                estimated_time=0.5,
                priority=2,
                dependencies=[step.step_id for step in steps]
            )
            steps.append(integration_step)
            
            total_time = max(step.estimated_time for step in steps[:-1]) + integration_step.estimated_time
            
            plan = RoutePlan(
                plan_id=plan_id,
                task_id=task.id,
                strategy=strategy,
                steps=steps,
                total_estimated_time=total_time,
                confidence_score=0.8,  # 并行执行置信度较高
                fallback_plans=[],
                metadata={
                    "execution_type": "parallel",
                    "engines": [engine.value for engine in engines],
                    "created_at": datetime.now().isoformat()
                }
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"创建并行计划失败: {e}")
            return None
    
    async def _create_pipeline_plan(self, task: Any, analysis_result: TaskAnalysisResult,
                                  engines: List[ExecutionEngine], 
                                  strategy: RouteStrategy) -> Optional[RoutePlan]:
        """创建流水线执行计划"""
        try:
            plan_id = f"plan_{task.id}_pipeline_{datetime.now().strftime('%H%M%S')}"
            steps = []
            
            # 为每个引擎创建流水线步骤
            for i, engine in enumerate(engines):
                agent = self._select_best_agent(analysis_result, engine)
                mcp = self._select_best_mcp(analysis_result, engine)
                
                dependencies = []
                if i > 0:
                    dependencies.append(steps[i-1].step_id)
                
                step = RouteStep(
                    step_id=f"step_pipeline_{i}_{engine.value}",
                    engine=engine,
                    agent=agent,
                    mcp=mcp,
                    config=self._create_step_config(analysis_result, engine, agent, mcp),
                    estimated_time=analysis_result.estimated_time / len(engines),
                    priority=i,
                    dependencies=dependencies
                )
                steps.append(step)
            
            total_time = sum(step.estimated_time for step in steps)
            
            plan = RoutePlan(
                plan_id=plan_id,
                task_id=task.id,
                strategy=strategy,
                steps=steps,
                total_estimated_time=total_time,
                confidence_score=0.75,  # 流水线执行置信度中等
                fallback_plans=[],
                metadata={
                    "execution_type": "pipeline",
                    "engines": [engine.value for engine in engines],
                    "created_at": datetime.now().isoformat()
                }
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"创建流水线计划失败: {e}")
            return None
    
    async def _select_best_plan(self, candidate_plans: List[RoutePlan], 
                              analysis_result: TaskAnalysisResult,
                              strategy: RouteStrategy) -> RoutePlan:
        """选择最佳路由计划"""
        if not candidate_plans:
            raise ValueError("没有可用的候选计划")
        
        # 根据策略评分
        scored_plans = []
        for plan in candidate_plans:
            score = await self._score_plan(plan, analysis_result, strategy)
            scored_plans.append((plan, score))
        
        # 选择得分最高的计划
        best_plan, best_score = max(scored_plans, key=lambda x: x[1])
        
        self.logger.info(f"选择最佳计划: {best_plan.plan_id}, 得分: {best_score:.2f}")
        
        return best_plan
    
    async def _score_plan(self, plan: RoutePlan, analysis_result: TaskAnalysisResult,
                        strategy: RouteStrategy) -> float:
        """为路由计划评分"""
        score = 0.0
        
        # 基础置信度
        score += plan.confidence_score * 0.3
        
        # 策略特定评分
        if strategy == RouteStrategy.PERFORMANCE:
            # 性能优先：时间越短越好
            time_score = max(0, 1 - (plan.total_estimated_time / (analysis_result.estimated_time * 2)))
            score += time_score * 0.4
            
        elif strategy == RouteStrategy.LOAD_BALANCE:
            # 负载均衡：选择负载较低的引擎
            load_scores = []
            for step in plan.steps:
                load = self.current_loads.get(step.engine.value, 0)
                load_scores.append(1 - load)
            avg_load_score = sum(load_scores) / len(load_scores) if load_scores else 0
            score += avg_load_score * 0.4
            
        elif strategy == RouteStrategy.COST_OPTIMIZE:
            # 成本优化：选择成本较低的引擎
            cost_scores = []
            for step in plan.steps:
                engine_caps = self.engine_capabilities.get(step.engine, {})
                cost_factor = engine_caps.get("cost_factor", 0.5)
                cost_scores.append(1 - cost_factor)
            avg_cost_score = sum(cost_scores) / len(cost_scores) if cost_scores else 0
            score += avg_cost_score * 0.4
            
        elif strategy == RouteStrategy.RELIABILITY:
            # 可靠性优先：选择可靠性高的引擎
            reliability_scores = []
            for step in plan.steps:
                engine_caps = self.engine_capabilities.get(step.engine, {})
                reliability = engine_caps.get("reliability_score", 0.5)
                reliability_scores.append(reliability)
            avg_reliability = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0
            score += avg_reliability * 0.4
            
        elif strategy == RouteStrategy.ADAPTIVE:
            # 自适应：综合考虑各因素
            score += plan.confidence_score * 0.2
            
            # 时间因子
            time_factor = max(0, 1 - (plan.total_estimated_time / (analysis_result.estimated_time * 1.5)))
            score += time_factor * 0.1
            
            # 负载因子
            avg_load = sum(self.current_loads.get(step.engine.value, 0) for step in plan.steps) / len(plan.steps)
            score += (1 - avg_load) * 0.1
        
        # 历史性能加分
        for step in plan.steps:
            metrics_key = f"{step.engine.value}_{step.agent}_{step.mcp}"
            if metrics_key in self.metrics:
                metrics = self.metrics[metrics_key]
                score += metrics.success_rate * 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _generate_fallback_plans(self, task: Any, analysis_result: TaskAnalysisResult,
                                     primary_plan: RoutePlan) -> List[RoutePlan]:
        """生成备用计划"""
        fallback_plans = []
        
        try:
            # 获取未使用的引擎
            used_engines = set()
            for step in primary_plan.steps:
                used_engines.add(step.engine)
            
            available_engines = [
                engine for engine in ExecutionEngine 
                if engine not in used_engines
            ]
            
            # 为每个可用引擎创建简单的备用计划
            for engine in available_engines[:2]:  # 最多2个备用计划
                fallback_plan = await self._create_engine_plan(
                    task, analysis_result, engine, RouteStrategy.RELIABILITY
                )
                if fallback_plan:
                    fallback_plan.plan_id = f"fallback_{fallback_plan.plan_id}"
                    fallback_plans.append(fallback_plan)
            
        except Exception as e:
            self.logger.warning(f"生成备用计划失败: {e}")
        
        return fallback_plans
    
    async def _create_default_plan(self, task: Any, analysis_result: TaskAnalysisResult) -> RoutePlan:
        """创建默认路由计划"""
        plan_id = f"plan_{task.id}_default_{datetime.now().strftime('%H%M%S')}"
        
        # 使用Local Adapter作为默认引擎
        default_step = RouteStep(
            step_id="step_default",
            engine=ExecutionEngine.LOCAL_ADAPTER,
            agent="developer_agent",
            mcp="local_adapter_mcp",
            config={
                "task_type": analysis_result.task_type.value,
                "fallback_mode": True
            },
            estimated_time=analysis_result.estimated_time * 1.5,  # 默认计划时间较长
            priority=1,
            dependencies=[]
        )
        
        return RoutePlan(
            plan_id=plan_id,
            task_id=task.id,
            strategy=RouteStrategy.RELIABILITY,
            steps=[default_step],
            total_estimated_time=default_step.estimated_time,
            confidence_score=0.3,  # 默认计划置信度较低
            fallback_plans=[],
            metadata={
                "is_default": True,
                "created_at": datetime.now().isoformat()
            }
        )
    
    def _update_routing_stats(self, strategy: RouteStrategy, planning_time: float, success: bool):
        """更新路由统计信息"""
        self.stats["total_routes"] += 1
        
        if success:
            self.stats["successful_routes"] += 1
        else:
            self.stats["failed_routes"] += 1
        
        # 更新平均规划时间
        total = self.stats["total_routes"]
        current_avg = self.stats["average_planning_time"]
        self.stats["average_planning_time"] = (current_avg * (total - 1) + planning_time) / total
        
        # 更新策略使用统计
        self.stats["strategy_usage"][strategy.value] += 1
    
    async def update_execution_metrics(self, plan: RoutePlan, step_id: str, 
                                     success: bool, execution_time: float, error: Optional[str] = None):
        """更新执行指标"""
        try:
            # 找到对应的步骤
            step = None
            for s in plan.steps:
                if s.step_id == step_id:
                    step = s
                    break
            
            if not step:
                return
            
            # 更新指标
            metrics_key = f"{step.engine.value}_{step.agent}_{step.mcp}"
            
            if metrics_key not in self.metrics:
                self.metrics[metrics_key] = ExecutionMetrics(
                    engine=step.engine,
                    agent=step.agent,
                    mcp=step.mcp,
                    success_rate=0.0,
                    average_time=0.0,
                    load_factor=0.0,
                    last_used=datetime.now(),
                    error_count=0,
                    total_executions=0
                )
            
            metrics = self.metrics[metrics_key]
            metrics.total_executions += 1
            metrics.last_used = datetime.now()
            
            if success:
                # 更新成功率
                total = metrics.total_executions
                current_rate = metrics.success_rate
                metrics.success_rate = (current_rate * (total - 1) + 1) / total
                
                # 更新平均时间
                current_avg = metrics.average_time
                metrics.average_time = (current_avg * (total - 1) + execution_time) / total
            else:
                metrics.error_count += 1
                # 更新成功率
                total = metrics.total_executions
                current_rate = metrics.success_rate
                metrics.success_rate = (current_rate * (total - 1)) / total
            
            # 记录执行历史
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "plan_id": plan.plan_id,
                "step_id": step_id,
                "engine": step.engine.value,
                "agent": step.agent,
                "mcp": step.mcp,
                "success": success,
                "execution_time": execution_time,
                "error": error
            })
            
        except Exception as e:
            self.logger.error(f"更新执行指标失败: {e}")
    
    def update_load(self, engine: str, load_delta: float):
        """更新引擎负载"""
        self.current_loads[engine] = max(0.0, min(1.0, self.current_loads[engine] + load_delta))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_loads": dict(self.current_loads),
            "total_metrics": len(self.metrics),
            "execution_history_size": len(self.execution_history)
        }
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取执行指标"""
        return {
            key: asdict(metrics) for key, metrics in self.metrics.items()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "stats": self.get_stats(),
            "engine_loads": dict(self.current_loads),
            "available_engines": [engine.value for engine in ExecutionEngine],
            "total_metrics": len(self.metrics)
        }


if __name__ == "__main__":
    # 测试智能路由器
    import asyncio
    from .task_analyzer import TaskAnalyzer
    
    async def test_intelligent_router():
        # 创建组件
        analyzer = TaskAnalyzer()
        router = IntelligentRouter()
        
        # 模拟任务
        class MockTask:
            def __init__(self, task_id, description):
                self.id = task_id
                self.description = description
        
        test_tasks = [
            ("task_1", "Create a React frontend with authentication"),
            ("task_2", "Deploy Python API to AWS using Docker"),
            ("task_3", "Implement comprehensive testing suite"),
            ("task_4", "Set up monitoring and alerting system")
        ]
        
        for task_id, description in test_tasks:
            print(f"\n测试任务: {description}")
            
            # 分析任务
            task = MockTask(task_id, description)
            analysis_result = await analyzer.analyze_task(description)
            
            # 路由任务
            route_plan = await router.route_task(task, analysis_result)
            
            print(f"路由计划ID: {route_plan.plan_id}")
            print(f"策略: {route_plan.strategy.value}")
            print(f"总预估时间: {route_plan.total_estimated_time:.1f}小时")
            print(f"置信度: {route_plan.confidence_score:.2f}")
            print(f"步骤数: {len(route_plan.steps)}")
            
            for i, step in enumerate(route_plan.steps):
                print(f"  步骤{i+1}: {step.engine.value} -> {step.agent} -> {step.mcp}")
            
            # 模拟执行结果更新
            for step in route_plan.steps:
                await router.update_execution_metrics(
                    route_plan, step.step_id, True, step.estimated_time * 0.8
                )
        
        # 显示统计信息
        print(f"\n路由器统计: {router.get_stats()}")
        print(f"执行指标: {list(router.get_metrics().keys())}")
    
    # 运行测试
    asyncio.run(test_intelligent_router())

