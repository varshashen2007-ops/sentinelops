from dataclasses import dataclass
from typing import Any

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.vector_store import InMemoryVectorStore, VectorMatch
from models.incident import Incident


@dataclass
class IndexedIncident:
    """
    Metadata describing an incident stored in the vector index.
    """

    incident_id: str
    document: str


class IncidentVectorIndex:
    """
    Semantic index for historical incidents.

    Coordinates incident embedding generation and vector storage
    while keeping the incident domain model independent of the
    underlying vector-store implementation.
    """

    def __init__(
        self,
        embedding_service: IncidentEmbeddingService,
        vector_store: InMemoryVectorStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def add_incident(
        self,
        incident: Incident,
    ) -> IndexedIncident:
        """
        Generate an embedding for an incident and store it.
        """

        embedded = self.embedding_service.embed_incident(
            incident
        )

        metadata = {
            "incident_id": embedded.incident_id,
            "document": embedded.document,
        }

        self.vector_store.add(
            record_id=embedded.incident_id,
            vector=embedded.vector,
            metadata=metadata,
        )

        return IndexedIncident(
            incident_id=embedded.incident_id,
            document=embedded.document,
        )

    def add_incidents(
        self,
        incidents: list[Incident],
    ) -> list[IndexedIncident]:
        """
        Generate embeddings and index multiple incidents.
        """

        if not incidents:
            return []

        embedded_incidents = (
            self.embedding_service.embed_incidents(
                incidents
            )
        )

        indexed: list[IndexedIncident] = []

        for embedded in embedded_incidents:
            metadata = {
                "incident_id": embedded.incident_id,
                "document": embedded.document,
            }

            self.vector_store.add(
                record_id=embedded.incident_id,
                vector=embedded.vector,
                metadata=metadata,
            )

            indexed.append(
                IndexedIncident(
                    incident_id=embedded.incident_id,
                    document=embedded.document,
                )
            )

        return indexed

    def search_similar(
        self,
        incident: Incident,
        top_k: int = 5,
    ) -> list[VectorMatch]:
        """
        Embed a query incident and retrieve similar historical incidents.

        The query incident itself is not automatically inserted into
        the index.
        """

        embedded = self.embedding_service.embed_incident(
            incident
        )

        return self.vector_store.search(
            query_vector=embedded.vector,
            top_k=top_k,
        )

    def count(self) -> int:
        """Return the number of indexed incidents."""

        return self.vector_store.count()

    def clear(self) -> None:
        """Remove all indexed incidents."""

        self.vector_store.clear()