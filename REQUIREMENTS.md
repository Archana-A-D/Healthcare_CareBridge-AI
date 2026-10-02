# Hackathon requirement check

Checked against the 4-Week Curriculum syllabus, Healthcare Track brief, and supplied load-test template.

## Syllabus acceptance criteria

The syllabus adds measurable acceptance criteria beyond the hackathon feature checklist. Code that supports a criterion is not proof that the target was achieved; benchmark and evaluation results are required.

| Syllabus criterion | Current status | Evidence / remaining work |
| --- | --- | --- |
| RAG answer accuracy at least 80% over 20 questions; retrieval accuracy at least 80% | Heuristic thresholds met on synthetic fixture; formal Ragas scoring incomplete | Lexical retrieval measured 1.00 page recall and 0.80 evidence precision on 20 questions. Gemini answer/citation checks scored v1 0.90/0.95, v2 0.80/0.95, and v3 0.90/0.95 over 20 questions/version. Ragas currently has a partial v1 report (17/20); v2/v3 are still running. None of these synthetic results is clinical validation. |
| Chunk size supported by benchmark data | Partially met | `backend/api/chunk_benchmark.py` compares five chunk limits on 20 questions. A local synthetic lexical run supports 1000 characters provisionally; semantic retrieval and actual PDFs still need benchmark coverage. |
| Three concurrent requests without degradation; P95 query latency at most 300 ms | Measured; latency target not met | The live synthetic-document profile completed 3/3 queries at 3 users and 10/10 at 10 users with zero Locust failures. End-to-end query p95 was 3.5 s and 6.1 s; async submission p95 was 490 ms and 540 ms. See [`loadtest/live-query-profile-report.md`](loadtest/live-query-profile-report.md). |
| At least 30% latency improvement with before/after measurements | Redis query-embedding cache added; numerical target unproven | `embed_query` now caches normalized vectors by model/question in Redis. [`loadtest/compare-locust-profiles.py`](loadtest/compare-locust-profiles.py) validates matched environment, data, ramp, AI mode, and duration metadata and checks p95 reduction. Matched before/after query runs are still required. |
| Agent loop at most 10 seconds and at most three tool iterations | Three-step cap implemented; live time target pending | Normal plans are capped at three steps. [`evaluation/agent-acceptance-report.json`](evaluation/agent-acceptance-report.json) records mock-provider calls under 17 ms; live Gemini latency still needs measurement against the 10-second target. |
| Session continuity across three calls; token usage logged and capped | Verified locally with mocked provider | [`evaluation/agent-acceptance-report.json`](evaluation/agent-acceptance-report.json) records three turns in one session, plus a test that verifies two bounded provider calls and token logging under one correlation ID. Production cost reporting still needs current token rates. |
| Five agent failure/edge cases, including two injected failures, without a crash | Verified in regression suite | `test_five_agent_edge_cases_return_controlled_results` covers empty corpus, safety escalation, injected provider outage, invalid model output, and prompt injection. CI runs this test. |
| API P95 at most 2 seconds under 10 users; Locust latency and error graph | Measured for async submission; full query completion misses | In the live 10-user run, `POST /api/agent/jobs/` p95 was 540 ms with 0/10 failures, while end-to-end AI completion p95 was 6.1 s. The operation-specific graph is [`loadtest/query-profile-graph.html`](loadtest/query-profile-graph.html). This short run does not establish sustained capacity. |
| Redis behavior under concurrent load | Measured in both API and document-query profiles | The live query run measured direct Redis SET/GET p95 at 8 ms (6 calls) for 3 users and 7 ms (79 calls) for 10 users with zero failures. Earlier results remain in [`loadtest/concurrent-redis-report.md`](loadtest/concurrent-redis-report.md). |
| 50-PDF practical evaluation; OpenAPI/Postman collection | Synthetic text-PDF run complete | [`evaluation/50-pdf-report.json`](evaluation/50-pdf-report.json) records 50/50 single-page synthetic text PDFs processed and persisted. OCR and generated-summary quality are outside this mocked run. OpenAPI and Postman artifacts are present. |
| Zero-downtime redeployment and Docker image at most 1 GB | Production TLS config added; rollout unproven | [`docker-compose.production.yml`](docker-compose.production.yml) adds secure Django settings and Caddy TLS termination. Prior local images were below 1 GB; no external cloud rollout or zero-downtime test has been performed. |
| RAGAS report, three prompt-version scores, and zero unvalidated AI outputs | Partial | The v1 Ragas score checkpoint is 17/20 (faithfulness 0.8333, context precision 0.7778, context recall 0.9444, answer correctness 0.8631); v2/v3 scores are pending. Ragas resumes from checkpoints and assigns zero grounding scores to empty retrieval contexts. Pydantic rejects malformed generated outputs, covered by regression tests. |
| Trace failures with correlation IDs; document fallback chain and SLA | Implemented / partial evidence | Correlation logging and provider/retrieval fallbacks are implemented and documented. A production SLA/live deployment is not established. |
| Live demo URL and five-minute presentation | Deployment-ready config; live URL pending | A presentation outline and HTTPS Compose overlay exist. A cloud account, public DNS, production secrets, and actual rollout are still required for a URL and zero-downtime evidence. |

