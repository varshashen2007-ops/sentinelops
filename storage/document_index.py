from __future__ import annotations

from storage.document_store import Document, DocumentStore
from storage.vector import VectorRecord, VectorStore
from rag.embeddings.provider import EmbeddingProvider


class DocumentIndexer:
    """Indexes documents into document and vector storage."""

    def __init__(
        self,
        document_store: DocumentStore,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.document_store = document_store
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def index(self, documents: list[Document]) -> None:
        if not documents:
            return

        embeddings = self.embedding_provider.embed_batch(
            [document.content for document in documents]
        )

        if len(embeddings) != len(documents):
            raise ValueError(
                "Embedding provider returned a different number of embeddings"
            )

        records = [
            VectorRecord(
                record_id=document.document_id,
                vector=embedding,
                metadata=dict(document.metadata),
            )
            for document, embedding in zip(documents, embeddings)
        ]

        self.document_store.upsert(documents)
        self.vector_store.upsert(records)