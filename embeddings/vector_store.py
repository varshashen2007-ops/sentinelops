from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class VectorRecord:
    """
    A stored vector and the metadata associated with it.
    """

    record_id: str
    vector: list[float]
    metadata: dict[str, Any]


@dataclass
class VectorMatch:
    """
    A vector record returned by similarity search.
    """

    record_id: str
    similarity_score: float
    metadata: dict[str, Any]


class InMemoryVectorStore:
    """
    Simple in-memory vector index.

    This implementation is intentionally storage-independent.
    A persistent vector database can replace it later without
    changing the similarity-search contract.
    """

    def __init__(self, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")

        self.dimensions = dimensions
        self._records: dict[str, VectorRecord] = {}

    def add(
        self,
        record_id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add or replace a vector record.
        """

        self._validate_vector(vector)

        self._records[record_id] = VectorRecord(
            record_id=record_id,
            vector=list(vector),
            metadata=metadata or {},
        )

    def add_many(
        self,
        records: list[VectorRecord],
    ) -> None:
        """
        Add multiple vector records.
        """

        for record in records:
            self.add(
                record_id=record.record_id,
                vector=record.vector,
                metadata=record.metadata,
            )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[VectorMatch]:
        """
        Return the most similar stored vectors.

        Similarity is cosine similarity. Because embeddings generated
        by our provider are normalized, cosine similarity can also be
        computed as the dot product.
        """

        self._validate_vector(query_vector)

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        if not self._records:
            return []

        query = np.asarray(query_vector, dtype=np.float32)

        matches: list[VectorMatch] = []

        for record in self._records.values():
            vector = np.asarray(record.vector, dtype=np.float32)

            similarity = float(np.dot(query, vector))

            matches.append(
                VectorMatch(
                    record_id=record.record_id,
                    similarity_score=round(similarity, 4),
                    metadata=dict(record.metadata),
                )
            )

        matches.sort(
            key=lambda match: match.similarity_score,
            reverse=True,
        )

        return matches[:top_k]

    def get(self, record_id: str) -> VectorRecord | None:
        """Return a stored record by ID."""

        return self._records.get(record_id)

    def count(self) -> int:
        """Return the number of stored vectors."""

        return len(self._records)

    def clear(self) -> None:
        """Remove all stored vectors."""

        self._records.clear()

    def _validate_vector(self, vector: list[float]) -> None:
        if not isinstance(vector, list):
            raise TypeError("vector must be a list")

        if len(vector) != self.dimensions:
            raise ValueError(
                f"expected vector with {self.dimensions} dimensions, "
                f"got {len(vector)}"
            )

        if not all(isinstance(value, (int, float)) for value in vector):
            raise TypeError("vector values must be numeric")