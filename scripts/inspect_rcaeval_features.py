import pandas as pd

path = "data/rcaeval_case_features.csv"
df = pd.read_csv(path)

print("Shape:", df.shape)
print("Unique cases:", df["case_id"].nunique())
print("\nFault-type counts:")
print(df["fault_type"].value_counts().to_string())

print("\nDuplicate column names:", df.columns.duplicated().sum())
print("Duplicate case IDs:", df["case_id"].duplicated().sum())
print("Columns with all values missing:", int(df.isna().all().sum()))
print("Total missing feature values:", int(df.isna().sum().sum()))

print("\nSample feature columns:")
print(df.columns[:20].tolist())

print("\nCase-level feature preview:")
print(df[["case_id", "fault_type", "pre_rows", "post_rows"]].to_string(index=False))
