from pathlib import Path
import re
import pandas as pd

ROOT = Path("data/public")
OUTPUT = Path("data/rcaeval_case_features.csv")
WINDOW_SECONDS = 300

def fault_type(case_name):
    match = re.match(r"re1ob_.+?_(cpu|delay|disk|loss|mem)_\d+$", case_name)
    return match.group(1) if match else "unknown"

def summarize(series, prefix):
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {}
    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_max": float(values.max()),
        f"{prefix}_std": float(values.std()) if len(values) > 1 else 0.0,
    }

def main():
    records = []

    for folder in sorted(ROOT.glob("re1ob_*")):
        metrics_path = folder / "metrics.parquet"
        injection_path = folder / "inject_time.txt"

        if not metrics_path.exists() or not injection_path.exists():
            continue

        df = pd.read_parquet(metrics_path)
        injection = int(injection_path.read_text().strip())

        before = df[
            (df["time"] >= injection - WINDOW_SECONDS)
            & (df["time"] < injection)
        ]
        after = df[
            (df["time"] >= injection)
            & (df["time"] < injection + WINDOW_SECONDS)
        ]

        if before.empty or after.empty:
            print(f"SKIPPED {folder.name}: insufficient window data")
            continue

        record = {
            "case_id": folder.name,
            "fault_type": fault_type(folder.name),
            "injection_time": injection,
            "pre_rows": len(before),
            "post_rows": len(after),
        }

        metric_columns = [
            c for c in df.columns
            if c != "time"
            and any(token in c.lower() for token in (
                "cpu", "mem", "latency", "error", "load", "disk"
            ))
        ]

        for column in metric_columns:
            pre_stats = summarize(before[column], f"{column}_pre")
            post_stats = summarize(after[column], f"{column}_post")
            record.update(pre_stats)
            record.update(post_stats)

            pre_mean = pre_stats.get(f"{column}_pre_mean")
            post_mean = post_stats.get(f"{column}_post_mean")

            if pre_mean is not None and post_mean is not None:
                record[f"{column}_mean_delta"] = post_mean - pre_mean

        records.append(record)
        print(
            f"PROCESSED {folder.name}: "
            f"pre={len(before)}, post={len(after)}"
        )

    if not records:
        raise RuntimeError("No cases produced usable pre/post features.")

    result = pd.DataFrame(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print("\nFeature extraction complete.")
    print("Cases:", len(result))
    print("Feature columns:", len(result.columns))
    print("Fault types:", result["fault_type"].value_counts().to_dict())
    print("Output:", OUTPUT)

if __name__ == "__main__":
    main()
