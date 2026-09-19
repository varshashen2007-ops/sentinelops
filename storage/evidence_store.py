from abc import ABC, abstractmethod
from typing import Any

from models.evidence import Evidence


class EvidenceStore(ABC):
    """Storage interface for telemetry evidence."""

    @abstractmethod
    def save(self, evidence: Evidence) -> str:
        """Persist evidence and return its identifier."""
        raise NotImplementedError

    @abstractmethod
    def get(self, evidence_id: str) -> Evidence | None:
        """Retrieve evidence by identifier."""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Evidence]:
        """Return all stored evidence."""
        raise NotImplementedError

    @abstractmethod
    def search(self, **filters: Any) -> list[Evidence]:
        """Search evidence using storage-level filters."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, evidence_id: str) -> bool:
        """Delete evidence and report whether it existed."""
        raise NotImplementedError