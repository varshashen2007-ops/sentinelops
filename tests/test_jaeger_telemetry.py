from datetime import datetime, timezone

import pytest

from models.jaeger_telemetry import (
    jaeger_span_to_telemetry,
    jaeger_spans_to_telemetry,
)
from models.telemetry import TelemetryEvent, TelemetrySource


def make_span(
    trace_id="trace-001",
    span_id="span-001",
    operation="GET /api",
    start_time=1789387923000000,
    duration=250000,
    tags=None,
):
    return {
        "traceID": trace_id,
        "spanID": span_id,
        "references": [
            {
                "refType": "CHILD_OF",
                "spanID": "parent-001",
            }
        ],
        "operationName": operation,
        "startTime": start_time,
        "duration": duration,
        "tags": tags
        or [
            {
                "key": "service.name",
                "value": "sentinel-api",
            },
            {
                "key": "k8s.namespace.name",
                "value": "monitoring",
            },
            {
                "key": "k8s.pod.name",
                "value": "sentinel-api-123",
            },
            {
                "key": "http.status_code",
                "value": 200,
            },
        ],
    }


def test_jaeger_span_to_telemetry():
    span = make_span()

    telemetry = jaeger_span_to_telemetry(
        span,
        {"serviceName": "sentinel-api"},
    )

    assert isinstance(telemetry, TelemetryEvent)
    assert telemetry.source == TelemetrySource.JAEGER
    assert telemetry.timestamp is not None

    assert telemetry.entity is not None
    assert telemetry.entity.kind == "Pod"
    assert telemetry.entity.name == "sentinel-api-123"
    assert telemetry.entity.namespace == "monitoring"

    assert telemetry.trace is not None
    assert telemetry.trace.trace_id == "trace-001"
    assert telemetry.trace.span_id == "span-001"
    assert telemetry.trace.parent_span_id == "parent-001"
    assert telemetry.trace.service_name == "sentinel-api"
    assert telemetry.trace.operation_name == "GET /api"
    assert telemetry.trace.duration_ms == 250.0
    assert telemetry.trace.status == "200"


def test_jaeger_metadata_preserved():
    span = make_span()

    telemetry = jaeger_span_to_telemetry(
        span,
        {"serviceName": "sentinel-api"},
    )

    assert telemetry.metadata["trace_id"] == "trace-001"
    assert telemetry.metadata["span_id"] == "span-001"
    assert telemetry.metadata["service_name"] == "sentinel-api"
    assert telemetry.metadata["operation_name"] == "GET /api"

    assert (
        telemetry.metadata["jaeger_tags"]["service.name"]
        == "sentinel-api"
    )


def test_jaeger_duration_conversion():
    span = make_span(duration=1_500_000)

    telemetry = jaeger_span_to_telemetry(span)

    assert telemetry.trace is not None
    assert telemetry.trace.duration_ms == 1500.0


def test_jaeger_parent_span():
    span = make_span()

    telemetry = jaeger_span_to_telemetry(span)

    assert telemetry.trace is not None
    assert telemetry.trace.parent_span_id == "parent-001"


def test_jaeger_kubernetes_entity_mapping():
    span = make_span(
        tags=[
            {
                "key": "k8s.namespace.name",
                "value": "default",
            },
            {
                "key": "k8s.pod.name",
                "value": "nginx-demo",
            },
            {
                "key": "k8s.container.name",
                "value": "nginx",
            },
            {
                "key": "k8s.node.name",
                "value": "minikube",
            },
        ]
    )

    telemetry = jaeger_span_to_telemetry(span)

    assert telemetry.entity is not None
    assert telemetry.entity.kind == "Pod"
    assert telemetry.entity.name == "nginx-demo"
    assert telemetry.entity.namespace == "default"
    assert telemetry.entity.container == "nginx"
    assert telemetry.entity.node == "minikube"


def test_jaeger_service_entity_without_pod():
    span = make_span(
        tags=[
            {
                "key": "service.name",
                "value": "payment-service",
            }
        ]
    )

    telemetry = jaeger_span_to_telemetry(
        span,
        {"serviceName": "payment-service"},
    )

    assert telemetry.entity is not None
    assert telemetry.entity.kind == "Service"
    assert telemetry.entity.name == "payment-service"


def test_jaeger_multiple_spans():
    spans = [
        make_span(
            trace_id="trace-1",
            span_id="span-1",
        ),
        make_span(
            trace_id="trace-2",
            span_id="span-2",
        ),
        make_span(
            trace_id="trace-3",
            span_id="span-3",
        ),
    ]

    telemetry = jaeger_spans_to_telemetry(spans)

    assert len(telemetry) == 3
    assert all(
        item.source == TelemetrySource.JAEGER
        for item in telemetry
    )


def test_jaeger_missing_start_time():
    span = make_span()
    del span["startTime"]

    with pytest.raises(ValueError):
        jaeger_span_to_telemetry(span)


def test_jaeger_timestamp_is_utc():
    span = make_span()

    telemetry = jaeger_span_to_telemetry(span)

    assert telemetry.timestamp.tzinfo == timezone.utc