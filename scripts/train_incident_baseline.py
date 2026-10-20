import csv
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "synthetic_incidents.csv"
MODEL_PATH = ROOT / "data" / "incident_baseline.joblib"
METRICS_PATH = ROOT / "data" / "incident_baseline_metrics.json"

FEATURES = [
    "duration_seconds",
    "cpu_usage_pct",
    "memory_usage_pct",
    "restart_count",
    "pod_pending_minutes",
    "network_error_rate_pct",
    "dependency_latency_ms",
    "disk_usage_pct",
    "replica_count",
]


def main():
    with DATA_PATH.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    train = [r for r in rows if r["split"] == "train"]
    validation = [r for r in rows if r["split"] == "validation"]
    test = [r for r in rows if r["split"] == "test"]

    encoder = LabelEncoder()
    encoder.fit([r["category"] for r in train])

    def get_x(records):
        return np.asarray(
            [[float(r[name]) for name in FEATURES] for r in records],
            dtype=float,
        )

    def get_y(records):
        return encoder.transform([r["category"] for r in records])

    model = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced",
        random_state=20261020,
        min_samples_leaf=2,
        n_jobs=-1,
    )

    model.fit(get_x(train), get_y(train))

    validation_predictions = model.predict(get_x(validation))
    validation_accuracy = accuracy_score(
        get_y(validation), validation_predictions
    )
    validation_macro_f1 = f1_score(
        get_y(validation),
        validation_predictions,
        average="macro",
        zero_division=0,
    )

    test_predictions = model.predict(get_x(test))
    test_accuracy = accuracy_score(get_y(test), test_predictions)
    test_macro_f1 = f1_score(
        get_y(test),
        test_predictions,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        get_y(test),
        test_predictions,
        labels=np.arange(len(encoder.classes_)),
        target_names=encoder.classes_,
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "data_source": "synthetic",
        "warning": (
            "Synthetic benchmark only. Results do not establish "
            "real-world incident classification performance."
        ),
        "feature_names": FEATURES,
        "classes": encoder.classes_.tolist(),
        "sample_counts": {
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "validation": {
            "accuracy": float(validation_accuracy),
            "macro_f1": float(validation_macro_f1),
        },
        "test": {
            "accuracy": float(test_accuracy),
            "macro_f1": float(test_macro_f1),
            "classification_report": report,
            "confusion_matrix": confusion_matrix(
                get_y(test),
                test_predictions,
                labels=np.arange(len(encoder.classes_)),
            ).tolist(),
        },
        "feature_importances": dict(
            sorted(
                zip(FEATURES, model.feature_importances_.tolist()),
                key=lambda item: item[1],
                reverse=True,
            )
        ),
    }

    # Save model and encoder together for reproducible inference.
    import joblib

    joblib.dump(
        {"model": model, "label_encoder": encoder, "features": FEATURES},
        MODEL_PATH,
    )

    METRICS_PATH.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print("Train / validation / test:", len(train), len(validation), len(test))
    print(f"Validation accuracy: {validation_accuracy:.3f}")
    print(f"Validation macro-F1: {validation_macro_f1:.3f}")
    print(f"Test accuracy: {test_accuracy:.3f}")
    print(f"Test macro-F1: {test_macro_f1:.3f}")
    print("\nPer-class test metrics:")
    print(classification_report(
        get_y(test),
        test_predictions,
        labels=np.arange(len(encoder.classes_)),
        target_names=encoder.classes_,
        zero_division=0,
    ))
    print("Model:", MODEL_PATH)
    print("Metrics:", METRICS_PATH)
    print("Reminder: report these as synthetic-data results only.")


if __name__ == "__main__":
    main()
