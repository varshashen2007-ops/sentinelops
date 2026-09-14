from dataclasses import dataclass
from datetime import datetime
from typing import Any

from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence


@dataclass
class TimelineEntry:
    """
    One chronological event in an incident timeline.
    """

    timestamp: datetime
    source: str
    description: str
    namespace: str | None = None
    resource: str | None = None
    evidence: Evidence | None = None


@dataclass
class IncidentTimeline:
    """
    Chronological timeline for one incident.
    """

    incident: IncidentCandidate
    entries: list[TimelineEntry]

    def __post_init__(self) -> None:
        self.entries.sort(key=lambda entry: entry.timestamp)


class IncidentTimelineBuilder:
    """
    Builds an IncidentTimeline from an IncidentCandidate
    and related Evidence objects.
    """

    def build(
        self,
        incident: IncidentCandidate,
        evidence: list[Evidence],
    ) -> IncidentTimeline:

        related = [
            item
            for item in evidence
            if self._is_related(incident, item)
        ]

        entries = [
            self._evidence_to_entry(item)
            for item in related
        ]

        # Make sure the incident itself is also represented
        # in the timeline.
        if incident.evidence is not None:
            incident_evidence = incident.evidence

            if not any(
                entry.evidence is incident_evidence
                for entry in entries
            ):
                entries.append(
                    self._evidence_to_entry(
                        incident_evidence
                    )
                )

        return IncidentTimeline(
            incident=incident,
            entries=sorted(
                entries,
                key=lambda entry: entry.timestamp,
            ),
        )

    @staticmethod
    def _is_related(
        incident: IncidentCandidate,
        evidence: Evidence,
    ) -> bool:
        """
        Determine whether evidence belongs to the incident.

        Matching is intentionally explainable:
        namespace + resource are used when available.
        """

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
    def _evidence_to_entry(
        evidence: Evidence,
    ) -> TimelineEntry:
        """
        Convert normalized Evidence into a human-readable
        timeline entry.
        """

        description = (
            IncidentTimelineBuilder
            ._describe_evidence(evidence)
        )

        return TimelineEntry(
            timestamp=evidence.timestamp,
            source=evidence.source,
            description=description,
            namespace=evidence.namespace,
            resource=evidence.resource,
            evidence=evidence,
        )

    @staticmethod
    def _describe_evidence(
        evidence: Evidence,
    ) -> str:
        """
        Generate a concise description based on the
        evidence type.
        """

        data = evidence.data or {}

        if evidence.source == "kubernetes":
            reason = data.get("reason")
            message = data.get("message")
            status = data.get("status")

            if reason:
                return str(reason)

            if message:
                return str(message)

            if status:
                return f"Pod status: {status}"

            return "Kubernetes event"

        if evidence.source == "prometheus":
            metric_name = (
                data.get("metric_name")
                or data.get("name")
                or "metric"
            )

            value = data.get("value")

            if value is not None:
                return f"{metric_name}: {value}"

            return str(metric_name)

        if evidence.source == "loki":
            message = data.get("message")

            if message:
                return str(message)

            return "Application log"

        if evidence.source == "jaeger":
            operation = data.get("operation_name")
            status = data.get("status")

            if operation and status:
                return f"{operation} ({status})"

            if operation:
                return str(operation)

            return "Trace"

        return f"{evidence.source} {evidence.evidence_type}"