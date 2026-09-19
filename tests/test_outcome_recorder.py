from datetime import datetime, timezone

import pytest

from learning.outcome_recorder import IncidentOutcomeRecorder
from models.incident import Incident
from remediation.model import RemediationResult
from verification.model import VerificationResult


def make_incident(incident_id: str = "incident-1") -> Incident:
    return Incident(
        incident_id=incident_id,
        started_at=datetime.now(timezone.utc),
    )


def make_remediation_result(
    incident_id: str = "incident-1",
    request_id: str = "request-1",
    action_type: str = "restart",
) -> RemediationResult:
    return RemediationResult(
        request_id=request_id,
        incident_id=incident_id,
        action_type=action_type,
        target="deployment/api",
        status="executed",
        message="Remediation executed successfully.",
    )


def make_verification_result(
    incident_id: str = "incident-1",
    request_id: str = "request-1",
    action_type: str = "restart",
    status: str = "recovered",
    recovered: bool = True,
) -> VerificationResult:
    return VerificationResult(
        request_id=request_id,
        incident_id=incident_id,
        action_type=action_type,
        target="deployment/api",
        status=status,
        recovered=recovered,
        message="Post-remediation verification completed.",
    )


def test_records_successful_remediation_outcome():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    result = recorder.record(
        incident,
        make_remediation_result(),
        make_verification_result(),
    )

    assert result.resolution is not None
    assert result.resolution.action == "restart"

    assert result.outcome is not None
    assert result.outcome.status == "recovered"
    assert result.outcome.verified is True


def test_records_failed_recovery():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    result = recorder.record(
        incident,
        make_remediation_result(),
        make_verification_result(
            status="not_recovered",
            recovered=False,
        ),
    )

    assert result.outcome is not None
    assert result.outcome.status == "not_recovered"
    assert result.outcome.verified is True


def test_records_remediation_message_as_resolution_description():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    remediation = make_remediation_result()

    result = recorder.record(
        incident,
        remediation,
        make_verification_result(),
    )

    assert result.resolution is not None
    assert result.resolution.description == remediation.message


def test_records_verification_message_as_outcome_description():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    verification = make_verification_result()

    result = recorder.record(
        incident,
        make_remediation_result(),
        verification,
    )

    assert result.outcome is not None
    assert result.outcome.description == verification.message


def test_rejects_mismatched_incident_id_in_remediation():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident("incident-1")

    with pytest.raises(ValueError, match="Incident ID"):
        recorder.record(
            incident,
            make_remediation_result(incident_id="incident-2"),
            make_verification_result(),
        )


def test_rejects_mismatched_incident_id_in_verification():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident("incident-1")

    with pytest.raises(ValueError, match="Incident ID"):
        recorder.record(
            incident,
            make_remediation_result(),
            make_verification_result(incident_id="incident-2"),
        )


def test_rejects_mismatched_request_id():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    with pytest.raises(ValueError, match="Request ID"):
        recorder.record(
            incident,
            make_remediation_result(request_id="request-1"),
            make_verification_result(request_id="request-2"),
        )


def test_preserves_existing_incident_data():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    incident.metadata["environment"] = "test"

    result = recorder.record(
        incident,
        make_remediation_result(),
        make_verification_result(),
    )

    assert result.incident_id == "incident-1"
    assert result.metadata["environment"] == "test"
    assert result.started_at is not None


def test_returns_the_same_incident_object():
    recorder = IncidentOutcomeRecorder()
    incident = make_incident()

    result = recorder.record(
        incident,
        make_remediation_result(),
        make_verification_result(),
    )

    assert result is incident


def test_records_different_remediation_actions():
    recorder = IncidentOutcomeRecorder()

    for action_type in (
        "restart",
        "scale",
        "rollback",
        "increase_memory",
    ):
        incident = make_incident()

        result = recorder.record(
            incident,
            make_remediation_result(action_type=action_type),
            make_verification_result(action_type=action_type),
        )

        assert result.resolution is not None
        assert result.resolution.action == action_type