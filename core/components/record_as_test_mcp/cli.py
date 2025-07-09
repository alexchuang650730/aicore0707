#!/usr/bin/env python3
"""
录制即测试命令行接口

提供完整的CLI命令来管理录制即测试功能，包括录制、生成、
优化、回放等操作。
"""

import asyncio
import click
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .record_as_test_service import get_record_as_test_service, RecordAsTestService

# 配置Click
@click.group()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def record(ctx, config: Optional[str], verbose: bool):
    """录制即测试命令组"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

@record.command()
@click.argument('session_name')
@click.option('--metadata', '-m', help='会话元数据(JSON格式)')
@click.pass_context
def start(ctx, session_name: str, metadata: Optional[str]):
    """开始录制会话
    
    SESSION_NAME: 录制会话名称
    """
    try:
        service = get_record_as_test_service()
        
        # 解析元数据
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                click.echo(f"❌ 元数据格式错误: {metadata}", err=True)
                sys.exit(1)
        
        # 开始录制
        session = asyncio.run(service.start_recording_session(session_name, metadata_dict))
        
        click.echo(f"🎬 录制会话已开始")
        click.echo(f"   会话ID: {session.id}")
        click.echo(f"   会话名称: {session.name}")
        click.echo(f"   开始时间: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if ctx.obj['verbose']:
            click.echo(f"   元数据: {session.metadata}")
            
    except Exception as e:
        click.echo(f"❌ 启动录制失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.argument('session_id')
@click.pass_context
def stop(ctx, session_id: str):
    """停止录制会话
    
    SESSION_ID: 录制会话ID
    """
    try:
        service = get_record_as_test_service()
        
        # 停止录制
        session = asyncio.run(service.stop_recording_session(session_id))
        
        click.echo(f"⏹️ 录制会话已停止")
        click.echo(f"   会话ID: {session.id}")
        click.echo(f"   会话名称: {session.name}")
        click.echo(f"   结束时间: {session.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"   录制动作: {len(session.actions)}个")
        click.echo(f"   截图数量: {len(session.screenshots)}个")
        
        if session.video_path:
            click.echo(f"   视频文件: {session.video_path}")
            
    except Exception as e:
        click.echo(f"❌ 停止录制失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.argument('session_id')
@click.option('--optimize', '-o', is_flag=True, help='自动AI优化')
@click.pass_context
def generate(ctx, session_id: str, optimize: bool):
    """从录制生成测试用例
    
    SESSION_ID: 录制会话ID
    """
    try:
        service = get_record_as_test_service()
        
        # 生成测试用例
        test_case = asyncio.run(service.generate_test_from_recording(session_id))
        
        click.echo(f"🧪 测试用例已生成")
        click.echo(f"   测试ID: {test_case.id}")
        click.echo(f"   测试名称: {test_case.name}")
        click.echo(f"   测试步骤: {len(test_case.steps)}个")
        click.echo(f"   验证点: {len(test_case.assertions)}个")
        click.echo(f"   文件路径: {test_case.file_path}")
        
        # 手动优化
        if optimize and not test_case.optimized:
            click.echo("🤖 正在进行AI优化...")
            optimized_test = asyncio.run(service.optimize_test_with_ai(test_case.id))
            click.echo(f"✨ AI优化完成")
            
            if ctx.obj['verbose'] and optimized_test.metadata.get('optimization_suggestions'):
                click.echo("   优化建议:")
                for suggestion in optimized_test.metadata['optimization_suggestions']:
                    click.echo(f"   - {suggestion}")
            
    except Exception as e:
        click.echo(f"❌ 生成测试用例失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.argument('test_case_id')
@click.pass_context
def optimize(ctx, test_case_id: str):
    """使用AI优化测试用例
    
    TEST_CASE_ID: 测试用例ID
    """
    try:
        service = get_record_as_test_service()
        
        # AI优化
        test_case = asyncio.run(service.optimize_test_with_ai(test_case_id))
        
        click.echo(f"✨ 测试用例已优化")
        click.echo(f"   测试ID: {test_case.id}")
        click.echo(f"   测试名称: {test_case.name}")
        click.echo(f"   优化后步骤: {len(test_case.steps)}个")
        click.echo(f"   优化后验证点: {len(test_case.assertions)}个")
        
        if ctx.obj['verbose'] and test_case.metadata.get('optimization_suggestions'):
            click.echo("   优化建议:")
            for suggestion in test_case.metadata['optimization_suggestions']:
                click.echo(f"   - {suggestion}")
            
    except Exception as e:
        click.echo(f"❌ 优化测试用例失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.argument('test_case_id')
@click.option('--report', '-r', is_flag=True, help='生成详细报告')
@click.pass_context
def playback(ctx, test_case_id: str, report: bool):
    """回放测试用例
    
    TEST_CASE_ID: 测试用例ID
    """
    try:
        service = get_record_as_test_service()
        
        click.echo(f"▶️ 开始回放测试用例...")
        
        # 执行回放
        result = asyncio.run(service.playback_test_case(test_case_id))
        
        # 显示结果
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        click.echo(f"{status_icon} 回放完成")
        click.echo(f"   状态: {result['status']}")
        click.echo(f"   执行时间: {result.get('duration', 0):.2f}秒")
        click.echo(f"   成功步骤: {result.get('passed_steps', 0)}")
        click.echo(f"   失败步骤: {result.get('failed_steps', 0)}")
        
        if result.get('errors'):
            click.echo("   错误信息:")
            for error in result['errors']:
                click.echo(f"   - {error}")
        
        if report and result.get('report_path'):
            click.echo(f"   详细报告: {result['report_path']}")
            
    except Exception as e:
        click.echo(f"❌ 回放测试用例失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.argument('test_case_id')
@click.pass_context
def convert(ctx, test_case_id: str):
    """转换为Stagewise测试
    
    TEST_CASE_ID: 测试用例ID
    """
    try:
        service = get_record_as_test_service()
        
        # 转换为Stagewise测试
        stagewise_test_id = asyncio.run(service.convert_to_stagewise_test(test_case_id))
        
        click.echo(f"🔄 已转换为Stagewise测试")
        click.echo(f"   原测试ID: {test_case_id}")
        click.echo(f"   Stagewise测试ID: {stagewise_test_id}")
        
    except Exception as e:
        click.echo(f"❌ 转换失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='输出格式')
@click.pass_context
def list_sessions(ctx, format: str):
    """列出所有录制会话"""
    try:
        service = get_record_as_test_service()
        
        sessions = asyncio.run(service.get_session_list())
        
        if format == 'json':
            click.echo(json.dumps(sessions, ensure_ascii=False, indent=2))
        else:
            if not sessions:
                click.echo("📝 暂无录制会话")
                return
            
            click.echo("📝 录制会话列表:")
            click.echo()
            
            # 表格头
            click.echo(f"{'ID':<36} {'名称':<20} {'状态':<10} {'动作数':<8} {'持续时间':<12}")
            click.echo("-" * 90)
            
            # 表格内容
            for session in sessions:
                duration = f"{session.get('duration', 0):.1f}s" if session.get('duration') else "N/A"
                click.echo(f"{session['id']:<36} {session['name']:<20} {session['status']:<10} {session['actions_count']:<8} {duration:<12}")
            
    except Exception as e:
        click.echo(f"❌ 获取会话列表失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='输出格式')
@click.pass_context
def list_tests(ctx, format: str):
    """列出所有测试用例"""
    try:
        service = get_record_as_test_service()
        
        test_cases = asyncio.run(service.get_test_case_list())
        
        if format == 'json':
            click.echo(json.dumps(test_cases, ensure_ascii=False, indent=2))
        else:
            if not test_cases:
                click.echo("🧪 暂无测试用例")
                return
            
            click.echo("🧪 测试用例列表:")
            click.echo()
            
            # 表格头
            click.echo(f"{'ID':<36} {'名称':<25} {'步骤数':<8} {'优化':<6} {'创建时间':<20}")
            click.echo("-" * 100)
            
            # 表格内容
            for test_case in test_cases:
                optimized = "✅" if test_case['optimized'] else "❌"
                created_time = datetime.fromisoformat(test_case['created_time']).strftime('%Y-%m-%d %H:%M')
                click.echo(f"{test_case['id']:<36} {test_case['name']:<25} {test_case['steps_count']:<8} {optimized:<6} {created_time:<20}")
            
    except Exception as e:
        click.echo(f"❌ 获取测试用例列表失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.option('--days', '-d', type=int, default=30, help='清理多少天前的数据')
@click.option('--confirm', is_flag=True, help='确认清理')
@click.pass_context
def cleanup(ctx, days: int, confirm: bool):
    """清理旧的录制数据
    
    清理指定天数之前的录制会话和相关文件
    """
    if not confirm:
        click.echo(f"⚠️ 将清理 {days} 天前的录制数据")
        click.echo("使用 --confirm 参数确认清理")
        return
    
    try:
        service = get_record_as_test_service()
        
        cleaned_count = asyncio.run(service.cleanup_old_recordings(days))
        
        click.echo(f"🧹 清理完成")
        click.echo(f"   清理了 {cleaned_count} 个录制会话")
        
    except Exception as e:
        click.echo(f"❌ 清理失败: {e}", err=True)
        sys.exit(1)

@record.command()
@click.pass_context
def status(ctx):
    """显示录制即测试服务状态"""
    try:
        service = get_record_as_test_service()
        
        sessions = asyncio.run(service.get_session_list())
        test_cases = asyncio.run(service.get_test_case_list())
        
        # 统计信息
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s['status'] == 'recording'])
        completed_sessions = len([s for s in sessions if s['status'] == 'completed'])
        
        total_tests = len(test_cases)
        optimized_tests = len([t for t in test_cases if t['optimized']])
        
        click.echo("📊 录制即测试服务状态")
        click.echo()
        click.echo(f"录制会话:")
        click.echo(f"  总数: {total_sessions}")
        click.echo(f"  进行中: {active_sessions}")
        click.echo(f"  已完成: {completed_sessions}")
        click.echo()
        click.echo(f"测试用例:")
        click.echo(f"  总数: {total_tests}")
        click.echo(f"  已优化: {optimized_tests}")
        click.echo(f"  优化率: {(optimized_tests/total_tests*100):.1f}%" if total_tests > 0 else "  优化率: N/A")
        
        # 存储信息
        storage_config = service.config.get('storage', {})
        click.echo()
        click.echo(f"存储配置:")
        click.echo(f"  录制目录: {storage_config.get('recordings_path', './recordings')}")
        click.echo(f"  测试目录: {storage_config.get('tests_path', './generated_tests')}")
        click.echo(f"  视频目录: {storage_config.get('videos_path', './videos')}")
        
    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}", err=True)
        sys.exit(1)

# 主入口点
if __name__ == '__main__':
    record()

