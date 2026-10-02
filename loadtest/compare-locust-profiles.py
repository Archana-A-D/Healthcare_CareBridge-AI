"""Compare same-profile Locust CSVs and enforce a 30% p95 reduction."""

import argparse
import csv
import json
from pathlib import Path


def load(path, operation):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    row = next((item for item in rows if item.get("Name") == operation), None)
    if row is None:
        raise SystemExit(f"{operation!r} is absent from {path}")
    return {
        "request_count": int(row["Request Count"]),
        "failures": int(row["Failure Count"]),
        "p95_ms": float(row["95%"]),
        "requests_per_second": float(row["Requests/s"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--operation", default="GET /api/agent/usage/")
    parser.add_argument("--before-profile", type=Path, required=True, help="JSON sidecar with workload and environment metadata")
    parser.add_argument("--after-profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("loadtest/results/comparison.json"))
    args = parser.parse_args()
    before_profile = json.loads(args.before_profile.read_text(encoding="utf-8-sig"))
    after_profile = json.loads(args.after_profile.read_text(encoding="utf-8-sig"))
    required = {"users", "duration", "spawn_rate", "ai_mode", "ai_model", "prompt_version", "environment", "data_sha256", "warmup_requests"}
    if not required.issubset(before_profile) or not required.issubset(after_profile):
        raise SystemExit(f"Each profile sidecar must include: {', '.join(sorted(required))}")
    if any(before_profile[key] != after_profile[key] for key in required):
        raise SystemExit("Profiles differ. Match concurrency, duration, ramp, model/prompt, environment, dataset, and warm-up.")
    before, after = load(args.before, args.operation), load(args.after, args.operation)
    reduction = (before["p95_ms"] - after["p95_ms"]) / before["p95_ms"] if before["p95_ms"] else 0
    report = {
        "operation": args.operation,
        "profile": {key: before_profile[key] for key in sorted(required)},
        "before": before,
        "after": after,
        "p95_reduction_percent": round(reduction * 100, 2),
        "target_reduction_percent": 30,
        "target_met": reduction >= 0.30,
        "limits": "Compare only when host, stack, data, AI mode, and warm-up also match.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["target_met"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
