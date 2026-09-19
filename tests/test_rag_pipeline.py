from datetime import datetime, timezone

from models.incident import Incident
from rag.pipeline import RAGPipeline
from rag.retriever import RetrievedIncident


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.received_incident = None
        self.received_top_k = None

    def retrieve(self, incident, top_k=5):
        self.received_incident = incident
        self.received_top_k = top_k
        return self.results


class FakeContextBuilder:
    def __init__(self):
        self.received_incidents = None

    def build(self, incidents):
        self.received_incidents = incidents

        from rag.context_builder import RAGContext

        return RAGContext(incidents=list(incidents))


def make_incident(incident_id="current-001"):
    return Incident(
        incident_id=incident_id,
        started_at=datetime(
            2026,
            9,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )


def make_retrieved_incident(
    incident_id="historical-001",
    similarity_score=0.91,
):
    return RetrievedIncident(
        incident_id=incident_id,
        similarity_score=similarity_score,
        metadata={
            "incident_id": incident_id,
            "document": "Historical OOMKilled incident",
        },
    )


def test_pipeline_retrieves_and_builds_context():
    historical = [
        make_retrieved_incident("historical-001", 0.91),
        make_retrieved_incident("historical-002", 0.82),
    ]

    retriever = FakeRetriever(historical)
    context_builder = FakeContextBuilder()

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
    )

    incident = make_incident()

    result = pipeline.run(incident)

    assert result.incident_id == "current-001"
    assert result.retrieved_incidents == historical
    assert context_builder.received_incidents == historical


def test_pipeline_passes_top_k_to_retriever():
    retriever = FakeRetriever([])
    context_builder = FakeContextBuilder()

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
    )

    pipeline.run(
        make_incident(),
        top_k=3,
    )

    assert retriever.received_top_k == 3


def test_pipeline_passes_incident_to_retriever():
    retriever = FakeRetriever([])
    context_builder = FakeContextBuilder()

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
    )

    incident = make_incident("incident-123")

    pipeline.run(incident)

    assert retriever.received_incident is incident


def test_pipeline_handles_no_retrieved_incidents():
    retriever = FakeRetriever([])
    context_builder = FakeContextBuilder()

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
    )

    result = pipeline.run(make_incident())

    assert result.retrieved_incidents == []
    assert result.context.to_text() == (
        "No relevant historical incidents were retrieved."
    )


def test_pipeline_result_is_serializable():
    historical = [
        make_retrieved_incident("historical-001", 0.91),
    ]

    retriever = FakeRetriever(historical)
    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=FakeContextBuilder(),
    )

    result = pipeline.run(make_incident())

    data = result.to_dict()

    assert data["incident_id"] == "current-001"
    assert len(data["retrieved_incidents"]) == 1
    assert data["retrieved_incidents"][0]["incident_id"] == "historical-001"
    assert data["retrieved_incidents"][0]["similarity_score"] == 0.91
    assert "Historical OOMKilled incident" in data["context"]