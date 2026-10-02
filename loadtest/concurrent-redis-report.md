# Concurrent API and Redis Load-Test Report

| Item | Result |
| --- | --- |
| Tool and script | Locust 2.46.6, `loadtest/locustfile.py` |
| Test date and environment | 2026-10-02 05:24 IST; local Docker Compose stack; backend bound to host port 18000 |
| Test profile | 3 concurrent users; ramp-up 3 users/second; 1 minute; per-user wait 1–3 seconds; mixed health, usage, and Redis operations |
| Endpoints tested | `GET /api/health/` (51), `GET /api/agent/usage/` (8); Redis operations: `SET` + `GET` round trip (9) |
| AI mode | Disabled; no PDF, chat, or translation jobs |
| Throughput | 68 operations / 60 seconds: 1.13 operations/second, including 9 direct Redis operations |
| Latency | Aggregate p50 9 ms / p95 52 ms / p99 320 ms; health p50 9 / p95 50 / p99 160 ms; usage p50 14 / p95 320 / p99 320 ms |
| Redis latency | SET/GET p50 3 ms / p95 8 ms / p99 8 ms; 9 round trips |
| Error rate | 0/68 (0%); no Locust failures |
| Bottleneck found | No Redis failure was observed. Usage had a 320 ms p95 across only 8 requests; this short run is too small to isolate its cause or establish the syllabus query-latency target. |
| Fix applied and result | Added direct Redis SET/GET instrumentation and Locust Redis connectivity. No before/after performance claim; this is the first run with Redis instrumentation. |
| Limits | Does not exercise document queries, PDF/OCR, Gemini, Celery job completion, translation, or a synchronized burst. Three virtual users are not three simultaneous query requests. Results are local and the small sample is not a capacity claim. |

## Endpoint details

| Operation | Requests | p50 | p95 | p99 | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `GET /api/health/` | 51 | 9 ms | 50 ms | 160 ms | 0 |
| `GET /api/agent/usage/` | 8 | 14 ms | 320 ms | 320 ms | 0 |
| Redis `SET` + `GET` | 9 | 3 ms | 8 ms | 8 ms | 0 |

The health endpoint writes and reads Redis through Django. Direct Redis measurements are emitted separately as Locust's `REDIS / Redis SET/GET` operation. The run did not submit document-query requests, so it does not verify the syllabus's P95 query target of 300 ms.

[View the generated p95 latency and cumulative failure graph](concurrent-redis-graph.html).
