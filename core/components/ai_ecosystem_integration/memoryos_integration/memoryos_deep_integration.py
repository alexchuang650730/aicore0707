"""
MemoryOS深度集成核心模块

提供与MemoryOS记忆系统的深度集成功能，实现智能记忆管理和上下文感知。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """记忆类型枚举"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryPriority(Enum):
    """记忆优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority
    context: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MemoryContext:
    """记忆上下文数据结构"""
    user_id: str
    session_id: str
    task_context: Dict[str, Any]
    environmental_context: Dict[str, Any]
    temporal_context: Dict[str, Any]
    emotional_context: Dict[str, Any]

class MemoryOSDeepIntegration:
    """MemoryOS深度集成核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化MemoryOS深度集成
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.memory_store: Dict[str, MemoryItem] = {}
        self.context_history: List[MemoryContext] = []
        self.learning_patterns: Dict[str, Any] = {}
        self.retrieval_cache: Dict[str, List[MemoryItem]] = {}
        
        # 配置参数
        self.max_short_term_memories = self.config.get('max_short_term_memories', 100)
        self.max_working_memories = self.config.get('max_working_memories', 20)
        self.memory_decay_factor = self.config.get('memory_decay_factor', 0.95)
        self.context_similarity_threshold = self.config.get('context_similarity_threshold', 0.7)
        
        logger.info("MemoryOS深度集成初始化完成")
    
    async def store_memory(self, 
                          content: str,
                          memory_type: MemoryType,
                          priority: MemoryPriority,
                          context: MemoryContext,
                          tags: List[str] = None,
                          metadata: Dict[str, Any] = None) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            priority: 优先级
            context: 上下文
            tags: 标签
            metadata: 元数据
            
        Returns:
            记忆ID
        """
        try:
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            memory_item = MemoryItem(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                priority=priority,
                context=asdict(context),
                timestamp=datetime.now(),
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # 存储记忆
            self.memory_store[memory_id] = memory_item
            
            # 更新上下文历史
            self.context_history.append(context)
            
            # 触发记忆整理
            await self._organize_memories()
            
            # 更新学习模式
            await self._update_learning_patterns(memory_item, context)
            
            logger.info(f"记忆存储成功: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"记忆存储失败: {e}")
            raise
    
    async def retrieve_memories(self,
                               query: str,
                               context: MemoryContext,
                               memory_types: List[MemoryType] = None,
                               limit: int = 10) -> List[MemoryItem]:
        """
        检索记忆
        
        Args:
            query: 查询内容
            context: 当前上下文
            memory_types: 记忆类型过滤
            limit: 返回数量限制
            
        Returns:
            匹配的记忆列表
        """
        try:
            # 检查缓存
            cache_key = f"{query}_{hash(str(asdict(context)))}"
            if cache_key in self.retrieval_cache:
                logger.info(f"从缓存返回记忆检索结果: {cache_key}")
                return self.retrieval_cache[cache_key][:limit]
            
            # 过滤记忆类型
            candidate_memories = []
            for memory in self.memory_store.values():
                if memory_types and memory.memory_type not in memory_types:
                    continue
                candidate_memories.append(memory)
            
            # 计算相关性分数
            scored_memories = []
            for memory in candidate_memories:
                score = await self._calculate_relevance_score(memory, query, context)
                if score > 0.1:  # 最低相关性阈值
                    scored_memories.append((memory, score))
            
            # 排序并返回
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            result_memories = [memory for memory, score in scored_memories[:limit]]
            
            # 更新访问统计
            for memory in result_memories:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
            
            # 缓存结果
            self.retrieval_cache[cache_key] = result_memories
            
            logger.info(f"记忆检索完成，返回 {len(result_memories)} 条记忆")
            return result_memories
            
        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            return []
    
    async def update_memory_context(self, memory_id: str, new_context: Dict[str, Any]) -> bool:
        """
        更新记忆上下文
        
        Args:
            memory_id: 记忆ID
            new_context: 新的上下文信息
            
        Returns:
            更新是否成功
        """
        try:
            if memory_id not in self.memory_store:
                logger.warning(f"记忆不存在: {memory_id}")
                return False
            
            memory = self.memory_store[memory_id]
            memory.context.update(new_context)
            memory.metadata['last_updated'] = datetime.now().isoformat()
            
            # 清除相关缓存
            self._clear_retrieval_cache()
            
            logger.info(f"记忆上下文更新成功: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"记忆上下文更新失败: {e}")
            return False
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        try:
            total_memories = len(self.memory_store)
            memory_type_counts = {}
            priority_counts = {}
            
            for memory in self.memory_store.values():
                # 统计记忆类型
                memory_type = memory.memory_type.value
                memory_type_counts[memory_type] = memory_type_counts.get(memory_type, 0) + 1
                
                # 统计优先级
                priority = memory.priority.value
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # 计算平均访问次数
            total_access = sum(memory.access_count for memory in self.memory_store.values())
            avg_access = total_access / total_memories if total_memories > 0 else 0
            
            statistics = {
                'total_memories': total_memories,
                'memory_type_distribution': memory_type_counts,
                'priority_distribution': priority_counts,
                'average_access_count': round(avg_access, 2),
                'context_history_length': len(self.context_history),
                'learning_patterns_count': len(self.learning_patterns),
                'cache_size': len(self.retrieval_cache)
            }
            
            logger.info("记忆统计信息获取成功")
            return statistics
            
        except Exception as e:
            logger.error(f"获取记忆统计信息失败: {e}")
            return {}
    
    async def _organize_memories(self):
        """整理记忆，清理过期和低优先级记忆"""
        try:
            current_time = datetime.now()
            
            # 清理过期的短期记忆
            short_term_memories = [m for m in self.memory_store.values() 
                                 if m.memory_type == MemoryType.SHORT_TERM]
            
            if len(short_term_memories) > self.max_short_term_memories:
                # 按时间和访问频率排序，删除最旧的
                short_term_memories.sort(key=lambda m: (m.timestamp, m.access_count))
                to_remove = short_term_memories[:len(short_term_memories) - self.max_short_term_memories]
                
                for memory in to_remove:
                    del self.memory_store[memory.id]
                    logger.debug(f"清理过期短期记忆: {memory.id}")
            
            # 清理工作记忆
            working_memories = [m for m in self.memory_store.values() 
                              if m.memory_type == MemoryType.WORKING]
            
            if len(working_memories) > self.max_working_memories:
                working_memories.sort(key=lambda m: (m.timestamp, m.access_count))
                to_remove = working_memories[:len(working_memories) - self.max_working_memories]
                
                for memory in to_remove:
                    del self.memory_store[memory.id]
                    logger.debug(f"清理过期工作记忆: {memory.id}")
            
            # 清理检索缓存
            if len(self.retrieval_cache) > 1000:
                self._clear_retrieval_cache()
            
        except Exception as e:
            logger.error(f"记忆整理失败: {e}")
    
    async def _calculate_relevance_score(self, 
                                       memory: MemoryItem, 
                                       query: str, 
                                       context: MemoryContext) -> float:
        """
        计算记忆相关性分数
        
        Args:
            memory: 记忆项
            query: 查询内容
            context: 当前上下文
            
        Returns:
            相关性分数 (0-1)
        """
        try:
            score = 0.0
            
            # 内容相似性 (40%)
            content_similarity = self._calculate_text_similarity(memory.content, query)
            score += content_similarity * 0.4
            
            # 上下文相似性 (30%)
            context_similarity = self._calculate_context_similarity(memory.context, asdict(context))
            score += context_similarity * 0.3
            
            # 时间衰减 (15%)
            time_factor = self._calculate_time_decay(memory.timestamp)
            score += time_factor * 0.15
            
            # 访问频率 (10%)
            access_factor = min(memory.access_count / 10.0, 1.0)
            score += access_factor * 0.1
            
            # 优先级加权 (5%)
            priority_weights = {
                MemoryPriority.CRITICAL: 1.0,
                MemoryPriority.HIGH: 0.8,
                MemoryPriority.MEDIUM: 0.6,
                MemoryPriority.LOW: 0.4
            }
            priority_factor = priority_weights.get(memory.priority, 0.5)
            score += priority_factor * 0.05
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"计算相关性分数失败: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似性"""
        try:
            # 简单的词汇重叠相似性
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """计算上下文相似性"""
        try:
            # 比较关键上下文字段
            key_fields = ['user_id', 'task_context', 'environmental_context']
            similarities = []
            
            for field in key_fields:
                if field in context1 and field in context2:
                    if context1[field] == context2[field]:
                        similarities.append(1.0)
                    else:
                        similarities.append(0.0)
                else:
                    similarities.append(0.0)
            
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """计算时间衰减因子"""
        try:
            time_diff = datetime.now() - timestamp
            hours_passed = time_diff.total_seconds() / 3600
            
            # 指数衰减
            decay_factor = self.memory_decay_factor ** hours_passed
            return max(decay_factor, 0.1)  # 最小保持10%的权重
            
        except Exception:
            return 0.1
    
    async def _update_learning_patterns(self, memory: MemoryItem, context: MemoryContext):
        """更新学习模式"""
        try:
            user_id = context.user_id
            
            if user_id not in self.learning_patterns:
                self.learning_patterns[user_id] = {
                    'preferred_memory_types': {},
                    'common_contexts': {},
                    'access_patterns': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            patterns = self.learning_patterns[user_id]
            
            # 更新偏好的记忆类型
            memory_type = memory.memory_type.value
            patterns['preferred_memory_types'][memory_type] = \
                patterns['preferred_memory_types'].get(memory_type, 0) + 1
            
            # 更新常见上下文
            task_type = context.task_context.get('type', 'unknown')
            patterns['common_contexts'][task_type] = \
                patterns['common_contexts'].get(task_type, 0) + 1
            
            patterns['last_updated'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"更新学习模式失败: {e}")
    
    def _clear_retrieval_cache(self):
        """清除检索缓存"""
        self.retrieval_cache.clear()
        logger.debug("检索缓存已清除")
    
    async def export_memories(self, file_path: str) -> bool:
        """
        导出记忆数据
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            导出是否成功
        """
        try:
            export_data = {
                'memories': {},
                'context_history': [],
                'learning_patterns': self.learning_patterns,
                'export_timestamp': datetime.now().isoformat()
            }
            
            # 序列化记忆数据
            for memory_id, memory in self.memory_store.items():
                export_data['memories'][memory_id] = {
                    'id': memory.id,
                    'content': memory.content,
                    'memory_type': memory.memory_type.value,
                    'priority': memory.priority.value,
                    'context': memory.context,
                    'timestamp': memory.timestamp.isoformat(),
                    'access_count': memory.access_count,
                    'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
                    'tags': memory.tags,
                    'metadata': memory.metadata
                }
            
            # 序列化上下文历史
            for context in self.context_history:
                export_data['context_history'].append(asdict(context))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"记忆数据导出成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"记忆数据导出失败: {e}")
            return False
    
    async def import_memories(self, file_path: str) -> bool:
        """
        导入记忆数据
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            导入是否成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入记忆数据
            for memory_id, memory_data in import_data.get('memories', {}).items():
                memory = MemoryItem(
                    id=memory_data['id'],
                    content=memory_data['content'],
                    memory_type=MemoryType(memory_data['memory_type']),
                    priority=MemoryPriority(memory_data['priority']),
                    context=memory_data['context'],
                    timestamp=datetime.fromisoformat(memory_data['timestamp']),
                    access_count=memory_data['access_count'],
                    last_accessed=datetime.fromisoformat(memory_data['last_accessed']) 
                                 if memory_data['last_accessed'] else None,
                    tags=memory_data['tags'],
                    metadata=memory_data['metadata']
                )
                self.memory_store[memory_id] = memory
            
            # 导入学习模式
            self.learning_patterns.update(import_data.get('learning_patterns', {}))
            
            # 清除缓存
            self._clear_retrieval_cache()
            
            logger.info(f"记忆数据导入成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"记忆数据导入失败: {e}")
            return False

