from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from collectors.prometheus_collector import (
    PrometheusCollector as LegacyPrometheusCollector,
)
from models.evidence import Evidence


# ============================================================
# Legacy Prometheus Collector Tests
# ============================================================

def mock_instant_response():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {
                        "__name__": "up",
                        "instance": "localhost:9090",
                    },
                    "value": ["1750000000", "1"],
                }
            ]
        },
    }
    return response


def mock_range_response():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {
                        "__name__": "up",
                        "instance": "localhost:9090",
                    },
                    "values": [
                        ["1750000000", "1"],
                        ["1750000030", "1"],
                    ],
                }
            ]
        },
    }
    return response


def test_legacy_instant_query():
    collector = LegacyPrometheusCollector()

    with patch(
        "collectors.prometheus_collector.requests.get",
        return_value=mock_instant_response(),
    ):
        results = collector.instant_query("up")

    assert isinstance(results, list)
    assert len(results) > 0


def test_legacy_range_query():
    collector = LegacyPrometheusCollector()

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=5)

    with patch(
        "collectors.prometheus_collector.requests.get",
        return_value=mock_range_response(),
    ):
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


def test_legacy_query_pod_metrics():
    collector = LegacyPrometheusCollector()

    with patch(
        "collectors.prometheus_collector.requests.get",
        return_value=mock_instant_response(),
    ):
        results = collector.query_pod_metrics(
            namespace="default",
            pod="nginx-demo-5dc66cb97d-w66sr",
        )

    assert isinstance(results, dict)

    assert "cpu" in results
    assert "memory" in results
    assert "restarts" in results


def test_legacy_collect_returns_evidence():
    collector = LegacyPrometheusCollector()

    with patch(
        "collectors.prometheus_collector.requests.get",
        return_value=mock_instant_response(),
    ):
        evidence = collector.collect()

    assert isinstance(evidence, list)
    assert len(evidence) > 0

    for item in evidence:
        assert isinstance(item, Evidence)
        assert item.source == "prometheus"
        assert item.evidence_type == "metric"
        assert item.timestamp is not None


# ============================================================
# Dhrithi's Prometheus Collector Tests
# ============================================================

from collectors.prometheus import PrometheusCollector


def test_requires_endpoint():
    collector = PrometheusCollector(endpoint="http://localhost:9090")

    assert collector.endpoint == "http://localhost:9090"


def test_accepts_configured_endpoint():
    collector = PrometheusCollector(endpoint="http://prometheus:9090")

    assert collector.endpoint == "http://prometheus:9090"


def test_query_pod_metrics():
    collector = PrometheusCollector(endpoint="http://localhost:9090")

    with patch(
        "collectors.prometheus.collector.urlopen"
    ) as mock_urlopen:
        response = Mock()
        response.read.return_value = (
            b'{"status":"success","data":{"result":[]}}'
        )

        mock_urlopen.return_value.__enter__.return_value = response

        result = collector.query_pod_metrics(
            namespace="default",
            pod="nginx",
        )

    assert isinstance(result, dict)
    assert "cpu" in result
    assert "memory" in result
    assert "restarts" in result


def test_query_node_metrics():
    collector = PrometheusCollector(endpoint="http://localhost:9090")

    with patch(
        "collectors.prometheus.collector.urlopen"
    ) as mock_urlopen:
        response = Mock()
        response.read.return_value = (
            b'{"status":"success","data":{"result":[]}}'
        )

        mock_urlopen.return_value.__enter__.return_value = response

        result = collector.query_node_metrics("node-1")

    assert isinstance(result, dict)
    assert "cpu" in result
    assert "memory" in result


def test_new_instant_query():
    collector = PrometheusCollector(endpoint="http://localhost:9090")

    with patch(
        "collectors.prometheus.collector.urlopen"
    ) as mock_urlopen:
        response = Mock()
        response.read.return_value = (
            b'{"status":"success","data":{"result":[]}}'
        )

        mock_urlopen.return_value.__enter__.return_value = response

        result = collector.instant_query("up")

    assert isinstance(result, dict)
    assert result["status"] == "success"


def test_new_range_query():
    collector = PrometheusCollector(endpoint="http://localhost:9090")

    with patch(
        "collectors.prometheus.collector.urlopen"
    ) as mock_urlopen:
        response = Mock()
        response.read.return_value = (
            b'{"status":"success","data":{"result":[]}}'
        )

        mock_urlopen.return_value.__enter__.return_value = response

        result = collector.range_query(
            "up",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T00:05:00Z",
            step="30s",
        )

    assert isinstance(result, dict)
    assert result["status"] == "success"