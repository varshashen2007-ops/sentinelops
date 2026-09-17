from datetime import datetime, timezone

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.service import EmbeddingService
from incident_engine.dna import IncidentDNA
from models.incident import Incident


class FakeEmbeddingProvider:
    """
    Deterministic provider for testing the incident embedding
    orchestration without loading a real ML model.
    """

    def embed(self, text: str) -> list[float]:
        return [float(len(text)), 1.0, 2.0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [
            [float(len(text)), 1.0, 2.0]
            for text in texts
        ]


def create_incident(
    incident_id: str = "incident-001",
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
            trigger="memory_growth",
            failure="OOMKilled",
            severity="high",
        ),
    )


def create_service() -> IncidentEmbeddingService:
    provider = FakeEmbeddingProvider()
    embedding_service = EmbeddingService(provider)

    return IncidentEmbeddingService(
        embedding_service=embedding_service,
    )


def test_embed_incident_returns_incident_embedding():
    incident = create_incident()
    service = create_service()

    result = service.embed_incident(incident)

    assert result.incident_id == "incident-001"
    assert result.document.startswith(
        "Incident ID: incident-001"
    )
    assert "Failure: OOMKilled" in result.document
    assert isinstance(result.vector, list)
    assert len(result.vector) == 3


def test_embed_incident_does_not_modify_original_incident():
    incident = create_incident()
    original_dna = incident.dna.to_dict()

    service = create_service()

    service.embed_incident(incident)

    assert incident.dna.to_dict() == original_dna


def test_embed_incidents_returns_one_result_per_incident():
    incidents = [
        create_incident("incident-001"),
        create_incident("incident-002"),
        create_incident("incident-003"),
    ]

    service = create_service()

    results = service.embed_incidents(incidents)

    assert len(results) == 3
    assert [
        result.incident_id
        for result in results
    ] == [
        "incident-001",
        "incident-002",
        "incident-003",
    ]


def test_embed_incidents_preserves_document_and_vector_alignment():
    incidents = [
        create_incident("incident-001"),
        create_incident("incident-002"),
    ]

    service = create_service()

    results = service.embed_incidents(incidents)

    for incident, result in zip(incidents, results):
        assert result.incident_id == incident.incident_id
        assert result.document.startswith(
            f"Incident ID: {incident.incident_id}"
        )
        assert result.vector[0] == float(
            len(result.document)
        )


def test_empty_incident_list_returns_empty_result():
    service = create_service()

    results = service.embed_incidents([])

    assert results == []