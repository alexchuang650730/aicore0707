#!/usr/bin/env python3
"""
Zen MCP工具注册器

管理Zen MCP生态系统中的所有工具，提供工具发现、注册、配置和生命周期管理。
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ToolStatus(Enum):
    """工具状态"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"
    DEPRECATED = "deprecated"

class ToolCategory(Enum):
    """工具分类"""
    CORE_DEVELOPMENT = "core_development"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    QUALITY_ASSURANCE = "quality_assurance"
    DEPLOYMENT_OPERATIONS = "deployment_operations"
    CUSTOM = "custom"

@dataclass
class ToolCapability:
    """工具能力"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    dependencies: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class ToolMetadata:
    """工具元数据"""
    tool_id: str
    name: str
    version: str
    description: str
    category: ToolCategory
    capabilities: List[ToolCapability]
    author: str
    license: str
    homepage: str = ""
    documentation: str = ""
    tags: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolInstance:
    """工具实例"""
    instance_id: str
    tool_id: str
    metadata: ToolMetadata
    status: ToolStatus
    tool_class: Type
    instance: Any = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    performance_stats: Dict[str, Any] = field(default_factory=dict)

class ZenToolRegistry:
    """Zen工具注册器"""
    
    def __init__(self, registry_path: str = "./zen_tool_registry"):
        """初始化工具注册器"""
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # 工具存储
        self.registered_tools: Dict[str, ToolMetadata] = {}
        self.tool_instances: Dict[str, ToolInstance] = {}
        self.tool_classes: Dict[str, Type] = {}
        
        # 分类索引
        self.category_index: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        
        # 能力索引
        self.capability_index: Dict[str, List[str]] = {}
        
        # 依赖图
        self.dependency_graph: Dict[str, List[str]] = {}
        
        # 统计信息
        self.registry_stats = {
            "total_tools": 0,
            "active_tools": 0,
            "total_instances": 0,
            "total_usage": 0,
            "error_rate": 0.0
        }
        
        logger.info("Zen工具注册器初始化完成")
    
    async def register_tool(self, tool_class: Type, metadata: ToolMetadata) -> str:
        """注册工具"""
        tool_id = metadata.tool_id
        
        # 验证工具类
        if not self._validate_tool_class(tool_class):
            raise ValueError(f"工具类 {tool_class.__name__} 不符合Zen MCP规范")
        
        # 检查依赖
        missing_deps = await self._check_dependencies(metadata.capabilities)
        if missing_deps:
            logger.warning(f"工具 {tool_id} 缺少依赖: {missing_deps}")
        
        # 注册工具
        self.registered_tools[tool_id] = metadata
        self.tool_classes[tool_id] = tool_class
        
        # 更新索引
        self._update_category_index(tool_id, metadata.category)
        self._update_capability_index(tool_id, metadata.capabilities)
        self._update_dependency_graph(tool_id, metadata.capabilities)
        
        # 更新统计
        self.registry_stats["total_tools"] += 1
        
        # 持久化注册信息
        await self._persist_tool_metadata(metadata)
        
        logger.info(f"工具 {tool_id} 注册成功")
        return tool_id
    
    async def create_tool_instance(self, tool_id: str, 
                                 config: Dict[str, Any] = None) -> str:
        """创建工具实例"""
        if tool_id not in self.registered_tools:
            raise ValueError(f"工具 {tool_id} 未注册")
        
        tool_class = self.tool_classes[tool_id]
        metadata = self.registered_tools[tool_id]
        
        # 创建实例ID
        instance_id = f"{tool_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            # 合并配置
            final_config = metadata.configuration.copy()
            if config:
                final_config.update(config)
            
            # 创建工具实例
            tool_instance = tool_class(config=final_config)
            
            # 初始化工具
            if hasattr(tool_instance, 'initialize'):
                await tool_instance.initialize()
            
            # 创建实例记录
            instance_record = ToolInstance(
                instance_id=instance_id,
                tool_id=tool_id,
                metadata=metadata,
                status=ToolStatus.ACTIVE,
                tool_class=tool_class,
                instance=tool_instance
            )
            
            self.tool_instances[instance_id] = instance_record
            
            # 更新统计
            self.registry_stats["total_instances"] += 1
            self.registry_stats["active_tools"] += 1
            
            logger.info(f"工具实例 {instance_id} 创建成功")
            return instance_id
            
        except Exception as e:
            logger.error(f"创建工具实例失败 {tool_id}: {e}")
            raise
    
    async def get_tool_instance(self, instance_id: str) -> Optional[Any]:
        """获取工具实例"""
        if instance_id not in self.tool_instances:
            return None
        
        instance_record = self.tool_instances[instance_id]
        
        # 更新使用统计
        instance_record.last_used = datetime.now()
        instance_record.usage_count += 1
        self.registry_stats["total_usage"] += 1
        
        return instance_record.instance
    
    async def execute_tool(self, instance_id: str, method: str, 
                          *args, **kwargs) -> Any:
        """执行工具方法"""
        tool_instance = await self.get_tool_instance(instance_id)
        
        if not tool_instance:
            raise ValueError(f"工具实例 {instance_id} 不存在")
        
        instance_record = self.tool_instances[instance_id]
        
        try:
            # 检查方法是否存在
            if not hasattr(tool_instance, method):
                raise AttributeError(f"工具实例不支持方法 {method}")
            
            # 执行方法
            start_time = datetime.now()
            result = await getattr(tool_instance, method)(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新性能统计
            if method not in instance_record.performance_stats:
                instance_record.performance_stats[method] = {
                    "call_count": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0,
                    "success_count": 0
                }
            
            stats = instance_record.performance_stats[method]
            stats["call_count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["call_count"]
            stats["success_count"] += 1
            
            return result
            
        except Exception as e:
            # 记录错误
            instance_record.error_count += 1
            self._update_error_rate()
            
            logger.error(f"工具执行失败 {instance_id}.{method}: {e}")
            raise
    
    async def discover_tools(self, category: ToolCategory = None, 
                           capabilities: List[str] = None,
                           tags: List[str] = None) -> List[ToolMetadata]:
        """发现工具"""
        results = []
        
        for tool_id, metadata in self.registered_tools.items():
            # 分类过滤
            if category and metadata.category != category:
                continue
            
            # 能力过滤
            if capabilities:
                tool_capabilities = [cap.name for cap in metadata.capabilities]
                if not any(cap in tool_capabilities for cap in capabilities):
                    continue
            
            # 标签过滤
            if tags:
                if not any(tag in metadata.tags for tag in tags):
                    continue
            
            results.append(metadata)
        
        # 按使用频率排序
        results.sort(key=lambda m: self._get_tool_popularity(m.tool_id), reverse=True)
        
        return results
    
    async def recommend_tools(self, task_description: str, 
                            context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """推荐工具"""
        recommendations = []
        
        # 分析任务需求
        task_analysis = self._analyze_task_requirements(task_description, context)
        
        # 查找匹配的工具
        for tool_id, metadata in self.registered_tools.items():
            score = self._calculate_tool_relevance(metadata, task_analysis)
            
            if score > 0.3:  # 相关性阈值
                recommendations.append({
                    "tool_id": tool_id,
                    "metadata": metadata,
                    "relevance_score": score,
                    "recommendation_reason": self._generate_recommendation_reason(
                        metadata, task_analysis, score
                    )
                })
        
        # 按相关性排序
        recommendations.sort(key=lambda r: r["relevance_score"], reverse=True)
        
        return recommendations[:10]  # 返回前10个推荐
    
    async def get_tool_dependencies(self, tool_id: str) -> Dict[str, Any]:
        """获取工具依赖"""
        if tool_id not in self.registered_tools:
            return {}
        
        metadata = self.registered_tools[tool_id]
        dependencies = {
            "direct_dependencies": [],
            "indirect_dependencies": [],
            "dependency_tree": {}
        }
        
        # 收集直接依赖
        for capability in metadata.capabilities:
            dependencies["direct_dependencies"].extend(capability.dependencies)
        
        # 收集间接依赖
        indirect_deps = set()
        for dep in dependencies["direct_dependencies"]:
            indirect_deps.update(self._get_recursive_dependencies(dep))
        
        dependencies["indirect_dependencies"] = list(indirect_deps)
        
        # 构建依赖树
        dependencies["dependency_tree"] = self._build_dependency_tree(tool_id)
        
        return dependencies
    
    async def validate_tool_compatibility(self, tool_ids: List[str]) -> Dict[str, Any]:
        """验证工具兼容性"""
        compatibility_report = {
            "compatible": True,
            "conflicts": [],
            "missing_dependencies": [],
            "recommendations": []
        }
        
        # 检查依赖冲突
        all_dependencies = set()
        for tool_id in tool_ids:
            if tool_id in self.registered_tools:
                tool_deps = await self.get_tool_dependencies(tool_id)
                all_dependencies.update(tool_deps["direct_dependencies"])
        
        # 检查缺失依赖
        for dep in all_dependencies:
            if dep not in self.registered_tools:
                compatibility_report["missing_dependencies"].append(dep)
                compatibility_report["compatible"] = False
        
        # 检查版本冲突
        version_conflicts = self._check_version_conflicts(tool_ids)
        if version_conflicts:
            compatibility_report["conflicts"].extend(version_conflicts)
            compatibility_report["compatible"] = False
        
        # 生成建议
        if not compatibility_report["compatible"]:
            compatibility_report["recommendations"] = self._generate_compatibility_recommendations(
                compatibility_report
            )
        
        return compatibility_report
    
    def _validate_tool_class(self, tool_class: Type) -> bool:
        """验证工具类"""
        required_methods = ['execute', 'get_capabilities', 'get_status']
        
        for method in required_methods:
            if not hasattr(tool_class, method):
                return False
        
        return True
    
    async def _check_dependencies(self, capabilities: List[ToolCapability]) -> List[str]:
        """检查依赖"""
        missing_deps = []
        
        for capability in capabilities:
            for dep in capability.dependencies:
                if dep not in self.registered_tools:
                    missing_deps.append(dep)
        
        return missing_deps
    
    def _update_category_index(self, tool_id: str, category: ToolCategory):
        """更新分类索引"""
        if tool_id not in self.category_index[category]:
            self.category_index[category].append(tool_id)
    
    def _update_capability_index(self, tool_id: str, capabilities: List[ToolCapability]):
        """更新能力索引"""
        for capability in capabilities:
            cap_name = capability.name
            if cap_name not in self.capability_index:
                self.capability_index[cap_name] = []
            
            if tool_id not in self.capability_index[cap_name]:
                self.capability_index[cap_name].append(tool_id)
    
    def _update_dependency_graph(self, tool_id: str, capabilities: List[ToolCapability]):
        """更新依赖图"""
        dependencies = []
        for capability in capabilities:
            dependencies.extend(capability.dependencies)
        
        self.dependency_graph[tool_id] = list(set(dependencies))
    
    def _update_error_rate(self):
        """更新错误率"""
        total_errors = sum(instance.error_count for instance in self.tool_instances.values())
        total_usage = self.registry_stats["total_usage"]
        
        if total_usage > 0:
            self.registry_stats["error_rate"] = total_errors / total_usage
    
    def _get_tool_popularity(self, tool_id: str) -> int:
        """获取工具流行度"""
        popularity = 0
        for instance in self.tool_instances.values():
            if instance.tool_id == tool_id:
                popularity += instance.usage_count
        
        return popularity
    
    def _analyze_task_requirements(self, task_description: str, 
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析任务需求"""
        # 简化的任务分析
        keywords = task_description.lower().split()
        
        analysis = {
            "keywords": keywords,
            "inferred_capabilities": [],
            "complexity": "medium",
            "context": context or {}
        }
        
        # 基于关键词推断所需能力
        capability_mapping = {
            "analyze": ["code_analysis", "static_analysis"],
            "generate": ["code_generation", "template_generation"],
            "debug": ["debugging", "error_detection"],
            "test": ["testing", "unit_testing", "integration_testing"],
            "optimize": ["optimization", "performance_tuning"],
            "format": ["formatting", "code_styling"],
            "deploy": ["deployment", "packaging"],
            "monitor": ["monitoring", "logging"],
            "security": ["security_scanning", "vulnerability_detection"]
        }
        
        for keyword in keywords:
            if keyword in capability_mapping:
                analysis["inferred_capabilities"].extend(capability_mapping[keyword])
        
        return analysis
    
    def _calculate_tool_relevance(self, metadata: ToolMetadata, 
                                task_analysis: Dict[str, Any]) -> float:
        """计算工具相关性"""
        score = 0.0
        
        # 能力匹配
        tool_capabilities = [cap.name for cap in metadata.capabilities]
        inferred_capabilities = task_analysis["inferred_capabilities"]
        
        if inferred_capabilities:
            matches = len(set(tool_capabilities) & set(inferred_capabilities))
            score += (matches / len(inferred_capabilities)) * 0.6
        
        # 关键词匹配
        keywords = task_analysis["keywords"]
        tool_text = f"{metadata.name} {metadata.description} {' '.join(metadata.tags)}".lower()
        
        keyword_matches = sum(1 for keyword in keywords if keyword in tool_text)
        if keywords:
            score += (keyword_matches / len(keywords)) * 0.3
        
        # 流行度加成
        popularity = self._get_tool_popularity(metadata.tool_id)
        if popularity > 0:
            score += min(0.1, popularity / 100.0)
        
        return min(1.0, score)
    
    def _generate_recommendation_reason(self, metadata: ToolMetadata, 
                                      task_analysis: Dict[str, Any], 
                                      score: float) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 能力匹配
        tool_capabilities = [cap.name for cap in metadata.capabilities]
        inferred_capabilities = task_analysis["inferred_capabilities"]
        matches = set(tool_capabilities) & set(inferred_capabilities)
        
        if matches:
            reasons.append(f"具备所需能力: {', '.join(matches)}")
        
        # 流行度
        popularity = self._get_tool_popularity(metadata.tool_id)
        if popularity > 10:
            reasons.append(f"使用频率高 ({popularity} 次)")
        
        # 分类匹配
        if metadata.category != ToolCategory.CUSTOM:
            reasons.append(f"专业 {metadata.category.value} 工具")
        
        return "; ".join(reasons) if reasons else f"相关性评分: {score:.2f}"
    
    def _get_recursive_dependencies(self, tool_id: str) -> set:
        """获取递归依赖"""
        dependencies = set()
        
        if tool_id in self.dependency_graph:
            for dep in self.dependency_graph[tool_id]:
                dependencies.add(dep)
                dependencies.update(self._get_recursive_dependencies(dep))
        
        return dependencies
    
    def _build_dependency_tree(self, tool_id: str) -> Dict[str, Any]:
        """构建依赖树"""
        tree = {"tool_id": tool_id, "dependencies": []}
        
        if tool_id in self.dependency_graph:
            for dep in self.dependency_graph[tool_id]:
                tree["dependencies"].append(self._build_dependency_tree(dep))
        
        return tree
    
    def _check_version_conflicts(self, tool_ids: List[str]) -> List[Dict[str, Any]]:
        """检查版本冲突"""
        # 简化的版本冲突检查
        conflicts = []
        
        # 这里可以实现更复杂的版本兼容性检查
        # 目前返回空列表表示无冲突
        
        return conflicts
    
    def _generate_compatibility_recommendations(self, 
                                              compatibility_report: Dict[str, Any]) -> List[str]:
        """生成兼容性建议"""
        recommendations = []
        
        if compatibility_report["missing_dependencies"]:
            recommendations.append(
                f"安装缺失依赖: {', '.join(compatibility_report['missing_dependencies'])}"
            )
        
        if compatibility_report["conflicts"]:
            recommendations.append("解决版本冲突，考虑使用兼容版本")
        
        return recommendations
    
    async def _persist_tool_metadata(self, metadata: ToolMetadata):
        """持久化工具元数据"""
        metadata_file = self.registry_path / f"{metadata.tool_id}.json"
        
        metadata_dict = asdict(metadata)
        # 处理枚举类型
        metadata_dict["category"] = metadata.category.value
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False, default=str)
    
    async def get_registry_statistics(self) -> Dict[str, Any]:
        """获取注册器统计信息"""
        # 更新活跃工具数
        active_count = sum(1 for instance in self.tool_instances.values() 
                          if instance.status == ToolStatus.ACTIVE)
        self.registry_stats["active_tools"] = active_count
        
        # 分类统计
        category_stats = {}
        for category, tool_ids in self.category_index.items():
            category_stats[category.value] = len(tool_ids)
        
        # 能力统计
        capability_stats = {
            cap: len(tool_ids) for cap, tool_ids in self.capability_index.items()
        }
        
        # 实例统计
        instance_stats = {}
        for instance in self.tool_instances.values():
            status = instance.status.value
            instance_stats[status] = instance_stats.get(status, 0) + 1
        
        return {
            "registry_overview": self.registry_stats,
            "category_distribution": category_stats,
            "capability_distribution": capability_stats,
            "instance_status": instance_stats,
            "top_tools": self._get_top_tools(5)
        }
    
    def _get_top_tools(self, limit: int) -> List[Dict[str, Any]]:
        """获取热门工具"""
        tool_popularity = {}
        
        for tool_id in self.registered_tools.keys():
            tool_popularity[tool_id] = self._get_tool_popularity(tool_id)
        
        # 按流行度排序
        sorted_tools = sorted(tool_popularity.items(), key=lambda x: x[1], reverse=True)
        
        top_tools = []
        for tool_id, popularity in sorted_tools[:limit]:
            metadata = self.registered_tools[tool_id]
            top_tools.append({
                "tool_id": tool_id,
                "name": metadata.name,
                "category": metadata.category.value,
                "usage_count": popularity
            })
        
        return top_tools

