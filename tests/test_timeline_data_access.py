import pytest
from datetime import datetime, timezone

from models.evidence import Evidence
from telemetry.timeline import TimelineDataAccess


def make_evidence(
    *,
    timestamp,
    source="prometheus",
    entity=None,
    namespace=None,
    resource=None,
):
    data = {}

    if entity is not None:
        data["entity"] = entity

    return Evidence(
        source=source,
        evidence_type="test",
        timestamp=timestamp,
        namespace=namespace,
        resource=resource,
        data=data,
    )
    metadata = {}

    if entity is not None:
        metadata["entity"] = entity

    if namespace is not None:
        metadata["namespace"] = namespace

    if resource is not None:
        metadata["resource"] = resource

    return Evidence(
        source=source,
        evidence_type="test",
        timestamp=timestamp,
        metadata=metadata,
    )


@pytest.fixture
def evidence():
    return [
        make_evidence(
            timestamp=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            source="prometheus",
            entity="api",
            namespace="production",
            resource="pod/api-1",
        ),
        make_evidence(
            timestamp=datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
            source="loki",
            entity="api",
            namespace="production",
            resource="pod/api-1",
        ),
        make_evidence(
            timestamp=datetime(2026, 1, 1, 10, 10, tzinfo=timezone.utc),
            source="jaeger",
            entity="frontend",
            namespace="production",
            resource="pod/frontend-1",
        ),
    ]


def test_returns_evidence_in_timestamp_order(evidence):
    access = TimelineDataAccess(reversed(evidence))

    result = access.query()

    assert [item.timestamp for item in result] == sorted(
        item.timestamp for item in evidence
    )


def test_filters_by_time_range(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(
        start_time=datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 10, 10, tzinfo=timezone.utc),
    )

    assert len(result) == 2


def test_filters_by_source(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(source="loki")

    assert len(result) == 1
    assert result[0].source == "loki"


def test_filters_by_entity(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(entity="api")

    assert len(result) == 2


def test_filters_by_namespace(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(namespace="production")

    assert len(result) == 3


def test_filters_by_resource(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(resource="pod/api-1")

    assert len(result) == 2


def test_filters_can_be_combined(evidence):
    access = TimelineDataAccess(evidence)

    result = access.query(
        source="loki",
        namespace="production",
        resource="pod/api-1",
    )

    assert len(result) == 1
    assert result[0].source == "loki"


def test_add_then_query(evidence):
    access = TimelineDataAccess()

    access.add(evidence[0])

    result = access.query(source="prometheus")

    assert len(result) == 1