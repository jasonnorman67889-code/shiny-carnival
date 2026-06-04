"""
Phase 1 Strategic Foundations Test Suite
Tests KPI models, foresight scenarios, and risk dashboards.
"""

import pytest
import json
import csv
import os
import tempfile
from datetime import datetime, timedelta, timezone
from models.strategic_goals import KPI, StrategicGoal, ForesightScenario, RiskDashboard
from services.foresight_service import ForesightService


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample log file
        logs_file = os.path.join(tmpdir, "email_status_log.json")
        with open(logs_file, "w") as f:
            for i in range(10):
                f.write(
                    json.dumps({
                        "recipient_email": f"user{i}@example.com",
                        "delivery_status": "delivered" if i % 3 != 0 else "failed",
                        "region": "USA" if i % 2 == 0 else "EUROPE",
                    })
                    + "\n"
                )

        # Create sample compliance file
        compliance_file = os.path.join(tmpdir, "compliance_report.json")
        with open(compliance_file, "w") as f:
            json.dump({
                "regional_audit": [
                    {
                        "region": "USA",
                        "audit_status": "completed",
                        "status": "Compliant",
                    },
                    {
                        "region": "EUROPE",
                        "audit_status": "pending",
                        "status": "Under Review",
                    },
                ]
            }, f)

        # Create sample opt-out file
        opt_out_file = os.path.join(tmpdir, "opt_out_history.json")
        with open(opt_out_file, "w") as f:
            now = datetime.now(timezone.utc)
            opt_outs = [
                {
                    "email": "unsubscribe1@example.com",
                    "timestamp": (now - timedelta(days=10)).isoformat(),
                },
                {
                    "email": "unsubscribe2@example.com",
                    "timestamp": (now - timedelta(days=5)).isoformat(),
                },
                {
                    "email": "unsubscribe3@example.com",
                    "timestamp": now.isoformat(),
                },
            ]
            json.dump(opt_outs, f)

        # Create sample users CSV
        users_file = os.path.join(tmpdir, "users.csv")
        with open(users_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["email", "name", "region", "channel"])
            writer.writeheader()
            writer.writerows([
                {
                    "email": "user1@example.com",
                    "name": "User One",
                    "region": "USA",
                    "channel": "email",
                },
                {
                    "email": "user2@example.com",
                    "name": "User Two",
                    "region": "EUROPE",
                    "channel": "email",
                },
            ])

        yield tmpdir


class TestKPIModel:
    """Test KPI model and status tracking."""

    def test_kpi_creation(self):
        """Test KPI instantiation."""
        kpi = KPI(
            name="Test KPI",
            metric_type="resilience",
            target_value=100.0,
            current_value=85.0,
            threshold_critical=70.0,
            threshold_warning=90.0,
            unit="%",
            description="Test metric",
        )
        assert kpi.name == "Test KPI"
        assert kpi.metric_type == "resilience"

    def test_kpi_status_critical(self):
        """Test KPI critical status."""
        kpi = KPI(
            name="Critical KPI",
            metric_type="compliance",
            target_value=100.0,
            current_value=50.0,
            threshold_critical=70.0,
            threshold_warning=90.0,
            unit="%",
            description="Test",
        )
        assert kpi.status() == "critical"

    def test_kpi_status_warning(self):
        """Test KPI warning status."""
        kpi = KPI(
            name="Warning KPI",
            metric_type="compliance",
            target_value=100.0,
            current_value=85.0,
            threshold_critical=70.0,
            threshold_warning=90.0,
            unit="%",
            description="Test",
        )
        assert kpi.status() == "warning"

    def test_kpi_status_healthy(self):
        """Test KPI healthy status."""
        kpi = KPI(
            name="Healthy KPI",
            metric_type="resilience",
            target_value=100.0,
            current_value=95.0,
            threshold_critical=70.0,
            threshold_warning=90.0,
            unit="%",
            description="Test",
        )
        assert kpi.status() == "healthy"

    def test_kpi_progress_percent(self):
        """Test KPI progress calculation."""
        kpi = KPI(
            name="Progress KPI",
            metric_type="efficiency",
            target_value=100.0,
            current_value=50.0,
            threshold_critical=30.0,
            threshold_warning=70.0,
            unit="%",
            description="Test",
        )
        assert kpi.progress_percent() == 50.0


