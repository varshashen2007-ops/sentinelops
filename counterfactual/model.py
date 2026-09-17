from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CounterfactualAction:
    """
    Represents a hypothetical recovery action.

    The action is descriptive only. It does not execute any
    Kubernetes operation.
    """

    action_type: str
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "parameters": dict(self.parameters),
        }


@dataclass
class CounterfactualPrediction:
    """
    Predicted outcome of a hypothetical recovery action.

    Predictions are deterministic and explainable. They represent
    what the engine expects based on the incident characteristics,
    not an observed Kubernetes result.
    """

    action: CounterfactualAction
    predicted_status: str
    predicted_effect: str
    confidence: float
    rationale: str
    supporting_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "predicted_status": self.predicted_status,
            "predicted_effect": self.predicted_effect,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "supporting_factors": list(self.supporting_factors),
        }


@dataclass
class CounterfactualScenario:
    """
    Represents a complete what-if scenario for an incident.

    A scenario contains the incident being analyzed and one or more
    hypothetical recovery actions with their predicted outcomes.
    """

    incident_id: str
    actions: list[CounterfactualAction] = field(default_factory=list)
    predictions: list[CounterfactualPrediction] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "actions": [
                action.to_dict()
                for action in self.actions
            ],
            "predictions": [
                prediction.to_dict()
                for prediction in self.predictions
            ],
            "metadata": dict(self.metadata),
        }