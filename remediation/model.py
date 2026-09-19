from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RemediationResult:
    """
    Records the result of an executed remediation action.

    This represents an actual execution attempt, unlike a
    CounterfactualPrediction, which is hypothetical.
    """

    request_id: str
    incident_id: str
    action_type: str
    target: str | None
    status: str
    message: str
    executed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "target": self.target,
            "status": self.status,
            "message": self.message,
            "executed_at": self.executed_at.isoformat(),
            "details": dict(self.details),
        }
