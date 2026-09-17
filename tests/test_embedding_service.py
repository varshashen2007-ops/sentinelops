from typing import Sequence

from embeddings.provider import EmbeddingProvider
from embeddings.service import EmbeddingService


class FakeEmbeddingProvider(EmbeddingProvider):
    """Small deterministic provider used for unit testing."""

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("text must not be empty")

        return [float(len(text)), 1.0, 2.0]

    def embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def test_embed_text_delegates_to_provider():
    provider = FakeEmbeddingProvider()
    service = EmbeddingService(provider)

    vector = service.embed_text("OOMKilled incident")

    assert vector == [18.0, 1.0, 2.0]


def test_embed_texts_delegates_to_provider():
    provider = FakeEmbeddingProvider()
    service = EmbeddingService(provider)

    vectors = service.embed_texts(
        [
            "OOMKilled incident",
            "FailedScheduling incident",
        ]
    )

    assert len(vectors) == 2
    assert vectors[0] == [18.0, 1.0, 2.0]
    assert vectors[1] == [25.0, 1.0, 2.0]


def test_service_uses_injected_provider():
    provider = FakeEmbeddingProvider()
    service = EmbeddingService(provider)

    assert service.provider is provider


def test_empty_text_error_from_provider_is_preserved():
    provider = FakeEmbeddingProvider()
    service = EmbeddingService(provider)

    try:
        service.embed_text("   ")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "text must not be empty"