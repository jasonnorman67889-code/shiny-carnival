"""
Phase 2: Workflow and Control Loop Data Models

Defines the data structures for workflow orchestration, event processing,
and adaptive governance control loops.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum
import json


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class EventType(Enum):
    """Types of governance events"""
    METRIC_UPDATE = "metric_update"
    ALERT_TRIGGERED = "alert_triggered"
    SCENARIO_DETECTED = "scenario_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    DELIVERY_FAILURE = "delivery_failure"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    GOVERNANCE_ADAPTATION = "governance_adaptation"
    CONTROL_LOOP_CYCLE = "control_loop_cycle"


class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: str
    name: str
    description: str
    action_type: str  # "ai_evaluation", "notification", "policy_adjustment", "metric_collection", etc.
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    executed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "executed_at": self.executed_at,
        }


@dataclass
class Workflow:
    """Represents a complete governance workflow"""
    workflow_id: str
    name: str
    description: str
    trigger_event: str  # Event type that triggers this workflow
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    priority: EventPriority = EventPriority.MEDIUM
    created_at: str = field(default_factory=utc_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    def add_step(self, step: WorkflowStep) -> None:
        """Add a workflow step"""
        self.steps.append(step)

    def get_status_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary"""
        total_duration = sum(step.duration_seconds for step in self.steps)
        completed_steps = sum(1 for step in self.steps if step.status == WorkflowStatus.COMPLETED)
        failed_steps = sum(1 for step in self.steps if step.status == WorkflowStatus.FAILED)

        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "total_steps": len(self.steps),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "total_duration_seconds": total_duration,
            "execution_count": self.execution_count,
            "success_rate": (
                self.success_count / self.execution_count * 100 if self.execution_count > 0 else 0
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "trigger_event": self.trigger_event,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "summary": self.get_status_summary(),
        }


@dataclass
class GovernanceEvent:
    """Represents a governance event in the control loop"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    source: str  # Which service/component generated the event
    data: Dict[str, Any]
    created_at: str = field(default_factory=utc_now_iso)
    processed_at: Optional[str] = None
    triggered_workflows: List[str] = field(default_factory=list)
    resolution_status: str = "pending"  # "pending", "resolved", "escalated"

    def mark_processed(self) -> None:
        """Mark event as processed"""
        self.processed_at = utc_now_iso()

    def add_triggered_workflow(self, workflow_id: str) -> None:
        """Add a workflow triggered by this event"""
        self.triggered_workflows.append(workflow_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "source": self.source,
            "data": self.data,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "triggered_workflows": self.triggered_workflows,
            "resolution_status": self.resolution_status,
        }


@dataclass
class ControlLoopCycle:
    """Represents one cycle of the control loop"""
    cycle_id: str
    cycle_number: int
    phase: str  # "detection", "evaluation", "decision", "execution", "feedback"
    events_processed: int = 0
    workflows_triggered: int = 0
    decisions_made: int = 0
    adaptations_applied: int = 0
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=utc_now_iso)
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)

    def record_event_processing(self, count: int) -> None:
        """Record number of events processed"""
        self.events_processed += count

    def record_workflow_trigger(self, count: int) -> None:
        """Record workflows triggered"""
        self.workflows_triggered += count

    def record_decision(self, count: int) -> None:
        """Record decisions made"""
        self.decisions_made += count

    def record_adaptation(self, count: int) -> None:
        """Record adaptations applied"""
        self.adaptations_applied += count

    def add_error(self, error_msg: str) -> None:
        """Add error to log"""
        self.error_log.append(error_msg)

    def complete_cycle(self, duration_seconds: float) -> None:
        """Mark cycle as complete"""
        self.status = "completed"
        self.duration_seconds = duration_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "cycle_number": self.cycle_number,
            "phase": self.phase,
            "events_processed": self.events_processed,
            "workflows_triggered": self.workflows_triggered,
            "decisions_made": self.decisions_made,
            "adaptations_applied": self.adaptations_applied,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "status": self.status,
            "metrics": self.metrics,
            "error_count": len(self.error_log),
        }


@dataclass
class AIModelConfig:
    """Configuration for an AI model in the gateway"""
    model_id: str
    model_name: str
    model_type: str  # "foresight", "orchestration", "governance", "adaptive"
    endpoint_url: str
    api_key: str
    is_active: bool = True
    model_version: str = "1.0"
    capabilities: List[str] = field(default_factory=list)
    rate_limit: int = 1000  # requests per minute
    timeout_seconds: int = 30
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "endpoint_url": self.endpoint_url,
            "is_active": self.is_active,
            "model_version": self.model_version,
            "capabilities": self.capabilities,
            "rate_limit": self.rate_limit,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }


@dataclass
class AIGateway:
    """Manages AI models and inference requests"""
    gateway_id: str
    name: str
    description: str
    models: Dict[str, AIModelConfig] = field(default_factory=dict)
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    created_at: str = field(default_factory=utc_now_iso)

    def register_model(self, model: AIModelConfig) -> None:
        """Register an AI model"""
        self.models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[AIModelConfig]:
        """Get a model by ID"""
        return self.models.get(model_id)

    def get_active_models(self) -> List[AIModelConfig]:
        """Get all active models"""
        return [m for m in self.models.values() if m.is_active]

    def record_request(self, success: bool, latency_ms: float) -> None:
        """Record an inference request"""
        self.request_count += 1
        self.total_latency_ms += latency_ms
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_average_latency_ms(self) -> float:
        """Get average latency"""
        return self.total_latency_ms / self.request_count if self.request_count > 0 else 0.0

    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        return (self.success_count / self.request_count * 100) if self.request_count > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gateway_id": self.gateway_id,
            "name": self.name,
            "description": self.description,
            "active_models": len(self.get_active_models()),
            "total_models": len(self.models),
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "average_latency_ms": self.get_average_latency_ms(),
            "success_rate": self.get_success_rate(),
            "created_at": self.created_at,
        }
