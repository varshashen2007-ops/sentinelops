from datetime import datetime, timezone

from incident_engine.detector import (
    ApplicationErrorDetector,
    IncidentDetector,
    KubernetesFailureDetector,
    ResourceDetector,
)
from models.evidence import Evidence


TIMESTAMP = datetime.now(timezone.utc)


def make_evidence(
    source: str,
    evidence_type: str,
    data: dict,
    namespace: str = "default",
    resource: str = "test-pod",
):
    return Evidence(
        source=source,
        evidence_type=evidence_type,
        timestamp=TIMESTAMP,
        namespace=namespace,
        resource=resource,
        data=data,
    )


def test_crashloopbackoff_detection():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {"reason": "CrashLoopBackOff"},
        )
    ]

    candidates = KubernetesFailureDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "CrashLoopBackOff"
    assert candidates[0].severity == "critical"


def test_oomkilled_detection():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {"reason": "OOMKilled"},
        )
    ]

    candidates = KubernetesFailureDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "OOMKilled"
    assert candidates[0].severity == "critical"


def test_pending_detection():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {"reason": "Pending"},
        )
    ]

    candidates = KubernetesFailureDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "Pod Pending"


def test_failed_scheduling_detection():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {"reason": "FailedScheduling"},
        )
    ]

    candidates = KubernetesFailureDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "FailedScheduling"
    assert candidates[0].severity == "critical"


def test_readiness_failure_detection():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {
                "reason": "Readiness probe failed",
                "message": "readiness probe failed",
            },
        )
    ]

    candidates = KubernetesFailureDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "Readiness Failure"


def test_high_cpu_detection():
    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            {
                "metric_name": "cpu_usage",
                "value": 0.95,
            },
        )
    ]

    candidates = ResourceDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "High CPU"


def test_high_memory_detection():
    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            {
                "metric_name": "memory_usage",
                "value": 0.96,
            },
        )
    ]

    candidates = ResourceDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "High Memory"


def test_application_error_detection():
    evidence = [
        make_evidence(
            "loki",
            "log",
            {
                "message": "ERROR database connection failed",
                "labels": {},
            },
        )
    ]

    candidates = ApplicationErrorDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "Application Error"
    assert candidates[0].severity == "error"


def test_trace_error_detection():
    evidence = [
        make_evidence(
            "jaeger",
            "trace",
            {
                "status": "error",
            },
        )
    ]

    candidates = ApplicationErrorDetector().detect(evidence)

    assert len(candidates) == 1
    assert candidates[0].title == "Trace Error"
    assert candidates[0].severity == "error"


def test_incident_detector_combines_detectors():
    evidence = [
        make_evidence(
            "kubernetes",
            "event",
            {"reason": "OOMKilled"},
        ),
        make_evidence(
            "prometheus",
            "metric",
            {
                "metric_name": "cpu_usage",
                "value": 0.95,
            },
        ),
        make_evidence(
            "loki",
            "log",
            {
                "message": "ERROR application failed",
                "labels": {},
            },
        ),
    ]

    candidates = IncidentDetector().detect(evidence)

    assert len(candidates) == 3

    titles = {candidate.title for candidate in candidates}

    assert "OOMKilled" in titles
    assert "High CPU" in titles
    assert "Application Error" in titles


def test_irrelevant_evidence_is_ignored():
    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            {
                "metric_name": "cpu_usage",
                "value": 0.20,
            },
        ),
        make_evidence(
            "loki",
            "log",
            {
                "message": "INFO application started",
                "labels": {},
            },
        ),
    ]

    candidates = IncidentDetector().detect(evidence)

    assert candidates == []


def test_candidates_are_chronologically_sorted():
    earlier = datetime(
        2026,
        9,
        14,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    later = datetime(
        2026,
        9,
        14,
        12,
        5,
        0,
        tzinfo=timezone.utc,
    )

    evidence = [
        Evidence(
            source="loki",
            evidence_type="log",
            timestamp=later,
            namespace="default",
            resource="test-pod",
            data={
                "message": "ERROR something failed",
                "labels": {},
            },
        ),
        Evidence(
            source="kubernetes",
            evidence_type="event",
            timestamp=earlier,
            namespace="default",
            resource="test-pod",
            data={
                "reason": "OOMKilled",
            },
        ),
    ]

    candidates = IncidentDetector().detect(evidence)

    assert len(candidates) == 2
    assert candidates[0].timestamp == earlier
    assert candidates[1].timestamp == later