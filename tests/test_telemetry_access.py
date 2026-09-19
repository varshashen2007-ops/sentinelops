import pytest

from telemetry.access import TelemetryAccess
from telemetry.registry import TelemetryRegistry
from models.evidence import Evidence
from datetime import datetime, timezone


class FakeRegistry:
    def __init__(self):
        self.calls = []

    async def collect(self, source, **kwargs):
        self.calls.append((source, kwargs))
        return [
    Evidence(
        source=source,
        evidence_type="test",
        timestamp=datetime.now(timezone.utc),
    )
]


@pytest.mark.asyncio
async def test_collect_delegates_to_registry():
    registry = FakeRegistry()
    access = TelemetryAccess(registry)

    result = await access.collect("prometheus", query="up")

    assert len(result) == 1
    assert result[0].source == "prometheus"
    assert registry.calls == [("prometheus", {"query": "up"})]


@pytest.mark.asyncio
async def test_metrics_uses_prometheus():
    registry = FakeRegistry()
    access = TelemetryAccess(registry)

    result = await access.metrics(query="up")

    assert result[0].source == "prometheus"
    assert registry.calls == [("prometheus", {"query": "up"})]


@pytest.mark.asyncio
async def test_logs_uses_loki():
    registry = FakeRegistry()
    access = TelemetryAccess(registry)

    result = await access.logs(query='{job="app"}')

    assert result[0].source == "loki"
    assert registry.calls == [("loki", {"query": '{job="app"}'})]


@pytest.mark.asyncio
async def test_traces_uses_jaeger():
    registry = FakeRegistry()
    access = TelemetryAccess(registry)

    result = await access.traces(service="sentinelops")

    assert result[0].source == "jaeger"
    assert registry.calls == [("jaeger", {"service": "sentinelops"})]


@pytest.mark.asyncio
async def test_kubernetes_uses_kubernetes():
    registry = FakeRegistry()
    access = TelemetryAccess(registry)

    result = await access.kubernetes(namespace="default")

    assert result[0].source == "kubernetes"
    assert registry.calls == [("kubernetes", {"namespace": "default"})]