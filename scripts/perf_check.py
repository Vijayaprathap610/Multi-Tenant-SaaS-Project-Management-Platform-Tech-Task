#!/usr/bin/env python3
"""Measure API latency against a running stack. Standard library only.

Usage:
  python scripts/perf_check.py --base http://localhost:8000 --email owner@acme.demo --password '<demo password>' \
      --requests 100 --concurrency 1 > docs/test-results/performance.md

Prints a Markdown report with the test conditions. Numbers are only meaningful for the machine and data size
they were measured on; always quote the conditions with the results.
"""
import argparse
import http.cookiejar
import json
import platform
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--requests", type=int, default=50)
    ap.add_argument("--concurrency", type=int, default=1)
    a = ap.parse_args()

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(method, path, body=None):
        headers = {"Content-Type": "application/json", "Referer": a.base + "/", "Origin": a.base}
        csrf = next((c.value for c in jar if c.name == "csrftoken"), None)
        if csrf:
            headers["X-CSRFToken"] = csrf
        req = urllib.request.Request(a.base + path, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
        with opener.open(req, timeout=30) as r:
            return json.loads(r.read() or b"null")

    call("GET", "/api/auth/csrf/")
    me = call("POST", "/api/auth/login/", {"email": a.email, "password": a.password})
    ws = me["memberships"][0]["workspace_id"]
    base = f"/api/workspaces/{ws}"
    project = call("GET", f"{base}/projects/")["results"][0]["id"]
    pbase = f"{base}/projects/{project}"
    board = call("GET", f"{pbase}/boards/")["results"][0]["id"]
    issue = call("GET", f"{pbase}/issues/?page_size=1")["results"][0]["id"]
    total_issues = call("GET", f"{pbase}/issues/?page_size=1")["count"]

    endpoints = {
        "GET /auth/me/": "/api/auth/me/",
        "GET projects": f"{base}/projects/",
        "GET issues (page 1, 25)": f"{pbase}/issues/",
        "GET issues (search q=a)": f"{pbase}/issues/?q=a",
        "GET kanban board": f"{pbase}/boards/{board}/kanban/",
        "GET issue detail": f"{pbase}/issues/{issue}/",
        "GET audit log": f"{base}/audit/",
    }

    def timed(path):
        t = time.perf_counter()
        call("GET", path)
        return (time.perf_counter() - t) * 1000

    rows = []
    for name, path in endpoints.items():
        timed(path)  # warm-up, not counted
        with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
            t0 = time.perf_counter()
            samples = sorted(pool.map(lambda _: timed(path), range(a.requests)))
            wall = time.perf_counter() - t0
        p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
        rows.append((name, statistics.median(samples), p95, statistics.mean(samples), samples[-1], a.requests / wall))

    print("# Performance measurements\n")
    print("## Conditions\n")
    print(f"- Date (UTC): {datetime.now(timezone.utc):%Y-%m-%d %H:%M}")
    print(f"- Target: {a.base}  |  client: Python {platform.python_version()} on {platform.platform()}")
    print(f"- Issues in the measured project: {total_issues}; requests per endpoint: {a.requests} (+1 warm-up); concurrency: {a.concurrency}")
    print("- Client and server on the same machine unless stated otherwise. Fill in: CPU/RAM, DEBUG on/off, gunicorn workers, DB size.\n")
    print("## Results (milliseconds)\n")
    print("| Endpoint | p50 | p95 | mean | max | req/s |")
    print("|---|---|---|---|---|---|")
    for n, p50, p95, mean, mx, rps in rows:
        print(f"| {n} | {p50:.1f} | {p95:.1f} | {mean:.1f} | {mx:.1f} | {rps:.1f} |")
    print("\n## Limitations\n")
    print("Sequential/low-concurrency read latency only. No write load, no long-duration or multi-tenant contention test, "
          "and no claim about maximum capacity.")


if __name__ == "__main__":
    sys.exit(main())
