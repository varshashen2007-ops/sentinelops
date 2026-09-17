from datetime import datetime, timezone

from incident_engine.dna import IncidentDNA
from models.incident import (
    Incident,
    IncidentDiagnosis,
    IncidentOutcome,
    IncidentResolution,
    IncidentTimeline,
)


def test_incident_can_be_created():
    incident = Incident(
        incident_id="incident-001",
        started_at=datetime.now(timezone.utc),
    )

    assert incident.incident_id == "incident-001"
    assert incident.ended_at is None
    assert incident.dna is None
    assert incident.timeline.entries == []
    assert incident.diagnosis is None
    assert incident.resolution is None
    assert incident.outcome is None


def test_incident_can_store_dna():
    dna = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        severity="high",
    )

    incident = Incident(
        incident_id="incident-002",
        started_at=datetime.now(timezone.utc),
        dna=dna,
    )

    assert incident.dna == dna
    assert incident.dna.failure == "OOMKilled"


def test_incident_can_store_timeline():
    timeline = IncidentTimeline(
        entries=[
            {
                "timestamp": "2026-09-17T09:00:00Z",
                "description": "Memory usage increased",
            },
            {
                "timestamp": "2026-09-17T09:02:00Z",
                "description": "Container was OOMKilled",
            },
        ]
    )

    incident = Incident(
        incident_id="incident-003",
        started_at=datetime.now(timezone.utc),
        timeline=timeline,
    )

    assert len(incident.timeline.entries) == 2
    assert incident.timeline.entries[1]["description"] == "Container was OOMKilled"


def test_incident_can_store_diagnosis():
    diagnosis = IncidentDiagnosis(
        summary="Application memory exceeded its configured limit.",
        root_cause="Insufficient memory limit",
        evidence_references=[
            "kubernetes:event",
            "prometheus:metric",
        ],
    )

    incident = Incident(
        incident_id="incident-004",
        started_at=datetime.now(timezone.utc),
        diagnosis=diagnosis,
    )

    assert incident.diagnosis is not None
    assert incident.diagnosis.root_cause == "Insufficient memory limit"
    assert len(incident.diagnosis.evidence_references) == 2


def test_incident_can_store_resolution_and_outcome():
    resolution = IncidentResolution(
        action="increase_memory_limit",
        description="Increased the container memory limit.",
    )

    outcome = IncidentOutcome(
        status="resolved",
        description="Application remained healthy after the change.",
        verified=True,
    )

    incident = Incident(
        incident_id="incident-005",
        started_at=datetime.now(timezone.utc),
        resolution=resolution,
        outcome=outcome,
    )

    assert incident.resolution.action == "increase_memory_limit"
    assert incident.outcome.status == "resolved"
    assert incident.outcome.verified is True


def test_incident_metadata_is_independent():
    first = Incident(
        incident_id="incident-006",
        started_at=datetime.now(timezone.utc),
    )

    second = Incident(
        incident_id="incident-007",
        started_at=datetime.now(timezone.utc),
    )

    first.metadata["namespace"] = "default"

    assert first.metadata["namespace"] == "default"
    assert second.metadata == {}