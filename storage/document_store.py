from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """A document stored for embedding and later retrieval."""

    document_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentStore(ABC):
    """Backend-independent document storage interface."""

    @abstractmethod
    def upsert(self, documents: list[Document]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, document_id: str) -> Document | None:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Document]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, document_ids: list[str]) -> None:
        raise NotImplementedError


class InMemoryDocumentStore(DocumentStore):
    """Deterministic document store for tests and local development."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    def upsert(self, documents: list[Document]) -> None:
        for document in documents:
            self._documents[document.document_id] = document

    def get(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def list(self) -> list[Document]:
        return list(self._documents.values())

    def delete(self, document_ids: list[str]) -> None:
        for document_id in document_ids:
            self._documents.pop(document_id, None)