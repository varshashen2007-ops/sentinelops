import pytest

from collectors.loki.collector import LokiCollector


@pytest.mark.asyncio
async def test_loki_collector_requires_endpoint():
    collector = LokiCollector()

    with pytest.raises(ValueError, match="Loki endpoint is required"):
        await collector.collect(query='{app="test"}')


@pytest.mark.asyncio
async def test_loki_collector_collects_logs(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "data": {
                    "result": [
                        {
                            "stream": {
                                "app": "sentinelops",
                                "level": "error",
                            },
                            "values": [
                                ["1700000000000000000", "pod crashed"],
                                ["1700000001000000000", "restart failed"],
                            ],
                        }
                    ]
                }
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params):
            assert url == "http://localhost:3100/loki/api/v1/query_range"
            assert params["query"] == '{app="sentinelops"}'
            return FakeResponse()

    monkeypatch.setattr(
        "collectors.loki.collector.httpx.AsyncClient",
        lambda: FakeClient(),
    )

    collector = LokiCollector("http://localhost:3100")

    evidence = await collector.collect(
        query='{app="sentinelops"}',
    )

    assert len(evidence) == 2
    assert evidence[0].source == "loki"
    assert evidence[0].data["message"] == "pod crashed"
    assert evidence[0].data["labels"]["app"] == "sentinelops"
