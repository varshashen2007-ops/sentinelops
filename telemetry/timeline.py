from datetime import datetime
from typing import Iterable

from models.evidence import Evidence


class TimelineDataAccess:
    """Efficient access to already-collected telemetry evidence."""

    def __init__(self, evidence: Iterable[Evidence] | None = None) -> None:
        self._evidence = list(evidence or [])

    def add(self, evidence: Evidence) -> None:
        """Add evidence to the local timeline data set."""
        self._evidence.append(evidence)

    def query(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        entity: str | None = None,
        source: str | None = None,
        namespace: str | None = None,
        resource: str | None = None,
    ) -> list[Evidence]:
        """Return evidence matching the requested timeline filters."""
        results = self._evidence

        if start_time is not None:
            results = [
                item for item in results
                if item.timestamp >= start_time
            ]

        if end_time is not None:
            results = [
                item for item in results
                if item.timestamp <= end_time
            ]

        if source is not None:
            results = [
                item for item in results
                if item.source == source
            ]

        if entity is not None:
            results = [
                item for item in results
                if self._metadata(item, "entity") == entity
            ]

        if namespace is not None:
            results = [
                item for item in results
                if self._metadata(item, "namespace") == namespace
            ]

        if resource is not None:
            results = [
                item for item in results
                if self._metadata(item, "resource") == resource
            ]

        return sorted(results, key=lambda item: item.timestamp)

    @staticmethod
    @staticmethod
    def _metadata(evidence: Evidence, field: str):
        """Read a filter field from the evidence model, metadata, or data."""
        value = getattr(evidence, field, None)

        if value is not None:
            return value

        metadata = getattr(evidence, "metadata", None)

        if isinstance(metadata, dict) and field in metadata:
            return metadata[field]

        data = getattr(evidence, "data", None)

        if isinstance(data, dict):
            return data.get(field)

        return None