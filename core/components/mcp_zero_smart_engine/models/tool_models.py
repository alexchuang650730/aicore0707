"""
MCP-Zero Smart Engine 数据模型

定义工具发现和选择系统中使用的所有数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
from datetime import datetime

class ToolType(Enum):
    """工具类型枚举"""
    MCP_SERVER = "mcp_server"
    CLI_TOOL = "cli_tool"
    API_SERVICE = "api_service"
    LIBRARY = "library"
    PLUGIN = "plugin"
    EXTENSION = "extension"

class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"

class ToolStatus(Enum):
    """工具状态枚举"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    MAINTENANCE = "maintenance"

@dataclass
class ToolCapability:
    """工具能力描述"""
    name: str
    description: str
    supported_tasks: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    cost_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'description': self.description,
            'supported_tasks': self.supported_tasks,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'dependencies': self.dependencies,
            'performance_metrics': self.performance_metrics,
            'cost_metrics': self.cost_metrics
        }

@dataclass
class MCPTool:
    """MCP工具定义"""
    id: str
    name: str
    description: str
    version: str
    tool_type: ToolType
    capabilities: ToolCapability
    status: ToolStatus = ToolStatus.AVAILABLE
    
    # 发现信息
    discovery_source: str = ""  # 发现来源 (local, github, registry等)
    discovery_time: datetime = field(default_factory=datetime.now)
    
    # 连接信息
    endpoint: Optional[str] = None
    command: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    author: str = ""
    license: str = ""
    homepage: str = ""
    documentation: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 性能数据
    usage_count: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'tool_type': self.tool_type.value,
            'capabilities': self.capabilities.to_dict(),
            'status': self.status.value,
            'discovery_source': self.discovery_source,
            'discovery_time': self.discovery_time.isoformat(),
            'endpoint': self.endpoint,
            'command': self.command,
            'config': self.config,
            'author': self.author,
            'license': self.license,
            'homepage': self.homepage,
            'documentation': self.documentation,
            'tags': self.tags,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'average_response_time': self.average_response_time,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPTool':
        """从字典创建MCPTool实例"""
        capabilities = ToolCapability(**data['capabilities'])
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            version=data['version'],
            tool_type=ToolType(data['tool_type']),
            capabilities=capabilities,
            status=ToolStatus(data.get('status', 'available')),
            discovery_source=data.get('discovery_source', ''),
            discovery_time=datetime.fromisoformat(data.get('discovery_time', datetime.now().isoformat())),
            endpoint=data.get('endpoint'),
            command=data.get('command'),
            config=data.get('config', {}),
            author=data.get('author', ''),
            license=data.get('license', ''),
            homepage=data.get('homepage', ''),
            documentation=data.get('documentation', ''),
            tags=data.get('tags', []),
            usage_count=data.get('usage_count', 0),
            success_rate=data.get('success_rate', 0.0),
            average_response_time=data.get('average_response_time', 0.0),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None
        )

@dataclass
class TaskRequirement:
    """任务需求定义"""
    description: str
    task_type: str
    complexity: TaskComplexity
    
    # 功能需求
    required_capabilities: List[str]
    preferred_capabilities: List[str] = field(default_factory=list)
    
    # 性能需求
    max_response_time: Optional[float] = None
    min_success_rate: Optional[float] = None
    
    # 成本约束
    budget_constraints: Dict[str, float] = field(default_factory=dict)
    
    # 用户偏好
    preferred_tools: List[str] = field(default_factory=list)
    excluded_tools: List[str] = field(default_factory=list)
    
    # 上下文信息
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'description': self.description,
            'task_type': self.task_type,
            'complexity': self.complexity.value,
            'required_capabilities': self.required_capabilities,
            'preferred_capabilities': self.preferred_capabilities,
            'max_response_time': self.max_response_time,
            'min_success_rate': self.min_success_rate,
            'budget_constraints': self.budget_constraints,
            'preferred_tools': self.preferred_tools,
            'excluded_tools': self.excluded_tools,
            'context': self.context
        }

