#!/usr/bin/env python3
"""
Mirror Code 启动脚本
从Claude Code或命令行启动Mirror Code功能

使用方法:
1. 在Claude Code中: /run python launch_mirror.py
2. 命令行: python launch_mirror.py [path]
3. 作为模块: from launch_mirror import start_mirror_code
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.mirror_engine import MirrorEngine, launch_mirror

class MirrorCodeLauncher:
    """Mirror Code启动器"""
    
    def __init__(self):
        self.engine = None
        self.config = self._get_default_config()
    
    async def start(self, local_path: Optional[str] = None, 
                   remote_endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        启动Mirror Code
        
        Args:
            local_path: 本地路径
            remote_endpoint: 远程端点
            
        Returns:
            Dict: 启动结果
        """
        try:
            # 使用提供的参数更新配置
            if local_path:
                self.config["local_path"] = local_path
            if remote_endpoint:
                self.config["remote_endpoint"] = remote_endpoint
            
            # 创建并启动引擎
            self.engine = MirrorEngine(self.config)
            result = await self.engine.start(self.config["local_path"])
            
            if result.get("success"):
                print("🪞 Mirror Code 启动成功!")
                print(f"📁 本地路径: {self.config['local_path']}")
                print(f"🔗 远程端点: {self.config['remote_endpoint']}")
                print(f"🆔 会话ID: {result['session_id']}")
                print("🚀 开始实时同步...")
                print("\n按 Ctrl+C 停止")
                
                # 显示状态信息
                await self._show_status()
                
                # 保持运行
                await self._keep_running()
            
            return result
            
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号...")
            return await self.stop()
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop(self) -> Dict[str, Any]:
        """停止Mirror Code"""
        try:
            if self.engine:
                result = await self.engine.stop()
                print("✅ Mirror Code 已停止")
                return result
            else:
                return {"success": True, "message": "引擎未运行"}
                
        except Exception as e:
            print(f"❌ 停止失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        if self.engine:
            return await self.engine.get_status()
        else:
            return {"success": False, "error": "引擎未运行"}
    
    async def _show_status(self):
        """显示状态信息"""
        try:
            if self.engine:
                status = await self.engine.get_status()
                print("\n📊 当前状态:")
                print(f"   运行状态: {'✅ 运行中' if status['is_running'] else '❌ 已停止'}")
                print(f"   活跃连接: {status['active_connections']}")
                print(f"   同步统计: {status['sync_stats']['files_synced']} 文件")
                print(f"   最后同步: {status['sync_stats']['last_sync'] or '无'}")
                
        except Exception as e:
            print(f"⚠️ 获取状态失败: {e}")
    
    async def _keep_running(self):
        """保持运行"""
        try:
            while self.engine and self.engine.is_running:
                await asyncio.sleep(5)
                # 每5秒显示一次简要状态
                if self.engine:
                    status = await self.engine.get_status()
                    files_synced = status['sync_stats']['files_synced']
                    connections = status['active_connections']
                    print(f"🔄 运行中... 已同步 {files_synced} 文件, {connections} 个连接")
                    
        except KeyboardInterrupt:
            pass
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "local_path": os.getcwd(),  # 当前工作目录
            "remote_endpoint": "ws://localhost:8081/socket.io/",
            "sync": {
                "auto_sync": True,
                "sync_interval": 1.0,
                "batch_size": 10
            },
            "communication": {
                "reconnect_interval": 5.0,
                "heartbeat_interval": 30.0,
                "server_host": "0.0.0.0",
                "server_port": 8081
            },
            "git": {
                "auto_commit": False,
                "commit_message_template": "Mirror sync: {files_count} files",
                "author_name": "Mirror Code",
                "author_email": "mirror@example.com"
            },
            "file_monitor": {
                "ignore_patterns": [
                    ".git/*", "node_modules/*", "*.tmp", "*.log", 
                    ".DS_Store", "__pycache__/*", "*.pyc", 
                    ".vscode/*", ".idea/*", "*.swp", "*.swo"
                ],
                "debounce_delay": 0.5,
                "use_polling": False
            },
            "logging": {
                "level": "INFO"
            }
        }

# 便捷函数
async def start_mirror_code(local_path: Optional[str] = None, 
                           remote_endpoint: Optional[str] = None) -> Dict[str, Any]:
    """
    启动Mirror Code的便捷函数
    
    Args:
        local_path: 本地路径
        remote_endpoint: 远程端点
        
    Returns:
        Dict: 启动结果
    """
    launcher = MirrorCodeLauncher()
    return await launcher.start(local_path, remote_endpoint)

def print_usage():
    """打印使用说明"""
    print("""
🪞 Mirror Code - 实时代码同步工具

使用方法:
  python launch_mirror.py [选项]

选项:
  -p, --path PATH        本地路径 (默认: 当前目录)
  -r, --remote URL       远程端点 (默认: ws://localhost:8080/mirror)
  -h, --help            显示帮助信息

示例:
  python launch_mirror.py
  python launch_mirror.py -p /path/to/project
  python launch_mirror.py -r ws://example.com:8081/socket.io/

在Claude Code中使用:
  /run python launch_mirror.py
  /run python launch_mirror.py -p .
    """)

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Mirror Code - 实时代码同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-p", "--path", 
        default=None,
        help="本地路径 (默认: 当前目录)"
    )
    
    parser.add_argument(
        "-r", "--remote",
        default=None,
        help="远程端点 (默认: ws://localhost:8081/socket.io/)"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="显示状态信息"
    )
    
    args = parser.parse_args()
    
    # 如果没有参数且不是状态查询，显示使用说明
    if len(sys.argv) == 1 and not args.status:
        print_usage()
        return
    
    # 确定本地路径
    local_path = args.path or os.getcwd()
    
    # 验证路径
    if not os.path.exists(local_path):
        print(f"❌ 路径不存在: {local_path}")
        return
    
    print(f"🪞 Mirror Code 启动器")
    print(f"📁 本地路径: {local_path}")
    
    if args.remote:
        print(f"🔗 远程端点: {args.remote}")
    
    print()
    
    # 启动Mirror Code
    launcher = MirrorCodeLauncher()
    
    try:
        result = await launcher.start(local_path, args.remote)
        
        if not result.get("success"):
            print(f"❌ 启动失败: {result.get('error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

