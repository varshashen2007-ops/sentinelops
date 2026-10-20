from datetime import datetime, timezone

import pytest

from incident_engine.telemetry_evidence import analyze_metric


def test_metric_increase_produces_evidence():
    evidence = analyze_metric(
        metric_name="container_cpu_usage",
        baseline=20,
        current_value=80,
        timestamp=datetime(2026, 10, 20, tzinfo=timezone.utc),
        namespace="default",
        resource="checkout-service",
    )

    assert evidence.source == "prometheus"
    assert evidence.evidence_type == "metric"
    assert evidence.namespace == "default"
    assert evidence.resource == "checkout-service"
    assert evidence.data["absolute_change"] == 60
    assert evidence.data["relative_change_pct"] == 300
    assert evidence.data["interpretation"] == "Metric increased"


def test_zero_baseline_does_not_divide_by_zero():
    evidence = analyze_metric(
        metric_name="http_errors",
        baseline=0,
        current_value=5,
    )

    assert evidence.data["absolute_change"] == 5
    assert evidence.data["relative_change_pct"] is None
    assert evidence.data["baseline_is_zero"] is True


def test_unchanged_metric():
    evidence = analyze_metric(
        metric_name="request_rate",
        baseline=10,
        current_value=10,
    )

    assert evidence.data["absolute_change"] == 0
    assert evidence.data["relative_change_pct"] == 0
    assert evidence.data["interpretation"] == "Metric unchanged"


def test_metric_decrease():
    evidence = analyze_metric(
        metric_name="memory_usage",
        baseline=80,
        current_value=20,
    )

    assert evidence.data["absolute_change"] == -60
    assert evidence.data["relative_change_pct"] == -75
    assert evidence.data["interpretation"] == "Metric decreased"


def test_empty_metric_name_is_rejected():
    with pytest.raises(ValueError, match="metric_name"):
        analyze_metric("", 10, 20)


@pytest.mark.parametrize(
    "baseline,current",
    [
        (float("nan"), 10),
        (10, float("nan")),
        (float("inf"), 10),
        (10, float("-inf")),
    ],
)
def test_non_finite_values_are_rejected(baseline, current):
    with pytest.raises(ValueError):
        analyze_metric("cpu_usage", baseline, current)
