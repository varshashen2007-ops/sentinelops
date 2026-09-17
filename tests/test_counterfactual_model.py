from counterfactual.model import (
    CounterfactualAction,
    CounterfactualPrediction,
    CounterfactualScenario,
)


def test_counterfactual_action_to_dict():
    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
        parameters={
            "reason": "clear application failure",
        },
    )

    result = action.to_dict()

    assert result == {
        "action_type": "restart",
        "target": "checkout-api",
        "parameters": {
            "reason": "clear application failure",
        },
    }


def test_counterfactual_action_defaults():
    action = CounterfactualAction(
        action_type="rollback",
    )

    assert action.target is None
    assert action.parameters == {}


def test_counterfactual_action_is_immutable():
    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    try:
        action.action_type = "scale"
        assert False
    except AttributeError:
        pass


def test_counterfactual_prediction_to_dict():
    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    prediction = CounterfactualPrediction(
        action=action,
        predicted_status="likely_recovered",
        predicted_effect="Application failure may clear after restart.",
        confidence=0.85,
        rationale="The incident shows repeated application failures.",
        supporting_factors=[
            "CrashLoopBackOff detected",
            "Application container repeatedly failed",
        ],
    )

    result = prediction.to_dict()

    assert result["action"]["action_type"] == "restart"
    assert result["predicted_status"] == "likely_recovered"
    assert result["confidence"] == 0.85
    assert result["supporting_factors"] == [
        "CrashLoopBackOff detected",
        "Application container repeatedly failed",
    ]


def test_counterfactual_scenario_to_dict():
    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    prediction = CounterfactualPrediction(
        action=action,
        predicted_status="likely_recovered",
        predicted_effect="Application failure may clear.",
        confidence=0.80,
        rationale="Restart targets the affected workload.",
    )

    scenario = CounterfactualScenario(
        incident_id="incident-001",
        actions=[action],
        predictions=[prediction],
        metadata={
            "simulation_type": "deterministic",
        },
    )

    result = scenario.to_dict()

    assert result["incident_id"] == "incident-001"
    assert len(result["actions"]) == 1
    assert len(result["predictions"]) == 1
    assert result["metadata"]["simulation_type"] == "deterministic"


def test_counterfactual_scenario_defaults():
    scenario = CounterfactualScenario(
        incident_id="incident-001",
    )

    assert scenario.actions == []
    assert scenario.predictions == []
    assert scenario.metadata == {}