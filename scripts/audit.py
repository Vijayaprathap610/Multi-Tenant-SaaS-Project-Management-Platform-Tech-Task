#!/usr/bin/env python3
"""Requirements audit: reads the repository and reports what is done, what is pending and who owns it.
Never marks anything as done without a file or log that proves it. Exit code 1 while anything is pending.
Run from the repository root:  python scripts/audit.py
"""
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
checks = []  # (area, description, state, owner, detail) with state in DONE / PENDING / FAILED


def add(area, desc, ok, owner, detail="", failed=False):
    checks.append((area, desc, "FAILED" if failed else ("DONE" if ok else "PENDING"), owner, detail))


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


# 1. traceability: statuses and unsupported "Tested" claims
rows, header = [], None
for line in (read("docs/traceability.md") or "").splitlines():
    if not line.startswith("|"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if "Status" in cells:
        header = cells
        continue
    if header and re.match(r"^[RA]\d+$", cells[0]) and len(cells) == len(header):
        rows.append(dict(zip(header, cells)))
counts = {}
for r in rows:
    counts[r["Status"]] = counts.get(r["Status"], 0) + 1
tested = [r["ID"] for r in rows if r["Status"] == "Tested"]
have_logs = all(os.path.getsize(p) > 0 for p in glob.glob("docs/test-results/*.txt")) and glob.glob("docs/test-results/*.txt")
add("Traceability", f"No row marked Tested without logs (rows Tested: {len(tested)})", not tested or bool(have_logs),
    "Team", "Tested rows need real logs in docs/test-results/", failed=bool(tested) and not have_logs)
not_done = [r["ID"] for r in rows if r["Status"] in ("Not Started", "Blocked")]
add("Traceability", f"No Not Started / Blocked rows ({', '.join(not_done) or 'none'})", not not_done, "Team")

# 2. migrations committed for every app with models
# `tenancy` only defines an abstract base model, so it has no migrations of its own
apps = sorted(a for a in (os.path.basename(os.path.dirname(p)) for p in glob.glob("backend/*/models.py")) if a != "tenancy")
missing = [a for a in apps if not glob.glob(f"backend/{a}/migrations/0001_*.py")]
add("Backend", f"Migrations generated and committed ({len(apps) - len(missing)}/{len(apps)} apps)", not missing, "You",
    "run: docker compose run --rm backend python manage.py makemigrations" + (f"  (missing: {', '.join(missing)})" if missing else ""))
add("Backend", "Pinned lock file backend/requirements.txt", os.path.exists("backend/requirements.txt"), "You", "pip-compile backend/requirements.in -o backend/requirements.txt")
add("Frontend", "frontend/package-lock.json committed", os.path.exists("frontend/package-lock.json"), "You", "npm install --ignore-scripts, then commit the lockfile")
pkg = read("frontend/package.json") or ""
add("Frontend", 'axios pinned exactly to a safe version (1.14.0)', '"axios": "1.14.0"' in pkg or '"axios": "1.14.2"' in pkg, "Team", "1.14.1 and 0.30.4 were malicious")

# 3. real test runs (parse logs)
def log_state(path, ok_pat, fail_pat):
    t = read(path)
    if t is None or not t.strip():
        return None
    if re.search(fail_pat, t):
        return False
    return bool(re.search(ok_pat, t))
for label, path, okp, failp in (
        ("Backend tests", "docs/test-results/backend.txt", r"(?m)^OK\b", r"(?m)^FAILED|Traceback"),
        ("Frontend tests", "docs/test-results/frontend.txt", r"passed", r"failed"),
        ("End-to-end tests", "docs/test-results/e2e.txt", r"passed", r"failed|timed out")):
    st = log_state(path, okp, failp)
    add("Evidence", f"{label}: real log shows success", st is True, "You" if st is None else "You + Claude",
        f"{'missing log ' + path if st is None else 'log shows failures: send it for fixing'}", failed=(st is False))
add("Evidence", "Performance measurements with conditions", bool(read("docs/test-results/performance.md")), "You", "scripts/perf_check.py > docs/test-results/performance.md")
testing = read("docs/testing.md") or ""
section = testing.split("## Results (fill in from real runs)")[-1].split("###")[0]
unfilled = []
for line in section.splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if line.startswith("|") and cells and cells[0] in ("Backend", "Frontend", "End-to-end", "CI run"):
        if len(cells) < 5 or not cells[2] or not cells[3]:   # Date and Passed/failed/skipped must be filled
            unfilled.append(cells[0])
add("Evidence", f"docs/testing.md results table filled in (unfilled: {', '.join(unfilled) or 'none'})", not unfilled, "You")

# 4. deliverables that must contain real links / authored content
ev = read("docs/evidence.md") or ""
for label in ("CI run", "Deployed demo URL", "Screen recording", "Google Drive submission folder", "Repository"):
    line = next((l for l in ev.splitlines() if label.lower() in l.lower()), "")
    ok = "http" in line or (label.startswith("Deployed") and "n/a" in line.lower())
    add("Deliverables", f"Evidence link: {label}", ok, "You", "docs/evidence.md")
refl = [p for p in glob.glob("docs/reflections/*.md") if not p.endswith("TEMPLATE.md")]
add("Deliverables", f"Individual reflections written ({len(refl)} found)", len(refl) >= 1, "Each intern", "copy docs/reflections/TEMPLATE.md; one per intern")
add("Deliverables", "Architecture, ER, isolation, auth and async diagrams rendered", all(os.path.exists(f"docs/diagrams/{n}.png") for n in ("architecture", "er", "tenant-isolation", "auth-flow", "async-flows")), "Claude")
add("Deliverables", "API, security, architecture, testing, deployment, versions docs present", all(os.path.exists(f"docs/{n}.md") for n in ("api", "security", "architecture", "testing", "deployment", "versions")), "Claude")
ver = read("docs/versions.md") or ""
add("Versions", "No 'NOT verified' section left in docs/versions.md", "NOT verified" not in ver, "You + Claude", "verify, pin, then delete the section")

# 4b. frontend/backend API contract
r = subprocess.run([sys.executable, "scripts/check_api_contract.py"], capture_output=True, text=True)
add("Contract", "Every frontend API call matches a backend route and ends with a slash", r.returncode == 0, "Claude",
    r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:], failed=r.returncode != 0)

