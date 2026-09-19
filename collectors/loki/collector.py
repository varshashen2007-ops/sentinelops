from typing import Any
from datetime import datetime, timezone

import httpx

from collectors.base import BaseCollector
from models.evidence import Evidence


class LokiCollector(BaseCollector):
    """Collect log evidence from Grafana Loki."""

    source = "loki"

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint

    def _require_endpoint(self) -> str:
        if not self.endpoint:
            raise ValueError("Loki endpoint is required.")
        return self.endpoint.rstrip("/")

    async def collect(
        self,
        *,
        query: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> list[Evidence]:
        endpoint = self._require_endpoint()

        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }

        if start is not None:
            params["start"] = start

        if end is not None:
            params["end"] = end

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{endpoint}/loki/api/v1/query_range",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        results: list[Evidence] = []

        for stream in payload.get("data", {}).get("result", []):
            labels = stream.get("stream", {})

            for entry in stream.get("values", []):
                if len(entry) != 2:
                    continue

                timestamp_ns, message = entry

                timestamp = datetime.fromtimestamp(
                    int(timestamp_ns) / 1_000_000_000,
                    tz=timezone.utc,
                )

                evidence = Evidence(
                    timestamp=timestamp,
                    source=self.source,
                    evidence_type="log",
                    data={
                        "message": message,
                        "labels": labels,
                    },
                )

                results.append(evidence)

        return results
