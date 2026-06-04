import base64
import os
import sys
import pytest
from datetime import timedelta

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dashboard import app, analytics_service, control_loop_service


def auth_header(username='admin', password='adminpass'):
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {'Authorization': f'Basic {credentials}'}


@pytest.fixture(autouse=True)
def reset_services():
    analytics_service.data_points = []
    analytics_service.anomalies = []
    analytics_service.alerts = []
    control_loop_service.workflows = {}
    control_loop_service.event_queue = []
    control_loop_service.cycles = []
    control_loop_service.last_cycle_number = 0
    control_loop_service.control_loop_active = False
    control_loop_service.total_cycles_executed = 0
    control_loop_service.total_events_processed = 0
    control_loop_service.total_workflows_triggered = 0
    yield
    analytics_service.data_points = []
    analytics_service.anomalies = []
    analytics_service.alerts = []
    control_loop_service.workflows = {}
    control_loop_service.event_queue = []
    control_loop_service.cycles = []
    control_loop_service.last_cycle_number = 0
    control_loop_service.control_loop_active = False
    control_loop_service.total_cycles_executed = 0
    control_loop_service.total_events_processed = 0
    control_loop_service.total_workflows_triggered = 0


def test_track_metric_and_get_history():
    analytics_service.track_metric('test_metric', 12)
    analytics_service.track_metric('test_metric', 18)
    history = analytics_service.get_metric_history('test_metric', hours=24)

    assert len(history) >= 2
    assert history[0].metric_name == 'test_metric'
    assert history[0].value == 12
    assert history[1].value == 18


def test_analyze_trend_requires_multiple_points():
    analytics_service.track_metric('trend_metric', 15)
    trend = analytics_service.analyze_trend('trend_metric', hours=24)
    assert trend is None


def test_analyze_trend_returns_upward_direction():
    for value in [10, 20, 35, 55, 80, 110]:
        analytics_service.track_metric('trend_metric', value)

    trend = analytics_service.analyze_trend('trend_metric', hours=24)
    assert trend is not None
    assert trend.metric_name == 'trend_metric'
    assert trend.direction.name in {'UPWARD', 'STABLE'}
    assert trend.velocity >= 0


def test_detect_anomalies_spike():
    for _ in range(8):
        analytics_service.track_metric('spike_metric', 10)
    analytics_service.track_metric('spike_metric', 80)

    anomalies = analytics_service.detect_anomalies('spike_metric', hours=24)
    assert isinstance(anomalies, list)
    assert len(anomalies) >= 1
    assert anomalies[0].metric_name == 'spike_metric'
    assert anomalies[0].severity_score >= 0


def test_generate_predictive_alerts_with_higher_trend():
    for value in [50, 55, 60, 65, 70, 75]:
        analytics_service.track_metric('alert_metric', value)

    alerts = analytics_service.generate_predictive_alerts('alert_metric')
    assert isinstance(alerts, list)
    assert all(hasattr(alert, 'predicted_event') for alert in alerts) or len(alerts) == 0


def test_analytics_service_ingests_summary_and_log_feeds():
    summary = {
        'total_emails': 100,
        'successful_deliveries': 85,
        'failed_deliveries': 15
    }
    logs = [
        {'delivery_status': 'SUCCESS', 'region': 'USA'},
        {'delivery_status': 'FAILED', 'region': 'USA'},
        {'delivery_status': 'SUCCESS', 'region': 'EU'},
    ]
    analytics_service.ingest_data_feeds(summary, logs)

    metric_names = [dp.metric_name for dp in analytics_service.data_points]
    assert 'batch_total_emails' in metric_names
    assert 'successful_delivery_rate' in metric_names
    assert 'delivery_failure_rate' in metric_names


def test_build_analytics_dashboard_returns_insights():
    for value in [20, 25, 28, 31, 34, 39]:
        analytics_service.track_metric('dashboard_metric', value)

    dashboard = analytics_service.build_analytics_dashboard(['dashboard_metric'])
    assert dashboard.metrics_tracked == 1
    assert dashboard.data_points_total == len(analytics_service.data_points)
    assert isinstance(dashboard.key_insights, list)


def test_analytics_overview_endpoint_requires_admin():
    client = app.test_client()
    response = client.get('/api/phase3/analytics-overview')
    assert response.status_code == 401


def test_analytics_overview_endpoint_returns_data_for_admin():
    client = app.test_client()
    response = client.get('/api/phase3/analytics-overview', headers=auth_header())
    assert response.status_code == 200
    data = response.get_json()
    assert data['phase'] == 'Phase 3: Visualization Layer'
    assert 'analytics_dashboard' in data
    assert 'summary' in data
    assert isinstance(data['summary'].get('data_points_stored'), int)


def test_analytics_history_endpoint_returns_structure():
    client = app.test_client()
    response = client.get('/api/phase3/analytics-history?metric=test_metric&hours=24', headers=auth_header())
    assert response.status_code == 200
    data = response.get_json()
    assert data['metric_name'] == 'test_metric'
    assert isinstance(data['history'], list)


def test_login_page_renders():
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Sign in' in response.data


def test_root_redirects_to_login_when_unauthenticated():
    client = app.test_client()
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_root_redirects_to_dashboard_when_authenticated():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'role': 'admin'}
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']


def test_login_get_redirects_to_dashboard_when_authenticated():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'viewer', 'role': 'viewer'}
    response = client.get('/login', follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']


def test_login_post_sets_session_and_role():
    client = app.test_client()
    response = client.post('/login', data={'username': 'admin', 'password': 'adminpass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email Automation Dashboard' in response.data

    role_response = client.get('/role')
    assert role_response.status_code == 200
    role_data = role_response.get_json()
    assert role_data['role'] == 'admin'
    assert role_data['username'] == 'admin'


def test_role_endpoint_requires_authentication():
    client = app.test_client()
    response = client.get('/role')
    assert response.status_code == 401


def test_control_loop_status_endpoint_initial_state():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'role': 'admin'}

    response = client.get('/api/phase2/control-loop-status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['phase'] == 'Phase 2: Control Loop & Gateway'
    status = data['control_loop_status']
    assert status['total_cycles_executed'] == 0
    assert status['total_events_processed'] == 0
    assert status['total_workflows_triggered'] == 0
    assert status['event_queue_size'] == 0
    assert status['is_active'] is False


def test_control_loop_cycle_endpoint_executes_and_increments():
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = {'username': 'admin', 'role': 'admin'}

    response = client.post('/api/phase2/control-loop-cycle')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['phase'] == 'Phase 2: Control Loop & Gateway'
    assert data['cycle']['cycle_number'] == 1

    status_response = client.get('/api/phase2/control-loop-status')
    assert status_response.status_code == 200
    status = status_response.get_json()['control_loop_status']
    assert status['total_cycles_executed'] == 1
    assert status['recent_cycles'][0]['cycle_number'] == 1
