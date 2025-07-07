"""
PowerAutomation 结果整合器

智能整合来自多个执行引擎和智能体的结果：
- 多源结果合并和去重
- 结果质量评估和验证
- 冲突检测和解决
- 最终结果生成和格式化

支持并行执行、流水线执行和混合执行模式的结果整合。
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict

# 导入相关组件
from .task_analyzer import TaskAnalysisResult, TaskType, TaskComplexity
from .intelligent_router import RoutePlan, RouteStep, ExecutionEngine


class ResultType(Enum):
    """结果类型枚举"""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    REPORT = "report"
    ARTIFACT = "artifact"
    LOG = "log"
    METRIC = "metric"
    ERROR = "error"


class ResultQuality(Enum):
    """结果质量枚举"""
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    UNACCEPTABLE = 1


class ConflictType(Enum):
    """冲突类型枚举"""
    CONTENT_MISMATCH = "content_mismatch"
    FORMAT_INCONSISTENCY = "format_inconsistency"
    VERSION_CONFLICT = "version_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    LOGIC_CONTRADICTION = "logic_contradiction"


@dataclass
class ExecutionResult:
    """执行结果数据结构"""
    step_id: str
    engine: ExecutionEngine
    agent: Optional[str]
    mcp: Optional[str]
    result_type: ResultType
    content: Any
    metadata: Dict[str, Any]
    quality_score: float
    execution_time: float
    timestamp: datetime
    success: bool
    error_info: Optional[str] = None


@dataclass
class ResultConflict:
    """结果冲突数据结构"""
    conflict_id: str
    conflict_type: ConflictType
    involved_results: List[str]  # result IDs
    description: str
    severity: int  # 1-5, 5最严重
    resolution_strategy: Optional[str] = None
    resolved: bool = False


@dataclass
class IntegratedResult:
    """整合后的结果"""
    task_id: str
    result_type: ResultType
    content: Any
    metadata: Dict[str, Any]
    quality_score: float
    confidence_score: float
    source_results: List[str]  # source result IDs
    conflicts_resolved: List[str]  # conflict IDs
    integration_method: str
    timestamp: datetime


class ResultIntegrator:
    """
    结果整合器
    
    智能整合来自多个执行引擎和智能体的结果，
    处理冲突、评估质量、生成最终结果。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化结果整合器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 结果存储
        self.execution_results: Dict[str, ExecutionResult] = {}
        self.integrated_results: Dict[str, IntegratedResult] = {}
        self.conflicts: Dict[str, ResultConflict] = {}
        
        # 质量评估器
        self._init_quality_assessors()
        
        # 冲突解决策略
        self._init_conflict_resolvers()
        
        # 统计信息
        self.stats = {
            "total_integrations": 0,
            "successful_integrations": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "average_quality_score": 0.0,
            "by_result_type": defaultdict(int),
            "by_integration_method": defaultdict(int)
        }
        
        self.logger.info("结果整合器初始化完成")
    
    def _init_quality_assessors(self):
        """初始化质量评估器"""
        self.quality_assessors = {
            ResultType.CODE: self._assess_code_quality,
            ResultType.DOCUMENTATION: self._assess_documentation_quality,
            ResultType.CONFIGURATION: self._assess_configuration_quality,
            ResultType.DEPLOYMENT: self._assess_deployment_quality,
            ResultType.ANALYSIS: self._assess_analysis_quality,
            ResultType.REPORT: self._assess_report_quality,
            ResultType.ARTIFACT: self._assess_artifact_quality,
            ResultType.LOG: self._assess_log_quality,
            ResultType.METRIC: self._assess_metric_quality
        }
    
    def _init_conflict_resolvers(self):
        """初始化冲突解决策略"""
        self.conflict_resolvers = {
            ConflictType.CONTENT_MISMATCH: self._resolve_content_mismatch,
            ConflictType.FORMAT_INCONSISTENCY: self._resolve_format_inconsistency,
            ConflictType.VERSION_CONFLICT: self._resolve_version_conflict,
            ConflictType.DEPENDENCY_CONFLICT: self._resolve_dependency_conflict,
            ConflictType.LOGIC_CONTRADICTION: self._resolve_logic_contradiction
        }
    
    async def integrate_results(self, task: Any, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合执行结果
        
        Args:
            task: 任务对象
            execution_results: 执行结果字典
            
        Returns:
            整合后的结果
        """
        try:
            self.logger.info(f"开始整合任务结果: {task.id}")
            
            # 解析和标准化执行结果
            parsed_results = await self._parse_execution_results(task.id, execution_results)
            
            # 质量评估
            await self._assess_results_quality(parsed_results)
            
            # 冲突检测
            conflicts = await self._detect_conflicts(parsed_results)
            
            # 冲突解决
            resolved_conflicts = await self._resolve_conflicts(conflicts, parsed_results)
            
            # 结果整合
            integrated_results = await self._integrate_parsed_results(
                task, parsed_results, resolved_conflicts
            )
            
            # 生成最终结果
            final_result = await self._generate_final_result(
                task, integrated_results, resolved_conflicts
            )
            
            # 更新统计信息
            self._update_integration_stats(integrated_results, True)
            
            self.logger.info(f"任务结果整合完成: {task.id}")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"结果整合失败: {task.id} - {e}")
            self._update_integration_stats({}, False)
            
            # 返回错误结果
            return {
                "success": False,
                "error": str(e),
                "task_id": task.id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _parse_execution_results(self, task_id: str, 
                                     execution_results: Dict[str, Any]) -> List[ExecutionResult]:
        """解析和标准化执行结果"""
        parsed_results = []
        
        for source_key, result_data in execution_results.items():
            try:
                # 解析源信息
                engine_name, agent_name, mcp_name = self._parse_source_key(source_key)
                
                # 确定结果类型
                result_type = self._determine_result_type(result_data)
                
                # 提取内容和元数据
                content, metadata = self._extract_content_metadata(result_data)
                
                # 创建执行结果对象
                execution_result = ExecutionResult(
                    step_id=f"step_{source_key}_{len(parsed_results)}",
                    engine=ExecutionEngine(engine_name) if engine_name else ExecutionEngine.LOCAL_ADAPTER,
                    agent=agent_name,
                    mcp=mcp_name,
                    result_type=result_type,
                    content=content,
                    metadata=metadata,
                    quality_score=0.0,  # 稍后评估
                    execution_time=metadata.get("execution_time", 0.0),
                    timestamp=datetime.now(),
                    success=metadata.get("success", True),
                    error_info=metadata.get("error")
                )
                
                # 存储结果
                self.execution_results[execution_result.step_id] = execution_result
                parsed_results.append(execution_result)
                
            except Exception as e:
                self.logger.warning(f"解析执行结果失败 {source_key}: {e}")
        
        return parsed_results
    
    def _parse_source_key(self, source_key: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """解析源键获取引擎、智能体、MCP信息"""
        parts = source_key.split("_")
        
        engine_name = None
        agent_name = None
        mcp_name = None
        
        # 解析引擎名称
        if "agent" in source_key:
            engine_name = "local_adapter"  # 智能体通过local_adapter执行
            for part in parts:
                if "agent" in part:
                    agent_name = part
        elif "mcp" in source_key:
            for part in parts:
                if "mcp" in part:
                    mcp_name = part
                    # 根据MCP名称推断引擎
                    if "local_adapter" in part:
                        engine_name = "local_adapter"
                    elif "trae_agent" in part:
                        engine_name = "trae_agent"
                    elif "stagewise" in part:
                        engine_name = "stagewise"
                    elif "memoryos" in part:
                        engine_name = "memoryos"
                    elif "web_ui" in part:
                        engine_name = "web_ui"
        else:
            # 默认解析
            if len(parts) > 0:
                engine_name = parts[0]
        
        return engine_name, agent_name, mcp_name
    
    def _determine_result_type(self, result_data: Any) -> ResultType:
        """确定结果类型"""
        if isinstance(result_data, dict):
            # 检查元数据中的类型信息
            if "type" in result_data:
                try:
                    return ResultType(result_data["type"])
                except ValueError:
                    pass
            
            # 根据内容推断类型
            if "code" in result_data or "source_code" in result_data:
                return ResultType.CODE
            elif "documentation" in result_data or "readme" in result_data:
                return ResultType.DOCUMENTATION
            elif "config" in result_data or "configuration" in result_data:
                return ResultType.CONFIGURATION
            elif "deployment" in result_data or "deploy" in result_data:
                return ResultType.DEPLOYMENT
            elif "analysis" in result_data or "report" in result_data:
                return ResultType.ANALYSIS
            elif "metrics" in result_data or "performance" in result_data:
                return ResultType.METRIC
            elif "error" in result_data or "exception" in result_data:
                return ResultType.ERROR
            elif "logs" in result_data or "log" in result_data:
                return ResultType.LOG
        
        # 默认为工件类型
        return ResultType.ARTIFACT
    
    def _extract_content_metadata(self, result_data: Any) -> Tuple[Any, Dict[str, Any]]:
        """提取内容和元数据"""
        if isinstance(result_data, dict):
            # 分离内容和元数据
            content_keys = ["content", "result", "output", "data", "value"]
            metadata_keys = ["metadata", "info", "details", "stats", "metrics"]
            
            content = None
            metadata = {}
            
            # 提取内容
            for key in content_keys:
                if key in result_data:
                    content = result_data[key]
                    break
            
            # 如果没有找到明确的内容键，使用整个数据作为内容
            if content is None:
                content = result_data
            
            # 提取元数据
            for key in metadata_keys:
                if key in result_data:
                    if isinstance(result_data[key], dict):
                        metadata.update(result_data[key])
                    else:
                        metadata[key] = result_data[key]
            
            # 添加其他有用的元数据
            for key, value in result_data.items():
                if key not in content_keys and key not in metadata_keys:
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
            
            return content, metadata
        else:
            # 非字典类型，直接作为内容
            return result_data, {}
    
    async def _assess_results_quality(self, results: List[ExecutionResult]):
        """评估结果质量"""
        for result in results:
            try:
                # 使用对应的质量评估器
                assessor = self.quality_assessors.get(result.result_type, self._assess_default_quality)
                quality_score = await assessor(result)
                
                result.quality_score = quality_score
                
            except Exception as e:
                self.logger.warning(f"质量评估失败 {result.step_id}: {e}")
                result.quality_score = 0.5  # 默认中等质量
    
    async def _assess_code_quality(self, result: ExecutionResult) -> float:
        """评估代码质量"""
        score = 0.5  # 基础分数
        
        if not result.content:
            return 0.1
        
        content = str(result.content)
        
        # 检查代码长度
        if len(content) > 50:
            score += 0.1
        
        # 检查是否包含函数定义
        if "def " in content or "function " in content or "class " in content:
            score += 0.2
        
        # 检查是否有注释
        if "#" in content or "/*" in content or "/**" in content:
            score += 0.1
        
        # 检查是否有错误处理
        if "try" in content or "catch" in content or "except" in content:
            score += 0.1
        
        # 检查语法错误（简单检查）
        if "SyntaxError" in content or "Error:" in content:
            score -= 0.3
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_documentation_quality(self, result: ExecutionResult) -> float:
        """评估文档质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        content = str(result.content)
        
        # 检查文档长度
        if len(content) > 100:
            score += 0.1
        
        # 检查是否有标题
        if "#" in content or "Title:" in content:
            score += 0.1
        
        # 检查是否有示例
        if "example" in content.lower() or "```" in content:
            score += 0.2
        
        # 检查是否有说明
        if "description" in content.lower() or "overview" in content.lower():
            score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_configuration_quality(self, result: ExecutionResult) -> float:
        """评估配置质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        try:
            # 尝试解析JSON/YAML
            if isinstance(result.content, dict):
                score += 0.3
            elif isinstance(result.content, str):
                # 检查是否是有效的JSON或YAML格式
                if result.content.strip().startswith(("{", "[")):
                    json.loads(result.content)
                    score += 0.3
                elif ":" in result.content:
                    score += 0.2  # 可能是YAML
            
            # 检查是否有必要的配置项
            content_str = str(result.content).lower()
            if "host" in content_str or "port" in content_str:
                score += 0.1
            if "database" in content_str or "db" in content_str:
                score += 0.1
            
        except json.JSONDecodeError:
            score -= 0.2
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_deployment_quality(self, result: ExecutionResult) -> float:
        """评估部署质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        content_str = str(result.content).lower()
        
        # 检查部署相关关键词
        deployment_keywords = ["docker", "kubernetes", "deploy", "service", "container"]
        for keyword in deployment_keywords:
            if keyword in content_str:
                score += 0.1
        
        # 检查是否有配置文件
        if "dockerfile" in content_str or "docker-compose" in content_str:
            score += 0.2
        
        # 检查是否有部署脚本
        if "script" in content_str or ".sh" in content_str:
            score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_analysis_quality(self, result: ExecutionResult) -> float:
        """评估分析质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        content_str = str(result.content).lower()
        
        # 检查分析深度
        if len(content_str) > 200:
            score += 0.1
        
        # 检查是否有数据
        if "data" in content_str or "statistics" in content_str:
            score += 0.2
        
        # 检查是否有结论
        if "conclusion" in content_str or "summary" in content_str:
            score += 0.2
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_report_quality(self, result: ExecutionResult) -> float:
        """评估报告质量"""
        return await self._assess_analysis_quality(result)
    
    async def _assess_artifact_quality(self, result: ExecutionResult) -> float:
        """评估工件质量"""
        score = 0.5
        
        if result.content:
            score += 0.3
        
        if result.metadata:
            score += 0.2
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_log_quality(self, result: ExecutionResult) -> float:
        """评估日志质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        content_str = str(result.content).lower()
        
        # 检查日志级别
        log_levels = ["info", "debug", "warn", "error", "fatal"]
        for level in log_levels:
            if level in content_str:
                score += 0.1
        
        # 检查时间戳
        if "timestamp" in content_str or "time" in content_str:
            score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_metric_quality(self, result: ExecutionResult) -> float:
        """评估指标质量"""
        score = 0.5
        
        if not result.content:
            return 0.1
        
        # 检查是否包含数值
        content_str = str(result.content)
        import re
        numbers = re.findall(r'\d+\.?\d*', content_str)
        if numbers:
            score += 0.3
        
        # 检查是否有单位
        units = ["ms", "sec", "mb", "gb", "%", "cpu", "memory"]
        for unit in units:
            if unit in content_str.lower():
                score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _assess_default_quality(self, result: ExecutionResult) -> float:
        """默认质量评估"""
        score = 0.5
        
        if result.content:
            score += 0.2
        
        if result.success:
            score += 0.2
        else:
            score -= 0.3
        
        if result.metadata:
            score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    async def _detect_conflicts(self, results: List[ExecutionResult]) -> List[ResultConflict]:
        """检测结果冲突"""
        conflicts = []
        
        # 按结果类型分组
        results_by_type = defaultdict(list)
        for result in results:
            results_by_type[result.result_type].append(result)
        
        # 检测每种类型内的冲突
        for result_type, type_results in results_by_type.items():
            if len(type_results) > 1:
                type_conflicts = await self._detect_type_conflicts(result_type, type_results)
                conflicts.extend(type_conflicts)
        
        # 检测跨类型冲突
        cross_type_conflicts = await self._detect_cross_type_conflicts(results)
        conflicts.extend(cross_type_conflicts)
        
        # 存储冲突
        for conflict in conflicts:
            self.conflicts[conflict.conflict_id] = conflict
        
        return conflicts
    
    async def _detect_type_conflicts(self, result_type: ResultType, 
                                   results: List[ExecutionResult]) -> List[ResultConflict]:
        """检测同类型结果冲突"""
        conflicts = []
        
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                result1, result2 = results[i], results[j]
                
                # 内容不匹配检测
                if await self._is_content_mismatch(result1, result2):
                    conflict = ResultConflict(
                        conflict_id=f"conflict_{result1.step_id}_{result2.step_id}",
                        conflict_type=ConflictType.CONTENT_MISMATCH,
                        involved_results=[result1.step_id, result2.step_id],
                        description=f"Content mismatch between {result1.step_id} and {result2.step_id}",
                        severity=3
                    )
                    conflicts.append(conflict)
                
                # 格式不一致检测
                if await self._is_format_inconsistent(result1, result2):
                    conflict = ResultConflict(
                        conflict_id=f"format_conflict_{result1.step_id}_{result2.step_id}",
                        conflict_type=ConflictType.FORMAT_INCONSISTENCY,
                        involved_results=[result1.step_id, result2.step_id],
                        description=f"Format inconsistency between {result1.step_id} and {result2.step_id}",
                        severity=2
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_cross_type_conflicts(self, results: List[ExecutionResult]) -> List[ResultConflict]:
        """检测跨类型冲突"""
        conflicts = []
        
        # 检测依赖冲突
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                result1, result2 = results[i], results[j]
                
                if await self._is_dependency_conflict(result1, result2):
                    conflict = ResultConflict(
                        conflict_id=f"dep_conflict_{result1.step_id}_{result2.step_id}",
                        conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                        involved_results=[result1.step_id, result2.step_id],
                        description=f"Dependency conflict between {result1.step_id} and {result2.step_id}",
                        severity=4
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _is_content_mismatch(self, result1: ExecutionResult, result2: ExecutionResult) -> bool:
        """检测内容不匹配"""
        if result1.result_type != result2.result_type:
            return False
        
        content1 = str(result1.content) if result1.content else ""
        content2 = str(result2.content) if result2.content else ""
        
        # 简单的相似度检测
        if len(content1) > 0 and len(content2) > 0:
            # 计算内容相似度
            similarity = self._calculate_similarity(content1, content2)
            return similarity < 0.3  # 相似度低于30%认为是冲突
        
        return False
    
    async def _is_format_inconsistent(self, result1: ExecutionResult, result2: ExecutionResult) -> bool:
        """检测格式不一致"""
        if result1.result_type != result2.result_type:
            return False
        
        # 检查数据类型
        type1 = type(result1.content)
        type2 = type(result2.content)
        
        return type1 != type2
    
    async def _is_dependency_conflict(self, result1: ExecutionResult, result2: ExecutionResult) -> bool:
        """检测依赖冲突"""
        # 检查配置和代码之间的依赖冲突
        if (result1.result_type == ResultType.CONFIGURATION and 
            result2.result_type == ResultType.CODE):
            return await self._check_config_code_conflict(result1, result2)
        
        if (result1.result_type == ResultType.CODE and 
            result2.result_type == ResultType.CONFIGURATION):
            return await self._check_config_code_conflict(result2, result1)
        
        return False
    
    async def _check_config_code_conflict(self, config_result: ExecutionResult, 
                                        code_result: ExecutionResult) -> bool:
        """检查配置和代码冲突"""
        # 简单的依赖检查
        config_str = str(config_result.content).lower()
        code_str = str(code_result.content).lower()
        
        # 检查端口冲突
        import re
        config_ports = re.findall(r'port["\s]*:?\s*(\d+)', config_str)
        code_ports = re.findall(r'port["\s]*:?\s*(\d+)', code_str)
        
        if config_ports and code_ports:
            return set(config_ports) != set(code_ports)
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的Jaccard相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _resolve_conflicts(self, conflicts: List[ResultConflict], 
                               results: List[ExecutionResult]) -> List[ResultConflict]:
        """解决冲突"""
        resolved_conflicts = []
        
        for conflict in conflicts:
            try:
                resolver = self.conflict_resolvers.get(conflict.conflict_type)
                if resolver:
                    resolved = await resolver(conflict, results)
                    if resolved:
                        conflict.resolved = True
                        conflict.resolution_strategy = resolved
                        resolved_conflicts.append(conflict)
                        
                        self.stats["conflicts_resolved"] += 1
                
            except Exception as e:
                self.logger.warning(f"冲突解决失败 {conflict.conflict_id}: {e}")
        
        return resolved_conflicts
    
    async def _resolve_content_mismatch(self, conflict: ResultConflict, 
                                      results: List[ExecutionResult]) -> Optional[str]:
        """解决内容不匹配冲突"""
        involved_results = [r for r in results if r.step_id in conflict.involved_results]
        
        if len(involved_results) != 2:
            return None
        
        result1, result2 = involved_results
        
        # 选择质量更高的结果
        if result1.quality_score > result2.quality_score:
            return f"选择质量更高的结果: {result1.step_id}"
        elif result2.quality_score > result1.quality_score:
            return f"选择质量更高的结果: {result2.step_id}"
        else:
            # 质量相同，选择更新的结果
            if result1.timestamp > result2.timestamp:
                return f"选择更新的结果: {result1.step_id}"
            else:
                return f"选择更新的结果: {result2.step_id}"
    
    async def _resolve_format_inconsistency(self, conflict: ResultConflict, 
                                          results: List[ExecutionResult]) -> Optional[str]:
        """解决格式不一致冲突"""
        return "统一格式为JSON格式"
    
    async def _resolve_version_conflict(self, conflict: ResultConflict, 
                                      results: List[ExecutionResult]) -> Optional[str]:
        """解决版本冲突"""
        return "使用最新版本"
    
    async def _resolve_dependency_conflict(self, conflict: ResultConflict, 
                                         results: List[ExecutionResult]) -> Optional[str]:
        """解决依赖冲突"""
        return "更新依赖配置以保持一致性"
    
    async def _resolve_logic_contradiction(self, conflict: ResultConflict, 
                                         results: List[ExecutionResult]) -> Optional[str]:
        """解决逻辑矛盾冲突"""
        return "选择逻辑更合理的结果"
    
    async def _integrate_parsed_results(self, task: Any, results: List[ExecutionResult],
                                      resolved_conflicts: List[ResultConflict]) -> Dict[str, IntegratedResult]:
        """整合解析后的结果"""
        integrated_results = {}
        
        # 按结果类型分组
        results_by_type = defaultdict(list)
        for result in results:
            if result.success:  # 只整合成功的结果
                results_by_type[result.result_type].append(result)
        
        # 为每种类型整合结果
        for result_type, type_results in results_by_type.items():
            try:
                integrated_result = await self._integrate_type_results(
                    task.id, result_type, type_results, resolved_conflicts
                )
                
                if integrated_result:
                    integrated_results[result_type.value] = integrated_result
                    self.integrated_results[integrated_result.task_id + "_" + result_type.value] = integrated_result
                
            except Exception as e:
                self.logger.warning(f"整合类型结果失败 {result_type.value}: {e}")
        
        return integrated_results
    
    async def _integrate_type_results(self, task_id: str, result_type: ResultType,
                                    results: List[ExecutionResult],
                                    resolved_conflicts: List[ResultConflict]) -> Optional[IntegratedResult]:
        """整合同类型结果"""
        if not results:
            return None
        
        if len(results) == 1:
            # 单个结果，直接使用
            result = results[0]
            return IntegratedResult(
                task_id=task_id,
                result_type=result_type,
                content=result.content,
                metadata=result.metadata,
                quality_score=result.quality_score,
                confidence_score=result.quality_score,
                source_results=[result.step_id],
                conflicts_resolved=[],
                integration_method="single_result",
                timestamp=datetime.now()
            )
        
        # 多个结果，需要整合
        integration_method = self._determine_integration_method(result_type, results)
        
        if integration_method == "merge":
            return await self._merge_results(task_id, result_type, results, resolved_conflicts)
        elif integration_method == "select_best":
            return await self._select_best_result(task_id, result_type, results, resolved_conflicts)
        elif integration_method == "combine":
            return await self._combine_results(task_id, result_type, results, resolved_conflicts)
        else:
            # 默认选择最佳结果
            return await self._select_best_result(task_id, result_type, results, resolved_conflicts)
    
    def _determine_integration_method(self, result_type: ResultType, 
                                    results: List[ExecutionResult]) -> str:
        """确定整合方法"""
        if result_type in [ResultType.CODE, ResultType.CONFIGURATION]:
            return "select_best"  # 代码和配置选择最佳
        elif result_type in [ResultType.DOCUMENTATION, ResultType.ANALYSIS]:
            return "merge"  # 文档和分析可以合并
        elif result_type in [ResultType.METRIC, ResultType.LOG]:
            return "combine"  # 指标和日志可以组合
        else:
            return "select_best"  # 默认选择最佳
    
    async def _merge_results(self, task_id: str, result_type: ResultType,
                           results: List[ExecutionResult],
                           resolved_conflicts: List[ResultConflict]) -> IntegratedResult:
        """合并结果"""
        merged_content = []
        merged_metadata = {}
        total_quality = 0.0
        
        for result in results:
            if isinstance(result.content, str):
                merged_content.append(result.content)
            elif isinstance(result.content, list):
                merged_content.extend(result.content)
            else:
                merged_content.append(str(result.content))
            
            # 合并元数据
            merged_metadata.update(result.metadata)
            total_quality += result.quality_score
        
        # 计算平均质量
        avg_quality = total_quality / len(results)
        
        # 合并内容
        if result_type == ResultType.DOCUMENTATION:
            final_content = "\n\n".join(merged_content)
        else:
            final_content = merged_content
        
        return IntegratedResult(
            task_id=task_id,
            result_type=result_type,
            content=final_content,
            metadata=merged_metadata,
            quality_score=avg_quality,
            confidence_score=avg_quality * 0.9,  # 合并结果置信度略低
            source_results=[r.step_id for r in results],
            conflicts_resolved=[c.conflict_id for c in resolved_conflicts],
            integration_method="merge",
            timestamp=datetime.now()
        )
    
    async def _select_best_result(self, task_id: str, result_type: ResultType,
                                results: List[ExecutionResult],
                                resolved_conflicts: List[ResultConflict]) -> IntegratedResult:
        """选择最佳结果"""
        # 按质量分数排序
        sorted_results = sorted(results, key=lambda r: r.quality_score, reverse=True)
        best_result = sorted_results[0]
        
        return IntegratedResult(
            task_id=task_id,
            result_type=result_type,
            content=best_result.content,
            metadata=best_result.metadata,
            quality_score=best_result.quality_score,
            confidence_score=best_result.quality_score,
            source_results=[best_result.step_id],
            conflicts_resolved=[c.conflict_id for c in resolved_conflicts],
            integration_method="select_best",
            timestamp=datetime.now()
        )
    
    async def _combine_results(self, task_id: str, result_type: ResultType,
                             results: List[ExecutionResult],
                             resolved_conflicts: List[ResultConflict]) -> IntegratedResult:
        """组合结果"""
        combined_content = {}
        combined_metadata = {}
        total_quality = 0.0
        
        for i, result in enumerate(results):
            combined_content[f"source_{i}"] = result.content
            combined_metadata.update(result.metadata)
            total_quality += result.quality_score
        
        avg_quality = total_quality / len(results)
        
        return IntegratedResult(
            task_id=task_id,
            result_type=result_type,
            content=combined_content,
            metadata=combined_metadata,
            quality_score=avg_quality,
            confidence_score=avg_quality * 0.95,
            source_results=[r.step_id for r in results],
            conflicts_resolved=[c.conflict_id for c in resolved_conflicts],
            integration_method="combine",
            timestamp=datetime.now()
        )
    
    async def _generate_final_result(self, task: Any, integrated_results: Dict[str, IntegratedResult],
                                   resolved_conflicts: List[ResultConflict]) -> Dict[str, Any]:
        """生成最终结果"""
        final_result = {
            "success": True,
            "task_id": task.id,
            "timestamp": datetime.now().isoformat(),
            "results": {},
            "metadata": {
                "integration_summary": {
                    "total_results": len(integrated_results),
                    "conflicts_detected": len(self.conflicts),
                    "conflicts_resolved": len(resolved_conflicts),
                    "integration_methods": {}
                }
            }
        }
        
        # 添加整合后的结果
        for result_type, integrated_result in integrated_results.items():
            final_result["results"][result_type] = {
                "content": integrated_result.content,
                "metadata": integrated_result.metadata,
                "quality_score": integrated_result.quality_score,
                "confidence_score": integrated_result.confidence_score,
                "source_results": integrated_result.source_results,
                "integration_method": integrated_result.integration_method
            }
            
            # 统计整合方法
            method = integrated_result.integration_method
            final_result["metadata"]["integration_summary"]["integration_methods"][method] = \
                final_result["metadata"]["integration_summary"]["integration_methods"].get(method, 0) + 1
        
        # 添加冲突信息
        if resolved_conflicts:
            final_result["metadata"]["conflicts_resolved"] = [
                {
                    "conflict_id": c.conflict_id,
                    "type": c.conflict_type.value,
                    "description": c.description,
                    "resolution": c.resolution_strategy
                }
                for c in resolved_conflicts
            ]
        
        # 计算整体质量和置信度
        if integrated_results:
            avg_quality = sum(r.quality_score for r in integrated_results.values()) / len(integrated_results)
            avg_confidence = sum(r.confidence_score for r in integrated_results.values()) / len(integrated_results)
            
            final_result["metadata"]["overall_quality"] = avg_quality
            final_result["metadata"]["overall_confidence"] = avg_confidence
        
        return final_result
    
    def _update_integration_stats(self, integrated_results: Dict[str, IntegratedResult], success: bool):
        """更新整合统计信息"""
        self.stats["total_integrations"] += 1
        
        if success:
            self.stats["successful_integrations"] += 1
            
            # 更新按结果类型统计
            for result_type, result in integrated_results.items():
                self.stats["by_result_type"][result_type] += 1
                self.stats["by_integration_method"][result.integration_method] += 1
            
            # 更新平均质量分数
            if integrated_results:
                total_quality = sum(r.quality_score for r in integrated_results.values())
                avg_quality = total_quality / len(integrated_results)
                
                total_integrations = self.stats["successful_integrations"]
                current_avg = self.stats["average_quality_score"]
                self.stats["average_quality_score"] = (
                    (current_avg * (total_integrations - 1) + avg_quality) / total_integrations
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return dict(self.stats)
    
    def get_conflicts(self) -> Dict[str, Dict[str, Any]]:
        """获取冲突信息"""
        return {
            conflict_id: asdict(conflict) 
            for conflict_id, conflict in self.conflicts.items()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "stats": self.get_stats(),
            "total_results": len(self.execution_results),
            "total_integrated": len(self.integrated_results),
            "total_conflicts": len(self.conflicts),
            "resolved_conflicts": len([c for c in self.conflicts.values() if c.resolved])
        }


if __name__ == "__main__":
    # 测试结果整合器
    import asyncio
    
    async def test_result_integrator():
        integrator = ResultIntegrator()
        
        # 模拟任务
        class MockTask:
            def __init__(self, task_id):
                self.id = task_id
        
        task = MockTask("test_task_1")
        
        # 模拟执行结果
        execution_results = {
            "agent_developer": {
                "type": "code",
                "content": "def hello_world():\n    print('Hello, World!')",
                "metadata": {"success": True, "execution_time": 2.5}
            },
            "mcp_stagewise": {
                "type": "code", 
                "content": "function helloWorld() {\n    console.log('Hello, World!');\n}",
                "metadata": {"success": True, "execution_time": 1.8}
            },
            "agent_architect": {
                "type": "documentation",
                "content": "# Hello World Function\n\nThis function prints a greeting message.",
                "metadata": {"success": True, "execution_time": 1.2}
            }
        }
        
        print("测试结果整合器...")
        
        # 整合结果
        final_result = await integrator.integrate_results(task, execution_results)
        
        print(f"整合成功: {final_result['success']}")
        print(f"结果类型数: {len(final_result['results'])}")
        
        for result_type, result_data in final_result["results"].items():
            print(f"\n{result_type}:")
            print(f"  质量分数: {result_data['quality_score']:.2f}")
            print(f"  置信度: {result_data['confidence_score']:.2f}")
            print(f"  整合方法: {result_data['integration_method']}")
            print(f"  源结果: {result_data['source_results']}")
        
        # 显示统计信息
        print(f"\n统计信息: {integrator.get_stats()}")
        
        # 显示冲突信息
        conflicts = integrator.get_conflicts()
        if conflicts:
            print(f"检测到冲突: {len(conflicts)}")
            for conflict_id, conflict in conflicts.items():
                print(f"  {conflict_id}: {conflict['description']}")
    
    # 运行测试
    asyncio.run(test_result_integrator())

