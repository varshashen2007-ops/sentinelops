from dataclasses import dataclass, field
from typing import Any

from incident_engine.dna import IncidentDNA


@dataclass
class SimilarIncident:
    """
    Represents a historical incident that is similar to the
    current incident.
    """

    incident_id: str
    similarity_score: float
    dna: IncidentDNA

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "similarity_score": self.similarity_score,
            "dna": self.dna.to_dict(),
        }


@dataclass
class NoveltyResult:
    """
    Result of deterministic incident novelty detection.
    """

    novelty_score: float
    similar_incidents: list[SimilarIncident] = field(
        default_factory=list
    )
    known_pattern: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "novelty_score": self.novelty_score,
            "similar_incidents": [
                incident.to_dict()
                for incident in self.similar_incidents
            ],
            "known_pattern": self.known_pattern,
        }


class IncidentNoveltyDetector:
    """
    Deterministic novelty detector for Incident DNA.

    The detector compares the current IncidentDNA against historical
    IncidentDNA records using weighted field similarity.

    No machine learning, embeddings, vector database, or LLM is used.
    """

    FIELD_WEIGHTS = {
        "trigger": 0.15,
        "failure": 0.20,
        "restart_pattern": 0.10,
        "readiness": 0.10,
        "affected_workload": 0.10,
        "duration": 0.05,
        "severity": 0.10,
        "dependency_information": 0.10,
        "anomaly_information": 0.10,
    }

    KNOWN_PATTERN_THRESHOLD = 0.70

    def detect(
        self,
        current: IncidentDNA,
        historical: list[tuple[str, IncidentDNA]],
        top_k: int = 5,
    ) -> NoveltyResult:
        """
        Compare the current incident against historical incidents.

        Args:
            current: Current incident DNA.
            historical: List of (incident_id, IncidentDNA) pairs.
            top_k: Maximum number of similar incidents to return.
        """

        if not historical:
            return NoveltyResult(
                novelty_score=1.0,
                similar_incidents=[],
                known_pattern=False,
            )

        similarities: list[SimilarIncident] = []

        for incident_id, historical_dna in historical:
            similarity = self._calculate_similarity(
                current,
                historical_dna,
            )

            similarities.append(
                SimilarIncident(
                    incident_id=incident_id,
                    similarity_score=similarity,
                    dna=historical_dna,
                )
            )

        similarities.sort(
            key=lambda item: item.similarity_score,
            reverse=True,
        )

        similar_incidents = similarities[:top_k]

        best_similarity = similar_incidents[0].similarity_score

        novelty_score = round(1.0 - best_similarity, 4)

        known_pattern = (
            best_similarity >= self.KNOWN_PATTERN_THRESHOLD
        )

        return NoveltyResult(
            novelty_score=novelty_score,
            similar_incidents=similar_incidents,
            known_pattern=known_pattern,
        )

    def _calculate_similarity(
        self,
        current: IncidentDNA,
        historical: IncidentDNA,
    ) -> float:
        """
        Calculate deterministic weighted similarity between
        two IncidentDNA objects.

        Fields where both values are missing are ignored rather
        than treated as matches.
        """

        current_data = current.to_dict()
        historical_data = historical.to_dict()

        weighted_score = 0.0
        total_weight = 0.0

        for field_name, weight in self.FIELD_WEIGHTS.items():
            current_value = current_data.get(field_name)
            historical_value = historical_data.get(field_name)

            # Both values are missing. This field provides no
            # information, so exclude its weight from the score.
            if current_value is None and historical_value is None:
                continue

            total_weight += weight

            field_similarity = self._field_similarity(
                current_value,
                historical_value,
            )

            weighted_score += weight * field_similarity

        if total_weight == 0:
            return 0.0

        return round(weighted_score / total_weight, 4)

    @staticmethod
    def _field_similarity(
        current_value: Any,
        historical_value: Any,
    ) -> float:
        """
        Deterministically compare two DNA field values.

        Returns:
            1.0 for an exact match
            0.0 for a mismatch
            0.0 when only one value is missing
        """

        if current_value is None or historical_value is None:
            return 0.0

        if current_value == historical_value:
            return 1.0

        return 0.0