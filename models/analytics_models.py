"""
Phase 3: Visualization Layer
Data models for advanced analytics, historical trend tracking, and predictive analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TrendDirection(Enum):
    """Trend direction indicators"""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"


class AnomalyType(Enum):
    """Types of anomalies detected"""
    SPIKE = "spike"
    DIP = "dip"
    SUDDEN_CHANGE = "sudden_change"
    TREND_REVERSAL = "trend_reversal"
    OUTLIER = "outlier"


class AlertSeverity(Enum):
    """Alert severity levels for predictions"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AnalyticsDataPoint:
    """Time-series data point for metrics tracking"""
    timestamp: str  # ISO format: 2026-06-01T12:30:00
    metric_name: str  # e.g., "delivery_success_rate", "cycles_executed"
    value: float  # Numeric value
    region: Optional[str] = None  # Optional region for regional analytics
    tags: Dict[str, str] = field(default_factory=dict)  # Contextual tags
    source: str = "system"  # Data source identifier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "metric_name": self.metric_name,
            "value": self.value,
            "region": self.region,
            "tags": self.tags,
            "source": self.source,
        }


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric over time period"""
    metric_name: str
    time_period_hours: int  # Analysis period (e.g., 24, 72, 168)
    direction: TrendDirection  # Upward/downward/stable
    velocity: float  # Rate of change per hour
    moving_average_short: float  # 4-point moving average
    moving_average_long: float  # 20-point moving average
    current_value: float  # Latest value
    min_value: float  # Min in period
    max_value: float  # Max in period
    data_points_count: int  # Number of data points analyzed
    confidence_score: float  # 0-100, trend confidence
    forecast_next_24h: float  # Predicted value in 24 hours
    forecast_accuracy: float  # 0-100, forecast accuracy estimate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_name": self.metric_name,
            "time_period_hours": self.time_period_hours,
            "direction": self.direction.value,
            "velocity": round(self.velocity, 4),
            "moving_average_short": round(self.moving_average_short, 2),
            "moving_average_long": round(self.moving_average_long, 2),
            "current_value": round(self.current_value, 2),
            "min_value": round(self.min_value, 2),
            "max_value": round(self.max_value, 2),
            "data_points_count": self.data_points_count,
            "confidence_score": round(self.confidence_score, 1),
            "forecast_next_24h": round(self.forecast_next_24h, 2),
            "forecast_accuracy": round(self.forecast_accuracy, 1),
        }


@dataclass
class AnomalyDetection:
    """Detected anomaly in metric data"""
    metric_name: str
    timestamp: str  # When detected
    anomaly_type: AnomalyType
    value: float  # Anomalous value
    expected_value: float  # Expected value based on trend
    deviation_percent: float  # Deviation from expected (%)
    severity_score: float  # 0-100, how severe the anomaly
    description: str  # Human-readable description
    impact: str  # Potential impact
    recommendation: str  # Recommended action

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp,
            "anomaly_type": self.anomaly_type.value,
            "value": round(self.value, 2),
            "expected_value": round(self.expected_value, 2),
            "deviation_percent": round(self.deviation_percent, 1),
            "severity_score": round(self.severity_score, 1),
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
        }


@dataclass
class PredictiveAlert:
    """Predicted issue/opportunity alert"""
    alert_id: str  # Unique identifier
    metric_name: str
    alert_type: str  # "predicted_issue" or "opportunity"
    severity: AlertSeverity
    predicted_event: str  # What is predicted to happen
    probability_percent: float  # 0-100, likelihood
    time_to_event_hours: int  # Hours until predicted event
    estimated_timestamp: str  # ISO format when event predicted
    recommended_actions: List[str]  # Suggested actions
    affected_goals: List[str]  # Which strategic goals affected
    confidence_level: float  # 0-100, confidence in prediction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "metric_name": self.metric_name,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "predicted_event": self.predicted_event,
            "probability_percent": round(self.probability_percent, 1),
            "time_to_event_hours": self.time_to_event_hours,
            "estimated_timestamp": self.estimated_timestamp,
            "recommended_actions": self.recommended_actions,
            "affected_goals": self.affected_goals,
            "confidence_level": round(self.confidence_level, 1),
        }


@dataclass
class AnalyticsDashboard:
    """Aggregated analytics dashboard"""
    generated_at: str  # ISO format timestamp
    metrics_tracked: int  # Number of unique metrics
    data_points_total: int  # Total historical data points
    trends_analysis: List[TrendAnalysis] = field(default_factory=list)
    anomalies_detected: List[AnomalyDetection] = field(default_factory=list)
    alerts_active: List[PredictiveAlert] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "generated_at": self.generated_at,
            "metrics_tracked": self.metrics_tracked,
            "data_points_total": self.data_points_total,
            "trends_analysis": [t.to_dict() for t in self.trends_analysis],
            "anomalies_detected": [a.to_dict() for a in self.anomalies_detected],
            "alerts_active": [al.to_dict() for al in self.alerts_active],
            "key_insights": self.key_insights,
            "summary": {
                "trends_count": len(self.trends_analysis),
                "anomalies_count": len(self.anomalies_detected),
                "alerts_count": len(self.alerts_active),
                "critical_alerts": sum(1 for a in self.alerts_active if a.severity == AlertSeverity.CRITICAL),
            }
        }
