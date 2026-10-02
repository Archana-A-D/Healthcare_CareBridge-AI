# CareBridge-AI Load-Test Report Template

| Item | Result |
| --- | --- |
| Tool and script | Locust / k6; script path: |
| Test date and environment | |
| Test profile | Concurrent users: ; ramp-up: ; duration: ; wait time: ; request pattern: |
| Endpoints tested | |
| Redis profile | Direct Redis operation: ; Redis p50/p95/p99: ; API-mediated Redis check (`GET /api/health/`): ; errors: |
| AI mode | Disabled / Gemini enabled; model: |
| Throughput | Requests per second: |
| Latency | p50: ; p95: ; p99: |
| Error rate | Failed requests: ; rate: ; failure details: |
| Latency/error graph | File path: ; generated from Locust stats and history CSVs: |
| Bottleneck found | |
| Fix applied and result | Before: ; change: ; after: |
| Limits | |

## Notes

- Record whether AI endpoints were included. Gemini latency, quotas, and network conditions affect those results.
- Locust reports HTTP endpoints and `REDIS / Redis SET/GET` separately. `/api/health/` also writes and reads Redis through Django.
- State whether users were ramped gradually or started together; concurrent users are not the same as an instantaneous request burst.
- Generate a static latency/error graph with `python loadtest/render-locust-report.py <prefix>_stats.csv <prefix>_stats_history.csv --output loadtest/<run>-graph.html`.
- Report intentional failures separately from service errors.
- Do not claim a before/after improvement unless both runs used the same machine, profile, and data.
