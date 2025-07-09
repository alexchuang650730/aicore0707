"""
MonitoringService - 监控服务
提供实时监控、告警和性能分析功能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """告警"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Metric:
    """指标"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class PerformanceProfile:
    """性能概况"""
    component: str
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MonitoringService:
    """监控服务"""
    
    def __init__(self, config, resource_manager):
        self.config = config
        self.resource_manager = resource_manager
        self.logger = logging.getLogger(__name__)
        
        # 告警管理
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = {}
        self.max_alerts = 1000
        
        # 指标收集
        self.metrics: Dict[str, deque] = {}
        self.metric_handlers: Dict[str, List[Callable]] = {}
        self.max_metric_history = 10000
        
        # 性能分析
        self.performance_profiles: deque = deque(maxlen=5000)
        self.performance_stats: Dict[str, Dict[str, Any]] = {}
        
        # 监控配置
        self.monitoring_interval = config.monitoring_interval
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 阈值配置
        self.thresholds = {
            "cpu_usage": {"warning": 80, "critical": 95},
            "memory_usage": {"warning": 85, "critical": 95},
            "disk_usage": {"warning": 90, "critical": 98},
            "response_time": {"warning": 5.0, "critical": 10.0},
            "error_rate": {"warning": 0.05, "critical": 0.1}
        }
        
        # 健康检查
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, bool] = {}
        
        self.logger.info("监控服务初始化完成")
    
    async def initialize(self):
        """初始化监控服务"""
        try:
            # 注册默认健康检查
            self._register_default_health_checks()
            
            # 加载历史数据
            await self._load_monitoring_data()
            
            self.logger.info("监控服务初始化成功")
            
        except Exception as e:
            self.logger.error(f"监控服务初始化失败: {e}")
            raise
    
    async def start(self):
        """启动监控服务"""
        try:
            # 启动监控任务
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("监控服务启动")
            
        except Exception as e:
            self.logger.error(f"启动监控服务失败: {e}")
            raise
    
    async def stop(self):
        """停止监控服务"""
        try:
            # 停止监控任务
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # 保存监控数据
            await self._save_monitoring_data()
            
            self.logger.info("监控服务停止")
            
        except Exception as e:
            self.logger.error(f"停止监控服务失败: {e}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查监控任务是否运行
            if not self.monitoring_task or self.monitoring_task.done():
                return False
            
            # 检查告警数量
            if len(self.alerts) > self.max_alerts * 0.9:
                return False
            
            # 检查关键告警
            critical_alerts = [
                alert for alert in self.alerts.values()
                if alert.level == AlertLevel.CRITICAL and not alert.resolved
            ]
            if len(critical_alerts) > 5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    # 告警管理
    async def create_alert(self, level: AlertLevel, title: str, message: str, source: str = "system", metadata: Dict[str, Any] = None) -> str:
        """创建告警"""
        try:
            alert_id = f"alert_{int(time.time() * 1000)}_{len(self.alerts)}"
            
            alert = Alert(
                id=alert_id,
                level=level,
                title=title,
                message=message,
                source=source,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            self.alerts[alert_id] = alert
            
            # 限制告警数量
            if len(self.alerts) > self.max_alerts:
                # 删除最旧的已解决告警
                resolved_alerts = [
                    (alert.timestamp, alert_id) for alert_id, alert in self.alerts.items()
                    if alert.resolved
                ]
                if resolved_alerts:
                    resolved_alerts.sort()
                    oldest_id = resolved_alerts[0][1]
                    del self.alerts[oldest_id]
            
            # 触发告警处理器
            await self._trigger_alert_handlers(alert)
            
            # 记录告警
            self.logger.log(
                logging.WARNING if level in [AlertLevel.WARNING, AlertLevel.ERROR] else logging.CRITICAL,
                f"告警创建: [{level.value.upper()}] {title} - {message}"
            )
            
            return alert_id
            
        except Exception as e:
            self.logger.error(f"创建告警失败: {e}")
            raise
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            self.logger.info(f"告警已解决: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")
            return False
    
    def register_alert_handler(self, level: AlertLevel, handler: Callable):
        """注册告警处理器"""
        if level not in self.alert_handlers:
            self.alert_handlers[level] = []
        self.alert_handlers[level].append(handler)
    
    async def _trigger_alert_handlers(self, alert: Alert):
        """触发告警处理器"""
        if alert.level in self.alert_handlers:
            for handler in self.alert_handlers[alert.level]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    self.logger.error(f"告警处理器错误: {e}")
    
    # 指标收集
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, tags: Dict[str, str] = None):
        """记录指标"""
        try:
            metric = Metric(
                name=name,
                type=metric_type,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_metric_history)
            
            self.metrics[name].append(metric)
            
            # 触发指标处理器
            self._trigger_metric_handlers(metric)
            
            # 检查阈值
            asyncio.create_task(self._check_metric_thresholds(metric))
            
        except Exception as e:
            self.logger.error(f"记录指标失败: {e}")
    
    def register_metric_handler(self, metric_name: str, handler: Callable):
        """注册指标处理器"""
        if metric_name not in self.metric_handlers:
            self.metric_handlers[metric_name] = []
        self.metric_handlers[metric_name].append(handler)
    
    def _trigger_metric_handlers(self, metric: Metric):
        """触发指标处理器"""
        if metric.name in self.metric_handlers:
            for handler in self.metric_handlers[metric.name]:
                try:
                    handler(metric)
                except Exception as e:
                    self.logger.error(f"指标处理器错误: {e}")
    
    async def _check_metric_thresholds(self, metric: Metric):
        """检查指标阈值"""
        try:
            if metric.name in self.thresholds:
                thresholds = self.thresholds[metric.name]
                
                if metric.value >= thresholds.get("critical", float('inf')):
                    await self.create_alert(
                        AlertLevel.CRITICAL,
                        f"{metric.name} 达到临界值",
                        f"{metric.name} = {metric.value}, 临界阈值 = {thresholds['critical']}",
                        "threshold_monitor"
                    )
                elif metric.value >= thresholds.get("warning", float('inf')):
                    await self.create_alert(
                        AlertLevel.WARNING,
                        f"{metric.name} 达到警告值",
                        f"{metric.name} = {metric.value}, 警告阈值 = {thresholds['warning']}",
                        "threshold_monitor"
                    )
                    
        except Exception as e:
            self.logger.error(f"检查指标阈值失败: {e}")
    
    # 性能分析
    def record_performance(self, component: str, operation: str, duration: float, success: bool = True, error_message: str = None, metadata: Dict[str, Any] = None):
        """记录性能数据"""
        try:
            profile = PerformanceProfile(
                component=component,
                operation=operation,
                duration=duration,
                timestamp=datetime.now(),
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            self.performance_profiles.append(profile)
            
            # 更新性能统计
            self._update_performance_stats(profile)
            
            # 记录响应时间指标
            self.record_metric(
                f"{component}.{operation}.response_time",
                duration,
                MetricType.TIMER,
                {"component": component, "operation": operation}
            )
            
            # 记录成功率指标
            self.record_metric(
                f"{component}.{operation}.success_rate",
                1.0 if success else 0.0,
                MetricType.GAUGE,
                {"component": component, "operation": operation}
            )
            
        except Exception as e:
            self.logger.error(f"记录性能数据失败: {e}")
    
    def _update_performance_stats(self, profile: PerformanceProfile):
        """更新性能统计"""
        key = f"{profile.component}.{profile.operation}"
        
        if key not in self.performance_stats:
            self.performance_stats[key] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "avg_duration": 0.0,
                "success_rate": 0.0
            }
        
        stats = self.performance_stats[key]
        stats["total_calls"] += 1
        
        if profile.success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        stats["total_duration"] += profile.duration
        stats["min_duration"] = min(stats["min_duration"], profile.duration)
        stats["max_duration"] = max(stats["max_duration"], profile.duration)
        stats["avg_duration"] = stats["total_duration"] / stats["total_calls"]
        stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
    
    # 健康检查
    def register_health_check(self, name: str, check_func: Callable):
        """注册健康检查"""
        self.health_checks[name] = check_func
    
    async def run_health_checks(self) -> Dict[str, bool]:
        """运行所有健康检查"""
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = bool(result)
                self.health_status[name] = bool(result)
                
                # 如果健康检查失败，创建告警
                if not result:
                    await self.create_alert(
                        AlertLevel.ERROR,
                        f"健康检查失败: {name}",
                        f"组件 {name} 健康检查失败",
                        "health_monitor"
                    )
                    
            except Exception as e:
                results[name] = False
                self.health_status[name] = False
                
                await self.create_alert(
                    AlertLevel.ERROR,
                    f"健康检查异常: {name}",
                    f"组件 {name} 健康检查异常: {e}",
                    "health_monitor"
                )
                
                self.logger.error(f"健康检查 {name} 失败: {e}")
        
        return results
    
    def _register_default_health_checks(self):
        """注册默认健康检查"""
        # 系统资源健康检查
        self.register_health_check("system_resources", self._check_system_resources)
        
        # 资源管理器健康检查
        if self.resource_manager:
            self.register_health_check("resource_manager", self.resource_manager.health_check)
    
    async def _check_system_resources(self) -> bool:
        """检查系统资源"""
        try:
            if self.resource_manager:
                stats = await self.resource_manager.get_usage_stats()
                
                # 检查CPU使用率
                if stats.get("cpu_usage", 0) > 95:
                    return False
                
                # 检查内存使用率
                if stats.get("memory_usage", 0) > 95:
                    return False
                
                # 检查磁盘使用率
                if stats.get("disk_usage", 0) > 98:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"系统资源检查失败: {e}")
            return False
    
    # 监控循环
    async def _monitoring_loop(self):
        """监控主循环"""
        while True:
            try:
                # 收集系统指标
                await self._collect_system_metrics()
                
                # 运行健康检查
                await self.run_health_checks()
                
                # 清理过期数据
                await self._cleanup_expired_data()
                
                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            if self.resource_manager:
                # 获取资源使用统计
                stats = await self.resource_manager.get_usage_stats()
                
                # 记录指标
                for metric_name, value in stats.items():
                    self.record_metric(metric_name, value, MetricType.GAUGE)
                
                # 获取系统指标
                system_metrics = await self.resource_manager.get_system_metrics()
                if system_metrics:
                    # CPU指标
                    if "cpu" in system_metrics:
                        self.record_metric("cpu_usage", system_metrics["cpu"]["usage_percent"], MetricType.GAUGE)
                    
                    # 内存指标
                    if "memory" in system_metrics:
                        self.record_metric("memory_usage", system_metrics["memory"]["usage_percent"], MetricType.GAUGE)
                    
                    # 磁盘指标
                    if "disk" in system_metrics:
                        self.record_metric("disk_usage", system_metrics["disk"]["usage_percent"], MetricType.GAUGE)
                    
                    # 进程指标
                    if "processes" in system_metrics:
                        self.record_metric("process_count", system_metrics["processes"]["count"], MetricType.GAUGE)
                        
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
    
    async def _cleanup_expired_data(self):
        """清理过期数据"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=7)
            
            # 清理旧告警
            expired_alerts = [
                alert_id for alert_id, alert in self.alerts.items()
                if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time
            ]
            
            for alert_id in expired_alerts:
                del self.alerts[alert_id]
            
            if expired_alerts:
                self.logger.debug(f"清理过期告警: {len(expired_alerts)} 个")
                
        except Exception as e:
            self.logger.error(f"清理过期数据失败: {e}")
    
    # 查询接口
    def get_alerts(self, level: AlertLevel = None, resolved: bool = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alerts = list(self.alerts.values())
        
        # 过滤条件
        if level is not None:
            alerts = [alert for alert in alerts if alert.level == level]
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        # 按时间排序
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制数量
        if limit > 0:
            alerts = alerts[:limit]
        
        return [asdict(alert) for alert in alerts]
    
    def get_metrics(self, name: str = None, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """获取指标数据"""
        if name:
            if name in self.metrics:
                metrics = list(self.metrics[name])[-limit:] if limit > 0 else list(self.metrics[name])
                return {name: [asdict(metric) for metric in metrics]}
            else:
                return {}
        else:
            result = {}
            for metric_name, metric_list in self.metrics.items():
                metrics = list(metric_list)[-limit:] if limit > 0 else list(metric_list)
                result[metric_name] = [asdict(metric) for metric in metrics]
            return result
    
    def get_performance_stats(self, component: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        if component:
            return {
                key: stats for key, stats in self.performance_stats.items()
                if key.startswith(f"{component}.")
            }
        else:
            return self.performance_stats.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "overall_healthy": all(self.health_status.values()),
            "components": self.health_status.copy(),
            "last_check": datetime.now().isoformat()
        }
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        try:
            # 统计告警
            total_alerts = len(self.alerts)
            unresolved_alerts = len([a for a in self.alerts.values() if not a.resolved])
            critical_alerts = len([a for a in self.alerts.values() if a.level == AlertLevel.CRITICAL and not a.resolved])
            
            # 统计指标
            total_metrics = sum(len(metrics) for metrics in self.metrics.values())
            
            # 统计性能
            total_performance_records = len(self.performance_profiles)
            
            return {
                "alerts": {
                    "total": total_alerts,
                    "unresolved": unresolved_alerts,
                    "critical": critical_alerts
                },
                "metrics": {
                    "total_records": total_metrics,
                    "metric_types": len(self.metrics)
                },
                "performance": {
                    "total_records": total_performance_records,
                    "components": len(self.performance_stats)
                },
                "health": self.get_health_status(),
                "uptime": time.time()  # 简化的运行时间
            }
            
        except Exception as e:
            self.logger.error(f"获取监控摘要失败: {e}")
            return {}
    
    # 持久化
    async def _load_monitoring_data(self):
        """加载监控数据"""
        try:
            monitoring_dir = self.data_dir / "monitoring"
            if monitoring_dir.exists():
                # 加载指标数据
                metrics_file = monitoring_dir / "metrics.json"
                if metrics_file.exists():
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.metrics.update(data)
                
                # 加载告警数据
                alerts_file = monitoring_dir / "alerts.json"
                if alerts_file.exists():
                    with open(alerts_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for alert_data in data:
                            alert = Alert(**alert_data)
                            self.alerts[alert.id] = alert
        except Exception as e:
            self.logger.error(f"加载监控数据失败: {e}")
    
    async def _save_monitoring_data(self):
        """保存监控数据"""
        try:
            monitoring_dir = self.data_dir / "monitoring"
            monitoring_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存指标数据
            metrics_file = monitoring_dir / "metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.metrics), f, ensure_ascii=False, indent=2)
            
            # 保存告警数据
            alerts_file = monitoring_dir / "alerts.json"
            with open(alerts_file, 'w', encoding='utf-8') as f:
                alerts_data = [alert.dict() for alert in self.alerts.values()]
                json.dump(alerts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存监控数据失败: {e}")

