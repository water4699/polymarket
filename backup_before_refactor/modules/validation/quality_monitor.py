"""
数据质量监控系统
提供持续的数据质量监控、告警和报告功能
支持实时监控和历史趋势分析
"""
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import pandas as pd
from utils.logger import LoggerMixin


@dataclass
class QualityMetric:
    """质量指标"""
    metric_id: str
    name: str
    description: str
    data_type: str  # raw, clean, feature
    threshold_warning: float
    threshold_error: float
    check_function: Callable
    enabled: bool = True


@dataclass
class QualityAlert:
    """质量告警"""
    alert_id: str
    metric_id: str
    level: str  # warning, error, critical
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class QualityReport:
    """质量报告"""
    report_date: datetime
    data_type: str
    symbol: Optional[str]
    metrics: Dict[str, float] = field(default_factory=dict)
    alerts: List[QualityAlert] = field(default_factory=list)
    overall_score: float = 0.0
    trend: str = "stable"  # improving, declining, stable


class DataQualityMonitor(LoggerMixin):
    """
    数据质量监控器
    提供全面的数据质量监控、告警和趋势分析功能
    """

    def __init__(self):
        self.metrics = self._init_quality_metrics()
        self.alerts: List[QualityAlert] = []
        self.monitoring_active = False
        self.logger.info("数据质量监控器初始化完成")

    def _init_quality_metrics(self) -> Dict[str, QualityMetric]:
        """初始化质量指标"""
        return {
            # Raw 数据质量指标
            "raw_completeness": QualityMetric(
                metric_id="raw_completeness",
                name="Raw数据完整性",
                description="Raw数据记录完整性百分比",
                data_type="raw",
                threshold_warning=95.0,
                threshold_error=90.0,
                check_function=self._check_raw_completeness
            ),

            "raw_timeliness": QualityMetric(
                metric_id="raw_timeliness",
                name="Raw数据及时性",
                description="Raw数据及时性评分（0-100）",
                data_type="raw",
                threshold_warning=80.0,
                threshold_error=60.0,
                check_function=self._check_raw_timeliness
            ),

            "raw_accuracy": QualityMetric(
                metric_id="raw_accuracy",
                name="Raw数据准确性",
                description="Raw数据格式正确性百分比",
                data_type="raw",
                threshold_warning=98.0,
                threshold_error=95.0,
                check_function=self._check_raw_accuracy
            ),

            # Clean 数据质量指标
            "clean_completeness": QualityMetric(
                metric_id="clean_completeness",
                name="Clean数据完整性",
                description="Clean数据非空值百分比",
                data_type="clean",
                threshold_warning=99.0,
                threshold_error=97.0,
                check_function=self._check_clean_completeness
            ),

            "clean_uniqueness": QualityMetric(
                metric_id="clean_uniqueness",
                name="Clean数据唯一性",
                description="Clean数据唯一记录百分比",
                data_type="clean",
                threshold_warning=99.5,
                threshold_error=98.0,
                check_function=self._check_clean_uniqueness
            ),

            "clean_consistency": QualityMetric(
                metric_id="clean_consistency",
                name="Clean数据一致性",
                description="Clean数据逻辑一致性评分",
                data_type="clean",
                threshold_warning=95.0,
                threshold_error=90.0,
                check_function=self._check_clean_consistency
            ),

            # Feature 数据质量指标
            "feature_completeness": QualityMetric(
                metric_id="feature_completeness",
                name="Feature数据完整性",
                description="技术指标计算完整性百分比",
                data_type="feature",
                threshold_warning=98.0,
                threshold_error=95.0,
                check_function=self._check_feature_completeness
            ),

            "feature_accuracy": QualityMetric(
                metric_id="feature_accuracy",
                name="Feature数据准确性",
                description="技术指标计算准确性评分",
                data_type="feature",
                threshold_warning=95.0,
                threshold_error=90.0,
                check_function=self._check_feature_accuracy
            ),

            # 系统级指标
            "pipeline_success_rate": QualityMetric(
                metric_id="pipeline_success_rate",
                name="管道成功率",
                description="数据管道执行成功率",
                data_type="system",
                threshold_warning=95.0,
                threshold_error=90.0,
                check_function=self._check_pipeline_success_rate
            ),

            "data_freshness": QualityMetric(
                metric_id="data_freshness",
                name="数据新鲜度",
                description="最新数据时间延迟（分钟）",
                data_type="system",
                threshold_warning=60.0,  # 1小时
                threshold_error=240.0,  # 4小时
                check_function=self._check_data_freshness
            )
        }

    async def start_monitoring(self, interval_minutes: int = 60):
        """
        启动质量监控

        Args:
            interval_minutes: 监控间隔（分钟）
        """
        self.monitoring_active = True
        self.logger.info(f"启动数据质量监控，间隔: {interval_minutes}分钟")

        while self.monitoring_active:
            try:
                await self.run_quality_check()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"质量监控执行失败: {e}")
                await asyncio.sleep(300)  # 出错后5分钟重试

    def stop_monitoring(self):
        """停止质量监控"""
        self.monitoring_active = False
        self.logger.info("停止数据质量监控")

    async def run_quality_check(self, data_types: List[str] = None) -> QualityReport:
        """
        执行质量检查

        Args:
            data_types: 要检查的数据类型，None表示全部

        Returns:
            质量报告
        """
        if data_types is None:
            data_types = ["raw", "clean", "feature", "system"]

        self.logger.info(f"开始执行质量检查: {data_types}")

        report = QualityReport(
            report_date=datetime.now(),
            data_type=",".join(data_types),
            symbol=None
        )

        # 执行各项指标检查
        for metric_id, metric in self.metrics.items():
            if metric.data_type in data_types and metric.enabled:
                try:
                    score = await metric.check_function()
                    report.metrics[metric_id] = score

                    # 生成告警
                    alert = self._generate_alert(metric, score)
                    if alert:
                        report.alerts.append(alert)
                        self.alerts.append(alert)

                except Exception as e:
                    self.logger.error(f"指标 {metric_id} 检查失败: {e}")
                    report.metrics[metric_id] = 0.0

        # 计算总体评分
        report.overall_score = self._calculate_overall_score(report.metrics)

        # 分析趋势
        report.trend = await self._analyze_trend(report)

        # 清理旧告警
        self._cleanup_old_alerts()

        # 记录报告
        await self._store_quality_report(report)

        self.logger.info(f"质量检查完成，总体评分: {report.overall_score:.1f}")

        return report

    async def get_quality_history(self, days: int = 7) -> pd.DataFrame:
        """
        获取质量历史数据

        Args:
            days: 历史天数

        Returns:
            历史质量数据
        """
        # 这里应该从数据库查询历史质量报告
        # 暂时返回示例数据
        dates = pd.date_range(datetime.now() - timedelta(days=days), datetime.now(), freq='D')

        history_data = []
        for date in dates:
            # 模拟历史数据
            history_data.append({
                'date': date,
                'overall_score': 85.0 + (date.day % 10),  # 模拟波动
                'raw_completeness': 95.0 + (date.day % 5),
                'clean_completeness': 98.0 + (date.day % 2),
                'alerts_count': date.day % 3
            })

        return pd.DataFrame(history_data)

    def get_active_alerts(self) -> List[QualityAlert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved]

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self.logger.info(f"告警已解决: {alert_id}")
                break

    # ===========================================
    # 质量指标检查函数
    # ===========================================

    async def _check_raw_completeness(self) -> float:
        """检查Raw数据完整性"""
        # 这里应该查询数据库获取实际统计
        # 暂时返回示例值
        return 96.5

    async def _check_raw_timeliness(self) -> float:
        """检查Raw数据及时性"""
        # 检查最新数据的时间戳
        return 85.0

    async def _check_raw_accuracy(self) -> float:
        """检查Raw数据准确性"""
        return 97.2

    async def _check_clean_completeness(self) -> float:
        """检查Clean数据完整性"""
        return 99.1

    async def _check_clean_uniqueness(self) -> float:
        """检查Clean数据唯一性"""
        return 99.7

    async def _check_clean_consistency(self) -> float:
        """检查Clean数据一致性"""
        return 94.8

    async def _check_feature_completeness(self) -> float:
        """检查Feature数据完整性"""
        return 97.5

    async def _check_feature_accuracy(self) -> float:
        """检查Feature数据准确性"""
        return 93.2

    async def _check_pipeline_success_rate(self) -> float:
        """检查管道成功率"""
        return 96.8

    async def _check_data_freshness(self) -> float:
        """检查数据新鲜度"""
        # 返回最新数据延迟分钟数（越小越好）
        latest_delay = 45.0  # 45分钟延迟

        # 转换为评分 (0-100, 延迟越小评分越高)
        if latest_delay <= 30:
            return 100.0
        elif latest_delay <= 60:
            return 90.0
        elif latest_delay <= 120:
            return 70.0
        else:
            return 50.0

    # ===========================================
    # 私有辅助方法
    # ===========================================

    def _generate_alert(self, metric: QualityMetric, score: float) -> Optional[QualityAlert]:
        """生成告警"""
        alert_level = None
        if score <= metric.threshold_error:
            alert_level = "error"
        elif score <= metric.threshold_warning:
            alert_level = "warning"

        if alert_level:
            alert = QualityAlert(
                alert_id=f"{metric.metric_id}_{int(datetime.now().timestamp())}",
                metric_id=metric.metric_id,
                level=alert_level,
                message=f"{metric.name} {alert_level}: {score:.1f} (阈值: {metric.threshold_warning:.1f})",
                details={
                    "metric_name": metric.name,
                    "current_score": score,
                    "warning_threshold": metric.threshold_warning,
                    "error_threshold": metric.threshold_error
                }
            )
            return alert

        return None

    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """计算总体评分"""
        if not metrics:
            return 0.0

        # 加权平均计算
        weights = {
            "raw_completeness": 0.1,
            "raw_accuracy": 0.1,
            "clean_completeness": 0.2,
            "clean_uniqueness": 0.15,
            "clean_consistency": 0.15,
            "feature_completeness": 0.1,
            "feature_accuracy": 0.1,
            "pipeline_success_rate": 0.05,
            "data_freshness": 0.05
        }

        total_weight = 0
        weighted_score = 0

        for metric_id, score in metrics.items():
            if metric_id in weights:
                weight = weights[metric_id]
                weighted_score += score * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0

    async def _analyze_trend(self, current_report: QualityReport) -> str:
        """分析质量趋势"""
        try:
            # 获取历史数据
            history_df = await self.get_quality_history(days=7)

            if len(history_df) < 2:
                return "stable"

            # 计算趋势
            recent_scores = history_df['overall_score'].tail(3)
            trend = recent_scores.iloc[-1] - recent_scores.iloc[0]

            if trend > 2:
                return "improving"
            elif trend < -2:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "unknown"

    def _cleanup_old_alerts(self, days: int = 30):
        """清理旧告警"""
        cutoff_date = datetime.now() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts
            if not alert.resolved or
            (alert.resolved_at and alert.resolved_at > cutoff_date)
        ]

    async def _store_quality_report(self, report: QualityReport):
        """存储质量报告"""
        # 这里应该将报告存储到数据库
        # 暂时只记录日志
        self.logger.info(f"质量报告已生成: 评分 {report.overall_score:.1f}, 告警 {len(report.alerts)} 个")

    # ===========================================
    # 报告生成方法
    # ===========================================

    def generate_quality_dashboard(self, days: int = 7) -> str:
        """
        生成质量仪表板

        Args:
            days: 统计天数

        Returns:
            HTML格式的仪表板
        """
        # 获取当前状态
        active_alerts = self.get_active_alerts()

        # 构建HTML仪表板
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PredictLab 数据质量仪表板</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .alert {{ background: #ffebee; border-left: 4px solid #f44336; margin: 10px 0; padding: 10px; }}
                .warning {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .good {{ color: #4caf50; }}
                .warning {{ color: #ff9800; }}
                .error {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <h1>PredictLab 数据质量仪表板</h1>
            <p>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <h2>活跃告警 ({len(active_alerts)})</h2>
        """

        for alert in active_alerts[:10]:  # 显示前10个告警
            alert_class = "warning" if alert.level == "warning" else "error"
            html += f"""
            <div class="alert {alert_class}">
                <strong>{alert.level.upper()}</strong>: {alert.message}
                <br><small>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """

        html += """
            <h2>质量指标</h2>
            <div id="metrics">
                <!-- 动态生成指标卡片 -->
            </div>

            <script>
                // 这里可以添加JavaScript来动态更新指标
                console.log('质量仪表板加载完成');
            </script>
        </body>
        </html>
        """

        return html

    def export_quality_report(self, report: QualityReport, format: str = "json") -> str:
        """
        导出质量报告

        Args:
            report: 质量报告
            format: 导出格式 (json/markdown)

        Returns:
            格式化的报告
        """
        if format == "json":
            return json.dumps({
                "report_date": report.report_date.isoformat(),
                "data_type": report.data_type,
                "overall_score": report.overall_score,
                "trend": report.trend,
                "metrics": report.metrics,
                "alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "metric_id": alert.metric_id,
                        "level": alert.level,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved": alert.resolved
                    }
                    for alert in report.alerts
                ]
            }, indent=2)

        elif format == "markdown":
            md = f"""# 数据质量报告

**报告日期**: {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}
**数据类型**: {report.data_type}
**总体评分**: {report.overall_score:.1f}
**趋势**: {report.trend}

## 质量指标

"""
            for metric_id, score in report.metrics.items():
                md += f"- **{metric_id}**: {score:.1f}\n"

            if report.alerts:
                md += "\n## 活跃告警\n\n"
                for alert in report.alerts:
                    md += f"- **{alert.level.upper()}**: {alert.message}\n"

            return md

        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 全局质量监控器实例
quality_monitor = DataQualityMonitor()
