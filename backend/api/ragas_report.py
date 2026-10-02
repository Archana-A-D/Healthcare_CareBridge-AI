"""Score saved answer runs with Ragas; all external model calls are opt-in."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import statistics
import time
from collections import deque


def load_backend_env():
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path, help="JSON created by eval_harness.py --answers --all-prompts --output ...")
    parser.add_argument("--output", type=Path, default=Path("evaluation/ragas-report.json"))
    parser.add_argument("--version", choices=("v1", "v2", "v3"), help="Score one prompt version; default scores all present versions.")
    parser.add_argument("--resume", action="store_true", help="Resume from score arrays saved in the existing output checkpoint.")
    parser.add_argument("--requests-per-minute", type=int, default=10, help="Limit scoring calls per minute to respect provider quotas (1-15).")
    args = parser.parse_args()
    if not 1 <= args.requests_per_minute <= 15:
        parser.error("--requests-per-minute must be between 1 and 15")
    load_backend_env()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Set GEMINI_API_KEY; Ragas invokes Gemini as an evaluator and may incur API usage/cost.")
    payload = json.loads(args.samples.read_text(encoding="utf-8"))
    versions = payload.get("prompt_version_evaluation", {})
    if args.version:
        versions = {args.version: versions[args.version]} if args.version in versions else {}
    if not versions:
        raise SystemExit("No prompt-version samples found. First create an answer artifact with eval_harness.py --answers --all-prompts --output.")
    existing = {}
    if args.resume and args.output.is_file():
        existing = json.loads(args.output.read_text(encoding="utf-8")).get("prompt_versions", {})

    async def evaluate():
        from google import genai
        from openai import AsyncOpenAI
        from ragas.embeddings import GoogleEmbeddings
        from ragas.llms import llm_factory
        from ragas.metrics.collections import AnswerCorrectness, ContextPrecision, ContextRecall, Faithfulness

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        model = os.getenv("RAGAS_EVAL_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
        llm_client = AsyncOpenAI(
            api_key=os.environ["GEMINI_API_KEY"],
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        llm = llm_factory(model, provider="openai", client=llm_client)
        embeddings = GoogleEmbeddings(client=client, model=os.getenv("RAGAS_EMBEDDING_MODEL", "gemini-embedding-001"))
        metrics = {
            "faithfulness": Faithfulness(llm=llm),
            "context_precision": ContextPrecision(llm=llm),
            "context_recall": ContextRecall(llm=llm),
            "answer_correctness": AnswerCorrectness(llm=llm, embeddings=embeddings),
        }
        result = {
            "dataset": "synthetic 20-question discharge-summary set",
            "model": model,
            "scores_are_clinical_validation": False,
            "empty_context_policy": "faithfulness, context precision, and context recall score 0 when retrieval returns no contexts; answer correctness is still evaluated",
            "requests_per_minute_limit": args.requests_per_minute,
            "prompt_versions": existing.copy(),
        }

        request_times = deque()

        async def pace_metric_call():
            while True:
                now = time.monotonic()
                while request_times and now - request_times[0] >= 60:
                    request_times.popleft()
                if len(request_times) < args.requests_per_minute:
                    request_times.append(now)
                    return
                await asyncio.sleep(max(0.05, 60 - (now - request_times[0])) + 0.1)

        for version, version_data in versions.items():
            previous = existing.get(version, {}) if args.resume else {}
            if previous.get("status") == "complete":
                continue
            rows = {key: list(previous.get("raw_scores", {}).get(key, [])) for key in metrics}
            samples = version_data.get("ragas_samples", [])
            if len(samples) != 20:
                raise SystemExit(f"{version} has {len(samples)} samples; expected 20.")
            for sample_index, row in enumerate(samples):
                for key, metric in metrics.items():
                    if len(rows[key]) > sample_index:
                        continue
                    # No retrieved context is a real retrieval failure, not a malformed sample.
                    # Score grounding/retrieval metrics as zero and still score answer correctness.
                    if not row.get("contexts") and key in {"faithfulness", "context_precision", "context_recall"}:
                        rows[key].append(0.0)
                        result["prompt_versions"][version] = {
                            name: round(statistics.mean(values), 4)
                            for name, values in rows.items() if values
                        } | {
                            "questions_completed": min((len(values) for values in rows.values()), default=0),
                            "raw_scores": rows,
                            "status": "running",
                        }
                        checkpoint(args.output, result)
                        continue
                    for attempt in range(3):
                        try:
                            await pace_metric_call()
                            values = {
                                "user_input": row["question"],
                                "response": row["answer"],
                                "retrieved_contexts": row["contexts"],
                                "reference": row["reference"],
                            }
                            metric_fields = {
                                "faithfulness": ("user_input", "response", "retrieved_contexts"),
                                "context_precision": ("user_input", "reference", "retrieved_contexts"),
                                "context_recall": ("user_input", "retrieved_contexts", "reference"),
                                "answer_correctness": ("user_input", "response", "reference"),
                            }
                            inputs = {field: values[field] for field in metric_fields[key]}
                            score = await metric.ascore(**inputs)
                            break
                        except Exception as exc:
                            message = str(exc)
                            transient = any(
                                marker in message
                                for marker in (
                                    "429", "500", "502", "503", "504",
                                    "ResourceExhausted", "UNAVAILABLE", "deadline exceeded",
                                )
                            )
                            if not transient or attempt == 2:
                                raise
                            await asyncio.sleep(2 ** (attempt + 1))
                    rows[key].append(float(score.value))
                    result["prompt_versions"][version] = {
                        key: round(statistics.mean(values), 4) for key, values in rows.items() if values
                    } | {
                        "questions_completed": min((len(values) for values in rows.values()), default=0),
                        "raw_scores": rows,
                        "status": "running",
                    }
                    checkpoint(args.output, result)
            result["prompt_versions"][version] = {
                key: round(statistics.mean(values), 4) for key, values in rows.items()
            } | {"questions": len(samples), "raw_scores": rows, "status": "complete"}
            checkpoint(args.output, result)
        return result

    report = asyncio.run(evaluate())
    checkpoint(args.output, report)
    print(json.dumps(report, indent=2))


def checkpoint(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":
    main()
