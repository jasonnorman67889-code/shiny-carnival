"""
Database Persistence Engine
SQLite-backed storage for canonical metrics and alert events
"""

import sqlite3
from datetime import datetime
import json
from typing import List, Dict, Any, Optional


class DatabaseEngine:
    """Persistent storage for metrics and alerts"""

    def __init__(self, db_path: str = "analytics_platform.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Get a SQLite connection with row factory enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enables column access by name
        return conn

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Canonical Metrics Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_feed TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT
                )
            """)
            # 2. Predicted Alerts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    predicted_event TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    anomaly_threshold_crossed REAL NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            # 3. Anomalies Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    anomaly_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    expected_value REAL NOT NULL,
                    deviation_percent REAL NOT NULL,
                    severity_score REAL NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_metric(self, event_id: str, source_feed: str, metric_name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Save a canonical metric event"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, datetime.utcnow().isoformat(), source_feed, metric_name, value, json.dumps(metadata or {}))
            )
            conn.commit()

    def save_alert(self, alert_id: str, predicted_event: str, confidence: float, threshold: float, status: str = "active"):
        """Save a predicted alert event"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO alerts VALUES (?, ?, ?, ?, ?, ?)",
                (alert_id, datetime.utcnow().isoformat(), predicted_event, confidence, threshold, status)
            )
            conn.commit()

    def save_anomaly(self, anomaly_id: str, metric_name: str, anomaly_type: str, value: float, 
                    expected_value: float, deviation_percent: float, severity_score: float, description: str):
        """Save an anomaly detection event"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO anomalies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (anomaly_id, datetime.utcnow().isoformat(), metric_name, anomaly_type, value, 
                 expected_value, deviation_percent, severity_score, description)
            )
            conn.commit()

    def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve active alerts ordered by most recent"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts WHERE status = 'active' ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_anomalies(self, metric_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent anomalies, optionally filtered by metric"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if metric_name:
                cursor.execute("SELECT * FROM anomalies WHERE metric_name = ? ORDER BY timestamp DESC LIMIT ?", 
                             (metric_name, limit))
            else:
                cursor.execute("SELECT * FROM anomalies ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_metric_history(self, metric_name: str, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve metric history for a specific metric in last N hours"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE metric_name = ? 
                AND datetime(timestamp) >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp ASC LIMIT ?
            """, (metric_name, hours, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics about stored metrics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM metrics")
            total_metrics = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM alerts WHERE status = 'active'")
            active_alerts = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM anomalies")
            total_anomalies = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(DISTINCT metric_name) as metric_count FROM metrics")
            unique_metrics = cursor.fetchone()["metric_count"]
            
            cursor.execute("SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM metrics")
            row = cursor.fetchone()
            time_range = {"oldest": row["oldest"], "newest": row["newest"]} if row["oldest"] else None
            
            return {
                "data_points_stored": total_metrics,
                "active_alerts": active_alerts,
                "anomalies_detected": total_anomalies,
                "unique_metrics": unique_metrics,
                "time_range": time_range
            }

    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        with self._get_connection() as conn:
            conn.execute("UPDATE alerts SET status = 'resolved' WHERE alert_id = ?", (alert_id,))
            conn.commit()

    def clear_old_data(self, hours_retention: int = 168) -> int:
        """Clear data older than retention period (default 7 days)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM metrics 
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' hours')
            """, (hours_retention,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
