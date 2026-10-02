"""Offline retrieval evaluation on a fully synthetic fixture; makes no Gemini calls."""

import json
import os
import sys
import time
import argparse
import math
from pathlib import Path
import statistics
import uuid

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_backend_env():
    env_file = BACKEND / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


load_backend_env()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from api.views import chunks_for, retrieve


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini", action="store_true", help="Evaluate Gemini semantic embeddings (uses API quota).")
    parser.add_argument("--answers", action="store_true", help="Run all 20 questions through Gemini and score answers/citations (uses API quota).")
    parser.add_argument("--all-prompts", action="store_true", help="With --answers, run every registered prompt version (60 answer calls).")
    parser.add_argument("--output", type=Path, help="Also save the full JSON evaluation report to this path.")
    options = parser.parse_args()
    if options.all_prompts and not options.answers:
        parser.error("--all-prompts requires --answers")
    fixture = [
        {"page": 1, "text": "Patient Rahul Kumar, ID IPD123456. Admission Date 12 Sep 2024. Hospital City Care Hospital."},
        {"page": 2, "text": "Discharge Date 20 Sep 2024. Diagnosis: Community Acquired Pneumonia; Hypertension. Amoxicillin 500 mg: 1 tablet twice daily for 5 days. Paracetamol 500 mg: 1 tablet as needed for 5 days. Pantoprazole 40 mg: 1 tablet once daily for 10 days."},
        {"page": 3, "text": "Follow-up 04 Oct 2024, General Medicine. Repeat chest X-ray. Blood test if symptoms persist. Return to hospital for fever, breathlessness or chest pain. Rest and avoid strenuous activity for 1 week. Allergy information not found in document."},
    ]
    chunks = chunks_for(fixture)
    if options.gemini:
        from api.embeddings import embed_document_chunks, embed_query, rank_by_cosine

        if not embed_document_chunks(chunks, "eval-vector"):
            raise SystemExit("Could not embed the synthetic evaluation fixture.")
    questions = json.loads((Path(__file__).with_name("eval_questions.json")).read_text(encoding="utf-8"))
    latencies, passed, relevant_chunks, retrieved_chunks = [], 0, 0, 0
    for item in questions:
        started = time.perf_counter()
        if options.gemini:
            query_vector = embed_query(item["question"], "eval-vector")
            if not query_vector:
                raise SystemExit(f"Could not embed question {item['id']}.")
            result = rank_by_cosine(chunks, query_vector, limit=2)
        else:
            result = retrieve(chunks, item["question"])
        latencies.append((time.perf_counter() - started) * 1000)
        joined = " ".join(chunk["text"].casefold() for chunk in result)
        term_hit = any(term.casefold() in joined for term in item["expected_terms"])
        page_hit = any(chunk["page"] == item["page"] for chunk in result)
        passed += bool(term_hit and page_hit)
        retrieved_chunks += len(result)
        relevant_chunks += sum(
            chunk["page"] == item["page"]
            and any(term.casefold() in chunk["text"].casefold() for term in item["expected_terms"])
            for chunk in result
        )
    ordered = sorted(latencies)
    percentile = lambda values, p: round(sorted(values)[min(len(values) - 1, math.ceil(len(values) * p) - 1)], 3)
    report = {
        "dataset": "synthetic discharge summary fixture",
        "retriever": "Gemini semantic vectors + cosine" if options.gemini else "Unicode lexical fallback",
        "questions": len(questions),
        "top_k": 2,
        "retrieval_hit_rate": round(passed / len(questions), 3),
        "retrieval_recall": round(passed / len(questions), 3),
        "retrieval_precision": round(relevant_chunks / retrieved_chunks, 3) if retrieved_chunks else 0,
        "latency_ms": {"p50": percentile(ordered, 0.50), "p95": percentile(ordered, 0.95), "p99": percentile(ordered, 0.99)},
        "scope": "retrieval evidence/page hit only; not answer correctness or clinical validation",
    }
    if options.answers:
        if not os.getenv("GEMINI_API_KEY"):
            raise SystemExit("Set GEMINI_API_KEY before running answer evaluation; this mode uses Gemini quota.")
        from api.agent_service import answer_document_question
        from api.models import DischargeDocument, LLMUsageLog, MedicationMention
        from api.prompt_registry import PROMPT_VERSIONS
        from django.db.models import Sum

        document = DischargeDocument.objects.create(
            filename="synthetic-evaluation-fixture.pdf",
            text="\n\n".join(f"[Page {part['page']}] {part['text']}" for part in fixture),
            chunks=chunks,
            summary={"followUp": {"tests": ["Repeat chest X-ray", "Blood test if symptoms persist"]}},
        )
        for name, instructions, duration, timing, page in (
            ("Amoxicillin 500 mg", "1 tablet twice daily", "5 days", "Morning and night", 2),
            ("Paracetamol 500 mg", "1 tablet as needed", "5 days", "As needed", 2),
            ("Pantoprazole 40 mg", "1 tablet once daily", "10 days", "Morning", 2),
        ):
            MedicationMention.objects.create(
                document=document, name=name, instructions=instructions,
                duration=duration, timing=timing, source_page=page,
            )

        versions = list(PROMPT_VERSIONS) if options.all_prompts else [os.getenv("CAREBRIDGE_PROMPT_VERSION", "v3")]
        version_reports = {}

        def save_progress():
            if options.output:
                report["prompt_version_evaluation"] = version_reports
                options.output.parent.mkdir(parents=True, exist_ok=True)
                temporary = options.output.with_suffix(options.output.suffix + ".tmp")
                temporary.write_text(json.dumps(report, indent=2), encoding="utf-8")
                temporary.replace(options.output)

        try:
            for version in versions:
                os.environ["CAREBRIDGE_PROMPT_VERSION"] = version
                results, answer_latencies, costs, input_token_counts, output_token_counts, ragas_samples, unpriced = [], [], [], [], [], [], 0
                for item in questions:
                    correlation_id = f"eval-{version}-{item['id']}-{uuid.uuid4().hex[:8]}"
                    started = time.perf_counter()
                    for attempt in range(3):
                        try:
                            answer = answer_document_question(
                                document.id, item["question"], "en", correlation_id=correlation_id,
                            )
                            break
                        except RuntimeError as exc:
                            message = str(exc)
                            transient = any(
                                marker in message
                                for marker in (
                                    "Gemini API error (429)", "Gemini API error (500)",
                                    "Gemini API error (502)", "Gemini API error (503)",
                                    "Gemini API error (504)", "Gemini connection failed",
                                )
                            )
                            if not transient or attempt == 2:
                                raise
                            time.sleep(2 ** (attempt + 1))
                    answer_latencies.append((time.perf_counter() - started) * 1000)
                    answer_text = answer["answer"].casefold()
                    answer_correct = all(term.casefold() in answer_text for term in item["expected_terms"])
                    citation_correct = item["page"] in answer["retrievedPages"] and any(
                        citation["page"] == item["page"] for citation in answer["sources"]
                    )
                    results.append((answer_correct, citation_correct))
                    contexts = [chunk["text"] for chunk in chunks if chunk["page"] in answer["retrievedPages"]]
                    ragas_samples.append({
                        "question": item["question"],
                        "answer": answer["answer"],
                        "contexts": contexts,
                        "reference": "; ".join(item["expected_terms"]),
                    })
                    usage = LLMUsageLog.objects.filter(correlation_id=correlation_id)
                    token_totals = usage.aggregate(input_tokens=Sum("input_tokens"), output_tokens=Sum("output_tokens"))
                    input_token_counts.append(token_totals["input_tokens"] or 0)
                    output_token_counts.append(token_totals["output_tokens"] or 0)
                    # A run with any unpriced model call cannot claim a complete per-query cost.
                    usage_rows = list(usage.values_list("estimated_cost_usd", flat=True))
                    if not usage_rows or any(value is None for value in usage_rows):
                        unpriced += 1
                    else:
                        costs.append(sum(float(value) for value in usage_rows))
                    version_reports[version] = {
                        "status": "running",
                        "questions_completed": len(results),
                        "ragas_samples": ragas_samples,
                    }
                    save_progress()
                version_reports[version] = {
                    "questions": len(results),
                    "answer_correctness_rate": round(sum(correct for correct, _ in results) / len(results), 3),
                    "citation_correctness_rate": round(sum(correct for _, correct in results) / len(results), 3),
                    "joint_correctness_rate": round(sum(a and c for a, c in results) / len(results), 3),
                    "latency_ms": {
                        "p50": percentile(answer_latencies, 0.50),
                        "p95": percentile(answer_latencies, 0.95),
                        "p99": percentile(answer_latencies, 0.99),
                    },
                    "mean_tokens_per_question": {
                        "input": round(statistics.mean(input_token_counts)),
                        "output": round(statistics.mean(output_token_counts)),
                    },
                    "mean_cost_usd_per_question": round(statistics.mean(costs), 8) if len(costs) == len(results) else None,
                    "unpriced_questions": unpriced,
                    "scoring": "answer requires every expected term as a substring; citation requires the known page in retrieved pages and model citations",
                    "ragas_samples": ragas_samples,
                    "status": "complete",
                }
                save_progress()
        finally:
            document.delete()
        report["prompt_version_evaluation"] = version_reports
        report["scope"] += "; synthetic answer/citation checks are heuristic and not clinical validation"
    print(json.dumps(report, indent=2))
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    run()
