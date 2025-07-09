"""
Monaco Claude Plugin - PowerAutomation v4.3.0
为Monaco编辑器提供Claude AI集成功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import time

from .claude_api_client import ClaudeAPIClient
from .code_intelligence_engine import CodeIntelligenceEngine, CodeAnalysisResult, CodeIssue, CodeCompletion

@dataclass
class EditorPosition:
    """编辑器位置"""
    line: int
    column: int

@dataclass
class EditorRange:
    """编辑器范围"""
    start: EditorPosition
    end: EditorPosition

@dataclass
class CompletionItem:
    """Monaco补全项"""
    label: str
    kind: str
    detail: str
    documentation: str
    insert_text: str
    range: Optional[EditorRange] = None
    sort_text: Optional[str] = None

@dataclass
class DiagnosticItem:
    """Monaco诊断项"""
    severity: str  # error, warning, info, hint
    message: str
    range: EditorRange
    source: str = "Claude AI"
    code: Optional[str] = None

@dataclass
class HoverInfo:
    """悬停信息"""
    contents: List[str]
    range: Optional[EditorRange] = None

class MonacoClaudePlugin:
    """
    Monaco编辑器Claude插件
    提供AI驱动的代码编辑功能
    """
    
    def __init__(self, claude_client: ClaudeAPIClient):
        """
        初始化Monaco Claude插件
        
        Args:
            claude_client: Claude API客户端
        """
        self.claude_client = claude_client
        self.intelligence_engine = CodeIntelligenceEngine(claude_client)
        self.logger = logging.getLogger(__name__)
        
        # 插件配置
        self.config = {
            'auto_completion_enabled': True,
            'real_time_analysis_enabled': True,
            'hover_info_enabled': True,
            'code_actions_enabled': True,
            'completion_delay': 500,  # 毫秒
            'analysis_delay': 1000,   # 毫秒
            'max_completions': 10,
            'min_completion_length': 2
        }
        
        # 状态管理
        self.current_document: Optional[str] = None
        self.current_language: Optional[str] = None
        self.last_analysis_time: float = 0
        self.pending_analysis: Optional[asyncio.Task] = None
        
        # 缓存
        self.completion_cache: Dict[str, List[CompletionItem]] = {}
        self.diagnostic_cache: Dict[str, List[DiagnosticItem]] = {}
        self.hover_cache: Dict[str, HoverInfo] = {}
        
        # 回调函数
        self.on_diagnostics_update: Optional[Callable[[List[DiagnosticItem]], None]] = None
        self.on_completions_ready: Optional[Callable[[List[CompletionItem]], None]] = None
        self.on_hover_info: Optional[Callable[[HoverInfo], None]] = None
        
        # 统计信息
        self.stats = {
            'completions_provided': 0,
            'diagnostics_generated': 0,
            'hover_requests': 0,
            'analysis_requests': 0,
            'cache_hits': 0
        }
    
    def configure(self, config: Dict[str, Any]):
        """
        配置插件
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        self.logger.info(f"Plugin configured: {config}")
    
    def set_callbacks(self, 
                     on_diagnostics: Optional[Callable] = None,
                     on_completions: Optional[Callable] = None,
                     on_hover: Optional[Callable] = None):
        """
        设置回调函数
        
        Args:
            on_diagnostics: 诊断更新回调
            on_completions: 补全就绪回调
            on_hover: 悬停信息回调
        """
        if on_diagnostics:
            self.on_diagnostics_update = on_diagnostics
        if on_completions:
            self.on_completions_ready = on_completions
        if on_hover:
            self.on_hover_info = on_hover
    
    async def on_document_change(self, 
                                content: str, 
                                language: str,
                                filename: Optional[str] = None):
        """
        文档内容变化事件处理
        
        Args:
            content: 文档内容
            language: 编程语言
            filename: 文件名
        """
        self.current_document = content
        self.current_language = language
        
        # 取消之前的分析任务
        if self.pending_analysis and not self.pending_analysis.done():
            self.pending_analysis.cancel()
        
        # 如果启用了实时分析，延迟执行分析
        if self.config['real_time_analysis_enabled']:
            self.pending_analysis = asyncio.create_task(
                self._delayed_analysis(content, language, filename)
            )
    
    async def _delayed_analysis(self, 
                               content: str, 
                               language: str,
                               filename: Optional[str] = None):
        """
        延迟执行代码分析
        
        Args:
            content: 代码内容
            language: 编程语言
            filename: 文件名
        """
        try:
            # 等待延迟时间
            await asyncio.sleep(self.config['analysis_delay'] / 1000.0)
            
            # 执行分析
            await self._analyze_document(content, language, filename)
            
        except asyncio.CancelledError:
            self.logger.debug("Analysis cancelled due to new document change")
        except Exception as e:
            self.logger.error(f"Delayed analysis failed: {e}")
    
    async def _analyze_document(self, 
                               content: str, 
                               language: str,
                               filename: Optional[str] = None):
        """
        分析文档并更新诊断信息
        
        Args:
            content: 代码内容
            language: 编程语言
            filename: 文件名
        """
        try:
            self.stats['analysis_requests'] += 1
            
            # 执行代码分析
            analysis_result = await self.intelligence_engine.analyze_code(
                content, language, filename, include_completions=False
            )
            
            # 转换为Monaco诊断格式
            diagnostics = self._convert_issues_to_diagnostics(analysis_result.issues)
            
            # 缓存诊断结果
            cache_key = f"{language}:{hash(content)}"
            self.diagnostic_cache[cache_key] = diagnostics
            
            # 更新统计
            self.stats['diagnostics_generated'] += len(diagnostics)
            
            # 触发回调
            if self.on_diagnostics_update:
                self.on_diagnostics_update(diagnostics)
            
            self.logger.debug(f"Analysis completed: {len(diagnostics)} diagnostics generated")
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
    
    def _convert_issues_to_diagnostics(self, issues: List[CodeIssue]) -> List[DiagnosticItem]:
        """
        将代码问题转换为Monaco诊断格式
        
        Args:
            issues: 代码问题列表
            
        Returns:
            Monaco诊断项列表
        """
        diagnostics = []
        
        for issue in issues:
            # 映射严重程度
            severity_map = {
                'critical': 'error',
                'high': 'error',
                'medium': 'warning',
                'low': 'info',
                'info': 'hint'
            }
            
            severity = severity_map.get(issue.severity.value, 'info')
            
            # 创建范围
            line = max(1, issue.line_number or 1)
            start_pos = EditorPosition(line=line, column=issue.column or 1)
            end_pos = EditorPosition(line=line, column=(issue.column or 1) + 10)
            range_obj = EditorRange(start=start_pos, end=end_pos)
            
            # 创建诊断项
            diagnostic = DiagnosticItem(
                severity=severity,
                message=issue.message,
                range=range_obj,
                code=issue.type.value
            )
            
            diagnostics.append(diagnostic)
        
        return diagnostics
    
    async def provide_completions(self, 
                                 content: str,
                                 position: EditorPosition,
                                 language: str) -> List[CompletionItem]:
        """
        提供代码补全建议
        
        Args:
            content: 文档内容
            position: 光标位置
            language: 编程语言
            
        Returns:
            补全项列表
        """
        try:
            self.stats['completions_provided'] += 1
            
            # 检查缓存
            cache_key = f"{language}:{hash(content)}:{position.line}:{position.column}"
            if cache_key in self.completion_cache:
                self.stats['cache_hits'] += 1
                return self.completion_cache[cache_key]
            
            # 获取当前行内容
            lines = content.split('\n')
            if position.line <= len(lines):
                current_line = lines[position.line - 1]
                prefix = current_line[:position.column]
                
                # 检查是否需要补全
                if len(prefix.strip()) < self.config['min_completion_length']:
                    return []
            
            # 使用Claude生成补全
            claude_response = await self.claude_client.complete_code(content, language)
            
            # 解析补全建议
            completions = self._parse_completion_response(claude_response.content, position)
            
            # 限制补全数量
            completions = completions[:self.config['max_completions']]
            
            # 缓存结果
            self.completion_cache[cache_key] = completions
            
            return completions
            
        except Exception as e:
            self.logger.error(f"Completion provision failed: {e}")
            return []
    
    def _parse_completion_response(self, 
                                  response_content: str, 
                                  position: EditorPosition) -> List[CompletionItem]:
        """
        解析Claude的补全响应
        
        Args:
            response_content: Claude响应内容
            position: 光标位置
            
        Returns:
            补全项列表
        """
        completions = []
        
        # 简单的解析逻辑，实际可能需要更复杂的处理
        lines = response_content.strip().split('\n')
        
        for i, line in enumerate(lines[:self.config['max_completions']]):
            line = line.strip()
            if line:
                completion = CompletionItem(
                    label=line[:50] + "..." if len(line) > 50 else line,
                    kind="text",  # 可以根据内容类型调整
                    detail="Claude AI suggestion",
                    documentation=f"AI-generated completion suggestion {i+1}",
                    insert_text=line,
                    sort_text=f"{i:02d}"
                )
                completions.append(completion)
        
        return completions
    
    async def provide_hover_info(self, 
                                content: str,
                                position: EditorPosition,
                                language: str) -> Optional[HoverInfo]:
        """
        提供悬停信息
        
        Args:
            content: 文档内容
            position: 鼠标位置
            language: 编程语言
            
        Returns:
            悬停信息
        """
        try:
            self.stats['hover_requests'] += 1
            
            # 检查缓存
            cache_key = f"{language}:{hash(content)}:{position.line}:{position.column}"
            if cache_key in self.hover_cache:
                self.stats['cache_hits'] += 1
                return self.hover_cache[cache_key]
            
            # 获取当前位置的词汇或表达式
            lines = content.split('\n')
            if position.line <= len(lines):
                current_line = lines[position.line - 1]
                
                # 简单的词汇提取（可以改进）
                words = current_line.split()
                if words:
                    # 获取代码解释
                    explanation = await self.intelligence_engine.get_code_explanation(
                        current_line, language
                    )
                    
                    hover_info = HoverInfo(
                        contents=[
                            f"**Claude AI Analysis**",
                            explanation[:200] + "..." if len(explanation) > 200 else explanation
                        ]
                    )
                    
                    # 缓存结果
                    self.hover_cache[cache_key] = hover_info
                    
                    return hover_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Hover info provision failed: {e}")
            return None
    
    async def provide_code_actions(self, 
                                  content: str,
                                  range_obj: EditorRange,
                                  language: str,
                                  diagnostics: List[DiagnosticItem]) -> List[Dict[str, Any]]:
        """
        提供代码操作建议
        
        Args:
            content: 文档内容
            range_obj: 选中范围
            language: 编程语言
            diagnostics: 相关诊断信息
            
        Returns:
            代码操作列表
        """
        actions = []
        
        try:
            # 基于诊断信息提供修复建议
            for diagnostic in diagnostics:
                if diagnostic.severity in ['error', 'warning']:
                    actions.append({
                        'title': f"Fix: {diagnostic.message}",
                        'kind': 'quickfix',
                        'diagnostics': [asdict(diagnostic)],
                        'command': {
                            'command': 'claude.fix_issue',
                            'arguments': [content, asdict(range_obj), diagnostic.message]
                        }
                    })
            
            # 通用代码操作
            actions.extend([
                {
                    'title': 'Explain Code with Claude AI',
                    'kind': 'refactor',
                    'command': {
                        'command': 'claude.explain_code',
                        'arguments': [content, asdict(range_obj)]
                    }
                },
                {
                    'title': 'Generate Tests with Claude AI',
                    'kind': 'refactor',
                    'command': {
                        'command': 'claude.generate_tests',
                        'arguments': [content, asdict(range_obj)]
                    }
                },
                {
                    'title': 'Optimize Code with Claude AI',
                    'kind': 'refactor',
                    'command': {
                        'command': 'claude.optimize_code',
                        'arguments': [content, asdict(range_obj)]
                    }
                }
            ])
            
        except Exception as e:
            self.logger.error(f"Code actions provision failed: {e}")
        
        return actions
    
    async def execute_command(self, command: str, args: List[Any]) -> Any:
        """
        执行命令
        
        Args:
            command: 命令名称
            args: 命令参数
            
        Returns:
            命令执行结果
        """
        try:
            if command == 'claude.explain_code':
                content, range_obj = args[0], args[1]
                # 提取选中的代码
                selected_code = self._extract_code_from_range(content, range_obj)
                explanation = await self.intelligence_engine.get_code_explanation(
                    selected_code, self.current_language
                )
                return {'explanation': explanation}
            
            elif command == 'claude.generate_tests':
                content, range_obj = args[0], args[1]
                selected_code = self._extract_code_from_range(content, range_obj)
                tests = await self.intelligence_engine.generate_tests(
                    selected_code, self.current_language
                )
                return {'tests': tests}
            
            elif command == 'claude.optimize_code':
                content, range_obj = args[0], args[1]
                selected_code = self._extract_code_from_range(content, range_obj)
                
                # 使用Claude分析并提供优化建议
                analysis = await self.intelligence_engine.analyze_code(
                    selected_code, self.current_language
                )
                
                optimization_suggestions = []
                for suggestion in analysis.suggestions:
                    if 'optimization' in suggestion.lower() or 'performance' in suggestion.lower():
                        optimization_suggestions.append(suggestion)
                
                return {'optimizations': optimization_suggestions}
            
            elif command == 'claude.fix_issue':
                content, range_obj, issue_message = args[0], args[1], args[2]
                selected_code = self._extract_code_from_range(content, range_obj)
                
                # 请求Claude提供修复建议
                fix_prompt = f"Fix the following issue in this code: {issue_message}\n\nCode:\n{selected_code}"
                response = await self.claude_client.send_request(
                    ClaudeRequest(prompt=fix_prompt, max_tokens=1000)
                )
                
                return {'fix_suggestion': response.content}
            
            else:
                self.logger.warning(f"Unknown command: {command}")
                return None
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {command}, {e}")
            return {'error': str(e)}
    
    def _extract_code_from_range(self, content: str, range_obj: Dict[str, Any]) -> str:
        """
        从范围中提取代码
        
        Args:
            content: 文档内容
            range_obj: 范围对象
            
        Returns:
            提取的代码
        """
        lines = content.split('\n')
        start_line = range_obj['start']['line'] - 1
        end_line = range_obj['end']['line'] - 1
        start_col = range_obj['start']['column']
        end_col = range_obj['end']['column']
        
        if start_line == end_line:
            return lines[start_line][start_col:end_col]
        else:
            result_lines = []
            result_lines.append(lines[start_line][start_col:])
            for i in range(start_line + 1, end_line):
                result_lines.append(lines[i])
            result_lines.append(lines[end_line][:end_col])
            return '\n'.join(result_lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        return {
            **self.stats,
            'completion_cache_size': len(self.completion_cache),
            'diagnostic_cache_size': len(self.diagnostic_cache),
            'hover_cache_size': len(self.hover_cache),
            'config': self.config
        }
    
    def clear_cache(self):
        """清空所有缓存"""
        self.completion_cache.clear()
        self.diagnostic_cache.clear()
        self.hover_cache.clear()
        self.intelligence_engine.clear_cache()
        self.logger.info("All caches cleared")

# JavaScript接口生成器
def generate_monaco_integration_js() -> str:
    """
    生成Monaco编辑器集成的JavaScript代码
    
    Returns:
        JavaScript集成代码
    """
    return """
// Monaco Claude Plugin JavaScript Integration
// PowerAutomation v4.3.0

class MonacoClaudeIntegration {
    constructor(editor, pythonBridge) {
        this.editor = editor;
        this.pythonBridge = pythonBridge;
        this.isEnabled = true;
        this.completionProvider = null;
        this.hoverProvider = null;
        this.codeActionProvider = null;
        
        this.setupProviders();
        this.setupEventListeners();
    }
    
    setupProviders() {
        const monaco = window.monaco;
        
        // 代码补全提供器
        this.completionProvider = monaco.languages.registerCompletionItemProvider('*', {
            provideCompletionItems: async (model, position) => {
                if (!this.isEnabled) return { suggestions: [] };
                
                const content = model.getValue();
                const language = model.getLanguageId();
                
                try {
                    const completions = await this.pythonBridge.call('provide_completions', {
                        content: content,
                        position: { line: position.lineNumber, column: position.column },
                        language: language
                    });
                    
                    return {
                        suggestions: completions.map(item => ({
                            label: item.label,
                            kind: monaco.languages.CompletionItemKind.Text,
                            detail: item.detail,
                            documentation: item.documentation,
                            insertText: item.insert_text,
                            sortText: item.sort_text
                        }))
                    };
                } catch (error) {
                    console.error('Claude completion failed:', error);
                    return { suggestions: [] };
                }
            }
        });
        
        // 悬停信息提供器
        this.hoverProvider = monaco.languages.registerHoverProvider('*', {
            provideHover: async (model, position) => {
                if (!this.isEnabled) return null;
                
                const content = model.getValue();
                const language = model.getLanguageId();
                
                try {
                    const hoverInfo = await this.pythonBridge.call('provide_hover_info', {
                        content: content,
                        position: { line: position.lineNumber, column: position.column },
                        language: language
                    });
                    
                    if (hoverInfo && hoverInfo.contents) {
                        return {
                            contents: hoverInfo.contents.map(content => ({ value: content }))
                        };
                    }
                } catch (error) {
                    console.error('Claude hover failed:', error);
                }
                
                return null;
            }
        });
        
        // 代码操作提供器
        this.codeActionProvider = monaco.languages.registerCodeActionProvider('*', {
            provideCodeActions: async (model, range, context) => {
                if (!this.isEnabled) return { actions: [] };
                
                const content = model.getValue();
                const language = model.getLanguageId();
                const diagnostics = context.markers || [];
                
                try {
                    const actions = await this.pythonBridge.call('provide_code_actions', {
                        content: content,
                        range: {
                            start: { line: range.startLineNumber, column: range.startColumn },
                            end: { line: range.endLineNumber, column: range.endColumn }
                        },
                        language: language,
                        diagnostics: diagnostics
                    });
                    
                    return {
                        actions: actions.map(action => ({
                            title: action.title,
                            kind: action.kind,
                            edit: action.edit,
                            command: action.command
                        }))
                    };
                } catch (error) {
                    console.error('Claude code actions failed:', error);
                    return { actions: [] };
                }
            }
        });
    }
    
    setupEventListeners() {
        // 监听文档变化
        this.editor.onDidChangeModelContent(async (event) => {
            if (!this.isEnabled) return;
            
            const model = this.editor.getModel();
            if (!model) return;
            
            const content = model.getValue();
            const language = model.getLanguageId();
            
            try {
                await this.pythonBridge.call('on_document_change', {
                    content: content,
                    language: language,
                    filename: model.uri.path
                });
            } catch (error) {
                console.error('Document change notification failed:', error);
            }
        });
        
        // 监听诊断更新
        this.pythonBridge.on('diagnostics_update', (diagnostics) => {
            const model = this.editor.getModel();
            if (!model) return;
            
            const markers = diagnostics.map(diag => ({
                severity: this.getSeverityLevel(diag.severity),
                startLineNumber: diag.range.start.line,
                startColumn: diag.range.start.column,
                endLineNumber: diag.range.end.line,
                endColumn: diag.range.end.column,
                message: diag.message,
                source: diag.source
            }));
            
            monaco.editor.setModelMarkers(model, 'claude-ai', markers);
        });
    }
    
    getSeverityLevel(severity) {
        const monaco = window.monaco;
        switch (severity) {
            case 'error': return monaco.MarkerSeverity.Error;
            case 'warning': return monaco.MarkerSeverity.Warning;
            case 'info': return monaco.MarkerSeverity.Info;
            case 'hint': return monaco.MarkerSeverity.Hint;
            default: return monaco.MarkerSeverity.Info;
        }
    }
    
    enable() {
        this.isEnabled = true;
    }
    
    disable() {
        this.isEnabled = false;
    }
    
    dispose() {
        if (this.completionProvider) {
            this.completionProvider.dispose();
        }
        if (this.hoverProvider) {
            this.hoverProvider.dispose();
        }
        if (this.codeActionProvider) {
            this.codeActionProvider.dispose();
        }
    }
}

// 导出集成类
window.MonacoClaudeIntegration = MonacoClaudeIntegration;
"""

# 使用示例
async def main():
    """使用示例"""
    from .claude_api_client import ClaudeAPIClient
    
    async with ClaudeAPIClient() as claude_client:
        plugin = MonacoClaudePlugin(claude_client)
        
        # 配置插件
        plugin.configure({
            'auto_completion_enabled': True,
            'completion_delay': 300,
            'max_completions': 5
        })
        
        # 模拟文档变化
        python_code = "def hello():\n    print('Hello, "
        await plugin.on_document_change(python_code, 'python')
        
        # 模拟补全请求
        position = EditorPosition(line=2, column=20)
        completions = await plugin.provide_completions(python_code, position, 'python')
        
        print(f"Generated {len(completions)} completions")
        for completion in completions:
            print(f"  - {completion.label}: {completion.detail}")
        
        # 获取统计信息
        stats = plugin.get_stats()
        print(f"Plugin stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
"""

