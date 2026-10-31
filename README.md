> **First time here? Read `docs/START-HERE.md`** (browser-only setup, no local installs).

# Tech Task (FS-04) - backend foundation

Multi-tenant SaaS project management platform. This is the Day 1 slice:
Docker services, Django settings, custom user + single Platform Admin,
workspaces/memberships, and the tenancy base classes with isolation tests.
The React frontend is not scaffolded yet.

## First run
```bash
cp .env.example .env            # fill in secrets
docker compose run --rm backend python manage.py makemigrations
docker compose up --build
docker compose run --rm backend python manage.py test
docker compose run --rm backend python manage.py create_platform_admin --email you@example.com
```
Commit the generated `migrations/` files. Nothing here has been executed yet.

## Tenancy rules
- Workspace is the tenant. Tenant-owned models inherit `tenancy.models.TenantModel`.
- Tenant-owned views put `tenancy.mixins.TenantScopedMixin` first and declare
  `required_roles`; membership comes from the URL `workspace_id`, verified server-side.
- Non-members get 404 (no existence leak); insufficient role gets 403.

## API surface so far
`/api/auth/{csrf,register,login,logout,me,password-reset,password-reset/confirm}/`,
`/api/platform-admin/{login,stats}/`, `/api/workspaces/`,
`/api/workspaces/<id>/{members,invitations,audit}/`, `/api/invitations/accept/`.
Registration and password-reset responses are identical for existing and unknown
emails (no account enumeration). Invitation links use a signed, 7-day token bound to
one workspace, role and email address; password-reset links use Django's single-use token.

## Project management API (all under `/api/workspaces/<workspace_id>/projects/`)
`projects/`, `<pid>/members/`, `<pid>/statuses/`, `<pid>/transitions/`, `<pid>/boards/`,
`<pid>/boards/<bid>/{columns,kanban}/`, `<pid>/issues/` (+ `<id>/move/`), `<pid>/sprints/`
(+ `<id>/{start,complete,issues,report}/`).

- Owners/Admins see every project; Project Managers and Members only projects they were added to.
- Every id in a request body (status, sprint, assignee, issue_ids, membership_id) is validated
  against the project/workspace, so foreign ids fail as "invalid" and reveal nothing.
- Workflow rules live in `issues/services.check_transition` and are used by both PATCH and the
  Kanban `move` endpoint. New projects get To Do / In Progress / Done with To Do -> Done *not* allowed.
- The Kanban endpoint returns at most 500 issues (`truncated` flag) in a constant number of queries.

## Collaboration, jobs and integrations
- **Comments** `.../issues/<id>/comments/`; **attachments** `.../issues/<id>/attachments/` (+ `<id>/download/`).
  Uploads: extension allowlist, size cap, magic-byte check, server-decided content type, random storage
  name, optional scanner via `ATTACHMENT_SCAN_COMMAND` (fails closed). Files are never served by a media
  URL; the download view is tenant/project scoped and sends `attachment` + `nosniff` + sandbox CSP.
- **Notifications** `/api/workspaces/<id>/notifications/` (in-app + email via Celery; idempotent per event;
  recipients re-checked for project access).
- **Webhooks** `/api/workspaces/<id>/webhooks/` (Owner/Admin). HMAC-SHA256 header
  `X-TechTask-Signature: t=<ts>,v1=<hex>` over `"<ts>.<body>"`; `X-TechTask-Delivery` id for receiver-side
  de-duplication; up to 5 attempts with exponential backoff; https only and private/loopback targets
  refused (checked on save and again at delivery); secret shown once. Set `WEBHOOK_ALLOW_PRIVATE_NETWORKS=true`
  / `WEBHOOK_ALLOW_HTTP=true` only for local development.
- **Reports** `.../projects/<pid>/reports/` (async via Celery) and `.../reports/export/issues/` (CSV,
  formula-injection safe). Owner/Admin/PM only.
- **Celery beat** prunes old webhook deliveries, read notifications and stale invitations nightly.
- Known limitation: webhook secrets are stored in the database unencrypted (needed to sign requests).

## Frontend (React + Vite + React Bootstrap)
`frontend/` — routes: `/`, `/register`, `/login`, `/forgot-password`, `/reset-password`, `/accept-invite`,
`/onboarding`, `/app` (projects), `/app/projects/:id/{board,issues,sprints,workflow,members,reports}`,
`/app/{settings,billing,notifications,profile}`, `/platform-admin/login`, `/platform-admin`.
```bash
cd frontend && npm install        # creates package-lock.json: commit it
npm run dev                        # http://localhost:5173 (proxies /api to :8000)
npm test                           # Vitest + React Testing Library
npm run test:e2e                   # Playwright; needs `docker compose up` running
```
Auth uses Django's HttpOnly session cookie plus a CSRF header; nothing sensitive is kept in browser storage
(only the last selected workspace id as a UI hint). Route guards are a convenience: the backend authorizes every request.
See `docs/versions.md` (what was verified and what was not), `docs/deployment.md`.
