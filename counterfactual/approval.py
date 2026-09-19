from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ApprovalRequest:
    """
    Represents a human approval request for a counterfactual action.

    Creating an approval request does not execute the action.
    """

    request_id: str
    incident_id: str
    action_type: str
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    requested_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    decided_at: datetime | None = None
    decided_by: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "target": self.target,
            "parameters": dict(self.parameters),
            "status": self.status,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": (
                self.decided_at.isoformat()
                if self.decided_at is not None
                else None
            ),
            "decided_by": self.decided_by,
            "reason": self.reason,
        }
