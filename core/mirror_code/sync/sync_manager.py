"""
Sync Manager - 同步管理器
处理文件同步逻辑，冲突解决，版本控制

真实实现，无Mock代码
"""

import asyncio
import json
import logging
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import sqlite3
import threading

class SyncRecord:
    """同步记录"""
    
    def __init__(self, file_path: str, hash_value: str, timestamp: float, 
                 session_id: str, size: int = 0):
        self.file_path = file_path
        self.hash_value = hash_value
        self.timestamp = timestamp
        self.session_id = session_id
        self.size = size
        self.sync_id = f"{session_id}_{int(timestamp)}"

class ConflictResolver:
    """冲突解决器"""
    
    def __init__(self):
        self.resolution_strategies = {
            "latest_wins": self._latest_wins_strategy,
            "manual": self._manual_strategy,
            "merge": self._merge_strategy
        }
    
    async def resolve_conflict(self, local_record: SyncRecord, 
                             remote_record: SyncRecord, 
                             strategy: str = "latest_wins") -> Dict[str, Any]:
        """
        解决同步冲突
        
        Args:
            local_record: 本地记录
            remote_record: 远程记录
            strategy: 解决策略
            
        Returns:
            Dict: 解决结果
        """
        resolver = self.resolution_strategies.get(strategy, self._latest_wins_strategy)
        return await resolver(local_record, remote_record)
    
    async def _latest_wins_strategy(self, local_record: SyncRecord, 
                                  remote_record: SyncRecord) -> Dict[str, Any]:
        """最新版本获胜策略"""
        if remote_record.timestamp > local_record.timestamp:
            return {
                "action": "accept_remote",
                "winner": "remote",
                "reason": "remote_is_newer"
            }
        else:
            return {
                "action": "keep_local",
                "winner": "local", 
                "reason": "local_is_newer_or_equal"
            }
    
    async def _manual_strategy(self, local_record: SyncRecord, 
                             remote_record: SyncRecord) -> Dict[str, Any]:
        """手动解决策略"""
        return {
            "action": "manual_required",
            "local_record": local_record.__dict__,
            "remote_record": remote_record.__dict__,
            "reason": "manual_resolution_required"
        }
    
    async def _merge_strategy(self, local_record: SyncRecord, 
                            remote_record: SyncRecord) -> Dict[str, Any]:
        """合并策略（简单实现）"""
        # 这里可以实现更复杂的文件合并逻辑
        return {
            "action": "merge_required",
            "local_record": local_record.__dict__,
            "remote_record": remote_record.__dict__,
            "reason": "content_merge_needed"
        }

