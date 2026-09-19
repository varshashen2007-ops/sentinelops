import pytest

from collectors.jaeger.collector import JaegerCollector


@pytest.mark.asyncio
async def test_jaeger_collector_requires_endpoint():
    collector = JaegerCollector()

    with pytest.raises(ValueError, match="Jaeger endpoint is required"):
        await collector.search_traces(service="sentinelops")


@pytest.mark.asyncio
async def test_jaeger_collector_searches_traces(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "data": [
                    {
                        "traceID": "trace-123",
                        "spans": [],
                    }
                ]
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params):
            assert url == "http://localhost:16686/api/traces"
            assert params["service"] == "sentinelops"
            return FakeResponse()

    monkeypatch.setattr(
        "collectors.jaeger.collector.httpx.AsyncClient",
        lambda: FakeClient(),
    )

    collector = JaegerCollector("http://localhost:16686")

    traces = await collector.search_traces(
        service="sentinelops",
    )

    assert len(traces) == 1
    assert traces[0]["traceID"] == "trace-123"


def test_jaeger_collector_extracts_spans():
    collector = JaegerCollector("http://localhost:16686")

    trace = {
        "traceID": "trace-123",
        "spans": [
            {
                "spanID": "span-456",
                "operationName": "GET /api",
                "startTime": 1_700_000_000_000_000,
                "duration": 5000,
                "tags": [
                    {"key": "http.status_code", "value": 200},
                ],
                "process": {
                    "serviceName": "sentinelops",
                },
            }
        ],
    }

    evidence = collector.extract_spans(trace)

    assert len(evidence) == 1
    assert evidence[0].source == "jaeger"
    assert evidence[0].evidence_type == "trace"
    assert evidence[0].resource == "GET /api"
    assert evidence[0].data["trace_id"] == "trace-123"
    assert evidence[0].data["span_id"] == "span-456"