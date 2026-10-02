"""Create a self-contained SVG latency/error graph from Locust CSV output."""

import argparse
import csv
from html import escape
from pathlib import Path


WIDTH, HEIGHT = 960, 600
LEFT, RIGHT = 76, 930


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def polyline(points, x, y, color):
    values = " ".join(f"{x(a):.1f},{y(b):.1f}" for a, b in points)
    return f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{values}" />'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stats", type=Path, help="Locust _stats.csv")
    parser.add_argument("history", type=Path, help="Locust _stats_history.csv")
    parser.add_argument("--output", type=Path, required=True, help="SVG report path")
    args = parser.parse_args()
    rows = read_csv(args.stats)
    history = [row for row in read_csv(args.history) if row.get("Type") == "" and row.get("Name") == "Aggregated"]
    samples = []
    for index, row in enumerate(history):
        p95, failures = number(row.get("95%")), number(row.get("Total Failure Count"))
        if p95 is not None:
            samples.append((index, p95, failures or 0))
    if not samples:
        raise SystemExit("No completed aggregate p95 samples found in the Locust history CSV.")
    p95max = max(1, max(point[1] for point in samples))
    failuremax = max(1, max(point[2] for point in samples))
    x = lambda index: LEFT + index * (RIGHT - LEFT) / max(1, len(samples) - 1)
    y1 = lambda value: 250 - value * 190 / p95max
    y2 = lambda value: 515 - value * 190 / failuremax
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font:14px Arial,sans-serif;fill:#24324a}.grid{stroke:#d8deea;stroke-width:1}.axis{stroke:#50617c}</style>',
           '<text x="76" y="28" font-size="19" font-weight="bold">Locust latency and errors over the run</text>',
           '<text x="76" y="54">p95 latency (ms)</text>']
    for tick in range(5):
        val = p95max * tick / 4
        yy = y1(val)
        svg.append(f'<line class="grid" x1="{LEFT}" x2="{RIGHT}" y1="{yy}" y2="{yy}"/><text x="20" y="{yy+5}">{val:.0f}</text>')
    svg.append(polyline([(i, p) for i, p, _ in samples], x, y1, "#2868c7"))
    svg.append('<text x="76" y="294">Cumulative failed requests</text>')
    for tick in range(5):
        val = failuremax * tick / 4
        yy = y2(val)
        svg.append(f'<line class="grid" x1="{LEFT}" x2="{RIGHT}" y1="{yy}" y2="{yy}"/><text x="32" y="{yy+5}">{val:.0f}</text>')
    svg.append(polyline([(i, f) for i, _, f in samples], x, y2, "#d64a4a"))
    svg.extend([f'<line class="axis" x1="{LEFT}" x2="{RIGHT}" y1="250" y2="250"/>',
                f'<line class="axis" x1="{LEFT}" x2="{RIGHT}" y1="515" y2="515"/>',
                f'<text x="{LEFT}" y="550">Start</text>',
                f'<text x="{RIGHT-35}" y="550">End</text>',
                '<line x1="76" y1="580" x2="102" y2="580" stroke="#2868c7" stroke-width="3"/><text x="110" y="585">Aggregate p95</text>',
                '<line x1="280" y1="580" x2="306" y2="580" stroke="#d64a4a" stroke-width="3"/><text x="314" y="585">Cumulative failures</text>',
                '</svg>'])
    summary = "\n".join(
        f"<tr><td>{escape(row.get('Type') or 'HTTP')}</td><td>{escape(row.get('Name',''))}</td>"
        f"<td>{escape(row.get('Request Count',''))}</td><td>{escape(row.get('Failure Count',''))}</td>"
        f"<td>{escape(row.get('95%',''))}</td></tr>"
        for row in rows if row.get("Name") and row.get("Name") != "Aggregated"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        '<!doctype html><meta charset="utf-8"><title>Locust report</title>'
        '<h1>Locust latency and failure report</h1>' + "".join(svg)
        + '<h2>Operations</h2><table border="1" cellpadding="6"><tr><th>Type</th><th>Operation</th><th>Requests</th><th>Failures</th><th>p95 ms</th></tr>'
        + summary + '</table>', encoding="utf-8",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
