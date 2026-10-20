import csv
import json
import random
from collections import Counter
from pathlib import Path

SEED = 20261020
RECORDS_PER_CATEGORY = 100
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

SCENARIOS = {
    "Scheduling": {
        "titles": [
            "FailedScheduling: insufficient CPU",
            "Pod Pending due to node capacity",
            "Pod scheduling constraint failure",
            "Insufficient memory on available nodes",
        ],
        "detector": "kubernetes-scheduler",
        "causes": [
            "Insufficient allocatable node resources",
            "Scheduling constraints prevent pod placement",
            "Node selector or affinity mismatch",
        ],
        "actions": [
            "Inspect node capacity and pod resource requests",
            "Review node affinity, selectors, and taints",
            "Evaluate safe capacity expansion",
        ],
    },
    "Resource": {
        "titles": [
            "Pod OOMKilled",
            "Container memory usage exceeded limit",
            "CPU throttling detected",
            "Repeated container restarts under resource pressure",
        ],
        "detector": "kubernetes-resource-monitor",
        "causes": [
            "Container memory limit exhaustion",
            "CPU resource contention or throttling",
            "Workload demand exceeds configured resource capacity",
        ],
        "actions": [
            "Inspect resource usage and recent workload changes",
            "Review memory limits and application memory behavior",
            "Evaluate resource requests and limits before changing them",
        ],
    },
    "Application": {
        "titles": [
            "CrashLoopBackOff detected",
            "Application exception spike",
            "Application process repeatedly exits",
            "Container startup failure",
        ],
        "detector": "application-health-monitor",
        "causes": [
            "Application process repeatedly fails during execution",
            "Unhandled application exception",
            "Startup or runtime failure",
        ],
        "actions": [
            "Inspect application logs and stack traces",
            "Compare the failure with the latest application release",
            "Validate startup configuration and health checks",
        ],
    },
    "Networking": {
        "titles": [
            "Network connection timeout",
            "DNS resolution failure",
            "Elevated network error rate",
            "Service connectivity failure",
        ],
        "detector": "network-observability",
        "causes": [
            "Network connectivity or routing failure",
            "DNS resolution problem",
            "Elevated connection failures between workloads",
        ],
        "actions": [
            "Inspect DNS, endpoints, and network policies",
            "Check connectivity from the affected workload",
            "Correlate network errors with service and node events",
        ],
    },
    "Dependency": {
        "titles": [
            "Upstream dependency timeout",
            "Downstream service unavailable",
            "Dependency latency spike",
            "External dependency failure",
        ],
        "detector": "dependency-monitor",
        "causes": [
            "Upstream dependency is slow or unavailable",
            "Downstream service failure affects the workload",
            "Dependency latency exceeds the expected threshold",
        ],
        "actions": [
            "Trace requests across the dependency chain",
            "Inspect dependency health and latency",
            "Review timeout and retry behavior before changing it",
        ],
    },
    "Configuration": {
        "titles": [
            "Configuration validation failure",
            "Invalid application config",
            "Missing required configuration",
            "Configuration mismatch detected",
        ],
        "detector": "configuration-monitor",
        "causes": [
            "Invalid or inconsistent workload configuration",
            "Required configuration value is missing",
            "Configuration differs from the expected deployment",
        ],
        "actions": [
            "Compare effective configuration with the known-good version",
            "Validate configuration keys and mounted settings",
            "Inspect recent configuration changes",
        ],
    },
    "Infrastructure": {
        "titles": [
            "Node disk pressure detected",
            "Infrastructure node failure",
            "Disk capacity exhaustion",
            "Node health degradation",
        ],
        "detector": "infrastructure-monitor",
        "causes": [
            "Node health or infrastructure failure",
            "Node disk capacity pressure",
            "Underlying infrastructure resource degradation",
        ],
        "actions": [
            "Inspect node conditions and infrastructure events",
            "Review disk consumption and container runtime storage",
            "Assess node health before considering workload rescheduling",
        ],
    },
    "Unknown": {
        "titles": [
            "Unclassified workload anomaly",
            "Unexpected service behavior",
            "Unrecognized incident signal",
            "Unclassified telemetry deviation",
        ],
        "detector": "generic-anomaly-monitor",
        "causes": [
            "Insufficient evidence to establish a root cause",
            "Unclassified anomaly requiring further investigation",
            "Available signals do not identify a specific failure",
        ],
        "actions": [
            "Collect additional logs, metrics, and event evidence",
            "Correlate the incident with recent workload changes",
            "Gather more evidence before selecting a remediation",
        ],
    },
}

FIELDS = [
    "incident_id",
    "data_source",
    "category",
    "title",
    "detector",
    "severity",
    "duration_seconds",
    "cpu_usage_pct",
    "memory_usage_pct",
    "restart_count",
    "pod_pending_minutes",
    "network_error_rate_pct",
    "dependency_latency_ms",
    "disk_usage_pct",
    "replica_count",
    "evidence",
    "root_cause",
    "suggested_remediation",
    "outcome_status",
    "outcome_verified",
    "split",
]


def bounded(value, low, high):
    return round(max(low, min(high, value)), 2)


