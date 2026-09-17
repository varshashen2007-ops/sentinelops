from datetime import datetime, timezone

from embeddings.vector_store import InMemoryVectorStore
from models.incident import Incident
from rag.retriever import IncidentRetriever


class FakeIncidentIndex:
    def __init__(self, matches):
        self.matches = matches
        self.received_incident = None
        self.received_top_k = None

    def search_similar(self, incident, top_k=5):
        self.received_incident = incident
        self.received_top_k = top_k
        return self.matches


def make_incident(incident_id="current-incident"):
    return Incident(
        incident_id=incident_id,
        started_at=datetime(2026, 9, 17, 10, 0, tzinfo=timezone.utc),
    )


def test_retriever_returns_similar_incidents():
    from embeddings.vector_store import VectorMatch

    matches = [
        VectorMatch(
            record_id="incident-001",
            similarity_score=0.91,
            metadata={"document": "OOMKilled incident"},
        ),
        VectorMatch(
            record_id="incident-002",
            similarity_score=0.78,
            metadata={"document": "Memory pressure incident"},
        ),
    ]

    index = FakeIncidentIndex(matches)
    retriever = IncidentRetriever(index)

    results = retriever.retrieve(make_incident())

    assert len(results) == 2
    assert results[0].incident_id == "incident-001"
    assert results[0].similarity_score == 0.91
    assert results[1].incident_id == "incident-002"


def test_retriever_passes_top_k_to_index():
    index = FakeIncidentIndex([])
    retriever = IncidentRetriever(index)

    retriever.retrieve(make_incident(), top_k=3)

    assert index.received_top_k == 3


def test_retriever_passes_incident_to_index():
    incident = make_incident("incident-current")

    index = FakeIncidentIndex([])
    retriever = IncidentRetriever(index)

    retriever.retrieve(incident)

    assert index.received_incident is incident


def test_retriever_returns_empty_list_when_no_matches():
    index = FakeIncidentIndex([])
    retriever = IncidentRetriever(index)

    results = retriever.retrieve(make_incident())

    assert results == []


def test_retriever_copies_metadata():
    from embeddings.vector_store import VectorMatch

    metadata = {
        "incident_id": "incident-001",
        "document": "Historical OOMKilled incident",
    }

    index = FakeIncidentIndex(
        [
            VectorMatch(
                record_id="incident-001",
                similarity_score=0.88,
                metadata=metadata,
            )
        ]
    )

    retriever = IncidentRetriever(index)
    result = retriever.retrieve(make_incident())[0]

    assert result.metadata == metadata
    assert result.metadata is not metadata