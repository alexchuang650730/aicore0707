"""
PowerAutomation 性能监控器

实时监控PowerAutomation系统的性能指标：
- 系统资源使用监控
- 任务执行性能分析
- 智能体和MCP性能跟踪
- 异常检测和告警
- 性能优化建议

与现有监控组件集成，提供统一的性能监控视图。
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json

# 导入现有监控组件
from ..components.local_adapter_mcp.monitoring.real_time_monitor import RealTimeMonitor
from ..components.local_adapter_mcp.monitoring.performance_analyzer import PerformanceAnalyzer
from ..components.local_adapter_mcp.monitoring.metrics_collector import MetricsCollector
from ..components.local_adapter_mcp.monitoring.alert_system import AlertSystem


class MetricType(Enum):
    """指标类型枚举"""
    SYSTEM = "system"
    TASK = "task"
    AGENT = "agent"
    MCP = "mcp"
    NETWORK = "network"
    CUSTOM = "custom"


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PerformanceStatus(Enum):
    """性能状态枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    NORMAL = "normal"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]
    process_count: int


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    status: str
    cpu_usage: float
    memory_usage: float
    success: bool
    error_info: Optional[str]


@dataclass
class AgentMetrics:
    """智能体指标"""
    agent_name: str
    timestamp: datetime
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_response_time: float
    success_rate: float
    cpu_usage: float
    memory_usage: float
    last_activity: datetime