@dataclass
class SelectedTool:
    """选中的工具"""
    tool: MCPTool
    confidence_score: float
    selection_reason: str
    estimated_cost: float = 0.0
    estimated_performance: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'tool': self.tool.to_dict(),
            'confidence_score': self.confidence_score,
            'selection_reason': self.selection_reason,
            'estimated_cost': self.estimated_cost,
            'estimated_performance': self.estimated_performance
        }

@dataclass
class ToolRecommendation:
    """工具推荐结果"""
    task_requirement: TaskRequirement
    primary_tools: List[SelectedTool]
    alternative_tools: List[SelectedTool] = field(default_factory=list)
    
    # 整体评估
    total_confidence: float = 0.0
    estimated_total_cost: float = 0.0
    estimated_completion_time: float = 0.0
    
    # 推荐元数据
    recommendation_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ai_model_used: str = ""
    selection_strategy: str = ""
    
    # 执行计划
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_requirement': self.task_requirement.to_dict(),
            'primary_tools': [tool.to_dict() for tool in self.primary_tools],
            'alternative_tools': [tool.to_dict() for tool in self.alternative_tools],
            'total_confidence': self.total_confidence,
            'estimated_total_cost': self.estimated_total_cost,
            'estimated_completion_time': self.estimated_completion_time,
            'recommendation_id': self.recommendation_id,
            'timestamp': self.timestamp.isoformat(),
            'ai_model_used': self.ai_model_used,
            'selection_strategy': self.selection_strategy,
            'execution_plan': self.execution_plan
        }
    
    def get_summary(self) -> str:
        """获取推荐摘要"""
        primary_names = [tool.tool.name for tool in self.primary_tools]
        return f"推荐 {len(self.primary_tools)} 个主要工具: {', '.join(primary_names)}"

@dataclass
class ToolRegistry:
    """工具注册表"""
    tools: Dict[str, MCPTool] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def add_tool(self, tool: MCPTool):
        """添加工具到注册表"""
        self.tools[tool.id] = tool
        self.last_updated = datetime.now()
    
    def remove_tool(self, tool_id: str):
        """从注册表移除工具"""
        if tool_id in self.tools:
            del self.tools[tool_id]
            self.last_updated = datetime.now()
    
    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """获取指定工具"""
        return self.tools.get(tool_id)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[MCPTool]:
        """按类型获取工具"""
        return [tool for tool in self.tools.values() if tool.tool_type == tool_type]
    
    def get_tools_by_capability(self, capability: str) -> List[MCPTool]:
        """按能力获取工具"""
        return [
            tool for tool in self.tools.values() 
            if capability in tool.capabilities.supported_tasks
        ]
    
    def search_tools(self, query: str) -> List[MCPTool]:
        """搜索工具"""
        query_lower = query.lower()
        results = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                results.append(tool)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        total_tools = len(self.tools)
        tools_by_type = {}
        tools_by_status = {}
        
        for tool in self.tools.values():
            tool_type = tool.tool_type.value
            status = tool.status.value
            
            tools_by_type[tool_type] = tools_by_type.get(tool_type, 0) + 1
            tools_by_status[status] = tools_by_status.get(status, 0) + 1
        
        return {
            'total_tools': total_tools,
            'tools_by_type': tools_by_type,
            'tools_by_status': tools_by_status,
            'last_updated': self.last_updated.isoformat(),
            'version': self.version
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'tools': {tool_id: tool.to_dict() for tool_id, tool in self.tools.items()},
            'last_updated': self.last_updated.isoformat(),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolRegistry':
        """从字典创建ToolRegistry实例"""
        registry = cls(
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            version=data.get('version', '1.0.0')
        )
        
        for tool_id, tool_data in data.get('tools', {}).items():
            tool = MCPTool.from_dict(tool_data)
            registry.tools[tool_id] = tool
        
        return registry

