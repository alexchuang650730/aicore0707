"""
Release Trigger Engine - ClaudEditor发布触发引擎
负责监控Git仓库变化并触发自动化发布流程
集成Test MCP能力提供全面的测试支持
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入Test MCP集成
from .test_mcp_integration import TestMCPIntegration, TestLevel

class ReleaseTriggerEngine:
    """发布触发引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化发布触发引擎"""
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.git_monitor = GitMonitor(self.config)
        self.deployment_controller = DeploymentController(self.config)
        self.notification_manager = NotificationManager(self.config)
        
        # 初始化Test MCP集成
        self.test_mcp = TestMCPIntegration(self.config)
        
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
                "tag_pattern": r"v(\d+)\.(\d+)\.(\d+)",
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
        print("🚀 开始监控Git仓库发布触发...")
        
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
        print(f"🔍 检测到新发布: {version}")
        
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
        
        print(f"🚀 触发发布流程: {version}")
        
        try:
            # 运行测试
            test_results = await self._run_tests(release_info)
            self.active_releases[release_id]['test_results'] = test_results
            
            if not test_results['passed']:
                print(f"❌ 测试失败，取消发布: {version}")
                self.active_releases[release_id]['status'] = 'failed'
                await self.notification_manager.send_release_notification(
                    f"发布失败: {version}", "测试未通过", test_results
                )
                return
            
            # 执行部署
            deployment_results = await self._deploy_release(release_info)
            self.active_releases[release_id]['deployment_results'] = deployment_results
            
            if deployment_results['success']:
                print(f"✅ 发布成功: {version}")
                self.active_releases[release_id]['status'] = 'completed'
                await self.notification_manager.send_release_notification(
                    f"发布成功: {version}", "已成功部署到所有目标平台", deployment_results
                )
            else:
                print(f"❌ 部署失败: {version}")
                self.active_releases[release_id]['status'] = 'failed'
                
                # 如果启用了回滚
                if self.config['deployment']['rollback_on_failure']:
                    await self._rollback_release(release_info)
                
                await self.notification_manager.send_release_notification(
                    f"发布失败: {version}", "部署过程中出现错误", deployment_results
                )
                
        except Exception as e:
            print(f"❌ 发布流程异常: {version} - {e}")
            self.active_releases[release_id]['status'] = 'error'
            await self.notification_manager.send_error_notification(
                f"发布流程异常: {version}", str(e)
            )
    
    async def _check_release_conditions(self, release_info: Dict[str, Any]) -> bool:
        """检查发布条件"""
        version = release_info['version']
        
        # 检查版本格式
        pattern = self.config['release']['tag_pattern']
        if not re.match(pattern, version):
            print(f"⚠️ 版本格式不匹配: {version}")
            return False
        
        # 检查分支
        if release_info.get('branch') != self.config['repository']['branch']:
            print(f"⚠️ 分支不匹配: {release_info.get('branch')}")
            return False
        
        # 检查是否已经在处理中
        for active_release in self.active_releases.values():
            if active_release['release_info']['version'] == version:
                print(f"⚠️ 版本已在处理中: {version}")
                return False
        
        return True
    
    async def _run_tests(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行测试 - 使用集成的Test MCP"""
        version = release_info['version']
        print(f"🧪 开始测试: {version}")
        
        # 确定测试级别
        test_level = self._determine_test_level(version)
        print(f"📋 测试级别: {test_level}")
        
        # 使用Test MCP运行测试
        test_results = await self.test_mcp.run_tests_for_release(
            release_info, test_level
        )
        
        # 检查质量门禁
        quality_check = self._check_quality_gate(test_results)
        test_results['quality_gate_passed'] = quality_check
        test_results['passed'] = quality_check
        
        # 记录测试结果
        print(f"✅ 测试完成: 通过率 {test_results.get('pass_rate', 0):.2f}%")
        print(f"📊 测试统计: {test_results.get('passed_tests', 0)} 通过, {test_results.get('failed_tests', 0)} 失败")
        
        return test_results
    
    def _determine_test_level(self, version: str) -> str:
        """确定测试级别"""
        pattern = self.config['release']['tag_pattern']
        match = re.match(pattern, version)
        
        if not match:
            return "full"
        
        major, minor, patch = match.groups()
        
        # 根据版本变化确定测试级别
        if major != "0":  # 主版本变化
            return self.config['release']['test_levels']['major']
        elif minor != "0":  # 次版本变化
            return self.config['release']['test_levels']['minor']
        else:  # 补丁版本变化
            return self.config['release']['test_levels']['patch']
    
    def _check_quality_gate(self, test_results: Dict[str, Any]) -> bool:
        """检查质量门禁"""
        gate_config = self.config['quality_gate']
        
        # 检查通过率
        pass_rate = test_results.get('pass_rate', 0)
        if pass_rate < gate_config['min_pass_rate']:
            print(f"❌ 测试通过率不足: {pass_rate}% < {gate_config['min_pass_rate']}%")
            return False
        
        # 检查失败测试数量
        failed_tests = test_results.get('failed_count', 0)
        if failed_tests > gate_config['max_failed_tests']:
            print(f"❌ 失败测试过多: {failed_tests} > {gate_config['max_failed_tests']}")
            return False
        
        # 检查必需测试套件
        for required_suite in gate_config['required_test_suites']:
            if required_suite not in test_results.get('completed_suites', []):
                print(f"❌ 缺少必需测试套件: {required_suite}")
                return False
        
        # 检查性能阈值
        performance = test_results.get('performance', {})
        thresholds = gate_config['performance_thresholds']
        
        for metric, threshold in thresholds.items():
            if metric in performance:
                if performance[metric] > threshold:
                    print(f"❌ 性能指标超阈值: {metric} = {performance[metric]} > {threshold}")
                    return False
        
        return True
    
    async def _deploy_release(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """部署发布"""
        version = release_info['version']
        print(f"🚀 开始部署: {version}")
        
        deployment_results = {
            'success': True,
            'targets': {},
            'errors': []
        }
        
        targets = self.config['deployment']['deployment_targets']
        
        for target in targets:
            try:
                print(f"📦 部署到 {target}...")
                result = await self.deployment_controller.deploy_to_target(
                    release_info, target
                )
                deployment_results['targets'][target] = result
                
                if not result.get('success', False):
                    deployment_results['success'] = False
                    deployment_results['errors'].append(f"{target}: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ 部署到 {target} 失败: {e}")
                deployment_results['success'] = False
                deployment_results['targets'][target] = {'success': False, 'error': str(e)}
                deployment_results['errors'].append(f"{target}: {str(e)}")
        
        return deployment_results
    
    async def _rollback_release(self, release_info: Dict[str, Any]):
        """回滚发布"""
        version = release_info['version']
        print(f"🔄 开始回滚: {version}")
        
        try:
            await self.deployment_controller.rollback_release(release_info)
            print(f"✅ 回滚成功: {version}")
            
            await self.notification_manager.send_release_notification(
                f"回滚完成: {version}", "已成功回滚到上一个稳定版本", {}
            )
            
        except Exception as e:
            print(f"❌ 回滚失败: {version} - {e}")
            await self.notification_manager.send_error_notification(
                f"回滚失败: {version}", str(e)
            )
    
    async def _check_active_releases(self):
        """检查活跃发布状态"""
        completed_releases = []
        
        for release_id, release_data in self.active_releases.items():
            status = release_data['status']
            
            # 清理已完成或失败的发布（保留24小时）
            if status in ['completed', 'failed', 'error']:
                elapsed = datetime.now() - release_data['start_time']
                if elapsed.total_seconds() > 86400:  # 24小时
                    completed_releases.append(release_id)
        
        # 清理已完成的发布
        for release_id in completed_releases:
            del self.active_releases[release_id]
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'is_running': self.is_running,
            'active_releases_count': len(self.active_releases),
            'active_releases': self.active_releases,
            'config': self.config,
            'test_capabilities': self.test_mcp.get_test_capabilities(),
            'components': {
                'git_monitor': 'available',
                'deployment_controller': 'available', 
                'notification_manager': 'available',
                'test_mcp': 'available'
            }
        }
    
    async def trigger_manual_release(self, version: str, force: bool = False) -> Dict[str, Any]:
        """手动触发发布"""
        print(f"🔧 手动触发发布: {version}")
        
        # 创建发布信息
        release_info = {
            'version': version,
            'branch': self.config['repository']['branch'],
            'commit_hash': await self.git_monitor.get_latest_commit(),
            'manual_trigger': True,
            'force': force
        }
        
        # 如果不是强制模式，检查发布条件
        if not force and not await self._check_release_conditions(release_info):
            return {
                'success': False,
                'error': '发布条件不满足'
            }
        
        # 处理发布
        await self._handle_new_release(release_info)
        
        return {
            'success': True,
            'message': f'已触发发布: {version}'
        }


