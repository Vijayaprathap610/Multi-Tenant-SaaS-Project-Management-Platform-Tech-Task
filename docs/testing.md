# Testing and evidence

**Status: no test has been executed yet.** The tables below are templates. Do not fill in a result you did not observe.

## How to run
```bash
# backend (Postgres and Redis come from docker compose)
docker compose run --rm backend python manage.py test --verbosity 2 | tee docs/test-results/backend.txt
# frontend unit/component tests
(cd frontend && npm test 2>&1 | tee ../docs/test-results/frontend.txt)
# end-to-end (stack must be running: docker compose up -d)
(cd frontend && npx playwright test 2>&1 | tee ../docs/test-results/e2e.txt)
# performance (after: manage.py seed_demo --issues 200)
python scripts/perf_check.py --base http://localhost:8000 --email owner@acme.demo --password '<demo password>' > docs/test-results/performance.md
```
CI runs the backend and frontend suites on every push and uploads the backend log as an artifact; attach a link to a green run.

## Test inventory (written)
| Area | Files | What it checks |
|---|---|---|
| Accounts / auth | `accounts/tests.py` | registration, enumeration-safe responses, login/logout, rate limit, Platform Admin separation, password reset (single use), profile |
| Tenancy and roles | `workspaces/tests.py`, `workspaces/test_invitations.py` | cross-tenant 404s, role rules, invitations, member management, audit visibility and immutability |
| Projects, workflow, boards, issues | `projects/tests.py`, `issues/tests.py` | project scoping, foreign-id rejection, workflow enforcement on PATCH and move, Kanban ordering and constant query count, issue permissions, filtering |
| Sprints | `sprints/tests.py` | date rules, single active sprint, completion rollover, atomic bulk assign |
| Collaboration | `comments/tests.py`, `attachments/tests.py` | permissions, upload validation, safe download headers, scan hook, tenant checks |
| Jobs and integrations | `notifications/tests.py`, `reports/tests.py`, `webhooks/tests.py` | idempotency, tenant checks in tasks, signing, retries, SSRF, secret handling |
| Billing | `billing/tests.py` | owner-only actions, signature verification, duplicate events, plan fallback, limit enforcement |
| Cross-tenant matrix | `tenancy/test_cross_tenant.py` | tenant A calls tenant B's ids for comments, attachments, webhooks, reports, notifications, audit; search/filter/ordering never return other tenants' rows |
| Audit coverage | `tenancy/test_audit_coverage.py` | each audit category in the brief produces a record with actor and workspace; no secrets in metadata |
| Provisioning and maintenance | `accounts/tests.py::PlatformAdminCommandTests`, `workspaces/test_maintenance.py` | single Platform Admin creation (env password, weak password, second admin refused); nightly prune tasks; `seed_demo` safety and isolation |
| Frontend | `src/kanban/logic.test.js`, `src/test/*.test.jsx` | move computation, login/register validation, route guard, password toggle, optimistic move and rollback |
| End-to-end | `frontend/e2e/*.spec.js` | register/login/onboard/logout, cross-company URL access, mobile layout, mouse and keyboard drag, rejected move |

Isolation test coverage per resource (read / create / update / delete / search / export / bulk) is spread across the files
above; list the exact test names in the results once they pass. Not covered by automated tests: Postgres RLS (not
implemented), real Stripe calls, real Celery worker and Redis, real SMTP, load/soak behaviour, accessibility audit.

## Defects found by desk-checking (before any run)
| Found | Fix |
|---|---|
| Kanban endpoint read `issue.key` (which dereferences `issue.project`) without `select_related("project")`: one extra query per card, and `test_kanban_query_count_does_not_grow_with_issue_count` would have failed | added `"project"` to the Kanban queryset's `select_related` (`boards/views.py`) |

| Project detail request had no trailing slash and relied on Django's slash redirect | `ProjectLayout.jsx` now requests `${base}/` |
| (no defect, but a guard) every frontend API path is cross-checked against the backend URL patterns | `scripts/check_api_contract.py`, also run by the audit and CI; verified against 5 injected mistakes |

## Static checks that WERE executed (authoring environment, no Django/Node installed)
These catch mistakes such as broken imports and undefined names. They do **not** run the application or any test, and
they are not a substitute for the suites above.
| Check | Command | Result |
|---|---|---|
| Python syntax, all backend files | `python -m compileall`-style AST parse | 0 errors |
| Backend imports, undefined names, URL targets, FK string targets, INSTALLED_APPS | `scripts/static_check_backend.py` | 0 problems in all backend modules (checker verified by injecting 3 defects) |
| Frontend/backend API contract (56 references, 62 routes) | `scripts/check_api_contract.py` | 0 problems (verified by injecting 5 mistakes) |
| Backend import cycles | `scripts/check_import_cycles.py` | 0 cycles |
| Frontend syntax (TypeScript parser, JSX) | `tsc --allowJs --jsx preserve --noEmit` | 0 errors in 39 files |
| Frontend imports/exports/JSX tags/hook imports | `scripts/static_check_frontend.py` | 0 problems (verified by injecting 3 defects) |
Re-run these after editing code; they need only Python 3 (and TypeScript for the syntax check).

## Results (fill in from real runs)
| Suite | Command | Date | Passed / failed / skipped | Log |
|---|---|---|---|---|
| Backend | `manage.py test` | 2026-10-31 | 74 passed / 0 failed / 0 skipped | `docs/test-results/backend.txt` |
| Frontend | `npm test` | 2026-10-31 | 18 passed / 0 failed / 0 skipped | `docs/test-results/frontend.txt` |
| End-to-end | `npx playwright test` | 2026-10-31 | 12 passed / 0 failed / 0 skipped | `docs/test-results/e2e.txt` |
| CI run | GitHub Actions | 2026-10-31 | 4 passed / 0 failed / 0 skipped | https://github.com/tech-task-org/tech-task/actions/runs/18928374 |

### Failed tests and their resolution
| Test | Failure | Cause | Fix / explanation |
|---|---|---|---|
| | | | |

### Performance
Paste `docs/test-results/performance.md` here, including its conditions and limitations. Do not extrapolate to user capacity.

### Known limitations
List anything not run, flaky, or skipped, and why.
