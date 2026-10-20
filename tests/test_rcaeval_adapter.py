from pathlib import Path

import pandas as pd
import pytest

from embeddings.incident_document import IncidentDocumentBuilder
from rag.rcaeval_adapter import RCAEvalAdapter


def test_adapter_loads_all_valid_rcaeval_cases():
    incidents = RCAEvalAdapter(
        "data/rcaeval_case_features.csv"
    ).load_incidents()

    assert len(incidents) == 123
    assert all(
        incident.incident_id.startswith("rcaeval:")
        for incident in incidents
    )


def test_adapter_keeps_fault_label_out_of_searchable_document():
    incidents = RCAEvalAdapter(
        "data/rcaeval_case_features.csv"
    ).load_incidents()

    for incident in incidents:
        document = IncidentDocumentBuilder().build(incident)
        fault_type = incident.metadata["fault_type"]

        assert "fault_type:" not in document
        assert "Fault Type:" not in document
        assert incident.metadata["source"] == "RCAEval"
        assert incident.metadata["outcome_verified"] is False


def test_adapter_includes_service_and_telemetry_in_document():
    incidents = RCAEvalAdapter(
        "data/rcaeval_case_features.csv"
    ).load_incidents()

    incident = incidents[0]
    document = IncidentDocumentBuilder().build(incident)

    assert incident.metadata["service"] in document
    assert "mean_delta" in document
    assert incident.metadata["telemetry_features"]


def test_adapter_rejects_missing_required_columns(tmp_path: Path):
    feature_file = tmp_path / "invalid.csv"
    pd.DataFrame(
        [{"case_id": "case-1", "service": "adservice"}]
    ).to_csv(feature_file, index=False)

    with pytest.raises(ValueError, match="missing columns"):
        RCAEvalAdapter(feature_file).load_incidents()


def test_adapter_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        RCAEvalAdapter(
            tmp_path / "does-not-exist.csv"
        ).load_incidents()
