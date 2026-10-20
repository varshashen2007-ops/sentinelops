from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from incident_engine.dna import IncidentDNA
from models.incident import Incident, IncidentDiagnosis


class RCAEvalAdapter:
    """Convert RCAEval feature rows into searchable historical incidents."""

    def __init__(self, feature_csv: str | Path) -> None:
        self.feature_csv = Path(feature_csv)

    def load_incidents(self) -> list[Incident]:
        if not self.feature_csv.exists():
            raise FileNotFoundError(
                f"RCAEval feature file not found: {self.feature_csv}"
            )

        frame = pd.read_csv(self.feature_csv)
        required = {
            "case_id", "service", "fault_type", "injection_time"
        }
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"RCAEval feature file is missing columns: {sorted(missing)}"
            )

        incidents = []
        for _, row in frame.iterrows():
            telemetry = {}
            for column in frame.columns:
                if column in required or column in {"pre_rows", "post_rows"}:
                    continue
                value = pd.to_numeric(
                    pd.Series([row[column]]), errors="coerce"
                ).iloc[0]
                if pd.notna(value):
                    telemetry[column] = round(float(value), 6)

            timestamp = datetime.fromtimestamp(
                float(row["injection_time"]), tz=timezone.utc
            )
            searchable_signals = {
                key: value for key, value in telemetry.items()
                if key.endswith("_mean_delta")
            }
            summary = ", ".join(
                f"{key}={value}" for key, value in
                list(searchable_signals.items())[:30]
            ) or "No numeric telemetry deltas available"

            incident = Incident(
                incident_id=f"rcaeval:{row['case_id']}",
                started_at=timestamp,
                dna=IncidentDNA(
                    trigger=f"Observed telemetry around service {row['service']}",
                    failure="Telemetry change detected around injection time",
                    affected_workload=str(row["service"]),
                ),
                diagnosis=IncidentDiagnosis(
                    summary=(
                        f"Historical telemetry case for service "
                        f"{row['service']}. Observed signals: {summary}"
                    )
                ),
                metadata={
                    "source": "RCAEval",
                    "service": str(row["service"]),
                    "fault_type": str(row["fault_type"]),
                    "injection_time": int(row["injection_time"]),
                    "telemetry_features": telemetry,
                    "outcome_verified": False,
                },
            )
            incidents.append(incident)

        return incidents
