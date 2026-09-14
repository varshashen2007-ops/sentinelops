from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence


@dataclass
class AnomalyCandidate:
    """
    Represents a detected anomaly and explains why
    it is considered important.
    """

    detector: str
    title: str
    anomaly_type: str
    score: float
    timestamp: datetime
    namespace: str | None = None
    resource: str | None = None
    reasons: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"AnomalyCandidate("
            f"title={self.title!r}, "
            f"type={self.anomaly_type!r}, "
            f"score={self.score:.2f}, "
            f"resource={self.resource!r})"
        )


class BaseAnomalyDetector:
    """
    Base interface for anomaly detectors.
    """

    def detect(
        self,
        incident: IncidentCandidate,
        evidence: list[Evidence],
    ) -> list[AnomalyCandidate]:
        raise NotImplementedError


class ResourceAnomalyDetector(BaseAnomalyDetector):
    """
    Detect resource-related anomalies using explicit,
    explainable rules.
    """

    def detect(
        self,
        incident: IncidentCandidate,
        evidence: list[Evidence],
    ) -> list[AnomalyCandidate]:

        candidates: list[AnomalyCandidate] = []

        related = [
            item
            for item in evidence
            if self._is_related(incident, item)
        ]

        metrics = [
            item
            for item in related
            if item.source == "prometheus"
            and item.evidence_type == "metric"
        ]

        for metric in metrics:
            data = metric.data or {}

            metric_name = str(
                data.get("metric_name")
                or data.get("name")
                or ""
            ).lower()

            value = self._to_float(data.get("value"))

            if value is None:
                continue

            # High CPU
            if "cpu" in metric_name and value >= 0.90:
                candidates.append(
                    AnomalyCandidate(
                        detector="ResourceAnomalyDetector",
                        title="High CPU Usage",
                        anomaly_type="actionable_anomaly",
                        score=0.80,
                        timestamp=metric.timestamp,
                        namespace=metric.namespace,
                        resource=metric.resource,
                        reasons=[
                            "CPU usage reached or exceeded 90%"
                        ],
                        evidence=[metric],
                    )
                )

            # High memory
            elif "memory" in metric_name and value >= 0.90:
                candidates.append(
                    AnomalyCandidate(
                        detector="ResourceAnomalyDetector",
                        title="High Memory Usage",
                        anomaly_type="actionable_anomaly",
                        score=0.90,
                        timestamp=metric.timestamp,
                        namespace=metric.namespace,
                        resource=metric.resource,
                        reasons=[
                            "Memory usage reached or exceeded 90%"
                        ],
                        evidence=[metric],
                    )
                )

        return candidates

    @staticmethod
    def _is_related(
        incident: IncidentCandidate,
        evidence: Evidence,
    ) -> bool:

        if (
            incident.namespace is not None
            and evidence.namespace is not None
            and incident.namespace != evidence.namespace
        ):
            return False

        if (
            incident.resource is not None
            and evidence.resource is not None
            and incident.resource != evidence.resource
        ):
            return False

        return True

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class FailureAnomalyDetector(BaseAnomalyDetector):
    """
    Connect detected failures with their preceding evidence.

    This helps distinguish a final failure from an earlier
    potentially actionable condition.
    """

    def detect(
        self,
        incident: IncidentCandidate,
        evidence: list[Evidence],
    ) -> list[AnomalyCandidate]:

        candidates: list[AnomalyCandidate] = []

        related = [
            item
            for item in evidence
            if self._is_related(incident, item)
        ]

        if incident.title == "OOMKilled":
            memory_evidence = []

            for item in related:
                if item.source != "prometheus":
                    continue

                data = item.data or {}

                metric_name = str(
                    data.get("metric_name")
                    or data.get("name")
                    or ""
                ).lower()

                if "memory" not in metric_name:
                    continue

                value = self._to_float(data.get("value"))

                if value is not None:
                    memory_evidence.append(item)

            if memory_evidence:
                memory_evidence.sort(
                    key=lambda item: item.timestamp
                )

                first = memory_evidence[0]

                candidates.append(
                    AnomalyCandidate(
                        detector="FailureAnomalyDetector",
                        title="Memory Pressure Before OOMKilled",
                        anomaly_type="actionable_anomaly",
                        score=0.95,
                        timestamp=first.timestamp,
                        namespace=first.namespace,
                        resource=first.resource,
                        reasons=[
                            "Memory evidence occurred before OOMKilled",
                            "Memory pressure may have preceded the failure",
                        ],
                        evidence=memory_evidence,
                    )
                )

        return candidates

    @staticmethod
    def _is_related(
        incident: IncidentCandidate,
        evidence: Evidence,
    ) -> bool:

        if (
            incident.namespace is not None
            and evidence.namespace is not None
            and incident.namespace != evidence.namespace
        ):
            return False

        if (
            incident.resource is not None
            and evidence.resource is not None
            and incident.resource != evidence.resource
        ):
            return False

        return True

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class AnomalyAnalyzer:
    """
    Coordinates anomaly detectors and returns explainable
    anomaly candidates.
    """

    def __init__(
        self,
        detectors: list[BaseAnomalyDetector] | None = None,
    ):
        self.detectors = detectors or [
            ResourceAnomalyDetector(),
            FailureAnomalyDetector(),
        ]

    def analyze(
        self,
        incident: IncidentCandidate,
        evidence: list[Evidence],
    ) -> list[AnomalyCandidate]:

        anomalies: list[AnomalyCandidate] = []

        for detector in self.detectors:
            anomalies.extend(
                detector.detect(
                    incident,
                    evidence,
                )
            )

        return sorted(
            anomalies,
            key=lambda anomaly: (
                anomaly.timestamp,
                -anomaly.score,
            ),
        )