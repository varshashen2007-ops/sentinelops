from datetime import datetime, timezone
from typing import Any

from models.evidence import Evidence


def analyze_metric(
    metric_name: str,
    baseline: float,
    current_value: float,
    timestamp: datetime | None = None,
    namespace: str | None = None,
    resource: str | None = None,
) -> Evidence:
    """Create evidence describing a telemetry change."""

    baseline = float(baseline)
    current_value = float(current_value)

    if not metric_name.strip():
        raise ValueError("metric_name must not be empty")

    if baseline != baseline or current_value != current_value:
        raise ValueError("Metric values must not be NaN")

    if abs(baseline) == float("inf") or abs(current_value) == float("inf"):
        raise ValueError("Metric values must be finite")

    absolute_change = current_value - baseline

    relative_change_pct = (
        (absolute_change / abs(baseline)) * 100.0
        if baseline != 0
        else None
    )

    data: dict[str, Any] = {
        "metric_name": metric_name,
        "baseline": baseline,
        "current_value": current_value,
        "absolute_change": absolute_change,
        "relative_change_pct": relative_change_pct,
        "baseline_is_zero": baseline == 0,
        "interpretation": (
            "Metric increased"
            if absolute_change > 0
            else "Metric decreased"
            if absolute_change < 0
            else "Metric unchanged"
        ),
    }

    return Evidence(
        source="prometheus",
        evidence_type="metric",
        timestamp=timestamp or datetime.now(timezone.utc),
        namespace=namespace,
        resource=resource,
        data=data,
    )
