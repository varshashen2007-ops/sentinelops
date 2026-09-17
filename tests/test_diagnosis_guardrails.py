from diagnosis.guardrails import (
    DiagnosisGuardrail,
    GuardrailIssue,
    GuardrailResult,
)
from diagnosis.model import Diagnosis, EvidenceReference


def make_supported_diagnosis():
    return Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Container was OOMKilled.",
                timestamp="2026-09-17T10:00:00+00:00",
                resource="checkout-api",
                data={
                    "reason": "OOMKilled",
                    "message": "Container exceeded memory limit",
                },
            )
        ],
        historical_incident_ids=[],
        explanation="Current Kubernetes evidence supports the diagnosis.",
    )


def make_unsupported_diagnosis():
    return Diagnosis(
        summary="Dependency failure detected.",
        root_cause="Redis caused the current incident.",
        confidence=0.70,
        evidence_references=[],
        historical_incident_ids=[],
        explanation="No direct evidence was available.",
    )


def test_supported_diagnosis_passes():
    diagnosis = make_supported_diagnosis()

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is True
    assert result.supported_claims == [
        "Container memory limit exhaustion."
    ]
    assert result.issues == []


def test_diagnosis_without_current_evidence_fails():
    diagnosis = make_unsupported_diagnosis()

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is False
    assert result.supported_claims == []
    assert len(result.issues) == 1

    issue = result.issues[0]

    assert issue.claim == "Redis caused the current incident."
    assert issue.severity == "error"
    assert "No current evidence reference" in issue.reason


def test_historical_context_does_not_count_as_current_evidence():
    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.90,
        evidence_references=[],
        historical_incident_ids=[
            "historical-001",
            "historical-002",
        ],
        explanation="Similar historical incidents were retrieved.",
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is False
    assert result.supported_claims == []
    assert result.contextual_claims == [
        "historical-001",
        "historical-002",
    ]
    assert len(result.issues) == 1


def test_historical_context_is_recorded_when_current_evidence_exists():
    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Container was OOMKilled.",
                data={
                    "reason": "OOMKilled",
                },
            )
        ],
        historical_incident_ids=[
            "historical-001",
        ],
        explanation="Current evidence plus historical context.",
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is True
    assert result.supported_claims == [
        "Container memory limit exhaustion."
    ]
    assert result.contextual_claims == [
        "historical-001"
    ]
    assert result.issues == []


def test_empty_root_cause_fails():
    diagnosis = Diagnosis(
        summary="Incomplete diagnosis.",
        root_cause="   ",
        confidence=0.50,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Some event occurred.",
            )
        ],
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is False
    assert len(result.issues) == 1

    issue = result.issues[0]

    assert issue.claim == ""
    assert issue.severity == "error"
    assert "root-cause claim" in issue.reason


def test_guardrail_issue_serializes():
    issue = GuardrailIssue(
        claim="Redis caused the incident.",
        reason="No current evidence supports the claim.",
        severity="error",
    )

    result = issue.to_dict()

    assert result == {
        "claim": "Redis caused the incident.",
        "reason": "No current evidence supports the claim.",
        "severity": "error",
    }


def test_guardrail_result_serializes():
    diagnosis = make_supported_diagnosis()

    result = DiagnosisGuardrail().validate(diagnosis)
    serialized = result.to_dict()

    assert serialized["passed"] is True
    assert serialized["supported_claims"] == [
        "Container memory limit exhaustion."
    ]
    assert serialized["contextual_claims"] == []
    assert serialized["issues"] == []


def test_guardrail_does_not_modify_diagnosis():
    diagnosis = make_supported_diagnosis()

    original_root_cause = diagnosis.root_cause
    original_evidence = list(diagnosis.evidence_references)

    DiagnosisGuardrail().validate(diagnosis)

    assert diagnosis.root_cause == original_root_cause
    assert diagnosis.evidence_references == original_evidence


def test_evidence_content_supports_root_cause():
    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Container exceeded memory limit.",
                data={
                    "reason": "OOMKilled",
                    "memory_limit": "512Mi",
                },
            )
        ],
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is True
    assert result.supported_claims == [
        "Container memory limit exhaustion."
    ]
    assert result.issues == []


def test_evidence_content_that_does_not_support_claim_fails():
    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Pod failed scheduling.",
                data={
                    "reason": "FailedScheduling",
                    "message": "No suitable node was available.",
                },
            )
        ],
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is False
    assert result.supported_claims == []
    assert len(result.issues) == 1
    assert result.issues[0].severity == "error"
    assert "does not contain deterministic support" in result.issues[0].reason


def test_historical_evidence_cannot_support_current_claim():
    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[
            EvidenceReference(
                source="kubernetes",
                evidence_type="event",
                description="Pod failed scheduling.",
                data={
                    "reason": "FailedScheduling",
                },
            )
        ],
        historical_incident_ids=[
            "historical-oom-001",
        ],
    )

    result = DiagnosisGuardrail().validate(diagnosis)

    assert result.passed is False
    assert result.supported_claims == []
    assert result.contextual_claims == [
        "historical-oom-001"
    ]
    assert len(result.issues) == 1