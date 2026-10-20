from pathlib import Path

from embeddings.incident_index import IncidentVectorIndex
from rag.rcaeval_adapter import RCAEvalAdapter


class RCAEvalIndexService:
    """Load and index RCAEval cases in the existing incident vector index."""

    def __init__(
        self,
        incident_index: IncidentVectorIndex,
        feature_csv: str | Path = "data/rcaeval_case_features.csv",
    ) -> None:
        self.incident_index = incident_index
        self.adapter = RCAEvalAdapter(feature_csv)

    def index_cases(self) -> int:
        incidents = self.adapter.load_incidents()
        self.incident_index.add_incidents(incidents)
        return len(incidents)
