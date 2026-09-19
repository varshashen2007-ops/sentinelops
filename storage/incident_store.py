from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from models.incident import Incident


class IncidentStore(ABC):
    """Storage interface for incidents."""

    @abstractmethod
    def save(self, incident: "Incident") -> str:
        """Persist an incident and return its identifier."""
        raise NotImplementedError

    @abstractmethod
    def get(self, incident_id: str) -> "Incident | None":
        """Retrieve an incident by identifier."""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list["Incident"]:
        """Return stored incidents."""
        raise NotImplementedError

    @abstractmethod
    def search(self, **filters: Any) -> list["Incident"]:
        """Search incidents using storage-level filters."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, incident_id: str) -> bool:
        """Delete an incident."""
        raise NotImplementedError