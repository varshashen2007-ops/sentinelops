from storage.document_store import (
    Document,
    InMemoryDocumentStore,
)


def test_upsert_and_get_document() -> None:
    store = InMemoryDocumentStore()

    document = Document(
        document_id="doc-1",
        content="Pod restart runbook",
        metadata={
            "document_type": "runbook",
            "service": "api",
        },
    )

    store.upsert([document])

    assert store.get("doc-1") == document


def test_upsert_replaces_existing_document() -> None:
    store = InMemoryDocumentStore()

    first = Document(
        document_id="doc-1",
        content="old content",
    )
    second = Document(
        document_id="doc-1",
        content="new content",
    )

    store.upsert([first])
    store.upsert([second])

    assert store.get("doc-1") == second


def test_list_documents() -> None:
    store = InMemoryDocumentStore()

    documents = [
        Document(document_id="doc-1", content="one"),
        Document(document_id="doc-2", content="two"),
    ]

    store.upsert(documents)

    assert store.list() == documents


def test_missing_document_returns_none() -> None:
    store = InMemoryDocumentStore()

    assert store.get("missing") is None


def test_delete_documents() -> None:
    store = InMemoryDocumentStore()

    store.upsert(
        [
            Document(document_id="doc-1", content="one"),
            Document(document_id="doc-2", content="two"),
        ]
    )

    store.delete(["doc-1"])

    assert store.get("doc-1") is None
    assert store.get("doc-2") is not None


def test_document_metadata_is_preserved() -> None:
    store = InMemoryDocumentStore()

    document = Document(
        document_id="incident-123",
        content="Database connection failures",
        metadata={
            "document_type": "incident",
            "incident_id": "123",
            "namespace": "production",
        },
    )

    store.upsert([document])

    result = store.get("incident-123")

    assert result is not None
    assert result.metadata["document_type"] == "incident"
    assert result.metadata["incident_id"] == "123"
    assert result.metadata["namespace"] == "production"