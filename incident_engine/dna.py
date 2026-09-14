from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class IncidentDNA:
    """
    Deterministic and serializable representation of an incident.

    Incident DNA summarizes the important characteristics of an
    incident for later classification, novelty detection, and memory.
    """

    trigger: str | None = None
    failure: str | None = None
    restart_pattern: str | None = None
    readiness: str | None = None
    affected_workload: str | None = None
    duration: float | None = None
    severity: str | None = None
    dependency_information: dict[str, Any] | None = None
    anomaly_information: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Incident DNA into a deterministic dictionary.
        """
        return asdict(self)

    def to_json_dict(self) -> dict[str, Any]:
        """
        Return a JSON-serializable representation.

        This is intentionally kept separate from domain logic so
        persistence implementations can serialize the model later.
        """
        return self.to_dict()