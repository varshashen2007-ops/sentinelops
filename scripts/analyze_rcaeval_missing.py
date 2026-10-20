import pandas as pd

df = pd.read_csv("data/rcaeval_case_features.csv")
feature_cols = [
    c for c in df.columns
    if c not in {
        "case_id", "fault_type", "injection_time",
        "pre_rows", "post_rows"
    }
]

missing_pct = (df[feature_cols].isna().mean() * 100).sort_values(ascending=False)

print("Total numeric feature columns:", len(feature_cols))
print("Features complete across all cases:", int((missing_pct == 0).sum()))
print("Features missing in some cases:", int(((missing_pct > 0) & (missing_pct < 100)).sum()))
print("Features entirely missing:", int((missing_pct == 100).sum()))

print("\nMost frequently missing features:")
print(missing_pct.head(20).round(1).to_string())

print("\nMissing values by case:")
print(
    df.set_index("case_id")[feature_cols]
      .isna().sum(axis=1)
      .to_string()
)
