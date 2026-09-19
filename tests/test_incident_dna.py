from incident_engine.dna import IncidentDNA


def test_incident_dna_creation():
    dna = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        readiness="failed",
        affected_workload="sentinel-api",
        duration=120.5,
        severity="high",
    )

    assert dna.trigger == "memory_growth"
    assert dna.failure == "OOMKilled"
    assert dna.restart_pattern == "repeated"
    assert dna.readiness == "failed"
    assert dna.affected_workload == "sentinel-api"
    assert dna.duration == 120.5
    assert dna.severity == "high"


def test_incident_dna_serialization():
    dna = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    result = dna.to_dict()

    assert isinstance(result, dict)
    assert result["trigger"] == "memory_growth"
    assert result["failure"] == "OOMKilled"
    assert result["restart_pattern"] == "repeated"
    assert result["severity"] == "high"


def test_incident_dna_is_deterministic():
    dna1 = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    dna2 = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    assert dna1.to_dict() == dna2.to_dict()


def test_incident_dna_supports_dependency_and_anomaly_information():
    dna = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        dependency_information={
            "upstream": ["sentinel-api"],
        },
        anomaly_information={
            "type": "actionable_anomaly",
            "score": 0.9,
        },
    )

    result = dna.to_dict()

    assert result["dependency_information"]["upstream"] == [
        "sentinel-api"
    ]
    assert result["anomaly_information"]["type"] == (
        "actionable_anomaly"
    )