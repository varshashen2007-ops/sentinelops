from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from incident_engine.dna import IncidentDNA


@dataclass
class IncidentTimeline:
    """Chronological events associated with an incident."""

    entries: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class IncidentDiagnosis:
    """Diagnosis produced for an incident."""

    summary: str
    root_cause: str | None = None
    evidence_references: list[str] = field(default_factory=list)


@dataclass
class IncidentResolution:
    """Recovery action associated with an incident."""

    action: str
    description: str | None = None


@dataclass
class IncidentOutcome:
    """Observed result after a resolution."""

    status: str
    description: str | None = None
    verified: bool = False


@dataclass(init=False)
class Incident:
    """
    Canonical, storage-independent domain representation of an incident.

    The canonical identifier is ``incident_id``. Compatibility aliases
    ``id`` and ``timestamp`` are provided for infrastructure code that
    uses Dhrithi's storage contract.
    """

    incident_id: str
    started_at: datetime
    ended_at: datetime | None

    dna: IncidentDNA | None
    timeline: IncidentTimeline
    diagnosis: IncidentDiagnosis | None
    resolution: IncidentResolution | None
    outcome: IncidentOutcome | None
    metadata: dict[str, Any]

    severity: str | None
    status: str | None

    def __init__(
        self,
        incident_id: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        dna: IncidentDNA | None = None,
        timeline: IncidentTimeline | None = None,
        diagnosis: IncidentDiagnosis | None = None,
        resolution: IncidentResolution | None = None,
        outcome: IncidentOutcome | None = None,
        metadata: dict[str, Any] | None = None,
        severity: str | None = None,
        status: str | None = None,
        *,
        id: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        if incident_id is not None and id is not None and incident_id != id:
            raise ValueError(
                "incident_id and id must refer to the same incident."
            )

        resolved_id = incident_id if incident_id is not None else id

        if resolved_id is None:
            raise ValueError("Incident must provide an incident_id or id.")

        if started_at is not None and timestamp is not None and started_at != timestamp:
            raise ValueError(
                "started_at and timestamp must refer to the same time."
            )

        resolved_started_at = (
            started_at
            if started_at is not None
            else timestamp
        )

        if resolved_started_at is None:
            raise ValueError(
                "Incident must provide started_at or timestamp."
            )

        self.incident_id = resolved_id
        self.started_at = resolved_started_at
        self.ended_at = ended_at
        self.dna = dna
        self.timeline = (
            timeline
            if timeline is not None
            else IncidentTimeline()
        )
        self.diagnosis = diagnosis
        self.resolution = resolution
        self.outcome = outcome
        self.metadata = (
            metadata
            if metadata is not None
            else {}
        )
        self.severity = severity
        self.status = status

    @property
    def id(self) -> str:
        """Compatibility alias for the canonical incident_id."""
        return self.incident_id

    @property
    def timestamp(self) -> datetime:
        """Compatibility alias for the incident start timestamp."""
        return self.started_at