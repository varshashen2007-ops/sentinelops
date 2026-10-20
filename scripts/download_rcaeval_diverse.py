import argparse
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

API_URL = (
    "https://huggingface.co/api/datasets/phamquiluan/"
    "RCAEval/tree/main?recursive=true&expand=false"
)
BASE_URL = "https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/main"
OUTPUT_DIR = Path("data/public")
MAX_CASES = 125

def fetch_json(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "SentinelOps-RCAEval/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def parse_case(path):
    name = path.rsplit("/", 1)[-1]
    match = re.fullmatch(r"re1ob_(.+)_([a-z]+)_(\d+)", name)
    if not match:
        return None
    service, fault, repeat = match.groups()
    return {"name": name, "service": service, "fault": fault}

def choose_cases(cases, limit):
    groups = defaultdict(list)
    for case in cases:
        groups[(case["service"], case["fault"])].append(case)

    for group in groups.values():
        group.sort(key=lambda case: case["name"])

    selected = []
    used = set()

    # First pass: prefer different services and fault types.
    services = sorted({case["service"] for case in cases})
    faults = sorted({case["fault"] for case in cases})

    while len(selected) < limit:
        added_this_round = False
        for fault in faults:
            for service in services:
                key = (service, fault)
                group = groups.get(key, [])
                candidate = next(
                    (item for item in group if item["name"] not in used),
                    None,
                )
                if candidate is not None:
                    selected.append(candidate)
                    used.add(candidate["name"])
                    added_this_round = True
                    if len(selected) >= limit:
                        break
            if len(selected) >= limit:
                break
        if not added_this_round:
            break

    return selected

def download(url, destination):
    if destination.exists() and destination.stat().st_size > 0:
        print(f"EXISTS     {destination}")
        return True

    request = urllib.request.Request(
        url, headers={"User-Agent": "SentinelOps-RCAEval/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            content = response.read()
        if not content:
            print(f"EMPTY      {destination}")
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        print(f"DOWNLOADED {destination} ({len(content):,} bytes)")
        return True
    except Exception as exc:
        print(f"FAILED     {destination}: {exc}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the selected cases; otherwise preview only.",
    )
    args = parser.parse_args()

    print("Fetching RCAEval case list...")
    entries = fetch_json(API_URL)
    cases = []
    for entry in entries:
        if entry.get("type") != "directory":
            continue
        if not entry.get("path", "").startswith("re1ob_"):
            continue
        parsed = parse_case(entry["path"])
        if parsed:
            cases.append(parsed)

    if not cases:
        raise RuntimeError("No cases matched the expected naming pattern.")

    selected = choose_cases(cases, MAX_CASES)
    print(f"\nAvailable cases: {len(cases)}")
    print(f"Selected cases:  {len(selected)}")
    print(f"Available services: {len(set(c['service'] for c in cases))}")
    print("Available fault types:", dict(Counter(c["fault"] for c in cases)))
    print("\nProposed selection:")
    for case in selected:
        print(f"  {case['name']}")

    print("\nSelected service counts:",
          dict(Counter(c["service"] for c in selected)))
    print("Selected fault counts:",
          dict(Counter(c["fault"] for c in selected)))

    if not args.download:
        print("\nPREVIEW ONLY: no files downloaded.")
        print("Review this list before running with --download.")
        return

    failures = []
    for index, case in enumerate(selected, 1):
        print(f"\n[{index}/{len(selected)}] {case['name']}")
        folder = OUTPUT_DIR / case["name"]
        for filename in ("metrics.parquet", "inject_time.txt"):
            url = f"{BASE_URL}/{case['name']}/{filename}"
            if not download(url, folder / filename):
                failures.append(f"{case['name']}/{filename}")

    print(f"\nDownload complete. Cases selected: {len(selected)}")
    print(f"Failed files: {len(failures)}")
    for failure in failures:
        print(" -", failure)
    print("Keep evaluation splits at the case level, not the row level.")

if __name__ == "__main__":
    main()

