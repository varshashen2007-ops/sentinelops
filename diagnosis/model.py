from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceReference:
    """
    Reference to evidence supporting a diagnosis.

    The diagnosis stores a lightweight representation of the
    underlying evidence rather than owning or modifying the
    original evidence object.
    """

    source: str
    evidence_type: str
    description: str
    timestamp: str | None = None
    resource: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "timestamp": self.timestamp,
            "resource": self.resource,
            "data": self.data,
        }


@dataclass
class Diagnosis:
    """
    Evidence-grounded diagnosis of a Kubernetes incident.

    A diagnosis is an explanation supported by explicit evidence
    references and optionally informed by retrieved historical
    incidents.
    """

    summary: str
    root_cause: str
    confidence: float
    evidence_references: list[EvidenceReference] = field(
        default_factory=list
    )
    historical_incident_ids: list[str] = field(
        default_factory=list
    )
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "evidence_references": [
                reference.to_dict()
                for reference in self.evidence_references
            ],
            "historical_incident_ids": self.historical_incident_ids,
            "explanation": self.explanation,
        }