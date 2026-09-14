from datetime import datetime, timedelta, timezone

from collectors.prometheus_collector import PrometheusCollector
from models.evidence import Evidence


def test_instant_query():
    collector = PrometheusCollector()

    results = collector.instant_query("up")

    assert isinstance(results, list)
    assert len(results) > 0


def test_range_query():
    collector = PrometheusCollector()

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)

    results = collector.range_query(
        "up",
        start,
        end,
        30,
    )

    assert isinstance(results, list)
    assert len(results) > 0

    for result in results:
        assert "metric" in result
        assert "values" in result
        assert len(result["values"]) > 0


def test_query_pod_metrics():
    collector = PrometheusCollector()

    results = collector.query_pod_metrics(
        namespace="default",
        pod="nginx-demo-5dc66cb97d-w66sr",
    )

    assert isinstance(results, dict)

    assert "cpu" in results
    assert "memory" in results
    assert "restarts" in results


def test_collect_returns_evidence():
    collector = PrometheusCollector()

    evidence = collector.collect()

    assert isinstance(evidence, list)
    assert len(evidence) > 0

    for item in evidence:
        assert isinstance(item, Evidence)
        assert item.source == "prometheus"
        assert item.evidence_type == "metric"
        assert item.timestamp is not None