from datetime import datetime, timezone
from typing import Any

from models.telemetry import (
    EntityReference,
    MetricObservation,
    TelemetryEvent,
    TelemetrySource,
)


def prometheus_result_to_telemetry(
    result: dict[str, Any],
    metric_name: str | None = None,
) -> TelemetryEvent:
    """
    Convert one Prometheus instant-query result into
    the unified SentinelOps TelemetryEvent contract.

    Prometheus result format:

        {
            "metric": {...labels...},
            "value": [timestamp, value]
        }
    """

    metric = result.get("metric", {})
    value = result.get("value", [])

    # Prometheus instant-query timestamps are Unix timestamps.
    timestamp = datetime.now(timezone.utc)

    if value:
        try:
            timestamp = datetime.fromtimestamp(
                float(value[0]),
                tz=timezone.utc,
            )
        except (TypeError, ValueError, OverflowError):
            pass

    # Prometheus returns metric values as strings.
    numeric_value: float | int | None = None

    if len(value) > 1:
        try:
            numeric_value = float(value[1])
        except (TypeError, ValueError):
            numeric_value = None

    # Identify the Kubernetes entity represented by the metric.
    entity = EntityReference(
        kind=_infer_entity_kind(metric),
        name=(
            metric.get("pod")
            or metric.get("deployment")
            or metric.get("node")
            or metric.get("instance")
        ),
        namespace=metric.get("namespace"),
        container=metric.get("container"),
        node=metric.get("node"),
    )

    # Avoid creating an empty entity when no identifying labels exist.
    if not any(
        [
            entity.kind,
            entity.name,
            entity.namespace,
            entity.container,
            entity.node,
        ]
    ):
        entity = None

    observation = MetricObservation(
        name=metric_name or metric.get("__name__", "unknown"),
        value=numeric_value,
        unit=_infer_metric_unit(metric_name or metric.get("__name__", "")),
        labels={
            str(key): str(value)
            for key, value in metric.items()
            if key != "__name__"
        },
    )

    return TelemetryEvent(
        timestamp=timestamp,
        source=TelemetrySource.PROMETHEUS,
        entity=entity,
        metadata={
            "prometheus_metric": metric.get("__name__"),
            "job": metric.get("job"),
            "endpoint": metric.get("endpoint"),
            "metrics_path": metric.get("metrics_path"),
        },
        metric=observation,
    )


def prometheus_results_to_telemetry(
    results: list[dict[str, Any]],
    metric_name: str | None = None,
) -> list[TelemetryEvent]:
    """
    Convert multiple Prometheus results into unified telemetry events.
    """

    return [
        prometheus_result_to_telemetry(
            result=result,
            metric_name=metric_name,
        )
        for result in results
    ]


def _infer_entity_kind(metric: dict[str, Any]) -> str | None:
    """
    Infer the Kubernetes entity kind from Prometheus labels.
    """

    if metric.get("pod"):
        return "Pod"

    if metric.get("deployment"):
        return "Deployment"

    if metric.get("node"):
        return "Node"

    if metric.get("container"):
        return "Container"

    if metric.get("instance"):
        return "Instance"

    return None


def _infer_metric_unit(metric_name: str) -> str | None:
    """
    Infer a useful unit from common Prometheus metric names.

    This is intentionally conservative. Unknown metrics
    return None rather than guessing.
    """

    name = metric_name.lower()

    if "memory" in name and (
        "bytes" in name
        or "working_set" in name
        or "rss" in name
    ):
        return "bytes"

    if "cpu_usage_seconds" in name:
        return "seconds_per_second"

    if name.startswith("rate(") and "cpu" in name:
        return "seconds_per_second"

    if "restarts" in name:
        return "count"

    if "network" in name and (
        "receive" in name
        or "transmit" in name
        or "bytes" in name
    ):
        return "bytes_per_second"

    if name == "up":
        return "boolean"

    return None