"""
Release Trigger Engine - ClaudEditor发布触发引擎
负责监控Git仓库变化并触发自动化发布流程
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .git_monitor import GitMonitor
from .deployment_controller import DeploymentController
from .notification_manager import NotificationManager


class ReleaseTriggerEngine:
    """发布触发引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化发布触发引擎"""
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.git_monitor = GitMonitor(self.config)
        self.deployment_controller = DeploymentController(self.config)
        self.notification_manager = NotificationManager(self.config)
        
        # 状态管理
        self.is_running = False
        self.active_releases = {}
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "repository": {
                "url": "https://github.com/alexchuang650730/aicore0707.git",
                "branch": "main",
                "local_path": "/home/ubuntu/aicore0707"
            },
            "release": {
                "tag_pattern": r"^v(\d+)\.(\d+)\.(\d+)$",
                "supported_platforms": ["mac", "windows", "linux"],
                "test_levels": {
                    "patch": "smoke",
                    "minor": "regression", 
                    "major": "full"
                }
            },
            "quality_gate": {
                "min_pass_rate": 98.0,
                "max_failed_tests": 2,
                "required_test_suites": ["core"],
                "performance_thresholds": {
                    "startup_time": 3.0,
                    "memory_usage": 200,
                    "cpu_usage": 5.0
                }
            },
            "deployment": {
                "auto_deploy": True,
                "deployment_targets": ["github_releases", "mac_app_store"],
                "rollback_on_failure": True
            },
            "notifications": {
                "slack_webhook": None,
                "email_recipients": [],
                "github_notifications": True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 配置文件加载失败，使用默认配置: {e}")
        
        return default_config
    
    async def start_monitoring(self):
        """开始监控发布触发"""
        if self.is_running:
            print("⚠️ 发布监控已在运行中")
            return
        
        self.is_running = True
        print("🔍 开始监控Git仓库发布触发...")
        
        try:
            while self.is_running:
                # 检查新的发布标签
                new_releases = await self.git_monitor.check_new_releases()
                
                for release_info in new_releases:
                    await self._handle_new_release(release_info)
                
                # 检查进行中的发布状态
                await self._check_active_releases()
                
                # 等待下次检查
                await asyncio.sleep(30)  # 每30秒检查一次
                
        except Exception as e:
            print(f"❌ 发布监控异常: {e}")
            await self.notification_manager.send_error_notification(
                "发布监控异常", str(e)
            )
        finally:
            self.is_running = False
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        print("⏹️ 发布监控已停止")
    
    async def _handle_new_release(self, release_info: Dict[str, Any]):
        """处理新发布"""
        version = release_info['version']
        print(f"🎯 检测到新发布: {version}")
        
        # 检查发布条件
        if not await self._check_release_conditions(release_info):
            print(f"❌ 发布条件不满足，跳过 {version}")
            return
        
        # 添加到活跃发布列表
        release_id = f"{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_releases[release_id] = {
            'release_info': release_info,
            'status': 'triggered',
            'start_time': datetime.now(),
            'test_results': None,
            'deployment_results': None
        }
        
        # 发送开始通知
        await self.notification_manager.send_release_start_notification(release_info)
        
        # 触发测试流程
        await self._trigger_testing(release_id, release_info)
    
    async def _check_release_conditions(self, release_info: Dict[str, Any]) -> bool:
        """检查发布条件"""
        version = release_info['version']
        
        # 检查版本格式
        tag_pattern = self.config['release']['tag_pattern']
        if not re.match(tag_pattern, version):
            print(f"❌ 版本格式不符合要求: {version}")
            return False
        
        # 检查平台支持
        platform = release_info.get('platform', 'mac')
        if platform not in self.config['release']['supported_platforms']:
            print(f"❌ 不支持的平台: {platform}")
            return False
        
        # 检查是否已经在处理中
        for active_release in self.active_releases.values():
            if active_release['release_info']['version'] == version:
                print(f"⚠️ 版本 {version} 已在处理中")
                return False
        
        return True
    
    async def _trigger_testing(self, release_id: str, release_info: Dict[str, Any]):
        """触发测试流程"""
        print(f"🧪 触发测试流程: {release_info['version']}")
        
        try:
            # 更新状态
            self.active_releases[release_id]['status'] = 'testing'
            
            # 确定测试级别
            test_level = self._determine_test_level(release_info['version'])
            release_info['test_level'] = test_level
            
            # 导入并运行test_mcp
            from ..test_mcp import TestMCPEngine
            
            test_engine = TestMCPEngine()
            test_results = await test_engine.run_release_testing(release_info)
            
            # 保存测试结果
            self.active_releases[release_id]['test_results'] = test_results
            
            # 检查质量门禁
            if test_results['quality_gate']['passed']:
                print(f"✅ 质量门禁通过: {release_info['version']}")
                await self._trigger_deployment(release_id, release_info, test_results)
            else:
                print(f"❌ 质量门禁失败: {release_info['version']}")
                await self._handle_quality_gate_failure(release_id, release_info, test_results)
                
        except Exception as e:
            print(f"❌ 测试流程异常: {e}")
            self.active_releases[release_id]['status'] = 'test_failed'
            await self.notification_manager.send_test_failure_notification(
                release_info, str(e)
            )
    
    def _determine_test_level(self, version: str) -> str:
        """确定测试级别"""
        # 解析版本号
        match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", version)
        if not match:
            return "full"
        
        major, minor, patch = map(int, match.groups())
        
        # 根据版本变化确定测试级别
        test_levels = self.config['release']['test_levels']
        
        if patch > 0:
            return test_levels.get('patch', 'smoke')
        elif minor > 0:
            return test_levels.get('minor', 'regression')
        else:
            return test_levels.get('major', 'full')
    
    async def _trigger_deployment(self, release_id: str, release_info: Dict[str, Any], test_results: Dict[str, Any]):
        """触发部署流程"""
        print(f"🚀 触发部署流程: {release_info['version']}")
        
        try:
            # 更新状态
            self.active_releases[release_id]['status'] = 'deploying'
            
            # 执行部署
            deployment_results = await self.deployment_controller.deploy_release(
                release_info, test_results
            )
            
            # 保存部署结果
            self.active_releases[release_id]['deployment_results'] = deployment_results
            
            if deployment_results['success']:
                print(f"✅ 部署成功: {release_info['version']}")
                self.active_releases[release_id]['status'] = 'completed'
                await self.notification_manager.send_deployment_success_notification(
                    release_info, deployment_results
                )
            else:
                print(f"❌ 部署失败: {release_info['version']}")
                self.active_releases[release_id]['status'] = 'deploy_failed'
                await self.notification_manager.send_deployment_failure_notification(
                    release_info, deployment_results
                )
                
                # 自动回滚
                if self.config['deployment']['rollback_on_failure']:
                    await self._trigger_rollback(release_id, release_info)
                    
        except Exception as e:
            print(f"❌ 部署流程异常: {e}")
            self.active_releases[release_id]['status'] = 'deploy_failed'
            await self.notification_manager.send_deployment_failure_notification(
                release_info, {'error': str(e)}
            )
    
    async def _handle_quality_gate_failure(self, release_id: str, release_info: Dict[str, Any], test_results: Dict[str, Any]):
        """处理质量门禁失败"""
        self.active_releases[release_id]['status'] = 'quality_gate_failed'
        
        # 发送失败通知
        await self.notification_manager.send_quality_gate_failure_notification(
            release_info, test_results
        )
        
        # 生成详细报告
        await self._generate_failure_report(release_id, release_info, test_results)
    
    async def _trigger_rollback(self, release_id: str, release_info: Dict[str, Any]):
        """触发回滚"""
        print(f"🔄 触发回滚: {release_info['version']}")
        
        try:
            rollback_result = await self.deployment_controller.rollback_release(release_info)
            
            if rollback_result['success']:
                print(f"✅ 回滚成功: {release_info['version']}")
                self.active_releases[release_id]['status'] = 'rolled_back'
            else:
                print(f"❌ 回滚失败: {release_info['version']}")
                self.active_releases[release_id]['status'] = 'rollback_failed'
            
            await self.notification_manager.send_rollback_notification(
                release_info, rollback_result
            )
            
        except Exception as e:
            print(f"❌ 回滚异常: {e}")
            self.active_releases[release_id]['status'] = 'rollback_failed'
    
    async def _check_active_releases(self):
        """检查活跃发布状态"""
        current_time = datetime.now()
        
        for release_id, release_data in list(self.active_releases.items()):
            # 清理完成的发布 (保留24小时)
            if release_data['status'] in ['completed', 'quality_gate_failed', 'deploy_failed', 'rolled_back']:
                elapsed_hours = (current_time - release_data['start_time']).total_seconds() / 3600
                if elapsed_hours > 24:
                    del self.active_releases[release_id]
                    continue
            
            # 检查超时的发布
            elapsed_minutes = (current_time - release_data['start_time']).total_seconds() / 60
            if elapsed_minutes > 60:  # 超过60分钟
                if release_data['status'] in ['triggered', 'testing', 'deploying']:
                    print(f"⏰ 发布超时: {release_data['release_info']['version']}")
                    release_data['status'] = 'timeout'
                    await self.notification_manager.send_timeout_notification(
                        release_data['release_info']
                    )
    
    async def _generate_failure_report(self, release_id: str, release_info: Dict[str, Any], test_results: Dict[str, Any]):
        """生成失败报告"""
        report = {
            'release_id': release_id,
            'release_info': release_info,
            'test_results': test_results,
            'failure_analysis': self._analyze_test_failures(test_results),
            'recommendations': self._generate_failure_recommendations(test_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存报告
        reports_dir = Path(__file__).parent / "reports" / "failure_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"failure_report_{release_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 失败报告已生成: {report_file}")
    
    def _analyze_test_failures(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试失败原因"""
        analysis = {
            'failed_suites': [],
            'critical_failures': [],
            'performance_issues': [],
            'common_patterns': []
        }
        
        for suite_name, suite_result in test_results.get('test_results', {}).items():
            if not suite_result.get('passed', False):
                analysis['failed_suites'].append({
                    'suite': suite_name,
                    'failed_tests': suite_result.get('failed_tests', 0),
                    'errors': suite_result.get('errors', [])
                })
        
        return analysis
    
    def _generate_failure_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """生成失败建议"""
        recommendations = []
        
        quality_gate = test_results.get('quality_gate', {})
        
        if not quality_gate.get('checks', {}).get('pass_rate_check', True):
            recommendations.append("修复失败的测试用例，提高测试通过率")
        
        if not quality_gate.get('checks', {}).get('performance_check', True):
            recommendations.append("优化应用性能，满足性能基准要求")
        
        if not quality_gate.get('checks', {}).get('required_suites_check', True):
            recommendations.append("确保核心功能测试套件通过")
        
        return recommendations
    
    async def manual_trigger_release(self, version: str, platform: str = "mac", test_level: str = "full") -> str:
        """手动触发发布"""
        release_info = {
            'version': version,
            'platform': platform,
            'release_type': 'manual',
            'test_level': test_level,
            'triggered_by': 'manual',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"🎯 手动触发发布: {version}")
        
        # 检查发布条件
        if not await self._check_release_conditions(release_info):
            raise ValueError(f"发布条件不满足: {version}")
        
        # 生成发布ID
        release_id = f"{version}_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 添加到活跃发布列表
        self.active_releases[release_id] = {
            'release_info': release_info,
            'status': 'triggered',
            'start_time': datetime.now(),
            'test_results': None,
            'deployment_results': None
        }
        
        # 触发测试流程
        await self._trigger_testing(release_id, release_info)
        
        return release_id
    
    def get_active_releases(self) -> Dict[str, Any]:
        """获取活跃发布列表"""
        return self.active_releases.copy()
    
    def get_release_status(self, release_id: str) -> Optional[Dict[str, Any]]:
        """获取发布状态"""
        return self.active_releases.get(release_id)

