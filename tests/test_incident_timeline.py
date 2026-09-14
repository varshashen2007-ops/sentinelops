from datetime import datetime, timedelta, timezone

from incident_engine.detector import IncidentCandidate
from incident_engine.timeline import (
    IncidentTimeline,
    IncidentTimelineBuilder,
    TimelineEntry,
)
from models.evidence import Evidence


def make_evidence(
    source: str,
    evidence_type: str,
    timestamp: datetime,
    namespace: str = "default",
    resource: str = "nginx-demo",
    data: dict | None = None,
) -> Evidence:
    return Evidence(
        source=source,
        evidence_type=evidence_type,
        timestamp=timestamp,
        namespace=namespace,
        resource=resource,
        data=data or {},
    )


def make_incident(
    evidence: Evidence,
) -> IncidentCandidate:
    return IncidentCandidate(
        detector="KubernetesFailureDetector",
        title="OOMKilled",
        severity="critical",
        timestamp=evidence.timestamp,
        namespace=evidence.namespace,
        resource=evidence.resource,
        evidence=evidence,
        details=evidence.data,
    )


def test_timeline_entry_creation():
    timestamp = datetime.now(timezone.utc)

    entry = TimelineEntry(
        timestamp=timestamp,
        source="kubernetes",
        description="OOMKilled",
    )

    assert entry.timestamp == timestamp
    assert entry.source == "kubernetes"
    assert entry.description == "OOMKilled"


def test_timeline_is_chronologically_sorted():
    now = datetime.now(timezone.utc)

    late = make_evidence(
        "kubernetes",
        "event",
        now + timedelta(seconds=20),
        data={"reason": "OOMKilled"},
    )

    early = make_evidence(
        "kubernetes",
        "event",
        now,
        data={"reason": "Started"},
    )

    incident = make_incident(late)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [late, early],
    )

    assert isinstance(timeline, IncidentTimeline)

    assert timeline.entries[0].timestamp == early.timestamp
    assert timeline.entries[1].timestamp == late.timestamp


def test_kubernetes_evidence_supported():
    timestamp = datetime.now(timezone.utc)

    evidence = make_evidence(
        "kubernetes",
        "event",
        timestamp,
        data={
            "reason": "OOMKilled",
            "message": "Container exceeded memory limit",
        },
    )

    incident = make_incident(evidence)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [evidence],
    )

    assert len(timeline.entries) == 1
    assert timeline.entries[0].description == "OOMKilled"


def test_prometheus_evidence_supported():
    timestamp = datetime.now(timezone.utc)

    evidence = make_evidence(
        "prometheus",
        "metric",
        timestamp,
        data={
            "metric_name": "memory_usage",
            "value": 0.95,
        },
    )

    incident = IncidentCandidate(
        detector="ResourceDetector",
        title="High Memory",
        severity="warning",
        timestamp=timestamp,
        namespace="default",
        resource="nginx-demo",
        evidence=evidence,
    )

    timeline = IncidentTimelineBuilder().build(
        incident,
        [evidence],
    )

    assert len(timeline.entries) == 1
    assert "memory_usage" in timeline.entries[0].description
    assert "0.95" in timeline.entries[0].description


def test_loki_evidence_supported():
    timestamp = datetime.now(timezone.utc)

    evidence = make_evidence(
        "loki",
        "log",
        timestamp,
        data={
            "message": "Application error occurred",
        },
    )

    incident = make_incident(evidence)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [evidence],
    )

    assert len(timeline.entries) == 1
    assert timeline.entries[0].description == (
        "Application error occurred"
    )


def test_jaeger_evidence_supported():
    timestamp = datetime.now(timezone.utc)

    evidence = make_evidence(
        "jaeger",
        "trace",
        timestamp,
        data={
            "operation_name": "GET /api",
            "status": "error",
        },
    )

    incident = make_incident(evidence)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [evidence],
    )

    assert len(timeline.entries) == 1
    assert "GET /api" in timeline.entries[0].description
    assert "error" in timeline.entries[0].description


def test_unrelated_namespace_is_excluded():
    timestamp = datetime.now(timezone.utc)

    related = make_evidence(
        "kubernetes",
        "event",
        timestamp,
        namespace="default",
        resource="nginx-demo",
        data={"reason": "Started"},
    )

    unrelated = make_evidence(
        "kubernetes",
        "event",
        timestamp,
        namespace="monitoring",
        resource="prometheus",
        data={"reason": "Started"},
    )

    incident = make_incident(related)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [related, unrelated],
    )

    assert len(timeline.entries) == 1
    assert timeline.entries[0].resource == "nginx-demo"


def test_multiple_telemetry_sources_are_supported():
    now = datetime.now(timezone.utc)

    kubernetes = make_evidence(
        "kubernetes",
        "event",
        now,
        data={"reason": "Pod Scheduled"},
    )

    prometheus = make_evidence(
        "prometheus",
        "metric",
        now + timedelta(seconds=5),
        data={
            "metric_name": "cpu_usage",
            "value": 0.95,
        },
    )

    loki = make_evidence(
        "loki",
        "log",
        now + timedelta(seconds=10),
        data={
            "message": "Application error",
        },
    )

    jaeger = make_evidence(
        "jaeger",
        "trace",
        now + timedelta(seconds=15),
        data={
            "operation_name": "GET /api",
            "status": "error",
        },
    )

    incident = make_incident(kubernetes)

    timeline = IncidentTimelineBuilder().build(
        incident,
        [
            jaeger,
            loki,
            prometheus,
            kubernetes,
        ],
    )

    assert len(timeline.entries) == 4

    assert [
        entry.source
        for entry in timeline.entries
    ] == [
        "kubernetes",
        "prometheus",
        "loki",
        "jaeger",
    ]