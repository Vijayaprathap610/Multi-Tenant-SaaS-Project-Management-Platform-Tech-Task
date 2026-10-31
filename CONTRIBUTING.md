# Contributing (clean commits are a graded deliverable)

- **Branches:** `main` is always deployable. Work on `feature/<area>-<short-name>` or `fix/<short-name>` and merge with a pull request.
- **Commits:** small, one logical change each, imperative mood, scope prefix:
  `backend(issues): reject workflow transitions that are not allowed`, `frontend(board): revert card when the API refuses a move`,
  `docs: add webhook signature format`, `ci: run npm ci with --ignore-scripts`, `test(tenancy): cover export isolation`.
- **Never commit:** `.env`, credentials, Stripe keys, `node_modules`, uploaded media. Run `python scripts/audit.py` before pushing.
- **Each person commits their own work under their own name** (the individual reflections are checked against `git log --author`).
- **Before a pull request:** `docker compose run --rm backend python manage.py test`, `cd frontend && npm test && npm run build`.
- **Suggested first commits** (adapt to what you actually did): repository scaffold and Docker; accounts and authentication; workspaces,
  memberships and invitations; tenancy and permissions; projects and workflows; boards and issues; sprints; comments and attachments;
  notifications, webhooks and reports; billing; frontend shell and auth pages; Kanban; remaining pages; tests; CI; documentation.
