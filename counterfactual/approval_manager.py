from datetime import datetime, timezone

from counterfactual.approval import ApprovalRequest


class ApprovalManager:
    """
    Manages human approval decisions for recovery actions.

    This component only records and validates approval state.
    It never executes Kubernetes operations.
    """

    _VALID_DECISIONS = {"approved", "rejected"}

    def create_request(
        self,
        request_id: str,
        incident_id: str,
        action_type: str,
        target: str | None = None,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=request_id,
            incident_id=incident_id,
            action_type=action_type,
            target=target,
        )

    def decide(
        self,
        request: ApprovalRequest,
        decision: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        normalized_decision = decision.lower().strip()

        if normalized_decision not in self._VALID_DECISIONS:
            raise ValueError(
                "Decision must be either 'approved' or 'rejected'."
            )

        if not decided_by or not decided_by.strip():
            raise ValueError(
                "A decision maker must be provided."
            )

        if request.status != "pending":
            raise ValueError(
                "Only pending approval requests can be decided."
            )

        request.status = normalized_decision
        request.decided_at = datetime.now(timezone.utc)
        request.decided_by = decided_by
        request.reason = reason

        return request

    @staticmethod
    def is_approved(request: ApprovalRequest) -> bool:
        return request.status == "approved"

    @staticmethod
    def is_pending(request: ApprovalRequest) -> bool:
        return request.status == "pending"

    @staticmethod
    def is_rejected(request: ApprovalRequest) -> bool:
        return request.status == "rejected"
