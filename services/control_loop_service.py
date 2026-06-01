"""
Phase 2: Control Loop Service

Implements the core control loop orchestration for adaptive governance.
Manages detection → evaluation → decision → execution → feedback cycles.
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import os

from models.workflow_models import (
    Workflow,
    WorkflowStep,
    WorkflowStatus,
    GovernanceEvent,
    EventType,
    EventPriority,
    ControlLoopCycle,
)
from models.strategic_goals import KPI, StrategicGoal, ForesightScenario, RiskDashboard
from services.foresight_service import ForesightService


class ControlLoopService:
    """
    Orchestrates the continuous control loop:
    Detection → Evaluation → Decision → Execution → Feedback → Adaptation
    """

    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.foresight_service = ForesightService(data_dir)

        # State management
        self.workflows: Dict[str, Workflow] = {}
        self.event_queue: List[GovernanceEvent] = []
        self.cycles: List[ControlLoopCycle] = []
        self.last_cycle_number = 0
        self.control_loop_active = False

        # Metrics
        self.total_cycles_executed = 0
        self.total_events_processed = 0
        self.total_workflows_triggered = 0

    def create_workflow(
        self,
        name: str,
        description: str,
        trigger_event: str,
        priority: EventPriority = EventPriority.MEDIUM,
    ) -> Workflow:
        """Create a new workflow"""
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            trigger_event=trigger_event,
            priority=priority,
        )
        self.workflows[workflow_id] = workflow
        return workflow

    def add_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        action_type: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowStep]:
        """Add a step to a workflow"""
        if workflow_id not in self.workflows:
            return None

        step_id = f"step_{uuid.uuid4().hex[:8]}"
        step = WorkflowStep(
            step_id=step_id,
            name=step_name,
            description=f"{action_type} - {step_name}",
            action_type=action_type,
            inputs=inputs or {},
        )
        self.workflows[workflow_id].add_step(step)
        return step

    def create_event(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM,
    ) -> GovernanceEvent:
        """Create a governance event"""
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        event = GovernanceEvent(
            event_id=event_id,
            event_type=event_type,
            priority=priority,
            source=source,
            data=data,
        )
        self.event_queue.append(event)
        return event

    def detect_events(self) -> List[GovernanceEvent]:
        """
        Detection Phase: Scan for new governance events
        Returns: List of detected events
        """
        detected = []

        try:
            # Load current metrics from data sources
            success_rate, delivered, failed = self.foresight_service.load_delivery_metrics()
            compliance_pending, pending_regions = self.foresight_service.load_compliance_status()
            opt_out_trend = self.foresight_service.load_opt_out_trend()

            # Detect metric changes and anomalies
            if success_rate < 95:
                event = self.create_event(
                    EventType.METRIC_UPDATE,
                    "delivery_monitor",
                    {
                        "metric": "delivery_success_rate",
                        "value": success_rate,
                        "threshold": 95,
                        "status": "below_threshold",
                    },
                    EventPriority.HIGH if success_rate < 90 else EventPriority.MEDIUM,
                )
                detected.append(event)

            if compliance_pending > 0:
                event = self.create_event(
                    EventType.COMPLIANCE_VIOLATION,
                    "compliance_monitor",
                    {
                        "pending_audits": compliance_pending,
                        "pending_regions": pending_regions,
                        "status": "action_required",
                    },
                    EventPriority.CRITICAL,
                )
                detected.append(event)

            if opt_out_trend > 5:  # 5% trend increase
                event = self.create_event(
                    EventType.OPTIMIZATION_OPPORTUNITY,
                    "engagement_monitor",
                    {
                        "metric": "opt_out_trend",
                        "value": opt_out_trend,
                        "status": "accelerating",
                    },
                    EventPriority.HIGH,
                )
                detected.append(event)

        except Exception as e:
            print(f"Error in event detection: {e}")

        return detected

    def evaluate_events(self, events: List[GovernanceEvent]) -> Dict[str, Any]:
        """
        Evaluation Phase: Analyze events and determine appropriate responses
        Returns: Evaluation results and recommendations
        """
        evaluation = {
            "total_events": len(events),
            "critical_events": 0,
            "high_priority_events": 0,
            "triggered_scenarios": [],
            "recommendations": [],
        }

        try:
            # Build strategic goals and risk scenarios
            strategic_goals = self.foresight_service.build_strategic_goals()
            risk_scenarios = self.foresight_service.generate_risk_scenarios(strategic_goals)

            for event in events:
                if event.priority == EventPriority.CRITICAL:
                    evaluation["critical_events"] += 1
                elif event.priority == EventPriority.HIGH:
                    evaluation["high_priority_events"] += 1

                # Map events to scenarios
                if event.event_type == EventType.COMPLIANCE_VIOLATION:
                    for scenario in risk_scenarios:
                        if "compliance" in scenario.name.lower():
                            evaluation["triggered_scenarios"].append(
                                {
                                    "scenario_id": scenario.scenario_id,
                                    "name": scenario.name,
                                    "probability": scenario.probability,
                                    "mitigation": scenario.mitigation_actions,
                                }
                            )

                # Generate recommendations
                if event.event_type == EventType.METRIC_UPDATE:
                    evaluation["recommendations"].append(
                        {
                            "action": "adjust_delivery_parameters",
                            "reason": event.data.get("status"),
                            "priority": event.priority.value,
                        }
                    )

        except Exception as e:
            print(f"Error in event evaluation: {e}")

        return evaluation

    def make_decisions(self, evaluation: Dict[str, Any]) -> List[Workflow]:
        """
        Decision Phase: Decide which workflows to execute
        Returns: List of workflows to execute
        """
        workflows_to_execute = []

        try:
            # Decision logic based on evaluation
            if evaluation["critical_events"] > 0:
                # High-priority workflow for critical issues
                workflow = self.create_workflow(
                    name="Critical Issue Response",
                    description="Handle critical governance issues",
                    trigger_event="critical_event",
                    priority=EventPriority.CRITICAL,
                )

                self.add_workflow_step(
                    workflow.workflow_id, "escalate_alerts", "notification", {"targets": ["admin"]}
                )
                self.add_workflow_step(
                    workflow.workflow_id,
                    "evaluate_mitigation",
                    "ai_evaluation",
                    {"scenario_count": len(evaluation["triggered_scenarios"])},
                )

                workflows_to_execute.append(workflow)

            if evaluation["high_priority_events"] > 0:
                # Standard workflow for medium issues
                workflow = self.create_workflow(
                    name="Optimization Workflow",
                    description="Optimize governance metrics",
                    trigger_event="optimization_event",
                    priority=EventPriority.HIGH,
                )

                self.add_workflow_step(
                    workflow.workflow_id,
                    "analyze_metrics",
                    "ai_evaluation",
                    {"metrics": ["delivery_rate", "opt_out_trend"]},
                )
                self.add_workflow_step(
                    workflow.workflow_id,
                    "apply_adjustments",
                    "policy_adjustment",
                    {"adjustments": evaluation["recommendations"]},
                )

                workflows_to_execute.append(workflow)

        except Exception as e:
            print(f"Error in decision making: {e}")

        return workflows_to_execute

    def execute_workflows(self, workflows: List[Workflow]) -> Tuple[int, List[str]]:
        """
        Execution Phase: Execute selected workflows
        Returns: (success_count, workflow_ids)
        """
        success_count = 0
        executed_ids = []

        for workflow in workflows:
            try:
                workflow.status = WorkflowStatus.RUNNING
                workflow.started_at = datetime.utcnow().isoformat()
                workflow.execution_count += 1

                start_time = time.time()

                # Execute each step
                for step in workflow.steps:
                    step.status = WorkflowStatus.RUNNING
                    step.executed_at = datetime.utcnow().isoformat()

                    # Simulate step execution
                    time.sleep(0.1)  # Simulate work
                    step.outputs = {"result": "success", "timestamp": datetime.utcnow().isoformat()}
                    step.status = WorkflowStatus.COMPLETED
                    step.duration_seconds = time.time() - start_time

                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.utcnow().isoformat()
                workflow.success_count += 1
                success_count += 1
                executed_ids.append(workflow.workflow_id)

                self.total_workflows_triggered += 1

            except Exception as e:
                workflow.status = WorkflowStatus.FAILED
                workflow.failure_count += 1
                print(f"Workflow execution error: {e}")

        return success_count, executed_ids

    def collect_feedback(self) -> Dict[str, Any]:
        """
        Feedback Phase: Collect results and metrics
        Returns: Feedback data
        """
        try:
            success_rate, _, _ = self.foresight_service.load_delivery_metrics()
            pending_count, _ = self.foresight_service.load_compliance_status()

            return {
                "delivery_success_rate": success_rate,
                "compliance_status": "pending" if pending_count > 0 else "clear",
                "pending_audits": pending_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"Error collecting feedback: {e}")
            return {}

    def run_control_loop_cycle(self) -> ControlLoopCycle:
        """
        Execute one complete control loop cycle
        Returns: Cycle summary
        """
        self.last_cycle_number += 1
        cycle_id = f"cycle_{uuid.uuid4().hex[:12]}"
        cycle = ControlLoopCycle(
            cycle_id=cycle_id,
            cycle_number=self.last_cycle_number,
            phase="detection",
        )

        start_time = time.time()

        try:
            # Phase 1: Detection
            cycle.phase = "detection"
            detected_events = self.detect_events()
            cycle.record_event_processing(len(detected_events))
            self.total_events_processed += len(detected_events)

            # Phase 2: Evaluation
            cycle.phase = "evaluation"
            evaluation = self.evaluate_events(detected_events)

            # Phase 3: Decision
            cycle.phase = "decision"
            workflows = self.make_decisions(evaluation)
            cycle.record_decision(len(workflows))

            # Phase 4: Execution
            cycle.phase = "execution"
            success_count, executed_ids = self.execute_workflows(workflows)
            cycle.record_workflow_trigger(success_count)

            # Phase 5: Feedback
            cycle.phase = "feedback"
            feedback = self.collect_feedback()
            cycle.metrics = feedback

            cycle.status = "completed"
            cycle.complete_cycle(time.time() - start_time)
            self.total_cycles_executed += 1

        except Exception as e:
            cycle.add_error(str(e))
            cycle.status = "failed"

        self.cycles.append(cycle)
        return cycle

    def get_control_loop_status(self) -> Dict[str, Any]:
        """Get current control loop status"""
        recent_cycles = self.cycles[-5:] if self.cycles else []

        return {
            "is_active": self.control_loop_active,
            "total_cycles_executed": self.total_cycles_executed,
            "total_events_processed": self.total_events_processed,
            "total_workflows_triggered": self.total_workflows_triggered,
            "recent_cycles": [cycle.to_dict() for cycle in recent_cycles],
            "workflow_count": len(self.workflows),
            "event_queue_size": len(self.event_queue),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        workflow = self.workflows.get(workflow_id)
        return workflow.to_dict() if workflow else None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        return [wf.to_dict() for wf in self.workflows.values()]
