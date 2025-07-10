"""
File Watcher - 文件监控器
实时监控文件系统变化，支持跨平台

真实实现，使用系统级文件监控
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Set
import fnmatch
from datetime import datetime

# 尝试导入watchdog，如果没有则使用轮询方式
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileSystemEvent = None

class FileChangeEvent:
    """文件变化事件"""
    
    def __init__(self, file_path: str, event_type: str, timestamp: float = None):
        self.file_path = file_path
        self.event_type = event_type  # created, modified, deleted, moved
        self.timestamp = timestamp or time.time()
        self.event_id = f"{event_type}_{int(self.timestamp)}_{hash(file_path)}"

class PollingWatcher:
    """轮询方式的文件监控器（备用方案）"""
    
    def __init__(self, path: str, callback: Callable, ignore_patterns: List[str] = None):
        self.path = Path(path)
        self.callback = callback
        self.ignore_patterns = ignore_patterns or []
        self.file_states = {}
        self.is_running = False
        self.poll_interval = 1.0
        self.logger = logging.getLogger("PollingWatcher")
    
    async def start(self):
        """开始监控"""
        self.is_running = True
        self.logger.info(f"开始轮询监控: {self.path}")
        
        # 初始化文件状态
        await self._scan_files()
        
        # 开始轮询
        while self.is_running:
            try:
                await self._check_changes()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"轮询监控错误: {e}")
                await asyncio.sleep(1)
    
    async def stop(self):
        """停止监控"""
        self.is_running = False
        self.logger.info("停止轮询监控")
    
    async def _scan_files(self):
        """扫描文件状态"""
        try:
            for file_path in self.path.rglob("*"):
                if file_path.is_file() and not self._should_ignore(str(file_path)):
                    stat = file_path.stat()
                    self.file_states[str(file_path)] = {
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "exists": True
                    }
        except Exception as e:
            self.logger.error(f"扫描文件失败: {e}")
    
    async def _check_changes(self):
        """检查文件变化"""
        try:
            current_files = set()
            
            # 检查现有文件
            for file_path in self.path.rglob("*"):
                if file_path.is_file() and not self._should_ignore(str(file_path)):
                    file_str = str(file_path)
                    current_files.add(file_str)
                    
                    stat = file_path.stat()
                    current_state = {
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "exists": True
                    }
                    
                    if file_str in self.file_states:
                        # 检查是否修改
                        old_state = self.file_states[file_str]
                        if (current_state["size"] != old_state["size"] or 
                            current_state["mtime"] != old_state["mtime"]):
                            
                            relative_path = str(file_path.relative_to(self.path))
                            event = FileChangeEvent(relative_path, "modified")
                            await self.callback(event)
                    else:
                        # 新文件
                        relative_path = str(file_path.relative_to(self.path))
                        event = FileChangeEvent(relative_path, "created")
                        await self.callback(event)
                    
                    self.file_states[file_str] = current_state
            
            # 检查删除的文件
            deleted_files = set(self.file_states.keys()) - current_files
            for file_str in deleted_files:
                file_path = Path(file_str)
                relative_path = str(file_path.relative_to(self.path))
                event = FileChangeEvent(relative_path, "deleted")
                await self.callback(event)
                del self.file_states[file_str]
                
        except Exception as e:
            self.logger.error(f"检查文件变化失败: {e}")
    
    def _should_ignore(self, file_path: str) -> bool:
        """检查是否应该忽略文件"""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

class WatchdogHandler(FileSystemEventHandler):
    """Watchdog事件处理器"""
    
    def __init__(self, callback: Callable, base_path: str, ignore_patterns: List[str] = None):
        super().__init__()
        self.callback = callback
        self.base_path = Path(base_path)
        self.ignore_patterns = ignore_patterns or []
        self.logger = logging.getLogger("WatchdogHandler")
        
        # 防抖动
        self.debounce_delay = 0.5
        self.pending_events = {}
    
    def on_any_event(self, event: FileSystemEvent):
        """处理任何文件系统事件"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 检查是否应该忽略
        if self._should_ignore(str(file_path)):
            return
        
        try:
            relative_path = str(file_path.relative_to(self.base_path))
            
            # 映射事件类型
            event_type_map = {
                "created": "created",
                "modified": "modified", 
                "deleted": "deleted",
                "moved": "moved"
            }
            
            event_type = event_type_map.get(event.event_type, "modified")
            
            # 防抖动处理
            self._debounce_event(relative_path, event_type)
            
        except ValueError:
            # 文件不在监控路径内
            pass
        except Exception as e:
            self.logger.error(f"处理文件事件失败: {e}")
    
    def _debounce_event(self, file_path: str, event_type: str):
        """防抖动处理"""
        current_time = time.time()
        
        # 取消之前的事件
        if file_path in self.pending_events:
            self.pending_events[file_path].cancel()
        
        # 创建新的延迟任务
        async def delayed_callback():
            try:
                await asyncio.sleep(self.debounce_delay)
                event = FileChangeEvent(file_path, event_type, current_time)
                await self.callback(event)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.logger.error(f"延迟回调失败: {e}")
            finally:
                if file_path in self.pending_events:
                    del self.pending_events[file_path]
        
        task = asyncio.create_task(delayed_callback())
        self.pending_events[file_path] = task
    
    def _should_ignore(self, file_path: str) -> bool:
        """检查是否应该忽略文件"""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

