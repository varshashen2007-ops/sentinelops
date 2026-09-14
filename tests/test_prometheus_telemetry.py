from datetime import datetime, timezone

from models.prometheus_telemetry import (
    prometheus_result_to_telemetry,
    prometheus_results_to_telemetry,
)
from models.telemetry import TelemetrySource


def test_prometheus_result_to_telemetry():
    result = {
        "metric": {
            "__name__": "container_memory_working_set_bytes",
            "namespace": "monitoring",
            "pod": "test-pod",
            "container": "app",
            "node": "minikube",
            "job": "kubelet",
        },
        "value": ["1789384980", "52428800"],
    }

    event = prometheus_result_to_telemetry(result)

    assert event.source == TelemetrySource.PROMETHEUS
    assert event.timestamp == datetime.fromtimestamp(
        1789384980,
        tz=timezone.utc,
    )

    assert event.entity is not None
    assert event.entity.kind == "Pod"
    assert event.entity.name == "test-pod"
    assert event.entity.namespace == "monitoring"
    assert event.entity.container == "app"
    assert event.entity.node == "minikube"

    assert event.metric is not None
    assert event.metric.name == "container_memory_working_set_bytes"
    assert event.metric.value == 52428800.0
    assert event.metric.unit == "bytes"

    assert event.metric.labels["namespace"] == "monitoring"
    assert event.metric.labels["pod"] == "test-pod"
    assert event.metric.labels["container"] == "app"


def test_prometheus_results_to_telemetry():
    results = [
        {
            "metric": {
                "__name__": "container_cpu_usage_seconds_total",
                "namespace": "default",
                "pod": "pod-a",
                "container": "app",
            },
            "value": ["1789384980", "0.25"],
        },
        {
            "metric": {
                "__name__": "kube_pod_container_status_restarts_total",
                "namespace": "default",
                "pod": "pod-b",
                "container": "app",
            },
            "value": ["1789384981", "2"],
        },
    ]

    events = prometheus_results_to_telemetry(results)

    assert len(events) == 2

    assert events[0].source == TelemetrySource.PROMETHEUS
    assert events[0].metric is not None
    assert events[0].metric.name == "container_cpu_usage_seconds_total"
    assert events[0].metric.value == 0.25

    assert events[1].source == TelemetrySource.PROMETHEUS
    assert events[1].metric is not None
    assert events[1].metric.name == "kube_pod_container_status_restarts_total"
    assert events[1].metric.value == 2.0


def test_metric_name_override():
    result = {
        "metric": {
            "__name__": "up",
            "job": "kubelet",
            "node": "minikube",
        },
        "value": ["1789384980", "1"],
    }

    event = prometheus_result_to_telemetry(
        result,
        metric_name="node_health",
    )

    assert event.metric is not None
    assert event.metric.name == "node_health"
    assert event.metric.value == 1.0


def test_entity_inference():
    pod_result = {
        "metric": {
            "pod": "demo-pod",
        },
        "value": ["1789384980", "1"],
    }

    node_result = {
        "metric": {
            "node": "minikube",
        },
        "value": ["1789384980", "1"],
    }

    deployment_result = {
        "metric": {
            "deployment": "demo-deployment",
        },
        "value": ["1789384980", "1"],
    }

    assert prometheus_result_to_telemetry(
        pod_result
    ).entity.kind == "Pod"

    assert prometheus_result_to_telemetry(
        node_result
    ).entity.kind == "Node"

    assert prometheus_result_to_telemetry(
        deployment_result
    ).entity.kind == "Deployment"


def test_unknown_metric_unit_returns_none():
    result = {
        "metric": {
            "__name__": "some_custom_metric",
            "pod": "demo-pod",
        },
        "value": ["1789384980", "42"],
    }

    event = prometheus_result_to_telemetry(result)

    assert event.metric is not None
    assert event.metric.name == "some_custom_metric"
    assert event.metric.value == 42.0
    assert event.metric.unit is None