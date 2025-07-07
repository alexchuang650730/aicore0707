"""
统一工具管理接口

整合MCP-Zero发现引擎和Smart Tool Engine，提供：
- 统一的工具管理API
- 工具生命周期管理
- 实时工具状态监控
- 工具使用分析和优化
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

from ..discovery import get_discovery_engine, MCPZeroDiscoveryEngine
from ..selection import get_selection_engine, SmartToolSelectionEngine, SelectionStrategy, SelectionContext
from ..models.tool_models import MCPTool, TaskRequirement, ToolRecommendation, ToolCapability


@dataclass
class ToolManagerConfig:
    """工具管理器配置"""
    auto_discovery: bool = True
    discovery_interval: int = 300  # 5分钟
    max_concurrent_tools: int = 50
    tool_timeout: int = 300  # 5分钟
    enable_analytics: bool = True
    enable_caching: bool = True


class UnifiedToolManager:
    """统一工具管理器"""
    
    def __init__(self, config: ToolManagerConfig = None):
        self.config = config or ToolManagerConfig()
        self.logger = logging.getLogger(__name__)
        
        # 核心引擎
        self.discovery_engine = get_discovery_engine()
        self.selection_engine = get_selection_engine()
        
        # 工具状态管理
        self.active_tools: Dict[str, Dict] = {}
        self.tool_registry: Dict[str, MCPTool] = {}
        self.execution_history: List[Dict] = []
        self.tool_analytics: Dict[str, Dict] = {}
        
        # 缓存和优化
        self.recommendation_cache: Dict[str, List[ToolRecommendation]] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        
        # 状态标志
        self.is_running = False
        self.background_tasks = []
    
    async def initialize(self) -> None:
        """初始化工具管理器"""
        self.logger.info("初始化统一工具管理器")
        
        # 启动发现引擎
        await self.discovery_engine.start_discovery()
        
        # 初始化工具注册表
        await self._initialize_tool_registry()
        
        # 启动后台任务
        if self.config.auto_discovery:
            self.background_tasks.append(
                asyncio.create_task(self._background_discovery())
            )
        
        if self.config.enable_analytics:
            self.background_tasks.append(
                asyncio.create_task(self._background_analytics())
            )
        
        self.is_running = True
        self.logger.info("统一工具管理器初始化完成")
    
    async def shutdown(self) -> None:
        """关闭工具管理器"""
        self.logger.info("关闭统一工具管理器")
        self.is_running = False
        
        # 停止发现引擎
        await self.discovery_engine.stop_discovery()
        
        # 取消后台任务
        for task in self.background_tasks:
            task.cancel()
        
        # 清理活跃工具
        await self._cleanup_active_tools()
    
    async def _initialize_tool_registry(self) -> None:
        """初始化工具注册表"""
        # 从发现引擎获取已发现的工具
        discovered_tools = self.discovery_engine.get_discovered_tools()
        self.tool_registry.update(discovered_tools)
        
        self.logger.info(f"工具注册表初始化完成，共{len(self.tool_registry)}个工具")
    
    async def discover_tools(self, force_scan: bool = False) -> Dict[str, Any]:
        """发现工具"""
        self.logger.info(f"开始工具发现，强制扫描: {force_scan}")
        
        if force_scan:
            scan_results = await self.discovery_engine.full_scan()
        else:
            scan_results = {'new_tools': [], 'updated_tools': [], 'removed_tools': []}
        
        # 更新工具注册表
        discovered_tools = self.discovery_engine.get_discovered_tools()
        self.tool_registry.update(discovered_tools)
        
        # 返回发现结果
        return {
            'total_tools': len(self.tool_registry),
            'new_tools': len(scan_results['new_tools']),
            'updated_tools': len(scan_results['updated_tools']),
            'removed_tools': len(scan_results['removed_tools']),
            'scan_timestamp': time.time()
        }
    
    async def recommend_tools(
        self,
        task_description: str,
        task_type: str = "general",
        required_capabilities: List[str] = None,
        user_id: str = "default",
        session_id: str = None,
        strategy: str = "balanced",
        max_recommendations: int = 5,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """推荐工具"""
        
        # 生成缓存键
        cache_key = f"{task_type}_{hash(task_description)}_{strategy}_{max_recommendations}"
        
        # 检查缓存
        if use_cache and self.config.enable_caching and cache_key in self.recommendation_cache:
            cached_recommendations = self.recommendation_cache[cache_key]
            self.logger.info(f"使用缓存推荐，任务: {task_description[:50]}...")
            return [self._recommendation_to_dict(rec) for rec in cached_recommendations]
        
        # 创建任务需求
        capabilities = []
        if required_capabilities:
            for cap_str in required_capabilities:
                try:
                    capabilities.append(ToolCapability[cap_str.upper()])
                except KeyError:
                    self.logger.warning(f"未知的能力类型: {cap_str}")
        
        task_requirement = TaskRequirement(
            task_type=task_type,
            description=task_description,
            required_capabilities=capabilities,
            priority="medium",
            estimated_complexity=0.5
        )
        
        # 创建选择上下文
        context = SelectionContext(
            user_id=user_id,
            session_id=session_id or f"session_{int(time.time())}",
            task_history=[],
            user_preferences=self._get_user_preferences(user_id),
            resource_constraints={}
        )
        
        # 选择策略
        try:
            selection_strategy = SelectionStrategy[strategy.upper()]
        except KeyError:
            selection_strategy = SelectionStrategy.BALANCED
        
        # 获取可用工具
        available_tools = list(self.tool_registry.values())
        
        # 执行智能选择
        recommendations = await self.selection_engine.select_tools(
            task_requirement=task_requirement,
            available_tools=available_tools,
            context=context,
            strategy=selection_strategy,
            max_tools=max_recommendations
        )
        
        # 缓存结果
        if self.config.enable_caching:
            self.recommendation_cache[cache_key] = recommendations
        
        # 记录推荐历史
        await self._record_recommendation(task_requirement, recommendations, context)
        
        self.logger.info(f"完成工具推荐，任务: {task_description[:50]}..., 推荐数量: {len(recommendations)}")
        
        return [self._recommendation_to_dict(rec) for rec in recommendations]
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        user_id: str = "default",
        session_id: str = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """执行工具"""
        
        if tool_id not in self.tool_registry:
            raise ValueError(f"工具不存在: {tool_id}")
        
        tool = self.tool_registry[tool_id]
        execution_timeout = timeout or self.config.tool_timeout
        
        self.logger.info(f"开始执行工具: {tool.name} ({tool_id})")
        
        # 创建执行记录
        execution_id = f"exec_{int(time.time())}_{hash(tool_id) % 10000}"
        execution_record = {
            'execution_id': execution_id,
            'tool_id': tool_id,
            'tool_name': tool.name,
            'user_id': user_id,
            'session_id': session_id,
            'parameters': parameters,
            'start_time': time.time(),
            'status': 'running'
        }
        
        self.active_tools[execution_id] = execution_record
        
        try:
            # 真实工具执行逻辑
            result = await self._execute_real_tool(tool, parameters, execution_timeout)
            
            # 更新执行记录
            execution_record.update({
                'status': 'completed',
                'end_time': time.time(),
                'result': result,
                'success': True
            })
            
            # 更新工具使用统计
            await self._update_tool_usage(tool_id, True)
            
            self.logger.info(f"工具执行成功: {tool.name}")
            
            return {
                'execution_id': execution_id,
                'status': 'completed',
                'result': result,
                'execution_time': execution_record['end_time'] - execution_record['start_time']
            }
            
        except Exception as e:
            # 更新执行记录
            execution_record.update({
                'status': 'failed',
                'end_time': time.time(),
                'error': str(e),
                'success': False
            })
            
            # 更新工具使用统计
            await self._update_tool_usage(tool_id, False)
            
            self.logger.error(f"工具执行失败: {tool.name}, 错误: {e}")
            
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': execution_record['end_time'] - execution_record['start_time']
            }
            
        finally:
            # 移动到历史记录
            self.execution_history.append(execution_record)
            if execution_id in self.active_tools:
                del self.active_tools[execution_id]
    
    async def _execute_real_tool(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """执行真实工具"""
        
        # 根据工具类型执行真实的工具
        if tool.type == 'python':
            return await self._execute_python_tool(tool, parameters, timeout)
        elif tool.type == 'mcp_server':
            return await self._execute_mcp_tool(tool, parameters, timeout)
        elif tool.type == 'executable':
            return await self._execute_executable_tool(tool, parameters, timeout)
        else:
            raise NotImplementedError(f"工具类型 {tool.type} 的执行尚未实现")
    
    async def _execute_python_tool(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """执行Python工具"""
        import subprocess
        import asyncio
        
        try:
            # 构建Python执行命令
            source_path = tool.metadata.source_path
            cmd = ['python3', source_path]
            
            # 添加参数
            for key, value in parameters.items():
                cmd.extend([f'--{key}', str(value)])
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'output': stdout.decode('utf-8'),
                    'return_code': process.returncode
                }
            else:
                raise Exception(f"Python工具执行失败: {stderr.decode('utf-8')}")
                
        except asyncio.TimeoutError:
            raise Exception(f"Python工具执行超时 ({timeout}秒)")
        except Exception as e:
            raise Exception(f"Python工具执行错误: {str(e)}")
    
    async def _execute_mcp_tool(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """执行MCP工具"""
        # 这里应该实现真实的MCP工具调用
        # 需要根据MCP协议进行通信
        raise NotImplementedError("MCP工具执行需要实现MCP协议通信")
    
    async def _execute_executable_tool(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """执行可执行文件工具"""
        import subprocess
        import asyncio
        
        try:
            # 构建执行命令
            cmd = [tool.metadata.source_path]
            
            # 添加参数
            for key, value in parameters.items():
                if key.startswith('--'):
                    cmd.extend([key, str(value)])
                else:
                    cmd.extend([f'--{key}', str(value)])
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'output': stdout.decode('utf-8'),
                    'return_code': process.returncode
                }
            else:
                raise Exception(f"可执行文件执行失败: {stderr.decode('utf-8')}")
                
        except asyncio.TimeoutError:
            raise Exception(f"可执行文件执行超时 ({timeout}秒)")
        except Exception as e:
            raise Exception(f"可执行文件执行错误: {str(e)}")
    
    async def get_tool_status(self, tool_id: str) -> Dict[str, Any]:
        """获取工具状态"""
        
        if tool_id not in self.tool_registry:
            raise ValueError(f"工具不存在: {tool_id}")
        
        tool = self.tool_registry[tool_id]
        
        # 获取工具分析数据
        analytics = self.tool_analytics.get(tool_id, {})
        
        # 获取性能指标
        performance = self.performance_metrics.get(tool_id, {})
        
        return {
            'tool_id': tool_id,
            'name': tool.name,
            'type': tool.type,
            'is_active': tool.is_active,
            'usage_count': tool.usage_count,
            'last_used': tool.last_used,
            'performance_score': tool.performance_score,
            'success_rate': analytics.get('success_rate', 0.0),
            'average_execution_time': analytics.get('avg_execution_time', 0.0),
            'total_executions': analytics.get('total_executions', 0),
            'recent_errors': analytics.get('recent_errors', []),
            'performance_trend': performance.get('trend', 'stable')
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        
        # 工具统计
        total_tools = len(self.tool_registry)
        active_tools = len([t for t in self.tool_registry.values() if t.is_active])
        
        # 类型分布
        type_distribution = {}
        for tool in self.tool_registry.values():
            type_distribution[tool.type] = type_distribution.get(tool.type, 0) + 1
        
        # 执行统计
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.get('success', False)])
        
        # 发现引擎统计
        discovery_stats = self.discovery_engine.get_scan_statistics()
        
        # 选择引擎统计
        selection_stats = self.selection_engine.get_selection_statistics()
        
        return {
            'system_status': 'running' if self.is_running else 'stopped',
            'tools': {
                'total': total_tools,
                'active': active_tools,
                'type_distribution': type_distribution
            },
            'executions': {
                'total': total_executions,
                'successful': successful_executions,
                'success_rate': successful_executions / max(total_executions, 1),
                'active_executions': len(self.active_tools)
            },
            'discovery_engine': discovery_stats,
            'selection_engine': selection_stats,
            'cache': {
                'recommendation_cache_size': len(self.recommendation_cache),
                'performance_cache_size': len(self.performance_metrics)
            },
            'timestamp': time.time()
        }
    
    def _recommendation_to_dict(self, recommendation: ToolRecommendation) -> Dict[str, Any]:
        """将推荐对象转换为字典"""
        tool = self.tool_registry.get(recommendation.tool_id)
        
        return {
            'tool_id': recommendation.tool_id,
            'tool_name': tool.name if tool else 'Unknown',
            'tool_type': tool.type if tool else 'unknown',
            'confidence_score': recommendation.confidence_score,
            'reasoning': recommendation.reasoning,
            'estimated_cost': recommendation.estimated_cost,
            'estimated_time': recommendation.estimated_time,
            'priority': recommendation.priority,
            'alternative_tools': recommendation.alternative_tools,
            'usage_tips': recommendation.usage_tips,
            'tool_description': tool.description if tool else '',
            'tool_capabilities': [cap.value for cap in tool.capabilities] if tool else []
        }
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好"""
        # 这里应该从数据库或配置文件中获取用户偏好
        return {
            'preferred_tools': [],
            'blacklist': [],
            'whitelist': [],
            'strategy_preference': 'balanced'
        }
    
    async def _record_recommendation(
        self,
        task_requirement: TaskRequirement,
        recommendations: List[ToolRecommendation],
        context: SelectionContext
    ) -> None:
        """记录推荐历史"""
        record = {
            'timestamp': time.time(),
            'user_id': context.user_id,
            'session_id': context.session_id,
            'task_type': task_requirement.task_type,
            'task_description': task_requirement.description,
            'recommendations': [rec.tool_id for rec in recommendations],
            'top_confidence': recommendations[0].confidence_score if recommendations else 0.0
        }
        
        # 这里应该保存到数据库
        pass
    
    async def _update_tool_usage(self, tool_id: str, success: bool) -> None:
        """更新工具使用统计"""
        if tool_id in self.tool_registry:
            tool = self.tool_registry[tool_id]
            tool.usage_count += 1
            tool.last_used = time.time()
            
            # 更新分析数据
            if tool_id not in self.tool_analytics:
                self.tool_analytics[tool_id] = {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'execution_times': [],
                    'recent_errors': []
                }
            
            analytics = self.tool_analytics[tool_id]
            analytics['total_executions'] += 1
            
            if success:
                analytics['successful_executions'] += 1
            else:
                analytics['failed_executions'] += 1
            
            # 计算成功率
            analytics['success_rate'] = analytics['successful_executions'] / analytics['total_executions']
    
    async def _background_discovery(self) -> None:
        """后台工具发现任务"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.discovery_interval)
                if self.is_running:
                    await self.discover_tools(force_scan=False)
            except Exception as e:
                self.logger.error(f"后台发现任务错误: {e}")
    
    async def _background_analytics(self) -> None:
        """后台分析任务"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 每分钟运行一次
                if self.is_running:
                    await self._update_performance_metrics()
            except Exception as e:
                self.logger.error(f"后台分析任务错误: {e}")
    
    async def _update_performance_metrics(self) -> None:
        """更新性能指标"""
        for tool_id, analytics in self.tool_analytics.items():
            if analytics['total_executions'] > 0:
                # 计算平均执行时间
                if analytics['execution_times']:
                    avg_time = sum(analytics['execution_times']) / len(analytics['execution_times'])
                    analytics['avg_execution_time'] = avg_time
                
                # 更新性能趋势
                if tool_id not in self.performance_metrics:
                    self.performance_metrics[tool_id] = {'trend': 'stable', 'history': []}
                
                # 这里可以添加更复杂的性能分析逻辑
    
    async def _cleanup_active_tools(self) -> None:
        """清理活跃工具"""
        for execution_id, record in list(self.active_tools.items()):
            record['status'] = 'cancelled'
            record['end_time'] = time.time()
            self.execution_history.append(record)
        
        self.active_tools.clear()


