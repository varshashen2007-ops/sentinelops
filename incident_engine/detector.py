from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from models.evidence import Evidence


class IncidentCandidate:
    """
    Represents a detected incident candidate.

    A candidate is evidence that a failure, anomaly, or error
    may require further investigation.
    """

    def __init__(
        self,
        detector: str,
        title: str,
        severity: str,
        timestamp: datetime,
        namespace: str | None = None,
        resource: str | None = None,
        evidence: Evidence | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.detector = detector
        self.title = title
        self.severity = severity
        self.timestamp = timestamp
        self.namespace = namespace
        self.resource = resource
        self.evidence = evidence
        self.details = details or {}

    def __repr__(self) -> str:
        return (
            f"IncidentCandidate("
            f"detector={self.detector!r}, "
            f"title={self.title!r}, "
            f"severity={self.severity!r}, "
            f"resource={self.resource!r})"
        )


class BaseDetector(ABC):
    """
    Base interface for all incident detectors.
    """

    @abstractmethod
    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[IncidentCandidate]:
        """
        Inspect evidence and return detected incident candidates.
        """
        raise NotImplementedError


class KubernetesFailureDetector(BaseDetector):
    """
    Detect Kubernetes workload and scheduling failures.

    Supported failures:
    - CrashLoopBackOff
    - OOMKilled
    - Pending
    - FailedScheduling
    - readiness failures
    """

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[IncidentCandidate]:

        candidates: list[IncidentCandidate] = []

        for item in evidence:
            if item.source != "kubernetes":
                continue

            data = item.data or {}

            reason = str(data.get("reason", "")).lower()
            message = str(data.get("message", "")).lower()
            status = str(data.get("status", "")).lower()

            text = f"{reason} {message} {status}"

            title = None
            severity = "warning"

            if "crashloopbackoff" in text:
                title = "CrashLoopBackOff"
                severity = "critical"

            elif "oomkilled" in text:
                title = "OOMKilled"
                severity = "critical"

            elif "failedscheduling" in text:
                title = "FailedScheduling"
                severity = "critical"

            elif "pending" in text:
                title = "Pod Pending"
                severity = "warning"

            elif (
                "readiness" in text
                and (
                    "fail" in text
                    or "false" in text
                    or "unready" in text
                )
            ):
                title = "Readiness Failure"
                severity = "warning"

            if title is None:
                continue

            candidates.append(
                IncidentCandidate(
                    detector="KubernetesFailureDetector",
                    title=title,
                    severity=severity,
                    timestamp=item.timestamp,
                    namespace=item.namespace,
                    resource=item.resource,
                    evidence=item,
                    details=data,
                )
            )

        return candidates


class ResourceDetector(BaseDetector):
    """
    Detect high CPU and high memory conditions.

    Thresholds are intentionally explicit and explainable.
    """

    def __init__(
        self,
        cpu_threshold: float = 0.90,
        memory_threshold: float = 0.90,
    ):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[IncidentCandidate]:

        candidates: list[IncidentCandidate] = []

        for item in evidence:
            if item.source != "prometheus":
                continue

            if item.evidence_type != "metric":
                continue

            data = item.data or {}

            metric_name = str(
                data.get("metric_name")
                or data.get("name")
                or ""
            ).lower()

            raw_value = data.get("value")

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            title = None

            if "cpu" in metric_name and value >= self.cpu_threshold:
                title = "High CPU"

            elif (
                "memory" in metric_name
                and value >= self.memory_threshold
            ):
                title = "High Memory"

            if title is None:
                continue

            candidates.append(
                IncidentCandidate(
                    detector="ResourceDetector",
                    title=title,
                    severity="warning",
                    timestamp=item.timestamp,
                    namespace=item.namespace,
                    resource=item.resource,
                    evidence=item,
                    details={
                        "metric_name": metric_name,
                        "value": value,
                    },
                )
            )

        return candidates


class ApplicationErrorDetector(BaseDetector):
    """
    Detect application errors from Loki logs and Jaeger traces.
    """

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[IncidentCandidate]:

        candidates: list[IncidentCandidate] = []

        for item in evidence:

            if item.source == "loki":
                self._detect_log_error(item, candidates)

            elif item.source == "jaeger":
                self._detect_trace_error(item, candidates)

        return candidates

    @staticmethod
    def _detect_log_error(
        item: Evidence,
        candidates: list[IncidentCandidate],
    ) -> None:

        message = str(
            (item.data or {}).get("message", "")
        ).lower()

        labels = (item.data or {}).get("labels", {})

        severity = str(
            labels.get("level")
            or labels.get("severity")
            or ""
        ).lower()

        if (
            severity in {"error", "critical", "fatal"}
            or "error" in message
            or "exception" in message
            or "fatal" in message
        ):
            candidates.append(
                IncidentCandidate(
                    detector="ApplicationErrorDetector",
                    title="Application Error",
                    severity="error",
                    timestamp=item.timestamp,
                    namespace=item.namespace,
                    resource=item.resource,
                    evidence=item,
                    details={
                        "message": message,
                        "severity": severity,
                    },
                )
            )

    @staticmethod
    def _detect_trace_error(
        item: Evidence,
        candidates: list[IncidentCandidate],
    ) -> None:

        data = item.data or {}

        status = str(
            data.get("status", "")
        ).lower()

        if status in {
            "error",
            "failed",
            "failure",
        }:
            candidates.append(
                IncidentCandidate(
                    detector="ApplicationErrorDetector",
                    title="Trace Error",
                    severity="error",
                    timestamp=item.timestamp,
                    namespace=item.namespace,
                    resource=item.resource,
                    evidence=item,
                    details={
                        "trace_status": status,
                    },
                )
            )


class IncidentDetector:
    """
    Coordinates all Day 8 detectors.
    """

    def __init__(
        self,
        detectors: list[BaseDetector] | None = None,
    ):
        self.detectors = detectors or [
            KubernetesFailureDetector(),
            ResourceDetector(),
            ApplicationErrorDetector(),
        ]

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[IncidentCandidate]:

        candidates: list[IncidentCandidate] = []

        for detector in self.detectors:
            candidates.extend(
                detector.detect(evidence)
            )

        return sorted(
            candidates,
            key=lambda candidate: candidate.timestamp,
        )