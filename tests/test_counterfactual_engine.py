from counterfactual.engine import CounterfactualEngine
from counterfactual.model import CounterfactualAction
from incident_engine.dna import IncidentDNA


def test_restart_is_predicted_for_crashloop_incident():
    dna = IncidentDNA(
        failure="CrashLoopBackOff",
        restart_pattern="Repeated container restarts",
    )

    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "likely_recovered"
    assert result.confidence == 0.85
    assert "restart" in result.rationale.lower()
    assert "CrashLoopBackOff pattern detected" in result.supporting_factors


def test_restart_on_memory_failure_is_temporary():
    dna = IncidentDNA(
        failure="OOMKilled due to memory exhaustion",
    )

    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "temporary_recovery"
    assert result.confidence == 0.70
    assert "memory" in result.predicted_effect.lower()


def test_rollback_is_predicted_for_configuration_failure():
    dna = IncidentDNA(
        trigger="New deployment configuration",
        failure="Configuration caused application failure",
    )

    action = CounterfactualAction(
        action_type="rollback",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "likely_recovered"
    assert result.confidence == 0.80
    assert "configuration" in result.rationale.lower()


def test_rollback_is_uncertain_for_unrelated_failure():
    dna = IncidentDNA(
        failure="OOMKilled",
    )

    action = CounterfactualAction(
        action_type="rollback",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "uncertain"
    assert result.confidence == 0.40


def test_scale_is_predicted_for_resource_pressure():
    dna = IncidentDNA(
        failure="CPU resource exhaustion",
        anomaly_information={
            "signal": "high CPU load",
        },
    )

    action = CounterfactualAction(
        action_type="scale",
        target="checkout-api",
        parameters={
            "replicas": 3,
        },
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "potentially_recovered"
    assert result.confidence == 0.75
    assert "resource" in result.rationale.lower()


def test_scale_is_uncertain_for_non_resource_failure():
    dna = IncidentDNA(
        failure="Application configuration failure",
    )

    action = CounterfactualAction(
        action_type="scale",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "uncertain"
    assert result.confidence == 0.40


def test_increase_memory_is_predicted_for_oom():
    dna = IncidentDNA(
        failure="OOMKilled",
    )

    action = CounterfactualAction(
        action_type="increase_memory",
        target="checkout-api",
        parameters={
            "memory_limit": "1Gi",
        },
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "likely_recovered"
    assert result.confidence == 0.90
    assert "memory" in result.predicted_effect.lower()


def test_increase_memory_is_uncertain_for_non_memory_failure():
    dna = IncidentDNA(
        failure="FailedScheduling",
    )

    action = CounterfactualAction(
        action_type="increase_memory",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "uncertain"
    assert result.confidence == 0.35


def test_unknown_action_is_not_predicted_as_recovered():
    dna = IncidentDNA(
        failure="OOMKilled",
    )

    action = CounterfactualAction(
        action_type="unknown_action",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.predicted_status == "insufficient_information"
    assert result.confidence == 0.20
    assert "not supported" in result.rationale.lower()


def test_missing_dna_produces_insufficient_information():
    action = CounterfactualAction(
        action_type="restart",
        target="checkout-api",
    )

    result = CounterfactualEngine().predict(action, None)

    assert result.predicted_status == "insufficient_information"
    assert result.confidence == 0.10
    assert "DNA" in result.rationale


def test_prediction_preserves_original_action():
    dna = IncidentDNA(
        failure="OOMKilled",
    )

    action = CounterfactualAction(
        action_type="increase_memory",
        target="checkout-api",
        parameters={
            "memory_limit": "1Gi",
        },
    )

    result = CounterfactualEngine().predict(action, dna)

    assert result.action is action
    assert result.action.target == "checkout-api"
    assert result.action.parameters["memory_limit"] == "1Gi"