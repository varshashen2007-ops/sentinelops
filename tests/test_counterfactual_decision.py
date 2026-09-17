from counterfactual.decision_engine import CounterfactualDecisionEngine
from counterfactual.model import (
    CounterfactualAction,
    CounterfactualPrediction,
)


def make_prediction(
    action_type: str,
    status: str,
    confidence: float,
) -> CounterfactualPrediction:
    return CounterfactualPrediction(
        action=CounterfactualAction(action_type=action_type),
        predicted_status=status,
        predicted_effect="Test effect",
        confidence=confidence,
        rationale="Test rationale",
        supporting_factors=["Test factor"],
    )


def test_evaluate_returns_all_predictions():
    engine = CounterfactualDecisionEngine()

    predictions = [
        make_prediction("restart", "temporary_recovery", 0.70),
        make_prediction("rollback", "likely_recovered", 0.80),
    ]

    result = engine.evaluate(
        incident_id="INC-001",
        predictions=predictions,
    )

    assert result.incident_id == "INC-001"
    assert len(result.evaluations) == 2


def test_likely_recovered_scores_higher_than_uncertain():
    engine = CounterfactualDecisionEngine()

    predictions = [
        make_prediction("restart", "uncertain", 0.90),
        make_prediction("rollback", "likely_recovered", 0.80),
    ]

    result = engine.evaluate(
        incident_id="INC-002",
        predictions=predictions,
    )

    scores = {
        evaluation.prediction.action.action_type:
        evaluation.decision_score
        for evaluation in result.evaluations
    }

    assert scores["rollback"] > scores["restart"]


def test_selected_action_is_highest_scoring_action():
    engine = CounterfactualDecisionEngine()

    predictions = [
        make_prediction("restart", "temporary_recovery", 0.70),
        make_prediction("increase_memory", "likely_recovered", 0.90),
        make_prediction("scale", "uncertain", 0.80),
    ]

    result = engine.evaluate(
        incident_id="INC-003",
        predictions=predictions,
    )

    assert result.selected_action_type == "increase_memory"


def test_empty_predictions_selects_no_action():
    engine = CounterfactualDecisionEngine()

    result = engine.evaluate(
        incident_id="INC-004",
        predictions=[],
    )

    assert result.evaluations == []
    assert result.selected_action_type is None


def test_unknown_status_uses_conservative_score():
    engine = CounterfactualDecisionEngine()

    prediction = make_prediction(
        "restart",
        "unknown_status",
        0.50,
    )

    result = engine.evaluate(
        incident_id="INC-005",
        predictions=[prediction],
    )

    assert result.evaluations[0].decision_score == 0.26


def test_confidence_is_clamped():
    engine = CounterfactualDecisionEngine()

    high = make_prediction(
        "restart",
        "likely_recovered",
        2.0,
    )

    low = make_prediction(
        "rollback",
        "likely_recovered",
        -1.0,
    )

    result = engine.evaluate(
        incident_id="INC-006",
        predictions=[high, low],
    )

    assert result.evaluations[0].prediction.confidence == 2.0
    assert result.evaluations[0].decision_score == 1.0

    assert result.evaluations[1].prediction.confidence == -1.0
    assert result.evaluations[1].decision_score == 0.6


def test_tradeoffs_are_exposed():
    engine = CounterfactualDecisionEngine()

    prediction = make_prediction(
        "restart",
        "temporary_recovery",
        0.70,
    )

    result = engine.evaluate(
        incident_id="INC-007",
        predictions=[prediction],
    )

    tradeoffs = result.evaluations[0].tradeoffs

    assert "Test factor" in tradeoffs
    assert any(
        "temporary" in tradeoff.lower()
        for tradeoff in tradeoffs
    )


def test_decision_serializes():
    engine = CounterfactualDecisionEngine()

    prediction = make_prediction(
        "increase_memory",
        "likely_recovered",
        0.90,
    )

    result = engine.evaluate(
        incident_id="INC-008",
        predictions=[prediction],
    )

    data = result.to_dict()

    assert data["incident_id"] == "INC-008"
    assert len(data["evaluations"]) == 1
    assert data["selected_action_type"] == "increase_memory"
