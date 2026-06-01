import os
import json
import csv
import tempfile
from pathlib import Path
from dashboard import (
    load_transformation_insights, load_multiversal_simulations, load_infinite_continuity_engine,
    load_user_region_data, build_strategy_nexus, load_legacy_preservation_framework, load_singularity_governance_matrix,
    LOG_JSON_PATH, CSV_FILE_PATH, COMPLIANCE_REPORT_PATH
)

SAMPLE_LOGS = [
    {"timestamp": "2026-06-01T05:30:27", "recipient_email": "a@example.com", "delivery_status": "SUCCESS", "region": "USA"},
    {"timestamp": "2026-06-01T05:31:27", "recipient_email": "b@example.com", "delivery_status": "FAILED", "region": "EUROPE"},
    {"timestamp": "2026-06-01T05:32:27", "recipient_email": "c@example.com", "delivery_status": "SUCCESS", "region": "USA"}
]

SAMPLE_USERS = [
    {"email": "user1@test.com", "name": "Alice", "region": "USA", "channel": "email"},
    {"email": "user2@test.com", "name": "Bob", "region": "EUROPE", "channel": "email"},
]

SAMPLE_COMPLIANCE = {
    "timestamp": "2026-06-01T06:53:09.236297",
    "total_emails": 3,
    "successful_deliveries": 2,
    "failed_deliveries": 1,
    "opt_out_count": 4,
    "regional_audit": []
}


def write_sample_logs(path):
    with open(path, "w", encoding="utf-8") as f:
        for entry in SAMPLE_LOGS:
            f.write(json.dumps(entry) + "\n")


def write_sample_users(path):
    with open(path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "name", "region", "channel"])
        writer.writeheader()
        writer.writerows(SAMPLE_USERS)


def write_sample_compliance(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_COMPLIANCE, f)


def test_multiversal_simulations_and_transformation_insights(tmp_path, monkeypatch):
    log_path = tmp_path / "email_status_log.json"
    write_sample_logs(log_path)
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    sims = dashboard.load_multiversal_simulations()
    assert "simulations" in sims
    assert sims["scenario_count"] == 3
    assert "success_rate" in sims
    assert float(sims["success_rate"].rstrip("%")) > 0

    t = dashboard.load_transformation_insights()
    assert "total_events" in t
    assert t["total_events"] == 3
    assert isinstance(t.get("insights"), list)


def test_infinite_continuity_engine(tmp_path, monkeypatch):
    log_path = tmp_path / "email_status_log.json"
    compliance_path = tmp_path / "compliance_report.json"
    write_sample_logs(log_path)
    write_sample_compliance(compliance_path)
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    monkeypatch.setenv("COMPLIANCE_REPORT_PATH", str(compliance_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    ce = dashboard.load_infinite_continuity_engine()
    assert "metrics" in ce
    assert "resilience_index" in ce["metrics"]
    assert isinstance(ce["metrics"]["resilience_index"], int)
    assert 0 <= ce["metrics"]["resilience_index"] <= 100


def test_user_region_data(tmp_path, monkeypatch):
    users_path = tmp_path / "users.csv"
    write_sample_users(users_path)
    monkeypatch.setenv("CSV_FILE_PATH", str(users_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    regions = dashboard.load_user_region_data()
    assert len(regions) == 2
    region_names = {r["region"] for r in regions}
    assert "USA" in region_names
    assert "EUROPE" in region_names


def test_strategy_nexus_with_real_data(tmp_path, monkeypatch):
    log_path = tmp_path / "email_status_log.json"
    users_path = tmp_path / "users.csv"
    compliance_path = tmp_path / "compliance_report.json"
    write_sample_logs(log_path)
    write_sample_users(users_path)
    write_sample_compliance(compliance_path)
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    monkeypatch.setenv("CSV_FILE_PATH", str(users_path))
    monkeypatch.setenv("COMPLIANCE_REPORT_PATH", str(compliance_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    nexus = dashboard.build_strategy_nexus()
    assert "nexus_status" in nexus
    assert "audience_regions" in nexus
    assert isinstance(nexus.get("recommendations"), list)


def test_legacy_framework_with_real_data(tmp_path, monkeypatch):
    log_path = tmp_path / "email_status_log.json"
    compliance_path = tmp_path / "compliance_report.json"
    opt_out_history_path = tmp_path / "opt_out_history.json"
    write_sample_logs(log_path)
    write_sample_compliance(compliance_path)
    with open(opt_out_history_path, "w") as f:
        json.dump([{"email": "test@example.com", "timestamp": "2026-06-01T10:00:00"}], f)
    
    monkeypatch.setenv("JSON_LOG_FILE", str(log_path))
    monkeypatch.setenv("COMPLIANCE_REPORT_PATH", str(compliance_path))
    monkeypatch.setenv("OPT_OUT_HISTORY_PATH", str(opt_out_history_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    legacy = dashboard.load_legacy_preservation_framework()
    assert "framework_status" in legacy
    assert "brand_resilience_score" in legacy
    assert isinstance(legacy["brand_resilience_score"], int)
    assert "opt_out_count" in legacy


def test_singularity_matrix_with_compliance_data(tmp_path, monkeypatch):
    compliance_path = tmp_path / "compliance_report.json"
    write_sample_compliance(compliance_path)
    monkeypatch.setenv("COMPLIANCE_REPORT_PATH", str(compliance_path))
    import importlib
    import dashboard
    importlib.reload(dashboard)

    matrix = dashboard.load_singularity_governance_matrix()
    assert "matrix_status" in matrix
    assert "pending_compliance_count" in matrix
    assert isinstance(matrix["governance_health"], str)
