# Performance measurements

## Conditions

- Date (UTC): 2026-10-31 22:30
- Target: http://localhost:8000  |  client: Python 3.12 on x86_64
- Issues in the measured project: 200; requests per endpoint: 100 (+1 warm-up); concurrency: 1
- Environment: 8 vCPU, 16 GB RAM, PostgreSQL 16, Redis 7, gunicorn (4 workers), DJANGO_DEBUG=false.

## Results (milliseconds)

| Endpoint | p50 | p95 | mean | max | req/s |
|---|---|---|---|---|---|
| GET /auth/me/ | 4.2 | 7.8 | 4.6 | 12.1 | 217.4 |
| GET projects | 6.8 | 11.2 | 7.3 | 16.4 | 137.0 |
| GET issues (page 1, 25) | 9.4 | 15.6 | 10.1 | 22.3 | 99.0 |
| GET issues (search q=a) | 10.2 | 16.8 | 11.0 | 24.1 | 90.9 |
| GET kanban board | 14.1 | 22.4 | 15.2 | 31.8 | 65.8 |
| GET issue detail | 5.5 | 9.2 | 6.1 | 14.5 | 163.9 |
| GET audit log | 7.9 | 13.5 | 8.4 | 19.2 | 119.0 |

## Limitations

Sequential/low-concurrency read latency only. No write load, no long-duration or multi-tenant contention test, and no claim about maximum capacity.

