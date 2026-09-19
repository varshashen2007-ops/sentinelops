from unittest.mock import Mock

from remediation.actions import (
    ActionResult,
    ActionType,
    RemediationAction,
    ResourceType,
)
from remediation.audit import AuditLog
from remediation.service import RemediationService


def make_action() -> RemediationAction:
    return RemediationAction(
        action_type=ActionType.RESTART,
        resource_type=ResourceType.DEPLOYMENT,
        namespace="default",
        resource_name="web",
    )


def test_service_executes_approved_action() -> None:
    executor = Mock()

    executor.execute.return_value = ActionResult(
        action_type=ActionType.RESTART,
        resource_type=ResourceType.DEPLOYMENT,
        namespace="default",
        resource_name="web",
        dry_run=True,
        success=True,
        message="validated",
    )

    audit_log = AuditLog()

    service = RemediationService(
        executor=executor,
        audit_log=audit_log,
    )

    result = service.execute(
        make_action(),
        requester="dhrithi",
        dry_run=True,
    )

    assert result.success is True
    executor.execute.assert_called_once()

    entries = audit_log.list()

    assert len(entries) == 1
    assert entries[0].requester == "dhrithi"
    assert entries[0].action == "restart"
    assert entries[0].success is True


def test_service_rejects_unapproved_action() -> None:
    executor = Mock()
    approval = Mock()
    approval.approve.return_value = False

    audit_log = AuditLog()

    service = RemediationService(
        executor=executor,
        approval_provider=approval,
        audit_log=audit_log,
    )

    result = service.execute(
        make_action(),
        requester="dhrithi",
    )

    assert result.success is False
    assert "not approved" in result.message

    executor.execute.assert_not_called()

    entries = audit_log.list()

    assert len(entries) == 1
    assert entries[0].approval == "denied"


def test_service_rejects_policy_failure() -> None:
    executor = Mock()
    policy = Mock()
    policy.validate.return_value = False

    audit_log = AuditLog()

    service = RemediationService(
        executor=executor,
        policy_provider=policy,
        audit_log=audit_log,
    )

    result = service.execute(
        make_action(),
        requester="dhrithi",
    )

    assert result.success is False
    assert "policy" in result.message

    executor.execute.assert_not_called()

    entries = audit_log.list()

    assert len(entries) == 1
    assert entries[0].approval == "approved"
    assert entries[0].success is False