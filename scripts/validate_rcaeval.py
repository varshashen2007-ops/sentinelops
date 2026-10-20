from pathlib import Path
import pandas as pd

root = Path("data/public")
cases = sorted(p for p in root.glob("re1ob_*") if p.is_dir())

total_rows = 0
issues = []
invalid_injection_timestamps = {
    "re1ob_currencyservice_loss_1": (
        "Source timestamp is malformed and outside telemetry range"
    )
}

print(f"Cases found: {len(cases)}\n")

for case in cases:
    metrics_file = case / "metrics.parquet"
    timestamp_file = case / "inject_time.txt"

    try:
        if not metrics_file.exists() or not timestamp_file.exists():
            raise FileNotFoundError("Required file is missing")

        df = pd.read_parquet(metrics_file)
        injection_time = int(timestamp_file.read_text().strip())

        if "time" not in df.columns or df.empty:
            raise ValueError("Missing time column or empty telemetry")

        total_rows += len(df)
        in_range = df["time"].min() <= injection_time <= df["time"].max()

        if case.name in invalid_injection_timestamps:
            status = "INVALID_INJECTION_TIMESTAMP"
            print(
                f"{case.name}: rows={len(df)}, "
                f"columns={len(df.columns)}, status={status}"
            )
            print(f"  Reason: {invalid_injection_timestamps[case.name]}")
            continue

        status = "VALID" if in_range else "OUT_OF_RANGE"
        print(
            f"{case.name}: rows={len(df)}, "
            f"columns={len(df.columns)}, status={status}"
        )

        if not in_range:
            issues.append(case.name)

    except Exception as exc:
        issues.append(case.name)
        print(f"{case.name}: ERROR - {exc}")

print(f"\nTotal time-series rows: {total_rows}")
print(f"Other validation issues: {issues}")
print(
    "Cases excluded from before/after analysis:",
    list(invalid_injection_timestamps),
)
