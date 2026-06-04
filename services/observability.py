"""
Operational Observability Service
System health telemetry and performance metrics collection
"""

from typing import Dict, Any, Optional
from collections import deque
import time


class OperationalMetricsCollector:
    """Collects and aggregates operational system metrics"""

    def __init__(self, max_history: int = 1000):
        """Initialize metrics collector"""
        self.max_history = max_history
        self.ingestion_rates: deque = deque(maxlen=max_history)  # events/sec
        self.processing_latencies: deque = deque(maxlen=max_history)  # ms
        self.alert_counts: deque = deque(maxlen=max_history)  # alerts per window
        self.anomaly_counts: deque = deque(maxlen=max_history)  # anomalies per window
        self.request_counts: deque = deque(maxlen=max_history)  # requests per window
        self.error_counts: deque = deque(maxlen=max_history)  # errors per window
        self.start_time = time.time()

    def record_ingestion_event(self, count: int = 1):
        """Record metric ingestion"""
        self.ingestion_rates.append({"timestamp": time.time(), "count": count})

    def record_processing_latency(self, latency_ms: float):
        """Record processing latency in milliseconds"""
        self.processing_latencies.append({"timestamp": time.time(), "latency_ms": latency_ms})

    def record_alert(self, alert_count: int = 1):
        """Record alert generation"""
        self.alert_counts.append({"timestamp": time.time(), "count": alert_count})

    def record_anomaly(self, anomaly_count: int = 1):
        """Record anomaly detection"""
        self.anomaly_counts.append({"timestamp": time.time(), "count": anomaly_count})

    def record_request(self, request_count: int = 1, is_error: bool = False):
        """Record API request"""
        self.request_counts.append({"timestamp": time.time(), "count": request_count})
        if is_error:
            self.error_counts.append({"timestamp": time.time(), "count": 1})

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        uptime_seconds = time.time() - self.start_time

        # Calculate averages
        avg_latency_ms = 0
        if self.processing_latencies:
            latencies = [item["latency_ms"] for item in self.processing_latencies]
            avg_latency_ms = sum(latencies) / len(latencies)

        ingestion_rate = 0
        if self.ingestion_rates:
            ingestion_rate = sum(item["count"] for item in self.ingestion_rates)

        total_alerts = sum(item["count"] for item in self.alert_counts)
        total_anomalies = sum(item["count"] for item in self.anomaly_counts)
        total_requests = sum(item["count"] for item in self.request_counts)
        total_errors = sum(item["count"] for item in self.error_counts)

        error_rate_percent = 0
        if total_requests > 0:
            error_rate_percent = (total_errors / total_requests) * 100

        return {
            "status": "healthy" if error_rate_percent < 5 else "degraded" if error_rate_percent < 20 else "critical",
            "timestamp": time.time(),
            "uptime_seconds": uptime_seconds,
            "telemetry_summary": {
                "ingestion_events_total": ingestion_rate,
                "avg_processing_latency_ms": round(avg_latency_ms, 2),
                "alerts_generated": total_alerts,
                "anomalies_detected": total_anomalies,
                "api_requests_total": total_requests,
                "api_errors_total": total_errors,
                "error_rate_percent": round(error_rate_percent, 2),
            }
        }

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Get latency percentiles (p50, p95, p99)"""
        if not self.processing_latencies:
            return {"p50": 0, "p95": 0, "p99": 0}

        latencies = sorted([item["latency_ms"] for item in self.processing_latencies])
        n = len(latencies)

        return {
            "p50": latencies[int(n * 0.50)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)],
        }

    def reset(self):
        """Reset all metrics"""
        self.ingestion_rates.clear()
        self.processing_latencies.clear()
        self.alert_counts.clear()
        self.anomaly_counts.clear()
        self.request_counts.clear()
        self.error_counts.clear()
        self.start_time = time.time()
