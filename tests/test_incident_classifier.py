from datetime import datetime

from incident_engine.classifier import IncidentClassifier
from incident_engine.detector import IncidentCandidate


def make_incident(
    title: str,
    detector: str = "TestDetector",
) -> IncidentCandidate:
    return IncidentCandidate(
        detector=detector,
        title=title,
        severity="warning",
        timestamp=datetime.now(),
    )


def test_classify_scheduling():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Pod Pending")
    )

    assert result.category == "Scheduling"
    assert result.confidence > 0.9


def test_classify_resource():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("High CPU")
    )

    assert result.category == "Resource"


def test_classify_oom():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("OOMKilled")
    )

    assert result.category == "Resource"


def test_classify_application():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Application Error")
    )

    assert result.category == "Application"


def test_classify_networking():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Network Timeout")
    )

    assert result.category == "Networking"


def test_classify_dependency():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Dependency Failure")
    )

    assert result.category == "Dependency"


def test_classify_configuration():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Configuration Error")
    )

    assert result.category == "Configuration"


def test_unknown_classification():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("Something Strange")
    )

    assert result.category == "Unknown"


def test_classification_is_serializable():
    classifier = IncidentClassifier()

    result = classifier.classify(
        make_incident("High Memory")
    )

    data = result.to_dict()

    assert data["category"] == "Resource"
    assert "confidence" in data
    assert "evidence_references" in data
    assert "explanation" in data