"""
MCP-Zero 工具发现引擎

基于MCP-Zero项目的主动工具发现系统，实现：
- 自动扫描和发现MCP工具
- 工具能力分析和分类
- 工具元数据管理
- 动态工具注册
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import inspect
import subprocess
import sys
import os

from ..models.tool_models import MCPTool, ToolCapability, ToolMetadata


@dataclass
class DiscoveryConfig:
    """工具发现配置"""
    scan_paths: List[str]
    scan_interval: int = 300  # 5分钟
    max_tools: int = 2797  # 基于MCP-Zero数据集
    enable_auto_discovery: bool = True
    capability_analysis: bool = True
    metadata_extraction: bool = True


class MCPZeroDiscoveryEngine:
    """MCP-Zero 工具发现引擎"""
    
    def __init__(self, config: DiscoveryConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.discovered_tools: Dict[str, MCPTool] = {}
        self.tool_registry: Dict[str, Any] = {}
        self.scan_history: List[Dict] = []
        self.is_running = False
        
        # 工具类型映射
        self.tool_type_mapping = {
            'terminal': ['shell', 'command', 'exec', 'run'],
            'file': ['read', 'write', 'edit', 'file'],
            'web': ['http', 'request', 'browser', 'web'],
            'ai': ['llm', 'model', 'ai', 'gpt', 'claude'],
            'data': ['database', 'sql', 'data', 'query'],
            'api': ['api', 'rest', 'graphql', 'endpoint'],
            'git': ['git', 'version', 'commit', 'repo'],
            'deploy': ['deploy', 'docker', 'k8s', 'cloud'],
            'monitor': ['monitor', 'log', 'metric', 'alert'],
            'security': ['auth', 'security', 'encrypt', 'token']
        }
    
    async def start_discovery(self) -> None:
        """启动工具发现服务"""
        self.logger.info("启动MCP-Zero工具发现引擎")
        self.is_running = True
        
        # 初始扫描
        await self.full_scan()
        
        # 如果启用自动发现，开始定期扫描
        if self.config.enable_auto_discovery:
            asyncio.create_task(self._periodic_scan())
    
    async def stop_discovery(self) -> None:
        """停止工具发现服务"""
        self.logger.info("停止MCP-Zero工具发现引擎")
        self.is_running = False
    
    async def full_scan(self) -> Dict[str, List[MCPTool]]:
        """执行完整的工具扫描"""
        self.logger.info("开始完整工具扫描")
        scan_start = time.time()
        
        scan_results = {
            'new_tools': [],
            'updated_tools': [],
            'removed_tools': []
        }
        
        # 扫描所有配置的路径
        for scan_path in self.config.scan_paths:
            path_results = await self._scan_path(scan_path)
            for category, tools in path_results.items():
                scan_results[category].extend(tools)
        
        # 记录扫描历史
        scan_duration = time.time() - scan_start
        self.scan_history.append({
            'timestamp': time.time(),
            'duration': scan_duration,
            'new_tools': len(scan_results['new_tools']),
            'updated_tools': len(scan_results['updated_tools']),
            'removed_tools': len(scan_results['removed_tools']),
            'total_tools': len(self.discovered_tools)
        })
        
        self.logger.info(f"扫描完成: {len(scan_results['new_tools'])}新工具, "
                        f"{len(scan_results['updated_tools'])}更新工具, "
                        f"耗时{scan_duration:.2f}秒")
        
        return scan_results
    
    async def _scan_path(self, scan_path: str) -> Dict[str, List[MCPTool]]:
        """扫描指定路径"""
        results = {'new_tools': [], 'updated_tools': [], 'removed_tools': []}
        
        if not os.path.exists(scan_path):
            self.logger.warning(f"扫描路径不存在: {scan_path}")
            return results
        
        # 扫描Python模块
        python_tools = await self._scan_python_modules(scan_path)
        results['new_tools'].extend(python_tools)
        
        # 扫描MCP服务器配置
        mcp_tools = await self._scan_mcp_servers(scan_path)
        results['new_tools'].extend(mcp_tools)
        
        # 扫描可执行文件
        executable_tools = await self._scan_executables(scan_path)
        results['new_tools'].extend(executable_tools)
        
        return results
    
    async def _scan_python_modules(self, path: str) -> List[MCPTool]:
        """扫描Python模块中的工具"""
        tools = []
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    module_tools = await self._analyze_python_module(file_path)
                    tools.extend(module_tools)
        
        return tools
    
    async def _analyze_python_module(self, file_path: str) -> List[MCPTool]:
        """分析Python模块"""
        tools = []
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基础工具信息
            module_name = os.path.basename(file_path)[:-3]
            
            # 分析工具类型和能力
            capabilities = self._analyze_capabilities(content)
            tool_type = self._determine_tool_type(content, capabilities)
            
            # 提取元数据
            metadata = self._extract_metadata(content, file_path)
            
            # 创建工具对象
            tool = MCPTool(
                id=f"python_{module_name}_{hash(file_path) % 10000}",
                name=module_name,
                description=metadata.get('description', f"Python模块: {module_name}"),
                type=tool_type,
                capabilities=capabilities,
                metadata=ToolMetadata(
                    source_path=file_path,
                    language='python',
                    version=metadata.get('version', '1.0.0'),
                    author=metadata.get('author', 'Unknown'),
                    tags=metadata.get('tags', []),
                    dependencies=metadata.get('dependencies', [])
                ),
                performance_score=0.8,  # 默认分数
                usage_count=0,
                last_used=None,
                is_active=True
            )
            
            tools.append(tool)
            self.discovered_tools[tool.id] = tool
            
        except Exception as e:
            self.logger.error(f"分析Python模块失败 {file_path}: {e}")
        
        return tools
    
    async def _scan_mcp_servers(self, path: str) -> List[MCPTool]:
        """扫描MCP服务器配置"""
        tools = []
        
        # 查找MCP配置文件
        config_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.json', '.yaml', '.yml')) and 'mcp' in file.lower():
                    config_files.append(os.path.join(root, file))
        
        for config_file in config_files:
            mcp_tools = await self._analyze_mcp_config(config_file)
            tools.extend(mcp_tools)
        
        return tools
    
    async def _analyze_mcp_config(self, config_path: str) -> List[MCPTool]:
        """分析MCP配置文件"""
        tools = []
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    # 简单的YAML解析
                    import yaml
                    config = yaml.safe_load(f)
            
            # 解析MCP服务器配置
            if 'mcpServers' in config:
                for server_name, server_config in config['mcpServers'].items():
                    tool = await self._create_mcp_tool(server_name, server_config, config_path)
                    if tool:
                        tools.append(tool)
                        self.discovered_tools[tool.id] = tool
        
        except Exception as e:
            self.logger.error(f"分析MCP配置失败 {config_path}: {e}")
        
        return tools
    
    async def _create_mcp_tool(self, name: str, config: Dict, config_path: str) -> Optional[MCPTool]:
        """创建MCP工具对象"""
        try:
            # 分析工具能力
            capabilities = []
            if 'command' in config:
                capabilities.append(ToolCapability.EXECUTION)
            if 'args' in config:
                capabilities.append(ToolCapability.CONFIGURATION)
            
            # 确定工具类型
            tool_type = 'mcp_server'
            if 'filesystem' in name.lower():
                tool_type = 'file'
            elif 'web' in name.lower() or 'http' in name.lower():
                tool_type = 'web'
            elif 'git' in name.lower():
                tool_type = 'git'
            
            tool = MCPTool(
                id=f"mcp_{name}_{hash(config_path) % 10000}",
                name=name,
                description=config.get('description', f"MCP服务器: {name}"),
                type=tool_type,
                capabilities=capabilities,
                metadata=ToolMetadata(
                    source_path=config_path,
                    language='mcp',
                    version='1.0.0',
                    author='MCP',
                    tags=['mcp', 'server'],
                    dependencies=[]
                ),
                performance_score=0.9,  # MCP工具通常性能较好
                usage_count=0,
                last_used=None,
                is_active=True
            )
            
            return tool
            
        except Exception as e:
            self.logger.error(f"创建MCP工具失败 {name}: {e}")
            return None
    
    async def _scan_executables(self, path: str) -> List[MCPTool]:
        """扫描可执行文件"""
        tools = []
        
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.access(file_path, os.X_OK) and not file.endswith('.py'):
                    tool = await self._create_executable_tool(file_path)
                    if tool:
                        tools.append(tool)
                        self.discovered_tools[tool.id] = tool
        
        return tools
    
    async def _create_executable_tool(self, file_path: str) -> Optional[MCPTool]:
        """创建可执行文件工具"""
        try:
            file_name = os.path.basename(file_path)
            
            # 基础能力
            capabilities = [ToolCapability.EXECUTION]
            
            # 确定工具类型
            tool_type = 'executable'
            if any(keyword in file_name.lower() for keyword in ['git', 'svn']):
                tool_type = 'git'
            elif any(keyword in file_name.lower() for keyword in ['docker', 'kubectl']):
                tool_type = 'deploy'
            elif any(keyword in file_name.lower() for keyword in ['curl', 'wget']):
                tool_type = 'web'
            
            tool = MCPTool(
                id=f"exec_{file_name}_{hash(file_path) % 10000}",
                name=file_name,
                description=f"可执行文件: {file_name}",
                type=tool_type,
                capabilities=capabilities,
                metadata=ToolMetadata(
                    source_path=file_path,
                    language='executable',
                    version='1.0.0',
                    author='System',
                    tags=['executable'],
                    dependencies=[]
                ),
                performance_score=0.7,
                usage_count=0,
                last_used=None,
                is_active=True
            )
            
            return tool
            
        except Exception as e:
            self.logger.error(f"创建可执行工具失败 {file_path}: {e}")
            return None
    
    def _analyze_capabilities(self, content: str) -> List[ToolCapability]:
        """分析工具能力"""
        capabilities = []
        
        # 基于关键词分析
        if any(keyword in content.lower() for keyword in ['def ', 'class ', 'function']):
            capabilities.append(ToolCapability.EXECUTION)
        
        if any(keyword in content.lower() for keyword in ['read', 'write', 'file']):
            capabilities.append(ToolCapability.FILE_OPERATIONS)
        
        if any(keyword in content.lower() for keyword in ['http', 'request', 'api']):
            capabilities.append(ToolCapability.NETWORK_ACCESS)
        
        if any(keyword in content.lower() for keyword in ['config', 'setting', 'option']):
            capabilities.append(ToolCapability.CONFIGURATION)
        
        if any(keyword in content.lower() for keyword in ['monitor', 'log', 'metric']):
            capabilities.append(ToolCapability.MONITORING)
        
        return capabilities
    
    def _determine_tool_type(self, content: str, capabilities: List[ToolCapability]) -> str:
        """确定工具类型"""
        for tool_type, keywords in self.tool_type_mapping.items():
            if any(keyword in content.lower() for keyword in keywords):
                return tool_type
        
        # 基于能力确定类型
        if ToolCapability.FILE_OPERATIONS in capabilities:
            return 'file'
        elif ToolCapability.NETWORK_ACCESS in capabilities:
            return 'web'
        elif ToolCapability.MONITORING in capabilities:
            return 'monitor'
        
        return 'general'
    
    def _extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        # 提取文档字符串
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                # 找到文档字符串
                doc_start = i
                for j in range(i + 1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        doc_content = '\n'.join(lines[doc_start:j+1])
                        metadata['description'] = doc_content.strip('"""').strip("'''").strip()
                        break
                break
        
        # 提取版本信息
        for line in lines:
            if '__version__' in line or 'version' in line.lower():
                if '=' in line:
                    version_part = line.split('=')[1].strip().strip('"').strip("'")
                    metadata['version'] = version_part
                    break
        
        # 提取作者信息
        for line in lines:
            if '__author__' in line or 'author' in line.lower():
                if '=' in line:
                    author_part = line.split('=')[1].strip().strip('"').strip("'")
                    metadata['author'] = author_part
                    break
        
        return metadata
    
    async def _periodic_scan(self) -> None:
        """定期扫描"""
        while self.is_running:
            await asyncio.sleep(self.config.scan_interval)
            if self.is_running:
                await self.full_scan()
    
    def get_discovered_tools(self) -> Dict[str, MCPTool]:
        """获取已发现的工具"""
        return self.discovered_tools.copy()
    
    def get_tools_by_type(self, tool_type: str) -> List[MCPTool]:
        """按类型获取工具"""
        return [tool for tool in self.discovered_tools.values() if tool.type == tool_type]
    
    def get_tools_by_capability(self, capability: ToolCapability) -> List[MCPTool]:
        """按能力获取工具"""
        return [tool for tool in self.discovered_tools.values() if capability in tool.capabilities]
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        return {
            'total_tools': len(self.discovered_tools),
            'tools_by_type': {
                tool_type: len(self.get_tools_by_type(tool_type))
                for tool_type in set(tool.type for tool in self.discovered_tools.values())
            },
            'scan_history': self.scan_history[-10:],  # 最近10次扫描
            'last_scan': self.scan_history[-1] if self.scan_history else None
        }


# 工具发现引擎实例
discovery_engine = None

def get_discovery_engine() -> MCPZeroDiscoveryEngine:
    """获取工具发现引擎实例"""
    global discovery_engine
    if discovery_engine is None:
        config = DiscoveryConfig(
            scan_paths=[
                '/home/ubuntu/aicore0707/core/components',
                '/home/ubuntu/aicore0707/core/agents',
                '/usr/local/bin',
                '/usr/bin'
            ]
        )
        discovery_engine = MCPZeroDiscoveryEngine(config)
    return discovery_engine


if __name__ == "__main__":
    # 测试工具发现引擎
    async def test_discovery():
        engine = get_discovery_engine()
        await engine.start_discovery()
        
        # 等待扫描完成
        await asyncio.sleep(2)
        
        # 打印统计信息
        stats = engine.get_scan_statistics()
        print(f"发现工具总数: {stats['total_tools']}")
        print(f"工具类型分布: {stats['tools_by_type']}")
        
        # 打印部分工具
        tools = list(engine.get_discovered_tools().values())[:5]
        for tool in tools:
            print(f"工具: {tool.name} ({tool.type}) - {tool.description}")
        
        await engine.stop_discovery()
    
    asyncio.run(test_discovery())

