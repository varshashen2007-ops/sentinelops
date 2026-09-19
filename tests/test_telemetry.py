from datetime import datetime, timezone

import pytest

from models.evidence import Evidence
from models.telemetry import (
    EntityReference,
    LogObservation,
    MetricObservation,
    Severity,
    TelemetryEvent,
    TelemetrySource,
    TraceObservation,
)
from telemetry.adapters import TelemetryAdapter
from telemetry.registry import TelemetryRegistry


# ---------------------------------------------------------------------------
# Core SentinelOps telemetry model tests
# ---------------------------------------------------------------------------

def test_telemetry_event_requires_timestamp_and_source():
    event = TelemetryEvent(
        timestamp=datetime.now(timezone.utc),
        source=TelemetrySource.KUBERNETES,
    )

    assert event.timestamp is not None
    assert event.source == TelemetrySource.KUBERNETES


def test_entity_reference():
    entity = EntityReference(
        kind="Pod",
        name="nginx-demo",
        namespace="default",
        container="nginx",
        node="minikube",
    )

    assert entity.kind == "Pod"
    assert entity.name == "nginx-demo"
    assert entity.namespace == "default"
    assert entity.container == "nginx"
    assert entity.node == "minikube"


def test_metric_observation():
    metric = MetricObservation(
        name="cpu_usage",
        value=42.5,
        unit="percent",
        labels={"pod": "nginx-demo"},
    )

    assert metric.name == "cpu_usage"
    assert metric.value == 42.5
    assert metric.unit == "percent"
    assert metric.labels["pod"] == "nginx-demo"


def test_log_observation():
    log = LogObservation(
        message="connection refused",
        severity=Severity.ERROR,
        labels={"pod": "nginx-demo"},
    )

    assert log.message == "connection refused"
    assert log.severity == Severity.ERROR
    assert log.labels["pod"] == "nginx-demo"


def test_trace_observation():
    trace = TraceObservation(
        trace_id="trace-123",
        span_id="span-456",
        service_name="sentinelops",
        operation_name="collect",
        duration_ms=25.5,
        status="ok",
    )

    assert trace.trace_id == "trace-123"
    assert trace.span_id == "span-456"
    assert trace.service_name == "sentinelops"
    assert trace.operation_name == "collect"
    assert trace.duration_ms == 25.5
    assert trace.status == "ok"


def test_all_telemetry_sources():
    timestamp = datetime.now(timezone.utc)

    sources = [
        TelemetrySource.KUBERNETES,
        TelemetrySource.PROMETHEUS,
        TelemetrySource.LOKI,
        TelemetrySource.JAEGER,
    ]

    events = [
        TelemetryEvent(
            timestamp=timestamp,
            source=source,
            metadata={"test": True},
        )
        for source in sources
    ]

    assert [event.source for event in events] == sources


def test_telemetry_event_supports_metric_log_and_trace():
    timestamp = datetime.now(timezone.utc)

    metric_event = TelemetryEvent(
        timestamp=timestamp,
        source=TelemetrySource.PROMETHEUS,
        metric=MetricObservation(
            name="memory_usage",
            value=1024,
            unit="bytes",
        ),
    )

    log_event = TelemetryEvent(
        timestamp=timestamp,
        source=TelemetrySource.LOKI,
        log=LogObservation(
            message="pod started",
            severity=Severity.INFO,
        ),
    )

    trace_event = TelemetryEvent(
        timestamp=timestamp,
        source=TelemetrySource.JAEGER,
        trace=TraceObservation(
            trace_id="trace-1",
            span_id="span-1",
        ),
    )

    assert metric_event.metric.name == "memory_usage"
    assert log_event.log.message == "pod started"
    assert trace_event.trace.trace_id == "trace-1"


# ---------------------------------------------------------------------------
# Dhrithi's telemetry adapter and registry tests
# ---------------------------------------------------------------------------

class DummyAdapter(TelemetryAdapter):
    source = "dummy"

    def collect(self, **kwargs):
        return [
            self.normalize(
                Evidence(
                    source="original",
                    evidence_type="metric",
                    timestamp=datetime.now(timezone.utc),
                    data={"value": 42},
                )
            )
        ]


def test_normalize_sets_timestamp_and_source():
    adapter = DummyAdapter()

    evidence = Evidence(
        source="old",
        evidence_type="metric",
        timestamp=datetime.now(timezone.utc),
        data={"value": 1},
    )

    result = adapter.normalize(evidence)

    assert result.source == "dummy"
    assert result.timestamp.tzinfo is not None


def test_normalize_adds_utc_timestamp_when_missing():
    adapter = DummyAdapter()

    evidence = Evidence(
        source="old",
        evidence_type="metric",
        timestamp=datetime.now(timezone.utc),
        data={},
    )

    result = adapter.normalize(evidence)

    assert result.timestamp is not None
    assert result.timestamp.tzinfo == timezone.utc


def test_registry_register_and_get():
    registry = TelemetryRegistry()
    adapter = DummyAdapter()

    registry.register("dummy", adapter)

    assert registry.get("dummy") is adapter
    assert "dummy" in registry.names()


def test_registry_rejects_duplicate():
    registry = TelemetryRegistry()
    adapter = DummyAdapter()

    registry.register("dummy", adapter)

    with pytest.raises(ValueError):
        registry.register("dummy", adapter)


def test_registry_rejects_empty_name():
    registry = TelemetryRegistry()

    with pytest.raises(ValueError):
        registry.register("", DummyAdapter())


def test_registry_get_missing_adapter():
    registry = TelemetryRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")


def test_registry_unregister():
    registry = TelemetryRegistry()
    registry.register("dummy", DummyAdapter())

    registry.unregister("dummy")

    assert "dummy" not in registry.names()


def test_registry_collect():
    registry = TelemetryRegistry()
    registry.register("dummy", DummyAdapter())

    evidence = registry.collect("dummy")

    assert len(evidence) == 1
    assert evidence[0].source == "dummy"
    assert evidence[0].evidence_type == "metric"