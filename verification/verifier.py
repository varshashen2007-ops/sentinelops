from typing import Any

from remediation.model import RemediationResult
from verification.model import VerificationResult


class RemediationVerifier:
    """
    Deterministically verifies whether an executed remediation recovered
    the incident based on observed post-remediation state.
    """

    def verify(
        self,
        remediation_result: RemediationResult,
        observed_state: dict[str, Any],
    ) -> VerificationResult:
        if remediation_result.status != "executed":
            return VerificationResult(
                request_id=remediation_result.request_id,
                incident_id=remediation_result.incident_id,
                action_type=remediation_result.action_type,
                target=remediation_result.target,
                status="not_verified",
                recovered=False,
                message="Remediation was not successfully executed.",
                details={
                    "remediation_status": remediation_result.status,
                },
            )

        recovery_checks = self._evaluate_recovery(
            action_type=remediation_result.action_type,
            observed_state=observed_state,
        )

        recovered = bool(recovery_checks["recovered"])

        return VerificationResult(
            request_id=remediation_result.request_id,
            incident_id=remediation_result.incident_id,
            action_type=remediation_result.action_type,
            target=remediation_result.target,
            status="recovered" if recovered else "not_recovered",
            recovered=recovered,
            message=(
                "Post-remediation verification confirms recovery."
                if recovered
                else "Post-remediation verification does not confirm recovery."
            ),
            details=recovery_checks,
        )

    @staticmethod
    def _evaluate_recovery(
        action_type: str,
        observed_state: dict[str, Any],
    ) -> dict[str, Any]:
        action = action_type.lower().strip()

        checks: dict[str, Any] = {
            "action_type": action,
            "observed_state": dict(observed_state),
            "recovered": False,
        }

        if action == "restart":
            checks["recovered"] = (
                observed_state.get("ready") is True
                and observed_state.get("restart_loop") is False
            )

        elif action == "scale":
            checks["recovered"] = (
                observed_state.get("ready_replicas", 0)
                >= observed_state.get("desired_replicas", 1)
            )

        elif action == "rollback":
            checks["recovered"] = (
                observed_state.get("deployment_healthy") is True
                and observed_state.get("rollback_complete") is True
            )

        elif action == "increase_memory":
            checks["recovered"] = (
                observed_state.get("ready") is True
                and observed_state.get("oom_killed") is False
            )

        else:
            checks["recovered"] = observed_state.get("healthy") is True

        return checks