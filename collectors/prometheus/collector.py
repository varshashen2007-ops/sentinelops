import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from collectors.base import BaseCollector
from models.evidence import Evidence
from telemetry.adapters import TelemetryAdapter


class PrometheusCollector(TelemetryAdapter):
    """Collect metrics from a Prometheus HTTP API."""

    source = "prometheus"

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or os.getenv("PROMETHEUS_URL")

        if not self.endpoint:
            raise ValueError(
                "Prometheus endpoint must be provided or set via PROMETHEUS_URL."
            )

        self.endpoint = self.endpoint.rstrip("/")

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a Prometheus HTTP API request."""
        url = f"{self.endpoint}{path}?{urlencode(params)}"

        request = Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )

        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus query failed: {payload.get('error', 'unknown error')}"
            )

        return payload

    def instant_query(self, query: str, time: float | None = None) -> dict[str, Any]:
        """Execute an instant PromQL query."""
        params: dict[str, Any] = {"query": query}

        if time is not None:
            params["time"] = time

        return self._request("/api/v1/query", params)

    def range_query(
        self,
        query: str,
        start: float,
        end: float,
        step: str | int,
    ) -> dict[str, Any]:
        """Execute a range PromQL query."""
        return self._request(
            "/api/v1/query_range",
            {
                "query": query,
                "start": start,
                "end": end,
                "step": step,
            },
        )

    def query_pod_metrics(self, namespace: str, pod: str) -> dict[str, Any]:
        """Query CPU, memory, restarts and network metrics for a pod."""
        return {
            "cpu": self.instant_query(
                f'sum(rate(container_cpu_usage_seconds_total'
                f'{{namespace="{namespace}",pod="{pod}"}}[5m]))'
            ),
            "memory": self.instant_query(
                f'sum(container_memory_working_set_bytes'
                f'{{namespace="{namespace}",pod="{pod}"}})'
            ),
            "restarts": self.instant_query(
                f'kube_pod_container_status_restarts_total'
                f'{{namespace="{namespace}",pod="{pod}"}}'
            ),
            "network_receive": self.instant_query(
                f'sum(rate(container_network_receive_bytes_total'
                f'{{namespace="{namespace}",pod="{pod}"}}[5m]))'
            ),
            "network_transmit": self.instant_query(
                f'sum(rate(container_network_transmit_bytes_total'
                f'{{namespace="{namespace}",pod="{pod}"}}[5m]))'
            ),
        }

    def query_node_metrics(self, node: str) -> dict[str, Any]:
        """Query CPU and memory metrics for a Kubernetes node."""
        return {
            "cpu": self.instant_query(
                f'1 - avg(rate(node_cpu_seconds_total'
                f'{{instance="{node}",mode="idle"}}[5m]))'
            ),
            "memory": self.instant_query(
                f'1 - (node_memory_MemAvailable_bytes'
                f'{{instance="{node}"}} / '
                f'node_memory_MemTotal_bytes{{instance="{node}"}})'
            ),
        }

    def collect(self, **kwargs: Any) -> list[Evidence]:
        """Collect Prometheus evidence."""
        namespace = kwargs.get("namespace")
        pod = kwargs.get("pod")
        node = kwargs.get("node")

        evidence: list[Evidence] = []

        if namespace and pod:
            pod_metrics = self.query_pod_metrics(namespace, pod)

            for metric_type, data in pod_metrics.items():
                evidence.append(
                    self.normalize(
                        Evidence(
                            source=self.source,
                            evidence_type="metric",
                            timestamp=datetime.now(timezone.utc),
                            namespace=namespace,
                            resource=pod,
                            data={
                                "metric": metric_type,
                                "values": data,
                            },
                        )
                    )
                )

        if node:
            node_metrics = self.query_node_metrics(node)

            for metric_type, data in node_metrics.items():
                evidence.append(
                    self.normalize(
                        Evidence(
                            source=self.source,
                            evidence_type="metric",
                            timestamp=datetime.now(timezone.utc),
                            resource=node,
                            data={
                                "metric": metric_type,
                                "values": data,
                            },
                        )
                    )
                )

        return evidence