class TestStrategicGoal:
    """Test Strategic Goal model."""

    def test_goal_creation(self):
        """Test strategic goal instantiation."""
        goal = StrategicGoal(
            goal_id="goal_001",
            title="Test Goal",
            description="Test strategic goal",
            category="resilience",
            priority="high",
            status="active",
        )
        assert goal.goal_id == "goal_001"
        assert goal.status == "active"

    def test_goal_add_kpi(self):
        """Test adding KPIs to goal."""
        goal = StrategicGoal(
            goal_id="goal_002",
            title="KPI Test Goal",
            description="Test",
            category="compliance",
            priority="critical",
            status="active",
        )
        kpi = KPI(
            name="Test KPI",
            metric_type="compliance",
            target_value=100.0,
            current_value=90.0,
            threshold_critical=70.0,
            threshold_warning=85.0,
            unit="%",
            description="Test",
        )
        goal.add_kpi(kpi)
        assert len(goal.kpis) == 1
        assert goal.kpis[0].name == "Test KPI"

    def test_goal_overall_progress(self):
        """Test goal overall progress calculation."""
        goal = StrategicGoal(
            goal_id="goal_003",
            title="Progress Goal",
            description="Test",
            category="sustainability",
            priority="high",
            status="active",
        )
        kpi1 = KPI(
            name="KPI 1",
            metric_type="sustainability",
            target_value=100.0,
            current_value=60.0,
            threshold_critical=40.0,
            threshold_warning=80.0,
            unit="%",
            description="Test",
        )
        kpi2 = KPI(
            name="KPI 2",
            metric_type="sustainability",
            target_value=100.0,
            current_value=80.0,
            threshold_critical=40.0,
            threshold_warning=80.0,
            unit="%",
            description="Test",
        )
        goal.add_kpi(kpi1)
        goal.add_kpi(kpi2)
        assert goal.overall_progress() == 70.0

    def test_goal_overall_status(self):
        """Test goal overall status determination."""
        goal = StrategicGoal(
            goal_id="goal_004",
            title="Status Goal",
            description="Test",
            category="resilience",
            priority="critical",
            status="active",
        )
        kpi_critical = KPI(
            name="Critical KPI",
            metric_type="resilience",
            target_value=100.0,
            current_value=50.0,
            threshold_critical=70.0,
            threshold_warning=90.0,
            unit="%",
            description="Test",
        )
        goal.add_kpi(kpi_critical)
        assert goal.overall_status() == "critical"


class TestForesightService:
    """Test Foresight Service for strategic planning."""

    def test_service_initialization(self, temp_data_dir):
        """Test service initialization."""
        service = ForesightService(data_dir=temp_data_dir)
        assert service.data_dir == temp_data_dir

    def test_load_delivery_metrics(self, temp_data_dir):
        """Test loading delivery metrics from logs."""
        service = ForesightService(data_dir=temp_data_dir)
        success_rate, delivered, failed = service.load_delivery_metrics()
        assert 0 <= success_rate <= 100
        assert delivered + failed == 10

    def test_load_compliance_status(self, temp_data_dir):
        """Test loading compliance status."""
        service = ForesightService(data_dir=temp_data_dir)
        pending, regions = service.load_compliance_status()
        assert pending == 1
        assert "EUROPE" in regions

    def test_load_opt_out_trend(self, temp_data_dir):
        """Test loading opt-out trend."""
        service = ForesightService(data_dir=temp_data_dir)
        total, trend = service.load_opt_out_trend()
        assert total == 3
        assert 0 <= trend <= 100

    def test_build_strategic_goals(self, temp_data_dir):
        """Test building strategic goals from data."""
        service = ForesightService(data_dir=temp_data_dir)
        goals = service.build_strategic_goals()
        assert len(goals) >= 3  # At least 3 goal categories
        assert all(isinstance(g, StrategicGoal) for g in goals)
        assert all(len(g.kpis) > 0 for g in goals)

    def test_generate_risk_scenarios(self, temp_data_dir):
        """Test risk scenario generation."""
        service = ForesightService(data_dir=temp_data_dir)
        goals = service.build_strategic_goals()
        scenarios = service.generate_risk_scenarios(goals)
        assert len(scenarios) > 0
        assert all(isinstance(s, ForesightScenario) for s in scenarios)
        assert all(0 <= s.risk_score() <= 100 for s in scenarios)

    def test_build_risk_dashboard(self, temp_data_dir):
        """Test risk dashboard construction."""
        service = ForesightService(data_dir=temp_data_dir)
        goals = service.build_strategic_goals()
        scenarios = service.generate_risk_scenarios(goals)
        dashboard = service.build_risk_dashboard(goals, scenarios)
        assert isinstance(dashboard, RiskDashboard)
        assert len(dashboard.strategic_goals) > 0
        assert len(dashboard.scenarios) > 0
        assert 0 <= dashboard.calculate_composite_resilience() <= 100

    def test_generate_phase_1_summary(self, temp_data_dir):
        """Test Phase 1 summary generation."""
        service = ForesightService(data_dir=temp_data_dir)
        summary = service.generate_phase_1_summary()
        assert summary["phase"] == "Phase 1: Strategic Foundations"
        assert "strategic_goals" in summary
        assert "risk_scenarios" in summary
        assert "dashboard_summary" in summary
        assert 0 <= summary["foresight_confidence"] <= 1


