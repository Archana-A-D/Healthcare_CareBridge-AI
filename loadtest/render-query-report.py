"""Render a small HTML comparison of Locust query and Redis profiles."""

import argparse
import csv
from html import escape
from pathlib import Path


OPERATIONS = (
    ("Document query end-to-end", "AGENT"),
    ("POST /api/agent/jobs/ [Gemini]", "HTTP"),
    ("Redis SET/GET", "REDIS"),
)


def load(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = {row.get("Name"): row for row in csv.DictReader(handle)}
    result = {}
    for name, kind in OPERATIONS:
        row = rows.get(name)
        if row:
            result[name] = {
                "kind": kind,
                "count": int(row["Request Count"]),
                "failures": int(row["Failure Count"]),
                "p95": float(row["95%"]),
            }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("three_user_stats", type=Path)
    parser.add_argument("ten_user_stats", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profiles = (("3 concurrent users", load(args.three_user_stats)), ("10 concurrent users", load(args.ten_user_stats)))
    all_values = [item["p95"] for _, profile in profiles for item in profile.values()]
    max_value = max(all_values, default=1) or 1
    rows, bars = [], []
    y = 50
    colors = {"AGENT": "#c24b32", "HTTP": "#2868c7", "REDIS": "#29805c"}
    for profile_name, profile in profiles:
        rows.append(f'<h2>{escape(profile_name)}</h2><table><tr><th>Operation</th><th>Requests</th><th>Failures</th><th>p95</th></tr>')
        for name, _ in OPERATIONS:
            item = profile.get(name)
            if not item:
                continue
            rows.append(
                f'<tr><td>{escape(name)}</td><td>{item["count"]}</td><td>{item["failures"]}</td>'
                f'<td>{item["p95"]:.0f} ms</td></tr>'
            )
            width = 700 * item["p95"] / max_value
            label = f'{profile_name}: {name} ({item["p95"]:.0f} ms)'
            bars.append(
                f'<text x="8" y="{y+14}">{escape(label)}</text>'
                f'<rect x="310" y="{y}" width="{width:.1f}" height="20" fill="{colors[item["kind"]]}"/>'
            )
            y += 35
        rows.append("</table>")
    svg = f'<svg viewBox="0 0 1040 {y+20}" role="img" aria-label="p95 latency bars">{"".join(bars)}</svg>'
    html = (
        '<!doctype html><meta charset="utf-8"><title>CareBridge query load profiles</title>'
        '<style>body{font:15px Arial,sans-serif;color:#24324a;max-width:1120px;margin:32px auto} '
        'table{border-collapse:collapse;margin:12px 0 24px}th,td{border:1px solid #ccd4df;padding:7px 12px;text-align:left} '
        'svg{width:100%;height:auto;font:12px Arial,sans-serif}</style>'
        '<h1>Concurrent document query profiles</h1>' + svg + "".join(rows)
        + '<p>End-to-end bars include Gemini processing and job polling. Submission bars show enqueue latency. '
        'The profiles are local synthetic-data measurements, not a capacity guarantee.</p>'
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
