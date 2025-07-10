"""
Mirror Engine - 代码镜像引擎
实现真实的端云代码同步和协作功能

支持从Mac端Claude Code启动，实现实时文件同步
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import hashlib
import shutil

# 修复导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 尝试导入组件
try:
    from ..sync.sync_manager import SyncManager
    from ..communication.comm_manager import CommunicationManager
    from ..git_integration.git_manager import GitManager
    from ..file_monitor.file_watcher import FileWatcher
except ImportError:
    try:
        from sync.sync_manager import SyncManager
        from communication.comm_manager import CommunicationManager
        from git_integration.git_manager import GitManager
        from file_monitor.file_watcher import FileWatcher
    except ImportError:
        # 如果仍然失败，导入单个文件
        sys.path.insert(0, os.path.join(parent_dir, "sync"))
        sys.path.insert(0, os.path.join(parent_dir, "communication"))
        sys.path.insert(0, os.path.join(parent_dir, "git_integration"))
        sys.path.insert(0, os.path.join(parent_dir, "file_monitor"))
        
        from sync_manager import SyncManager
        from comm_manager import CommunicationManager
        from git_manager import GitManager
        from file_watcher import FileWatcher

class MirrorEngine:
    """Mirror引擎 - 代码镜像的核心控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Mirror引擎
        
        Args:
            config: 配置信息
        """
        self.config = config or self._get_default_config()
        
        # 状态管理 - 需要在logger之前初始化
        self.is_running = False
        self.start_time = None
        self.session_id = f"mirror_{int(time.time())}"
        
        # 初始化logger
        self.logger = self._setup_logger()
        
        # 同步状态
        self.local_path = self.config.get("local_path", "/Users/alexchuang/Desktop/alex/tests/package")
        self.remote_endpoint = self.config.get("remote_endpoint", "ws://localhost:8081/socket.io/")
        self.sync_stats = {
            "files_synced": 0,
            "bytes_transferred": 0,
            "last_sync": None
        }
        
        # 核心组件
        self.sync_manager = SyncManager(self.config.get("sync", {}))
        self.comm_manager = CommunicationManager(self.config.get("communication", {}))
        self.git_manager = GitManager(self.config.get("git", {}))
        self.file_watcher = FileWatcher(self.config.get("file_monitor", {}))
        
        # 活跃连接
        self.active_connections = set()
        self.peer_sessions = {}
        
        self.logger.info(f"Mirror引擎初始化完成 - 会话ID: {self.session_id}")
    
    async def start(self, local_path: Optional[str] = None) -> Dict[str, Any]:
        """
        启动Mirror引擎
        
        Args:
            local_path: 本地路径（从Claude Code传入）
            
        Returns:
            Dict: 启动结果
        """
        try:
            if local_path:
                self.local_path = local_path
                
            self.logger.info(f"启动Mirror引擎 - 本地路径: {self.local_path}")
            
            # 验证本地路径
            if not os.path.exists(self.local_path):
                raise ValueError(f"本地路径不存在: {self.local_path}")
            
            # 启动核心组件
            await self._start_components()
            
            # 建立通信连接
            await self._establish_connections()
            
            # 开始文件监控
            await self._start_file_monitoring()
            
            # 执行初始同步
            await self._initial_sync()
            
            self.is_running = True
            self.start_time = time.time()
            
            result = {
                "success": True,
                "session_id": self.session_id,
                "local_path": self.local_path,
                "remote_endpoint": self.remote_endpoint,
                "message": "Mirror引擎启动成功，开始实时同步"
            }
            
            self.logger.info("✅ Mirror引擎启动成功")
            return result
            
        except Exception as e:
            self.logger.error(f"启动Mirror引擎失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    async def stop(self) -> Dict[str, Any]:
        """
        停止Mirror引擎
        
        Returns:
            Dict: 停止结果
        """
        try:
            self.logger.info("停止Mirror引擎...")
            
            self.is_running = False
            
            # 停止文件监控
            if self.file_watcher:
                await self.file_watcher.stop()
            
            # 关闭通信连接
            if self.comm_manager:
                await self.comm_manager.disconnect_all()
            
            # 停止同步管理器
            if self.sync_manager:
                await self.sync_manager.stop()
            
            result = {
                "success": True,
                "session_id": self.session_id,
                "sync_stats": self.sync_stats,
                "message": "Mirror引擎已停止"
            }
            
            self.logger.info("✅ Mirror引擎已停止")
            return result
            
        except Exception as e:
            self.logger.error(f"停止Mirror引擎失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        同步单个文件
        
        Args:
            file_path: 文件路径
            content: 文件内容（可选，如果不提供则读取文件）
            
        Returns:
            Dict: 同步结果
        """
        try:
            full_path = os.path.join(self.local_path, file_path)
            
            # 读取文件内容
            if content is None:
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    return {"success": False, "error": f"文件不存在: {file_path}"}
            
            # 计算文件哈希
            file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # 创建同步数据
            sync_data = {
                "type": "file_sync",
                "session_id": self.session_id,
                "file_path": file_path,
                "content": content,
                "hash": file_hash,
                "timestamp": time.time(),
                "size": len(content.encode('utf-8'))
            }
            
            # 通过同步管理器处理
            result = await self.sync_manager.sync_file(sync_data)
            
            # 广播到所有连接
            await self.comm_manager.broadcast(sync_data)
            
            # 更新统计
            if result.get("success"):
                self.sync_stats["files_synced"] += 1
                self.sync_stats["bytes_transferred"] += sync_data["size"]
                self.sync_stats["last_sync"] = datetime.now().isoformat()
            
            self.logger.info(f"文件同步完成: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"文件同步失败: {e}")
            self.sync_stats["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    async def receive_sync(self, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收远程同步数据
        
        Args:
            sync_data: 同步数据
            
        Returns:
            Dict: 处理结果
        """
        try:
            file_path = sync_data.get("file_path")
            content = sync_data.get("content")
            remote_hash = sync_data.get("hash")
            
            if not all([file_path, content, remote_hash]):
                return {"success": False, "error": "同步数据不完整"}
            
            # 验证哈希
            local_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            if local_hash != remote_hash:
                return {"success": False, "error": "文件哈希验证失败"}
            
            # 写入本地文件
            full_path = os.path.join(self.local_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新统计
            self.sync_stats["files_synced"] += 1
            self.sync_stats["bytes_transferred"] += len(content.encode('utf-8'))
            self.sync_stats["last_sync"] = datetime.now().isoformat()
            
            result = {
                "success": True,
                "file_path": file_path,
                "size": len(content.encode('utf-8')),
                "message": "远程文件同步成功"
            }
            
            self.logger.info(f"接收远程同步: {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"接收同步失败: {e}")
            self.sync_stats["errors"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取Mirror引擎状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "local_path": self.local_path,
            "remote_endpoint": self.remote_endpoint,
            "sync_stats": self.sync_stats,
            "active_connections": len(self.active_connections),
            "peer_sessions": list(self.peer_sessions.keys()),
            "components_status": {
                "sync_manager": self.sync_manager.get_status() if self.sync_manager else None,
                "comm_manager": self.comm_manager.get_status() if self.comm_manager else None,
                "git_manager": self.git_manager.get_status() if self.git_manager else None,
                "file_watcher": self.file_watcher.get_status() if self.file_watcher else None
            }
        }
    
    async def list_files(self, pattern: str = "*") -> Dict[str, Any]:
        """
        列出本地文件
        
        Args:
            pattern: 文件模式
            
        Returns:
            Dict: 文件列表
        """
        try:
            from pathlib import Path
            import fnmatch
            
            files = []
            base_path = Path(self.local_path)
            
            for file_path in base_path.rglob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(base_path)
                    stat = file_path.stat()
                    
                    files.append({
                        "path": str(relative_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "is_synced": await self._is_file_synced(str(relative_path))
                    })
            
            return {
                "success": True,
                "files": files,
                "total_count": len(files),
                "local_path": self.local_path
            }
            
        except Exception as e:
            self.logger.error(f"列出文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _start_components(self):
        """启动核心组件"""
        # 启动同步管理器
        await self.sync_manager.start()
        
        # 启动通信管理器
        await self.comm_manager.start()
        
        # 启动Git管理器
        await self.git_manager.start(self.local_path)
        
        self.logger.info("核心组件启动完成")
    
    async def _establish_connections(self):
        """建立通信连接"""
        try:
            # 连接到远程端点
            connection = await self.comm_manager.connect(self.remote_endpoint)
            if connection:
                self.active_connections.add(connection)
                self.logger.info(f"连接到远程端点: {self.remote_endpoint}")
            else:
                self.logger.warning(f"无法连接到远程端点: {self.remote_endpoint}")
        except Exception as e:
            self.logger.warning(f"建立连接失败: {e}")
    
    async def _start_file_monitoring(self):
        """开始文件监控"""
        # 设置文件变化回调
        self.file_watcher.set_callback(self._on_file_changed)
        
        # 开始监控
        await self.file_watcher.start(self.local_path)
        
        self.logger.info(f"开始监控文件变化: {self.local_path}")
    
    async def _initial_sync(self):
        """执行初始同步"""
        try:
            # 获取所有文件
            files_result = await self.list_files()
            if not files_result.get("success"):
                return
            
            files = files_result.get("files", [])
            self.logger.info(f"开始初始同步，共 {len(files)} 个文件")
            
            # 同步每个文件
            for file_info in files[:10]:  # 限制初始同步文件数量
                await self.sync_file(file_info["path"])
                await asyncio.sleep(0.1)  # 避免过快同步
            
            self.logger.info("初始同步完成")
            
        except Exception as e:
            self.logger.error(f"初始同步失败: {e}")
    
    async def _on_file_changed(self, file_path: str, event_type: str):
        """文件变化回调"""
        try:
            self.logger.info(f"文件变化: {file_path} ({event_type})")
            
            if event_type in ["modified", "created"]:
                # 延迟一点时间，确保文件写入完成
                await asyncio.sleep(0.5)
                await self.sync_file(file_path)
            elif event_type == "deleted":
                # 处理文件删除
                await self._handle_file_deletion(file_path)
                
        except Exception as e:
            self.logger.error(f"处理文件变化失败: {e}")
    
    async def _handle_file_deletion(self, file_path: str):
        """处理文件删除"""
        delete_data = {
            "type": "file_delete",
            "session_id": self.session_id,
            "file_path": file_path,
            "timestamp": time.time()
        }
        
        await self.comm_manager.broadcast(delete_data)
        self.logger.info(f"广播文件删除: {file_path}")
    
    async def _is_file_synced(self, file_path: str) -> bool:
        """检查文件是否已同步"""
        # 这里可以实现更复杂的同步状态检查
        return True
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "local_path": "/Users/alexchuang/Desktop/alex/tests/package",
            "remote_endpoint": "ws://localhost:8080/mirror",
            "sync": {
                "auto_sync": True,
                "sync_interval": 1.0,
                "batch_size": 10
            },
            "communication": {
                "reconnect_interval": 5.0,
                "heartbeat_interval": 30.0
            },
            "git": {
                "auto_commit": False,
                "commit_message_template": "Mirror sync: {files_count} files"
            },
            "file_monitor": {
                "ignore_patterns": [".git/*", "node_modules/*", "*.tmp"],
                "debounce_delay": 0.5
            },
            "logging": {
                "level": "INFO"
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(f"MirrorEngine.{self.session_id}")
        
        if logger.handlers:
            return logger
        
        level = self.config.get("logging", {}).get("level", "INFO")
        logger.setLevel(getattr(logging, level))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger


# CLI接口，支持从Claude Code调用
async def launch_mirror(local_path: str = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    启动Mirror Code功能 - 从Claude Code调用的入口
    
    Args:
        local_path: 本地路径
        config: 配置信息
        
    Returns:
        Dict: 启动结果
    """
    try:
        # 如果没有提供路径，使用当前工作目录
        if not local_path:
            local_path = os.getcwd()
        
        # 创建Mirror引擎
        engine = MirrorEngine(config)
        
        # 启动引擎
        result = await engine.start(local_path)
        
        if result.get("success"):
            # 保持引擎运行
            print(f"🪞 Mirror Code 启动成功!")
            print(f"📁 本地路径: {local_path}")
            print(f"🔗 会话ID: {result['session_id']}")
            print(f"🚀 开始实时同步...")
            
            # 返回引擎实例以便后续操作
            result["engine"] = engine
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # 支持直接运行
    import sys
    
    local_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(launch_mirror(local_path))
    
    if result.get("success"):
        print("Mirror Code 启动成功!")
        # 保持运行
        try:
            engine = result["engine"]
            while engine.is_running:
                asyncio.run(asyncio.sleep(1))
        except KeyboardInterrupt:
            print("\n停止Mirror Code...")
            asyncio.run(engine.stop())
    else:
        print(f"启动失败: {result.get('error')}")

