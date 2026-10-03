# Acceptance and evaluation runs

All datasets and PDFs used below are synthetic. Generated-answer evaluation sends prompts to Gemini and Ragas; check quota and cost first. The normal Django test suite mocks Gemini and makes no provider calls.

## Local, no-provider checks

From the repository root:

```powershell
python backend/manage.py check
python backend/manage.py test api
python backend/api/eval_harness.py --output evaluation/retrieval-report.json
python backend/manage.py test api.tests.PdfProcessingTests.test_50_synthetic_pdf_practical_evaluation
python backend/manage.py test api.tests.PdfProcessingTests.test_session_continuity_persists_three_turns api.tests.PdfProcessingTests.test_five_agent_edge_cases_return_controlled_results
python backend/manage.py test api.tests.PdfProcessingTests.test_token_budget_bounds_repair_and_logs_each_provider_call
```

The PDF test covers text extraction, persistence, and page/chunk provenance for 50 one-page synthetic PDFs. Its AI summary response is mocked, so it does not score OCR or generated summaries. The continuity and token-budget tests use mocked Gemini and verify session persistence, tool-step counts, configured output caps, token logging, and orchestration latency; they do not establish live Gemini latency or cost.

The retrieval harness prints a terminal summary with hit rate, recall, and precision as percentages, plus p50/p95/p99 latency. Its `--output` option also saves the detailed metrics as JSON. Retrieval scores measure evidence/page matching, not generated-answer correctness or clinical accuracy.

## Generated answers, prompt versions, and Ragas

Put a Gemini key in `backend/.env`; the evaluation harness loads it without printing it. Configure current token rates if cost reporting is needed. Install optional dependencies with Python 3.12 using `python -m pip install -r evaluation/requirements-ragas.txt`, or use the provided evaluator container: build with `docker build -f evaluation/Dockerfile.ragas -t carebridge-ragas-eval evaluation`, then run the Ragas command in a container with the repository mounted at `/workspace`.

```powershell
python backend/api/eval_harness.py --answers --all-prompts --output evaluation/answer-quality.json
python backend/api/ragas_report.py evaluation/answer-quality.json --output evaluation/ragas-report.json
```

The first command generates 60 answers (20 questions for each of v1, v2, and v3), plus document/query embeddings and retries/repairs if needed. The Ragas command then scores saved samples for faithfulness, context precision, context recall, and answer correctness using Gemini as evaluator. Both commands make external calls and may incur cost. These synthetic heuristic/model-judge scores are not clinical validation.

## Concurrent document-query profile

Start the Compose backend, Redis, MySQL, and Celery worker; upload a synthetic discharge PDF and wait for processing. Pass its summary ID to the Locust runner:

```powershell
.\loadtest\run-query-profile.ps1 -SummaryId '<summary-uuid>' -Users 3 -Minutes 2 -SpawnRate 1
```

The test submits asynchronous Gemini questions and records submit latency, job-poll latency, end-to-end query latency, failures, and Redis separately. `-QueryLimitPerUser` bounds provider calls (default one per user). This makes model calls; the runbook prints a quota/cost notice and writes sidecar metadata for model, prompt version, and a hash of the summary ID. See `loadtest/live-query-profile-report.md` for the latest local 3/10-user synthetic run. A matched cache-off/cache-on comparison is still required to claim a 30% p95 reduction.

## Cloud deployment

`docker-compose.production.yml` supplies production Django cookie/HTTPS settings and a Caddy HTTPS reverse proxy. On a VM with a public DNS name, configure `SITE_ADDRESS`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DJANGO_SECRET_KEY`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD`, then run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.production.yml config -q
docker compose -f docker-compose.yml -f docker-compose.production.yml up --build -d
```

Set SMTP variables if the deployment must send email. Point the DNS A/AAAA records at that VM and allow inbound TCP 80/443. The overlay prepares a TLS-backed single-host deployment and passes Django's `check --deploy` when valid secrets/hosts are configured; it does not provision cloud resources or demonstrate zero-downtime rollout. Those require a cloud account, DNS, secrets management, and a multi-instance rolling deployment target.
