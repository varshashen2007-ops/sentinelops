from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from incident_engine.timeline import IncidentTimeline


class TimelineStore(ABC):
    """Storage interface for incident timelines."""

    @abstractmethod
    def save(self, timeline: "IncidentTimeline") -> str:
        """Persist a timeline and return its identifier."""
        raise NotImplementedError

    @abstractmethod
    def get(self, timeline_id: str) -> "IncidentTimeline | None":
        """Retrieve a timeline by identifier."""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list["IncidentTimeline"]:
        """Return stored timelines."""
        raise NotImplementedError

    @abstractmethod
    def search(self, **filters: Any) -> list["IncidentTimeline"]:
        """Search timelines using storage-level filters."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, timeline_id: str) -> bool:
        """Delete a timeline."""
        raise NotImplementedError