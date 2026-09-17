from datetime import datetime, timezone

import pytest

from remediation.model import RemediationResult
from verification.model import VerificationResult
from verification.verifier import RemediationVerifier


def make_remediation_result(
    action_type: str = "restart",
    status: str = "executed",
) -> RemediationResult:
    return RemediationResult(
        request_id="req-1",
        incident_id="incident-1",
        action_type=action_type,
        target="deployment/api",
        status=status,
        message="test remediation",
        executed_at=datetime.now(timezone.utc),
    )


def test_successful_restart_is_verified_as_recovered():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("restart"),
        {
            "ready": True,
            "restart_loop": False,
        },
    )

    assert result.status == "recovered"
    assert result.recovered is True


def test_restart_loop_means_not_recovered():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("restart"),
        {
            "ready": False,
            "restart_loop": True,
        },
    )

    assert result.status == "not_recovered"
    assert result.recovered is False


def test_restart_requires_ready_state():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("restart"),
        {
            "ready": False,
            "restart_loop": False,
        },
    )

    assert result.recovered is False


def test_scale_is_recovered_when_ready_replicas_match_desired():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("scale"),
        {
            "ready_replicas": 3,
            "desired_replicas": 3,
        },
    )

    assert result.status == "recovered"
    assert result.recovered is True


def test_scale_is_not_recovered_when_replicas_are_insufficient():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("scale"),
        {
            "ready_replicas": 2,
            "desired_replicas": 3,
        },
    )

    assert result.status == "not_recovered"
    assert result.recovered is False


def test_rollback_requires_healthy_deployment_and_completion():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("rollback"),
        {
            "deployment_healthy": True,
            "rollback_complete": True,
        },
    )

    assert result.recovered is True


def test_incomplete_rollback_is_not_recovered():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("rollback"),
        {
            "deployment_healthy": True,
            "rollback_complete": False,
        },
    )

    assert result.recovered is False


def test_memory_increase_is_recovered_when_ready_and_no_oom():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("increase_memory"),
        {
            "ready": True,
            "oom_killed": False,
        },
    )

    assert result.status == "recovered"
    assert result.recovered is True


def test_memory_increase_is_not_recovered_after_oom():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("increase_memory"),
        {
            "ready": True,
            "oom_killed": True,
        },
    )

    assert result.status == "not_recovered"
    assert result.recovered is False


def test_failed_remediation_is_not_verified():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("restart", status="failed"),
        {
            "ready": True,
            "restart_loop": False,
        },
    )

    assert result.status == "not_verified"
    assert result.recovered is False


def test_verification_result_serializes():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("restart"),
        {
            "ready": True,
            "restart_loop": False,
        },
    )

    data = result.to_dict()

    assert data["request_id"] == "req-1"
    assert data["incident_id"] == "incident-1"
    assert data["action_type"] == "restart"
    assert data["recovered"] is True
    assert data["status"] == "recovered"
    assert "verified_at" in data
    assert "details" in data


def test_unknown_action_uses_generic_health_check():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("custom_action"),
        {
            "healthy": True,
        },
    )

    assert result.recovered is True


def test_unknown_action_without_health_is_not_recovered():
    verifier = RemediationVerifier()

    result = verifier.verify(
        make_remediation_result("custom_action"),
        {},
    )

    assert result.recovered is False