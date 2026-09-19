from incident_engine.dna import IncidentDNA
from incident_engine.novelty import IncidentNoveltyDetector


def test_identical_incident_has_low_novelty():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        readiness="failed",
        affected_workload="sentinel-api",
        duration=120.5,
        severity="high",
    )

    historical = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        readiness="failed",
        affected_workload="sentinel-api",
        duration=120.5,
        severity="high",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        [("incident-001", historical)],
    )

    assert result.novelty_score == 0.0
    assert result.known_pattern is True
    assert len(result.similar_incidents) == 1


def test_different_incident_has_high_novelty():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    historical = IncidentDNA(
        trigger="insufficient_cpu",
        failure="FailedScheduling",
        restart_pattern="none",
        severity="warning",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        [("incident-002", historical)],
    )

    assert result.novelty_score == 1.0
    assert result.known_pattern is False


def test_similar_incidents_are_returned():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    historical = [
        (
            "incident-001",
            IncidentDNA(
                trigger="memory_growth",
                failure="OOMKilled",
                restart_pattern="repeated",
                severity="high",
            ),
        ),
        (
            "incident-002",
            IncidentDNA(
                trigger="insufficient_cpu",
                failure="FailedScheduling",
                severity="warning",
            ),
        ),
    ]

    detector = IncidentNoveltyDetector()

    result = detector.detect(current, historical)

    assert len(result.similar_incidents) == 2
    assert result.similar_incidents[0].incident_id == "incident-001"


def test_results_are_sorted_by_similarity():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        severity="high",
    )

    historical = [
        (
            "low-match",
            IncidentDNA(
                trigger="insufficient_cpu",
                failure="FailedScheduling",
                severity="warning",
            ),
        ),
        (
            "high-match",
            IncidentDNA(
                trigger="memory_growth",
                failure="OOMKilled",
                severity="high",
            ),
        ),
    ]

    detector = IncidentNoveltyDetector()

    result = detector.detect(current, historical)

    assert result.similar_incidents[0].incident_id == "high-match"
    assert (
        result.similar_incidents[0].similarity_score
        >= result.similar_incidents[1].similarity_score
    )


def test_empty_history_is_fully_novel():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(current, [])

    assert result.novelty_score == 1.0
    assert result.similar_incidents == []
    assert result.known_pattern is False


def test_top_k_limits_results():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
    )

    historical = [
        (
            f"incident-{index}",
            IncidentDNA(
                trigger="memory_growth",
                failure="OOMKilled",
            ),
        )
        for index in range(5)
    ]

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        historical,
        top_k=2,
    )

    assert len(result.similar_incidents) == 2


def test_novelty_result_serialization():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
    )

    historical = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        [("incident-001", historical)],
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert "novelty_score" in data
    assert "similar_incidents" in data
    assert "known_pattern" in data


def test_partial_match_produces_intermediate_novelty():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        severity="high",
    )

    historical = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        severity="warning",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        [("incident-001", historical)],
    )

    assert 0.0 < result.novelty_score < 1.0
    assert result.known_pattern is True


def test_known_pattern_threshold():
    current = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="high",
    )

    historical = IncidentDNA(
        trigger="memory_growth",
        failure="OOMKilled",
        restart_pattern="repeated",
        severity="warning",
    )

    detector = IncidentNoveltyDetector()

    result = detector.detect(
        current,
        [("incident-001", historical)],
    )

    assert result.known_pattern is True