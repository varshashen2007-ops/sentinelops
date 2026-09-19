from __future__ import annotations

from dataclasses import dataclass

from remediation.actions import ActionType, RemediationAction


@dataclass(frozen=True)
class DryRunResult:
    valid: bool
    message: str


class DryRunValidator:
    """Validates remediation actions before execution."""

    def validate(self, action: RemediationAction) -> DryRunResult:
        parameters = action.parameters

        if action.action_type is ActionType.RESTART:
            return self._validate_restart(parameters)

        if action.action_type is ActionType.SCALE:
            return self._validate_scale(parameters)

        if action.action_type is ActionType.ROLLBACK:
            return self._validate_rollback(parameters)

        if action.action_type is ActionType.PATCH:
            return self._validate_patch(parameters)

        return DryRunResult(
            valid=False,
            message="Unsupported remediation action.",
        )

    @staticmethod
    def _validate_restart(parameters: dict) -> DryRunResult:
        if parameters:
            allowed = {"reason"}

            unexpected = set(parameters) - allowed

            if unexpected:
                return DryRunResult(
                    valid=False,
                    message=(
                        "restart contains unsupported parameters: "
                        f"{sorted(unexpected)}"
                    ),
                )

        return DryRunResult(
            valid=True,
            message="Restart action passed validation.",
        )

    @staticmethod
    def _validate_scale(parameters: dict) -> DryRunResult:
        replicas = parameters.get("replicas")

        if not isinstance(replicas, int):
            return DryRunResult(
                valid=False,
                message="scale requires integer parameter 'replicas'.",
            )

        if replicas < 0:
            return DryRunResult(
                valid=False,
                message="replicas must be greater than or equal to zero.",
            )

        return DryRunResult(
            valid=True,
            message="Scale action passed validation.",
        )

    @staticmethod
    def _validate_rollback(parameters: dict) -> DryRunResult:
        revision = parameters.get("revision")

        if revision is not None:
            if not isinstance(revision, int):
                return DryRunResult(
                    valid=False,
                    message="revision must be an integer.",
                )

            if revision <= 0:
                return DryRunResult(
                    valid=False,
                    message="revision must be greater than zero.",
                )

        return DryRunResult(
            valid=True,
            message="Rollback action passed validation.",
        )

    @staticmethod
    def _validate_patch(parameters: dict) -> DryRunResult:
        patch = parameters.get("patch")

        if not isinstance(patch, dict):
            return DryRunResult(
                valid=False,
                message="patch requires a dictionary parameter 'patch'.",
            )

        if not patch:
            return DryRunResult(
                valid=False,
                message="patch must not be empty.",
            )

        return DryRunResult(
            valid=True,
            message="Patch action passed validation.",
        )