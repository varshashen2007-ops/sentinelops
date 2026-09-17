from dataclasses import dataclass, field
from typing import Any

from counterfactual.model import CounterfactualPrediction


@dataclass
class DecisionEvaluation:
    """
    Evaluation of a counterfactual recovery strategy.

    The evaluation compares a predicted recovery outcome using
    deterministic factors such as prediction confidence and
    predicted status.

    This evaluation does not execute or approve any Kubernetes action.
    """

    prediction: CounterfactualPrediction
    decision_score: float
    recommendation_basis: str
    tradeoffs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.prediction.to_dict(),
            "decision_score": self.decision_score,
            "recommendation_basis": self.recommendation_basis,
            "tradeoffs": list(self.tradeoffs),
        }


@dataclass
class CounterfactualDecision:
    """
    Comparison of multiple counterfactual recovery strategies.

    The result preserves every evaluated strategy and identifies the
    highest-scoring strategy based on deterministic decision rules.
    """

    incident_id: str
    evaluations: list[DecisionEvaluation] = field(default_factory=list)
    selected_action_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "evaluations": [
                evaluation.to_dict()
                for evaluation in self.evaluations
            ],
            "selected_action_type": self.selected_action_type,
        }