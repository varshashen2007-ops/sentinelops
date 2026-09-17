from datetime import datetime, timezone

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.incident_index import IncidentVectorIndex
from embeddings.service import EmbeddingService
from embeddings.vector_store import InMemoryVectorStore
from incident_engine.dna import IncidentDNA
from models.incident import Incident


class FakeEmbeddingProvider:
    """
    Deterministic embedding provider for unit tests.

    The first three dimensions encode simple incident concepts:
    memory, scheduling, and application.
    """

    def embed(self, text: str) -> list[float]:
        text_lower = text.lower()

        if "oomkilled" in text_lower:
            return [1.0, 0.0, 0.0]
        if "failedscheduling" in text_lower:
            return [0.0, 1.0, 0.0]
        if "application" in text_lower:
            return [0.0, 0.0, 1.0]

        return [0.5, 0.5, 0.0]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def create_index() -> IncidentVectorIndex:
    provider = FakeEmbeddingProvider()

    embedding_service = EmbeddingService(provider)

    incident_embedding_service = IncidentEmbeddingService(
        embedding_service=embedding_service,
    )

    vector_store = InMemoryVectorStore(dimensions=3)

    return IncidentVectorIndex(
        embedding_service=incident_embedding_service,
        vector_store=vector_store,
    )


def create_incident(
    incident_id: str,
    failure: str,
) -> Incident:
    return Incident(
        incident_id=incident_id,
        started_at=datetime(
            2026,
            9,
            17,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        dna=IncidentDNA(
            failure=failure,
        ),
    )


def test_add_incident_indexes_incident():
    index = create_index()

    incident = create_incident(
        "incident-001",
        "OOMKilled",
    )

    indexed = index.add_incident(incident)

    assert indexed.incident_id == "incident-001"
    assert index.count() == 1


def test_add_incidents_indexes_multiple_incidents():
    index = create_index()

    incidents = [
        create_incident(
            "incident-001",
            "OOMKilled",
        ),
        create_incident(
            "incident-002",
            "FailedScheduling",
        ),
    ]

    indexed = index.add_incidents(incidents)

    assert len(indexed) == 2
    assert index.count() == 2


def test_search_returns_similar_historical_incident():
    index = create_index()

    historical = create_incident(
        "incident-001",
        "OOMKilled",
    )

    unrelated = create_incident(
        "incident-002",
        "FailedScheduling",
    )

    current = create_incident(
        "incident-current",
        "OOMKilled",
    )

    index.add_incident(historical)
    index.add_incident(unrelated)

    matches = index.search_similar(
        current,
        top_k=2,
    )

    assert len(matches) == 2
    assert matches[0].record_id == "incident-001"
    assert matches[0].similarity_score == 1.0


def test_search_does_not_add_query_incident():
    index = create_index()

    historical = create_incident(
        "incident-001",
        "OOMKilled",
    )

    current = create_incident(
        "incident-current",
        "OOMKilled",
    )

    index.add_incident(historical)

    assert index.count() == 1

    index.search_similar(current)

    assert index.count() == 1


def test_search_preserves_incident_metadata():
    index = create_index()

    incident = create_incident(
        "incident-001",
        "OOMKilled",
    )

    index.add_incident(incident)

    matches = index.search_similar(
        create_incident(
            "incident-current",
            "OOMKilled",
        )
    )

    assert matches[0].metadata["incident_id"] == "incident-001"
    assert "document" in matches[0].metadata


def test_empty_incident_batch_returns_empty_result():
    index = create_index()

    result = index.add_incidents([])

    assert result == []
    assert index.count() == 0


def test_clear_removes_indexed_incidents():
    index = create_index()

    index.add_incident(
        create_incident(
            "incident-001",
            "OOMKilled",
        )
    )

    assert index.count() == 1

    index.clear()

    assert index.count() == 0