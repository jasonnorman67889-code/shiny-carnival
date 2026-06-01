"""
Foresight AI Service (Phase 1)
Implements predictive analytics and scenario forecasting for strategic planning.
"""

import json
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from models.strategic_goals import (
    KPI,
    StrategicGoal,
    ForesightScenario,
    RiskDashboard,
)


class ForesightService:
    """AI service for strategic foresight and predictive modeling."""

    def __init__(self, data_dir: str = "data"):
        """Initialize with data directory."""
        self.data_dir = data_dir
        self.logs_file = os.path.join(data_dir, "email_status_log.json")
        self.compliance_file = os.path.join(data_dir, "compliance_report.json")
        self.users_file = os.path.join(data_dir, "users.csv")
        self.opt_out_file = os.path.join(data_dir, "opt_out_history.json")

    def load_delivery_metrics(self) -> Tuple[float, int, int]:
        """
        Load delivery success rate and counts from logs.
        Returns: (success_rate, total_delivered, failed_count)
        """
        try:
            with open(self.logs_file, "r") as f:
                logs = [json.loads(line) for line in f if line.strip()]
                total = len(logs)
                if total == 0:
                    return 0.0, 0, 0

                successful = sum(
                    1 for log in logs if log.get("delivery_status") == "delivered"
                )
                failed = total - successful
                success_rate = (successful / total) * 100 if total > 0 else 0

                return success_rate, successful, failed
        except Exception:
            return 0.0, 0, 0

    def load_compliance_status(self) -> Tuple[int, List[str]]:
        """
        Load compliance audit status.
        Returns: (pending_audit_count, regions_with_issues)
        """
        try:
            with open(self.compliance_file, "r") as f:
                compliance_data = json.load(f)
                regional_audits = compliance_data.get("regional_audit", [])
                pending = sum(
                    1
                    for audit in regional_audits
                    if audit.get("audit_status") == "pending"
                )
                regions = [
                    audit.get("region")
                    for audit in regional_audits
                    if audit.get("audit_status") == "pending"
                ]
                return pending, regions
        except Exception:
            return 0, []

    def load_opt_out_trend(self) -> Tuple[int, float]:
        """
        Load opt-out metrics.
        Returns: (total_opt_outs, recent_trend_percent)
        """
        try:
            with open(self.opt_out_file, "r") as f:
                opt_outs = json.load(f)
                total = len(opt_outs)

                # Calculate recent trend (last 7 days)
                now = datetime.utcnow()
                seven_days_ago = now - timedelta(days=7)
                recent = sum(
                    1
                    for entry in opt_outs
                    if datetime.fromisoformat(entry.get("timestamp", now.isoformat()))
                    >= seven_days_ago
                )
                trend = (recent / max(1, total)) * 100

                return total, trend
        except Exception:
            return 0, 0.0

    def build_strategic_goals(self) -> List[StrategicGoal]:
        """
        Build strategic goals with real data-driven KPIs.
        """
        success_rate, delivered, failed = self.load_delivery_metrics()
        opt_outs, opt_out_trend = self.load_opt_out_trend()
        pending_audits, audit_regions = self.load_compliance_status()

        goals = []

        # Goal 1: Email Delivery Excellence (Resilience)
        goal_1 = StrategicGoal(
            goal_id="goal_001",
            title="Email Delivery Excellence",
            description="Achieve 95%+ email delivery success rate across all regions.",
            category="resilience",
            priority="critical",
            status="active",
            owner="Operations",
            target_date=(datetime.utcnow() + timedelta(days=90)).isoformat(),
        )
        goal_1.add_kpi(
            KPI(
                name="Delivery Success Rate",
                metric_type="resilience",
                target_value=95.0,
                current_value=success_rate,
                threshold_critical=80.0,
                threshold_warning=90.0,
                unit="%",
                description="Percentage of emails successfully delivered",
            )
        )
        goal_1.add_kpi(
            KPI(
                name="Failed Deliveries",
                metric_type="resilience",
                target_value=0.0,
                current_value=max(0, 100 - failed),
                threshold_critical=50.0,
                threshold_warning=80.0,
                unit="count",
                description="Number of failed delivery attempts",
            )
        )
        goals.append(goal_1)

        # Goal 2: Regulatory Compliance (Compliance)
        goal_2 = StrategicGoal(
            goal_id="goal_002",
            title="Regulatory Compliance",
            description="Maintain 100% compliance with GDPR, CCPA, and regional regulations.",
            category="compliance",
            priority="critical",
            status="active",
            owner="Compliance",
            target_date=(datetime.utcnow() + timedelta(days=60)).isoformat(),
        )
        goal_2.add_kpi(
            KPI(
                name="Audit Completion Rate",
                metric_type="compliance",
                target_value=100.0,
                current_value=max(0, 100 - pending_audits * 10),
                threshold_critical=70.0,
                threshold_warning=90.0,
                unit="%",
                description="Percentage of compliance audits completed",
            )
        )
        goal_2.add_kpi(
            KPI(
                name="Regulatory Adherence",
                metric_type="compliance",
                target_value=100.0,
                current_value=100.0 - (len(audit_regions) * 15),
                threshold_critical=80.0,
                threshold_warning=95.0,
                unit="%",
                description="Adherence to regulatory frameworks",
            )
        )
        goals.append(goal_2)

        # Goal 3: Subscriber Engagement (Sustainability)
        goal_3 = StrategicGoal(
            goal_id="goal_003",
            title="Subscriber Engagement & Retention",
            description="Minimize opt-out rates and maintain healthy subscriber engagement.",
            category="sustainability",
            priority="high",
            status="active",
            owner="Marketing",
            target_date=(datetime.utcnow() + timedelta(days=90)).isoformat(),
        )
        goal_3.add_kpi(
            KPI(
                name="Opt-Out Rate",
                metric_type="sustainability",
                target_value=2.0,
                current_value=min(100, opt_out_trend * 2),
                threshold_critical=10.0,
                threshold_warning=5.0,
                unit="%",
                description="Percentage of subscribers opting out",
            )
        )
        goal_3.add_kpi(
            KPI(
                name="Subscriber Retention",
                metric_type="sustainability",
                target_value=98.0,
                current_value=max(0, 100 - opt_outs / max(1, delivered) * 100),
                threshold_critical=85.0,
                threshold_warning=92.0,
                unit="%",
                description="Percentage of retained subscribers",
            )
        )
        goals.append(goal_3)

        # Goal 4: Operational Efficiency (Efficiency)
        goal_4 = StrategicGoal(
            goal_id="goal_004",
            title="Operational Efficiency",
            description="Optimize campaign execution and resource allocation.",
            category="efficiency",
            priority="high",
            status="active",
            owner="Operations",
        )
        goal_4.add_kpi(
            KPI(
                name="Campaign Execution Speed",
                metric_type="efficiency",
                target_value=90.0,
                current_value=min(100, success_rate * 0.95),
                threshold_critical=70.0,
                threshold_warning=85.0,
                unit="%",
                description="Percentage of campaigns executed on schedule",
            )
        )
        goals.append(goal_4)

        return goals

    def generate_risk_scenarios(
        self, strategic_goals: List[StrategicGoal]
    ) -> List[ForesightScenario]:
        """
        Generate predictive risk scenarios based on current metrics.
        """
        success_rate, _, failed = self.load_delivery_metrics()
        opt_outs, opt_out_trend = self.load_opt_out_trend()
        pending_audits, audit_regions = self.load_compliance_status()

        scenarios = []

        # Scenario 1: Delivery System Degradation
        if success_rate < 90:
            scenarios.append(
                ForesightScenario(
                    scenario_id="risk_001",
                    name="Email Delivery System Degradation",
                    description="Risk of cascading email delivery failures impacting campaign reach.",
                    probability=min(1.0, (100 - success_rate) / 100),
                    impact_level="high",
                    affected_goals=["goal_001", "goal_004"],
                    predicted_kpi_changes={
                        "Delivery Success Rate": -10.0,
                        "Failed Deliveries": failed * 1.5,
                    },
                    mitigation_actions=[
                        "Implement redundant mail servers",
                        "Increase monitoring frequency",
                        "Establish failover procedures",
                    ],
                    scenario_type="risk",
                    confidence_score=0.85,
                )
            )

        # Scenario 2: Regulatory Non-Compliance
        if pending_audits > 0:
            scenarios.append(
                ForesightScenario(
                    scenario_id="risk_002",
                    name="Regulatory Non-Compliance Detection",
                    description=f"Risk of compliance violations in {', '.join(audit_regions)}.",
                    probability=min(1.0, pending_audits / 5),
                    impact_level="high",
                    affected_goals=["goal_002"],
                    predicted_kpi_changes={
                        "Audit Completion Rate": -20.0,
                        "Regulatory Adherence": -15.0,
                    },
                    mitigation_actions=[
                        "Fast-track compliance audits",
                        "Audit regional workflows",
                        "Remediate policy gaps",
                    ],
                    scenario_type="risk",
                    confidence_score=0.90,
                )
            )

        # Scenario 3: Subscriber Churn
        if opt_out_trend > 5:
            scenarios.append(
                ForesightScenario(
                    scenario_id="risk_003",
                    name="Accelerated Subscriber Opt-Out",
                    description="Risk of increasing subscriber opt-out rates due to engagement issues.",
                    probability=min(1.0, opt_out_trend / 20),
                    impact_level="medium",
                    affected_goals=["goal_003", "goal_001"],
                    predicted_kpi_changes={
                        "Opt-Out Rate": opt_out_trend * 1.5,
                        "Subscriber Retention": -(opt_out_trend * 0.5),
                    },
                    mitigation_actions=[
                        "Launch re-engagement campaigns",
                        "Segment high-risk subscribers",
                        "Personalize content strategy",
                    ],
                    scenario_type="risk",
                    confidence_score=0.78,
                )
            )

        # Scenario 4: Opportunity - Market Expansion
        scenarios.append(
            ForesightScenario(
                scenario_id="opp_001",
                name="Market Expansion Opportunity",
                description="Opportunity to expand campaigns to new regions with positive market conditions.",
                probability=0.65,
                impact_level="high",
                affected_goals=["goal_001", "goal_004"],
                predicted_kpi_changes={
                    "Campaign Execution Speed": 15.0,
                    "Subscriber Retention": 5.0,
                },
                mitigation_actions=[
                    "Develop regional market strategy",
                    "Allocate expansion resources",
                    "Test regional compliance frameworks",
                ],
                scenario_type="opportunity",
                confidence_score=0.72,
            )
        )

        return scenarios

    def build_risk_dashboard(
        self, strategic_goals: List[StrategicGoal], scenarios: List[ForesightScenario]
    ) -> RiskDashboard:
        """
        Build comprehensive risk dashboard from goals and scenarios.
        """
        dashboard = RiskDashboard(strategic_goals=strategic_goals, scenarios=scenarios)

        # Calculate composite scores
        success_rate, _, _ = self.load_delivery_metrics()
        _, audit_regions = self.load_compliance_status()

        dashboard.resilience_score = success_rate
        dashboard.compliance_score = max(0, 100 - len(audit_regions) * 20)
        dashboard.efficiency_score = min(100, success_rate * 1.05)
        dashboard.sustainability_score = 85.0  # Placeholder, can be enhanced

        return dashboard

    def generate_phase_1_summary(self) -> Dict:
        """
        Generate Phase 1 strategic foundations summary.
        """
        goals = self.build_strategic_goals()
        scenarios = self.generate_risk_scenarios(goals)
        dashboard = self.build_risk_dashboard(goals, scenarios)

        return {
            "phase": "Phase 1: Strategic Foundations",
            "timestamp": datetime.utcnow().isoformat(),
            "strategic_goals": [
                {
                    "goal_id": g.goal_id,
                    "title": g.title,
                    "status": g.overall_status(),
                    "progress": g.overall_progress(),
                    "kpis_count": len(g.kpis),
                }
                for g in goals
            ],
            "risk_scenarios": [
                {
                    "scenario_id": s.scenario_id,
                    "name": s.name,
                    "type": s.scenario_type,
                    "risk_score": s.risk_score(),
                    "probability": s.probability,
                }
                for s in scenarios
            ],
            "dashboard_summary": dashboard.get_summary(),
            "foresight_confidence": sum(s.confidence_score for s in scenarios)
            / max(1, len(scenarios)),
        }