class TestRiskScenarios:
    """Test Risk Scenario model."""

    def test_scenario_creation(self):
        """Test risk scenario instantiation."""
        scenario = ForesightScenario(
            scenario_id="risk_001",
            name="Test Risk",
            description="Test scenario",
            probability=0.7,
            impact_level="high",
            affected_goals=["goal_001", "goal_002"],
            predicted_kpi_changes={"KPI_1": -10.0},
            mitigation_actions=["Action 1", "Action 2"],
            scenario_type="risk",
            confidence_score=0.85,
        )
        assert scenario.scenario_id == "risk_001"
        assert scenario.probability == 0.7

    def test_scenario_risk_score(self):
        """Test risk score calculation."""
        scenario = ForesightScenario(
            scenario_id="risk_002",
            name="High Risk",
            description="Test",
            probability=0.8,
            impact_level="high",
            affected_goals=["goal_001"],
            predicted_kpi_changes={"KPI_1": -20.0},
            mitigation_actions=["Action 1"],
            scenario_type="risk",
            confidence_score=0.9,
        )
        risk_score = scenario.risk_score()
        assert 0 <= risk_score <= 100
        assert risk_score > 50  # High probability × high impact should score >50


class TestRiskDashboard:
    """Test Risk Dashboard aggregation."""

    def test_dashboard_creation(self):
        """Test dashboard instantiation."""
        dashboard = RiskDashboard()
        assert len(dashboard.scenarios) == 0
        assert len(dashboard.strategic_goals) == 0

    def test_dashboard_add_goal(self):
        """Test adding goals to dashboard."""
        dashboard = RiskDashboard()
        goal = StrategicGoal(
            goal_id="goal_001",
            title="Test Goal",
            description="Test",
            category="resilience",
            priority="high",
            status="active",
        )
        dashboard.add_goal(goal)
        assert len(dashboard.strategic_goals) == 1

    def test_dashboard_add_scenario(self):
        """Test adding scenarios to dashboard."""
        dashboard = RiskDashboard()
        scenario = ForesightScenario(
            scenario_id="risk_001",
            name="Test Risk",
            description="Test",
            probability=0.5,
            impact_level="medium",
            affected_goals=["goal_001"],
            predicted_kpi_changes={"KPI_1": -5.0},
            mitigation_actions=["Action 1"],
            scenario_type="risk",
            confidence_score=0.8,
        )
        dashboard.add_scenario(scenario)
        assert len(dashboard.scenarios) == 1

    def test_dashboard_top_risks(self):
        """Test getting top risks from dashboard."""
        dashboard = RiskDashboard()
        for i in range(5):
            scenario = ForesightScenario(
                scenario_id=f"risk_{i}",
                name=f"Risk {i}",
                description="Test",
                probability=0.1 * (i + 1),
                impact_level="high",
                affected_goals=["goal_001"],
                predicted_kpi_changes={"KPI_1": -10.0},
                mitigation_actions=["Action 1"],
                scenario_type="risk",
                confidence_score=0.8,
            )
            dashboard.add_scenario(scenario)
        
        top_risks = dashboard.top_risks(limit=3)
        assert len(top_risks) == 3
        # Verify they are sorted by risk score (descending)
        risk_scores = [s.risk_score() for s in top_risks]
        assert risk_scores == sorted(risk_scores, reverse=True)
