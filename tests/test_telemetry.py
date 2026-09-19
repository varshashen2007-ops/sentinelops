import pytest
from datetime import datetime, timezone

from models.evidence import Evidence
from telemetry.adapters import TelemetryAdapter
from telemetry.registry import TelemetryRegistry


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