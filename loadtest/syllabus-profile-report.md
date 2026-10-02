# Syllabus concurrency profile report

| Item | 3-user profile | 10-user profile |
| --- | --- | --- |
| Tool/script | Locust 2.46.6, `loadtest/locustfile.py` | Locust 2.46.6, `loadtest/locustfile.py` |
| Environment | Local Docker Compose; backend published on port 18000 | Local Docker Compose; backend published on port 18000 |
| Profile | 3 users, 2 users/second ramp, 1 minute | 10 users, 2 users/second ramp, 2 minutes |
| Endpoints | `GET /api/health/`, `GET /api/agent/usage/` | `GET /api/health/`, `GET /api/agent/usage/` |
| AI workload | Disabled | Disabled |
| Throughput | 0.93 requests/second | 3.29 requests/second |
| Latency, aggregate | p50 14 ms / p95 680 ms / p99 1000 ms | p50 11 ms / p95 22 ms / p99 75 ms |
| Error rate | 0/54 (0%) | 0/390 (0%) |
| Endpoint detail | Health p95 33 ms; usage p95 1000 ms, with cold-start outliers | Health p95 19 ms; usage p95 49 ms |
| Bottleneck | Two first usage requests each took about 1 second; cause not isolated | No bottleneck observed for these two lightweight endpoints |
| Before/after | No optimization comparison performed | No optimization comparison performed |
| Limits | Does not measure document retrieval, PDF/OCR, AI, Celery job completion, or translation | Same; this does not prove query/agent latency or AI capacity |

Run reproducibly from the repository root:

```powershell
$env:BACKEND_PORT = '18000'
.\loadtest\run-syllabus-profiles.ps1
```

Raw Locust CSV files are in `loadtest/results/` and are ignored by Git. The backend and worker Docker images are 401 MB each; the frontend image is 92.8 MB. All are below the syllabus's 1 GB image-size cap for this local build.
