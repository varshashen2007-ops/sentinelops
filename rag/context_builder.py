from dataclasses import dataclass, field
from typing import Any

from rag.retriever import RetrievedIncident


@dataclass
class HistoricalExperience:
    """
    Structured recovery experience extracted from a retrieved
    historical incident.

    This contains only information explicitly present in the
    retrieved incident metadata.
    """

    incident_id: str
    similarity_score: float
    resolution_action: str | None = None
    resolution_description: str | None = None
    outcome_status: str | None = None
    outcome_description: str | None = None
    outcome_verified: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "similarity_score": self.similarity_score,
            "resolution_action": self.resolution_action,
            "resolution_description": self.resolution_description,
            "outcome_status": self.outcome_status,
            "outcome_description": self.outcome_description,
            "outcome_verified": self.outcome_verified,
        }


@dataclass
class RAGContext:
    """
    Structured context assembled from retrieved historical incidents.

    This object contains only information that was actually retrieved.
    It does not generate or infer new information.
    """

    incidents: list[RetrievedIncident] = field(default_factory=list)

    @property
    def experiences(self) -> list[HistoricalExperience]:
        """
        Extract explicit remediation and outcome information from
        retrieved incident documents.
        """

        experiences: list[HistoricalExperience] = []

        for incident in self.incidents:
            document = incident.metadata.get("document", "")

            experiences.append(
                HistoricalExperience(
                    incident_id=incident.incident_id,
                    similarity_score=incident.similarity_score,
                    resolution_action=self._extract_field(
                        document,
                        "Resolution Action",
                    ),
                    resolution_description=self._extract_field(
                        document,
                        "Resolution Description",
                    ),
                    outcome_status=self._extract_field(
                        document,
                        "Outcome Status",
                    ),
                    outcome_description=self._extract_field(
                        document,
                        "Outcome Description",
                    ),
                    outcome_verified=self._extract_bool_field(
                        document,
                        "Outcome Verified",
                    ),
                )
            )

        return experiences

    def to_text(self) -> str:
        """
        Convert retrieved incidents into deterministic text context.
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
                section.append(
                    f"Incident Description: {document}"
                )

            experience = self._experience_for(
                incident
            )

            if experience is not None:
                if experience.resolution_action:
                    section.append(
                        f"Historical Resolution: "
                        f"{experience.resolution_action}"
                    )

                if experience.outcome_status:
                    section.append(
                        f"Historical Outcome: "
                        f"{experience.outcome_status}"
                    )

                if experience.outcome_verified is not None:
                    section.append(
                        f"Historical Outcome Verified: "
                        f"{experience.outcome_verified}"
                    )

            sections.append("\n".join(section))

        return "\n\n".join(sections)

    @staticmethod
    def _experience_for(
        incident: RetrievedIncident,
    ) -> HistoricalExperience | None:
        document = incident.metadata.get("document")

        if not document:
            return None

        return HistoricalExperience(
            incident_id=incident.incident_id,
            similarity_score=incident.similarity_score,
            resolution_action=RAGContext._extract_field(
                document,
                "Resolution Action",
            ),
            resolution_description=RAGContext._extract_field(
                document,
                "Resolution Description",
            ),
            outcome_status=RAGContext._extract_field(
                document,
                "Outcome Status",
            ),
            outcome_description=RAGContext._extract_field(
                document,
                "Outcome Description",
            ),
            outcome_verified=RAGContext._extract_bool_field(
                document,
                "Outcome Verified",
            ),
        )

    @staticmethod
    def _extract_field(
        document: str,
        label: str,
    ) -> str | None:
        prefix = f"{label}:"

        for line in document.splitlines():
            if line.startswith(prefix):
                value = line[len(prefix):].strip()

                if value:
                    return value

        return None

    @staticmethod
    def _extract_bool_field(
        document: str,
        label: str,
    ) -> bool | None:
        value = RAGContext._extract_field(
            document,
            label,
        )

        if value is None:
            return None

        if value.lower() == "true":
            return True

        if value.lower() == "false":
            return False

        return None


class RAGContextBuilder:
    """
    Builds structured RAG context from retrieved incidents.

    The builder is intentionally deterministic and does not perform
    retrieval, diagnosis, or language-model generation.
    """

    def build(
        self,
        incidents: list[RetrievedIncident],
    ) -> RAGContext:
        """
        Build a RAG context object from retrieved incidents.
        """

        return RAGContext(
            incidents=list(incidents)
        )