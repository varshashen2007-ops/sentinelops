import pytest

from collectors.jaeger.collector import JaegerCollector
from collectors.loki.collector import LokiCollector
from collectors.prometheus.collector import PrometheusCollector


@pytest.mark.asyncio
async def test_observability_collectors_can_be_initialized():
    prometheus = PrometheusCollector("http://localhost:9090")
    loki = LokiCollector("http://localhost:3100")
    jaeger = JaegerCollector("http://localhost:16686")

    assert prometheus.endpoint == "http://localhost:9090"
    assert loki.endpoint == "http://localhost:3100"
    assert jaeger.endpoint == "http://localhost:16686"