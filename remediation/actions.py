from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    RESTART = "restart"
    SCALE = "scale"
    ROLLBACK = "rollback"
    PATCH = "patch"


class ResourceType(str, Enum):
    DEPLOYMENT = "deployment"
    STATEFULSET = "statefulset"


@dataclass(frozen=True)
class RemediationAction:
    """Structured remediation action.

    This contract intentionally contains no shell commands.
    """

    action_type: ActionType
    resource_type: ResourceType
    namespace: str
    resource_name: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.namespace.strip():
            raise ValueError("namespace must not be empty")

        if not self.resource_name.strip():
            raise ValueError("resource_name must not be empty")

        if not isinstance(self.parameters, dict):
            raise TypeError("parameters must be a dictionary")


@dataclass(frozen=True)
class ActionResult:
    """Structured result returned by remediation execution."""

    action_type: ActionType
    resource_type: ResourceType
    namespace: str
    resource_name: str
    dry_run: bool
    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)