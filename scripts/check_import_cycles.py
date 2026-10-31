"""Detect top-level circular imports. Run from backend/: python ../scripts/check_import_cycles.py"""
import ast, os, sys
files = [os.path.join(d, f) for d, _, fs in os.walk(".") for f in fs if f.endswith(".py") and "migrations" not in d and "tests" not in f and "test_" not in f and "venv" not in d]
def modname(p):
    m = p[2:-3].replace("\\", "/").replace("/", "."); return m[:-9] if m.endswith(".__init__") else m
mods = {modname(f): f for f in files}
graph = {}
for m, f in mods.items():
    t = ast.parse(open(f, encoding="utf-8").read()); deps = set()
    for n in t.body:  # top-level statements only (function-level imports are lazy)
        nodes = [n] if isinstance(n, (ast.Import, ast.ImportFrom)) else [x for x in ast.walk(n) if isinstance(x, (ast.Import, ast.ImportFrom))] if isinstance(n, (ast.If, ast.Try)) else []
        for x in nodes:
            if isinstance(x, ast.ImportFrom) and x.module:
                cands = [x.module] + [f"{x.module}.{a.name}" for a in x.names]
            elif isinstance(x, ast.Import):
                cands = [a.name for a in x.names]
            else: continue
            for c in cands:
                if c in mods and c != m: deps.add(c)
    graph[m] = deps
seen, stack, cycles = set(), [], []
def dfs(n, path):
    if n in path: cycles.append(path[path.index(n):] + [n]); return
    if n in seen: return
    seen.add(n)
    for d in graph[n]: dfs(d, path + [n])
for m in graph: dfs(m, [])
uniq = {tuple(sorted(c)) for c in cycles}
print(f"{len(mods)} modules; import cycles: {len(uniq)}")
for c in sorted(uniq): print(" -> ".join(c))