class FileWatcher:
    """文件监控器 - 监控文件系统变化"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文件监控器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 监控配置
        self.ignore_patterns = self.config.get("ignore_patterns", [
            ".git/*", "node_modules/*", "*.tmp", "*.log", ".DS_Store",
            "__pycache__/*", "*.pyc", ".vscode/*", ".idea/*"
        ])
        self.debounce_delay = self.config.get("debounce_delay", 0.5)
        self.use_polling = self.config.get("use_polling", not WATCHDOG_AVAILABLE)
        
        # 状态管理
        self.is_running = False
        self.watch_path = None
        self.callback = None
        
        # 监控组件
        self.observer = None
        self.polling_watcher = None
        self.watch_task = None
        
        # 统计信息
        self.stats = {
            "events_processed": 0,
            "files_created": 0,
            "files_modified": 0,
            "files_deleted": 0,
            "last_event": None
        }
        
        self.logger.info(f"文件监控器初始化完成 (使用{'轮询' if self.use_polling else 'Watchdog'})")
    
    def set_callback(self, callback: Callable):
        """
        设置文件变化回调函数
        
        Args:
            callback: 回调函数，接收 (file_path: str, event_type: str) 参数
        """
        async def wrapper(event: FileChangeEvent):
            try:
                await callback(event.file_path, event.event_type)
                
                # 更新统计
                self.stats["events_processed"] += 1
                self.stats["last_event"] = event.timestamp
                
                if event.event_type == "created":
                    self.stats["files_created"] += 1
                elif event.event_type == "modified":
                    self.stats["files_modified"] += 1
                elif event.event_type == "deleted":
                    self.stats["files_deleted"] += 1
                
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")
        
        self.callback = wrapper
    
    async def start(self, watch_path: str):
        """
        开始监控文件变化
        
        Args:
            watch_path: 监控路径
        """
        try:
            self.logger.info(f"开始监控文件变化: {watch_path}")
            
            self.watch_path = Path(watch_path)
            
            if not self.watch_path.exists():
                raise ValueError(f"监控路径不存在: {watch_path}")
            
            if not self.callback:
                raise ValueError("未设置回调函数")
            
            self.is_running = True
            
            if self.use_polling or not WATCHDOG_AVAILABLE:
                # 使用轮询方式
                await self._start_polling_watcher()
            else:
                # 使用Watchdog
                await self._start_watchdog_observer()
            
            self.logger.info("✅ 文件监控启动成功")
            
        except Exception as e:
            self.logger.error(f"启动文件监控失败: {e}")
            raise
    
    async def stop(self):
        """停止文件监控"""
        try:
            self.logger.info("停止文件监控...")
            
            self.is_running = False
            
            # 停止Watchdog观察者
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            # 停止轮询监控
            if self.polling_watcher:
                await self.polling_watcher.stop()
                self.polling_watcher = None
            
            # 停止监控任务
            if self.watch_task:
                self.watch_task.cancel()
                try:
                    await self.watch_task
                except asyncio.CancelledError:
                    pass
                self.watch_task = None
            
            self.logger.info("✅ 文件监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止文件监控失败: {e}")
    
    async def add_ignore_pattern(self, pattern: str):
        """添加忽略模式"""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            self.logger.info(f"添加忽略模式: {pattern}")
    
    async def remove_ignore_pattern(self, pattern: str):
        """移除忽略模式"""
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
            self.logger.info(f"移除忽略模式: {pattern}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控器状态"""
        return {
            "is_running": self.is_running,
            "watch_path": str(self.watch_path) if self.watch_path else None,
            "use_polling": self.use_polling,
            "watchdog_available": WATCHDOG_AVAILABLE,
            "ignore_patterns": self.ignore_patterns,
            "debounce_delay": self.debounce_delay,
            "stats": self.stats
        }
    
    async def _start_watchdog_observer(self):
        """启动Watchdog观察者"""
        try:
            handler = WatchdogHandler(
                callback=self.callback,
                base_path=str(self.watch_path),
                ignore_patterns=self.ignore_patterns
            )
            
            self.observer = Observer()
            self.observer.schedule(handler, str(self.watch_path), recursive=True)
            self.observer.start()
            
            self.logger.info("Watchdog观察者启动成功")
            
        except Exception as e:
            self.logger.error(f"启动Watchdog观察者失败: {e}")
            raise
    
    async def _start_polling_watcher(self):
        """启动轮询监控"""
        try:
            self.polling_watcher = PollingWatcher(
                path=str(self.watch_path),
                callback=self.callback,
                ignore_patterns=self.ignore_patterns
            )
            
            self.watch_task = asyncio.create_task(self.polling_watcher.start())
            
            self.logger.info("轮询监控启动成功")
            
        except Exception as e:
            self.logger.error(f"启动轮询监控失败: {e}")
            raise
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("FileWatcher")
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

