# CareBridge-AI Load-Test Report

| Item | Result |
| --- | --- |
| Tool and script | Locust 2.46.6, `loadtest/locustfile.py` |
| Test date and environment | 2026-10-01 22:01:57–22:06:57 UTC; Docker Desktop Linux engine 29.8.1, 12 CPUs and 3.7 GiB memory allocated |
| Test profile | 20 concurrent users; ramp-up 4 users/second; 5 minutes; per-user wait 1–3 seconds |
| Endpoints tested | `GET /api/health/`, `GET /api/agent/usage/` |
| AI mode | Disabled; no PDF, chat, or translation requests were included |
| Throughput | 1,959 requests; 6.55 requests/second |
| Latency | p50: 9 ms; p95: 14 ms; p99: 33 ms; p99.9: 500 ms; maximum: 712 ms |
| Error rate | 2/1,959 (0.10%); one connection reset on each tested endpoint |
| Bottleneck found | No sustained throughput bottleneck is evident for these lightweight endpoints. Two transient connection resets and rare high-latency outliers occurred. The test does not identify their cause. |
| Fix applied and result | No before/after run was supplied. This run establishes a baseline only. |
| Limits | Does not measure PDF parsing/OCR, Gemini calls, chat, translation, Celery job polling, or AI costs. Results apply only to this local Docker setup and this traffic mix. |

## Run outcome

All 20 users spawned and the 5-minute time limit was reached. Locust exited with code 1 because the run contained failed requests; the two failures were recorded as `ConnectionResetError(104, 'Connection reset by peer')`. This is a completed run with a 0.10% failure rate, not a Compose startup failure.

The `95%` and `99%` values are from the final Locust percentile table. The supplied CSV snapshot is a few requests behind the final console summary; the final console totals above are used here.

## Scope note

The run proves that the local stack served health and usage traffic with 20 Locust users. It does not establish capacity for AI workloads. For that, run a separate controlled test with a synthetic uploaded document and `LOAD_TEST_SUMMARY_ID` configured, monitor Gemini quota/cost, and report its results separately.
