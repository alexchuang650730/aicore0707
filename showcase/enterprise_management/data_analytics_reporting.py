#!/usr/bin/env python3
"""
数据分析报告系统
PowerAutomation 4.1 - 企业级数据分析和报告生成

功能特性:
- 多维度数据分析
- 自动化报告生成
- 实时数据监控
- 可视化图表生成
- 预测性分析
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import statistics
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportType(Enum):
    """报告类型枚举"""
    PERFORMANCE = "performance"
    PRODUCTIVITY = "productivity"
    COLLABORATION = "collaboration"
    USAGE = "usage"
    SECURITY = "security"
    CUSTOM = "custom"

class MetricType(Enum):
    """指标类型枚举"""
    COUNT = "count"
    RATE = "rate"
    DURATION = "duration"
    PERCENTAGE = "percentage"
    SCORE = "score"
    TREND = "trend"

class ChartType(Enum):
    """图表类型枚举"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"

class TimeRange(Enum):
    """时间范围枚举"""
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    LAST_90D = "last_90d"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"

@dataclass
class DataPoint:
    """数据点"""
    timestamp: datetime
    metric_name: str
    value: float
    dimensions: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Metric:
    """指标定义"""
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    unit: str
    aggregation_method: str = "sum"  # sum, avg, max, min, count
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class Report:
    """报告"""
    report_id: str
    name: str
    description: str
    report_type: ReportType
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    time_range: TimeRange = TimeRange.LAST_30D
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    metrics: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None
    recipients: List[str] = field(default_factory=list)

