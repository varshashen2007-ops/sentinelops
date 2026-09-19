from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    requester: str
    action: str
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)
    approval: str = "not_required"
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    success: bool = False
    error: str | None = None


class AuditLog:
    """In-memory audit log for remediation actions.

    The storage implementation can be replaced by persistent storage later.
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def list(self) -> list[AuditEntry]:
        return list(self._entries)