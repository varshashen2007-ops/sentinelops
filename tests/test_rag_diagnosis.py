from datetime import datetime, timezone

from diagnosis.engine import DiagnosisEngine
from incident_engine.classifier import IncidentClassifier
from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence
from rag.context_builder import RAGContext
from rag.pipeline import RAGResult
from rag.retriever import RetrievedIncident


def make_incident():
    timestamp = datetime(
        2026,
        9,
        17,
        10,
        0,
        tzinfo=timezone.utc,
    )

    evidence = Evidence(
        source="kubernetes",
        evidence_type="event",
        timestamp=timestamp,
        namespace="default",
        resource="checkout-api",
        data={"reason": "OOMKilled"},
    )

    return IncidentCandidate(
        detector="kubernetes-failure",
        title="Pod OOMKilled",
        severity="high",
        timestamp=timestamp,
        namespace="default",
        resource="checkout-api",
        evidence=evidence,
        details="Container exceeded its configured memory limit.",
    )


def make_rag_result():
    incidents = [
        RetrievedIncident(
            incident_id="historical-001",
            similarity_score=0.91,
            metadata={
                "incident_id": "historical-001",
                "document": "Historical memory exhaustion incident.",
            },
        ),
        RetrievedIncident(
            incident_id="historical-002",
            similarity_score=0.82,
            metadata={
                "incident_id": "historical-002",
                "document": "Previous checkout workload failure.",
            },
        ),
    ]

    return RAGResult(
        incident_id="current-001",
        context=RAGContext(incidents=incidents),
    )


def test_diagnosis_without_rag_has_no_historical_incidents():
    incident = make_incident()
    classification = IncidentClassifier().classify(incident)

    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.historical_incident_ids == []


def test_diagnosis_records_retrieved_historical_incidents():
    incident = make_incident()
    classification = IncidentClassifier().classify(incident)

    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
        rag_result=make_rag_result(),
    )

    assert diagnosis.historical_incident_ids == [
        "historical-001",
        "historical-002",
    ]


def test_historical_incidents_are_not_added_to_evidence_references():
    incident = make_incident()
    classification = IncidentClassifier().classify(incident)

    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
        rag_result=make_rag_result(),
    )

    assert len(diagnosis.evidence_references) == 1

    reference = diagnosis.evidence_references[0]

    assert reference.source == "kubernetes"
    assert reference.resource == "checkout-api"

    assert "historical-001" not in reference.description
    assert "historical-002" not in reference.description


def test_explanation_mentions_historical_context():
    incident = make_incident()
    classification = IncidentClassifier().classify(incident)

    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
        rag_result=make_rag_result(),
    )

    assert "historical-001" in diagnosis.explanation
    assert "historical-002" in diagnosis.explanation


def test_diagnosis_root_cause_still_comes_from_current_incident():
    incident = make_incident()
    classification = IncidentClassifier().classify(incident)

    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
        rag_result=make_rag_result(),
    )

    assert diagnosis.root_cause == (
        "Container memory limit exhaustion."
    )