from datetime import datetime, timezone

from incident_engine.anomaly import (
    AnomalyAnalyzer,
    FailureAnomalyDetector,
    ResourceAnomalyDetector,
)
from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence


def make_evidence(
    source,
    evidence_type,
    timestamp,
    namespace="default",
    resource="test-pod",
    data=None,
):
    return Evidence(
        source=source,
        evidence_type=evidence_type,
        timestamp=timestamp,
        namespace=namespace,
        resource=resource,
        data=data or {},
    )


def make_incident(
    title="High Memory",
    namespace="default",
    resource="test-pod",
):
    evidence = make_evidence(
        source="kubernetes",
        evidence_type="event",
        timestamp=datetime.now(timezone.utc),
        namespace=namespace,
        resource=resource,
        data={"reason": title},
    )

    return IncidentCandidate(
        detector="TestDetector",
        title=title,
        severity="warning",
        timestamp=evidence.timestamp,
        namespace=namespace,
        resource=resource,
        evidence=evidence,
    )


def test_high_cpu_is_actionable_anomaly():
    incident = make_incident()

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            datetime.now(timezone.utc),
            data={
                "metric_name": "cpu_usage",
                "value": 0.95,
            },
        )
    ]

    detector = ResourceAnomalyDetector()
    results = detector.detect(incident, evidence)

    assert len(results) == 1
    assert results[0].title == "High CPU Usage"
    assert results[0].anomaly_type == "actionable_anomaly"
    assert results[0].score >= 0.80
    assert len(results[0].reasons) > 0


def test_high_memory_is_actionable_anomaly():
    incident = make_incident()

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            datetime.now(timezone.utc),
            data={
                "metric_name": "memory_usage",
                "value": 0.95,
            },
        )
    ]

    detector = ResourceAnomalyDetector()
    results = detector.detect(incident, evidence)

    assert len(results) == 1
    assert results[0].title == "High Memory Usage"
    assert results[0].anomaly_type == "actionable_anomaly"
    assert results[0].score >= 0.90


def test_low_resource_usage_is_not_anomaly():
    incident = make_incident()

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            datetime.now(timezone.utc),
            data={
                "metric_name": "memory_usage",
                "value": 0.40,
            },
        )
    ]

    detector = ResourceAnomalyDetector()
    results = detector.detect(incident, evidence)

    assert results == []


def test_oomkilled_finds_memory_evidence():
    incident = make_incident(title="OOMKilled")

    first_time = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 14, 12, 1, tzinfo=timezone.utc)

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            second_time,
            data={
                "metric_name": "container_memory_usage",
                "value": 0.95,
            },
        ),
        make_evidence(
            "prometheus",
            "metric",
            first_time,
            data={
                "metric_name": "container_memory_usage",
                "value": 0.85,
            },
        ),
    ]

    detector = FailureAnomalyDetector()
    results = detector.detect(incident, evidence)

    assert len(results) == 1
    assert results[0].title == "Memory Pressure Before OOMKilled"
    assert results[0].anomaly_type == "actionable_anomaly"
    assert results[0].score == 0.95
    assert len(results[0].reasons) >= 2


def test_unrelated_namespace_is_ignored():
    incident = make_incident()

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            datetime.now(timezone.utc),
            namespace="other",
            resource="test-pod",
            data={
                "metric_name": "memory_usage",
                "value": 0.99,
            },
        )
    ]

    detector = ResourceAnomalyDetector()
    results = detector.detect(incident, evidence)

    assert results == []


def test_analyzer_returns_chronological_results():
    incident = make_incident()

    first_time = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 14, 12, 1, tzinfo=timezone.utc)

    evidence = [
        make_evidence(
            "prometheus",
            "metric",
            second_time,
            data={
                "metric_name": "memory_usage",
                "value": 0.95,
            },
        ),
        make_evidence(
            "prometheus",
            "metric",
            first_time,
            data={
                "metric_name": "cpu_usage",
                "value": 0.95,
            },
        ),
    ]

    analyzer = AnomalyAnalyzer()
    results = analyzer.analyze(incident, evidence)

    assert len(results) == 2
    assert results[0].timestamp <= results[1].timestamp