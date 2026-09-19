from datetime import datetime, timezone

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.provider import SentenceTransformerProvider
from embeddings.service import EmbeddingService
from embeddings.vector_store import InMemoryVectorStore
from embeddings.incident_index import IncidentVectorIndex
from models.incident import Incident
from incident_engine.dna import IncidentDNA
from rag.context_builder import RAGContextBuilder
from rag.pipeline import RAGPipeline
from rag.retriever import IncidentRetriever


def make_incident(
    incident_id: str,
    failure: str,
    affected_workload: str,
) -> Incident:
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
        dna=IncidentDNA(
            trigger="resource exhaustion",
            failure=failure,
            affected_workload=affected_workload,
            severity="high",
        ),
    )


def test_real_rag_pipeline_retrieves_semantically_similar_incident():
    provider = SentenceTransformerProvider()
    embedding_service = EmbeddingService(provider)

    incident_embedding_service = IncidentEmbeddingService(
        embedding_service
    )

    vector_store = InMemoryVectorStore(dimensions=384)

    index = IncidentVectorIndex(
        embedding_service=incident_embedding_service,
        vector_store=vector_store,
    )

    historical_memory_incident = make_incident(
        "historical-memory-001",
        "container exceeded its configured memory limit",
        "checkout-api",
    )

    historical_scheduling_incident = make_incident(
        "historical-scheduling-001",
        "scheduler rejected the pod because insufficient CPU capacity was available",
        "payment-worker",
    )

    current_incident = make_incident(
        "current-memory-001",
        "workload experienced an out-of-memory kill after memory usage crossed the container limit",
        "checkout-api",
    )

    index.add_incidents(
        [
            historical_memory_incident,
            historical_scheduling_incident,
        ]
    )

    retriever = IncidentRetriever(index)
    context_builder = RAGContextBuilder()

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
    )

    result = pipeline.run(
        current_incident,
        top_k=2,
    )

    assert result.incident_id == "current-memory-001"
    assert len(result.retrieved_incidents) == 2

    assert (
        result.retrieved_incidents[0].incident_id
        == "historical-memory-001"
    )

    assert (
        result.retrieved_incidents[0].similarity_score
        > result.retrieved_incidents[1].similarity_score
    )

    context_text = result.context.to_text()

    assert "historical-memory-001" in context_text
    assert "container exceeded its configured memory limit" in context_text