@dataclass
class Dashboard:
    """仪表板"""
    dashboard_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    is_public: bool = False
    shared_with: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """告警"""
    alert_id: str
    name: str
    description: str
    metric_id: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    notification_channels: List[str] = field(default_factory=list)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class DataAnalyticsReportingManager:
    """数据分析报告管理器"""
    
    def __init__(self):
        self.data_points: List[DataPoint] = []
        self.metrics: Dict[str, Metric] = {}
        self.reports: Dict[str, Report] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        self.alerts: Dict[str, Alert] = {}
        
        # 数据索引
        self.metric_data: Dict[str, List[DataPoint]] = defaultdict(list)
        self.time_series_cache: Dict[str, Dict] = {}
        
        # 分析结果缓存
        self.analysis_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 预定义指标
        self._initialize_default_metrics()
        
        # 启动后台任务
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("数据分析报告管理器初始化完成")
    
    def _initialize_default_metrics(self):
        """初始化默认指标"""
        default_metrics = [
            # 性能指标
            Metric("response_time", "响应时间", "API响应时间", MetricType.DURATION, "ms", "avg"),
            Metric("throughput", "吞吐量", "每秒处理请求数", MetricType.RATE, "req/s", "sum"),
            Metric("error_rate", "错误率", "错误请求占比", MetricType.PERCENTAGE, "%", "avg"),
            Metric("cpu_usage", "CPU使用率", "系统CPU使用率", MetricType.PERCENTAGE, "%", "avg"),
            Metric("memory_usage", "内存使用率", "系统内存使用率", MetricType.PERCENTAGE, "%", "avg"),
            
            # 生产力指标
            Metric("tasks_completed", "任务完成数", "完成的任务数量", MetricType.COUNT, "个", "sum"),
            Metric("code_commits", "代码提交数", "代码提交次数", MetricType.COUNT, "次", "sum"),
            Metric("bugs_fixed", "修复Bug数", "修复的Bug数量", MetricType.COUNT, "个", "sum"),
            Metric("features_delivered", "功能交付数", "交付的功能数量", MetricType.COUNT, "个", "sum"),
            
            # 协作指标
            Metric("collaboration_sessions", "协作会话数", "协作会话数量", MetricType.COUNT, "次", "sum"),
            Metric("team_activity", "团队活跃度", "团队成员活跃度评分", MetricType.SCORE, "分", "avg"),
            Metric("knowledge_sharing", "知识分享次数", "知识分享活动次数", MetricType.COUNT, "次", "sum"),
            
            # 使用指标
            Metric("active_users", "活跃用户数", "活跃用户数量", MetricType.COUNT, "人", "count"),
            Metric("session_duration", "会话时长", "用户会话平均时长", MetricType.DURATION, "分钟", "avg"),
            Metric("feature_usage", "功能使用率", "各功能使用频率", MetricType.RATE, "次/天", "avg"),
            
            # 安全指标
            Metric("login_failures", "登录失败次数", "登录失败尝试次数", MetricType.COUNT, "次", "sum"),
            Metric("security_alerts", "安全告警数", "安全告警数量", MetricType.COUNT, "个", "sum"),
            Metric("permission_violations", "权限违规次数", "权限违规尝试次数", MetricType.COUNT, "次", "sum")
        ]
        
        for metric in default_metrics:
            self.metrics[metric.metric_id] = metric
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        # 数据聚合任务
        asyncio.create_task(self._data_aggregation_task())
        
        # 告警检查任务
        asyncio.create_task(self._alert_monitoring_task())
        
        # 缓存清理任务
        asyncio.create_task(self._cache_cleanup_task())
        
        # 报告生成任务
        asyncio.create_task(self._scheduled_report_task())
    
    async def _data_aggregation_task(self):
        """数据聚合任务"""
        while True:
            try:
                await self._aggregate_time_series_data()
                await asyncio.sleep(60)  # 每分钟聚合一次
                
            except Exception as e:
                logger.error(f"数据聚合任务失败: {e}")
                await asyncio.sleep(60)
    
    async def _alert_monitoring_task(self):
        """告警监控任务"""
        while True:
            try:
                await self._check_alerts()
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"告警监控任务失败: {e}")
                await asyncio.sleep(30)
    
    async def _cache_cleanup_task(self):
        """缓存清理任务"""
        while True:
            try:
                current_time = datetime.now()
                
                # 清理过期的分析缓存
                expired_keys = []
                for cache_key, cache_data in self.analysis_cache.items():
                    if (current_time - cache_data.get("timestamp", current_time)).total_seconds() > self.cache_ttl:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    del self.analysis_cache[key]
                
                await asyncio.sleep(300)  # 每5分钟清理一次
                
            except Exception as e:
                logger.error(f"缓存清理任务失败: {e}")
                await asyncio.sleep(300)
    
    async def _scheduled_report_task(self):
        """定时报告任务"""
        while True:
            try:
                current_time = datetime.now()
                
                # 检查需要生成的定时报告
                for report in self.reports.values():
                    if report.is_scheduled and report.schedule_cron:
                        # 简化的定时检查逻辑
                        if await self._should_generate_report(report, current_time):
                            await self._generate_scheduled_report(report)
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"定时报告任务失败: {e}")
                await asyncio.sleep(60)
    
    async def record_data_point(self, metric_name: str, value: float,
                              dimensions: Optional[Dict[str, str]] = None,
                              metadata: Optional[Dict[str, Any]] = None,
                              timestamp: Optional[datetime] = None):
        """记录数据点"""
        try:
            if metric_name not in self.metrics:
                logger.warning(f"未知指标: {metric_name}")
                return
            
            data_point = DataPoint(
                timestamp=timestamp or datetime.now(),
                metric_name=metric_name,
                value=value,
                dimensions=dimensions or {},
                metadata=metadata or {}
            )
            
            self.data_points.append(data_point)
            self.metric_data[metric_name].append(data_point)
            
            # 清理旧数据（保留90天）
            cutoff_time = datetime.now() - timedelta(days=90)
            self.metric_data[metric_name] = [
                dp for dp in self.metric_data[metric_name]
                if dp.timestamp >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"记录数据点失败: {e}")
    
    async def create_metric(self, name: str, description: str, metric_type: MetricType,
                          unit: str, aggregation_method: str = "sum",
                          tags: Optional[List[str]] = None) -> str:
        """创建自定义指标"""
        try:
            metric_id = str(uuid.uuid4())
            
            metric = Metric(
                metric_id=metric_id,
                name=name,
                description=description,
                metric_type=metric_type,
                unit=unit,
                aggregation_method=aggregation_method,
                tags=tags or []
            )
            
            self.metrics[metric_id] = metric
            
            logger.info(f"指标已创建: {name} ({metric_id})")
            return metric_id
            
        except Exception as e:
            logger.error(f"创建指标失败: {e}")
            raise
    
    async def create_report(self, name: str, description: str, report_type: ReportType,
                          created_by: str, metrics: List[str],
                          time_range: TimeRange = TimeRange.LAST_30D,
                          filters: Optional[Dict[str, Any]] = None,
                          charts: Optional[List[Dict[str, Any]]] = None) -> str:
        """创建报告"""
        try:
            report_id = str(uuid.uuid4())
            
            report = Report(
                report_id=report_id,
                name=name,
                description=description,
                report_type=report_type,
                created_by=created_by,
                metrics=metrics,
                time_range=time_range,
                filters=filters or {},
                charts=charts or []
            )
            
            self.reports[report_id] = report
            
            logger.info(f"报告已创建: {name} ({report_id})")
            return report_id
            
        except Exception as e:
            logger.error(f"创建报告失败: {e}")
            raise
    
    async def generate_report(self, report_id: str) -> Dict[str, Any]:
        """生成报告"""
        try:
            if report_id not in self.reports:
                raise ValueError("报告不存在")
            
            report = self.reports[report_id]
            
            # 检查缓存
            cache_key = f"report_{report_id}_{report.updated_at.isoformat()}"
            if cache_key in self.analysis_cache:
                cache_data = self.analysis_cache[cache_key]
                if (datetime.now() - cache_data["timestamp"]).total_seconds() < self.cache_ttl:
                    return cache_data["result"]
            
            # 获取时间范围
            start_date, end_date = self._get_time_range(report.time_range, 
                                                       report.custom_start_date, 
                                                       report.custom_end_date)
            
            # 收集指标数据
            report_data = {
                "report_info": {
                    "report_id": report.report_id,
                    "name": report.name,
                    "description": report.description,
                    "type": report.report_type.value,
                    "generated_at": datetime.now().isoformat(),
                    "time_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                },
                "metrics": {},
                "charts": [],
                "summary": {},
                "insights": []
            }
            
            # 分析每个指标
            for metric_id in report.metrics:
                if metric_id in self.metrics:
                    metric_analysis = await self._analyze_metric(
                        metric_id, start_date, end_date, report.filters
                    )
                    report_data["metrics"][metric_id] = metric_analysis
            
            # 生成图表
            for chart_config in report.charts:
                chart_data = await self._generate_chart(chart_config, start_date, end_date)
                report_data["charts"].append(chart_data)
            
            # 生成摘要和洞察
            report_data["summary"] = await self._generate_report_summary(report_data["metrics"])
            report_data["insights"] = await self._generate_insights(report_data["metrics"])
            
            # 缓存结果
            self.analysis_cache[cache_key] = {
                "result": report_data,
                "timestamp": datetime.now()
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise
    
    async def _analyze_metric(self, metric_id: str, start_date: datetime, 
                            end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """分析指标"""
        try:
            metric = self.metrics[metric_id]
            data_points = self.metric_data.get(metric_id, [])
            
            # 过滤时间范围
            filtered_points = [
                dp for dp in data_points
                if start_date <= dp.timestamp <= end_date
            ]
            
            # 应用过滤器
            for filter_key, filter_value in filters.items():
                filtered_points = [
                    dp for dp in filtered_points
                    if dp.dimensions.get(filter_key) == filter_value
                ]
            
            if not filtered_points:
                return {
                    "metric_info": {
                        "metric_id": metric_id,
                        "name": metric.name,
                        "description": metric.description,
                        "unit": metric.unit
                    },
                    "statistics": {},
                    "time_series": [],
                    "trends": {}
                }
            
            values = [dp.value for dp in filtered_points]
            
            # 基础统计
            statistics_data = {
                "count": len(values),
                "sum": sum(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0
            }
            
            # 时间序列数据
            time_series = [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                    "dimensions": dp.dimensions
                }
                for dp in filtered_points
            ]
            
            # 趋势分析
            trends = await self._calculate_trends(filtered_points)
            
            return {
                "metric_info": {
                    "metric_id": metric_id,
                    "name": metric.name,
                    "description": metric.description,
                    "unit": metric.unit,
                    "type": metric.metric_type.value
                },
                "statistics": statistics_data,
                "time_series": time_series,
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"分析指标失败: {e}")
            return {}
    
    async def _calculate_trends(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """计算趋势"""
        try:
            if len(data_points) < 2:
                return {"trend": "insufficient_data"}
            
            # 按时间排序
            sorted_points = sorted(data_points, key=lambda x: x.timestamp)
            
            # 准备数据进行线性回归
            timestamps = [(dp.timestamp - sorted_points[0].timestamp).total_seconds() 
                         for dp in sorted_points]
            values = [dp.value for dp in sorted_points]
            
            # 线性回归
            X = np.array(timestamps).reshape(-1, 1)
            y = np.array(values)
            
            model = LinearRegression()
            model.fit(X, y)
            
            slope = model.coef_[0]
            r_squared = model.score(X, y)
            
            # 趋势判断
            if abs(slope) < 0.001:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # 计算变化率
            if len(sorted_points) >= 2:
                first_value = sorted_points[0].value
                last_value = sorted_points[-1].value
                
                if first_value != 0:
                    change_rate = ((last_value - first_value) / first_value) * 100
                else:
                    change_rate = 0
            else:
                change_rate = 0
            
            return {
                "trend": trend_direction,
                "slope": slope,
                "r_squared": r_squared,
                "change_rate": change_rate,
                "confidence": "high" if r_squared > 0.7 else "medium" if r_squared > 0.3 else "low"
            }
            
        except Exception as e:
            logger.error(f"计算趋势失败: {e}")
            return {"trend": "error"}
    
    async def _generate_chart(self, chart_config: Dict[str, Any], 
                            start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成图表"""
        try:
            chart_type = ChartType(chart_config.get("type", "line"))
            metric_ids = chart_config.get("metrics", [])
            title = chart_config.get("title", "图表")
            
            # 收集数据
            chart_data = {
                "chart_id": str(uuid.uuid4()),
                "title": title,
                "type": chart_type.value,
                "data": {},
                "config": chart_config
            }
            
            for metric_id in metric_ids:
                if metric_id in self.metrics:
                    metric_data = self.metric_data.get(metric_id, [])
                    
                    # 过滤时间范围
                    filtered_data = [
                        dp for dp in metric_data
                        if start_date <= dp.timestamp <= end_date
                    ]
                    
                    chart_data["data"][metric_id] = [
                        {
                            "timestamp": dp.timestamp.isoformat(),
                            "value": dp.value,
                            "metric_name": self.metrics[metric_id].name
                        }
                        for dp in filtered_data
                    ]
            
            # 生成图表图像（简化版本）
            chart_image = await self._create_chart_image(chart_data)
            chart_data["image"] = chart_image
            
            return chart_data
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            return {}
    
    async def _create_chart_image(self, chart_data: Dict[str, Any]) -> str:
        """创建图表图像"""
        try:
            plt.figure(figsize=(10, 6))
            
            chart_type = chart_data["type"]
            data = chart_data["data"]
            
            if chart_type == "line":
                for metric_id, points in data.items():
                    if points:
                        timestamps = [datetime.fromisoformat(p["timestamp"]) for p in points]
                        values = [p["value"] for p in points]
                        plt.plot(timestamps, values, label=points[0]["metric_name"], marker='o')
                
                plt.xlabel("时间")
                plt.ylabel("值")
                plt.legend()
                plt.xticks(rotation=45)
                
            elif chart_type == "bar":
                # 简化的柱状图实现
                metric_names = []
                metric_values = []
                
                for metric_id, points in data.items():
                    if points:
                        metric_names.append(points[0]["metric_name"])
                        metric_values.append(sum(p["value"] for p in points) / len(points))
                
                plt.bar(metric_names, metric_values)
                plt.xlabel("指标")
                plt.ylabel("平均值")
                plt.xticks(rotation=45)
            
            plt.title(chart_data["title"])
            plt.tight_layout()
            
            # 保存为base64字符串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"创建图表图像失败: {e}")
            return ""
    
    async def _generate_report_summary(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告摘要"""
        try:
            summary = {
                "total_metrics": len(metrics_data),
                "key_insights": [],
                "performance_indicators": {},
                "alerts": []
            }
            
            # 分析关键指标
            for metric_id, metric_data in metrics_data.items():
                if not metric_data.get("statistics"):
                    continue
                
                stats = metric_data["statistics"]
                trends = metric_data.get("trends", {})
                metric_info = metric_data["metric_info"]
                
                # 性能指标
                if metric_info["type"] in ["duration", "rate", "percentage"]:
                    summary["performance_indicators"][metric_id] = {
                        "name": metric_info["name"],
                        "current_value": stats.get("mean", 0),
                        "trend": trends.get("trend", "unknown"),
                        "change_rate": trends.get("change_rate", 0)
                    }
                
                # 异常检测
                if stats.get("std_dev", 0) > 0:
                    cv = stats["std_dev"] / stats["mean"] if stats["mean"] != 0 else 0
                    if cv > 0.5:  # 变异系数大于0.5认为是异常
                        summary["alerts"].append({
                            "type": "high_variability",
                            "metric": metric_info["name"],
                            "message": f"{metric_info['name']}存在较大波动"
                        })
            
            return summary
            
        except Exception as e:
            logger.error(f"生成报告摘要失败: {e}")
            return {}
    
    async def _generate_insights(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成洞察"""
        try:
            insights = []
            
            # 趋势洞察
            for metric_id, metric_data in metrics_data.items():
                trends = metric_data.get("trends", {})
                metric_info = metric_data["metric_info"]
                
                if trends.get("trend") == "increasing" and trends.get("confidence") == "high":
                    insights.append({
                        "type": "trend",
                        "severity": "info",
                        "title": f"{metric_info['name']}呈上升趋势",
                        "description": f"{metric_info['name']}在观察期内呈现明显上升趋势，变化率为{trends.get('change_rate', 0):.2f}%",
                        "recommendation": "建议持续监控该指标的变化"
                    })
                
                elif trends.get("trend") == "decreasing" and trends.get("confidence") == "high":
                    insights.append({
                        "type": "trend",
                        "severity": "warning",
                        "title": f"{metric_info['name']}呈下降趋势",
                        "description": f"{metric_info['name']}在观察期内呈现明显下降趋势，变化率为{trends.get('change_rate', 0):.2f}%",
                        "recommendation": "建议分析下降原因并采取相应措施"
                    })
            
            # 性能洞察
            performance_metrics = ["response_time", "error_rate", "cpu_usage", "memory_usage"]
            for metric_id in performance_metrics:
                if metric_id in metrics_data:
                    stats = metrics_data[metric_id].get("statistics", {})
                    mean_value = stats.get("mean", 0)
                    
                    if metric_id == "response_time" and mean_value > 1000:  # 响应时间大于1秒
                        insights.append({
                            "type": "performance",
                            "severity": "warning",
                            "title": "响应时间较长",
                            "description": f"平均响应时间为{mean_value:.2f}ms，超过推荐阈值",
                            "recommendation": "建议优化系统性能或增加资源配置"
                        })
                    
                    elif metric_id == "error_rate" and mean_value > 5:  # 错误率大于5%
                        insights.append({
                            "type": "quality",
                            "severity": "error",
                            "title": "错误率偏高",
                            "description": f"平均错误率为{mean_value:.2f}%，超过可接受范围",
                            "recommendation": "建议立即排查错误原因并修复相关问题"
                        })
            
            return insights
            
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return []
    
    async def create_dashboard(self, name: str, description: str, created_by: str,
                             widgets: Optional[List[Dict[str, Any]]] = None) -> str:
        """创建仪表板"""
        try:
            dashboard_id = str(uuid.uuid4())
            
            dashboard = Dashboard(
                dashboard_id=dashboard_id,
                name=name,
                description=description,
                created_by=created_by,
                widgets=widgets or []
            )
            
            self.dashboards[dashboard_id] = dashboard
            
            logger.info(f"仪表板已创建: {name} ({dashboard_id})")
            return dashboard_id
            
        except Exception as e:
            logger.error(f"创建仪表板失败: {e}")
            raise
    
    async def create_alert(self, name: str, description: str, metric_id: str,
                         condition: str, threshold: float, created_by: str,
                         notification_channels: Optional[List[str]] = None) -> str:
        """创建告警"""
        try:
            if metric_id not in self.metrics:
                raise ValueError("指标不存在")
            
            alert_id = str(uuid.uuid4())
            
            alert = Alert(
                alert_id=alert_id,
                name=name,
                description=description,
                metric_id=metric_id,
                condition=condition,
                threshold=threshold,
                created_by=created_by,
                notification_channels=notification_channels or []
            )
            
            self.alerts[alert_id] = alert
            
            logger.info(f"告警已创建: {name} ({alert_id})")
            return alert_id
            
        except Exception as e:
            logger.error(f"创建告警失败: {e}")
            raise
    
    async def _check_alerts(self):
        """检查告警"""
        try:
            current_time = datetime.now()
            
            for alert in self.alerts.values():
                if not alert.is_active:
                    continue
                
                # 获取最近的指标数据
                metric_data = self.metric_data.get(alert.metric_id, [])
                if not metric_data:
                    continue
                
                # 获取最近5分钟的数据
                recent_data = [
                    dp for dp in metric_data
                    if (current_time - dp.timestamp).total_seconds() <= 300
                ]
                
                if not recent_data:
                    continue
                
                # 计算当前值
                current_value = sum(dp.value for dp in recent_data) / len(recent_data)
                
                # 检查告警条件
                triggered = False
                if alert.condition == ">" and current_value > alert.threshold:
                    triggered = True
                elif alert.condition == "<" and current_value < alert.threshold:
                    triggered = True
                elif alert.condition == ">=" and current_value >= alert.threshold:
                    triggered = True
                elif alert.condition == "<=" and current_value <= alert.threshold:
                    triggered = True
                elif alert.condition == "==" and current_value == alert.threshold:
                    triggered = True
                elif alert.condition == "!=" and current_value != alert.threshold:
                    triggered = True
                
                if triggered:
                    await self._trigger_alert(alert, current_value)
            
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    async def _trigger_alert(self, alert: Alert, current_value: float):
        """触发告警"""
        try:
            alert.last_triggered = datetime.now()
            alert.trigger_count += 1
            
            # 发送告警通知
            alert_message = {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "description": alert.description,
                "metric_name": self.metrics[alert.metric_id].name,
                "current_value": current_value,
                "threshold": alert.threshold,
                "condition": alert.condition,
                "triggered_at": alert.last_triggered.isoformat()
            }
            
            # 这里可以集成实际的通知系统
            logger.warning(f"告警触发: {alert.name} - 当前值: {current_value}, 阈值: {alert.threshold}")
            
        except Exception as e:
            logger.error(f"触发告警失败: {e}")
    
    def _get_time_range(self, time_range: TimeRange, 
                       custom_start: Optional[datetime] = None,
                       custom_end: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """获取时间范围"""
        end_date = datetime.now()
        
        if time_range == TimeRange.CUSTOM:
            start_date = custom_start or (end_date - timedelta(days=30))
            end_date = custom_end or end_date
        elif time_range == TimeRange.LAST_24H:
            start_date = end_date - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7D:
            start_date = end_date - timedelta(days=7)
        elif time_range == TimeRange.LAST_30D:
            start_date = end_date - timedelta(days=30)
        elif time_range == TimeRange.LAST_90D:
            start_date = end_date - timedelta(days=90)
        elif time_range == TimeRange.LAST_YEAR:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
    
    async def _aggregate_time_series_data(self):
        """聚合时间序列数据"""
        try:
            # 按小时聚合数据
            current_time = datetime.now()
            hour_start = current_time.replace(minute=0, second=0, microsecond=0)
            
            for metric_id, data_points in self.metric_data.items():
                # 获取当前小时的数据
                hour_data = [
                    dp for dp in data_points
                    if hour_start <= dp.timestamp < hour_start + timedelta(hours=1)
                ]
                
                if hour_data:
                    metric = self.metrics[metric_id]
                    
                    # 根据聚合方法计算值
                    if metric.aggregation_method == "sum":
                        aggregated_value = sum(dp.value for dp in hour_data)
                    elif metric.aggregation_method == "avg":
                        aggregated_value = sum(dp.value for dp in hour_data) / len(hour_data)
                    elif metric.aggregation_method == "max":
                        aggregated_value = max(dp.value for dp in hour_data)
                    elif metric.aggregation_method == "min":
                        aggregated_value = min(dp.value for dp in hour_data)
                    elif metric.aggregation_method == "count":
                        aggregated_value = len(hour_data)
                    else:
                        aggregated_value = sum(dp.value for dp in hour_data)
                    
                    # 存储聚合数据
                    cache_key = f"hourly_{metric_id}_{hour_start.isoformat()}"
                    self.time_series_cache[cache_key] = {
                        "metric_id": metric_id,
                        "timestamp": hour_start,
                        "value": aggregated_value,
                        "data_points_count": len(hour_data)
                    }
            
        except Exception as e:
            logger.error(f"聚合时间序列数据失败: {e}")
    
    async def _should_generate_report(self, report: Report, current_time: datetime) -> bool:
        """检查是否应该生成报告"""
        # 简化的定时检查逻辑
        # 实际实现中应该使用cron表达式解析
        return False
    
    async def _generate_scheduled_report(self, report: Report):
        """生成定时报告"""
        try:
            report_data = await self.generate_report(report.report_id)
            
            # 发送给收件人
            for recipient in report.recipients:
                # 这里可以集成邮件或其他通知系统
                logger.info(f"定时报告已生成并发送给: {recipient}")
            
        except Exception as e:
            logger.error(f"生成定时报告失败: {e}")
    
    async def get_analytics_dashboard(self) -> Dict[str, Any]:
        """获取分析仪表板"""
        try:
            current_time = datetime.now()
            
            # 系统概览
            system_overview = {
                "total_metrics": len(self.metrics),
                "total_reports": len(self.reports),
                "total_dashboards": len(self.dashboards),
                "total_alerts": len(self.alerts),
                "active_alerts": len([a for a in self.alerts.values() if a.is_active]),
                "data_points_count": len(self.data_points)
            }
            
            # 最近24小时的数据统计
            last_24h = current_time - timedelta(hours=24)
            recent_data_points = [
                dp for dp in self.data_points
                if dp.timestamp >= last_24h
            ]
            
            # 按指标分组统计
            metric_stats = {}
            for metric_id, metric in self.metrics.items():
                metric_data = [dp for dp in recent_data_points if dp.metric_name == metric_id]
                
                if metric_data:
                    values = [dp.value for dp in metric_data]
                    metric_stats[metric_id] = {
                        "name": metric.name,
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
            
            # 告警统计
            alert_stats = {
                "total_alerts": len(self.alerts),
                "active_alerts": len([a for a in self.alerts.values() if a.is_active]),
                "triggered_today": len([
                    a for a in self.alerts.values()
                    if a.last_triggered and a.last_triggered >= last_24h
                ])
            }
            
            return {
                "system_overview": system_overview,
                "metric_statistics": metric_stats,
                "alert_statistics": alert_stats,
                "cache_statistics": {
                    "analysis_cache_size": len(self.analysis_cache),
                    "time_series_cache_size": len(self.time_series_cache)
                },
                "generated_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取分析仪表板失败: {e}")
            return {}

# 示例使用
async def main():
    """示例主函数"""
    analytics_manager = DataAnalyticsReportingManager()
    
    # 记录一些示例数据
    for i in range(100):
        await analytics_manager.record_data_point(
            "response_time", 
            50 + i * 2 + (i % 10) * 5,  # 模拟响应时间数据
            {"service": "api", "endpoint": "/users"},
            timestamp=datetime.now() - timedelta(hours=i)
        )
        
        await analytics_manager.record_data_point(
            "tasks_completed",
            i % 5 + 1,  # 模拟任务完成数据
            {"team": "development", "project": "ai_assistant"}
        )
    
    # 创建报告
    report_id = await analytics_manager.create_report(
        name="性能分析报告",
        description="系统性能和生产力分析",
        report_type=ReportType.PERFORMANCE,
        created_by="admin",
        metrics=["response_time", "tasks_completed"],
        charts=[
            {
                "type": "line",
                "title": "响应时间趋势",
                "metrics": ["response_time"]
            }
        ]
    )
    
    # 生成报告
    report_data = await analytics_manager.generate_report(report_id)
    print(f"报告数据: {json.dumps(report_data, indent=2, ensure_ascii=False)}")
    
    # 创建告警
    alert_id = await analytics_manager.create_alert(
        name="响应时间告警",
        description="响应时间超过阈值告警",
        metric_id="response_time",
        condition=">",
        threshold=100.0,
        created_by="admin"
    )
    
    # 获取分析仪表板
    dashboard = await analytics_manager.get_analytics_dashboard()
    print(f"分析仪表板: {json.dumps(dashboard, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())