def generate_record(rng, category, index):
    scenario = SCENARIOS[category]

    # Feature values are simulated telemetry, not real observations.
    cpu = bounded(rng.gauss(55, 18), 1, 100)
    memory = bounded(rng.gauss(58, 18), 1, 100)
    restarts = rng.choices(
        [0, 1, 2, 3, 5, 8],
        weights=[35, 20, 15, 12, 10, 8],
    )[0]
    pending = bounded(rng.expovariate(1 / 4), 0, 120)
    network_errors = bounded(rng.expovariate(1 / 2), 0, 100)
    dependency_latency = bounded(rng.gauss(180, 100), 5, 5000)
    disk = bounded(rng.gauss(55, 20), 1, 100)
    replicas = rng.randint(1, 12)
    duration = max(5, int(rng.lognormvariate(4, 1)))

    if category == "Scheduling":
        pending = bounded(rng.uniform(2, 120), 0, 120)
        cpu = bounded(rng.gauss(45, 15), 1, 100)
    elif category == "Resource":
        memory = bounded(rng.gauss(94, 5), 65, 100)
        cpu = bounded(rng.gauss(88, 9), 45, 100)
        restarts = rng.randint(1, 12)
    elif category == "Application":
        restarts = rng.randint(2, 15)
    elif category == "Networking":
        network_errors = bounded(rng.gauss(28, 15), 3, 100)
    elif category == "Dependency":
        dependency_latency = bounded(rng.gauss(1800, 700), 300, 5000)
    elif category == "Configuration":
        # Configuration errors need not produce extreme telemetry.
        cpu = bounded(rng.gauss(50, 20), 1, 100)
        memory = bounded(rng.gauss(55, 20), 1, 100)
    elif category == "Infrastructure":
        disk = bounded(rng.gauss(94, 5), 70, 100)
    elif category == "Unknown":
        # Intentionally overlapping feature distributions.
        cpu = bounded(rng.gauss(55, 25), 1, 100)
        memory = bounded(rng.gauss(58, 25), 1, 100)

    title = rng.choice(scenario["titles"])
    root_cause = rng.choice(scenario["causes"])
    remediation = rng.choice(scenario["actions"])

    evidence = (
        f"Simulated telemetry: CPU={cpu}%, memory={memory}%, "
        f"restarts={restarts}, pending_minutes={pending}, "
        f"network_error_rate={network_errors}%, "
        f"dependency_latency_ms={dependency_latency}, "
        f"disk_usage={disk}%."
    )

    # This is a synthetic suggestion, not an executed action.
    # No synthetic outcome is represented as verified.
    outcome_status = rng.choices(
        ["simulated_success", "simulated_unverified", "not_observed"],
        weights=[45, 35, 20],
        k=1,
    )[0]

    return {
        "incident_id": f"SYN-{category.upper()}-{index:04d}",
        "data_source": "synthetic",
        "category": category,
        "title": title,
        "detector": scenario["detector"],
        "severity": rng.choices(
            ["low", "medium", "high", "critical"],
            weights=[10, 35, 40, 15],
        )[0],
        "duration_seconds": duration,
        "cpu_usage_pct": cpu,
        "memory_usage_pct": memory,
        "restart_count": restarts,
        "pod_pending_minutes": pending,
        "network_error_rate_pct": network_errors,
        "dependency_latency_ms": dependency_latency,
        "disk_usage_pct": disk,
        "replica_count": replicas,
        "evidence": evidence,
        "root_cause": root_cause,
        "suggested_remediation": remediation,
        "outcome_status": outcome_status,
        "outcome_verified": False,
        "split": "",
    }


def main():
    rng = random.Random(SEED)
    records = []

    for category in SCENARIOS:
        category_records = [
            generate_record(rng, category, index)
            for index in range(1, RECORDS_PER_CATEGORY + 1)
        ]

        rng.shuffle(category_records)

        for index, record in enumerate(category_records):
            if index < 70:
                record["split"] = "train"
            elif index < 85:
                record["split"] = "validation"
            else:
                record["split"] = "test"

        records.extend(category_records)

    rng.shuffle(records)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = DATA_DIR / "synthetic_incidents.csv"
    jsonl_path = DATA_DIR / "synthetic_incidents.jsonl"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    with jsonl_path.open("w", encoding="utf-8") as file:
        for record in records:
            document = {
                "incident_id": record["incident_id"],
                "data_source": record["data_source"],
                "title": record["title"],
                "category": record["category"],
                "severity": record["severity"],
                "evidence": record["evidence"],
                "root_cause": record["root_cause"],
                "suggested_remediation": record["suggested_remediation"],
                "outcome_status": record["outcome_status"],
                "outcome_verified": record["outcome_verified"],
                "split": record["split"],
                "metadata": {
                    "synthetic": True,
                    "seed": SEED,
                },
            }
            file.write(json.dumps(document) + "\n")

    print(f"Generated records: {len(records)}")
    print(f"Categories: {dict(Counter(r['category'] for r in records))}")
    print(f"Splits: {dict(Counter(r['split'] for r in records))}")
    print(f"CSV: {csv_path}")
    print(f"JSONL: {jsonl_path}")
    print("Synthetic outcomes are not verified real-world outcomes.")


if __name__ == "__main__":
    main()

