from datetime import datetime, timezone
from typing import Any

from models.telemetry import (
    EntityReference,
    TelemetryEvent,
    TelemetrySource,
    TraceObservation,
)


def _ensure_utc(value: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and represented in UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _parse_timestamp(value: Any) -> datetime:
    """
    Convert common Jaeger timestamp representations into UTC datetime.

    Jaeger commonly represents timestamps as:
    - microseconds since Unix epoch
    - milliseconds since Unix epoch
    - ISO-8601 strings
    """
    if isinstance(value, datetime):
        return _ensure_utc(value)

    if isinstance(value, (int, float)):
        numeric = float(value)

        # Jaeger trace timestamps are commonly microseconds.
        if numeric > 1_000_000_000_000:
            return datetime.fromtimestamp(
                numeric / 1_000_000,
                tz=timezone.utc,
            )

        # Also support milliseconds.
        if numeric > 1_000_000_000:
            return datetime.fromtimestamp(
                numeric / 1_000,
                tz=timezone.utc,
            )

        return datetime.fromtimestamp(
            numeric,
            tz=timezone.utc,
        )

    if isinstance(value, str):
        text = value.strip()

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            return _ensure_utc(
                datetime.fromisoformat(text)
            )
        except ValueError:
            pass

    raise ValueError(
        f"Unsupported Jaeger timestamp: {value!r}"
    )


def _get_process_service_name(
    process: dict[str, Any],
) -> str | None:
    """
    Extract service name from a Jaeger process object.
    """
    service_name = process.get("serviceName")

    if service_name:
        return str(service_name)

    service_name = process.get("service_name")

    if service_name:
        return str(service_name)

    return None


def _get_tag_value(
    tags: list[dict[str, Any]],
    *names: str,
) -> Any:
    """
    Find the first matching tag value.
    """
    wanted = set(names)

    for tag in tags:
        if tag.get("key") in wanted:
            return tag.get("value")

    return None


def jaeger_span_to_telemetry(
    span: dict[str, Any],
    process: dict[str, Any] | None = None,
) -> TelemetryEvent:
    """
    Convert one Jaeger span into a unified TelemetryEvent.

    Expected Jaeger span fields include:
        traceID
        spanID
        references
        operationName
        startTime
        duration
        tags

    Jaeger duration is normally represented in microseconds.
    SentinelOps stores duration in milliseconds.
    """
    process = process or {}

    trace_id = span.get("traceID")
    span_id = span.get("spanID")

    references = span.get("references") or []

    parent_span_id = None

    for reference in references:
        if reference.get("refType") == "CHILD_OF":
            parent_span_id = reference.get("spanID")
            break

    tags = span.get("tags") or []

    if not isinstance(tags, list):
        tags = []

    service_name = _get_process_service_name(process)

    if service_name is None:
        service_name = _get_tag_value(
            tags,
            "service.name",
            "service_name",
        )

    operation_name = (
        span.get("operationName")
        or span.get("operation_name")
    )

    start_time = span.get("startTime")

    if start_time is None:
        raise ValueError(
            "Jaeger span is missing startTime"
        )

    timestamp = _parse_timestamp(start_time)

    duration = span.get("duration")

    duration_ms = None

    if duration is not None:
        try:
            duration_ms = float(duration) / 1000.0
        except (TypeError, ValueError):
            duration_ms = None

    status = _get_tag_value(
        tags,
        "status",
        "otel.status_code",
        "http.status_code",
    )

    namespace = _get_tag_value(
        tags,
        "k8s.namespace.name",
        "namespace",
    )

    pod = _get_tag_value(
        tags,
        "k8s.pod.name",
        "pod",
    )

    container = _get_tag_value(
        tags,
        "k8s.container.name",
        "container",
    )

    node = _get_tag_value(
        tags,
        "k8s.node.name",
        "node",
    )

    entity = EntityReference(
        kind="Pod" if pod else "Service" if service_name else None,
        name=pod or service_name,
        namespace=str(namespace) if namespace else None,
        container=str(container) if container else None,
        node=str(node) if node else None,
    )

    string_tags = {
        str(tag.get("key")): str(tag.get("value"))
        for tag in tags
        if tag.get("key") is not None
    }

    return TelemetryEvent(
        timestamp=timestamp,
        source=TelemetrySource.JAEGER,
        entity=entity,
        metadata={
            "trace_id": trace_id,
            "span_id": span_id,
            "service_name": service_name,
            "operation_name": operation_name,
            "jaeger_tags": string_tags,
        },
        trace=TraceObservation(
            trace_id=str(trace_id) if trace_id else None,
            span_id=str(span_id) if span_id else None,
            parent_span_id=(
                str(parent_span_id)
                if parent_span_id
                else None
            ),
            service_name=(
                str(service_name)
                if service_name
                else None
            ),
            operation_name=(
                str(operation_name)
                if operation_name
                else None
            ),
            duration_ms=duration_ms,
            status=str(status) if status is not None else None,
        ),
    )


def jaeger_spans_to_telemetry(
    spans: list[dict[str, Any]],
) -> list[TelemetryEvent]:
    """
    Convert multiple Jaeger spans into unified telemetry events.
    """
    return [
        jaeger_span_to_telemetry(span)
        for span in spans
    ]