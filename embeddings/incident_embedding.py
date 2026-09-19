from dataclasses import dataclass

from embeddings.incident_document import IncidentDocumentBuilder
from embeddings.service import EmbeddingService
from models.incident import Incident


@dataclass
class IncidentEmbedding:
    """
    Embedding representation of a single incident.

    The original incident is not modified. The canonical document
    and generated vector are kept together for downstream retrieval.
    """

    incident_id: str
    document: str
    vector: list[float]


class IncidentEmbeddingService:
    """
    Coordinates incident document generation and embedding.

    This service keeps incident-domain objects separate from the
    embedding implementation.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        document_builder: IncidentDocumentBuilder | None = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.document_builder = (
            document_builder or IncidentDocumentBuilder()
        )

    def embed_incident(
        self,
        incident: Incident,
    ) -> IncidentEmbedding:
        """
        Build the canonical incident document and generate its vector.
        """

        document = self.document_builder.build(incident)
        vector = self.embedding_service.embed_text(document)

        return IncidentEmbedding(
            incident_id=incident.incident_id,
            document=document,
            vector=vector,
        )

    def embed_incidents(
        self,
        incidents: list[Incident],
    ) -> list[IncidentEmbedding]:
        """
        Build and embed multiple incidents.

        Embeddings are generated as a batch to avoid repeatedly
        invoking the underlying model for each incident.
        """

        if not incidents:
            return []

        documents = [
            self.document_builder.build(incident)
            for incident in incidents
        ]

        vectors = self.embedding_service.embed_texts(documents)

        return [
            IncidentEmbedding(
                incident_id=incident.incident_id,
                document=document,
                vector=vector,
            )
            for incident, document, vector in zip(
                incidents,
                documents,
                vectors,
            )
        ]