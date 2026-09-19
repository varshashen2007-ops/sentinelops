from datetime import datetime, timezone
from typing import Any

import requests

from collectors.base import BaseCollector
from models.evidence import Evidence


class PrometheusCollector(BaseCollector):
    """
    Collector for retrieving metrics from Prometheus.

    Prometheus is accessed through its HTTP API.
    The collector converts returned metric samples into
    SentinelOps Evidence objects.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9090",
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def collect(self) -> list[Evidence]:
        """
        Collect a basic set of Kubernetes-related metrics.

        This method provides the common BaseCollector interface.
        More specialized metric queries are exposed through
        instant_query(), range_query(), and query_pod_metrics().
        """
        evidence = []

        queries = {
            "up": "up",
            "node_cpu": "sum(rate(node_cpu_seconds_total[5m])) by (instance)",
            "pod_restarts": (
                "sum(kube_pod_container_status_restarts_total) "
                "by (namespace, pod)"
            ),
        }

        for metric_name, query in queries.items():
            try:
                results = self.instant_query(query)

                for result in results:
                    evidence.append(
                        self._result_to_evidence(
                            result=result,
                            metric_name=metric_name,
                        )
                    )

            except requests.RequestException:
                # One failed metric query should not prevent
                # the collector from attempting other metrics.
                continue

        return evidence

    def instant_query(self, query: str) -> list[dict[str, Any]]:
        """
        Execute an instant PromQL query.

        Returns the Prometheus result list.
        """
        response = requests.get(
            f"{self.base_url}/api/v1/query",
            params={"query": query},
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus query failed: {payload}"
            )

        data = payload.get("data", {})

        return data.get("result", [])

    def range_query(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "30s",
    ) -> list[dict[str, Any]]:
        """
        Execute a PromQL range query.

        Example:
            range_query(
                'up',
                start,
                end,
                '30s'
            )
        """
        start = self._ensure_utc(start)
        end = self._ensure_utc(end)

        response = requests.get(
            f"{self.base_url}/api/v1/query_range",
            params={
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus range query failed: {payload}"
            )

        data = payload.get("data", {})

        return data.get("result", [])

    def query_pod_metrics(
        self,
        namespace: str,
        pod: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Query commonly useful metrics for a specific Kubernetes Pod.

        Returns CPU, memory, and restart metrics.
        """

        queries = {
            "cpu": (
                "sum(rate(container_cpu_usage_seconds_total"
                f'{{namespace="{namespace}",pod="{pod}"}}[5m]))'
            ),
            "memory": (
                "sum(container_memory_working_set_bytes"
                f'{{namespace="{namespace}",pod="{pod}"}})'
            ),
            "restarts": (
                "sum(kube_pod_container_status_restarts_total"
                f'{{namespace="{namespace}",pod="{pod}"}})'
            ),
        }

        results = {}

        for metric_name, query in queries.items():
            results[metric_name] = self.instant_query(query)

        return results

    def _result_to_evidence(
        self,
        result: dict[str, Any],
        metric_name: str,
    ) -> Evidence:
        """
        Convert one Prometheus API result into SentinelOps Evidence.
        """

        metric = result.get("metric", {})
        value = result.get("value")

        timestamp = datetime.now(timezone.utc)

        if value and len(value) >= 1:
            try:
                timestamp = datetime.fromtimestamp(
                    float(value[0]),
                    tz=timezone.utc,
                )
            except (TypeError, ValueError, OverflowError):
                pass

        namespace = metric.get("namespace")
        resource = (
            metric.get("pod")
            or metric.get("deployment")
            or metric.get("instance")
            or metric.get("node")
        )

        return Evidence(
            source="prometheus",
            evidence_type="metric",
            timestamp=timestamp,
            namespace=namespace,
            resource=resource,
            data={
                "metric_name": metric_name,
                "labels": metric,
                "value": value[1] if value and len(value) > 1 else None,
            },
        )

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        """
        Ensure a datetime is timezone-aware and represented in UTC.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)