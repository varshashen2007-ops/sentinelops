from datetime import datetime, timezone

from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.incident_index import IncidentVectorIndex
from embeddings.service import EmbeddingService
from embeddings.vector_store import InMemoryVectorStore
from incident_engine.dna import IncidentDNA
from learning.outcome_recorder import IncidentOutcomeRecorder
from models.incident import Incident
from remediation.model import RemediationResult
from verification.model import VerificationResult


class FakeEmbeddingProvider:
    """
    Deterministic provider for testing the complete
    outcome-to-memory workflow.
    """

    def embed(self, text: str) -> list[float]:
        text_lower = text.lower()

        if "oomkilled" in text_lower:
            return [1.0, 0.0, 0.0]

        if "failedscheduling" in text_lower:
            return [0.0, 1.0, 0.0]

        return [0.5, 0.5, 0.0]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def create_index() -> IncidentVectorIndex:
    embedding_service = EmbeddingService(
        FakeEmbeddingProvider()
    )

    incident_embedding_service = IncidentEmbeddingService(
        embedding_service=embedding_service,
    )

    vector_store = InMemoryVectorStore(
        dimensions=3
    )

    return IncidentVectorIndex(
        embedding_service=incident_embedding_service,
        vector_store=vector_store,
    )


def create_incident() -> Incident:
    return Incident(
        incident_id="incident-001",
        started_at=datetime(
            2026,
            9,
            17,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        dna=IncidentDNA(
            failure="OOMKilled",
        ),
    )


def create_remediation_result() -> RemediationResult:
    return RemediationResult(
        request_id="request-001",
        incident_id="incident-001",
        action_type="increase_memory",
        target="deployment/api",
        status="executed",
        message="Memory limit increased successfully.",
    )


def create_verification_result() -> VerificationResult:
    return VerificationResult(
        request_id="request-001",
        incident_id="incident-001",
        action_type="increase_memory",
        target="deployment/api",
        status="recovered",
        recovered=True,
        message="Application recovered after memory increase.",
    )


def test_verified_outcome_is_added_to_incident_memory():
    incident = create_incident()

    recorder = IncidentOutcomeRecorder()

    updated_incident = recorder.record(
        incident,
        create_remediation_result(),
        create_verification_result(),
    )

    index = create_index()

    index.add_incident(updated_incident)

    stored = index.vector_store.get("incident-001")

    assert stored is not None

    document = stored.metadata["document"]

    assert "Resolution Action: increase_memory" in document
    assert "Outcome Status: recovered" in document
    assert "Outcome Verified: True" in document


def test_updating_memory_replaces_previous_incident_representation():
    incident = create_incident()

    index = create_index()

    index.add_incident(incident)

    stored_before = index.vector_store.get(
        "incident-001"
    )

    assert stored_before is not None
    assert "Outcome Status" not in stored_before.metadata["document"]

    recorder = IncidentOutcomeRecorder()

    recorder.record(
        incident,
        create_remediation_result(),
        create_verification_result(),
    )

    index.update_incident(incident)

    stored_after = index.vector_store.get(
        "incident-001"
    )

    assert stored_after is not None
    assert "Outcome Status: recovered" in stored_after.metadata["document"]
    assert "Resolution Action: increase_memory" in stored_after.metadata["document"]
    assert index.count() == 1


def test_failed_recovery_is_also_preserved_in_memory():
    incident = create_incident()

    recorder = IncidentOutcomeRecorder()

    verification = VerificationResult(
        request_id="request-001",
        incident_id="incident-001",
        action_type="increase_memory",
        target="deployment/api",
        status="not_recovered",
        recovered=False,
        message="Application remained unhealthy after remediation.",
    )

    recorder.record(
        incident,
        create_remediation_result(),
        verification,
    )

    index = create_index()
    index.add_incident(incident)

    stored = index.vector_store.get(
        "incident-001"
    )

    assert stored is not None

    document = stored.metadata["document"]

    assert "Outcome Status: not_recovered" in document
    assert "Outcome Verified: True" in document


def test_memory_count_remains_stable_after_outcome_update():
    incident = create_incident()

    index = create_index()

    index.add_incident(incident)

    assert index.count() == 1

    recorder = IncidentOutcomeRecorder()

    recorder.record(
        incident,
        create_remediation_result(),
        create_verification_result(),
    )

    index.update_incident(incident)

    assert index.count() == 1