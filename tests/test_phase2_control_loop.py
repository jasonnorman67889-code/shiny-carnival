"""
Phase 2: Control Loop & Gateway Tests

Comprehensive test suite for Phase 2 implementation including:
- Control Loop Service orchestration and cycles
- Workflow management and execution
- AI Gateway service and model routing
- Event detection and processing
"""

import json
import os
import tempfile
import pytest
from datetime import datetime, timedelta

from models.workflow_models import (
    Workflow, WorkflowStep, WorkflowStatus, EventType, EventPriority,
    GovernanceEvent, ControlLoopCycle, AIModelConfig, AIGateway
)
from services.control_loop_service import ControlLoopService
from services.ai_gateway_service import AIGatewayService


class TestWorkflowModel:
    """Test Workflow data model"""

    def test_workflow_creation(self):
        """Test creating a workflow"""
        workflow = Workflow(
            workflow_id="wf_001",
            name="Test Workflow",
            description="Test description",
            trigger_event="test_event"
        )
        
        assert workflow.workflow_id == "wf_001"
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.steps) == 0

    def test_add_workflow_step(self):
        """Test adding steps to a workflow"""
        workflow = Workflow(
            workflow_id="wf_001",
            name="Test Workflow",
            description="Test description",
            trigger_event="test_event"
        )
        
        step = WorkflowStep(
            step_id="step_001",
            name="Test Step",
            description="Test step description",
            action_type="ai_evaluation"
        )
        
        workflow.add_step(step)
        
        assert len(workflow.steps) == 1
        assert workflow.steps[0].step_id == "step_001"

    def test_workflow_status_summary(self):
        """Test workflow status summary"""
        workflow = Workflow(
            workflow_id="wf_001",
            name="Test Workflow",
            description="Test description",
            trigger_event="test_event"
        )
        
        step1 = WorkflowStep(
            step_id="step_001",
            name="Step 1",
            description="Step 1",
            action_type="ai_evaluation",
            status=WorkflowStatus.COMPLETED,
            duration_seconds=5.0
        )
        step2 = WorkflowStep(
            step_id="step_002",
            name="Step 2",
            description="Step 2",
            action_type="policy_adjustment",
            status=WorkflowStatus.COMPLETED,
            duration_seconds=3.0
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        summary = workflow.get_status_summary()
        
        assert summary["total_steps"] == 2
        assert summary["completed_steps"] == 2
        assert summary["total_duration_seconds"] == 8.0

    def test_workflow_execution_tracking(self):
        """Test workflow execution tracking"""
        workflow = Workflow(
            workflow_id="wf_001",
            name="Test Workflow",
            description="Test description",
            trigger_event="test_event"
        )
        
        assert workflow.execution_count == 0
        assert workflow.success_count == 0
        
        workflow.execution_count = 5
        workflow.success_count = 4
        workflow.failure_count = 1
        
        summary = workflow.get_status_summary()
        assert summary["execution_count"] == 5
        assert summary["success_rate"] == 80.0


class TestGovernanceEvent:
    """Test GovernanceEvent model"""

    def test_event_creation(self):
        """Test creating a governance event"""
        event = GovernanceEvent(
            event_id="evt_001",
            event_type=EventType.METRIC_UPDATE,
            priority=EventPriority.HIGH,
            source="test_source",
            data={"metric": "test", "value": 95}
        )
        
        assert event.event_id == "evt_001"
        assert event.event_type == EventType.METRIC_UPDATE
        assert event.priority == EventPriority.HIGH
        assert event.resolution_status == "pending"

    def test_event_processing(self):
        """Test event processing tracking"""
        event = GovernanceEvent(
            event_id="evt_001",
            event_type=EventType.METRIC_UPDATE,
            priority=EventPriority.MEDIUM,
            source="test_source",
            data={}
        )
        
        assert event.processed_at is None
        event.mark_processed()
        assert event.processed_at is not None

    def test_event_workflow_triggering(self):
        """Test workflow triggering from events"""
        event = GovernanceEvent(
            event_id="evt_001",
            event_type=EventType.COMPLIANCE_VIOLATION,
            priority=EventPriority.CRITICAL,
            source="compliance_monitor",
            data={}
        )
        
        assert len(event.triggered_workflows) == 0
        event.add_triggered_workflow("wf_001")
        event.add_triggered_workflow("wf_002")
        assert len(event.triggered_workflows) == 2


class TestControlLoopCycle:
    """Test ControlLoopCycle model"""

    def test_cycle_creation(self):
        """Test creating a control loop cycle"""
        cycle = ControlLoopCycle(
            cycle_id="cycle_001",
            cycle_number=1,
            phase="detection"
        )
        
        assert cycle.cycle_id == "cycle_001"
        assert cycle.cycle_number == 1
        assert cycle.events_processed == 0
        assert cycle.status == "in_progress"

    def test_cycle_event_tracking(self):
        """Test event tracking in cycles"""
        cycle = ControlLoopCycle(
            cycle_id="cycle_001",
            cycle_number=1,
            phase="detection"
        )
        
        cycle.record_event_processing(5)
        cycle.record_workflow_trigger(2)
        cycle.record_decision(3)
        cycle.record_adaptation(1)
        
        assert cycle.events_processed == 5
        assert cycle.workflows_triggered == 2
        assert cycle.decisions_made == 3
        assert cycle.adaptations_applied == 1

    def test_cycle_completion(self):
        """Test cycle completion tracking"""
        cycle = ControlLoopCycle(
            cycle_id="cycle_001",
            cycle_number=1,
            phase="detection"
        )
        
        assert cycle.status == "in_progress"
        cycle.complete_cycle(2.5)
        
        assert cycle.status == "completed"
        assert cycle.duration_seconds == 2.5


class TestControlLoopService:
    """Test ControlLoopService"""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample data files
            email_log_file = os.path.join(tmpdir, "email_status_log.json")
            compliance_file = os.path.join(tmpdir, "compliance_report.json")
            opt_out_file = os.path.join(tmpdir, "opt_out_history.json")
            users_file = os.path.join(tmpdir, "users.csv")
            
            # Write sample email logs
            with open(email_log_file, "w") as f:
                f.write('{"recipient_email": "user1@test.com", "delivery_status": "SUCCESS", "region": "USA"}\n')
                f.write('{"recipient_email": "user2@test.com", "delivery_status": "SUCCESS", "region": "USA"}\n')
            
            # Write sample compliance report
            with open(compliance_file, "w") as f:
                json.dump({
                    "regional_audit": [
                        {"region": "USA", "status": "Compliant"},
                        {"region": "EUROPE", "status": "Pending"}
                    ]
                }, f)
            
            # Write sample opt-out history
            with open(opt_out_file, "w") as f:
                json.dump([
                    {"email": "test@test.com", "timestamp": datetime.utcnow().isoformat()}
                ], f)
            
            # Write sample users CSV
            with open(users_file, "w") as f:
                f.write("email,name,region,channel\n")
                f.write("user@test.com,Test User,USA,email\n")
            
            yield tmpdir

    def test_control_loop_service_initialization(self, temp_data_dir):
        """Test service initialization"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        assert service.control_loop_active == False
        assert service.total_cycles_executed == 0
        assert len(service.workflows) == 0
        assert len(service.event_queue) == 0

    def test_workflow_creation(self, temp_data_dir):
        """Test workflow creation"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        workflow = service.create_workflow(
            name="Test Workflow",
            description="Test description",
            trigger_event="test_event",
            priority=EventPriority.HIGH
        )
        
        assert workflow.name == "Test Workflow"
        assert workflow.workflow_id in service.workflows

    def test_event_creation(self, temp_data_dir):
        """Test event creation"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        event = service.create_event(
            event_type=EventType.METRIC_UPDATE,
            source="test_source",
            data={"value": 95},
            priority=EventPriority.HIGH
        )
        
        assert event.event_type == EventType.METRIC_UPDATE
        assert len(service.event_queue) == 1

    def test_event_detection(self, temp_data_dir):
        """Test event detection from real data"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        events = service.detect_events()
        # Should detect at least compliance event
        assert len(events) > 0

    def test_event_evaluation(self, temp_data_dir):
        """Test event evaluation"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        events = [
            GovernanceEvent(
                event_id="evt_001",
                event_type=EventType.COMPLIANCE_VIOLATION,
                priority=EventPriority.CRITICAL,
                source="compliance",
                data={}
            )
        ]
        
        evaluation = service.evaluate_events(events)
        assert evaluation["total_events"] == 1
        assert evaluation["critical_events"] == 1

    def test_decision_making(self, temp_data_dir):
        """Test decision making from evaluation"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        evaluation = {
            "total_events": 1,
            "critical_events": 1,
            "high_priority_events": 0,
            "triggered_scenarios": [],
            "recommendations": []
        }
        
        workflows = service.make_decisions(evaluation)
        assert len(workflows) > 0

    def test_workflow_execution(self, temp_data_dir):
        """Test workflow execution"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        workflow = service.create_workflow(
            name="Test Workflow",
            description="Test",
            trigger_event="test",
            priority=EventPriority.MEDIUM
        )
        
        service.add_workflow_step(
            workflow.workflow_id,
            "test_step",
            "ai_evaluation"
        )
        
        success_count, executed_ids = service.execute_workflows([workflow])
        
        assert success_count == 1
        assert workflow.workflow_id in executed_ids
        assert workflow.status == WorkflowStatus.COMPLETED

    def test_control_loop_cycle(self, temp_data_dir):
        """Test full control loop cycle"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        cycle = service.run_control_loop_cycle()
        
        assert cycle.cycle_number == 1
        assert cycle.status == "completed"
        assert service.total_cycles_executed == 1

    def test_control_loop_status(self, temp_data_dir):
        """Test control loop status reporting"""
        service = ControlLoopService(data_dir=temp_data_dir)
        
        # Run a cycle
        service.run_control_loop_cycle()
        
        status = service.get_control_loop_status()
        
        assert status["total_cycles_executed"] >= 1
        assert "recent_cycles" in status


