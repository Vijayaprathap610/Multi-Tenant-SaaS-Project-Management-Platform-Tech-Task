#!/usr/bin/env python3
"""Cross-check: every API path the frontend uses must match a backend URL pattern and end with a slash.
Offline, no dependencies. Run from the repository root:  python scripts/check_api_contract.py

Matching rules (segment by segment, comparing the END of the path, because `${base}` hides the prefix):
  - a literal frontend segment must equal the literal backend segment (so a typo like 'begin' vs 'start' fails);
  - a dynamic frontend segment `${...}` matches any backend segment;
  - a backend parameter `<uuid:pk>` only matches a dynamic frontend segment.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---------- backend URL patterns ----------
patterns = set()


def norm(p):
    return "/" + re.sub(r"<[^>]+>", "{}", p).strip("/") + "/"


for f in glob.glob("backend/*/urls.py"):
    src = open(f, encoding="utf-8").read()
    m = re.search(r'^P\s*=\s*"([^"]*)"', src, re.M)
    prefix = m.group(1) if m else ""
    for a in re.findall(r'path\(\s*("(?:[^"\\]|\\.)*"|P\s*\+\s*"(?:[^"\\]|\\.)*"|P)\s*,', src):
        a = a.strip()
        if a == "P":
            patterns.add(norm(prefix))
        elif a.startswith("P"):
            patterns.add(norm(prefix + a.split("+", 1)[1].strip().strip('"')))
        else:
            patterns.add(norm(a.strip('"')))
    for r in re.findall(r'router\.register\(\s*"([^"]+)"', src):
        patterns.add(norm(r))
        patterns.add(norm(r + "/<pk>"))


def matches(path):
    fs = [x for x in path.strip("/").split("/") if x]
    for p in patterns:
        bs = [x for x in p.strip("/").split("/") if x]
        if len(fs) <= len(bs) and all(a == b or a == "{}" for a, b in zip(fs, bs[len(bs) - len(fs):])):
            return True
    return False


# ---------- frontend ----------
problems, checked = [], 0
PLACEHOLDER = r"\$\{(?:wsBase|base)\}"


def check(f, raw, local_urls):
    """raw: template literal text (without backticks), possibly starting with ${url}, ${base} or /api${...}"""
    global checked
    raw = re.sub(r"^/api(?=\$\{)", "", raw)
    candidates = [raw] if "${url}" not in raw else [raw.replace("${url}", d) for d in local_urls] or [raw]
    last = None
    for cand in candidates:
        s = re.sub(PLACEHOLDER, "@", cand)
        s = re.sub(r"\$\{[^}]+\}", "{}", s).split("?")[0]
        if not s.startswith(("@", "/")):
            return                                  # not an API path we can reason about
        tail = s.split("@")[-1] if "@" in s else s
        # '@/' alone is the workspace detail URL (/workspaces/{id}/)
        probe = "/workspaces/{}/" if (s.startswith("@") and not tail.strip("/")) else "/" + tail.strip("/") + "/"
        last = (cand, s.endswith("/"))
        if s.endswith("/") and matches(probe):
            checked += 1
            return
    checked += 1
    cand, slash = last
    problems.append(f"{f}: " + (f"no backend route matches '{cand}'" if slash else f"'{cand}' does not end with a slash"))


call_re = re.compile(r'(?:api\.(?:get|post|patch|put|delete)|useFetch|all)\(\s*(`[^`]*`)')
cond_re = re.compile(r"\?\s*(`[^`]*`)\s*:\s*null")
href_re = re.compile(r"(`/api\$\{[^`]*`)")
for f in sorted(glob.glob("frontend/src/**/*.js*", recursive=True)):
    if ".test." in f:
        continue
    src = open(f, encoding="utf-8").read()
    local_urls = [d[1:-1] for d in re.findall(r"const url = (`[^`]*`)", src)]
    seen = set()
    for rx in (call_re, cond_re, href_re):
        for m in rx.finditer(src):
            raw = m.group(1)[1:-1]
            if raw.startswith("/workspaces/${active") or (m.start(1), raw) in seen:
                continue
            seen.add((m.start(1), raw))
            check(f, raw, local_urls)

print(f"{len(patterns)} backend URL patterns; {checked} frontend API references checked; {len(problems)} problems")
for p in sorted(set(problems)):
    print(" -", p)
sys.exit(1 if problems else 0)