# 辅助类
class GitMonitor:
    """Git监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.repo_path = Path(config['repository']['local_path'])
        self.last_check_time = None
    
    async def check_new_releases(self) -> List[Dict[str, Any]]:
        """检查新发布"""
        # 实现Git标签检查逻辑
        return []
    
    async def get_latest_commit(self) -> str:
        """获取最新提交哈希"""
        return "abc123def456"


class DeploymentController:
    """部署控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def run_tests(self, release_info: Dict[str, Any], test_level: str) -> Dict[str, Any]:
        """运行测试"""
        return {
            'pass_rate': 99.5,
            'failed_count': 1,
            'completed_suites': ['core', 'integration'],
            'performance': {
                'startup_time': 2.5,
                'memory_usage': 180,
                'cpu_usage': 3.2
            }
        }
    
    async def deploy_to_target(self, release_info: Dict[str, Any], target: str) -> Dict[str, Any]:
        """部署到目标平台"""
        return {'success': True}
    
    async def rollback_release(self, release_info: Dict[str, Any]):
        """回滚发布"""
        pass


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send_release_notification(self, title: str, message: str, data: Dict[str, Any]):
        """发送发布通知"""
        print(f"📢 {title}: {message}")
    
    async def send_error_notification(self, title: str, error: str):
        """发送错误通知"""
        print(f"🚨 {title}: {error}")


# 主函数
async def main():
    """主函数"""
    engine = ReleaseTriggerEngine()
    
    try:
        await engine.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ 收到停止信号")
        engine.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())

