#!/usr/bin/env bash
# One-shot first run: builds, generates migrations, runs every automated suite, and writes ONE log file
# (first-run-log.txt) you can send back for debugging. Needs Docker; Node is optional (frontend steps are skipped without it).
# Usage (from the repository root):  bash scripts/first_run.sh
set -u
cd "$(dirname "$0")/.."
LOG=first-run-log.txt
: > "$LOG"
FAILED=()

if [ ! -f .env ]; then
  cp .env.example .env
  python3 - <<'PY'
import re, secrets
s = open(".env").read()
s = re.sub(r"^DJANGO_SECRET_KEY=.*$", "DJANGO_SECRET_KEY=" + secrets.token_urlsafe(50), s, flags=re.M)
s = re.sub(r"^POSTGRES_PASSWORD=.*$", "POSTGRES_PASSWORD=" + secrets.token_urlsafe(18), s, flags=re.M)
s = re.sub(r"^DJANGO_DEBUG=.*$", "DJANGO_DEBUG=true", s, flags=re.M)
open(".env", "w").write(s)
PY
  echo "Created .env with generated local secrets (it is git-ignored; never commit it)." | tee -a "$LOG"
fi

step() {  # step "name" command...
  local name="$1"; shift
  echo "" >> "$LOG"; echo "=================== $name ===================" | tee -a "$LOG"
  echo "\$ $*" >> "$LOG"
  "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "exit code: $rc" | tee -a "$LOG"
  [ $rc -ne 0 ] && FAILED+=("$name")
  return 0
}

if command -v npm >/dev/null 2>&1; then
  step "0. frontend npm install (creates package-lock.json)"  bash -c "cd frontend && npm install --ignore-scripts"
fi
step "1. docker compose build"            docker compose build
step "2. start database and redis"        docker compose up -d --wait db redis
step "3. makemigrations"                  docker compose run --rm backend python manage.py makemigrations
step "4. migrate (applies migrations)"    docker compose run --rm backend python manage.py migrate
step "5. Django system check"             docker compose run --rm backend python manage.py check
step "6. backend tests"                   docker compose run --rm backend python manage.py test --verbosity 2
if command -v npm >/dev/null 2>&1; then
  step "7. frontend tests"                bash -c "cd frontend && npm test"
  step "8. frontend build"                bash -c "cd frontend && npm run build"
else
  echo "Node/npm not found: frontend steps skipped." | tee -a "$LOG"
fi

echo "" | tee -a "$LOG"
echo "==================== SUMMARY ====================" | tee -a "$LOG"
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "All steps exited with code 0. Still send the log: exit codes are not the same as 'every test passed'." | tee -a "$LOG"
else
  printf 'Failed steps:\n'; printf ' - %s\n' "${FAILED[@]}"
  printf 'Failed steps:\n' >> "$LOG"; printf ' - %s\n' "${FAILED[@]}" >> "$LOG"
fi
echo "Log saved to $LOG (generated migrations are in backend/*/migrations/ and should be committed)."
