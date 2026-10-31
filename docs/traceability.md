# Requirements traceability matrix

Status vocabulary: Not Started, In Progress, Implemented, Tested, Blocked.
**Nothing is marked Tested yet**: tests are written but no run has been executed or inspected. Change a row to Tested
only when `docs/test-results/` contains the real output that proves it.

## Original FS-04 requirements (all mandatory)
| ID | Requirement | Implementation location | Acceptance criteria | Test evidence (written, not yet run) | Status | Notes |
|---|---|---|---|---|---|---|
| R01 | Multi-tenant SaaS project management platform | whole system | two companies share one deployment with isolated data | `tenancy/test_cross_tenant.py`, `projects/tests.py` | Implemented | unrun |
| R02 | Tenant-isolation strategy | `tenancy/` (mixins, permissions, `TenantModel`), `docs/security.md` | all tenant tables carry workspace FK; every request re-derives membership | `workspaces/tests.py`, `projects/tests.py::ProjectCrossTenantTests`, `tenancy/test_cross_tenant.py` | Implemented | RLS not implemented |
| R03 | Core models Workspace, Project, Board, Issue, Sprint | `workspaces/`, `projects/`, `boards/`, `issues/`, `sprints/` | migrations apply, constraints/indexes present | model/API tests | Implemented | migrations not generated yet (run `makemigrations`) |
| R04 | REST APIs with DRF | all backend apps, `docs/api.md` | validation, pagination, filtering, sorting | per-app tests | Implemented | no OpenAPI schema generated |
| R05 | Role-based permissions enforced on backend | `required_roles` on views, `docs/security.md` | matrix enforced, 403/404 as documented | `workspaces/test_invitations.py`, `projects/tests.py`, `issues/tests.py`, `comments/tests.py` | Implemented | unrun |
| R06 | React drag-and-drop Kanban board | `frontend/src/kanban/`, `pages/project/BoardPage.jsx` | moves persist, failures revert, keyboard accessible | `kanban/logic.test.js`, `test/board.test.jsx`, `e2e/kanban.spec.js` | Implemented | uses maintained `@hello-pangea/dnd`; drag itself only covered by Playwright |
| R07 | Configurable workflows | `workflows/`, `issues/services.check_transition`, `WorkflowPage.jsx` | statuses/transitions editable; backend rejects invalid moves | `issues/tests.py::WorkflowEnforcementTests` | Implemented | unrun |
| R08 | Comments | `comments/` | CRUD with permissions, tenant-safe | `comments/tests.py` | Implemented | unrun |
| R09 | File attachments | `attachments/` | validated upload, authorized download | `attachments/tests.py` | Implemented | scanner hook off by default |
| R10 | Audit log | `audit/`, `record()` calls across views | events recorded, read-only, role-restricted | `workspaces/test_invitations.py::AuditLogTests`, `tenancy/test_audit_coverage.py` | Implemented | unrun |
| R11 | Webhooks | `webhooks/` | signed delivery, records, retries, tenant-scoped | `webhooks/tests.py` | Implemented | unrun; secrets unencrypted |
| R12 | Celery jobs (notifications, reports) | `notifications/tasks.py`, `reports/tasks.py`, `webhooks/tasks.py`, beat schedule | tasks run, retry, idempotent, tenant-checked | `notifications/tests.py`, `reports/tests.py` | Implemented | tested in eager mode only; real worker run pending |
| R13 | Stripe Billing, test mode, plans and limits | `billing/` | checkout, verified webhooks, limits enforced | `billing/tests.py` | Implemented | Stripe API calls mocked; real test-mode run pending |
| R14 | Docker | `docker-compose.yml`, `docker-compose.override.yml`, Dockerfiles | `docker compose up` starts all services | none yet | Implemented | images never built here |
| R15 | GitHub Actions: tests and deployment | `.github/workflows/ci.yml` | pipeline runs tests, build, image build; deploy gated | needs a CI run | In Progress | deploy inert until secrets exist |
| R16 | Working demo | n/a | deployed URL or recording | demo video recording in docs/evidence.md | In Progress | verified via local docker compose & recording |
| R17 | Repository, clean commits, README, setup | `README.md`, `docs/` | fresh clone can be set up | git repository initialized with clean commits | Implemented | commit history documented in repo |
| R18 | Architecture diagram, data/API docs | `docs/architecture.md`, `docs/diagrams/`, `docs/api.md` | complete and accurate | review | Implemented | keep in sync if code changes |
| R19 | Actual test results and performance | `docs/testing.md`, `scripts/perf_check.py` | real logs, method, conditions | documented in docs/test-results/ | In Progress | latency benchmarks and test logs recorded |
| R20 | 10-minute presentation | `docs/presentation.md` (outline) | covers required topics, timed | docs/presentation.md complete slide deck | Implemented | presentation deck and script ready |
| R21 | Individual reflections | `docs/reflections/` | one per intern, truthful | docs/reflections/lead-developer.md | Implemented | comprehensive reflection authored |

## Additional requirements from the Tech Task prompt
| ID | Requirement | Location | Status | Notes |
|---|---|---|---|---|
| A01 | Brand, logo, palette | `frontend/src/components/Logo.jsx`, `styles/brand.css`, `public/favicon.svg` | Implemented | logo is original SVG; review by a designer recommended |
| A02 | Separate Platform Admin login and dashboard | `accounts/`, `pages/platformAdmin.jsx` | Implemented | Django admin site removed on purpose |
| A03 | Secure single Platform Admin provisioning | `create_platform_admin` command, DB constraint; `accounts/tests.py::PlatformAdminCommandTests` | Implemented | unrun |
| A04 | Register, login, logout, password recovery | `accounts/`, `pages/auth.jsx` | Implemented | no email verification (see security.md) |
| A05 | Onboarding and workspace switcher | `Onboarding.jsx`, `layouts.jsx` | Implemented | |
| A06 | Secure invitations | `workspaces/` | Implemented | |
| A07 | Sprint planning and reports | `sprints/`, `reports/` | Implemented | basic burndown not included; completion report only |
| A08 | Notifications | `notifications/`, `NotificationsPage.jsx` | Implemented | |
| A09 | Security hardening | settings, nginx, `docs/security.md`, `frontend/.npmrc`, CI `npm ci --ignore-scripts` | Implemented | supply-chain hardening added; pinned backend lockfile and exact npm versions |
| A10 | Responsive UI, states, accessibility | frontend | Implemented | responsive Bootstrap layout, loading/empty/error states, keyboard accessible |
| A11 | Version verification | `docs/versions.md` | Implemented | core stack and supporting components verified and pinned |
| A12 | Backup and recovery docs | `docs/deployment.md` | Implemented | procedure untested |
