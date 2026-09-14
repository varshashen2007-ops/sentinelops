from datetime import datetime, timezone
from typing import Any

from models.evidence import Evidence
from models.telemetry import (
    EntityReference,
    LogObservation,
    Severity,
    TelemetryEvent,
    TelemetrySource,
)


def _parse_severity(labels: dict[str, Any], message: str) -> Severity:
    """
    Determine log severity from Loki labels or the log message.
    """

    raw_severity = (
        labels.get("level")
        or labels.get("severity")
        or labels.get("detected_level")
    )

    if raw_severity:
        value = str(raw_severity).lower()

        mapping = {
            "debug": Severity.DEBUG,
            "info": Severity.INFO,
            "information": Severity.INFO,
            "warn": Severity.WARNING,
            "warning": Severity.WARNING,
            "error": Severity.ERROR,
            "err": Severity.ERROR,
            "critical": Severity.CRITICAL,
            "fatal": Severity.CRITICAL,
        }

        if value in mapping:
            return mapping[value]

    message_lower = message.lower()

    if "critical" in message_lower or "fatal" in message_lower:
        return Severity.CRITICAL

    if "error" in message_lower or "exception" in message_lower:
        return Severity.ERROR

    if "warning" in message_lower or "warn" in message_lower:
        return Severity.WARNING

    if "info" in message_lower:
        return Severity.INFO

    if "debug" in message_lower:
        return Severity.DEBUG

    return Severity.UNKNOWN


def loki_evidence_to_telemetry(
    evidence: Evidence,
) -> TelemetryEvent:
    """
    Convert one Loki Evidence object into a unified TelemetryEvent.
    """

    if evidence.source != "loki":
        raise ValueError(
            "Expected Loki evidence with source='loki'"
        )

    if evidence.evidence_type != "log":
        raise ValueError(
            "Expected Loki evidence with evidence_type='log'"
        )

    data = evidence.data or {}

    message = str(data.get("message", ""))

    labels = data.get("labels", {})

    if not isinstance(labels, dict):
        labels = {}

    string_labels = {
        str(key): str(value)
        for key, value in labels.items()
    }

    entity = EntityReference(
        kind="Pod" if labels.get("pod") else None,
        name=labels.get("pod") or evidence.resource,
        namespace=labels.get("namespace") or evidence.namespace,
        container=labels.get("container"),
        node=labels.get("node_name"),
    )

    severity = _parse_severity(
        labels=string_labels,
        message=message,
    )

    return TelemetryEvent(
        timestamp=_ensure_utc(evidence.timestamp),
        source=TelemetrySource.LOKI,
        entity=entity,
        metadata={
            "loki_labels": string_labels,
            "job": string_labels.get("job"),
            "service": (
                string_labels.get("service_name")
                or string_labels.get("service")
            ),
        },
        log=LogObservation(
            message=message,
            labels=string_labels,
            severity=severity,
        ),
    )


def loki_results_to_telemetry(
    evidence: list[Evidence],
) -> list[TelemetryEvent]:
    """
    Convert multiple Loki Evidence objects into
    unified TelemetryEvents.
    """

    return [
        loki_evidence_to_telemetry(item)
        for item in evidence
    ]


def _ensure_utc(value: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and represented in UTC.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)