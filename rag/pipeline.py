from dataclasses import dataclass

from models.incident import Incident
from rag.context_builder import RAGContext, RAGContextBuilder
from rag.retriever import IncidentRetriever


@dataclass
class RAGResult:
    """
    Result produced by the retrieval-augmented context pipeline.

    The result contains the retrieved incidents and the deterministic
    context constructed from them.
    """

    incident_id: str
    context: RAGContext

    @property
    def retrieved_incidents(self):
        return self.context.incidents

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "retrieved_incidents": [
                {
                    "incident_id": incident.incident_id,
                    "similarity_score": incident.similarity_score,
                    "metadata": incident.metadata,
                }
                for incident in self.retrieved_incidents
            ],
            "context": self.context.to_text(),
        }


class RAGPipeline:
    """
    Coordinates retrieval and context construction.

    This pipeline intentionally does not perform diagnosis or
    language-model generation.

    Flow:

        Incident
            ↓
        Retriever
            ↓
        Retrieved historical incidents
            ↓
        Context Builder
            ↓
        RAGResult
    """

    def __init__(
        self,
        retriever: IncidentRetriever,
        context_builder: RAGContextBuilder | None = None,
    ) -> None:
        self.retriever = retriever
        self.context_builder = context_builder or RAGContextBuilder()

    def run(
        self,
        incident: Incident,
        top_k: int = 5,
    ) -> RAGResult:
        """
        Retrieve relevant historical incidents and build RAG context.
        """

        retrieved_incidents = self.retriever.retrieve(
            incident=incident,
            top_k=top_k,
        )

        context = self.context_builder.build(retrieved_incidents)

        return RAGResult(
            incident_id=incident.incident_id,
            context=context,
        )