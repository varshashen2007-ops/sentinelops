from abc import ABC, abstractmethod
from typing import Sequence

from sentence_transformers import SentenceTransformer


class EmbeddingProvider(ABC):
    """
    Abstract interface for generating semantic embeddings.

    The rest of SentinelOps depends on this interface rather than
    directly depending on a specific embedding model or provider.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text input."""
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple text inputs."""
        raise NotImplementedError


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Local embedding provider backed by Sentence Transformers.

    Default model:
        all-MiniLM-L6-v2

    This model produces 384-dimensional embeddings.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for one text string.
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text.strip():
            raise ValueError("text must not be empty")

        vector = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vector.tolist()

    def embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate normalized embeddings for multiple text strings.
        """

        if not texts:
            return []

        if any(not isinstance(text, str) for text in texts):
            raise TypeError("all texts must be strings")

        if any(not text.strip() for text in texts):
            raise ValueError("texts must not contain empty strings")

        vectors = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vectors.tolist()