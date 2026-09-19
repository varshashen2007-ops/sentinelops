from unittest.mock import patch

import pytest

from collectors.prometheus import PrometheusCollector


def test_requires_endpoint(monkeypatch):
    monkeypatch.delenv("PROMETHEUS_URL", raising=False)

    with pytest.raises(ValueError):
        PrometheusCollector()


def test_accepts_configured_endpoint():
    collector = PrometheusCollector("http://prometheus:9090")

    assert collector.endpoint == "http://prometheus:9090"


@patch.object(PrometheusCollector, "instant_query")
def test_query_pod_metrics(mock_query):
    mock_query.return_value = {
        "status": "success",
        "data": {"resultType": "vector", "result": []},
    }

    collector = PrometheusCollector("http://prometheus:9090")

    result = collector.query_pod_metrics("default", "api")

    assert set(result) == {
        "cpu",
        "memory",
        "restarts",
        "network_receive",
        "network_transmit",
    }

    assert mock_query.call_count == 5


@patch.object(PrometheusCollector, "instant_query")
def test_query_node_metrics(mock_query):
    mock_query.return_value = {
        "status": "success",
        "data": {"resultType": "vector", "result": []},
    }

    collector = PrometheusCollector("http://prometheus:9090")

    result = collector.query_node_metrics("node-1")

    assert set(result) == {"cpu", "memory"}
    assert mock_query.call_count == 2


@patch.object(PrometheusCollector, "_request")
def test_instant_query(mock_request):
    mock_request.return_value = {
        "status": "success",
        "data": {"resultType": "vector", "result": []},
    }

    collector = PrometheusCollector("http://prometheus:9090")

    result = collector.instant_query("up")

    assert result["status"] == "success"
    mock_request.assert_called_once()


@patch.object(PrometheusCollector, "_request")
def test_range_query(mock_request):
    mock_request.return_value = {
        "status": "success",
        "data": {"resultType": "matrix", "result": []},
    }

    collector = PrometheusCollector("http://prometheus:9090")

    result = collector.range_query(
        "up",
        start=1000,
        end=2000,
        step=60,
    )

    assert result["status"] == "success"
    mock_request.assert_called_once()
    