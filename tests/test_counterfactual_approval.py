from datetime import datetime

import pytest

from counterfactual.approval import ApprovalRequest
from counterfactual.approval_manager import ApprovalManager


def test_create_request_starts_pending():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-001",
        incident_id="INC-001",
        action_type="restart",
        target="api-server",
    )

    assert request.request_id == "REQ-001"
    assert request.incident_id == "INC-001"
    assert request.action_type == "restart"
    assert request.target == "api-server"
    assert request.status == "pending"
    assert isinstance(request.requested_at, datetime)
    assert request.decided_at is None
    assert request.decided_by is None


def test_approve_request():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-002",
        incident_id="INC-002",
        action_type="rollback",
    )

    result = manager.decide(
        request=request,
        decision="approved",
        decided_by="operator-1",
        reason="Verified against incident evidence.",
    )

    assert result.status == "approved"
    assert result.decided_by == "operator-1"
    assert result.reason == "Verified against incident evidence."
    assert result.decided_at is not None
    assert manager.is_approved(result)


def test_reject_request():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-003",
        incident_id="INC-003",
        action_type="scale",
    )

    result = manager.decide(
        request=request,
        decision="rejected",
        decided_by="operator-2",
        reason="Scaling does not address the identified failure.",
    )

    assert result.status == "rejected"
    assert result.decided_by == "operator-2"
    assert result.decided_at is not None
    assert manager.is_rejected(result)


def test_pending_request_detection():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-004",
        incident_id="INC-004",
        action_type="restart",
    )

    assert manager.is_pending(request)
    assert not manager.is_approved(request)
    assert not manager.is_rejected(request)


def test_invalid_decision_is_rejected():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-005",
        incident_id="INC-005",
        action_type="restart",
    )

    with pytest.raises(ValueError, match="approved.*rejected"):
        manager.decide(
            request=request,
            decision="maybe",
            decided_by="operator-1",
        )


def test_missing_decision_maker_is_rejected():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-006",
        incident_id="INC-006",
        action_type="restart",
    )

    with pytest.raises(
        ValueError,
        match="decision maker",
    ):
        manager.decide(
            request=request,
            decision="approved",
            decided_by="",
        )


def test_non_pending_request_cannot_be_decided_twice():
    manager = ApprovalManager()

    request = manager.create_request(
        request_id="REQ-007",
        incident_id="INC-007",
        action_type="restart",
    )

    manager.decide(
        request=request,
        decision="approved",
        decided_by="operator-1",
    )

    with pytest.raises(
        ValueError,
        match="Only pending",
    ):
        manager.decide(
            request=request,
            decision="rejected",
            decided_by="operator-2",
        )


def test_approval_request_serializes():
    request = ApprovalRequest(
        request_id="REQ-008",
        incident_id="INC-008",
        action_type="increase_memory",
        target="api-server",
    )

    data = request.to_dict()

    assert data["request_id"] == "REQ-008"
    assert data["incident_id"] == "INC-008"
    assert data["action_type"] == "increase_memory"
    assert data["target"] == "api-server"
    assert data["status"] == "pending"
    assert data["requested_at"] is not None
    assert data["decided_at"] is None