class TestAIModelConfig:
    """Test AI Model Configuration"""

    def test_model_creation(self):
        """Test creating an AI model config"""
        model = AIModelConfig(
            model_id="model_001",
            model_name="Test Model",
            model_type="foresight",
            endpoint_url="http://localhost:5001",
            api_key="test_key"
        )
        
        assert model.model_id == "model_001"
        assert model.is_active == True
        assert model.model_type == "foresight"

    def test_model_capabilities(self):
        """Test model capabilities"""
        model = AIModelConfig(
            model_id="model_001",
            model_name="Test Model",
            model_type="governance",
            endpoint_url="http://localhost:5003",
            api_key="test_key",
            capabilities=["compliance_checking", "ethical_validation"]
        )
        
        assert "compliance_checking" in model.capabilities
        assert len(model.capabilities) == 2


class TestAIGatewayService:
    """Test AI Gateway Service"""

    def test_gateway_initialization(self):
        """Test gateway initialization"""
        gateway = AIGatewayService()
        
        assert gateway.gateway.gateway_id == "gateway_001"
        assert len(gateway.gateway.get_active_models()) == 4  # Should have 4 default models

    def test_model_retrieval_by_type(self):
        """Test getting models by type"""
        gateway = AIGatewayService()
        
        foresight_model = gateway.get_model_by_type("foresight")
        assert foresight_model is not None
        assert foresight_model.model_type == "foresight"

    def test_models_by_capability(self):
        """Test getting models by capability"""
        gateway = AIGatewayService()
        
        models = gateway.get_models_by_capability("compliance_checking")
        assert len(models) > 0
        assert all("compliance_checking" in m.capabilities for m in models)

    def test_request_routing(self):
        """Test request routing to models"""
        gateway = AIGatewayService()
        
        model, reason = gateway.route_request("scenario_generation", {})
        assert model is not None
        assert model.model_type == "foresight"

    def test_inference_execution(self):
        """Test executing inference"""
        gateway = AIGatewayService()
        
        result = gateway.execute_inference("scenario_generation", {})
        
        assert result["status"] == "success"
        assert "model_used" in result
        assert result["latency_ms"] > 0

    def test_batch_inference(self):
        """Test batch inference execution"""
        gateway = AIGatewayService()
        
        requests = [
            {"task_type": "scenario_generation", "data": {}},
            {"task_type": "workflow_planning", "data": {}},
            {"task_type": "compliance_check", "data": {}},
        ]
        
        results, stats = gateway.batch_inference(requests)
        
        assert stats["total"] == 3
        assert stats["successful"] == 3
        assert len(results) == 3

    def test_gateway_status(self):
        """Test gateway status reporting"""
        gateway = AIGatewayService()
        
        status = gateway.get_gateway_status()
        
        assert status["gateway_id"] == "gateway_001"
        assert status["active_models"] == 4
        assert "inference_metrics" in status

    def test_model_enable_disable(self):
        """Test enabling/disabling models"""
        gateway = AIGatewayService()
        
        model_id = "foresight_001"
        assert gateway.disable_model(model_id) == True
        
        model = gateway.gateway.get_model(model_id)
        assert model.is_active == False
        
        assert gateway.enable_model(model_id) == True
        assert model.is_active == True

    def test_gateway_request_metrics(self):
        """Test gateway request metrics tracking"""
        gateway = AIGatewayService()
        
        initial_count = gateway.gateway.request_count
        
        gateway.execute_inference("compliance_check", {})
        gateway.execute_inference("workflow_planning", {})
        
        assert gateway.gateway.request_count == initial_count + 2
        assert gateway.gateway.success_count > initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
