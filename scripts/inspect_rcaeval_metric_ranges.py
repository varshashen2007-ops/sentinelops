from pathlib import Path
import pandas as pd

for case in [
    "re1ob_adservice_cpu_1",
    "re1ob_adservice_delay_1",
    "re1ob_adservice_mem_1",
]:
    folder = Path("data/public") / case
    df = pd.read_parquet(folder / "metrics.parquet")
    injection = int((folder / "inject_time.txt").read_text().strip())

    print(f"\n{'=' * 65}\nCASE: {case}")
    print("Columns:", len(df.columns))

    for column in df.columns:
        if column == "time" or not column.lower().startswith("adservice_"):
            continue

        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            continue

        before = values[df.loc[values.index, "time"] < injection]
        after = values[df.loc[values.index, "time"] >= injection]

        print(
            f"{column}: min={values.min():.5g}, "
            f"median={values.median():.5g}, "
            f"max={values.max():.5g}, "
            f"pre_n={len(before)}, post_n={len(after)}"
        )
