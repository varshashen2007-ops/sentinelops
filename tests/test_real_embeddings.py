import numpy as np

from embeddings.provider import SentenceTransformerProvider


def test_real_embedding_model_captures_incident_similarity():
    provider = SentenceTransformerProvider()

    texts = [
        (
            "The container was terminated after exceeding "
            "its configured memory limit."
        ),
        (
            "The workload experienced an out-of-memory kill "
            "because its memory usage crossed the container limit."
        ),
        (
            "The Kubernetes scheduler rejected the pod because "
            "the node did not have enough requested CPU capacity."
        ),
    ]

    vectors = provider.embed_batch(texts)

    similarity_matrix = np.dot(
        np.asarray(vectors),
        np.asarray(vectors).T,
    )

    memory_similarity = float(
        similarity_matrix[0, 1]
    )

    scheduling_similarity = float(
        similarity_matrix[0, 2]
    )

    assert len(vectors) == 3
    assert all(len(vector) == 384 for vector in vectors)

    assert memory_similarity > scheduling_similarity