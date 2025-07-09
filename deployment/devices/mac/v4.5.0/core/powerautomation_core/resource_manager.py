"""
ResourceManager - 资源管理器
管理系统资源分配、监控和优化
"""

import asyncio
import psutil
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"

@dataclass
class ResourceQuota:
    """资源配额"""
    resource_type: ResourceType
    total: float
    allocated: float = 0.0
    reserved: float = 0.0
    
    @property
    def available(self) -> float:
        return self.total - self.allocated - self.reserved
    
    @property
    def usage_percentage(self) -> float:
        return (self.allocated / self.total) * 100 if self.total > 0 else 0

@dataclass
class ResourceAllocation:
    """资源分配"""
    id: str
    resource_type: ResourceType
    amount: float
    allocated_to: str  # 分配给谁
    allocated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ResourceManager:
    """资源管理器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 资源配额
        self.quotas: Dict[ResourceType, ResourceQuota] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        
        # 监控数据
        self.usage_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # 监控控制
        self.monitoring_interval = config.resource_check_interval
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 初始化资源配额
        self._initialize_quotas()
        
        self.logger.info("资源管理器初始化完成")
    
    def _initialize_quotas(self):
        """初始化资源配额"""
        try:
            # CPU配额
            cpu_count = psutil.cpu_count()
            self.quotas[ResourceType.CPU] = ResourceQuota(
                resource_type=ResourceType.CPU,
                total=cpu_count * 100,  # 以百分比计算
                reserved=cpu_count * 10  # 保留10%
            )
            
            # 内存配额
            memory = psutil.virtual_memory()
            self.quotas[ResourceType.MEMORY] = ResourceQuota(
                resource_type=ResourceType.MEMORY,
                total=memory.total / (1024**3),  # GB
                reserved=memory.total / (1024**3) * 0.1  # 保留10%
            )
            
            # 磁盘配额
            disk = psutil.disk_usage('/')
            self.quotas[ResourceType.DISK] = ResourceQuota(
                resource_type=ResourceType.DISK,
                total=disk.total / (1024**3),  # GB
                reserved=disk.total / (1024**3) * 0.05  # 保留5%
            )
            
            # 网络配额（带宽，单位Mbps）
            self.quotas[ResourceType.NETWORK] = ResourceQuota(
                resource_type=ResourceType.NETWORK,
                total=1000,  # 假设1Gbps
                reserved=100  # 保留100Mbps
            )
            
            self.logger.debug("资源配额初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化资源配额失败: {e}")
            raise
    
    async def initialize(self):
        """初始化资源管理器"""
        try:
            # 加载已保存的分配
            await self._load_allocations()
            
            # 清理过期分配
            await self._cleanup_expired_allocations()
            
            self.logger.info("资源管理器初始化成功")
            
        except Exception as e:
            self.logger.error(f"资源管理器初始化失败: {e}")
            raise
    
    async def start(self):
        """启动资源管理器"""
        try:
            # 启动监控任务
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("资源管理器启动")
            
        except Exception as e:
            self.logger.error(f"启动资源管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止资源管理器"""
        try:
            # 停止监控任务
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # 保存分配状态
            await self._save_allocations()
            
            self.logger.info("资源管理器停止")
            
        except Exception as e:
            self.logger.error(f"停止资源管理器失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查系统资源使用情况
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            # 检查是否超过阈值
            if cpu_usage > 95 or memory_usage > 95 or disk_usage > 95:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    # 资源分配
    async def allocate_resource(self, resource_type: str, amount: float, allocated_to: str = "unknown", duration: int = None) -> str:
        """分配资源"""
        try:
            res_type = ResourceType(resource_type)
            
            # 检查资源是否可用
            if res_type not in self.quotas:
                raise ValueError(f"不支持的资源类型: {resource_type}")
            
            quota = self.quotas[res_type]
            if quota.available < amount:
                raise RuntimeError(f"资源不足: 需要 {amount}, 可用 {quota.available}")
            
            # 创建分配
            allocation_id = f"{resource_type}_{len(self.allocations)}_{int(datetime.now().timestamp())}"
            expires_at = None
            if duration:
                expires_at = datetime.now() + timedelta(seconds=duration)
            
            allocation = ResourceAllocation(
                id=allocation_id,
                resource_type=res_type,
                amount=amount,
                allocated_to=allocated_to,
                allocated_at=datetime.now(),
                expires_at=expires_at
            )
            
            # 更新配额
            quota.allocated += amount
            self.allocations[allocation_id] = allocation
            
            # 保存分配
            await self._save_allocation(allocation)
            
            self.logger.info(f"资源分配成功: {allocation_id}, {resource_type}={amount}")
            return allocation_id
            
        except Exception as e:
            self.logger.error(f"分配资源失败: {e}")
            raise
    
    async def release_resource(self, allocation_id: str) -> bool:
        """释放资源"""
        try:
            if allocation_id not in self.allocations:
                return False
            
            allocation = self.allocations[allocation_id]
            quota = self.quotas[allocation.resource_type]
            
            # 释放配额
            quota.allocated -= allocation.amount
            
            # 移除分配
            del self.allocations[allocation_id]
            
            # 删除保存的分配
            await self._delete_allocation(allocation_id)
            
            self.logger.info(f"资源释放成功: {allocation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"释放资源失败: {e}")
            return False
    
    async def get_resource_usage(self, resource_type: str = None) -> Dict[str, Any]:
        """获取资源使用情况"""
        try:
            if resource_type:
                res_type = ResourceType(resource_type)
                if res_type in self.quotas:
                    quota = self.quotas[res_type]
                    return {
                        "type": resource_type,
                        "total": quota.total,
                        "allocated": quota.allocated,
                        "reserved": quota.reserved,
                        "available": quota.available,
                        "usage_percentage": quota.usage_percentage
                    }
                else:
                    return {}
            else:
                # 返回所有资源使用情况
                usage = {}
                for res_type, quota in self.quotas.items():
                    usage[res_type.value] = {
                        "total": quota.total,
                        "allocated": quota.allocated,
                        "reserved": quota.reserved,
                        "available": quota.available,
                        "usage_percentage": quota.usage_percentage
                    }
                return usage
                
        except Exception as e:
            self.logger.error(f"获取资源使用情况失败: {e}")
            return {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存指标
            memory = psutil.virtual_memory()
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            
            # 网络指标
            network = psutil.net_io_counters()
            
            # 进程指标
            process_count = len(psutil.pids())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": process_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取系统指标失败: {e}")
            return {}
    
    # 监控循环
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                # 收集系统指标
                metrics = await self.get_system_metrics()
                if metrics:
                    self.usage_history.append(metrics)
                    
                    # 限制历史记录大小
                    if len(self.usage_history) > self.max_history_size:
                        self.usage_history = self.usage_history[-self.max_history_size:]
                
                # 清理过期分配
                await self._cleanup_expired_allocations()
                
                # 检查资源警告
                await self._check_resource_warnings()
                
                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _cleanup_expired_allocations(self):
        """清理过期分配"""
        current_time = datetime.now()
        expired_allocations = []
        
        for allocation_id, allocation in self.allocations.items():
            if allocation.expires_at and allocation.expires_at <= current_time:
                expired_allocations.append(allocation_id)
        
        for allocation_id in expired_allocations:
            await self.release_resource(allocation_id)
            self.logger.debug(f"清理过期分配: {allocation_id}")
    
    async def _check_resource_warnings(self):
        """检查资源警告"""
        for res_type, quota in self.quotas.items():
            if quota.usage_percentage > 90:
                self.logger.warning(f"资源使用率过高: {res_type.value} = {quota.usage_percentage:.1f}%")
            elif quota.usage_percentage > 80:
                self.logger.info(f"资源使用率较高: {res_type.value} = {quota.usage_percentage:.1f}%")
    
    # 状态查询
    async def get_status(self) -> Dict[str, Any]:
        """获取资源管理器状态"""
        try:
            system_metrics = await self.get_system_metrics()
            resource_usage = await self.get_resource_usage()
            
            return {
                "quotas": {res_type.value: asdict(quota) for res_type, quota in self.quotas.items()},
                "allocations": {alloc_id: asdict(alloc) for alloc_id, alloc in self.allocations.items()},
                "system_metrics": system_metrics,
                "resource_usage": resource_usage,
                "total_allocations": len(self.allocations),
                "history_size": len(self.usage_history)
            }
            
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            return {}
    
    async def get_usage_stats(self) -> Dict[str, float]:
        """获取使用统计"""
        try:
            stats = {}
            
            # 系统指标
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            stats.update({
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent
            })
            
            # 配额使用率
            for res_type, quota in self.quotas.items():
                stats[f"{res_type.value}_quota_usage"] = quota.usage_percentage
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取使用统计失败: {e}")
            return {}
    
    def get_usage_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取使用历史"""
        if limit > 0:
            return self.usage_history[-limit:]
        else:
            return self.usage_history.copy()
    
    # 资源优化
    async def optimize_resources(self) -> Dict[str, Any]:
        """优化资源分配"""
        try:
            optimization_results = {
                "actions_taken": [],
                "recommendations": []
            }
            
            # 检查长期未使用的分配
            current_time = datetime.now()
            for allocation_id, allocation in self.allocations.items():
                age = (current_time - allocation.allocated_at).total_seconds()
                if age > 3600:  # 超过1小时
                    optimization_results["recommendations"].append(
                        f"考虑释放长期分配: {allocation_id} (已分配 {age/3600:.1f} 小时)"
                    )
            
            # 检查资源碎片
            for res_type, quota in self.quotas.items():
                if quota.usage_percentage < 50 and quota.allocated > 0:
                    optimization_results["recommendations"].append(
                        f"资源利用率较低: {res_type.value} = {quota.usage_percentage:.1f}%"
                    )
            
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"资源优化失败: {e}")
            return {"error": str(e)}
    
    # 持久化
    async def _load_allocations(self):
        """加载分配"""
        try:
            allocations_dir = self.data_dir / "allocations"
            if allocations_dir.exists():
                for allocation_file in allocations_dir.glob("*.json"):
                    try:
                        with open(allocation_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            allocation = ResourceAllocation(**data)
                            self.allocations[allocation.id] = allocation
                    except Exception as e:
                        self.logger.error(f"加载分配失败 {allocation_file}: {e}")
        except Exception as e:
            self.logger.error(f"加载分配失败: {e}")
    
    async def _save_allocation(self, allocation: ResourceAllocation):
        """保存分配"""
        try:
            allocations_dir = self.data_dir / "allocations"
            allocations_dir.mkdir(parents=True, exist_ok=True)
            
            allocation_file = allocations_dir / f"{allocation.id}.json"
            with open(allocation_file, 'w', encoding='utf-8') as f:
                json.dump(allocation.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存分配失败 {allocation.id}: {e}")
    
    async def _save_allocations(self):
        """保存所有分配"""
        try:
            for allocation in self.allocations.values():
                await self._save_allocation(allocation)
        except Exception as e:
            self.logger.error(f"批量保存分配失败: {e}")
    
    async def _delete_allocation(self, allocation_id: str):
        """删除分配"""
        try:
            allocation_file = self.data_dir / f"allocations/{allocation_id}.json"
            if allocation_file.exists():
                allocation_file.unlink()
        except Exception as e:
            self.logger.error(f"删除分配失败 {allocation_id}: {e}")

