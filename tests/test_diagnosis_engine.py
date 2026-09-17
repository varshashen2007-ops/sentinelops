from datetime import datetime, timezone

from diagnosis.engine import DiagnosisEngine
from incident_engine.classifier import IncidentClassifier
from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence


def make_incident(
    title: str,
    detector: str = "test-detector",
    details: str = "Test incident evidence",
    evidence_type: str = "event",
):
    evidence = Evidence(
        source="kubernetes",
        evidence_type=evidence_type,
        timestamp=datetime(
            2026,
            9,
            17,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        namespace="default",
        resource="test-pod",
        data={"reason": title},
    )

    return IncidentCandidate(
        detector=detector,
        title=title,
        severity="high",
        timestamp=evidence.timestamp,
        namespace="default",
        resource="test-pod",
        evidence=evidence,
        details=details,
    )


def test_diagnoses_oomkilled_incident():
    incident = make_incident(
        "Pod OOMKilled",
        details="Container exceeded its memory limit.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.root_cause == (
        "Container memory limit exhaustion."
    )
    assert diagnosis.confidence == classification.confidence
    assert len(diagnosis.evidence_references) == 1

    reference = diagnosis.evidence_references[0]

    assert reference.source == "kubernetes"
    assert reference.evidence_type == "event"
    assert reference.resource == "test-pod"


def test_diagnoses_scheduling_failure():
    incident = make_incident(
        "FailedScheduling",
        details="Insufficient CPU on available nodes.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.root_cause == (
        "Kubernetes scheduling constraints prevented pod placement."
    )
    assert diagnosis.evidence_references[0].description == (
        "Insufficient CPU on available nodes."
    )


def test_diagnoses_crashloopbackoff():
    incident = make_incident(
        "CrashLoopBackOff",
        details="Container repeatedly exited.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.root_cause == (
        "Application container repeatedly failed during startup or execution."
    )


def test_diagnoses_networking_incident():
    incident = make_incident(
        "Network connection timeout",
        details="Service connection timed out.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.root_cause == (
        "A networking or connectivity failure affected the workload."
    )


def test_unknown_incident_reports_insufficient_cause():
    incident = make_incident(
        "Unrecognized incident",
        details="No known failure pattern.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.root_cause == (
        "The root cause could not be determined from the available evidence."
    )
    assert diagnosis.confidence == classification.confidence


def test_diagnosis_contains_classification_explanation():
    incident = make_incident(
        "Pod OOMKilled",
        details="Memory limit exceeded.",
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.explanation == classification.explanation


def test_incident_without_evidence_produces_no_evidence_references():
    incident = IncidentCandidate(
        detector="test-detector",
        title="Unknown incident",
        severity="medium",
        timestamp=datetime.now(timezone.utc),
        namespace="default",
        resource="test-pod",
        evidence=None,
        details=None,
    )

    classification = IncidentClassifier().classify(incident)
    diagnosis = DiagnosisEngine().diagnose(
        incident,
        classification,
    )

    assert diagnosis.evidence_references == []