"""
Phase 2: AI Gateway Service

Manages AI model routing, inference requests, and adaptive model selection.
Provides a unified interface to multiple AI services (Foresight, Orchestration, Governance).
"""

import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import json

from models.workflow_models import AIModelConfig, AIGateway


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIGatewayService:
    """
    AI Gateway for managing multiple AI models and inference requests.
    Routes requests to appropriate models based on task type and availability.
    """

    def __init__(self, gateway_id: str = "gateway_001"):
        self.gateway = AIGateway(
            gateway_id=gateway_id,
            name="Governance AI Gateway",
            description="Central gateway for all governance AI services",
        )

        # Initialize default AI models
        self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """Initialize default AI models for governance"""

        # Foresight AI - Predictive analytics and scenario forecasting
        foresight_model = AIModelConfig(
            model_id="foresight_001",
            model_name="Foresight Predictor",
            model_type="foresight",
            endpoint_url="http://localhost:5001/foresight",
            api_key="sk_foresight_demo",
            is_active=True,
            model_version="2.1",
            capabilities=["scenario_generation", "risk_scoring", "trend_analysis", "anomaly_detection"],
            rate_limit=1000,
            timeout_seconds=30,
        )
        self.gateway.register_model(foresight_model)

        # Orchestration AI - Workflow orchestration and decision making
        orchestration_model = AIModelConfig(
            model_id="orchestration_001",
            model_name="Orchestration Engine",
            model_type="orchestration",
            endpoint_url="http://localhost:5002/orchestrate",
            api_key="sk_orchestration_demo",
            is_active=True,
            model_version="1.8",
            capabilities=["workflow_planning", "resource_allocation", "decision_making", "optimization"],
            rate_limit=500,
            timeout_seconds=45,
        )
        self.gateway.register_model(orchestration_model)

        # Governance AI - Compliance and ethical governance
        governance_model = AIModelConfig(
            model_id="governance_001",
            model_name="Governance Guardian",
            model_type="governance",
            endpoint_url="http://localhost:5003/govern",
            api_key="sk_governance_demo",
            is_active=True,
            model_version="1.5",
            capabilities=["compliance_checking", "policy_enforcement", "ethical_validation", "audit_logging"],
            rate_limit=800,
            timeout_seconds=60,
        )
        self.gateway.register_model(governance_model)

        # Adaptive AI - Real-time learning and adaptation
        adaptive_model = AIModelConfig(
            model_id="adaptive_001",
            model_name="Adaptive Intelligence",
            model_type="adaptive",
            endpoint_url="http://localhost:5004/adapt",
            api_key="sk_adaptive_demo",
            is_active=True,
            model_version="1.2",
            capabilities=["model_retraining", "feedback_integration", "parameter_tuning", "self_healing"],
            rate_limit=300,
            timeout_seconds=90,
        )
        self.gateway.register_model(adaptive_model)

    def get_model_by_type(self, model_type: str) -> Optional[AIModelConfig]:
        """Get the first active model of a given type"""
        for model in self.gateway.get_active_models():
            if model.model_type == model_type:
                return model
        return None

    def get_models_by_capability(self, capability: str) -> List[AIModelConfig]:
        """Get all active models that have a specific capability"""
        return [
            model
            for model in self.gateway.get_active_models()
            if capability in model.capabilities
        ]

    def route_request(
        self, task_type: str, request_data: Dict[str, Any]
    ) -> Tuple[Optional[AIModelConfig], str]:
        """
        Route an inference request to the appropriate AI model
        Returns: (model_config, routing_reason)
        """

        # Route based on task type
        if task_type == "scenario_generation":
            model = self.get_model_by_type("foresight")
            return model, "foresight_model_selected"

        elif task_type == "workflow_planning":
            model = self.get_model_by_type("orchestration")
            return model, "orchestration_model_selected"

        elif task_type == "compliance_check":
            model = self.get_model_by_type("governance")
            return model, "governance_model_selected"

        elif task_type == "model_adaptation":
            model = self.get_model_by_type("adaptive")
            return model, "adaptive_model_selected"

        else:
            # Default fallback routing
            active_models = self.gateway.get_active_models()
            if active_models:
                return active_models[0], "default_routing"
            return None, "no_models_available"

    def execute_inference(
        self, task_type: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an inference request through the gateway
        Returns: Inference result with metadata
        """

        result = {
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "task_type": task_type,
            "status": "executing",
            "model_used": None,
            "latency_ms": 0.0,
            "result": None,
            "error": None,
            "timestamp": utc_now_iso(),
        }

        start_time = time.time()

        try:
            # Route request to appropriate model
            model, routing_reason = self.route_request(task_type, request_data)

            if not model:
                result["status"] = "error"
                result["error"] = "No suitable AI model available"
                self.gateway.record_request(False, 0)
                return result

            result["model_used"] = {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "model_type": model.model_type,
                "routing_reason": routing_reason,
            }

            # Simulate inference execution
            # In production, this would call the actual model endpoint
            inference_result = self._simulate_inference(task_type, request_data, model)

            result["status"] = "success"
            result["result"] = inference_result

            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            result["latency_ms"] = latency_ms
            self.gateway.record_request(True, latency_ms)

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            latency_ms = (time.time() - start_time) * 1000
            result["latency_ms"] = latency_ms
            self.gateway.record_request(False, latency_ms)

        return result

    def _simulate_inference(
        self, task_type: str, request_data: Dict[str, Any], model: AIModelConfig
    ) -> Dict[str, Any]:
        """Simulate AI inference (for demonstration purposes)"""

        time.sleep(0.05)  # Simulate processing time

        if task_type == "scenario_generation":
            return {
                "scenarios": [
                    {
                        "id": "scen_1",
                        "name": "Delivery Performance Decline",
                        "probability": 0.35,
                        "impact": "high",
                    },
                    {
                        "id": "scen_2",
                        "name": "Compliance Audit Triggered",
                        "probability": 0.25,
                        "impact": "critical",
                    },
                ],
                "confidence": 0.87,
            }

        elif task_type == "workflow_planning":
            return {
                "workflow_plan": {
                    "steps": [
                        {"step": 1, "action": "detect_anomalies", "duration_seconds": 2},
                        {"step": 2, "action": "evaluate_impact", "duration_seconds": 5},
                        {"step": 3, "action": "recommend_action", "duration_seconds": 3},
                    ],
                    "estimated_duration_seconds": 10,
                    "priority": "high",
                },
                "confidence": 0.92,
            }

        elif task_type == "compliance_check":
            return {
                "compliance_status": "compliant",
                "violations": [],
                "warnings": ["High opt-out trend detected"],
                "recommendations": ["Review subscriber retention strategy"],
                "confidence": 0.95,
            }

        elif task_type == "model_adaptation":
            return {
                "adaptation_applied": True,
                "parameters_updated": ["foresight_weight", "compliance_threshold"],
                "new_metrics": {"accuracy": 0.89, "precision": 0.92},
                "confidence": 0.78,
            }

        else:
            return {"result": "inference_completed", "confidence": 0.5}

    def batch_inference(
        self, requests: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Execute multiple inference requests in batch
        Returns: (results, statistics)
        """

        results = []
        stats = {"total": len(requests), "successful": 0, "failed": 0}

        for request in requests:
            result = self.execute_inference(request["task_type"], request.get("data", {}))
            results.append(result)

            if result["status"] == "success":
                stats["successful"] += 1
            else:
                stats["failed"] += 1

        return results, stats

    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""

        return {
            "gateway_id": self.gateway.gateway_id,
            "name": self.gateway.name,
            "status": "operational",
            "active_models": len(self.gateway.get_active_models()),
            "total_models": len(self.gateway.models),
            "models": [
                {
                    "model_id": m.model_id,
                    "model_name": m.model_name,
                    "model_type": m.model_type,
                    "is_active": m.is_active,
                    "capabilities": m.capabilities,
                }
                for m in self.gateway.get_active_models()
            ],
            "inference_metrics": {
                "total_requests": self.gateway.request_count,
                "successful_requests": self.gateway.success_count,
                "failed_requests": self.gateway.error_count,
                "success_rate": f"{self.gateway.get_success_rate():.2f}%",
                "average_latency_ms": f"{self.gateway.get_average_latency_ms():.2f}",
            },
            "timestamp": utc_now_iso(),
        }

    def get_model_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a specific model"""

        model = self.gateway.get_model(model_id)
        if not model:
            return None

        return {
            "model_id": model.model_id,
            "model_name": model.model_name,
            "model_type": model.model_type,
            "is_active": model.is_active,
            "capabilities": model.capabilities,
            "rate_limit": model.rate_limit,
            "timeout_seconds": model.timeout_seconds,
            "version": model.model_version,
            "created_at": model.created_at,
        }

    def enable_model(self, model_id: str) -> bool:
        """Enable a model"""
        model = self.gateway.get_model(model_id)
        if model:
            model.is_active = True
            return True
        return False

    def disable_model(self, model_id: str) -> bool:
        """Disable a model"""
        model = self.gateway.get_model(model_id)
        if model:
            model.is_active = False
            return True
        return False