# 全局工具管理器实例
tool_manager = None

def get_tool_manager() -> UnifiedToolManager:
    """获取工具管理器实例"""
    global tool_manager
    if tool_manager is None:
        tool_manager = UnifiedToolManager()
    return tool_manager


# Flask API 应用
def create_api_app() -> Flask:
    """创建API应用"""
    app = Flask(__name__)
    CORS(app)  # 启用CORS
    
    manager = get_tool_manager()
    
    @app.route('/api/tools/discover', methods=['POST'])
    def discover_tools():
        """发现工具API"""
        try:
            data = request.get_json() or {}
            force_scan = data.get('force_scan', False)
            
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(manager.discover_tools(force_scan))
            loop.close()
            
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/recommend', methods=['POST'])
    def recommend_tools():
        """推荐工具API"""
        try:
            data = request.get_json()
            if not data or 'task_description' not in data:
                return jsonify({'success': False, 'error': '缺少task_description参数'}), 400
            
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(manager.recommend_tools(
                task_description=data['task_description'],
                task_type=data.get('task_type', 'general'),
                required_capabilities=data.get('required_capabilities', []),
                user_id=data.get('user_id', 'default'),
                session_id=data.get('session_id'),
                strategy=data.get('strategy', 'balanced'),
                max_recommendations=data.get('max_recommendations', 5),
                use_cache=data.get('use_cache', True)
            ))
            loop.close()
            
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/execute', methods=['POST'])
    def execute_tool():
        """执行工具API"""
        try:
            data = request.get_json()
            if not data or 'tool_id' not in data:
                return jsonify({'success': False, 'error': '缺少tool_id参数'}), 400
            
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(manager.execute_tool(
                tool_id=data['tool_id'],
                parameters=data.get('parameters', {}),
                user_id=data.get('user_id', 'default'),
                session_id=data.get('session_id'),
                timeout=data.get('timeout')
            ))
            loop.close()
            
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools/<tool_id>/status', methods=['GET'])
    def get_tool_status(tool_id):
        """获取工具状态API"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(manager.get_tool_status(tool_id))
            loop.close()
            
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/system/status', methods=['GET'])
    def get_system_status():
        """获取系统状态API"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(manager.get_system_status())
            loop.close()
            
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/tools', methods=['GET'])
    def list_tools():
        """列出所有工具API"""
        try:
            tools = []
            for tool in manager.tool_registry.values():
                tools.append({
                    'id': tool.id,
                    'name': tool.name,
                    'type': tool.type,
                    'description': tool.description,
                    'capabilities': [cap.value for cap in tool.capabilities],
                    'performance_score': tool.performance_score,
                    'usage_count': tool.usage_count,
                    'is_active': tool.is_active
                })
            
            return jsonify({'success': True, 'data': tools})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app


if __name__ == "__main__":
    # 测试统一工具管理器
    async def test_manager():
        manager = get_tool_manager()
        await manager.initialize()
        
        # 测试发现工具
        discovery_result = await manager.discover_tools(force_scan=True)
        print(f"发现结果: {discovery_result}")
        
        # 测试推荐工具
        recommendations = await manager.recommend_tools(
            task_description="处理文本文件并生成报告",
            task_type="file",
            required_capabilities=["FILE_OPERATIONS"]
        )
        print(f"推荐工具: {len(recommendations)}个")
        for rec in recommendations:
            print(f"  - {rec['tool_name']}: {rec['confidence_score']:.2f}")
        
        # 测试系统状态
        status = await manager.get_system_status()
        print(f"系统状态: {status['system_status']}, 工具总数: {status['tools']['total']}")
        
        await manager.shutdown()
    
    # 运行测试
    asyncio.run(test_manager())

