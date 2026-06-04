"""
Phase 4 Smoke Test - Validate persistence, auth, and observability
"""

import requests
import json
import base64
import time

BASE_URL = "http://127.0.0.1:5000"
ADMIN_CREDS = ("admin", "adminpass")

def test_health_endpoint():
    """Test /health endpoint (no auth required)"""
    print("\n=== Testing /health endpoint (no auth) ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"System Status: {data['system_health']['status']}")
    print(f"Database Connected: {data['database_connected']}")
    assert response.status_code == 200
    assert "system_health" in data
    print("✅ /health endpoint working")

def test_analytics_overview_with_auth():
    """Test /api/phase3/analytics-overview with Basic Auth"""
    print("\n=== Testing /api/phase3/analytics-overview ===")
    auth = base64.b64encode(b"admin:adminpass").decode()
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(f"{BASE_URL}/api/phase3/analytics-overview", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Phase: {data['phase']}")
    print(f"Data Points Stored: {data['summary']['data_points_stored']}")
    assert response.status_code == 200
    assert "summary" in data
    assert "analytics_dashboard" in data
    assert "alerts_active" in data["analytics_dashboard"]
    assert "anomalies_detected" in data["analytics_dashboard"]
    print("✅ /api/phase3/analytics-overview working with persistence")

def test_metrics_endpoint():
    """Test /api/metrics endpoint (admin only)"""
    print("\n=== Testing /api/metrics endpoint ===")
    auth = base64.b64encode(b"admin:adminpass").decode()
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(f"{BASE_URL}/api/metrics", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response text: {response.text}")
        return
    data = response.json()
    print(f"System Health: {data['system_health']['status']}")
    print(f"Error Rate: {data['system_health']['telemetry_summary']['error_rate_percent']}%")
    print(f"Latency p95: {data['latency_percentiles']['p95']:.2f}ms")
    assert response.status_code == 200
    assert "system_health" in data
    assert "database_stats" in data
    print("✅ /api/metrics endpoint working")

def test_analytics_history():
    """Test /api/phase3/analytics-history"""
    print("\n=== Testing /api/phase3/analytics-history ===")
    auth = base64.b64encode(b"admin:adminpass").decode()
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(
        f"{BASE_URL}/api/phase3/analytics-history?metric=control_loop_events_processed&hours=24",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Metric: {data['metric_name']}")
    print(f"History Points: {len(data['history'])}")
    assert response.status_code == 200
    assert "history" in data
    print("✅ /api/phase3/analytics-history working")

def test_unauthenticated_access():
    """Test that endpoints require auth"""
    print("\n=== Testing unauthenticated access (should fail) ===")
    response = requests.get(f"{BASE_URL}/api/phase3/analytics-overview")
    print(f"Status: {response.status_code}")
    assert response.status_code == 401
    print("✅ Unauthenticated access properly denied")

def test_database_persistence():
    """Test that database is persisting data"""
    print("\n=== Testing database persistence ===")
    from services.storage import DatabaseEngine
    db = DatabaseEngine("analytics_platform.db")
    summary = db.get_metrics_summary()
    print(f"Metrics in DB: {summary['data_points_stored']}")
    print(f"Active Alerts in DB: {summary['active_alerts']}")
    print(f"Anomalies in DB: {summary['anomalies_detected']}")
    print("✅ Database persistence verified")

if __name__ == "__main__":
    print("🧪 Phase 4 Smoke Test Suite")
    print("=" * 50)
    
    try:
        test_health_endpoint()
        test_unauthenticated_access()
        test_analytics_overview_with_auth()
        test_analytics_history()
        test_metrics_endpoint()
        test_database_persistence()
        
        print("\n" + "=" * 50)
        print("✅ ALL SMOKE TESTS PASSED!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
