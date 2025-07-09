#!/usr/bin/env python3
"""
Release Trigger MCP CLI
命令行接口，用于管理发布触发和测试流程
"""

import asyncio
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 导入核心组件
from .release_trigger_engine import ReleaseTriggerEngine
from .test_mcp_integration import TestMCPIntegration, TestLevel


class ReleaseTriggerCLI:
    """Release Trigger MCP命令行接口"""
    
    def __init__(self):
        self.engine = None
        self.config_file = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description='Release Trigger MCP - 自动化发布和测试管理工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  # 启动发布监控
  python -m release_trigger_mcp.cli monitor --config config/release_config.yaml
  
  # 手动触发发布
  python -m release_trigger_mcp.cli release --version v4.5.1 --test-level regression
  
  # 运行测试
  python -m release_trigger_mcp.cli test --version v4.5.1 --level full
  
  # 查看状态
  python -m release_trigger_mcp.cli status
  
  # 查看测试能力
  python -m release_trigger_mcp.cli capabilities
            """
        )
        
        # 全局参数
        parser.add_argument(
            '--config', '-c',
            type=str,
            default='config/release_config.yaml',
            help='配置文件路径'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='详细输出'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='静默模式'
        )
        
        # 子命令
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # monitor命令
        monitor_parser = subparsers.add_parser(
            'monitor',
            help='启动发布监控'
        )
        monitor_parser.add_argument(
            '--daemon', '-d',
            action='store_true',
            help='后台运行'
        )
        
        # release命令
        release_parser = subparsers.add_parser(
            'release',
            help='手动触发发布'
        )
        release_parser.add_argument(
            '--version',
            required=True,
            help='发布版本号 (例如: v4.5.1)'
        )
        release_parser.add_argument(
            '--test-level',
            choices=['smoke', 'regression', 'full', 'performance'],
            default='regression',
            help='测试级别'
        )
        release_parser.add_argument(
            '--force',
            action='store_true',
            help='强制发布 (跳过质量门禁)'
        )
        release_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行 (不实际执行)'
        )
        
        # test命令
        test_parser = subparsers.add_parser(
            'test',
            help='运行测试'
        )
        test_parser.add_argument(
            '--version',
            required=True,
            help='测试版本号'
        )
        test_parser.add_argument(
            '--level',
            choices=['smoke', 'regression', 'full', 'performance'],
            default='smoke',
            help='测试级别'
        )
        test_parser.add_argument(
            '--suite',
            action='append',
            help='指定测试套件 (可多次使用)'
        )
        test_parser.add_argument(
            '--output',
            help='测试结果输出文件'
        )
        
        # status命令
        status_parser = subparsers.add_parser(
            'status',
            help='查看系统状态'
        )
        status_parser.add_argument(
            '--json',
            action='store_true',
            help='JSON格式输出'
        )
        
        # capabilities命令
        capabilities_parser = subparsers.add_parser(
            'capabilities',
            help='查看测试能力'
        )
        capabilities_parser.add_argument(
            '--json',
            action='store_true',
            help='JSON格式输出'
        )
        
        # stop命令
        stop_parser = subparsers.add_parser(
            'stop',
            help='停止发布监控'
        )
        
        # history命令
        history_parser = subparsers.add_parser(
            'history',
            help='查看发布历史'
        )
        history_parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='显示记录数量'
        )
        history_parser.add_argument(
            '--version',
            help='过滤特定版本'
        )
        
        return parser
    
    async def initialize_engine(self, config_file: str):
        """初始化发布引擎"""
        try:
            self.config_file = config_file
            self.engine = ReleaseTriggerEngine(config_file)
            self.logger.info(f"发布引擎初始化完成，配置文件: {config_file}")
        except Exception as e:
            self.logger.error(f"发布引擎初始化失败: {e}")
            sys.exit(1)
    
    async def cmd_monitor(self, args):
        """监控命令处理"""
        print("🚀 启动发布监控...")
        
        if args.daemon:
            print("📡 后台模式启动")
            # TODO: 实现后台运行逻辑
        
        try:
            await self.engine.start_monitoring()
        except KeyboardInterrupt:
            print("\n⏹️ 收到停止信号，正在停止监控...")
            self.engine.stop_monitoring()
        except Exception as e:
            self.logger.error(f"监控异常: {e}")
            sys.exit(1)
    
    async def cmd_release(self, args):
        """发布命令处理"""
        print(f"🚀 手动触发发布: {args.version}")
        print(f"📋 测试级别: {args.test_level}")
        print(f"🔧 强制模式: {'是' if args.force else '否'}")
        print(f"🎭 模拟运行: {'是' if args.dry_run else '否'}")
        
        if args.dry_run:
            print("⚠️ 模拟运行模式，不会实际执行发布")
            return
        
        try:
            result = await self.engine.trigger_manual_release(
                args.version, 
                force=args.force
            )
            
            if result.get('success', False):
                print(f"✅ 发布触发成功: {result.get('message', '')}")
            else:
                print(f"❌ 发布触发失败: {result.get('error', '未知错误')}")
                sys.exit(1)
                
        except Exception as e:
            self.logger.error(f"发布触发异常: {e}")
            sys.exit(1)
    
    async def cmd_test(self, args):
        """测试命令处理"""
        print(f"🧪 运行测试: {args.version}")
        print(f"📋 测试级别: {args.level}")
        
        if args.suite:
            print(f"📦 指定套件: {', '.join(args.suite)}")
        
        try:
            # 创建发布信息
            release_info = {
                'version': args.version,
                'branch': 'main',
                'manual_trigger': True
            }
            
            # 运行测试
            test_results = await self.engine.test_mcp.run_tests_for_release(
                release_info, args.level
            )
            
            # 输出结果
            self._print_test_results(test_results)
            
            # 保存结果到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                print(f"📄 测试结果已保存到: {args.output}")
            
            # 根据测试结果设置退出码
            if not test_results.get('success', False):
                sys.exit(1)
                
        except Exception as e:
            self.logger.error(f"测试运行异常: {e}")
            sys.exit(1)
    
    async def cmd_status(self, args):
        """状态命令处理"""
        try:
            status = self.engine.get_status()
            
            if args.json:
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                self._print_status(status)
                
        except Exception as e:
            self.logger.error(f"获取状态异常: {e}")
            sys.exit(1)
    
    async def cmd_capabilities(self, args):
        """能力命令处理"""
        try:
            capabilities = self.engine.test_mcp.get_test_capabilities()
            
            if args.json:
                print(json.dumps(capabilities, indent=2, ensure_ascii=False))
            else:
                self._print_capabilities(capabilities)
                
        except Exception as e:
            self.logger.error(f"获取测试能力异常: {e}")
            sys.exit(1)
    
    async def cmd_stop(self, args):
        """停止命令处理"""
        print("⏹️ 停止发布监控...")
        
        try:
            self.engine.stop_monitoring()
            print("✅ 发布监控已停止")
        except Exception as e:
            self.logger.error(f"停止监控异常: {e}")
            sys.exit(1)
    
    async def cmd_history(self, args):
        """历史命令处理"""
        print(f"📚 查看发布历史 (最近 {args.limit} 条)")
        
        if args.version:
            print(f"🔍 过滤版本: {args.version}")
        
        try:
            # TODO: 实现历史记录查询
            print("📝 历史记录功能开发中...")
        except Exception as e:
            self.logger.error(f"查询历史异常: {e}")
            sys.exit(1)
    
    def _print_test_results(self, results: Dict[str, Any]):
        """打印测试结果"""
        print("\n" + "="*60)
        print("🧪 测试结果报告")
        print("="*60)
        
        print(f"📋 版本: {results.get('version', 'N/A')}")
        print(f"📊 测试级别: {results.get('test_level', 'N/A')}")
        print(f"⏱️ 开始时间: {results.get('start_time', 'N/A')}")
        print(f"⏱️ 结束时间: {results.get('end_time', 'N/A')}")
        print(f"⏳ 持续时间: {results.get('duration', 0):.2f} 秒")
        
        print(f"\n📈 测试统计:")
        print(f"  总测试数: {results.get('total_tests', 0)}")
        print(f"  通过测试: {results.get('passed_tests', 0)}")
        print(f"  失败测试: {results.get('failed_tests', 0)}")
        print(f"  跳过测试: {results.get('skipped_tests', 0)}")
        print(f"  通过率: {results.get('pass_rate', 0):.2f}%")
        
        print(f"\n✅ 完成套件: {', '.join(results.get('completed_suites', []))}")
        
        # 性能数据
        performance = results.get('performance', {})
        if performance:
            print(f"\n⚡ 性能指标:")
            for metric, value in performance.items():
                print(f"  {metric}: {value}")
        
        # 错误信息
        errors = results.get('errors', [])
        if errors:
            print(f"\n❌ 错误信息:")
            for error in errors:
                print(f"  - {error}")
        
        # 总体结果
        success = results.get('success', False)
        print(f"\n🎯 总体结果: {'✅ 成功' if success else '❌ 失败'}")
        print("="*60)
    
    def _print_status(self, status: Dict[str, Any]):
        """打印系统状态"""
        print("\n" + "="*50)
        print("📊 Release Trigger MCP 状态")
        print("="*50)
        
        print(f"🔄 运行状态: {'运行中' if status.get('is_running', False) else '已停止'}")
        print(f"📦 活跃发布: {status.get('active_releases_count', 0)} 个")
        
        # 组件状态
        components = status.get('components', {})
        print(f"\n🔧 组件状态:")
        for component, state in components.items():
            print(f"  {component}: {state}")
        
        # 测试能力
        test_capabilities = status.get('test_capabilities', {})
        if test_capabilities:
            print(f"\n🧪 测试能力:")
            print(f"  框架可用: {'是' if test_capabilities.get('framework_available', False) else '否'}")
            print(f"  运行器可用: {'是' if test_capabilities.get('test_runner_available', False) else '否'}")
            print(f"  可视化可用: {'是' if test_capabilities.get('visual_recorder_available', False) else '否'}")
            print(f"  智能体可用: {'是' if test_capabilities.get('test_agent_available', False) else '否'}")
        
        print("="*50)
    
    def _print_capabilities(self, capabilities: Dict[str, Any]):
        """打印测试能力"""
        print("\n" + "="*50)
        print("🧪 Test MCP 测试能力")
        print("="*50)
        
        print(f"📋 支持的测试级别:")
        for level in capabilities.get('supported_test_levels', []):
            print(f"  - {level}")
        
        print(f"\n📦 测试分类:")
        for category in capabilities.get('test_categories', []):
            print(f"  - {category}")
        
        print(f"\n⭐ 测试优先级:")
        for priority in capabilities.get('test_priorities', []):
            print(f"  - {priority}")
        
        print(f"\n🔧 组件状态:")
        print(f"  测试框架: {'可用' if capabilities.get('framework_available', False) else '不可用'}")
        print(f"  测试运行器: {'可用' if capabilities.get('test_runner_available', False) else '不可用'}")
        print(f"  可视化记录器: {'可用' if capabilities.get('visual_recorder_available', False) else '不可用'}")
        print(f"  测试智能体: {'可用' if capabilities.get('test_agent_available', False) else '不可用'}")
        
        print("="*50)
    
    async def run(self):
        """运行CLI"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # 设置日志级别
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        
        # 检查命令
        if not args.command:
            parser.print_help()
            return
        
        # 初始化引擎
        await self.initialize_engine(args.config)
        
        # 执行命令
        command_handlers = {
            'monitor': self.cmd_monitor,
            'release': self.cmd_release,
            'test': self.cmd_test,
            'status': self.cmd_status,
            'capabilities': self.cmd_capabilities,
            'stop': self.cmd_stop,
            'history': self.cmd_history
        }
        
        handler = command_handlers.get(args.command)
        if handler:
            await handler(args)
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()
            sys.exit(1)


def main():
    """主入口函数"""
    cli = ReleaseTriggerCLI()
    
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

