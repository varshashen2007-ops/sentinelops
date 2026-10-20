from pathlib import Path

path = Path("diagnosis/engine.py")
source = path.read_text(encoding="utf-8")

old = '''        explanation = self._build_explanation(
            classification=classification,
            historical_incident_ids=historical_incident_ids,
        )
'''

new = '''        explanation = self._build_explanation(
            classification=classification,
            historical_incident_ids=historical_incident_ids,
        )
        explanation += self._build_telemetry_explanation(incident)
'''

if old not in source:
    raise SystemExit(
        "Expected explanation block not found. No changes made."
    )

if "explanation += self._build_telemetry_explanation(incident)" in source:
    raise SystemExit(
        "Telemetry explanation is already connected. No changes made."
    )

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Connected telemetry explanation to DiagnosisEngine.")
