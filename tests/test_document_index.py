from rag.embeddings.provider import DeterministicEmbeddingProvider
from storage.document_index import DocumentIndexer
from storage.document_store import Document, InMemoryDocumentStore
from storage.vector import InMemoryVectorStore


def test_index_stores_documents_and_vectors() -> None:
    document_store = InMemoryDocumentStore()
    vector_store = InMemoryVectorStore()
    embedding_provider = DeterministicEmbeddingProvider(dimensions=8)

    indexer = DocumentIndexer(
        document_store=document_store,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    documents = [
        Document(
            document_id="runbook-1",
            content="Restart the API deployment.",
            metadata={
                "document_type": "runbook",
                "service": "api",
            },
        )
    ]

    indexer.index(documents)

    stored_document = document_store.get("runbook-1")

    assert stored_document == documents[0]

    results = vector_store.search(
        embedding_provider.embed(documents[0].content),
        limit=1,
    )

    assert len(results) == 1
    assert results[0].record_id == "runbook-1"
    assert results[0].metadata["document_type"] == "runbook"
    assert results[0].metadata["service"] == "api"


def test_index_supports_multiple_documents() -> None:
    document_store = InMemoryDocumentStore()
    vector_store = InMemoryVectorStore()
    embedding_provider = DeterministicEmbeddingProvider(dimensions=8)

    indexer = DocumentIndexer(
        document_store=document_store,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    documents = [
        Document(
            document_id="incident-1",
            content="API latency increased.",
            metadata={"document_type": "incident"},
        ),
        Document(
            document_id="runbook-1",
            content="Restart the API deployment.",
            metadata={"document_type": "runbook"},
        ),
    ]

    indexer.index(documents)

    assert document_store.get("incident-1") is not None
    assert document_store.get("runbook-1") is not None

    results = vector_store.search(
        embedding_provider.embed("API latency increased."),
        limit=2,
    )

    assert len(results) == 2


def test_index_empty_documents_does_nothing() -> None:
    document_store = InMemoryDocumentStore()
    vector_store = InMemoryVectorStore()
    embedding_provider = DeterministicEmbeddingProvider(dimensions=8)

    indexer = DocumentIndexer(
        document_store=document_store,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    indexer.index([])

    assert document_store.list() == []
    assert vector_store.search([1.0] * 8) == []