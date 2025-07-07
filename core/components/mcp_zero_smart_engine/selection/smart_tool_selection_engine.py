"""
Smart Tool Engine 智能选择层

基于AI驱动的智能工具选择系统，实现：
- AI决策引擎
- 成本优化算法
- 性能预测系统
- 智能工具组合推荐
"""

import asyncio
import json
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import math

from ..models.tool_models import MCPTool, TaskRequirement, ToolRecommendation, ToolCapability


class SelectionStrategy(Enum):
    """选择策略"""
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    COST_OPTIMIZED = "cost_optimized"       # 成本优化
    BALANCED = "balanced"                    # 平衡策略
    SPEED_FIRST = "speed_first"              # 速度优先
    ACCURACY_FIRST = "accuracy_first"        # 准确性优先


@dataclass
class SelectionContext:
    """选择上下文"""
    user_id: str
    session_id: str
    task_history: List[Dict]
    user_preferences: Dict[str, Any]
    resource_constraints: Dict[str, Any]
    time_constraints: Optional[float] = None
    budget_constraints: Optional[float] = None


@dataclass
class ToolScore:
    """工具评分"""
    tool_id: str
    relevance_score: float      # 相关性分数 (0-1)
    performance_score: float    # 性能分数 (0-1)
    cost_score: float          # 成本分数 (0-1)
    speed_score: float         # 速度分数 (0-1)
    accuracy_score: float      # 准确性分数 (0-1)
    user_preference_score: float # 用户偏好分数 (0-1)
    final_score: float         # 最终综合分数 (0-1)
    reasoning: str             # 选择理由


