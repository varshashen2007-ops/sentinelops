from datetime import datetime, timezone
from typing import Any

import httpx

from models.evidence import Evidence


class JaegerCollector:
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint.rstrip("/") if endpoint else None

    async def search_traces(
        self,
        service: str,
        start: int | None = None,
        end: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not self.endpoint:
            raise ValueError("Jaeger endpoint is required")

        params: dict[str, Any] = {
            "service": service,
            "limit": limit,
        }

        if start is not None:
            params["start"] = start

        if end is not None:
            params["end"] = end

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.endpoint}/api/traces",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        return payload.get("data", [])

    async def get_trace(self, trace_id: str) -> dict[str, Any]:
        if not self.endpoint:
            raise ValueError("Jaeger endpoint is required")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.endpoint}/api/traces/{trace_id}"
            )
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data", [])
        return data[0] if data else {}

    def extract_spans(
        self,
        trace: dict[str, Any],
    ) -> list[Evidence]:
        evidence: list[Evidence] = []

        for span in trace.get("spans", []):
            start_time = span.get("startTime")

            if start_time is None:
                timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.fromtimestamp(
                    start_time / 1_000_000,
                    tz=timezone.utc,
                )

            process = span.get("process", {})
            tags = span.get("tags", [])

            evidence.append(
                Evidence(
                    source="jaeger",
                    evidence_type="trace",
                    timestamp=timestamp,
                    resource=span.get("operationName"),
                    data={
                        "trace_id": trace.get("traceID"),
                        "span_id": span.get("spanID"),
                        "operation": span.get("operationName"),
                        "duration": span.get("duration"),
                        "tags": tags,
                        "process": process,
                    },
                )
            )

        return evidence