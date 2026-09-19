from dataclasses import dataclass
from models.incident import Incident
from embeddings.incident_index import IncidentVectorIndex
from embeddings.vector_store import VectorMatch


@dataclass
class RetrievedIncident:
    """
    A historical incident retrieved as relevant context.
    """

    incident_id: str
    similarity_score: float
    metadata: dict


class IncidentRetriever:
    """
    Retrieves historical incidents that are semantically similar
    to a current incident.

    Retrieval is intentionally separated from diagnosis and
    generation. This component only answers:

        "Which historical incidents are relevant to this incident?"
    """

    def __init__(self, incident_index: IncidentVectorIndex) -> None:
        self.incident_index = incident_index

    def retrieve(
        self,
        incident: Incident,
        top_k: int = 5,
    ) -> list[RetrievedIncident]:
        """
        Retrieve the most semantically similar historical incidents.
        """

        matches: list[VectorMatch] = self.incident_index.search_similar(
            incident=incident,
            top_k=top_k,
        )

        return [
            RetrievedIncident(
                incident_id=match.record_id,
                similarity_score=match.similarity_score,
                metadata=dict(match.metadata),
            )
            for match in matches
        ]