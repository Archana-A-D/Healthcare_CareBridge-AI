# Live concurrent document-query report

| Item | Result |
| --- | --- |
| Tool and script | Locust 2.46.6; `loadtest/locustfile.py`; per-user query cap and end-to-end timing in this profile |
| Environment and date | Local Docker Compose on 2026-10-02; backend, Celery, MySQL, Redis; Gemini async jobs; synthetic repository discharge PDF |
| 3-user profile | 3 concurrent users; ramp 3 users/second; 1 minute; max 1 document query/user; 62 total measured operations, 1.07 operations/second |
| 10-user profile | 10 concurrent users; ramp 10 users/second; 2 minutes; max 1 document query/user; 470 total measured operations, 3.97 operations/second |
| Endpoints tested | `POST /api/agent/jobs/`, `GET /api/agent/jobs/<id>/`, `GET /api/health/`, `GET /api/agent/usage/`, and direct Redis `SET`/`GET` |
| 3-user query latency | Enqueue p50 270 ms / p95 490 ms / p99 490 ms; full document query p50 3,100 ms / p95 3,500 ms / p99 3,500 ms |
| 10-user query latency | Enqueue p50 180 ms / p95 540 ms / p99 540 ms; full document query p50 4,500 ms / p95 6,100 ms / p99 6,100 ms |
| Redis latency | 3 users: 6 round trips, p95 8 ms; 10 users: 79 round trips, p95 7 ms; zero Redis failures |
| Error rate | 0 Locust request failures in both runs; 3/3 and 10/10 document jobs completed |
| Bottleneck | The full AI query dominates at 3.5–6.1 seconds p95. The 10-user enqueue route measured 540 ms p95, also over the 300 ms goal. These small samples do not isolate whether the queue, database, or Gemini service is the main contributor. |
| Fix applied and result | Added an end-to-end query metric and configurable per-user query cap. The Redis query-embedding cache is enabled, but no matched cache-off/cache-on comparison was collected, so no percentage improvement is claimed. |
| Limits | One AI question per user; local machine; 3 and 10 users; one synthetic document; live Gemini latency/quota; these short profiles do not prove sustained capacity. |
| Graph | [`query-profile-graph.html`](query-profile-graph.html), generated from the Locust stats CSVs. Raw CSVs and profile sidecars are in ignored `loadtest/results/` on this machine. |

## Conclusion against latency targets

The measured full-query p95 does **not** meet the syllabus's 300 ms target. The asynchronous submit request also exceeded 300 ms in both runs (490 ms and 540 ms p95). The 10-user submit p95 remained below the separate 2 second general API target, while the completed AI query did not. The Redis SET/GET path remained below 10 ms p95 in these samples.

No before/after latency reduction is claimed. The harness now supports a bounded live query workload and records full job completion time; a controlled cache-off/cache-on experiment is still needed to verify the 30% improvement requirement. Public deployment and zero-downtime rollout also remain unverified because this project has no public site address or cloud target configured.