@dataclass
class MCPMetrics:
    """MCP指标"""
    mcp_name: str
    timestamp: datetime
    active_connections: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    throughput: float
    error_rate: float
    last_activity: datetime


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    alert_type: MetricType
    level: AlertLevel
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class PerformanceMonitor:
    """
    性能监控器
    
    实时监控PowerAutomation系统的各项性能指标，
    提供异常检测、告警和性能优化建议。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化性能监控器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 监控配置
        self.monitoring_interval = self.config.get("monitoring_interval", 30)  # 秒
        self.metrics_retention_days = self.config.get("metrics_retention_days", 7)
        self.alert_thresholds = self._init_alert_thresholds()
        
        # 数据存储
        self.system_metrics: deque = deque(maxlen=2880)  # 24小时数据（30秒间隔）
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.agent_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=288))  # 2.4小时
        self.mcp_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=288))
        self.alerts: Dict[str, PerformanceAlert] = {}
        
        # 监控状态
        self.is_monitoring = False
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # 集成现有监控组件
        self.real_time_monitor = RealTimeMonitor()
        self.performance_analyzer = PerformanceAnalyzer()
        self.metrics_collector = MetricsCollector()
        self.alert_system = AlertSystem()
        
        # 性能基线
        self.performance_baseline = {
            "cpu_threshold": 80.0,
            "memory_threshold": 85.0,
            "disk_threshold": 90.0,
            "response_time_threshold": 5.0,
            "error_rate_threshold": 0.05
        }
        
        # 统计信息
        self.stats = {
            "monitoring_start_time": None,
            "total_metrics_collected": 0,
            "total_alerts_generated": 0,
            "active_alerts": 0,
            "system_status": PerformanceStatus.NORMAL.value,
            "last_health_check": None
        }
        
        self.logger.info("性能监控器初始化完成")
    
    def _init_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """初始化告警阈值"""
        return {
            "system": {
                "cpu_warning": 70.0,
                "cpu_critical": 90.0,
                "memory_warning": 75.0,
                "memory_critical": 90.0,
                "disk_warning": 80.0,
                "disk_critical": 95.0
            },
            "task": {
                "duration_warning": 300.0,  # 5分钟
                "duration_critical": 1800.0,  # 30分钟
                "error_rate_warning": 0.1,
                "error_rate_critical": 0.3
            },
            "agent": {
                "response_time_warning": 3.0,
                "response_time_critical": 10.0,
                "success_rate_warning": 0.8,
                "success_rate_critical": 0.6
            },
            "mcp": {
                "response_time_warning": 2.0,
                "response_time_critical": 8.0,
                "error_rate_warning": 0.05,
                "error_rate_critical": 0.2
            }
        }
    
    async def start(self):
        """启动性能监控"""
        if self.is_monitoring:
            self.logger.warning("性能监控已在运行中")
            return
        
        self.is_monitoring = True
        self.stats["monitoring_start_time"] = datetime.now().isoformat()
        
        self.logger.info("启动性能监控器")
        
        # 启动现有监控组件
        await self.real_time_monitor.start()
        await self.metrics_collector.start()
        await self.alert_system.start()
        
        # 启动监控任务
        self.monitoring_tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._task_monitoring_loop()),
            asyncio.create_task(self._agent_monitoring_loop()),
            asyncio.create_task(self._mcp_monitoring_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        self.logger.info("性能监控器启动完成")
    
    async def stop(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.logger.info("停止性能监控器")
        
        # 停止监控任务
        for task in self.monitoring_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        # 停止现有监控组件
        await self.alert_system.stop()
        await self.metrics_collector.stop()
        await self.real_time_monitor.stop()
        
        self.logger.info("性能监控器已停止")
    
    async def _system_monitoring_loop(self):
        """系统监控循环"""
        self.logger.info("启动系统监控循环")
        
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()
                self.system_metrics.append(metrics)
                
                # 检查系统告警
                await self._check_system_alerts(metrics)
                
                # 更新统计信息
                self.stats["total_metrics_collected"] += 1
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"系统监控循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # 网络使用情况
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024**2)
        network_recv_mb = network.bytes_recv / (1024**2)
        
        # 系统负载
        try:
            load_average = list(psutil.getloadavg())
        except AttributeError:
            # Windows系统没有getloadavg
            load_average = [0.0, 0.0, 0.0]
        
        # 进程数量
        process_count = len(psutil.pids())
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            load_average=load_average,
            process_count=process_count
        )
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """检查系统告警"""
        thresholds = self.alert_thresholds["system"]
        
        # CPU告警
        if metrics.cpu_percent >= thresholds["cpu_critical"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.CRITICAL,
                "CPU使用率过高", f"CPU使用率达到 {metrics.cpu_percent:.1f}%",
                "cpu_percent", metrics.cpu_percent, thresholds["cpu_critical"]
            )
        elif metrics.cpu_percent >= thresholds["cpu_warning"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.WARNING,
                "CPU使用率较高", f"CPU使用率达到 {metrics.cpu_percent:.1f}%",
                "cpu_percent", metrics.cpu_percent, thresholds["cpu_warning"]
            )
        
        # 内存告警
        if metrics.memory_percent >= thresholds["memory_critical"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.CRITICAL,
                "内存使用率过高", f"内存使用率达到 {metrics.memory_percent:.1f}%",
                "memory_percent", metrics.memory_percent, thresholds["memory_critical"]
            )
        elif metrics.memory_percent >= thresholds["memory_warning"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.WARNING,
                "内存使用率较高", f"内存使用率达到 {metrics.memory_percent:.1f}%",
                "memory_percent", metrics.memory_percent, thresholds["memory_warning"]
            )
        
        # 磁盘告警
        if metrics.disk_percent >= thresholds["disk_critical"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.CRITICAL,
                "磁盘使用率过高", f"磁盘使用率达到 {metrics.disk_percent:.1f}%",
                "disk_percent", metrics.disk_percent, thresholds["disk_critical"]
            )
        elif metrics.disk_percent >= thresholds["disk_warning"]:
            await self._create_alert(
                MetricType.SYSTEM, AlertLevel.WARNING,
                "磁盘使用率较高", f"磁盘使用率达到 {metrics.disk_percent:.1f}%",
                "disk_percent", metrics.disk_percent, thresholds["disk_warning"]
            )
    
    async def _task_monitoring_loop(self):
        """任务监控循环"""
        self.logger.info("启动任务监控循环")
        
        while self.is_monitoring:
            try:
                # 检查任务超时
                await self._check_task_timeouts()
                
                # 分析任务性能
                await self._analyze_task_performance()
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.logger.error(f"任务监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _check_task_timeouts(self):
        """检查任务超时"""
        current_time = datetime.now()
        thresholds = self.alert_thresholds["task"]
        
        for task_id, metrics in self.task_metrics.items():
            if metrics.end_time is None:  # 任务仍在运行
                duration = (current_time - metrics.start_time).total_seconds()
                
                if duration >= thresholds["duration_critical"]:
                    await self._create_alert(
                        MetricType.TASK, AlertLevel.CRITICAL,
                        "任务执行超时", f"任务 {task_id} 已运行 {duration/60:.1f} 分钟",
                        "duration", duration, thresholds["duration_critical"]
                    )
                elif duration >= thresholds["duration_warning"]:
                    await self._create_alert(
                        MetricType.TASK, AlertLevel.WARNING,
                        "任务执行时间较长", f"任务 {task_id} 已运行 {duration/60:.1f} 分钟",
                        "duration", duration, thresholds["duration_warning"]
                    )
    
    async def _analyze_task_performance(self):
        """分析任务性能"""
        # 计算任务成功率
        total_tasks = len(self.task_metrics)
        if total_tasks > 0:
            successful_tasks = sum(1 for m in self.task_metrics.values() if m.success)
            error_rate = 1 - (successful_tasks / total_tasks)
            
            thresholds = self.alert_thresholds["task"]
            
            if error_rate >= thresholds["error_rate_critical"]:
                await self._create_alert(
                    MetricType.TASK, AlertLevel.CRITICAL,
                    "任务错误率过高", f"任务错误率达到 {error_rate*100:.1f}%",
                    "error_rate", error_rate, thresholds["error_rate_critical"]
                )
            elif error_rate >= thresholds["error_rate_warning"]:
                await self._create_alert(
                    MetricType.TASK, AlertLevel.WARNING,
                    "任务错误率较高", f"任务错误率达到 {error_rate*100:.1f}%",
                    "error_rate", error_rate, thresholds["error_rate_warning"]
                )
    
    async def _agent_monitoring_loop(self):
        """智能体监控循环"""
        self.logger.info("启动智能体监控循环")
        
        while self.is_monitoring:
            try:
                # 收集智能体指标
                await self._collect_agent_metrics()
                
                # 检查智能体告警
                await self._check_agent_alerts()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"智能体监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _collect_agent_metrics(self):
        """收集智能体指标"""
        # 这里应该从智能体协调器获取实际指标
        # 目前使用模拟数据
        agent_names = ["architect_agent", "developer_agent", "deploy_agent", 
                      "test_agent", "monitor_agent", "security_agent"]
        
        for agent_name in agent_names:
            # 模拟智能体指标
            metrics = AgentMetrics(
                agent_name=agent_name,
                timestamp=datetime.now(),
                active_tasks=0,  # 实际应从智能体获取
                completed_tasks=0,
                failed_tasks=0,
                average_response_time=1.5,
                success_rate=0.95,
                cpu_usage=5.0,
                memory_usage=50.0,
                last_activity=datetime.now()
            )
            
            self.agent_metrics[agent_name].append(metrics)
    
    async def _check_agent_alerts(self):
        """检查智能体告警"""
        thresholds = self.alert_thresholds["agent"]
        
        for agent_name, metrics_list in self.agent_metrics.items():
            if not metrics_list:
                continue
            
            latest_metrics = metrics_list[-1]
            
            # 响应时间告警
            if latest_metrics.average_response_time >= thresholds["response_time_critical"]:
                await self._create_alert(
                    MetricType.AGENT, AlertLevel.CRITICAL,
                    f"智能体 {agent_name} 响应时间过长",
                    f"平均响应时间 {latest_metrics.average_response_time:.1f} 秒",
                    "response_time", latest_metrics.average_response_time,
                    thresholds["response_time_critical"]
                )
            elif latest_metrics.average_response_time >= thresholds["response_time_warning"]:
                await self._create_alert(
                    MetricType.AGENT, AlertLevel.WARNING,
                    f"智能体 {agent_name} 响应时间较长",
                    f"平均响应时间 {latest_metrics.average_response_time:.1f} 秒",
                    "response_time", latest_metrics.average_response_time,
                    thresholds["response_time_warning"]
                )
            
            # 成功率告警
            if latest_metrics.success_rate <= thresholds["success_rate_critical"]:
                await self._create_alert(
                    MetricType.AGENT, AlertLevel.CRITICAL,
                    f"智能体 {agent_name} 成功率过低",
                    f"成功率 {latest_metrics.success_rate*100:.1f}%",
                    "success_rate", latest_metrics.success_rate,
                    thresholds["success_rate_critical"]
                )
            elif latest_metrics.success_rate <= thresholds["success_rate_warning"]:
                await self._create_alert(
                    MetricType.AGENT, AlertLevel.WARNING,
                    f"智能体 {agent_name} 成功率较低",
                    f"成功率 {latest_metrics.success_rate*100:.1f}%",
                    "success_rate", latest_metrics.success_rate,
                    thresholds["success_rate_warning"]
                )
    
    async def _mcp_monitoring_loop(self):
        """MCP监控循环"""
        self.logger.info("启动MCP监控循环")
        
        while self.is_monitoring:
            try:
                # 收集MCP指标
                await self._collect_mcp_metrics()
                
                # 检查MCP告警
                await self._check_mcp_alerts()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"MCP监控循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _collect_mcp_metrics(self):
        """收集MCP指标"""
        # 这里应该从MCP协调器获取实际指标
        # 目前使用模拟数据
        mcp_names = ["local_adapter_mcp", "trae_agent_mcp", "stagewise_mcp", 
                    "memoryos_mcp", ]
        
        for mcp_name in mcp_names:
            # 模拟MCP指标
            metrics = MCPMetrics(
                mcp_name=mcp_name,
                timestamp=datetime.now(),
                active_connections=2,
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                average_response_time=0.8,
                throughput=10.0,
                error_rate=0.05,
                last_activity=datetime.now()
            )
            
            self.mcp_metrics[mcp_name].append(metrics)
    
    async def _check_mcp_alerts(self):
        """检查MCP告警"""
        thresholds = self.alert_thresholds["mcp"]
        
        for mcp_name, metrics_list in self.mcp_metrics.items():
            if not metrics_list:
                continue
            
            latest_metrics = metrics_list[-1]
            
            # 响应时间告警
            if latest_metrics.average_response_time >= thresholds["response_time_critical"]:
                await self._create_alert(
                    MetricType.MCP, AlertLevel.CRITICAL,
                    f"MCP {mcp_name} 响应时间过长",
                    f"平均响应时间 {latest_metrics.average_response_time:.1f} 秒",
                    "response_time", latest_metrics.average_response_time,
                    thresholds["response_time_critical"]
                )
            elif latest_metrics.average_response_time >= thresholds["response_time_warning"]:
                await self._create_alert(
                    MetricType.MCP, AlertLevel.WARNING,
                    f"MCP {mcp_name} 响应时间较长",
                    f"平均响应时间 {latest_metrics.average_response_time:.1f} 秒",
                    "response_time", latest_metrics.average_response_time,
                    thresholds["response_time_warning"]
                )
            
            # 错误率告警
            if latest_metrics.error_rate >= thresholds["error_rate_critical"]:
                await self._create_alert(
                    MetricType.MCP, AlertLevel.CRITICAL,
                    f"MCP {mcp_name} 错误率过高",
                    f"错误率 {latest_metrics.error_rate*100:.1f}%",
                    "error_rate", latest_metrics.error_rate,
                    thresholds["error_rate_critical"]
                )
            elif latest_metrics.error_rate >= thresholds["error_rate_warning"]:
                await self._create_alert(
                    MetricType.MCP, AlertLevel.WARNING,
                    f"MCP {mcp_name} 错误率较高",
                    f"错误率 {latest_metrics.error_rate*100:.1f}%",
                    "error_rate", latest_metrics.error_rate,
                    thresholds["error_rate_warning"]
                )
    
    async def _create_alert(self, alert_type: MetricType, level: AlertLevel,
                          title: str, description: str, metric_name: str,
                          current_value: float, threshold_value: float):
        """创建告警"""
        alert_id = f"alert_{alert_type.value}_{metric_name}_{int(time.time())}"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            level=level,
            title=title,
            description=description,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=datetime.now()
        )
        
        self.alerts[alert_id] = alert
        self.stats["total_alerts_generated"] += 1
        self.stats["active_alerts"] = len([a for a in self.alerts.values() if not a.resolved])
        
        # 发送到告警系统
        await self.alert_system.send_alert({
            "id": alert_id,
            "type": alert_type.value,
            "level": level.value,
            "title": title,
            "description": description,
            "timestamp": alert.timestamp.isoformat()
        })
        
        self.logger.warning(f"生成告警: {title} - {description}")
    
    async def _alert_processing_loop(self):
        """告警处理循环"""
        self.logger.info("启动告警处理循环")
        
        while self.is_monitoring:
            try:
                # 检查告警自动恢复
                await self._check_alert_recovery()
                
                # 更新系统状态
                await self._update_system_status()
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.logger.error(f"告警处理循环错误: {e}")
                await asyncio.sleep(10)
    
    async def _check_alert_recovery(self):
        """检查告警恢复"""
        current_time = datetime.now()
        
        for alert in self.alerts.values():
            if alert.resolved:
                continue
            
            # 检查是否可以自动恢复
            if await self._is_alert_recovered(alert):
                alert.resolved = True
                alert.resolution_time = current_time
                
                self.logger.info(f"告警自动恢复: {alert.title}")
    
    async def _is_alert_recovered(self, alert: PerformanceAlert) -> bool:
        """检查告警是否已恢复"""
        if alert.alert_type == MetricType.SYSTEM:
            if not self.system_metrics:
                return False
            
            latest_metrics = self.system_metrics[-1]
            
            if alert.metric_name == "cpu_percent":
                return latest_metrics.cpu_percent < alert.threshold_value * 0.8
            elif alert.metric_name == "memory_percent":
                return latest_metrics.memory_percent < alert.threshold_value * 0.8
            elif alert.metric_name == "disk_percent":
                return latest_metrics.disk_percent < alert.threshold_value * 0.8
        
        # 其他类型的告警恢复检查
        return False
    
    async def _update_system_status(self):
        """更新系统状态"""
        active_alerts = [a for a in self.alerts.values() if not a.resolved]
        
        if not active_alerts:
            self.stats["system_status"] = PerformanceStatus.EXCELLENT.value
        else:
            critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
            error_alerts = [a for a in active_alerts if a.level == AlertLevel.ERROR]
            warning_alerts = [a for a in active_alerts if a.level == AlertLevel.WARNING]
            
            if critical_alerts:
                self.stats["system_status"] = PerformanceStatus.CRITICAL.value
            elif error_alerts:
                self.stats["system_status"] = PerformanceStatus.DEGRADED.value
            elif len(warning_alerts) > 3:
                self.stats["system_status"] = PerformanceStatus.DEGRADED.value
            elif warning_alerts:
                self.stats["system_status"] = PerformanceStatus.NORMAL.value
            else:
                self.stats["system_status"] = PerformanceStatus.GOOD.value
        
        self.stats["active_alerts"] = len(active_alerts)
    
    async def _cleanup_loop(self):
        """清理循环"""
        self.logger.info("启动清理循环")
        
        while self.is_monitoring:
            try:
                # 清理过期数据
                await self._cleanup_expired_data()
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_expired_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(days=self.metrics_retention_days)
        
        # 清理过期告警
        expired_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_time and alert.resolved
        ]
        
        for alert_id in expired_alerts:
            del self.alerts[alert_id]
        
        # 清理过期任务指标
        expired_tasks = [
            task_id for task_id, metrics in self.task_metrics.items()
            if metrics.start_time < cutoff_time
        ]
        
        for task_id in expired_tasks:
            del self.task_metrics[task_id]
        
        if expired_alerts or expired_tasks:
            self.logger.info(f"清理过期数据: {len(expired_alerts)} 告警, {len(expired_tasks)} 任务")
    
    async def collect_metrics(self, custom_metrics: Dict[str, Any]):
        """收集自定义指标"""
        try:
            # 与现有指标收集器集成
            await self.metrics_collector.collect_custom_metrics(custom_metrics)
            
            self.stats["total_metrics_collected"] += 1
            
        except Exception as e:
            self.logger.error(f"收集自定义指标失败: {e}")
    
    def record_task_start(self, task_id: str, task_type: str):
        """记录任务开始"""
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            start_time=datetime.now(),
            end_time=None,
            duration=None,
            status="running",
            cpu_usage=0.0,
            memory_usage=0.0,
            success=False,
            error_info=None
        )
    
    def record_task_end(self, task_id: str, success: bool, error_info: Optional[str] = None):
        """记录任务结束"""
        if task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.status = "completed" if success else "failed"
            metrics.success = success
            metrics.error_info = error_info
    
    def get_system_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取系统指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = [
            asdict(m) for m in self.system_metrics
            if m.timestamp >= cutoff_time
        ]
        
        # 转换datetime为字符串
        for metrics in filtered_metrics:
            metrics["timestamp"] = metrics["timestamp"].isoformat()
        
        return filtered_metrics
    
    def get_task_metrics(self) -> List[Dict[str, Any]]:
        """获取任务指标"""
        metrics_list = []
        
        for metrics in self.task_metrics.values():
            metrics_dict = asdict(metrics)
            metrics_dict["start_time"] = metrics_dict["start_time"].isoformat()
            if metrics_dict["end_time"]:
                metrics_dict["end_time"] = metrics_dict["end_time"].isoformat()
            metrics_list.append(metrics_dict)
        
        return metrics_list
    
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取智能体指标"""
        result = {}
        
        agents_to_process = [agent_name] if agent_name else self.agent_metrics.keys()
        
        for name in agents_to_process:
            if name in self.agent_metrics:
                metrics_list = []
                for metrics in self.agent_metrics[name]:
                    metrics_dict = asdict(metrics)
                    metrics_dict["timestamp"] = metrics_dict["timestamp"].isoformat()
                    metrics_dict["last_activity"] = metrics_dict["last_activity"].isoformat()
                    metrics_list.append(metrics_dict)
                result[name] = metrics_list
        
        return result
    
    def get_mcp_metrics(self, mcp_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取MCP指标"""
        result = {}
        
        mcps_to_process = [mcp_name] if mcp_name else self.mcp_metrics.keys()
        
        for name in mcps_to_process:
            if name in self.mcp_metrics:
                metrics_list = []
                for metrics in self.mcp_metrics[name]:
                    metrics_dict = asdict(metrics)
                    metrics_dict["timestamp"] = metrics_dict["timestamp"].isoformat()
                    metrics_dict["last_activity"] = metrics_dict["last_activity"].isoformat()
                    metrics_list.append(metrics_dict)
                result[name] = metrics_list
        
        return result
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取告警信息"""
        alerts_list = []
        
        for alert in self.alerts.values():
            if resolved is None or alert.resolved == resolved:
                alert_dict = asdict(alert)
                alert_dict["timestamp"] = alert_dict["timestamp"].isoformat()
                if alert_dict["resolution_time"]:
                    alert_dict["resolution_time"] = alert_dict["resolution_time"].isoformat()
                alert_dict["alert_type"] = alert_dict["alert_type"].value
                alert_dict["level"] = alert_dict["level"].value
                alerts_list.append(alert_dict)
        
        return sorted(alerts_list, key=lambda x: x["timestamp"], reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        self.stats["last_health_check"] = datetime.now().isoformat()
        
        health_status = {
            "status": "healthy" if self.is_monitoring else "stopped",
            "monitoring": self.is_monitoring,
            "stats": self.get_stats(),
            "system_status": self.stats["system_status"],
            "active_alerts": self.stats["active_alerts"],
            "components": {
                "real_time_monitor": await self.real_time_monitor.health_check(),
                "metrics_collector": await self.metrics_collector.health_check(),
                "alert_system": await self.alert_system.health_check()
            }
        }
        
        return health_status
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            "system_status": self.stats["system_status"],
            "monitoring_duration": None,
            "current_metrics": {},
            "alerts_summary": {
                "total": len(self.alerts),
                "active": len([a for a in self.alerts.values() if not a.resolved]),
                "by_level": defaultdict(int)
            },
            "performance_trends": {}
        }
        
        # 计算监控时长
        if self.stats["monitoring_start_time"]:
            start_time = datetime.fromisoformat(self.stats["monitoring_start_time"])
            duration = (datetime.now() - start_time).total_seconds()
            summary["monitoring_duration"] = duration
        
        # 当前系统指标
        if self.system_metrics:
            latest = self.system_metrics[-1]
            summary["current_metrics"] = {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_percent": latest.disk_percent,
                "process_count": latest.process_count
            }
        
        # 告警统计
        for alert in self.alerts.values():
            summary["alerts_summary"]["by_level"][alert.level.value] += 1
        
        return summary


if __name__ == "__main__":
    # 测试性能监控器
    import asyncio
    
    async def test_performance_monitor():
        monitor = PerformanceMonitor()
        
        print("启动性能监控器...")
        await monitor.start()
        
        # 模拟任务
        monitor.record_task_start("test_task_1", "development")
        await asyncio.sleep(2)
        monitor.record_task_end("test_task_1", True)
        
        monitor.record_task_start("test_task_2", "deployment")
        await asyncio.sleep(1)
        monitor.record_task_end("test_task_2", False, "模拟错误")
        
        # 等待一些监控数据
        await asyncio.sleep(35)
        
        # 获取指标
        system_metrics = monitor.get_system_metrics(hours=1)
        print(f"系统指标数量: {len(system_metrics)}")
        
        task_metrics = monitor.get_task_metrics()
        print(f"任务指标数量: {len(task_metrics)}")
        
        alerts = monitor.get_alerts()
        print(f"告警数量: {len(alerts)}")
        
        # 性能摘要
        summary = monitor.get_performance_summary()
        print(f"性能摘要: {summary}")
        
        # 健康检查
        health = await monitor.health_check()
        print(f"健康状态: {health['status']}")
        
        print("停止性能监控器...")
        await monitor.stop()
    
    # 运行测试
    asyncio.run(test_performance_monitor())

