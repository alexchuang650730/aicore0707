"""
Code Intelligence Engine - PowerAutomation v4.3.0
基于Claude的代码智能分析引擎
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import ast
import tokenize
from io import StringIO

from .claude_api_client import ClaudeAPIClient, ClaudeRequest, ClaudeModel

class CodeIssueType(Enum):
    """代码问题类型"""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    BEST_PRACTICE = "best_practice"
    MAINTAINABILITY = "maintainability"

class SeverityLevel(Enum):
    """严重程度级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class CodeIssue:
    """代码问题数据结构"""
    type: CodeIssueType
    severity: SeverityLevel
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class CodeCompletion:
    """代码补全建议"""
    text: str
    description: str
    confidence: float
    insert_position: int
    replace_length: int = 0

@dataclass
class CodeAnalysisResult:
    """代码分析结果"""
    issues: List[CodeIssue] = field(default_factory=list)
    completions: List[CodeCompletion] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    analysis_time: float = 0.0

class CodeIntelligenceEngine:
    """
    代码智能分析引擎
    提供基于Claude的代码分析、补全和建议功能
    """
    
    def __init__(self, claude_client: ClaudeAPIClient):
        """
        初始化代码智能引擎
        
        Args:
            claude_client: Claude API客户端
        """
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        
        # 支持的编程语言
        self.supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala',
            'html', 'css', 'sql', 'json', 'yaml', 'xml'
        }
        
        # 语言特定的配置
        self.language_configs = {
            'python': {
                'file_extensions': ['.py', '.pyw'],
                'comment_style': '#',
                'indent_style': 'spaces',
                'indent_size': 4
            },
            'javascript': {
                'file_extensions': ['.js', '.jsx'],
                'comment_style': '//',
                'indent_style': 'spaces',
                'indent_size': 2
            },
            'typescript': {
                'file_extensions': ['.ts', '.tsx'],
                'comment_style': '//',
                'indent_style': 'spaces',
                'indent_size': 2
            }
        }
        
        # 缓存
        self.analysis_cache: Dict[str, CodeAnalysisResult] = {}
        self.cache_ttl = 300  # 5分钟
        
        # 统计信息
        self.stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'average_analysis_time': 0.0,
            'issues_found': 0,
            'completions_generated': 0
        }
    
    def _get_cache_key(self, code: str, language: str, analysis_type: str) -> str:
        """生成缓存键"""
        return f"{analysis_type}:{language}:{hash(code)}"
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否有效"""
        return time.time() - timestamp < self.cache_ttl
    
    def _detect_language(self, code: str, filename: Optional[str] = None) -> str:
        """
        自动检测编程语言
        
        Args:
            code: 代码内容
            filename: 文件名（可选）
            
        Returns:
            检测到的编程语言
        """
        # 基于文件扩展名检测
        if filename:
            for lang, config in self.language_configs.items():
                for ext in config['file_extensions']:
                    if filename.endswith(ext):
                        return lang
        
        # 基于代码内容检测
        code_lower = code.lower().strip()
        
        # Python特征
        if any(keyword in code for keyword in ['def ', 'import ', 'from ', 'class ', 'if __name__']):
            return 'python'
        
        # JavaScript/TypeScript特征
        if any(keyword in code for keyword in ['function ', 'const ', 'let ', 'var ', '=>']):
            if 'interface ' in code or 'type ' in code or ': string' in code:
                return 'typescript'
            return 'javascript'
        
        # HTML特征
        if code_lower.startswith('<!doctype') or '<html' in code_lower:
            return 'html'
        
        # CSS特征
        if '{' in code and '}' in code and ':' in code and ';' in code:
            return 'css'
        
        # JSON特征
        if code_lower.startswith('{') and code_lower.endswith('}'):
            try:
                json.loads(code)
                return 'json'
            except:
                pass
        
        # 默认返回Python
        return 'python'
    
    def _parse_python_code(self, code: str) -> Tuple[bool, List[CodeIssue]]:
        """
        解析Python代码并检查语法错误
        
        Args:
            code: Python代码
            
        Returns:
            (是否有效, 问题列表)
        """
        issues = []
        
        try:
            # 语法检查
            ast.parse(code)
            
            # 基本的代码质量检查
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 检查过长的行
                if len(line) > 100:
                    issues.append(CodeIssue(
                        type=CodeIssueType.STYLE,
                        severity=SeverityLevel.LOW,
                        message=f"Line too long ({len(line)} characters)",
                        line_number=i,
                        suggestion="Consider breaking this line into multiple lines"
                    ))
                
                # 检查TODO注释
                if 'todo' in line_stripped.lower():
                    issues.append(CodeIssue(
                        type=CodeIssueType.MAINTAINABILITY,
                        severity=SeverityLevel.INFO,
                        message="TODO comment found",
                        line_number=i,
                        suggestion="Consider addressing this TODO item"
                    ))
            
            return True, issues
            
        except SyntaxError as e:
            issues.append(CodeIssue(
                type=CodeIssueType.SYNTAX_ERROR,
                severity=SeverityLevel.CRITICAL,
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                column=e.offset,
                suggestion="Fix the syntax error before proceeding"
            ))
            return False, issues
        
        except Exception as e:
            issues.append(CodeIssue(
                type=CodeIssueType.SYNTAX_ERROR,
                severity=SeverityLevel.HIGH,
                message=f"Parse error: {str(e)}",
                suggestion="Check code syntax and structure"
            ))
            return False, issues
    
    async def analyze_code(self, 
                          code: str, 
                          language: Optional[str] = None,
                          filename: Optional[str] = None,
                          include_completions: bool = True) -> CodeAnalysisResult:
        """
        分析代码
        
        Args:
            code: 要分析的代码
            language: 编程语言（可选，会自动检测）
            filename: 文件名（可选）
            include_completions: 是否包含代码补全建议
            
        Returns:
            代码分析结果
        """
        start_time = time.time()
        
        # 检测语言
        if not language:
            language = self._detect_language(code, filename)
        
        # 检查缓存
        cache_key = self._get_cache_key(code, language, "analysis")
        if cache_key in self.analysis_cache:
            cached_result, timestamp = self.analysis_cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.stats['cache_hits'] += 1
                return cached_result
        
        self.stats['total_analyses'] += 1
        
        # 初始化结果
        result = CodeAnalysisResult()
        
        # 基础语法检查
        if language == 'python':
            is_valid, syntax_issues = self._parse_python_code(code)
            result.issues.extend(syntax_issues)
        
        # 使用Claude进行深度分析
        try:
            claude_response = await self.claude_client.analyze_code(code, language)
            
            # 解析Claude的分析结果
            analysis_content = claude_response.content
            result.suggestions.append(analysis_content)
            
            # 尝试从Claude响应中提取结构化问题
            issues = self._extract_issues_from_analysis(analysis_content)
            result.issues.extend(issues)
            
        except Exception as e:
            self.logger.error(f"Claude analysis failed: {e}")
            result.issues.append(CodeIssue(
                type=CodeIssueType.LOGIC_ERROR,
                severity=SeverityLevel.INFO,
                message="AI analysis unavailable",
                suggestion="Claude API analysis failed, showing basic analysis only"
            ))
        
        # 生成代码补全建议
        if include_completions:
            try:
                completions = await self._generate_completions(code, language)
                result.completions.extend(completions)
            except Exception as e:
                self.logger.error(f"Completion generation failed: {e}")
        
        # 计算代码指标
        result.metrics = self._calculate_code_metrics(code, language)
        
        # 记录分析时间
        result.analysis_time = time.time() - start_time
        
        # 更新统计
        self.stats['issues_found'] += len(result.issues)
        self.stats['completions_generated'] += len(result.completions)
        self.stats['average_analysis_time'] = (
            (self.stats['average_analysis_time'] * (self.stats['total_analyses'] - 1) + 
             result.analysis_time) / self.stats['total_analyses']
        )
        
        # 缓存结果
        self.analysis_cache[cache_key] = (result, time.time())
        
        return result
    
    def _extract_issues_from_analysis(self, analysis_text: str) -> List[CodeIssue]:
        """
        从Claude分析文本中提取结构化问题
        
        Args:
            analysis_text: Claude分析文本
            
        Returns:
            提取的问题列表
        """
        issues = []
        
        # 简单的模式匹配来提取问题
        # 这里可以根据Claude响应的实际格式进行调整
        
        # 查找性能相关问题
        if 'performance' in analysis_text.lower():
            issues.append(CodeIssue(
                type=CodeIssueType.PERFORMANCE,
                severity=SeverityLevel.MEDIUM,
                message="Potential performance issue identified",
                suggestion="Review the performance analysis in the detailed feedback"
            ))
        
        # 查找安全相关问题
        if 'security' in analysis_text.lower():
            issues.append(CodeIssue(
                type=CodeIssueType.SECURITY,
                severity=SeverityLevel.HIGH,
                message="Potential security issue identified",
                suggestion="Review the security analysis in the detailed feedback"
            ))
        
        # 查找最佳实践问题
        if 'best practice' in analysis_text.lower():
            issues.append(CodeIssue(
                type=CodeIssueType.BEST_PRACTICE,
                severity=SeverityLevel.LOW,
                message="Best practice recommendation available",
                suggestion="Review the best practice suggestions in the detailed feedback"
            ))
        
        return issues
    
    async def _generate_completions(self, code: str, language: str) -> List[CodeCompletion]:
        """
        生成代码补全建议
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            代码补全建议列表
        """
        completions = []
        
        try:
            # 找到代码的最后一行，用于补全
            lines = code.split('\n')
            if not lines:
                return completions
            
            last_line = lines[-1]
            
            # 如果最后一行不完整，尝试补全
            if last_line.strip() and not last_line.strip().endswith((':',';', '{', '}')):
                claude_response = await self.claude_client.complete_code(code, language)
                
                completion_text = claude_response.content.strip()
                if completion_text:
                    completions.append(CodeCompletion(
                        text=completion_text,
                        description="AI-suggested completion",
                        confidence=0.8,
                        insert_position=len(code)
                    ))
        
        except Exception as e:
            self.logger.error(f"Completion generation failed: {e}")
        
        return completions
    
    def _calculate_code_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """
        计算代码指标
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            代码指标字典
        """
        metrics = {}
        
        lines = code.split('\n')
        
        # 基础指标
        metrics['total_lines'] = len(lines)
        metrics['non_empty_lines'] = len([line for line in lines if line.strip()])
        metrics['comment_lines'] = 0
        metrics['code_lines'] = 0
        
        # 语言特定的注释检测
        comment_patterns = {
            'python': [r'^\s*#'],
            'javascript': [r'^\s*//', r'^\s*/\*', r'^\s*\*'],
            'typescript': [r'^\s*//', r'^\s*/\*', r'^\s*\*']
        }
        
        patterns = comment_patterns.get(language, [r'^\s*#'])
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            is_comment = any(re.match(pattern, line) for pattern in patterns)
            if is_comment:
                metrics['comment_lines'] += 1
            else:
                metrics['code_lines'] += 1
        
        # 计算注释比例
        if metrics['non_empty_lines'] > 0:
            metrics['comment_ratio'] = metrics['comment_lines'] / metrics['non_empty_lines']
        else:
            metrics['comment_ratio'] = 0.0
        
        # 复杂度指标（简化版）
        if language == 'python':
            # 计算函数和类的数量
            metrics['function_count'] = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
            metrics['class_count'] = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
        
        # 平均行长度
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            metrics['average_line_length'] = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        else:
            metrics['average_line_length'] = 0.0
        
        return metrics
    
    async def get_code_explanation(self, code: str, language: Optional[str] = None) -> str:
        """
        获取代码解释
        
        Args:
            code: 要解释的代码
            language: 编程语言
            
        Returns:
            代码解释文本
        """
        if not language:
            language = self._detect_language(code)
        
        try:
            response = await self.claude_client.explain_code(code, language)
            return response.content
        except Exception as e:
            self.logger.error(f"Code explanation failed: {e}")
            return "Code explanation is currently unavailable."
    
    async def generate_tests(self, 
                           code: str, 
                           language: Optional[str] = None,
                           test_framework: Optional[str] = None) -> str:
        """
        生成测试代码
        
        Args:
            code: 要测试的代码
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            生成的测试代码
        """
        if not language:
            language = self._detect_language(code)
        
        if not test_framework:
            # 默认测试框架
            framework_map = {
                'python': 'pytest',
                'javascript': 'jest',
                'typescript': 'jest',
                'java': 'junit'
            }
            test_framework = framework_map.get(language, 'unittest')
        
        try:
            response = await self.claude_client.generate_tests(code, language, test_framework)
            return response.content
        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return f"# Test generation failed: {e}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            **self.stats,
            'cache_size': len(self.analysis_cache),
            'supported_languages': list(self.supported_languages)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.analysis_cache.clear()
        self.logger.info("Analysis cache cleared")

# 使用示例
async def main():
    """使用示例"""
    from .claude_api_client import ClaudeAPIClient
    
    async with ClaudeAPIClient() as claude_client:
        engine = CodeIntelligenceEngine(claude_client)
        
        # 分析Python代码
        python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# TODO: Optimize this function
result = fibonacci(10)
print(result)
"""
        
        result = await engine.analyze_code(python_code, 'python')
        
        print(f"Found {len(result.issues)} issues:")
        for issue in result.issues:
            print(f"  - {issue.severity.value}: {issue.message}")
        
        print(f"Generated {len(result.completions)} completions")
        print(f"Analysis took {result.analysis_time:.2f} seconds")
        print(f"Code metrics: {result.metrics}")
        
        # 获取代码解释
        explanation = await engine.get_code_explanation(python_code)
        print(f"Code explanation: {explanation[:200]}...")
        
        # 生成测试
        tests = await engine.generate_tests(python_code)
        print(f"Generated tests: {tests[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())

