from datetime import datetime, timezone

from embeddings.incident_document import IncidentDocumentBuilder
from incident_engine.dna import IncidentDNA
from models.incident import (
    Incident,
    IncidentDiagnosis,
    IncidentOutcome,
    IncidentResolution,
)


def create_incident() -> Incident:
    return Incident(
        incident_id="incident-001",
        started_at=datetime(
            2026,
            9,
            17,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        dna=IncidentDNA(
            trigger="memory_growth",
            failure="OOMKilled",
            restart_pattern="repeated",
            readiness="failed",
            affected_workload="payment-api",
            duration=120.0,
            severity="high",
        ),
        diagnosis=IncidentDiagnosis(
            summary="Application exceeded its memory limit.",
            root_cause="Insufficient memory limit",
            evidence_references=["kubernetes:event"],
        ),
        resolution=IncidentResolution(
            action="increase_memory_limit",
            description="Increased container memory limit.",
        ),
        outcome=IncidentOutcome(
            status="resolved",
            description="Application remained healthy.",
            verified=True,
        ),
    )


def test_incident_document_contains_core_fields():
    incident = create_incident()

    document = IncidentDocumentBuilder().build(incident)

    assert "Incident ID: incident-001" in document
    assert "Trigger: memory_growth" in document
    assert "Failure: OOMKilled" in document
    assert "Affected Workload: payment-api" in document
    assert "Severity: high" in document


def test_incident_document_contains_diagnosis():
    incident = create_incident()

    document = IncidentDocumentBuilder().build(incident)

    assert "Diagnosis: Application exceeded its memory limit." in document
    assert "Root Cause: Insufficient memory limit" in document


def test_incident_document_contains_resolution_and_outcome():
    incident = create_incident()

    document = IncidentDocumentBuilder().build(incident)

    assert "Resolution Action: increase_memory_limit" in document
    assert "Resolution Description: Increased container memory limit." in document
    assert "Outcome Status: resolved" in document
    assert "Outcome Description: Application remained healthy." in document
    assert "Outcome Verified: True" in document


def test_missing_optional_fields_are_not_written():
    incident = Incident(
        incident_id="incident-002",
        started_at=datetime(
            2026,
            9,
            17,
            9,
            0,
            tzinfo=timezone.utc,
        ),
    )

    document = IncidentDocumentBuilder().build(incident)

    assert "Incident ID: incident-002" in document
    assert "Trigger:" not in document
    assert "Failure:" not in document
    assert "Diagnosis:" not in document
    assert "Resolution Action:" not in document
    assert "Outcome Status:" not in document


def test_same_incident_produces_same_document():
    incident = create_incident()
    builder = IncidentDocumentBuilder()

    first = builder.build(incident)
    second = builder.build(incident)

    assert first == second