import pytest

from embeddings.vector_store import InMemoryVectorStore


def test_store_can_add_and_retrieve_vector():
    store = InMemoryVectorStore(dimensions=3)

    store.add(
        "incident-001",
        [1.0, 0.0, 0.0],
        {"failure": "OOMKilled"},
    )

    record = store.get("incident-001")

    assert record is not None
    assert record.record_id == "incident-001"
    assert record.vector == [1.0, 0.0, 0.0]
    assert record.metadata["failure"] == "OOMKilled"


def test_similarity_search_returns_most_similar_first():
    store = InMemoryVectorStore(dimensions=3)

    store.add(
        "incident-001",
        [1.0, 0.0, 0.0],
    )

    store.add(
        "incident-002",
        [0.9, 0.1, 0.0],
    )

    store.add(
        "incident-003",
        [0.0, 1.0, 0.0],
    )

    matches = store.search(
        [1.0, 0.0, 0.0],
        top_k=3,
    )

    assert matches[0].record_id == "incident-001"
    assert (
        matches[0].similarity_score
        >= matches[1].similarity_score
        >= matches[2].similarity_score
    )


def test_top_k_limits_results():
    store = InMemoryVectorStore(dimensions=3)

    for index in range(5):
        store.add(
            f"incident-{index}",
            [1.0, 0.0, 0.0],
        )

    matches = store.search(
        [1.0, 0.0, 0.0],
        top_k=2,
    )

    assert len(matches) == 2


def test_empty_store_returns_no_matches():
    store = InMemoryVectorStore(dimensions=3)

    matches = store.search(
        [1.0, 0.0, 0.0],
    )

    assert matches == []


def test_invalid_vector_dimensions_are_rejected():
    store = InMemoryVectorStore(dimensions=3)

    with pytest.raises(ValueError):
        store.add(
            "incident-001",
            [1.0, 0.0],
        )


def test_invalid_query_dimensions_are_rejected():
    store = InMemoryVectorStore(dimensions=3)

    with pytest.raises(ValueError):
        store.search(
            [1.0, 0.0],
        )


def test_invalid_top_k_is_rejected():
    store = InMemoryVectorStore(dimensions=3)

    with pytest.raises(ValueError):
        store.search(
            [1.0, 0.0, 0.0],
            top_k=0,
        )


def test_add_many_stores_multiple_records():
    store = InMemoryVectorStore(dimensions=3)

    from embeddings.vector_store import VectorRecord

    records = [
        VectorRecord(
            record_id="incident-001",
            vector=[1.0, 0.0, 0.0],
            metadata={"failure": "OOMKilled"},
        ),
        VectorRecord(
            record_id="incident-002",
            vector=[0.0, 1.0, 0.0],
            metadata={"failure": "FailedScheduling"},
        ),
    ]

    store.add_many(records)

    assert store.count() == 2
    assert store.get("incident-001") is not None
    assert store.get("incident-002") is not None


def test_clear_removes_all_records():
    store = InMemoryVectorStore(dimensions=3)

    store.add(
        "incident-001",
        [1.0, 0.0, 0.0],
    )

    assert store.count() == 1

    store.clear()

    assert store.count() == 0
    assert store.get("incident-001") is None