class SyncDatabase:
    """同步数据库"""
    
    def __init__(self, db_path: str = "mirror_sync.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_records (
                    sync_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    hash_value TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    session_id TEXT NOT NULL,
                    size INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON sync_records(file_path)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON sync_records(timestamp)
            """)
    
    def save_record(self, record: SyncRecord) -> bool:
        """保存同步记录"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO sync_records 
                        (sync_id, file_path, hash_value, timestamp, session_id, size)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (record.sync_id, record.file_path, record.hash_value, 
                         record.timestamp, record.session_id, record.size))
            return True
        except Exception as e:
            logging.error(f"保存同步记录失败: {e}")
            return False
    
    def get_record(self, file_path: str) -> Optional[SyncRecord]:
        """获取文件的最新同步记录"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT sync_id, file_path, hash_value, timestamp, session_id, size
                        FROM sync_records 
                        WHERE file_path = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (file_path,))
                    
                    row = cursor.fetchone()
                    if row:
                        return SyncRecord(
                            file_path=row[1],
                            hash_value=row[2], 
                            timestamp=row[3],
                            session_id=row[4],
                            size=row[5]
                        )
            return None
        except Exception as e:
            logging.error(f"获取同步记录失败: {e}")
            return None
    
    def get_all_records(self, limit: int = 100) -> List[SyncRecord]:
        """获取所有同步记录"""
        records = []
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT sync_id, file_path, hash_value, timestamp, session_id, size
                        FROM sync_records 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                    
                    for row in cursor.fetchall():
                        records.append(SyncRecord(
                            file_path=row[1],
                            hash_value=row[2],
                            timestamp=row[3], 
                            session_id=row[4],
                            size=row[5]
                        ))
        except Exception as e:
            logging.error(f"获取所有记录失败: {e}")
        
        return records

class SyncManager:
    """同步管理器 - 处理文件同步的核心逻辑"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化同步管理器
        
        Args:
            config: 配置信息
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 核心组件
        self.database = SyncDatabase(self.config.get("db_path", "mirror_sync.db"))
        self.conflict_resolver = ConflictResolver()
        
        # 同步配置
        self.auto_sync = self.config.get("auto_sync", True)
        self.sync_interval = self.config.get("sync_interval", 1.0)
        self.batch_size = self.config.get("batch_size", 10)
        
        # 状态管理
        self.is_running = False
        self.sync_queue = asyncio.Queue()
        self.pending_syncs = set()
        self.sync_stats = {
            "total_synced": 0,
            "conflicts_resolved": 0,
            "errors": 0,
            "last_sync": None
        }
        
        # 同步任务
        self.sync_task = None
        
        self.logger.info("同步管理器初始化完成")
    
    async def start(self):
        """启动同步管理器"""
        try:
            self.logger.info("启动同步管理器...")
            
            self.is_running = True
            
            # 启动同步处理任务
            if self.auto_sync:
                self.sync_task = asyncio.create_task(self._sync_processor())
            
            self.logger.info("✅ 同步管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动同步管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止同步管理器"""
        try:
            self.logger.info("停止同步管理器...")
            
            self.is_running = False
            
            # 停止同步任务
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            
            # 处理剩余的同步队列
            await self._flush_sync_queue()
            
            self.logger.info("✅ 同步管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止同步管理器失败: {e}")
    
    async def sync_file(self, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步文件
        
        Args:
            sync_data: 同步数据
            
        Returns:
            Dict: 同步结果
        """
        try:
            file_path = sync_data.get("file_path")
            content = sync_data.get("content", "")
            hash_value = sync_data.get("hash")
            timestamp = sync_data.get("timestamp", time.time())
            session_id = sync_data.get("session_id", "unknown")
            size = sync_data.get("size", len(content.encode('utf-8')))
            
            if not all([file_path, hash_value]):
                return {"success": False, "error": "同步数据不完整"}
            
            # 创建同步记录
            new_record = SyncRecord(
                file_path=file_path,
                hash_value=hash_value,
                timestamp=timestamp,
                session_id=session_id,
                size=size
            )
            
            # 检查是否存在冲突
            existing_record = self.database.get_record(file_path)
            
            if existing_record and existing_record.hash_value != hash_value:
                # 存在冲突，需要解决
                conflict_result = await self._handle_conflict(existing_record, new_record)
                if not conflict_result.get("success"):
                    return conflict_result
            
            # 保存同步记录
            if self.database.save_record(new_record):
                # 更新统计
                self.sync_stats["total_synced"] += 1
                self.sync_stats["last_sync"] = datetime.now().isoformat()
                
                result = {
                    "success": True,
                    "file_path": file_path,
                    "sync_id": new_record.sync_id,
                    "size": size,
                    "timestamp": timestamp
                }
                
                self.logger.info(f"文件同步成功: {file_path}")
                return result
            else:
                return {"success": False, "error": "保存同步记录失败"}
                
        except Exception as e:
            self.logger.error(f"文件同步失败: {e}")
            self.sync_stats["errors"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    async def queue_sync(self, sync_data: Dict[str, Any]):
        """将同步任务加入队列"""
        file_path = sync_data.get("file_path")
        if file_path and file_path not in self.pending_syncs:
            self.pending_syncs.add(file_path)
            await self.sync_queue.put(sync_data)
            self.logger.debug(f"同步任务入队: {file_path}")
    
    async def get_sync_status(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件同步状态
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 同步状态
        """
        try:
            record = self.database.get_record(file_path)
            
            if record:
                return {
                    "file_path": file_path,
                    "is_synced": True,
                    "last_sync": record.timestamp,
                    "hash": record.hash_value,
                    "session_id": record.session_id,
                    "size": record.size
                }
            else:
                return {
                    "file_path": file_path,
                    "is_synced": False,
                    "last_sync": None
                }
                
        except Exception as e:
            self.logger.error(f"获取同步状态失败: {e}")
            return {
                "file_path": file_path,
                "error": str(e)
            }
    
    async def get_sync_history(self, limit: int = 50) -> Dict[str, Any]:
        """
        获取同步历史
        
        Args:
            limit: 记录数量限制
            
        Returns:
            Dict: 同步历史
        """
        try:
            records = self.database.get_all_records(limit)
            
            history = []
            for record in records:
                history.append({
                    "sync_id": record.sync_id,
                    "file_path": record.file_path,
                    "hash": record.hash_value,
                    "timestamp": record.timestamp,
                    "session_id": record.session_id,
                    "size": record.size,
                    "formatted_time": datetime.fromtimestamp(record.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return {
                "success": True,
                "history": history,
                "total_count": len(history),
                "stats": self.sync_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取同步历史失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取同步管理器状态"""
        return {
            "is_running": self.is_running,
            "auto_sync": self.auto_sync,
            "sync_interval": self.sync_interval,
            "batch_size": self.batch_size,
            "queue_size": self.sync_queue.qsize(),
            "pending_syncs": len(self.pending_syncs),
            "stats": self.sync_stats
        }
    
    async def _sync_processor(self):
        """同步处理器 - 后台任务"""
        self.logger.info("启动同步处理器")
        
        while self.is_running:
            try:
                # 批量处理同步任务
                batch = []
                
                # 收集批量任务
                for _ in range(self.batch_size):
                    try:
                        sync_data = await asyncio.wait_for(
                            self.sync_queue.get(), 
                            timeout=self.sync_interval
                        )
                        batch.append(sync_data)
                    except asyncio.TimeoutError:
                        break
                
                # 处理批量任务
                if batch:
                    await self._process_sync_batch(batch)
                
            except Exception as e:
                self.logger.error(f"同步处理器错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_sync_batch(self, batch: List[Dict[str, Any]]):
        """处理同步批次"""
        self.logger.debug(f"处理同步批次: {len(batch)} 个任务")
        
        for sync_data in batch:
            try:
                file_path = sync_data.get("file_path")
                
                # 处理同步
                result = await self.sync_file(sync_data)
                
                # 从待处理集合中移除
                if file_path in self.pending_syncs:
                    self.pending_syncs.remove(file_path)
                
                if not result.get("success"):
                    self.logger.warning(f"同步失败: {file_path} - {result.get('error')}")
                
            except Exception as e:
                self.logger.error(f"处理同步任务失败: {e}")
    
    async def _handle_conflict(self, existing_record: SyncRecord, 
                             new_record: SyncRecord) -> Dict[str, Any]:
        """处理同步冲突"""
        try:
            self.logger.warning(f"检测到同步冲突: {existing_record.file_path}")
            
            # 使用冲突解决器
            resolution = await self.conflict_resolver.resolve_conflict(
                existing_record, 
                new_record,
                strategy=self.config.get("conflict_strategy", "latest_wins")
            )
            
            self.sync_stats["conflicts_resolved"] += 1
            
            if resolution.get("action") == "accept_remote":
                self.logger.info(f"冲突解决: 接受远程版本 - {existing_record.file_path}")
                return {"success": True, "resolution": resolution}
            elif resolution.get("action") == "keep_local":
                self.logger.info(f"冲突解决: 保持本地版本 - {existing_record.file_path}")
                return {"success": True, "resolution": resolution}
            else:
                self.logger.warning(f"冲突需要手动解决 - {existing_record.file_path}")
                return {
                    "success": False,
                    "error": "需要手动解决冲突",
                    "resolution": resolution
                }
                
        except Exception as e:
            self.logger.error(f"处理冲突失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _flush_sync_queue(self):
        """清空同步队列"""
        remaining_tasks = []
        
        while not self.sync_queue.empty():
            try:
                sync_data = self.sync_queue.get_nowait()
                remaining_tasks.append(sync_data)
            except asyncio.QueueEmpty:
                break
        
        if remaining_tasks:
            self.logger.info(f"处理剩余同步任务: {len(remaining_tasks)} 个")
            await self._process_sync_batch(remaining_tasks)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("SyncManager")
        
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

