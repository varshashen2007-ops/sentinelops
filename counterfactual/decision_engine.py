from counterfactual.decision import (
    CounterfactualDecision,
    DecisionEvaluation,
)
from counterfactual.model import CounterfactualPrediction


class CounterfactualDecisionEngine:
    """
    Deterministically compares counterfactual recovery predictions.

    The engine does not execute, approve, or directly recommend a
    Kubernetes operation. It evaluates the supplied predictions using
    explicit scoring rules and exposes the basis and trade-offs.
    """

    _STATUS_SCORES: dict[str, float] = {
        "likely_recovered": 1.00,
        "potentially_recovered": 0.85,
        "temporary_recovery": 0.65,
        "uncertain": 0.35,
        "insufficient_information": 0.10,
    }

    def evaluate(
        self,
        incident_id: str,
        predictions: list[CounterfactualPrediction],
    ) -> CounterfactualDecision:
        evaluations = [
            self._evaluate_prediction(prediction)
            for prediction in predictions
        ]

        selected_action_type = self._select_action(evaluations)

        return CounterfactualDecision(
            incident_id=incident_id,
            evaluations=evaluations,
            selected_action_type=selected_action_type,
        )

    def _evaluate_prediction(
        self,
        prediction: CounterfactualPrediction,
    ) -> DecisionEvaluation:
        status_score = self._STATUS_SCORES.get(
            prediction.predicted_status,
            0.10,
        )

        confidence = max(
            0.0,
            min(1.0, prediction.confidence),
        )

        decision_score = round(
            (status_score * 0.60) + (confidence * 0.40),
            4,
        )

        tradeoffs = self._build_tradeoffs(prediction)

        basis = (
            f"Status score={status_score:.2f}; "
            f"prediction confidence={confidence:.2f}; "
            f"combined deterministic score={decision_score:.4f}."
        )

        return DecisionEvaluation(
            prediction=prediction,
            decision_score=decision_score,
            recommendation_basis=basis,
            tradeoffs=tradeoffs,
        )

    @classmethod
    def _select_action(
        cls,
        evaluations: list[DecisionEvaluation],
    ) -> str | None:
        if not evaluations:
            return None

        selected = max(
            evaluations,
            key=lambda evaluation: evaluation.decision_score,
        )

        return selected.prediction.action.action_type

    @staticmethod
    def _build_tradeoffs(
        prediction: CounterfactualPrediction,
    ) -> list[str]:
        tradeoffs = list(prediction.supporting_factors)

        status = prediction.predicted_status

        if status == "likely_recovered":
            tradeoffs.append(
                "Prediction indicates a strong recovery signal, "
                "but the outcome remains hypothetical."
            )

        elif status == "potentially_recovered":
            tradeoffs.append(
                "Potential recovery is indicated, but effectiveness "
                "depends on the incident conditions."
            )

        elif status == "temporary_recovery":
            tradeoffs.append(
                "Recovery may be temporary and the underlying failure "
                "condition may remain."
            )

        elif status == "uncertain":
            tradeoffs.append(
                "Available incident evidence provides limited support "
                "for this recovery strategy."
            )

        else:
            tradeoffs.append(
                "Insufficient information is available for a reliable "
                "counterfactual evaluation."
            )

        return tradeoffs
