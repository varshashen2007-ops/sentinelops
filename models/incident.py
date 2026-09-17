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


@dataclass
class Incident:
    """
    Storage-independent domain representation of an incident.

    Persistence layers may serialize this model later, but the
    incident domain itself does not depend on a database.
    """

    incident_id: str
    started_at: datetime
    ended_at: datetime | None = None

    dna: IncidentDNA | None = None
    timeline: IncidentTimeline = field(
        default_factory=IncidentTimeline
    )
    diagnosis: IncidentDiagnosis | None = None
    resolution: IncidentResolution | None = None
    outcome: IncidentOutcome | None = None

    metadata: dict[str, Any] = field(default_factory=dict)