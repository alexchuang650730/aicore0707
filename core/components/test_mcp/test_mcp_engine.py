"""
Test MCP Engine - ClaudEditor自动化测试引擎
负责协调和执行所有测试套件
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .test_suites.core_functionality_tests import CoreFunctionalityTests
from .test_suites.ai_functionality_tests import AIFunctionalityTests
from .test_suites.ui_integration_tests import UIIntegrationTests
from .test_suites.performance_tests import PerformanceTests
from .test_suites.compatibility_tests import CompatibilityTests
from .test_suites.security_tests import SecurityTests
from .reports.test_report_generator import TestReportGenerator
from .config.test_config import TestConfig


class TestMCPEngine:
    """Test MCP核心引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化测试引擎"""
        self.config = TestConfig(config_path)
        self.report_generator = TestReportGenerator()
        
        # 初始化测试套件
        self.test_suites = {
            'core': CoreFunctionalityTests(self.config),
            'ai': AIFunctionalityTests(self.config),
            'ui': UIIntegrationTests(self.config),
            'performance': PerformanceTests(self.config),
            'compatibility': CompatibilityTests(self.config),
            'security': SecurityTests(self.config)
        }
        
        # 测试结果存储
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    async def run_release_testing(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的发布测试流程
        
        Args:
            release_info: 发布信息
                {
                    'version': '4.4.0',
                    'platform': 'mac',
                    'release_type': 'minor',
                    'test_level': 'full'
                }
        
        Returns:
            测试结果字典
        """
        print(f"🚀 开始ClaudEditor {release_info['version']} 发布测试")
        print(f"📋 测试平台: {release_info['platform']}")
        print(f"🎯 测试级别: {release_info['test_level']}")
        
        self.start_time = datetime.now()
        
        try:
            # 根据测试级别选择测试套件
            selected_suites = self._select_test_suites(release_info['test_level'])
            
            # 并行执行测试套件
            results = await self._execute_test_suites(selected_suites, release_info)
            
            # 生成测试报告
            test_report = await self._generate_test_report(results, release_info)
            
            # 质量门禁检查
            quality_gate_result = self._check_quality_gate(results)
            
            self.end_time = datetime.now()
            
            final_result = {
                'release_info': release_info,
                'test_results': results,
                'test_report': test_report,
                'quality_gate': quality_gate_result,
                'execution_time': (self.end_time - self.start_time).total_seconds(),
                'timestamp': self.end_time.isoformat()
            }
            
            # 保存测试结果
            await self._save_test_results(final_result)
            
            print(f"✅ 测试完成，总耗时: {final_result['execution_time']:.2f}秒")
            print(f"🎯 质量门禁: {'通过' if quality_gate_result['passed'] else '失败'}")
            
            return final_result
            
        except Exception as e:
            print(f"❌ 测试执行失败: {str(e)}")
            raise
    
    def _select_test_suites(self, test_level: str) -> List[str]:
        """根据测试级别选择测试套件"""
        suite_configs = {
            'smoke': ['core'],  # 冒烟测试
            'regression': ['core', 'ai', 'ui'],  # 回归测试
            'full': ['core', 'ai', 'ui', 'performance', 'compatibility', 'security'],  # 完整测试
            'performance': ['performance'],  # 性能测试
            'security': ['security']  # 安全测试
        }
        
        return suite_configs.get(test_level, ['core'])
    
    async def _execute_test_suites(self, selected_suites: List[str], release_info: Dict[str, Any]) -> Dict[str, Any]:
        """并行执行测试套件"""
        results = {}
        
        # 创建并发任务
        tasks = []
        for suite_name in selected_suites:
            if suite_name in self.test_suites:
                task = asyncio.create_task(
                    self._run_single_test_suite(suite_name, release_info),
                    name=f"test_suite_{suite_name}"
                )
                tasks.append(task)
        
        # 等待所有测试完成
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理测试结果
        for i, result in enumerate(completed_tasks):
            suite_name = selected_suites[i]
            if isinstance(result, Exception):
                results[suite_name] = {
                    'status': 'error',
                    'error': str(result),
                    'passed': False,
                    'execution_time': 0
                }
            else:
                results[suite_name] = result
        
        return results
    
    async def _run_single_test_suite(self, suite_name: str, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试套件"""
        print(f"🧪 运行 {suite_name} 测试套件...")
        
        start_time = time.time()
        test_suite = self.test_suites[suite_name]
        
        try:
            # 执行测试套件
            result = await test_suite.run(release_info)
            
            execution_time = time.time() - start_time
            
            # 标准化结果格式
            standardized_result = {
                'suite_name': suite_name,
                'status': 'completed',
                'passed': result.get('passed', False),
                'total_tests': result.get('total_tests', 0),
                'passed_tests': result.get('passed_tests', 0),
                'failed_tests': result.get('failed_tests', 0),
                'skipped_tests': result.get('skipped_tests', 0),
                'execution_time': execution_time,
                'details': result.get('details', {}),
                'metrics': result.get('metrics', {}),
                'errors': result.get('errors', [])
            }
            
            print(f"✅ {suite_name} 测试完成: {standardized_result['passed_tests']}/{standardized_result['total_tests']} 通过")
            
            return standardized_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {suite_name} 测试失败: {str(e)}")
            
            return {
                'suite_name': suite_name,
                'status': 'error',
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 1,
                'skipped_tests': 0,
                'execution_time': execution_time,
                'details': {},
                'metrics': {},
                'errors': [str(e)]
            }
    
    async def _generate_test_report(self, results: Dict[str, Any], release_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试报告"""
        return await self.report_generator.generate_report(results, release_info)
    
    def _check_quality_gate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """检查质量门禁"""
        total_tests = sum(result.get('total_tests', 0) for result in results.values())
        passed_tests = sum(result.get('passed_tests', 0) for result in results.values())
        failed_tests = sum(result.get('failed_tests', 0) for result in results.values())
        
        # 计算通过率
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 质量门禁规则
        quality_rules = {
            'min_pass_rate': 98.0,  # 最低通过率98%
            'max_failed_tests': 2,  # 最多2个失败测试
            'required_suites': ['core'],  # 必须通过的测试套件
            'performance_requirements': {
                'startup_time': 3.0,  # 启动时间 < 3秒
                'memory_usage': 200,  # 内存使用 < 200MB
                'cpu_usage': 5.0  # CPU使用 < 5%
            }
        }
        
        # 检查规则
        gate_checks = {
            'pass_rate_check': pass_rate >= quality_rules['min_pass_rate'],
            'failed_tests_check': failed_tests <= quality_rules['max_failed_tests'],
            'required_suites_check': all(
                results.get(suite, {}).get('passed', False) 
                for suite in quality_rules['required_suites']
            ),
            'performance_check': self._check_performance_requirements(
                results, quality_rules['performance_requirements']
            )
        }
        
        # 总体通过状态
        overall_passed = all(gate_checks.values())
        
        return {
            'passed': overall_passed,
            'pass_rate': pass_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'checks': gate_checks,
            'rules': quality_rules,
            'recommendation': self._generate_quality_recommendation(gate_checks, pass_rate)
        }
    
    def _check_performance_requirements(self, results: Dict[str, Any], requirements: Dict[str, float]) -> bool:
        """检查性能要求"""
        performance_result = results.get('performance', {})
        if not performance_result.get('passed', False):
            return False
        
        metrics = performance_result.get('metrics', {})
        
        checks = [
            metrics.get('startup_time', float('inf')) <= requirements['startup_time'],
            metrics.get('memory_usage', float('inf')) <= requirements['memory_usage'],
            metrics.get('cpu_usage', float('inf')) <= requirements['cpu_usage']
        ]
        
        return all(checks)
    
    def _generate_quality_recommendation(self, checks: Dict[str, bool], pass_rate: float) -> str:
        """生成质量建议"""
        if all(checks.values()):
            return "✅ 所有质量检查通过，可以进行部署"
        
        failed_checks = [check for check, passed in checks.items() if not passed]
        
        recommendations = {
            'pass_rate_check': f"❌ 测试通过率 {pass_rate:.1f}% 低于要求的98%，需要修复失败的测试",
            'failed_tests_check': "❌ 失败测试数量超过限制，需要修复关键问题",
            'required_suites_check': "❌ 核心测试套件未通过，必须修复后才能发布",
            'performance_check': "❌ 性能测试未达标，需要优化性能指标"
        }
        
        return "; ".join(recommendations[check] for check in failed_checks)
    
    async def _save_test_results(self, results: Dict[str, Any]) -> None:
        """保存测试结果"""
        # 创建报告目录
        reports_dir = Path(__file__).parent / "reports" / "test_results"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = results['release_info']['version']
        platform = results['release_info']['platform']
        
        filename = f"test_results_{version}_{platform}_{timestamp}.json"
        filepath = reports_dir / filename
        
        # 保存JSON格式结果
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 测试结果已保存: {filepath}")
    
    async def run_smoke_test(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行快速冒烟测试"""
        release_info['test_level'] = 'smoke'
        return await self.run_release_testing(release_info)
    
    async def run_performance_test(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行性能测试"""
        release_info['test_level'] = 'performance'
        return await self.run_release_testing(release_info)
    
    async def run_security_test(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行安全测试"""
        release_info['test_level'] = 'security'
        return await self.run_release_testing(release_info)
    
    def get_test_history(self, version: Optional[str] = None, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取测试历史记录"""
        reports_dir = Path(__file__).parent / "reports" / "test_results"
        
        if not reports_dir.exists():
            return []
        
        history = []
        for file_path in reports_dir.glob("test_results_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                # 过滤条件
                if version and result['release_info']['version'] != version:
                    continue
                if platform and result['release_info']['platform'] != platform:
                    continue
                
                history.append(result)
            except Exception as e:
                print(f"⚠️ 读取测试历史文件失败 {file_path}: {e}")
        
        # 按时间戳排序
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history