# 5. hygiene
tracked_env = False
if os.path.isdir(".git"):
    tracked_env = ".env" in subprocess.run(["git", "ls-files", ".env"], capture_output=True, text=True).stdout.split()
add("Hygiene", ".env is not committed", not tracked_env, "You", failed=tracked_env)
add("Hygiene", ".gitignore excludes .env", ".env" in (read(".gitignore") or "").split(), "Claude")
if os.path.isdir(".git"):
    n = subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip() or "0"
    add("Hygiene", f"Commit history exists ({n} commits); keep commits small and described", int(n) >= 10, "Team", "see CONTRIBUTING.md")
else:
    add("Hygiene", "Project is a git repository with a clean commit history", False, "Team", "git init / push to GitHub; see CONTRIBUTING.md")

# report
order = {"FAILED": 0, "PENDING": 1, "DONE": 2}
print("REQUIREMENTS AUDIT\n")
print("Traceability statuses: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + "\n")
for area, desc, state, owner, detail in sorted(checks, key=lambda c: (order[c[2]], c[0])):
    mark = {"DONE": "[x]", "PENDING": "[ ]", "FAILED": "[!]"}[state]
    print(f"{mark} {area}: {desc}" + (f"  -> owner: {owner}" if state != "DONE" else "") + (f"  ({detail})" if detail and state != "DONE" else ""))
pending = [c for c in checks if c[2] != "DONE"]
print(f"\n{len(checks) - len(pending)} done, {len(pending)} pending/failed of {len(checks)} checks.")
sys.exit(1 if pending else 0)
