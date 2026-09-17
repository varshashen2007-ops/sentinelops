from datetime import datetime, timezone

from diagnosis.model import Diagnosis, EvidenceReference


def test_evidence_reference_to_dict():
    reference = EvidenceReference(
        source="kubernetes",
        evidence_type="event",
        description="Container was OOMKilled",
        timestamp="2026-09-17T10:00:00+00:00",
        resource="checkout-api",
    )

    result = reference.to_dict()

    assert result == {
        "source": "kubernetes",
        "evidence_type": "event",
        "description": "Container was OOMKilled",
        "timestamp": "2026-09-17T10:00:00+00:00",
        "resource": "checkout-api",
        "data": {},
    }


def test_diagnosis_to_dict():
    reference = EvidenceReference(
        source="prometheus",
        evidence_type="metric",
        description="Memory usage exceeded configured limit",
    )

    diagnosis = Diagnosis(
        summary="Memory incident detected.",
        root_cause="Container memory limit exhaustion.",
        confidence=0.95,
        evidence_references=[reference],
        historical_incident_ids=["incident-001"],
        explanation="Prometheus evidence supports the diagnosis.",
    )

    result = diagnosis.to_dict()

    assert result["summary"] == "Memory incident detected."
    assert result["root_cause"] == "Container memory limit exhaustion."
    assert result["confidence"] == 0.95
    assert result["historical_incident_ids"] == ["incident-001"]
    assert len(result["evidence_references"]) == 1
    assert (
        result["evidence_references"][0]["source"]
        == "prometheus"
    )


def test_diagnosis_supports_empty_evidence():
    diagnosis = Diagnosis(
        summary="Insufficient evidence.",
        root_cause="Unknown",
        confidence=0.5,
    )

    assert diagnosis.evidence_references == []
    assert diagnosis.historical_incident_ids == []