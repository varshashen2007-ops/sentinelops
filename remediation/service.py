from __future__ import annotations

from typing import Protocol

from remediation.actions import ActionResult, RemediationAction
from remediation.audit import AuditEntry, AuditLog
from remediation.executor import RemediationExecutor


class ApprovalProvider(Protocol):
    def approve(self, action: RemediationAction, requester: str) -> bool:
        ...


class PolicyProvider(Protocol):
    def validate(
        self,
        action: RemediationAction,
        requester: str,
    ) -> bool:
        ...


class AllowAllApprovalProvider:
    """Infrastructure default used for local development and tests."""

    def approve(
        self,
        action: RemediationAction,
        requester: str,
    ) -> bool:
        return True


class AllowAllPolicyProvider:
    """Placeholder infrastructure provider.

    Domain-specific policy decisions belong outside this class.
    """

    def validate(
        self,
        action: RemediationAction,
        requester: str,
    ) -> bool:
        return True


class RemediationService:
    """Coordinates approval, policy validation, execution and auditing."""

    def __init__(
        self,
        executor: RemediationExecutor,
        approval_provider: ApprovalProvider | None = None,
        policy_provider: PolicyProvider | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.executor = executor
        self.approval_provider = (
            approval_provider or AllowAllApprovalProvider()
        )
        self.policy_provider = (
            policy_provider or AllowAllPolicyProvider()
        )
        self.audit_log = audit_log or AuditLog()

    def execute(
        self,
        action: RemediationAction,
        *,
        requester: str,
        dry_run: bool = False,
    ) -> ActionResult:
        approved = self.approval_provider.approve(
            action,
            requester,
        )

        if not approved:
            result = ActionResult(
                action_type=action.action_type,
                resource_type=action.resource_type,
                namespace=action.namespace,
                resource_name=action.resource_name,
                dry_run=dry_run,
                success=False,
                message="Remediation action was not approved.",
            )

            self._audit(
                action,
                requester=requester,
                approval="denied",
                result=result,
            )

            return result

        allowed = self.policy_provider.validate(
            action,
            requester,
        )

        if not allowed:
            result = ActionResult(
                action_type=action.action_type,
                resource_type=action.resource_type,
                namespace=action.namespace,
                resource_name=action.resource_name,
                dry_run=dry_run,
                success=False,
                message="Remediation action was rejected by policy.",
            )

            self._audit(
                action,
                requester=requester,
                approval="approved",
                result=result,
            )

            return result

        result = self.executor.execute(
            action,
            dry_run=dry_run,
        )

        self._audit(
            action,
            requester=requester,
            approval="approved",
            result=result,
        )

        return result

    def _audit(
        self,
        action: RemediationAction,
        *,
        requester: str,
        approval: str,
        result: ActionResult,
    ) -> None:
        self.audit_log.record(
            AuditEntry(
                requester=requester,
                action=action.action_type.value,
                target=(
                    f"{action.resource_type.value}/"
                    f"{action.namespace}/"
                    f"{action.resource_name}"
                ),
                parameters=dict(action.parameters),
                approval=approval,
                success=result.success,
                error=None if result.success else result.message,
            )
        )