from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from collectors.base import BaseCollector
from models.evidence import Evidence


class LokiCollector(BaseCollector):
    """
    Collector for retrieving logs from Loki.

    Loki is accessed through its HTTP API.
    Retrieved log entries are converted into
    SentinelOps Evidence objects.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3100",
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def collect(self) -> list[Evidence]:
        """
        Collect recent Kubernetes logs.

        This provides the common BaseCollector interface.
        """

        try:
            return self.query_logs('{namespace=~".+"}')
        except requests.RequestException:
            return []

    def query_logs(
        self,
        query: str,
        limit: int = 100,
    ) -> list[Evidence]:
        """
        Query recent logs from Loki using LogQL.

        Loki's range-query API is used over the
        previous five minutes.
        """

        end = datetime.now(timezone.utc)
        start = end.replace(microsecond=0) - timedelta(minutes=5)

        return self.query_range(
            query=query,
            start=start,
            end=end,
            limit=limit,
        )

    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[Evidence]:
        """
        Query logs from Loki over a specific time range.
        """

        start = self._ensure_utc(start)
        end = self._ensure_utc(end)

        response = requests.get(
            f"{self.base_url}/loki/api/v1/query_range",
            params={
                "query": query,
                "start": str(int(start.timestamp() * 1_000_000_000)),
                "end": str(int(end.timestamp() * 1_000_000_000)),
                "limit": limit,
                "direction": "forward",
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Loki range query failed: {payload}"
            )

        return self._response_to_evidence(payload)

    def query_pod_logs(
        self,
        namespace: str,
        pod: str,
        limit: int = 100,
    ) -> list[Evidence]:
        """
        Query logs for one Kubernetes Pod.
        """

        query = f'{{namespace="{namespace}",pod="{pod}"}}'

        return self.query_logs(
            query=query,
            limit=limit,
        )

    def _response_to_evidence(
        self,
        payload: dict[str, Any],
    ) -> list[Evidence]:
        """
        Convert Loki API results into SentinelOps Evidence.
        """

        evidence: list[Evidence] = []

        results = payload.get("data", {}).get("result", [])

        for stream in results:
            labels = stream.get("stream", {})
            values = stream.get("values", [])

            for timestamp_ns, log_line in values:
                timestamp = datetime.fromtimestamp(
                    int(timestamp_ns) / 1_000_000_000,
                    tz=timezone.utc,
                )

                evidence.append(
                    Evidence(
                        source="loki",
                        evidence_type="log",
                        timestamp=timestamp,
                        namespace=labels.get("namespace"),
                        resource=labels.get("pod"),
                        data={
                            "message": log_line,
                            "labels": labels,
                        },
                    )
                )

        return evidence

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        """
        Ensure a datetime is timezone-aware and represented in UTC.
        """

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)