from dataclasses import dataclass, field
from typing import Any

from diagnosis.model import Diagnosis


@dataclass
class GuardrailIssue:
    """
    Describes a problem found while validating a diagnosis.
    """

    claim: str
    reason: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass
class GuardrailResult:
    """
    Result of validating a diagnosis against available evidence.

    passed:
        Whether the diagnosis satisfies the configured guardrails.

    supported_claims:
        Claims that have explicit supporting evidence.

    contextual_claims:
        Claims informed by historical/RAG context.

    issues:
        Unsupported or problematic claims identified by validation.
    """

    passed: bool
    supported_claims: list[str] = field(default_factory=list)
    contextual_claims: list[str] = field(default_factory=list)
    issues: list[GuardrailIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "supported_claims": self.supported_claims,
            "contextual_claims": self.contextual_claims,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
        }


class DiagnosisGuardrail:
    """
    Validates a diagnosis against its available evidence.

    The guardrail is intentionally conservative:
    historical context can inform a diagnosis, but it cannot be
    treated as direct evidence for the current incident.

    Evidence support is determined deterministically from the
    root-cause claim and the content of current evidence references.
    """

    _ROOT_CAUSE_KEYWORDS: dict[str, tuple[str, ...]] = {
        "memory": (
            "memory",
            "oom",
            "oomkilled",
            "out of memory",
            "limit",
        ),
        "scheduling": (
            "scheduling",
            "failedscheduling",
            "unschedulable",
            "no nodes",
            "resource",
        ),
        "startup": (
            "startup",
            "start",
            "crashloopbackoff",
            "crash loop",
        ),
        "readiness": (
            "readiness",
            "ready",
            "unready",
            "health check",
        ),
        "network": (
            "network",
            "connection",
            "connectivity",
            "timeout",
            "dns",
        ),
        "dependency": (
            "dependency",
            "upstream",
            "downstream",
            "service unavailable",
        ),
        "configuration": (
            "configuration",
            "config",
            "environment variable",
            "misconfigured",
        ),
        "infrastructure": (
            "infrastructure",
            "node",
            "disk",
            "storage",
        ),
        "application": (
            "application",
            "exception",
            "error",
            "failure",
        ),
    }

    def validate(self, diagnosis: Diagnosis) -> GuardrailResult:
        supported_claims: list[str] = []
        contextual_claims: list[str] = []
        issues: list[GuardrailIssue] = []

        root_cause = diagnosis.root_cause.strip()

        if not root_cause:
            issues.append(
                GuardrailIssue(
                    claim="",
                    reason=(
                        "Diagnosis does not contain a root-cause claim."
                    ),
                    severity="error",
                )
            )

        elif not diagnosis.evidence_references:
            issues.append(
                GuardrailIssue(
                    claim=root_cause,
                    reason=(
                        "No current evidence reference supports "
                        "the root-cause claim."
                    ),
                    severity="error",
                )
            )

        elif self._claim_is_supported(diagnosis):
            supported_claims.append(root_cause)

        else:
            issues.append(
                GuardrailIssue(
                    claim=root_cause,
                    reason=(
                        "Current evidence references exist, but their "
                        "content does not contain deterministic support "
                        "for the root-cause claim."
                    ),
                    severity="error",
                )
            )

        if diagnosis.historical_incident_ids:
            contextual_claims.extend(
                diagnosis.historical_incident_ids
            )

        passed = len(issues) == 0

        return GuardrailResult(
            passed=passed,
            supported_claims=supported_claims,
            contextual_claims=contextual_claims,
            issues=issues,
        )

    def _claim_is_supported(self, diagnosis: Diagnosis) -> bool:
        """
        Determine whether current evidence contains content related
        to the diagnosis root cause.

        Matching is intentionally deterministic and explainable.
        Historical incidents are never inspected here.
        """

        root_cause = diagnosis.root_cause.lower()

        for evidence in diagnosis.evidence_references:
            evidence_text = self._evidence_to_text(evidence)

            if self._text_supports_claim(
                root_cause=root_cause,
                evidence_text=evidence_text,
            ):
                return True

        return False

    @staticmethod
    def _evidence_to_text(evidence: Any) -> str:
        """
        Flatten an evidence reference into searchable text.
        """

        parts: list[str] = [
            str(evidence.source),
            str(evidence.evidence_type),
            str(evidence.description),
            str(evidence.resource or ""),
        ]

        for key, value in evidence.data.items():
            parts.append(str(key))
            parts.append(str(value))

        return " ".join(parts).lower()

    @classmethod
    def _text_supports_claim(
        cls,
        root_cause: str,
        evidence_text: str,
    ) -> bool:
        """
        Check whether evidence contains terms associated with the
        root-cause category.

        Direct phrase matching is attempted first. If that does not
        match, deterministic category keywords are used.
        """

        if root_cause in evidence_text:
            return True

        for keywords in cls._ROOT_CAUSE_KEYWORDS.values():
            claim_matches_category = any(
                keyword in root_cause
                for keyword in keywords
            )

            if not claim_matches_category:
                continue

            return any(
                keyword in evidence_text
                for keyword in keywords
            )

        return False