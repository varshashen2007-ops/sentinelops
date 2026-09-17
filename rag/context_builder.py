from dataclasses import dataclass, field

from rag.retriever import RetrievedIncident


@dataclass
class RAGContext:
    """
    Structured context assembled from retrieved historical incidents.

    This object contains only information that was actually retrieved.
    It does not generate or infer new information.
    """

    incidents: list[RetrievedIncident] = field(default_factory=list)

    def to_text(self) -> str:
        """
        Convert retrieved incidents into a deterministic text context.
        """

        if not self.incidents:
            return "No relevant historical incidents were retrieved."

        sections = []

        for index, incident in enumerate(self.incidents, start=1):
            document = incident.metadata.get("document")

            section = [
                f"Historical Incident {index}",
                f"Incident ID: {incident.incident_id}",
                f"Similarity Score: {incident.similarity_score:.4f}",
            ]

            if document:
                section.append(f"Incident Description: {document}")

            sections.append("\n".join(section))

        return "\n\n".join(sections)


class RAGContextBuilder:
    """
    Builds structured RAG context from retrieved incidents.

    The builder is intentionally deterministic and does not perform
    retrieval, diagnosis, or language-model generation.
    """

    def build(self, incidents: list[RetrievedIncident]) -> RAGContext:
        """
        Build a RAG context object from retrieved incidents.
        """

        return RAGContext(incidents=list(incidents))