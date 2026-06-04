"""
Strategic Goals & KPI Models for Destiny Layer (Phase 1)
Defines enterprise strategic objectives, KPIs, and foresight scenarios.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime, timezone
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class KPI:
    """Key Performance Indicator for strategic tracking."""
    name: str
    metric_type: str  # 'resilience', 'compliance', 'efficiency', 'sustainability'
    target_value: float
    current_value: float
    threshold_critical: float
    threshold_warning: float
    unit: str
    description: str
    last_updated: str = field(default_factory=utc_now_iso)

    def status(self) -> str:
        """Determine KPI status: critical, warning, healthy."""
        if self.current_value <= self.threshold_critical:
            return "critical"
        elif self.current_value <= self.threshold_warning:
            return "warning"
        return "healthy"

    def progress_percent(self) -> float:
        """Calculate progress toward target (0-100)."""
        if self.target_value == 0:
            return 0.0
        return min(100, (self.current_value / self.target_value) * 100)


@dataclass
class StrategicGoal:
    """Strategic objective aligned with destiny planning."""
    goal_id: str
    title: str
    description: str
    category: str  # 'compliance', 'resilience', 'sustainability', 'efficiency'
    priority: str  # 'critical', 'high', 'medium', 'low'
    status: str  # 'active', 'paused', 'completed'
    kpis: List[KPI] = field(default_factory=list)
    owner: str = "Governance"
    created_at: str = field(default_factory=utc_now_iso)
    target_date: Optional[str] = None

    def add_kpi(self, kpi: KPI) -> None:
        """Add a KPI to this goal."""
        self.kpis.append(kpi)

    def overall_progress(self) -> float:
        """Calculate average KPI progress."""
        if not self.kpis:
            return 0.0
        return sum(kpi.progress_percent() for kpi in self.kpis) / len(self.kpis)

    def overall_status(self) -> str:
        """Determine overall goal status based on KPIs."""
        if not self.kpis:
            return "unknown"
        statuses = [kpi.status() for kpi in self.kpis]
        if "critical" in statuses:
            return "critical"
        elif "warning" in statuses:
            return "warning"
        return "healthy"


@dataclass
class ForesightScenario:
    """Predictive scenario for strategic planning."""
    scenario_id: str
    name: str
    description: str
    probability: float  # 0-1
    impact_level: str  # 'high', 'medium', 'low'
    affected_goals: List[str]  # IDs of strategic goals affected
    predicted_kpi_changes: Dict[str, float]  # {kpi_name: expected_change}
    mitigation_actions: List[str]
    scenario_type: str  # 'risk', 'opportunity', 'disruption'
    confidence_score: float  # 0-1, AI model confidence
    created_at: str = field(default_factory=utc_now_iso)

    def risk_score(self) -> float:
        """Calculate composite risk score (0-100)."""
        # Risk = probability × impact_level × (1 - mitigation_coverage)
        impact_weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        impact_score = impact_weights.get(self.impact_level, 0.5)
        mitigation_coverage = len(self.mitigation_actions) * 0.2  # Each action reduces risk by 20%
        mitigation_coverage = min(0.8, mitigation_coverage)  # Cap at 80% reduction
        return self.probability * impact_score * (1 - mitigation_coverage) * 100


@dataclass
class RiskDashboard:
    """Aggregate view of strategic risks and resilience."""
    timestamp: str = field(default_factory=utc_now_iso)
    scenarios: List[ForesightScenario] = field(default_factory=list)
    strategic_goals: List[StrategicGoal] = field(default_factory=list)
    resilience_score: float = 0.0
    compliance_score: float = 0.0
    efficiency_score: float = 0.0
    sustainability_score: float = 0.0

    def add_scenario(self, scenario: ForesightScenario) -> None:
        """Add a risk scenario."""
        self.scenarios.append(scenario)

    def add_goal(self, goal: StrategicGoal) -> None:
        """Add a strategic goal."""
        self.strategic_goals.append(goal)

    def top_risks(self, limit: int = 5) -> List[ForesightScenario]:
        """Get highest-risk scenarios."""
        sorted_scenarios = sorted(
            self.scenarios, key=lambda s: s.risk_score(), reverse=True
        )
        return sorted_scenarios[:limit]

    def calculate_composite_resilience(self) -> float:
        """Calculate overall resilience (weighted average of all KPIs)."""
        all_kpis = []
        for goal in self.strategic_goals:
            all_kpis.extend(goal.kpis)

        if not all_kpis:
            return 0.0

        # Weight by metric type
        weights = {
            "resilience": 0.4,
            "compliance": 0.3,
            "efficiency": 0.2,
            "sustainability": 0.1,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for kpi in all_kpis:
            weight = weights.get(kpi.metric_type, 0.1)
            weighted_sum += kpi.progress_percent() * weight
            weight_total += weight

        return weighted_sum / weight_total if weight_total > 0 else 0.0

    def get_summary(self) -> Dict:
        """Generate strategic summary for dashboards."""
        return {
            "timestamp": self.timestamp,
            "strategic_goals_count": len(self.strategic_goals),
            "active_scenarios": len(self.scenarios),
            "top_risks": [
                {
                    "name": s.name,
                    "risk_score": s.risk_score(),
                    "probability": s.probability,
                    "impact_level": s.impact_level,
                }
                for s in self.top_risks(3)
            ],
            "overall_resilience": self.calculate_composite_resilience(),
            "resilience_score": self.resilience_score,
            "compliance_score": self.compliance_score,
            "efficiency_score": self.efficiency_score,
            "sustainability_score": self.sustainability_score,
            "goal_statuses": [
                {
                    "goal_id": g.goal_id,
                    "title": g.title,
                    "status": g.overall_status(),
                    "progress": g.overall_progress(),
                }
                for g in self.strategic_goals
            ],
        }
