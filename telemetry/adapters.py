from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from models.evidence import Evidence


class TelemetryAdapter(ABC):
    """Common interface for telemetry source adapters."""

    source: str = "unknown"

    @abstractmethod
    def collect(self, **kwargs: Any) -> list[Evidence]:
        """Collect and return normalized telemetry evidence."""
        raise NotImplementedError

    def normalize(
        self,
        evidence: Evidence,
        *,
        timestamp: datetime | None = None,
    ) -> Evidence:
        """Normalize common metadata before evidence is consumed."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        evidence.timestamp = timestamp
        evidence.source = self.source

        return evidence