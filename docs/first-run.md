# First run: what to do and what to send back

1. Choose where to run it:
   - **No local install (easiest):** push the repository to GitHub, open it in **GitHub Codespaces** (Code, Codespaces, Create).
     `.devcontainer/devcontainer.json` provides Docker, Node 24 and Python 3.12. Its feature versions are from memory and not verified
     (docs/versions.md); if the container fails to build, send me the error. Codespaces has usage quotas: check your plan.
   - **Locally:** install Docker (with Compose) and, optionally, Node. On Windows use WSL2 and run the commands inside it.
2. From the repository root: `bash scripts/first_run.sh` (takes several minutes the first time).
3. Run `python3 scripts/summarize_log.py` and send its output (or send `first-run-log.txt`) (or, if it is huge, the **SUMMARY** plus the last ~150 lines of each failed step).
   The log contains no secrets; `.env` is never printed.
4. Commit `backend/*/migrations/` and `frontend/package-lock.json` once the steps pass.

## Failures that are likely on a first run (not bugs in your setup)
| Symptom | Likely cause | What I will do |
|---|---|---|
| `makemigrations` reports errors or `check` shows E/W codes | model definitions I could not execute | fix the model |
| `ImportError` / `ModuleNotFoundError` in tests | a dependency name or version | adjust `requirements.in` |
| Many tests fail with the same error | one shared helper or setting | fix once |
| `migrate` fails on a constraint | version-specific Django behaviour | adjust the constraint |
| `npm install` peer-dependency errors | version ranges not fully verified (Vite 8, Vitest 4, jsdom) | adjust `package.json` |
| Vitest/React Testing Library failures | component query or mock mismatch | fix the test or component |

After each fix round, re-run `scripts/first_run.sh`. Only then move on to `docker compose up`, the Playwright run
(`cd frontend && npx playwright install chromium && npx playwright test`), Stripe test setup and deployment (`docs/deployment.md`).
