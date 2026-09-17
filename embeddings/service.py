from typing import Sequence

from embeddings.provider import EmbeddingProvider


class EmbeddingService:
    """
    Application-level service for generating incident embeddings.

    This service coordinates embedding generation without exposing
    the concrete embedding provider to higher-level application code.
    """

    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text input.
        """

        return self.provider.embed(text)

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple text inputs.
        """

        return self.provider.embed_batch(texts)