class SmartToolSelectionEngine:
    """Smart Tool Engine 智能选择层"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.selection_history: List[Dict] = []
        self.user_preferences: Dict[str, Dict] = {}
        self.tool_performance_cache: Dict[str, Dict] = {}
        self.cost_model: Dict[str, float] = {}
        
        # AI模型权重配置
        self.strategy_weights = {
            SelectionStrategy.PERFORMANCE_FIRST: {
                'relevance': 0.3, 'performance': 0.4, 'cost': 0.1, 
                'speed': 0.1, 'accuracy': 0.1, 'user_preference': 0.0
            },
            SelectionStrategy.COST_OPTIMIZED: {
                'relevance': 0.3, 'performance': 0.1, 'cost': 0.4, 
                'speed': 0.1, 'accuracy': 0.1, 'user_preference': 0.0
            },
            SelectionStrategy.BALANCED: {
                'relevance': 0.25, 'performance': 0.2, 'cost': 0.2, 
                'speed': 0.15, 'accuracy': 0.15, 'user_preference': 0.05
            },
            SelectionStrategy.SPEED_FIRST: {
                'relevance': 0.3, 'performance': 0.1, 'cost': 0.1, 
                'speed': 0.4, 'accuracy': 0.1, 'user_preference': 0.0
            },
            SelectionStrategy.ACCURACY_FIRST: {
                'relevance': 0.3, 'performance': 0.1, 'cost': 0.1, 
                'speed': 0.1, 'accuracy': 0.4, 'user_preference': 0.0
            }
        }
        
        # 初始化成本模型
        self._initialize_cost_model()
    
    def _initialize_cost_model(self) -> None:
        """初始化成本模型"""
        self.cost_model = {
            'ai': 0.8,          # AI工具成本较高
            'web': 0.3,         # Web工具成本中等
            'file': 0.1,        # 文件工具成本低
            'terminal': 0.2,    # 终端工具成本低
            'git': 0.2,         # Git工具成本低
            'deploy': 0.6,      # 部署工具成本较高
            'monitor': 0.4,     # 监控工具成本中等
            'security': 0.5,    # 安全工具成本中等
            'data': 0.4,        # 数据工具成本中等
            'api': 0.3,         # API工具成本中等
            'general': 0.2      # 通用工具成本低
        }
    
    async def select_tools(
        self,
        task_requirement: TaskRequirement,
        available_tools: List[MCPTool],
        context: SelectionContext,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        max_tools: int = 5
    ) -> List[ToolRecommendation]:
        """智能选择工具"""
        
        self.logger.info(f"开始智能工具选择: {task_requirement.task_type}, 策略: {strategy.value}")
        
        # 1. 预过滤工具
        filtered_tools = await self._filter_tools(task_requirement, available_tools, context)
        
        # 2. 计算工具评分
        tool_scores = await self._calculate_tool_scores(
            task_requirement, filtered_tools, context, strategy
        )
        
        # 3. 排序和选择
        selected_scores = sorted(tool_scores, key=lambda x: x.final_score, reverse=True)[:max_tools]
        
        # 4. 生成推荐
        recommendations = await self._generate_recommendations(
            selected_scores, task_requirement, context
        )
        
        # 5. 记录选择历史
        await self._record_selection(task_requirement, recommendations, context, strategy)
        
        self.logger.info(f"完成工具选择，推荐{len(recommendations)}个工具")
        return recommendations
    
    async def _filter_tools(
        self,
        task_requirement: TaskRequirement,
        available_tools: List[MCPTool],
        context: SelectionContext
    ) -> List[MCPTool]:
        """预过滤工具"""
        
        filtered_tools = []
        
        for tool in available_tools:
            # 检查工具是否激活
            if not tool.is_active:
                continue
            
            # 检查能力匹配
            if not self._check_capability_match(task_requirement, tool):
                continue
            
            # 检查资源约束
            if not self._check_resource_constraints(tool, context):
                continue
            
            # 检查用户偏好
            if not self._check_user_preferences(tool, context):
                continue
            
            filtered_tools.append(tool)
        
        self.logger.info(f"预过滤完成: {len(available_tools)} -> {len(filtered_tools)}")
        return filtered_tools
    
    def _check_capability_match(self, task_requirement: TaskRequirement, tool: MCPTool) -> bool:
        """检查能力匹配"""
        required_capabilities = set(task_requirement.required_capabilities)
        tool_capabilities = set(tool.capabilities)
        
        # 至少需要一个能力匹配
        return len(required_capabilities.intersection(tool_capabilities)) > 0
    
    def _check_resource_constraints(self, tool: MCPTool, context: SelectionContext) -> bool:
        """检查资源约束"""
        constraints = context.resource_constraints
        
        # 检查内存约束
        if 'max_memory' in constraints:
            estimated_memory = self._estimate_tool_memory(tool)
            if estimated_memory > constraints['max_memory']:
                return False
        
        # 检查CPU约束
        if 'max_cpu' in constraints:
            estimated_cpu = self._estimate_tool_cpu(tool)
            if estimated_cpu > constraints['max_cpu']:
                return False
        
        return True
    
    def _check_user_preferences(self, tool: MCPTool, context: SelectionContext) -> bool:
        """检查用户偏好"""
        user_prefs = context.user_preferences
        
        # 检查黑名单
        if 'blacklist' in user_prefs:
            if tool.id in user_prefs['blacklist'] or tool.type in user_prefs['blacklist']:
                return False
        
        # 检查白名单
        if 'whitelist' in user_prefs:
            if tool.id not in user_prefs['whitelist'] and tool.type not in user_prefs['whitelist']:
                return False
        
        return True
    
    async def _calculate_tool_scores(
        self,
        task_requirement: TaskRequirement,
        tools: List[MCPTool],
        context: SelectionContext,
        strategy: SelectionStrategy
    ) -> List[ToolScore]:
        """计算工具评分"""
        
        tool_scores = []
        weights = self.strategy_weights[strategy]
        
        for tool in tools:
            # 计算各项分数
            relevance_score = self._calculate_relevance_score(task_requirement, tool)
            performance_score = self._calculate_performance_score(tool, context)
            cost_score = self._calculate_cost_score(tool, context)
            speed_score = self._calculate_speed_score(tool, context)
            accuracy_score = self._calculate_accuracy_score(tool, context)
            user_preference_score = self._calculate_user_preference_score(tool, context)
            
            # 计算最终分数
            final_score = (
                weights['relevance'] * relevance_score +
                weights['performance'] * performance_score +
                weights['cost'] * cost_score +
                weights['speed'] * speed_score +
                weights['accuracy'] * accuracy_score +
                weights['user_preference'] * user_preference_score
            )
            
            # 生成选择理由
            reasoning = self._generate_reasoning(
                tool, relevance_score, performance_score, cost_score,
                speed_score, accuracy_score, user_preference_score, strategy
            )
            
            tool_score = ToolScore(
                tool_id=tool.id,
                relevance_score=relevance_score,
                performance_score=performance_score,
                cost_score=cost_score,
                speed_score=speed_score,
                accuracy_score=accuracy_score,
                user_preference_score=user_preference_score,
                final_score=final_score,
                reasoning=reasoning
            )
            
            tool_scores.append(tool_score)
        
        return tool_scores
    
    def _calculate_relevance_score(self, task_requirement: TaskRequirement, tool: MCPTool) -> float:
        """计算相关性分数"""
        score = 0.0
        
        # 任务类型匹配
        if task_requirement.task_type == tool.type:
            score += 0.4
        elif task_requirement.task_type in ['general', 'mixed']:
            score += 0.2
        
        # 能力匹配度
        required_caps = set(task_requirement.required_capabilities)
        tool_caps = set(tool.capabilities)
        if required_caps:
            match_ratio = len(required_caps.intersection(tool_caps)) / len(required_caps)
            score += 0.4 * match_ratio
        
        # 关键词匹配
        task_keywords = task_requirement.description.lower().split()
        tool_keywords = (tool.name + ' ' + tool.description).lower().split()
        keyword_matches = len(set(task_keywords).intersection(set(tool_keywords)))
        if task_keywords:
            keyword_score = min(keyword_matches / len(task_keywords), 1.0)
            score += 0.2 * keyword_score
        
        return min(score, 1.0)
    
    def _calculate_performance_score(self, tool: MCPTool, context: SelectionContext) -> float:
        """计算性能分数"""
        # 基础性能分数
        base_score = tool.performance_score
        
        # 历史使用情况调整
        if tool.usage_count > 0:
            # 使用次数越多，可信度越高
            usage_bonus = min(tool.usage_count / 100.0, 0.2)
            base_score += usage_bonus
        
        # 最近使用情况调整
        if tool.last_used:
            time_since_last_use = time.time() - tool.last_used
            if time_since_last_use < 86400:  # 24小时内使用过
                base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_cost_score(self, tool: MCPTool, context: SelectionContext) -> float:
        """计算成本分数（分数越高表示成本越低）"""
        base_cost = self.cost_model.get(tool.type, 0.5)
        
        # 预算约束调整
        if context.budget_constraints:
            if base_cost > context.budget_constraints:
                return 0.0
        
        # 成本分数（反向，成本越低分数越高）
        cost_score = 1.0 - base_cost
        
        return max(cost_score, 0.0)
    
    def _calculate_speed_score(self, tool: MCPTool, context: SelectionContext) -> float:
        """计算速度分数"""
        # 基于工具类型的速度估计
        speed_mapping = {
            'file': 0.9,        # 文件操作通常很快
            'terminal': 0.8,    # 终端命令较快
            'git': 0.7,         # Git操作中等速度
            'web': 0.6,         # Web请求较慢
            'ai': 0.4,          # AI处理较慢
            'deploy': 0.3,      # 部署操作很慢
            'data': 0.5,        # 数据操作中等
            'api': 0.6,         # API调用中等
            'monitor': 0.7,     # 监控操作较快
            'security': 0.6,    # 安全操作中等
            'general': 0.5      # 通用工具中等
        }
        
        base_speed = speed_mapping.get(tool.type, 0.5)
        
        # 时间约束调整
        if context.time_constraints:
            if context.time_constraints < 10:  # 10秒内需要完成
                if base_speed < 0.7:
                    return 0.0
        
        return base_speed
    
    def _calculate_accuracy_score(self, tool: MCPTool, context: SelectionContext) -> float:
        """计算准确性分数"""
        # 基于工具类型的准确性估计
        accuracy_mapping = {
            'ai': 0.8,          # AI工具准确性较高
            'security': 0.9,    # 安全工具准确性很高
            'data': 0.8,        # 数据工具准确性较高
            'file': 0.9,        # 文件操作准确性很高
            'git': 0.9,         # Git操作准确性很高
            'terminal': 0.8,    # 终端操作准确性较高
            'web': 0.7,         # Web操作准确性中等
            'api': 0.7,         # API调用准确性中等
            'deploy': 0.8,      # 部署操作准确性较高
            'monitor': 0.8,     # 监控操作准确性较高
            'general': 0.7      # 通用工具准确性中等
        }
        
        base_accuracy = accuracy_mapping.get(tool.type, 0.7)
        
        # 历史成功率调整
        if tool.usage_count > 10:
            # 假设有成功率数据（实际应该从历史记录中获取）
            success_rate = 0.85  # 示例值
            base_accuracy = (base_accuracy + success_rate) / 2
        
        return base_accuracy
    
    def _calculate_user_preference_score(self, tool: MCPTool, context: SelectionContext) -> float:
        """计算用户偏好分数"""
        user_id = context.user_id
        
        if user_id not in self.user_preferences:
            return 0.5  # 默认中性偏好
        
        user_prefs = self.user_preferences[user_id]
        
        # 工具使用频率
        tool_usage = user_prefs.get('tool_usage', {})
        if tool.id in tool_usage:
            usage_count = tool_usage[tool.id]
            preference_score = min(usage_count / 50.0, 1.0)  # 最多50次使用达到满分
            return preference_score
        
        # 工具类型偏好
        type_prefs = user_prefs.get('type_preferences', {})
        if tool.type in type_prefs:
            return type_prefs[tool.type]
        
        return 0.5
    
    def _generate_reasoning(
        self,
        tool: MCPTool,
        relevance: float,
        performance: float,
        cost: float,
        speed: float,
        accuracy: float,
        user_pref: float,
        strategy: SelectionStrategy
    ) -> str:
        """生成选择理由"""
        
        reasons = []
        
        # 相关性理由
        if relevance > 0.8:
            reasons.append("高度相关的工具类型和能力")
        elif relevance > 0.6:
            reasons.append("较好的任务匹配度")
        
        # 策略相关理由
        if strategy == SelectionStrategy.PERFORMANCE_FIRST and performance > 0.8:
            reasons.append("优秀的性能表现")
        elif strategy == SelectionStrategy.COST_OPTIMIZED and cost > 0.8:
            reasons.append("成本效益优秀")
        elif strategy == SelectionStrategy.SPEED_FIRST and speed > 0.8:
            reasons.append("执行速度快")
        elif strategy == SelectionStrategy.ACCURACY_FIRST and accuracy > 0.8:
            reasons.append("准确性高")
        
        # 用户偏好理由
        if user_pref > 0.7:
            reasons.append("符合用户使用习惯")
        
        # 历史使用理由
        if tool.usage_count > 50:
            reasons.append("经过大量验证的稳定工具")
        
        if not reasons:
            reasons.append("综合评分较高的工具选择")
        
        return "; ".join(reasons)
    
    async def _generate_recommendations(
        self,
        tool_scores: List[ToolScore],
        task_requirement: TaskRequirement,
        context: SelectionContext
    ) -> List[ToolRecommendation]:
        """生成推荐"""
        
        recommendations = []
        
        for i, score in enumerate(tool_scores):
            recommendation = ToolRecommendation(
                tool_id=score.tool_id,
                confidence_score=score.final_score,
                reasoning=score.reasoning,
                estimated_cost=self._estimate_tool_cost(score.tool_id),
                estimated_time=self._estimate_execution_time(score.tool_id, task_requirement),
                priority=i + 1,
                alternative_tools=self._find_alternative_tools(score.tool_id, tool_scores),
                usage_tips=self._generate_usage_tips(score.tool_id, task_requirement)
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _estimate_tool_cost(self, tool_id: str) -> float:
        """估算工具成本"""
        # 这里应该基于实际的成本模型
        return 0.1  # 示例值
    
    def _estimate_execution_time(self, tool_id: str, task_requirement: TaskRequirement) -> float:
        """估算执行时间"""
        # 这里应该基于历史数据和任务复杂度
        base_time = 5.0  # 基础5秒
        complexity_factor = len(task_requirement.description) / 100.0
        return base_time * (1 + complexity_factor)
    
    def _find_alternative_tools(self, tool_id: str, all_scores: List[ToolScore]) -> List[str]:
        """找到替代工具"""
        alternatives = []
        for score in all_scores:
            if score.tool_id != tool_id and score.final_score > 0.6:
                alternatives.append(score.tool_id)
        return alternatives[:3]  # 最多3个替代工具
    
    def _generate_usage_tips(self, tool_id: str, task_requirement: TaskRequirement) -> List[str]:
        """生成使用提示"""
        tips = [
            "确保工具权限配置正确",
            "检查输入参数格式",
            "建议先在测试环境验证"
        ]
        return tips
    
    async def _record_selection(
        self,
        task_requirement: TaskRequirement,
        recommendations: List[ToolRecommendation],
        context: SelectionContext,
        strategy: SelectionStrategy
    ) -> None:
        """记录选择历史"""
        
        record = {
            'timestamp': time.time(),
            'user_id': context.user_id,
            'session_id': context.session_id,
            'task_type': task_requirement.task_type,
            'strategy': strategy.value,
            'selected_tools': [rec.tool_id for rec in recommendations],
            'top_confidence': recommendations[0].confidence_score if recommendations else 0.0
        }
        
        self.selection_history.append(record)
        
        # 更新用户偏好
        await self._update_user_preferences(context.user_id, recommendations)
    
    async def _update_user_preferences(self, user_id: str, recommendations: List[ToolRecommendation]) -> None:
        """更新用户偏好"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'tool_usage': {},
                'type_preferences': {},
                'strategy_preferences': {}
            }
        
        # 这里应该基于用户的实际使用反馈来更新偏好
        # 目前只是示例实现
        pass
    
    def _estimate_tool_memory(self, tool: MCPTool) -> float:
        """估算工具内存使用"""
        # 基于工具类型的内存估算
        memory_mapping = {
            'ai': 512.0,        # AI工具内存使用较大
            'data': 256.0,      # 数据工具内存使用中等
            'web': 128.0,       # Web工具内存使用中等
            'file': 64.0,       # 文件工具内存使用较小
            'terminal': 32.0,   # 终端工具内存使用很小
            'git': 64.0,        # Git工具内存使用较小
            'deploy': 256.0,    # 部署工具内存使用中等
            'monitor': 128.0,   # 监控工具内存使用中等
            'security': 128.0,  # 安全工具内存使用中等
            'api': 64.0,        # API工具内存使用较小
            'general': 64.0     # 通用工具内存使用较小
        }
        
        return memory_mapping.get(tool.type, 64.0)
    
    def _estimate_tool_cpu(self, tool: MCPTool) -> float:
        """估算工具CPU使用"""
        # 基于工具类型的CPU估算
        cpu_mapping = {
            'ai': 0.8,          # AI工具CPU使用较高
            'data': 0.6,        # 数据工具CPU使用中等
            'deploy': 0.7,      # 部署工具CPU使用较高
            'web': 0.3,         # Web工具CPU使用较低
            'file': 0.2,        # 文件工具CPU使用很低
            'terminal': 0.3,    # 终端工具CPU使用较低
            'git': 0.3,         # Git工具CPU使用较低
            'monitor': 0.4,     # 监控工具CPU使用中等
            'security': 0.5,    # 安全工具CPU使用中等
            'api': 0.2,         # API工具CPU使用较低
            'general': 0.3      # 通用工具CPU使用较低
        }
        
        return cpu_mapping.get(tool.type, 0.3)
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """获取选择统计信息"""
        if not self.selection_history:
            return {'total_selections': 0}
        
        total_selections = len(self.selection_history)
        avg_confidence = sum(record['top_confidence'] for record in self.selection_history) / total_selections
        
        strategy_usage = {}
        for record in self.selection_history:
            strategy = record['strategy']
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        return {
            'total_selections': total_selections,
            'average_confidence': avg_confidence,
            'strategy_usage': strategy_usage,
            'recent_selections': self.selection_history[-10:]
        }


