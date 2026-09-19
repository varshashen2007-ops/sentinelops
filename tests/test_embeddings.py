import pytest

from rag.embeddings.provider import (
    ConfigurableEmbeddingProvider,
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
)


def test_embedding_provider_is_abstract():
    with pytest.raises(TypeError):
        EmbeddingProvider()


def test_deterministic_embedding_is_repeatable():
    provider = DeterministicEmbeddingProvider(dimensions=8)

    first = provider.embed("memory spike")
    second = provider.embed("memory spike")

    assert first == second
    assert len(first) == 8


def test_different_text_produces_embedding():
    provider = DeterministicEmbeddingProvider(dimensions=8)

    first = provider.embed("memory spike")
    second = provider.embed("cpu saturation")

    assert first != second


def test_batch_embedding():
    provider = DeterministicEmbeddingProvider(dimensions=8)

    results = provider.embed_batch(
        ["incident one", "incident two"]
    )

    assert len(results) == 2
    assert all(len(result) == 8 for result in results)


def test_configurable_provider():
    def fake_embed(text):
        return [1.0, 2.0, 3.0]

    provider = ConfigurableEmbeddingProvider(fake_embed)

    assert provider.embed("hello") == [1.0, 2.0, 3.0]


def test_configurable_provider_batch():
    def fake_embed(texts):
        return [[1.0, 0.0], [0.0, 1.0]]

    provider = ConfigurableEmbeddingProvider(fake_embed)

    assert provider.embed_batch(["a", "b"]) == [
        [1.0, 0.0],
        [0.0, 1.0],
    ]