"""
Phase 3: Analytics Service
Real-time historical data tracking, trend analysis, and anomaly detection
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics
import math

from models.analytics_models import (
    AnalyticsDataPoint, TrendAnalysis, TrendDirection,
    AnomalyDetection, AnomalyType, PredictiveAlert,
    AlertSeverity, AnalyticsDashboard
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class AnalyticsService:
    """Service for tracking historical metrics and generating analytics"""

    def __init__(self, db=None):
        """Initialize analytics service with in-memory data storage and optional DB backend"""
        self.data_points: List[AnalyticsDataPoint] = []
        self.anomalies: List[AnomalyDetection] = []
        self.alerts: List[PredictiveAlert] = []
        self.metrics_baseline: Dict[str, float] = {}  # Baseline values for comparison
        self.db = db  # Optional DatabaseEngine for persistence

    def track_metric(self, metric_name: str, value: float, region: Optional[str] = None,
                     tags: Optional[Dict[str, str]] = None, source: str = "system") -> AnalyticsDataPoint:
        """Record a metric data point"""
        data_point = AnalyticsDataPoint(
            timestamp=utc_now_iso(),
            metric_name=metric_name,
            value=value,
            region=region,
            tags=tags or {},
            source=source,
        )
        self.data_points.append(data_point)
        
        # Persist to database if available
        if self.db:
            event_id = f"{metric_name}_{utc_now_iso()}"
            self.db.save_metric(event_id, source, metric_name, value, {"region": region, **tags} if tags else {})
        
        return data_point

    def has_recent_metric(self, metric_name: str, source: str, minutes: int = 10) -> bool:
        """Avoid duplicate ingestion of the same metric from the same source."""
        cutoff = utc_now() - timedelta(minutes=minutes)
        return any(
            dp.metric_name == metric_name and dp.source == source and parse_utc_datetime(dp.timestamp) >= cutoff
            for dp in self.data_points
        )

    def ingest_data_feeds(self, summary: Optional[Dict[str, Any]] = None, logs: Optional[List[Dict[str, Any]]] = None):
        """Ingest summary and log feed metrics into the analytics service."""
        if summary:
            if not self.has_recent_metric("batch_total_emails", "batch_summary"):
                self.track_metric("batch_total_emails", float(summary.get("total_emails", 0)), source="batch_summary")
            if not self.has_recent_metric("successful_delivery_rate", "batch_summary"):
                total_emails = float(summary.get("total_emails", 0))
                success = float(summary.get("successful_deliveries", 0))
                rate = (success / total_emails * 100) if total_emails else 0.0
                self.track_metric("successful_delivery_rate", rate, source="batch_summary")
            if not self.has_recent_metric("failed_delivery_count", "batch_summary"):
                self.track_metric("failed_delivery_count", float(summary.get("failed_deliveries", 0)), source="batch_summary")

        if logs:
            total = len(logs)
            failed = sum(1 for entry in logs if entry.get("delivery_status", "").upper() != "SUCCESS")
            success = total - failed
            if not self.has_recent_metric("delivery_success_rate", "delivery_logs"):
                success_rate = (success / total * 100) if total else 0.0
                self.track_metric("delivery_success_rate", success_rate, source="delivery_logs")
            if not self.has_recent_metric("delivery_failure_rate", "delivery_logs"):
                failure_rate = (failed / total * 100) if total else 0.0
                self.track_metric("delivery_failure_rate", failure_rate, source="delivery_logs")
            if not self.has_recent_metric("delivery_failure_count", "delivery_logs"):
                self.track_metric("delivery_failure_count", float(failed), source="delivery_logs")

    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[AnalyticsDataPoint]:
        """Get historical data for a metric in last N hours"""
        cutoff_time = utc_now() - timedelta(hours=hours)
        filtered = [
            dp for dp in self.data_points
            if dp.metric_name == metric_name and
               parse_utc_datetime(dp.timestamp) >= cutoff_time
        ]
        return sorted(filtered, key=lambda x: x.timestamp)

    def analyze_trend(self, metric_name: str, hours: int = 24) -> Optional[TrendAnalysis]:
        """Analyze trend for metric over specified time period"""
        history = self.get_metric_history(metric_name, hours)
        if len(history) < 2:
            return None

        values = [dp.value for dp in history]
        timestamps = [parse_utc_datetime(dp.timestamp) for dp in history]

        # Calculate basic statistics
        current_value = values[-1]
        min_value = min(values)
        max_value = max(values)
        mean_value = statistics.mean(values)
        data_points_count = len(values)

        # Calculate moving averages
        ma_short = statistics.mean(values[-4:]) if len(values) >= 4 else mean_value
        ma_long = statistics.mean(values[-20:]) if len(values) >= 20 else mean_value

        # Calculate velocity (rate of change per hour)
        time_span_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        if time_span_hours > 0:
            velocity = (current_value - values[0]) / time_span_hours
        else:
            velocity = 0

        # Determine trend direction
        if abs(velocity) < 0.01:  # Threshold for "stable"
            direction = TrendDirection.STABLE
            confidence = 75.0
        elif velocity > 0:
            direction = TrendDirection.UPWARD
            confidence = min(95.0, 50.0 + abs(velocity) * 10)
        else:
            direction = TrendDirection.DOWNWARD
            confidence = min(95.0, 50.0 + abs(velocity) * 10)

        # Simple linear forecast for next 24 hours
        forecast_next_24h = current_value + (velocity * 24)
        forecast_accuracy = min(95.0, 60.0 + (data_points_count / 50.0 * 35.0))  # More data = higher accuracy

        return TrendAnalysis(
            metric_name=metric_name,
            time_period_hours=hours,
            direction=direction,
            velocity=velocity,
            moving_average_short=ma_short,
            moving_average_long=ma_long,
            current_value=current_value,
            min_value=min_value,
            max_value=max_value,
            data_points_count=data_points_count,
            confidence_score=confidence,
            forecast_next_24h=forecast_next_24h,
            forecast_accuracy=forecast_accuracy,
        )

    def detect_anomalies(self, metric_name: str, hours: int = 24,
                        threshold_std_dev: float = 2.5) -> List[AnomalyDetection]:
        """Detect anomalies using statistical methods"""
        history = self.get_metric_history(metric_name, hours)
        if len(history) < 3:
            return []

        values = [dp.value for dp in history]
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        anomalies_found = []

        for i, dp in enumerate(history):
            value = dp.value
            # Z-score calculation
            z_score = abs((value - mean_value) / std_dev) if std_dev > 0 else 0

            if z_score >= threshold_std_dev:
                # Classify anomaly type
                if i > 0 and i < len(history) - 1:
                    prev_val = values[i - 1]
                    next_val = values[i + 1]
                    if value > prev_val and value > next_val:
                        anomaly_type = AnomalyType.SPIKE
                    elif value < prev_val and value < next_val:
                        anomaly_type = AnomalyType.DIP
                    else:
                        anomaly_type = AnomalyType.SUDDEN_CHANGE
                else:
                    anomaly_type = AnomalyType.OUTLIER

                deviation = ((value - mean_value) / mean_value * 100) if mean_value != 0 else 0
                severity = min(100.0, z_score * 15)  # Scale z-score to 0-100

                anomaly = AnomalyDetection(
                    metric_name=metric_name,
                    timestamp=dp.timestamp,
                    anomaly_type=anomaly_type,
                    value=value,
                    expected_value=mean_value,
                    deviation_percent=deviation,
                    severity_score=severity,
                    description=f"{anomaly_type.value.replace('_', ' ').title()}: {value:.2f} vs expected {mean_value:.2f}",
                    impact=f"Deviation of {abs(deviation):.1f}% from baseline",
                    recommendation=f"Investigate {metric_name} spike at {dp.timestamp}",
                )
                anomalies_found.append(anomaly)
                self.anomalies.append(anomaly)
                
                # Persist to database if available
                if self.db:
                    anomaly_id = f"{metric_name}_{dp.timestamp}_{anomaly_type.value}"
                    self.db.save_anomaly(
                        anomaly_id, metric_name, anomaly_type.value, value, 
                        mean_value, deviation, severity, anomaly.description
                    )

        return anomalies_found

    def generate_predictive_alerts(self, metric_name: str, hours: int = 24) -> List[PredictiveAlert]:
        """Generate predictive alerts based on trend analysis"""
        trend = self.analyze_trend(metric_name, hours)
        if not trend:
            return []

        alerts_generated = []

        # Alert 1: Predicted degradation
        if trend.direction == TrendDirection.DOWNWARD and trend.velocity < -0.5:
            alert = PredictiveAlert(
                alert_id=f"alert_{metric_name}_degradation_{utc_now_iso()}",
                metric_name=metric_name,
                alert_type="predicted_issue",
                severity=AlertSeverity.WARNING,
                predicted_event=f"{metric_name} continuing downward trend",
                probability_percent=min(95.0, trend.confidence_score),
                time_to_event_hours=12,
                estimated_timestamp=(utc_now() + timedelta(hours=12)).isoformat(),
                recommended_actions=[
                    f"Monitor {metric_name} closely",
                    "Consider preventive measures",
                    "Review recent changes to system",
                ],
                affected_goals=["Email Delivery Excellence", "Operational Efficiency"],
                confidence_level=trend.forecast_accuracy,
            )
            alerts_generated.append(alert)

        # Alert 2: Predicted improvement opportunity
        if trend.direction == TrendDirection.UPWARD and trend.velocity > 0.5:
            alert = PredictiveAlert(
                alert_id=f"alert_{metric_name}_opportunity_{utc_now_iso()}",
                metric_name=metric_name,
                alert_type="opportunity",
                severity=AlertSeverity.INFO,
                predicted_event=f"{metric_name} showing positive momentum",
                probability_percent=min(95.0, trend.confidence_score),
                time_to_event_hours=24,
                estimated_timestamp=(utc_now() + timedelta(hours=24)).isoformat(),
                recommended_actions=[
                    f"Capitalize on {metric_name} improvements",
                    "Scale successful initiatives",
                    "Document best practices",
                ],
                affected_goals=["Regulatory Compliance", "Subscriber Engagement"],
                confidence_level=trend.forecast_accuracy,
            )
            alerts_generated.append(alert)

        # Alert 3: Critical threshold breach forecast
        if trend.forecast_next_24h < 20.0 and "delivery" in metric_name.lower():
            alert = PredictiveAlert(
                alert_id=f"alert_{metric_name}_critical_{utc_now_iso()}",
                metric_name=metric_name,
                alert_type="predicted_issue",
                severity=AlertSeverity.CRITICAL,
                predicted_event="Predicted critical metric threshold breach",
                probability_percent=min(85.0, trend.forecast_accuracy * 0.9),
                time_to_event_hours=24,
                estimated_timestamp=(utc_now() + timedelta(hours=24)).isoformat(),
                recommended_actions=[
                    "Immediate escalation required",
                    "Activate contingency procedures",
                    "Notify stakeholders",
                    "Review SLA commitments",
                ],
                affected_goals=["Email Delivery Excellence"],
                confidence_level=trend.forecast_accuracy,
            )
            alerts_generated.append(alert)

        # Persist alerts to database
        for alert in alerts_generated:
            if self.db:
                self.db.save_alert(
                    alert.alert_id, alert.predicted_event, 
                    alert.probability_percent / 100.0, threshold=20.0
                )

        self.alerts.extend(alerts_generated)
        return alerts_generated

    def build_analytics_dashboard(self, metrics_to_analyze: List[str]) -> AnalyticsDashboard:
        """Build comprehensive analytics dashboard"""
        # Refresh stored alerts and anomalies for the current dashboard view.
        self.anomalies = []
        self.alerts = []
        trends = []
        all_anomalies = []
        all_alerts = []
        insights = []

        for metric in metrics_to_analyze:
            # Generate trend analysis
            trend = self.analyze_trend(metric, hours=24)
            if trend:
                trends.append(trend)

            # Detect anomalies
            anomalies = self.detect_anomalies(metric, hours=24)
            all_anomalies.extend(anomalies)

            # Generate alerts
            alerts = self.generate_predictive_alerts(metric)
            all_alerts.extend(alerts)

        # Generate key insights
        if trends:
            uptrends = [t for t in trends if t.direction == TrendDirection.UPWARD]
            downtrends = [t for t in trends if t.direction == TrendDirection.DOWNWARD]
            if uptrends:
                insights.append(f"Positive momentum: {len(uptrends)} metric(s) showing upward trends")
            if downtrends:
                insights.append(f"⚠️  Watch these: {len(downtrends)} metric(s) showing downward trends")

        if all_anomalies:
            critical = [a for a in all_anomalies if a.severity_score > 70]
            insights.append(f"Anomalies detected: {len(all_anomalies)} total ({len(critical)} high-severity)")

        if all_alerts:
            critical_alerts = [a for a in all_alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                insights.append(f"🚨 CRITICAL: {len(critical_alerts)} critical alert(s) require immediate attention")

        dashboard = AnalyticsDashboard(
            generated_at=utc_now_iso(),
            metrics_tracked=len(metrics_to_analyze),
            data_points_total=len(self.data_points),
            trends_analysis=trends,
            anomalies_detected=all_anomalies[-10:] if all_anomalies else [],  # Last 10
            alerts_active=[a for a in all_alerts if a.severity == AlertSeverity.CRITICAL],  # Only critical
            key_insights=insights,
        )

        return dashboard

    def clear_old_data(self, hours_retention: int = 168) -> int:
        """Clear data older than retention period (default 7 days)"""
        cutoff_time = utc_now() - timedelta(hours=hours_retention)
        initial_count = len(self.data_points)
        self.data_points = [
            dp for dp in self.data_points
            if parse_utc_datetime(dp.timestamp) >= cutoff_time
        ]
        removed_count = initial_count - len(self.data_points)
        return removed_count

    def get_summary(self) -> Dict[str, Any]:
        """Get analytics service summary"""
        return {
            "data_points_stored": len(self.data_points),
            "anomalies_detected": len(self.anomalies),
            "alerts_generated": len(self.alerts),
            "unique_metrics": len(set(dp.metric_name for dp in self.data_points)),
            "time_range": {
                "oldest": self.data_points[0].timestamp if self.data_points else None,
                "newest": self.data_points[-1].timestamp if self.data_points else None,
            }
        }
