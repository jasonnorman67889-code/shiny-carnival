"""
Analytics Service V1 - Decoupled aggregation logic with caching
Serves as the primary analytics API layer behind versioned routes
"""

from typing import List, Dict, Any, Optional
import time
from services.storage import DatabaseEngine


class AnalyticsServiceV1:
    """Decoupled analytics service with DB abstraction and caching"""

    def __init__(self, db: DatabaseEngine):
        self.db = db
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 30  # 30-second cache for expensive endpoints

    def _is_cache_fresh(self, cache_key: str) -> bool:
        """Check if a cache entry is still fresh"""
        if cache_key not in self._cache:
            return False
        entry = self._cache[cache_key]
        return time.time() - entry["timestamp"] < self._cache_ttl

    def get_cached_analytics_overview(self) -> Dict[str, Any]:
        """Get analytics overview with caching for expensive operations"""
        cache_key = "analytics_overview"
        
        if self._is_cache_fresh(cache_key):
            return self._cache[cache_key]["data"]
        
        # Cache miss - compute expensive query
        data = self._compute_analytics_overview()
        self._cache[cache_key] = {"timestamp": time.time(), "data": data}
        return data

    def _compute_analytics_overview(self) -> Dict[str, Any]:
        """Compute analytics overview from database"""
        summary = self.db.get_metrics_summary()
        active_alerts = self.db.get_active_alerts(limit=10)
        recent_anomalies = self.db.get_recent_anomalies(limit=10)
        
        return {
            "phase": "Phase 3: Visualization Layer",
            "timestamp": time.time(),
            "summary": summary,
            "alerts": [dict(a) for a in active_alerts],
            "anomalies": [dict(a) for a in recent_anomalies]
        }

    def get_metric_history(self, metric_name: str, hours: int = 72) -> List[Dict[str, Any]]:
        """Get historical metric data"""
        cache_key = f"metric_history:{metric_name}:{hours}"
        
        if self._is_cache_fresh(cache_key):
            return self._cache[cache_key]["data"]
        
        history = self.db.get_metric_history(metric_name, hours)
        self._cache[cache_key] = {"timestamp": time.time(), "data": history}
        return history

    def get_active_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get active alerts"""
        cache_key = f"active_alerts:{limit}"
        
        if self._is_cache_fresh(cache_key):
            return self._cache[cache_key]["data"]
        
        alerts = self.db.get_active_alerts(limit)
        self._cache[cache_key] = {"timestamp": time.time(), "data": alerts}
        return alerts

    def get_anomalies(self, metric_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        cache_key = f"anomalies:{metric_name}:{limit}"
        
        if self._is_cache_fresh(cache_key):
            return self._cache[cache_key]["data"]
        
        anomalies = self.db.get_recent_anomalies(metric_name, limit)
        self._cache[cache_key] = {"timestamp": time.time(), "data": anomalies}
        return anomalies

    def clear_cache(self, cache_key: Optional[str] = None):
        """Clear cache entries"""
        if cache_key:
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()
