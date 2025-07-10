"""
Local Adapter Engine - 本地适配引擎
专注于本地资源管理和能力提供

通过 Deployment MCP 接收部署指令并在本地执行
"""

import asyncio
import json
import logging
import os
import sys
import time
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List
import toml

# 本地组件导入
try:
    from .local_resource_manager import LocalResourceManager, SystemInfo, ResourceUsage
    from .platform.platform_detector import PlatformDetector
    from .platform.command_adapter import CommandAdapter
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from local_resource_manager import LocalResourceManager, SystemInfo, ResourceUsage
    from platform.platform_detector import PlatformDetector
    from platform.command_adapter import CommandAdapter

class LocalAdapterEngine:
    """本地适配引擎 - 专注本地能力的核心引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化本地适配引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "local_adapter_config.toml"
        self.config = self._load_config()
        self.logger = self._setup_logger()
        
        # 核心组件
        self.resource_manager = LocalResourceManager(self.config.get("resource_manager", {}))
        self.platform_detector = PlatformDetector()
        self.command_adapter = CommandAdapter()
        
        # 本地环境信息
        self.environment_id = self.config.get("environment_id", f"local_adapter_{int(time.time())}")
        self.environment_type = None
        self.platform_info = None
        
        # 运行状态
        self.is_running = False
        self.start_time = None
        
        # 部署管理
        self.active_deployments = {}
        self.deployment_history = []
        
        self.logger.info(f"本地适配引擎初始化 - 环境ID: {self.environment_id}")
    
    async def start(self):
        """启动本地适配引擎"""
        try:
            self.logger.info("启动本地适配引擎...")
            
            # 检测平台信息
            await self._detect_platform()
            
            # 启动资源管理器
            await self.resource_manager.start()
            
            # 初始化命令适配器
            await self.command_adapter.initialize(self.platform_info)
            
            self.is_running = True
            self.start_time = time.time()
            
            self.logger.info(f"本地适配引擎启动成功 - 平台: {self.environment_type}")
            
        except Exception as e:
            self.logger.error(f"启动本地适配引擎失败: {e}")
            raise
    
    async def stop(self):
        """停止本地适配引擎"""
        try:
            self.logger.info("停止本地适配引擎...")
            
            self.is_running = False
            
            # 停止资源管理器
            if self.resource_manager:
                await self.resource_manager.stop()
            
            self.logger.info("本地适配引擎已停止")
            
        except Exception as e:
            self.logger.error(f"停止本地适配引擎失败: {e}")
    
    async def _detect_platform(self):
        """检测平台信息"""
        try:
            self.platform_info = await self.platform_detector.detect()
            self.environment_type = self.platform_info.get("environment_type")
            
            self.logger.info(f"平台检测完成: {self.platform_info}")
            
        except Exception as e:
            self.logger.error(f"平台检测失败: {e}")
            raise
    
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行本地命令
        
        Args:
            command: 要执行的命令
            **kwargs: 命令参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            self.logger.info(f"执行本地命令: {command}")
            
            # 通过命令适配器执行
            result = await self.command_adapter.execute_command(
                command, 
                platform=self.environment_type,
                **kwargs
            )
            
            self.logger.debug(f"命令执行结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        获取本地能力信息
        
        Returns:
            Dict: 能力信息
        """
        try:
            # 获取资源管理器的能力摘要
            capabilities = await self.resource_manager.get_capabilities_summary()
            
            # 添加平台信息
            capabilities.update({
                "environment_id": self.environment_id,
                "environment_type": self.environment_type,
                "platform_info": self.platform_info,
                "engine_status": {
                    "is_running": self.is_running,
                    "start_time": self.start_time,
                    "uptime": time.time() - self.start_time if self.start_time else 0
                }
            })
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"获取能力信息失败: {e}")
            return {"error": str(e)}
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """
        获取资源状态
        
        Returns:
            Dict: 资源状态
        """
        try:
            current_usage = self.resource_manager.get_current_usage()
            average_usage = self.resource_manager.get_average_usage()
            system_info = self.resource_manager.get_system_info()
            
            return {
                "system_info": system_info.__dict__ if system_info else None,
                "current_usage": current_usage.__dict__ if current_usage else None,
                "average_usage": average_usage,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取资源状态失败: {e}")
            return {"error": str(e)}
    
    async def execute_deployment_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行部署任务
        
        Args:
            task_config: 部署任务配置
            
        Returns:
            Dict: 执行结果
        """
        try:
            task_id = task_config.get("task_id", f"task_{int(time.time())}")
            self.logger.info(f"执行部署任务: {task_id}")
            
            # 记录活跃部署
            self.active_deployments[task_id] = {
                "config": task_config,
                "start_time": time.time(),
                "status": "running"
            }
            
            # 根据任务类型执行相应操作
            task_type = task_config.get("type", "unknown")
            
            if task_type == "shell_command":
                result = await self._execute_shell_deployment(task_config)
            elif task_type == "file_operation":
                result = await self._execute_file_deployment(task_config)
            elif task_type == "service_management":
                result = await self._execute_service_deployment(task_config)
            else:
                result = {
                    "success": False,
                    "error": f"不支持的任务类型: {task_type}"
                }
            
            # 更新部署状态
            self.active_deployments[task_id].update({
                "status": "completed" if result.get("success") else "failed",
                "end_time": time.time(),
                "result": result
            })
            
            # 移动到历史记录
            self.deployment_history.append(self.active_deployments.pop(task_id))
            
            # 保持历史记录在合理范围内
            if len(self.deployment_history) > 100:
                self.deployment_history = self.deployment_history[-100:]
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行部署任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    async def _execute_shell_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行Shell命令部署"""
        try:
            command = config.get("command")
            if not command:
                return {"success": False, "error": "缺少命令参数"}
            
            result = await self.execute_command(command, **config.get("params", {}))
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_file_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作部署"""
        try:
            operation = config.get("operation")
            source = config.get("source")
            target = config.get("target")
            
            if operation == "copy":
                command = f"cp -r {source} {target}"
            elif operation == "move":
                command = f"mv {source} {target}"
            elif operation == "delete":
                command = f"rm -rf {target}"
            else:
                return {"success": False, "error": f"不支持的文件操作: {operation}"}
            
            result = await self.execute_command(command)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_service_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行服务管理部署"""
        try:
            action = config.get("action")
            service = config.get("service")
            
            if action == "start":
                command = f"systemctl start {service}"
            elif action == "stop":
                command = f"systemctl stop {service}"
            elif action == "restart":
                command = f"systemctl restart {service}"
            elif action == "status":
                command = f"systemctl status {service}"
            else:
                return {"success": False, "error": f"不支持的服务操作: {action}"}
            
            result = await self.execute_command(command)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
                return config
            else:
                # 返回默认配置
                return {
                    "environment_id": f"local_adapter_{int(time.time())}",
                    "resource_manager": {
                        "monitor_interval": 10,
                        "history_size": 100
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                }
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(__name__)
        
        # 避免重复设置
        if logger.handlers:
            return logger
        
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))
        format_str = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(level)
        
        return logger
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "environment_id": self.environment_id,
            "environment_type": self.environment_type,
            "active_deployments": len(self.active_deployments),
            "deployment_history_count": len(self.deployment_history),
            "resource_manager_status": self.resource_manager.get_status() if self.resource_manager else None
        }


# CLI主函数
async def cli_main():
    """CLI主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local Adapter Engine")
    parser.add_argument("--config", "-c", help="配置文件路径", default="config.toml")
    parser.add_argument("--host", help="服务器主机", default="0.0.0.0")
    parser.add_argument("--port", "-p", type=int, help="服务器端口", default=5000)
    parser.add_argument("--log-level", help="日志级别", default="INFO")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 启动命令
    start_parser = subparsers.add_parser("start", help="启动Local Adapter Engine")
    start_parser.add_argument("--daemon", "-d", action="store_true", help="后台运行")
    
    # 停止命令
    stop_parser = subparsers.add_parser("stop", help="停止Local Adapter Engine")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="查看引擎状态")
    
    args = parser.parse_args()
    
    if args.command == "start":
        engine = LocalAdapterEngine(args.config)
        try:
            await engine.start()
            # 保持运行
            while engine.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭...")
            await engine.stop()
    
    elif args.command == "stop":
        print("停止Local Adapter Engine...")
        # 这里可以添加停止逻辑
    
    elif args.command == "status":
        engine = LocalAdapterEngine(args.config)
        status = engine.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(cli_main())

