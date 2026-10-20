import json
import urllib.request
from pathlib import Path

BASE_URL = "https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/main"
API_URL = "https://huggingface.co/api/datasets/phamquiluan/RCAEval/tree/main?recursive=true&expand=false"
OUTPUT_DIR = Path("data/public")
MAX_CASES = 10

def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SentinelOps-RCAEval-Downloader/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def download(url, destination):
    if destination.exists() and destination.stat().st_size > 0:
        print(f"EXISTS  {destination}")
        return True

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SentinelOps-RCAEval-Downloader/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
        if not data:
            print(f"EMPTY   {destination}")
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        print(f"DOWNLOADED {destination} ({len(data):,} bytes)")
        return True
    except Exception as exc:
        print(f"FAILED  {url}: {exc}")
        return False

def main():
    print("Fetching RCAEval case list...")
    entries = fetch_json(API_URL)
    cases = sorted(
        item["path"] for item in entries
        if item.get("type") == "directory"
        and item["path"].startswith("re1ob_")
    )

    if not cases:
        raise RuntimeError("No RCAEval case directories were found.")

    # Select different fault types and workloads where available.
    selected = []
    seen_types = set()
    for case in cases:
        parts = case.split("_")
        fault_type = parts[-2] if len(parts) >= 3 else "unknown"
        if fault_type not in seen_types:
            selected.append(case)
            seen_types.add(fault_type)
        if len(selected) >= MAX_CASES:
            break

    # Fill remaining slots if there are fewer distinct types.
    for case in cases:
        if len(selected) >= MAX_CASES:
            break
        if case not in selected:
            selected.append(case)

    print(f"Found {len(cases)} cases; selected {len(selected)}:")
    failures = []

    for index, case in enumerate(selected, start=1):
        print(f"\n[{index}/{len(selected)}] {case}")
        folder = OUTPUT_DIR / case
        for filename in ("metrics.parquet", "inject_time.txt"):
            url = f"{BASE_URL}/{case}/{filename}"
            destination = folder / filename
            if not download(url, destination):
                failures.append(f"{case}/{filename}")

    print("\nDownload summary")
    print("Selected cases:", len(selected))
    print("Failed files:", len(failures))
    if failures:
        print("\nFailures:")
        for item in failures:
            print("-", item)
    print("\nNote: time-series rows are not independent incident labels.")
    print("Use case-level splits for evaluation to avoid data leakage.")

if __name__ == "__main__":
    main()
