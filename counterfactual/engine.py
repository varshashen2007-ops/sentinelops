from incident_engine.dna import IncidentDNA
from counterfactual.model import (
    CounterfactualAction,
    CounterfactualPrediction,
)


class CounterfactualEngine:
    """
    Deterministic engine for predicting hypothetical recovery outcomes.

    This engine does not execute Kubernetes operations. It evaluates
    recovery actions against the known characteristics of an incident
    and produces an explainable prediction.
    """

    def predict(
        self,
        action: CounterfactualAction,
        dna: IncidentDNA | None,
    ) -> CounterfactualPrediction:
        if dna is None:
            return self._unknown_prediction(action)

        action_type = action.action_type.lower().strip()

        if action_type == "restart":
            return self._predict_restart(action, dna)

        if action_type == "rollback":
            return self._predict_rollback(action, dna)

        if action_type == "scale":
            return self._predict_scale(action, dna)

        if action_type == "increase_memory":
            return self._predict_memory_increase(action, dna)

        return CounterfactualPrediction(
            action=action,
            predicted_status="insufficient_information",
            predicted_effect="No deterministic prediction is available.",
            confidence=0.20,
            rationale=(
                f"Recovery action '{action.action_type}' is not "
                "supported by the current prediction rules."
            ),
            supporting_factors=[],
        )

    @staticmethod
    def _predict_restart(
        action: CounterfactualAction,
        dna: IncidentDNA,
    ) -> CounterfactualPrediction:
        failure = (dna.failure or "").lower()
        restart_pattern = (dna.restart_pattern or "").lower()

        if "crashloop" in failure or "crashloop" in restart_pattern:
            return CounterfactualPrediction(
                action=action,
                predicted_status="likely_recovered",
                predicted_effect=(
                    "Restart may temporarily clear the repeated "
                    "application failure."
                ),
                confidence=0.85,
                rationale=(
                    "The incident contains a repeated application "
                    "failure pattern, making restart a relevant "
                    "counterfactual action."
                ),
                supporting_factors=[
                    "CrashLoopBackOff pattern detected",
                ],
            )

        if "oom" in failure or "memory" in failure:
            return CounterfactualPrediction(
                action=action,
                predicted_status="temporary_recovery",
                predicted_effect=(
                    "Restart may temporarily recover the container, "
                    "but memory exhaustion may recur."
                ),
                confidence=0.70,
                rationale=(
                    "Restart can clear the current process state, "
                    "but it does not change the memory constraint."
                ),
                supporting_factors=[
                    "Memory-related failure detected",
                    "Restart does not change resource limits",
                ],
            )

        return CounterfactualPrediction(
            action=action,
            predicted_status="uncertain",
            predicted_effect=(
                "Restart may change the workload state, but recovery "
                "cannot be determined from the available incident DNA."
            ),
            confidence=0.40,
            rationale=(
                "The incident does not contain a failure pattern "
                "strongly associated with restart recovery."
            ),
            supporting_factors=[],
        )

    @staticmethod
    def _predict_rollback(
        action: CounterfactualAction,
        dna: IncidentDNA,
    ) -> CounterfactualPrediction:
        failure = (dna.failure or "").lower()
        trigger = (dna.trigger or "").lower()

        configuration_related = any(
            term in failure or term in trigger
            for term in (
                "configuration",
                "config",
                "deployment",
                "release",
                "version",
            )
        )

        if configuration_related:
            return CounterfactualPrediction(
                action=action,
                predicted_status="likely_recovered",
                predicted_effect=(
                    "Rollback may restore a previously working "
                    "application configuration or version."
                ),
                confidence=0.80,
                rationale=(
                    "The incident characteristics indicate a "
                    "configuration or deployment-related failure."
                ),
                supporting_factors=[
                    "Configuration or deployment-related trigger detected",
                ],
            )

        return CounterfactualPrediction(
            action=action,
            predicted_status="uncertain",
            predicted_effect=(
                "Rollback may change the workload version, but its "
                "effect cannot be determined from the available DNA."
            ),
            confidence=0.40,
            rationale=(
                "No configuration or deployment-related failure "
                "pattern was identified."
            ),
            supporting_factors=[],
        )

    @staticmethod
    def _predict_scale(
        action: CounterfactualAction,
        dna: IncidentDNA,
    ) -> CounterfactualPrediction:
        failure = (dna.failure or "").lower()
        anomaly = str(dna.anomaly_information or {}).lower()

        resource_related = any(
            term in failure or term in anomaly
            for term in (
                "cpu",
                "memory",
                "resource",
                "capacity",
                "load",
            )
        )

        if resource_related:
            return CounterfactualPrediction(
                action=action,
                predicted_status="potentially_recovered",
                predicted_effect=(
                    "Scaling may distribute workload demand across "
                    "additional replicas."
                ),
                confidence=0.75,
                rationale=(
                    "The incident contains resource or capacity-related "
                    "signals for which additional replicas may help."
                ),
                supporting_factors=[
                    "Resource or capacity pressure detected",
                ],
            )

        return CounterfactualPrediction(
            action=action,
            predicted_status="uncertain",
            predicted_effect=(
                "Scaling changes replica capacity, but no clear "
                "scaling-related recovery signal was identified."
            ),
            confidence=0.40,
            rationale=(
                "The available incident DNA does not indicate that "
                "replica capacity is the primary failure mechanism."
            ),
            supporting_factors=[],
        )

    @staticmethod
    def _predict_memory_increase(
        action: CounterfactualAction,
        dna: IncidentDNA,
    ) -> CounterfactualPrediction:
        failure = (dna.failure or "").lower()

        if any(
            term in failure
            for term in (
                "oom",
                "oomkilled",
                "memory",
            )
        ):
            return CounterfactualPrediction(
                action=action,
                predicted_status="likely_recovered",
                predicted_effect=(
                    "Increasing the memory limit may prevent the "
                    "container from being killed by memory exhaustion."
                ),
                confidence=0.90,
                rationale=(
                    "The incident failure pattern directly indicates "
                    "memory exhaustion."
                ),
                supporting_factors=[
                    "Memory-related failure detected",
                    "OOMKilled pattern detected",
                ],
            )

        return CounterfactualPrediction(
            action=action,
            predicted_status="uncertain",
            predicted_effect=(
                "Increasing memory may not address the underlying "
                "failure mechanism."
            ),
            confidence=0.35,
            rationale=(
                "No memory-related failure pattern was identified."
            ),
            supporting_factors=[],
        )

    @staticmethod
    def _unknown_prediction(
        action: CounterfactualAction,
    ) -> CounterfactualPrediction:
        return CounterfactualPrediction(
            action=action,
            predicted_status="insufficient_information",
            predicted_effect=(
                "A reliable counterfactual outcome cannot be predicted "
                "without incident characteristics."
            ),
            confidence=0.10,
            rationale=(
                "Incident DNA is unavailable, so the prediction engine "
                "cannot evaluate the recovery action deterministically."
            ),
            supporting_factors=[],
        )