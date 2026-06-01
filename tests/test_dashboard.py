import os
import json
import tempfile
from dashboard import load_transformation_insights, load_multiversal_simulations, load_infinite_continuity_engine, LOG_JSON_PATH

SAMPLE_LOGS = [
    {"timestamp": "2026-06-01T05:30:27", "recipient_email": "a@example.com", "delivery_status": "SUCCESS", "region": "USA"},
    {"timestamp": "2026-06-01T05:31:27", "recipient_email": "b@example.com", "delivery_status": "FAILED", "region": "EUROPE"},
    {"timestamp": "2026-06-01T05:32:27", "recipient_email": "c@example.com", "delivery_status": "SUCCESS", "region": "USA"}
]


def write_sample_logs(path):
    with open(path, "w", encoding="utf-8") as f:
        for entry in SAMPLE_LOGS:
            f.write(json.dumps(entry) + "\n")


def test_multiversal_simulations_and_transformation_insights(tmp_path, monkeypatch):
    # write logs to the expected LOG_JSON_PATH
    log_path = tmp_path / "email_status_log.json"
    write_sample_logs(log_path)

    # monkeypatch the module-level path to point at temp file
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    # re-import module functions by forcing reload
    import importlib
    import dashboard
    importlib.reload(dashboard)

    sims = dashboard.load_multiversal_simulations()
    assert "simulations" in sims
    assert sims["scenario_count"] == 3
    assert "success_rate" in sims

    t = dashboard.load_transformation_insights()
    assert "total_events" in t
    assert t["total_events"] == 3
    assert isinstance(t.get("insights"), list)


def test_infinite_continuity_engine(tmp_path, monkeypatch):
    log_path = tmp_path / "email_status_log.json"
    write_sample_logs(log_path)
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    ce = dashboard.load_infinite_continuity_engine()
    assert "metrics" in ce
    assert "resilience_index" in ce["metrics"]
    assert isinstance(ce["metrics"]["resilience_index"], int)
