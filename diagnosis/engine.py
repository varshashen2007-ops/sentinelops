from incident_engine.classifier import IncidentClassification
from incident_engine.detector import IncidentCandidate
from diagnosis.model import Diagnosis, EvidenceReference
from rag.pipeline import RAGResult


class DiagnosisEngine:
    """
    Produces an evidence-grounded diagnosis from an incident.

    The engine uses current incident evidence as the basis for the
    diagnosis and may use retrieved historical incidents as context.

    Historical incidents are kept separate from current evidence so
    that retrieved context is never misrepresented as direct evidence
    from the current incident.
    """

    def diagnose(
        self,
        incident: IncidentCandidate,
        classification: IncidentClassification,
        rag_result: RAGResult | None = None,
    ) -> Diagnosis:
        evidence_references = self._build_evidence_references(incident)

        root_cause = self._determine_root_cause(
            incident=incident,
            classification=classification,
        )

        summary = self._build_summary(
            incident=incident,
            classification=classification,
            root_cause=root_cause,
        )

        historical_incident_ids = self._get_historical_incident_ids(
            rag_result
        )

        explanation = self._build_explanation(
            classification=classification,
            historical_incident_ids=historical_incident_ids,
        )

        return Diagnosis(
            summary=summary,
            root_cause=root_cause,
            confidence=classification.confidence,
            evidence_references=evidence_references,
            historical_incident_ids=historical_incident_ids,
            explanation=explanation,
        )

    @staticmethod
    def _build_evidence_references(
        incident: IncidentCandidate,
    ) -> list[EvidenceReference]:
        if incident.evidence is None:
            return []

        evidence = incident.evidence

        return [
            EvidenceReference(
                source=evidence.source,
                evidence_type=evidence.evidence_type,
                description=incident.details or incident.title,
                timestamp=evidence.timestamp.isoformat(),
                resource=evidence.resource,
            )
        ]

    @staticmethod
    def _get_historical_incident_ids(
        rag_result: RAGResult | None,
    ) -> list[str]:
        if rag_result is None:
            return []

        return [
            incident.incident_id
            for incident in rag_result.retrieved_incidents
        ]

    @staticmethod
    def _build_explanation(
        classification: IncidentClassification,
        historical_incident_ids: list[str],
    ) -> str:
        explanation = classification.explanation

        if historical_incident_ids:
            explanation += (
                " Historical incident context was retrieved from: "
                + ", ".join(historical_incident_ids)
                + "."
            )

        return explanation

    @staticmethod
    def _determine_root_cause(
        incident: IncidentCandidate,
        classification: IncidentClassification,
    ) -> str:
        title = incident.title.lower()

        if "oomkilled" in title:
            return "Container memory limit exhaustion."

        if "failedscheduling" in title or "scheduling" in title:
            return "Kubernetes scheduling constraints prevented pod placement."

        if "crashloopbackoff" in title:
            return (
                "Application container repeatedly failed during "
                "startup or execution."
            )

        if "pending" in title:
            return "Pod could not transition to a running state."

        if "readiness" in title:
            return (
                "Workload readiness conditions prevented traffic "
                "from reaching the pod."
            )

        if classification.category == "Resource":
            return "Resource pressure or resource exhaustion affected the workload."

        if classification.category == "Networking":
            return "A networking or connectivity failure affected the workload."

        if classification.category == "Dependency":
            return "A dependency failure affected the workload."

        if classification.category == "Configuration":
            return "A configuration issue affected the workload."

        if classification.category == "Infrastructure":
            return "An infrastructure-level failure affected the workload."

        if classification.category == "Application":
            return "An application-level failure affected the workload."

        return (
            "The root cause could not be determined from "
            "the available evidence."
        )

    @staticmethod
    def _build_summary(
        incident: IncidentCandidate,
        classification: IncidentClassification,
        root_cause: str,
    ) -> str:
        return (
            f"{classification.category} incident detected: "
            f"{incident.title}. "
            f"Likely root cause: {root_cause}"
        )