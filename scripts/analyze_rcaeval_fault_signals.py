from pathlib import Path
import pandas as pd

ROOT = Path("data/public")
OUTPUT = Path("data/rcaeval_robust_signals.csv")
WINDOW_SECONDS = 300

def main():
    records = []

    for folder in sorted(ROOT.glob("re1ob_*")):
        metrics_file = folder / "metrics.parquet"
        timestamp_file = folder / "inject_time.txt"

        if not metrics_file.exists() or not timestamp_file.exists():
            continue

        df = pd.read_parquet(metrics_file)
        injection = int(timestamp_file.read_text().strip())

        before = df[
            (df["time"] >= injection - WINDOW_SECONDS)
            & (df["time"] < injection)
        ]
        after = df[
            (df["time"] >= injection)
            & (df["time"] < injection + WINDOW_SECONDS)
        ]

        for column in df.columns:
            if column == "time" or not column.lower().startswith("adservice_"):
                continue

            pre = pd.to_numeric(before[column], errors="coerce").dropna()
            post = pd.to_numeric(after[column], errors="coerce").dropna()

            if pre.empty or post.empty:
                continue

            pre_median = float(pre.median())
            post_median = float(post.median())
            pre_mean = float(pre.mean())
            post_mean = float(post.mean())

            records.append({
                "case_id": folder.name,
                "fault_type": folder.name.rsplit("_", 2)[-2],
                "metric": column,
                "pre_median": pre_median,
                "post_median": post_median,
                "median_delta": post_median - pre_median,
                "pre_mean": pre_mean,
                "post_mean": post_mean,
                "mean_delta": post_mean - pre_mean,
                "pre_max": float(pre.max()),
                "post_max": float(post.max()),
                "pre_count": len(pre),
                "post_count": len(post),
            })

    result = pd.DataFrame(records)
    if result.empty:
        raise RuntimeError("No comparable metrics found.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print("Cases:", result["case_id"].nunique())
    print("Metric comparisons:", len(result))
    print("Saved:", OUTPUT)

    print("\nPer-case affected-workload metrics:")
    for case_id, group in result.groupby("case_id"):
        print(f"\n{case_id}")
        print(
            group[[
                "metric", "pre_median", "post_median",
                "median_delta", "pre_max", "post_max"
            ]].to_string(index=False, float_format=lambda x: f"{x:.5g}")
        )

if __name__ == "__main__":
    main()
