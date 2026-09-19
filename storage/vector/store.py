from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VectorRecord:
    """A vector plus metadata stored in the vector store."""

    record_id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorSearchResult:
    """A vector search result."""

    record_id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """Backend-independent interface for vector storage."""

    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None:
        """Insert or replace vector records."""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        vector: list[float],
        *,
        limit: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search vectors, optionally filtering by metadata."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, record_ids: list[str]) -> None:
        """Delete records by ID."""
        raise NotImplementedError

class InMemoryVectorStore(VectorStore):
    """Small deterministic vector store for tests and local development."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        for record in records:
            self._records[record.record_id] = record

    def search(
        self,
        vector: list[float],
        *,
        limit: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        if limit <= 0:
            return []

        results: list[VectorSearchResult] = []

        for record in self._records.values():
            if metadata_filter and any(
                record.metadata.get(key) != value
                for key, value in metadata_filter.items()
            ):
                continue

            score = self._cosine_similarity(vector, record.vector)

            results.append(
                VectorSearchResult(
                    record_id=record.record_id,
                    score=score,
                    metadata=dict(record.metadata),
                )
            )

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:limit]

    def delete(self, record_ids: list[str]) -> None:
        for record_id in record_ids:
            self._records.pop(record_id, None)

    @staticmethod
    def _cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:
        if len(left) != len(right):
            raise ValueError("Vectors must have the same dimension")

        if not left:
            raise ValueError("Vectors must not be empty")

        dot = sum(a * b for a, b in zip(left, right))
        left_norm = sum(value * value for value in left) ** 0.5
        right_norm = sum(value * value for value in right) ** 0.5

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot / (left_norm * right_norm)    