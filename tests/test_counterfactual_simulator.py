from datetime import datetime, timezone

from counterfactual.model import CounterfactualAction
from counterfactual.simulator import CounterfactualSimulator
from models.incident import Incident
from incident_engine.dna import IncidentDNA


def make_oom_incident() -> Incident:
    return Incident(
        incident_id="incident-oom-001",
        started_at=datetime(
            2026,
            9,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        dna=IncidentDNA(
            failure="OOMKilled",
            severity="critical",
            affected_workload="checkout-api",
        ),
    )


def test_simulator_evaluates_multiple_actions():
    incident = make_oom_incident()

    actions = [
        CounterfactualAction(
            action_type="restart",
            target="checkout-api",
        ),
        CounterfactualAction(
            action_type="increase_memory",
            target="checkout-api",
            parameters={
                "memory_limit": "1Gi",
            },
        ),
        CounterfactualAction(
            action_type="scale",
            target="checkout-api",
        ),
    ]

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=actions,
    )

    assert result.incident_id == "incident-oom-001"
    assert len(result.actions) == 3
    assert len(result.predictions) == 3


def test_simulator_preserves_action_order():
    incident = make_oom_incident()

    actions = [
        CounterfactualAction(
            action_type="restart",
            target="checkout-api",
        ),
        CounterfactualAction(
            action_type="rollback",
            target="checkout-api",
        ),
        CounterfactualAction(
            action_type="increase_memory",
            target="checkout-api",
        ),
    ]

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=actions,
    )

    assert [
        prediction.action.action_type
        for prediction in result.predictions
    ] == [
        "restart",
        "rollback",
        "increase_memory",
    ]


def test_simulator_uses_incident_dna():
    incident = make_oom_incident()

    actions = [
        CounterfactualAction(
            action_type="increase_memory",
            target="checkout-api",
        )
    ]

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=actions,
    )

    prediction = result.predictions[0]

    assert prediction.predicted_status == "likely_recovered"
    assert prediction.confidence == 0.90


def test_simulator_records_deterministic_metadata():
    incident = make_oom_incident()

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=[],
    )

    assert result.metadata == {
        "simulation_type": "deterministic",
        "execution": "not_executed",
    }


def test_simulator_handles_no_actions():
    incident = make_oom_incident()

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=[],
    )

    assert result.actions == []
    assert result.predictions == []


def test_simulator_handles_incident_without_dna():
    incident = Incident(
        incident_id="incident-unknown-001",
        started_at=datetime(
            2026,
            9,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    result = CounterfactualSimulator().simulate(
        incident=incident,
        actions=[action],
    )

    assert len(result.predictions) == 1
    assert (
        result.predictions[0].predicted_status
        == "insufficient_information"
    )


def test_simulator_does_not_modify_incident():
    incident = make_oom_incident()

    original_dna = incident.dna

    actions = [
        CounterfactualAction(
            action_type="restart",
            target="checkout-api",
        )
    ]

    CounterfactualSimulator().simulate(
        incident=incident,
        actions=actions,
    )

    assert incident.dna is original_dna