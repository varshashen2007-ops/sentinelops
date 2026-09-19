from storage.vector.store import InMemoryVectorStore, VectorRecord


def test_upsert_and_search():
    store = InMemoryVectorStore()

    store.upsert(
        [
            VectorRecord(
                record_id="incident-1",
                vector=[1.0, 0.0],
                metadata={"severity": "high"},
            ),
            VectorRecord(
                record_id="incident-2",
                vector=[0.0, 1.0],
                metadata={"severity": "low"},
            ),
        ]
    )

    results = store.search([1.0, 0.0], limit=1)

    assert len(results) == 1
    assert results[0].record_id == "incident-1"


def test_metadata_filter():
    store = InMemoryVectorStore()

    store.upsert(
        [
            VectorRecord(
                record_id="incident-1",
                vector=[1.0, 0.0],
                metadata={"severity": "high"},
            ),
            VectorRecord(
                record_id="incident-2",
                vector=[1.0, 0.0],
                metadata={"severity": "low"},
            ),
        ]
    )

    results = store.search(
        [1.0, 0.0],
        metadata_filter={"severity": "high"},
    )

    assert len(results) == 1
    assert results[0].record_id == "incident-1"


def test_delete():
    store = InMemoryVectorStore()

    store.upsert(
        [
            VectorRecord(
                record_id="incident-1",
                vector=[1.0, 0.0],
            )
        ]
    )

    store.delete(["incident-1"])

    assert store.search([1.0, 0.0]) == []


def test_dimension_mismatch_is_rejected():
    store = InMemoryVectorStore()

    store.upsert(
        [
            VectorRecord(
                record_id="incident-1",
                vector=[1.0, 0.0],
            )
        ]
    )

    try:
        store.search([1.0, 0.0, 0.0])
        assert False, "Expected ValueError"
    except ValueError:
        pass