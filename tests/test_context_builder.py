from rag.context_builder import RAGContextBuilder
from rag.retriever import RetrievedIncident


def make_incident(
    incident_id="incident-001",
    similarity_score=0.91,
    document="Historical OOMKilled incident",
):
    return RetrievedIncident(
        incident_id=incident_id,
        similarity_score=similarity_score,
        metadata={
            "incident_id": incident_id,
            "document": document,
        },
    )


def test_context_builder_preserves_retrieved_incidents():
    incidents = [
        make_incident("incident-001", 0.91),
        make_incident("incident-002", 0.82),
    ]

    builder = RAGContextBuilder()
    context = builder.build(incidents)

    assert context.incidents == incidents
    assert len(context.incidents) == 2


def test_context_builder_creates_deterministic_text():
    incidents = [
        make_incident("incident-001", 0.91),
        make_incident("incident-002", 0.82),
    ]

    builder = RAGContextBuilder()

    first = builder.build(incidents).to_text()
    second = builder.build(incidents).to_text()

    assert first == second


def test_context_text_contains_incident_information():
    incidents = [
        make_incident(
            "incident-001",
            0.91,
            "Container exceeded its configured memory limit.",
        )
    ]

    builder = RAGContextBuilder()
    context = builder.build(incidents)

    text = context.to_text()

    assert "Historical Incident 1" in text
    assert "incident-001" in text
    assert "0.9100" in text
    assert "Container exceeded its configured memory limit." in text


def test_empty_context_is_explicit():
    builder = RAGContextBuilder()

    context = builder.build([])

    assert context.incidents == []
    assert context.to_text() == "No relevant historical incidents were retrieved."


def test_context_builder_copies_incident_list():
    incidents = [make_incident()]

    builder = RAGContextBuilder()
    context = builder.build(incidents)

    assert context.incidents == incidents
    assert context.incidents is not incidents