from counterfactual.engine import CounterfactualEngine
from counterfactual.model import (
    CounterfactualAction,
    CounterfactualPrediction,
    CounterfactualScenario,
)
from incident_engine.dna import IncidentDNA
from models.incident import Incident


class CounterfactualSimulator:
    """
    Evaluates multiple hypothetical recovery actions for an incident.

    The simulator performs no real Kubernetes mutations. It only
    generates deterministic predictions for the supplied actions.
    """

    def __init__(
        self,
        engine: CounterfactualEngine | None = None,
    ) -> None:
        self.engine = engine or CounterfactualEngine()

    def simulate(
        self,
        incident: Incident,
        actions: list[CounterfactualAction],
    ) -> CounterfactualScenario:
        predictions: list[CounterfactualPrediction] = []

        for action in actions:
            prediction = self.engine.predict(
                action=action,
                dna=incident.dna,
            )

            predictions.append(prediction)

        return CounterfactualScenario(
            incident_id=incident.incident_id,
            actions=list(actions),
            predictions=predictions,
            metadata={
                "simulation_type": "deterministic",
                "execution": "not_executed",
            },
        )