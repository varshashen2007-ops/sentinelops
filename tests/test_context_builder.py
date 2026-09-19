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


def test_context_extracts_historical_resolution_and_outcome():
    document = (
        "Incident ID: incident-001\n"
        "Failure: OOMKilled\n"
        "Resolution Action: increase_memory\n"
        "Resolution Description: Memory limit increased.\n"
        "Outcome Status: recovered\n"
        "Outcome Description: Application recovered.\n"
        "Outcome Verified: True"
    )

    context = RAGContextBuilder().build(
        [make_incident("incident-001", 0.95, document)]
    )

    experiences = context.experiences

    assert len(experiences) == 1

    experience = experiences[0]

    assert experience.incident_id == "incident-001"
    assert experience.similarity_score == 0.95
    assert experience.resolution_action == "increase_memory"
    assert experience.resolution_description == "Memory limit increased."
    assert experience.outcome_status == "recovered"
    assert experience.outcome_description == "Application recovered."
    assert experience.outcome_verified is True


def test_context_extracts_failed_historical_outcome():
    document = (
        "Incident ID: incident-002\n"
        "Failure: OOMKilled\n"
        "Resolution Action: restart\n"
        "Outcome Status: not_recovered\n"
        "Outcome Verified: True"
    )

    context = RAGContextBuilder().build(
        [make_incident("incident-002", 0.88, document)]
    )

    experience = context.experiences[0]

    assert experience.resolution_action == "restart"
    assert experience.outcome_status == "not_recovered"
    assert experience.outcome_verified is True


def test_context_handles_incident_without_outcome():
    context = RAGContextBuilder().build(
        [
            make_incident(
                "incident-003",
                0.80,
                "Incident ID: incident-003\n"
                "Failure: FailedScheduling",
            )
        ]
    )

    experience = context.experiences[0]

    assert experience.resolution_action is None
    assert experience.resolution_description is None
    assert experience.outcome_status is None
    assert experience.outcome_description is None
    assert experience.outcome_verified is None


def test_experience_to_dict_contains_all_fields():
    document = (
        "Resolution Action: rollback\n"
        "Resolution Description: Rolled back deployment.\n"
        "Outcome Status: recovered\n"
        "Outcome Description: Service became healthy.\n"
        "Outcome Verified: True"
    )

    context = RAGContextBuilder().build(
        [make_incident("incident-004", 0.92, document)]
    )

    data = context.experiences[0].to_dict()

    assert data["incident_id"] == "incident-004"
    assert data["similarity_score"] == 0.92
    assert data["resolution_action"] == "rollback"
    assert data["resolution_description"] == "Rolled back deployment."
    assert data["outcome_status"] == "recovered"
    assert data["outcome_description"] == "Service became healthy."
    assert data["outcome_verified"] is True


def test_context_text_explicitly_shows_historical_experience():
    document = (
        "Incident ID: incident-005\n"
        "Failure: OOMKilled\n"
        "Resolution Action: increase_memory\n"
        "Outcome Status: recovered\n"
        "Outcome Verified: True"
    )

    context = RAGContextBuilder().build(
        [make_incident("incident-005", 0.90, document)]
    )

    text = context.to_text()

    assert "Historical Resolution: increase_memory" in text
    assert "Historical Outcome: recovered" in text
    assert "Historical Outcome Verified: True" in text