## Overall assessment

The project now has repeatable local acceptance coverage for Pydantic validation, three-call session continuity, five failure/edge cases, three-step tool planning, and 50 synthetic text PDFs. The live 3/10-user query run completed with no request failures, but query p95 (3.5/6.1 seconds) misses the 300 ms target. Heuristic Gemini answer/citation thresholds passed on synthetic data; full three-version Ragas, the 30% before/after comparison, a public URL, and zero-downtime rollout evidence remain pending.

| Requirement | Status | Evidence / scope |
| --- | --- | --- |
| End-to-end discharge summary explainer | Implemented | React upload/results/chat UI; Django processing; persisted summaries; async PDF, chat, and translation jobs. |
| RAG over the selected domain corpus | Implemented | Page-aware chunks, Gemini vector retrieval with Unicode lexical fallback, and source-page filtering for citations. The corpus is the uploaded discharge summary. |
| Agent with at least two real tools | Implemented | Document search, structured medication lookup, follow-up test lookup, and deterministic red-flag escalation. Medication records are stored in MySQL in Compose and are extracted from the uploaded document. |
| Django REST Framework endpoint | Implemented | `POST /api/agent/query/` is exposed through a DRF `@api_view`; queued endpoints are Django JSON endpoints. |
| MySQL-backed session memory | Implemented in Compose | `AgentSession` stores chat history linked to the document; Compose configures the Django database as MySQL. Local development defaults to SQLite. |
| Pydantic validation of generated structured outputs | Implemented | Extracted summaries, OCR results, translations, and agent answers are validated against Pydantic models before persistence/use. |
| 20-question evaluation with answer and citation scores | Completed on synthetic fixture | `evaluation/answer-quality.json` records 20 answers each for v1/v2/v3; answer correctness is 0.80–0.90 and citation correctness is 0.95. This is heuristic scoring, not clinical validation. |
| README setup, architecture, data sources and licenses | Implemented | `README.md` includes the architecture diagram, local/Compose setup, synthetic data provenance, and limitations. |
| Dockerized run / waived deployment | Implemented locally | Docker Compose configures Django, MySQL, Redis, Celery, frontend, and Locust. A local 20-user run completed. No cloud deployment was configured. |
| Correlation IDs, fallback, and bounded calls | Implemented | Structured request logs carry correlation IDs; Gemini model fallback/retry and lexical retrieval fallback are configured; output limits and per-query job usage/cost reporting are supported. Dollar estimates need current token rates configured in `backend/.env`. |
| Latency and load-test report | AI query report recorded; performance target not met | [`loadtest/live-query-profile-report.md`](loadtest/live-query-profile-report.md) records live 3/10-user asynchronous Gemini queries, end-to-end timings, Redis timings, and zero failed requests. Full-query p95 exceeded 300 ms; the 30% before/after target remains unmeasured. |
| Adversarial input safety | Implemented and regression tested | Retrieved/user text is always marked untrusted; high-fever and individualized-dose requests trigger a deterministic localized human-review response before a Gemini call. |
| Regional languages and human review | Implemented | English, Malayalam, Tamil, Hindi; safety escalation is localized for supported languages. |
| Live cloud URL / zero-downtime rollout | Not completed here | The local AI load profile and synthetic Gemini answer/citation checks are recorded. A public deployment target/domain and rollout evidence are still required. |

## Reproduce local checks

```powershell
python backend/manage.py test api
python backend/manage.py check
python backend/api/eval_harness.py
```

For generated-answer and citation scores, set the Gemini key and current input/output token rates in `backend/.env`, then run:

```powershell
python backend/api/eval_harness.py --answers --all-prompts
```

That command makes 60 logical Gemini answer calls over synthetic fixture data, plus embedding requests and any provider retries/JSON repairs. Do not treat the heuristic keyword-based answer score as clinical validation.