# 智能选择引擎实例
selection_engine = None

def get_selection_engine() -> SmartToolSelectionEngine:
    """获取智能选择引擎实例"""
    global selection_engine
    if selection_engine is None:
        selection_engine = SmartToolSelectionEngine()
    return selection_engine


if __name__ == "__main__":
    # 测试智能选择引擎
    async def test_selection():
        from ..models.tool_models import MCPTool, TaskRequirement, ToolCapability
        
        # 创建测试工具
        test_tools = [
            MCPTool(
                id="test_file_tool",
                name="File Manager",
                description="File operations tool",
                type="file",
                capabilities=[ToolCapability.FILE_OPERATIONS],
                performance_score=0.8,
                usage_count=100
            ),
            MCPTool(
                id="test_ai_tool", 
                name="AI Assistant",
                description="AI-powered assistant",
                type="ai",
                capabilities=[ToolCapability.AI_PROCESSING],
                performance_score=0.9,
                usage_count=50
            )
        ]
        
        # 创建测试任务
        task_req = TaskRequirement(
            task_type="file",
            description="Read and process text files",
            required_capabilities=[ToolCapability.FILE_OPERATIONS],
            priority="high",
            estimated_complexity=0.5
        )
        
        # 创建测试上下文
        context = SelectionContext(
            user_id="test_user",
            session_id="test_session",
            task_history=[],
            user_preferences={},
            resource_constraints={}
        )
        
        # 测试选择
        engine = get_selection_engine()
        recommendations = await engine.select_tools(
            task_req, test_tools, context, SelectionStrategy.BALANCED
        )
        
        print(f"推荐工具数量: {len(recommendations)}")
        for rec in recommendations:
            print(f"工具: {rec.tool_id}, 置信度: {rec.confidence_score:.2f}, 理由: {rec.reasoning}")
    
    asyncio.run(test_selection())

