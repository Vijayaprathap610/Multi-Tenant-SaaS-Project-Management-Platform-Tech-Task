#!/usr/bin/env python3
"""Shrink first-run-log.txt to what is needed for debugging: the summary plus the tail of every failed step.
Usage: python3 scripts/summarize_log.py [first-run-log.txt] [--tail 120]   (then paste the output to Claude)"""
import re
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
path = args[0] if args else "first-run-log.txt"
tail = int(sys.argv[sys.argv.index("--tail") + 1]) if "--tail" in sys.argv else 120
try:
    text = open(path, encoding="utf-8", errors="replace").read()
except OSError:
    sys.exit(f"Cannot open {path}. Run `bash scripts/first_run.sh` first (from the repository root).")

parts = re.split(r"^=+ (.+?) =+$", text, flags=re.M)   # [pre, name1, body1, name2, body2, ...]
steps = list(zip(parts[1::2], parts[2::2]))
print("FIRST-RUN SUMMARY\n")
failed = []
for name, body in steps:
    if name == "SUMMARY":
        continue
    m = re.findall(r"exit code: (\d+)", body)
    code = m[-1] if m else "?"
    print(f"  [{'ok' if code == '0' else 'FAILED'}] {name} (exit {code})")
    if code != "0":
        failed.append((name, body))
if not steps:
    print("  (no steps found in the log: did the script start?)")
for name, body in failed:
    lines = [l for l in body.splitlines() if l.strip()]
    print(f"\n----- {name}: last {min(tail, len(lines))} lines -----")
    print("\n".join(lines[-tail:]))
print("\nAll steps exited 0." if steps and not failed else f"\n{len(failed)} step(s) failed." if failed else "")
