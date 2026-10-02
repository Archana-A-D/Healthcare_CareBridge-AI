"""Compare lexical retrieval across chunk sizes using the synthetic 20-question set."""

import json
import os
import sys
import time
import argparse
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from api.views import chunks_for, retrieve


FIXTURE = [
    {"page": 1, "text": "Patient Rahul Kumar, ID IPD123456. Admission Date 12 Sep 2024. Hospital City Care Hospital."},
    {"page": 2, "text": "Discharge Date 20 Sep 2024. Diagnosis: Community Acquired Pneumonia; Hypertension. Amoxicillin 500 mg: 1 tablet twice daily for 5 days. Paracetamol 500 mg: 1 tablet as needed for 5 days. Pantoprazole 40 mg: 1 tablet once daily for 10 days."},
    {"page": 3, "text": "Follow-up 04 Oct 2024, General Medicine. Repeat chest X-ray. Blood test if symptoms persist. Return to hospital for fever, breathlessness or chest pain. Rest and avoid strenuous activity for 1 week. Allergy information not found in document."},
]

for _page in FIXTURE:
    # Repeated irrelevant text makes the fixed benchmark document long enough
    # that candidate chunk limits generate distinct chunk counts.
    _page["text"] += "\n\n" + " ".join(
        f"Administrative processing note {_i} contains no patient care information."
        for _i in range(1, 51)
    )


def percentile(values, p):
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, max(0, int(len(ordered) * p + .999999) - 1))], 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Also write the JSON report to this path.")
    options = parser.parse_args()
    questions = json.loads(Path(__file__).with_name("eval_questions.json").read_text(encoding="utf-8"))
    rows = []
    for size in (300, 500, 700, 1000, 1500):
        chunks = chunks_for(FIXTURE, limit=size)
        latencies = []
        relevant = retrieved = hits = 0
        for item in questions:
            started = time.perf_counter()
            found = retrieve(chunks, item["question"], limit=2)
            latencies.append((time.perf_counter() - started) * 1000)
            text = " ".join(chunk["text"].casefold() for chunk in found)
            expected = [term.casefold() for term in item["expected_terms"]]
            hits += bool(any(term in text for term in expected) and any(chunk["page"] == item["page"] for chunk in found))
            retrieved += len(found)
            relevant += sum(chunk["page"] == item["page"] and any(term in chunk["text"].casefold() for term in expected) for chunk in found)
        rows.append({
            "chunk_chars": size,
            "chunk_count": len(chunks),
            "hit_rate_at_2": round(hits / len(questions), 3),
            "evidence_precision_at_2": round(relevant / retrieved, 3) if retrieved else 0,
            "latency_ms": {"p50": percentile(latencies, .5), "p95": percentile(latencies, .95), "p99": percentile(latencies, .99)},
        })
    report = {
        "dataset": "three-page synthetic discharge summary; 20 fixed questions",
        "retriever": "Unicode lexical fallback",
        "metric_limit": "This microbenchmark informs chunk sizing for lexical retrieval only; it does not measure Gemini semantic retrieval or generated answer accuracy.",
        "results": rows,
    }
    print(json.dumps(report, indent=2))
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
