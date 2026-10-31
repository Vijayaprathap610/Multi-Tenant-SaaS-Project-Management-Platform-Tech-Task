# 10-minute final presentation: outline

Target: 9 slides + live demo, ~10 minutes. Build the deck after real results exist (use real screenshots and numbers only).

| # | Time | Slide | Content | Evidence to show |
|---|---|---|---|---|
| 1 | 0:45 | Problem | Teams need Jira-like planning, but companies must never see each other's data | one sentence + the isolation promise |
| 2 | 0:45 | Objectives | the 21 mandatory requirements grouped in 5 themes; what "done" means | traceability matrix summary (counts by status) |
| 3 | 1:15 | Architecture and stack | `docs/diagrams/architecture.png`; Django/DRF, React, Postgres, Celery/Redis, Stripe, Docker | diagram |
| 4 | 1:30 | Tenant isolation and security | shared schema; membership resolved server-side each request; 404 for foreign ids; role matrix; body-id validation; jobs re-check tenant | `tenant-isolation.png`; isolation test results |
| 5 | 1:30 | Features and workflows | onboarding, invitations, Kanban with workflow-validated moves, sprints, comments/attachments, webhooks, billing | 3-4 screenshots |
| 6 | 3:00 | **Live demo** | see script below | the running app (or recording) |
| 7 | 1:00 | Challenges and solutions | e.g. keeping isolation uniform (mixins), optimistic Kanban with rollback, idempotent webhooks/Stripe events, unverifiable-in-sandbox dependency versions | your real stories |
| 8 | 1:00 | Testing and results | real pass/fail counts, cross-tenant results, measured latency with conditions | `docs/test-results/*` |
| 9 | 0:30 | Limitations and next steps | RLS, secret encryption, scanner, load testing, email verification, accessibility audit | `docs/security.md` limitations list |

## Demo script (3 minutes)
1. Log in as `owner@acme.demo` (seeded) and show the board; drag a card To Do → In Progress (persists).
2. Try To Do → Done: rejected and reverted; show the workflow page that explains why.
3. Open an issue: comment, attach a PNG; show the audit log entry (Settings → Audit log).
4. Log in as `member@acme.demo` in a private window: no Settings/Billing menu; direct URL returns the access message.
5. Log in as `owner@globex.demo` and paste an Acme project URL: "not found / no access" (tenant isolation).
6. Billing: show plan, limits and a Stripe **test-mode** checkout (test card only; say it is test mode).
7. Webhooks: send a test event to a request-inspection URL and show the signature header.

Rehearse with a timer; cut slide 7 or the webhook step if over time.
