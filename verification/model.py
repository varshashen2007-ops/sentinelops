from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class VerificationResult:
    request_id: str
    incident_id: str
    action_type: str
    target: str | None
    status: str
    recovered: bool
    message: str
    verified_at: datetime = field(
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
            "recovered": self.recovered,
            "message": self.message,
            "verified_at": self.verified_at.isoformat(),
            "details": dict(self.details),
        }
    