from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TelemetrySource(str, Enum):
    """Origin of telemetry data."""

    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    LOKI = "loki"
    JAEGER = "jaeger"


class Severity(str, Enum):
    """Common severity levels for telemetry."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class EntityReference(BaseModel):
    """
    Identifies the Kubernetes or observability entity
    associated with a telemetry event.
    """

    kind: str | None = None
    name: str | None = None
    namespace: str | None = None
    container: str | None = None
    node: str | None = None


class MetricObservation(BaseModel):
    """Normalized metric observation."""

    name: str
    value: float | int | None = None
    unit: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class LogObservation(BaseModel):
    """Normalized log observation."""

    message: str
    labels: dict[str, str] = Field(default_factory=dict)
    severity: Severity = Severity.UNKNOWN


class TraceObservation(BaseModel):
    """Normalized distributed-trace observation."""

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    service_name: str | None = None
    operation_name: str | None = None
    duration_ms: float | None = None
    status: str | None = None


class TelemetryEvent(BaseModel):
    """
    Common telemetry contract shared by Kubernetes,
    Prometheus, Loki, and Jaeger data.
    """

    timestamp: datetime
    source: TelemetrySource
    entity: EntityReference | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    metric: MetricObservation | None = None
    log: LogObservation | None = None
    trace: TraceObservation | None = None