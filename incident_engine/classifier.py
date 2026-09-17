from dataclasses import dataclass, field
from typing import Any

from incident_engine.detector import IncidentCandidate


@dataclass
class IncidentClassification:
    """
    Explainable classification of an incident candidate.
    """

    category: str
    confidence: float
    evidence_references: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "evidence_references": self.evidence_references,
            "explanation": self.explanation,
        }


class IncidentClassifier:
    """
    Deterministic and explainable incident classifier.

    Categories:
    - Scheduling
    - Resource
    - Application
    - Networking
    - Dependency
    - Configuration
    - Infrastructure
    - Unknown
    """

    def classify(
        self,
        incident: IncidentCandidate,
    ) -> IncidentClassification:

        title = incident.title.lower()
        detector = incident.detector.lower()

        category = "Unknown"
        confidence = 0.50
        reason = "No specific classification rule matched."

        # Scheduling failures
        if (
            "pending" in title
            or "scheduling" in title
            or "failedscheduling" in title
        ):
            category = "Scheduling"
            confidence = 0.95
            reason = (
                "Incident indicates a Kubernetes scheduling failure."
            )

        # Resource failures
        elif (
            "cpu" in title
            or "memory" in title
            or "oomkilled" in title
        ):
            category = "Resource"
            confidence = 0.95
            reason = (
                "Incident indicates CPU, memory, or resource exhaustion."
            )

        # Application failures
        elif (
            "application" in title
            or "trace error" in title
            or "crashloopbackoff" in title
            or "exception" in title
        ):
            category = "Application"
            confidence = 0.90
            reason = (
                "Incident indicates an application-level failure or error."
            )

        # Networking failures
        elif any(
            word in title
            for word in (
                "network",
                "connection",
                "timeout",
                "dns",
            )
        ):
            category = "Networking"
            confidence = 0.85
            reason = (
                "Incident indicates a networking or connectivity problem."
            )

        # Dependency failures
        elif any(
            word in title
            for word in (
                "dependency",
                "upstream",
                "downstream",
            )
        ):
            category = "Dependency"
            confidence = 0.85
            reason = (
                "Incident indicates a dependency relationship failure."
            )

        # Configuration failures
        elif any(
            word in title
            for word in (
                "configuration",
                "config",
            )
        ):
            category = "Configuration"
            confidence = 0.85
            reason = (
                "Incident indicates a configuration-related problem."
            )

        # Infrastructure failures
        elif any(
            word in title
            for word in (
                "node",
                "infrastructure",
                "disk",
            )
        ):
            category = "Infrastructure"
            confidence = 0.80
            reason = (
                "Incident indicates an infrastructure-level problem."
            )

        evidence_references = []

        if incident.evidence is not None:
            evidence_references.append(
                f"{incident.evidence.source}:"
                f"{incident.evidence.evidence_type}"
            )

        explanation = (
            f"{reason} "
            f"Detector: {incident.detector}."
        )

        return IncidentClassification(
            category=category,
            confidence=confidence,
            evidence_references=evidence_references,
            explanation=explanation,
        )