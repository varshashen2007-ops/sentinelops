from models.incident import Incident, IncidentOutcome, IncidentResolution
from remediation.model import RemediationResult
from verification.model import VerificationResult


class IncidentOutcomeRecorder:
    """
    Records the observed result of a remediation into an Incident.

    This service does not execute remediation, perform diagnosis, or
    generate predictions. It only records the verified outcome.
    """

    def record(
        self,
        incident: Incident,
        remediation_result: RemediationResult,
        verification_result: VerificationResult,
    ) -> Incident:
        if incident.incident_id != remediation_result.incident_id:
            raise ValueError(
                "Incident ID does not match the remediation result."
            )

        if incident.incident_id != verification_result.incident_id:
            raise ValueError(
                "Incident ID does not match the verification result."
            )

        if (
            remediation_result.request_id
            != verification_result.request_id
        ):
            raise ValueError(
                "Request ID does not match between remediation and verification."
            )

        incident.resolution = IncidentResolution(
            action=remediation_result.action_type,
            description=remediation_result.message,
        )

        incident.outcome = IncidentOutcome(
            status=verification_result.status,
            description=verification_result.message,
            verified=True,
        )

        return incident