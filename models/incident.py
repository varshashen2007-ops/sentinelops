from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentDNA(BaseModel):
    """Deterministic fingerprint describing an incident."""

    trigger: str | None = None
    failure: str | None = None
    restart_pattern: str | None = None
    readiness: str | None = None
    affected_workload: str | None = None
    duration: float | None = None
    severity: str | None = None
    dependency_information: dict[str, Any] = Field(default_factory=dict)
    anomaly_information: dict[str, Any] = Field(default_factory=dict)


class Timeline(BaseModel):
    """Chronological evidence associated with an incident."""

    entries: list[Any] = Field(default_factory=list)


class Diagnosis(BaseModel):
    """Evidence-grounded diagnosis of an incident."""

    root_cause: str | None = None
    confidence: float | None = None
    evidence: list[Any] = Field(default_factory=list)
    timeline_references: list[Any] = Field(default_factory=list)
    similar_incidents: list[Any] = Field(default_factory=list)
    explanation: str | None = None


class Resolution(BaseModel):
    """Resolution information for an incident."""

    action: str | None = None
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class Outcome(BaseModel):
    """Observed outcome after incident handling."""

    resolved: bool = False
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    """Storage-independent domain model representing an incident."""

    id: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    severity: str | None = None
    status: str | None = None

    dna: IncidentDNA | None = None
    timeline: Timeline | None = None
    diagnosis: Diagnosis | None = None
    resolution: Resolution | None = None
    outcome: Outcome | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)