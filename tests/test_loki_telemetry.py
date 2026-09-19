from datetime import datetime, timezone

import pytest

from models.evidence import Evidence
from models.loki_telemetry import (
    loki_evidence_to_telemetry,
    loki_results_to_telemetry,
)
from models.telemetry import Severity, TelemetryEvent, TelemetrySource


def make_evidence(
    message="test log message",
    labels=None,
):
    return Evidence(
        source="loki",
        evidence_type="log",
        timestamp=datetime.now(timezone.utc),
        namespace="monitoring",
        resource="test-pod",
        data={
            "message": message,
            "labels": labels or {
                "namespace": "monitoring",
                "pod": "test-pod",
                "container": "test-container",
                "node_name": "minikube",
            },
        },
    )


def test_loki_evidence_to_telemetry():
    evidence = make_evidence()

    telemetry = loki_evidence_to_telemetry(evidence)

    assert isinstance(telemetry, TelemetryEvent)
    assert telemetry.source == TelemetrySource.LOKI
    assert telemetry.timestamp is not None
    assert telemetry.entity is not None
    assert telemetry.entity.kind == "Pod"
    assert telemetry.entity.name == "test-pod"
    assert telemetry.entity.namespace == "monitoring"
    assert telemetry.entity.container == "test-container"
    assert telemetry.entity.node == "minikube"
    assert telemetry.log is not None
    assert telemetry.log.message == "test log message"


def test_loki_labels_are_preserved():
    labels = {
        "namespace": "monitoring",
        "pod": "test-pod",
        "container": "nginx",
        "node_name": "minikube",
        "job": "monitoring/loki",
        "service_name": "loki",
    }

    telemetry = loki_evidence_to_telemetry(
        make_evidence(labels=labels)
    )

    assert telemetry.log is not None
    assert telemetry.log.labels == {
        key: str(value)
        for key, value in labels.items()
    }

    assert telemetry.metadata["job"] == "monitoring/loki"
    assert telemetry.metadata["service"] == "loki"


def test_loki_severity_from_label():
    telemetry = loki_evidence_to_telemetry(
        make_evidence(
            labels={
                "namespace": "monitoring",
                "pod": "test-pod",
                "level": "error",
            }
        )
    )

    assert telemetry.log is not None
    assert telemetry.log.severity == Severity.ERROR


def test_loki_severity_from_message():
    telemetry = loki_evidence_to_telemetry(
        make_evidence(
            message="database ERROR occurred"
        )
    )

    assert telemetry.log is not None
    assert telemetry.log.severity == Severity.ERROR


def test_unknown_severity():
    telemetry = loki_evidence_to_telemetry(
        make_evidence(
            message="normal request completed"
        )
    )

    assert telemetry.log is not None
    assert telemetry.log.severity == Severity.UNKNOWN


def test_multiple_loki_evidence_items():
    evidence = [
        make_evidence(message="first log"),
        make_evidence(message="second log"),
        make_evidence(message="third log"),
    ]

    telemetry = loki_results_to_telemetry(evidence)

    assert len(telemetry) == 3
    assert all(
        item.source == TelemetrySource.LOKI
        for item in telemetry
    )


def test_reject_non_loki_evidence():
    evidence = Evidence(
        source="prometheus",
        evidence_type="metric",
        timestamp=datetime.now(timezone.utc),
        resource="test-pod",
        data={"value": 1},
    )

    with pytest.raises(ValueError):
        loki_evidence_to_telemetry(evidence)


def test_reject_non_log_evidence():
    evidence = Evidence(
        source="loki",
        evidence_type="metric",
        timestamp=datetime.now(timezone.utc),
        resource="test-pod",
        data={"value": 1},
    )

    with pytest.raises(ValueError):
        loki_evidence_to_telemetry(evidence)