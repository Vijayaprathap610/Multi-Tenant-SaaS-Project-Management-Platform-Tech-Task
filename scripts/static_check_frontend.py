"""Offline sanity check of frontend imports/exports/JSX. Run from frontend/: python ../scripts/static_check_frontend.py"""
import os, re
SRC = "src"
files = [os.path.join(d, f) for d, _, fs in os.walk(SRC) for f in fs if f.endswith((".js", ".jsx"))]
def resolve(frm, spec):
    base = os.path.normpath(os.path.join(os.path.dirname(frm), spec))
    for cand in (base, base + ".js", base + ".jsx", os.path.join(base, "index.js"), os.path.join(base, "index.jsx")):
        if os.path.isfile(cand): return cand
    return None
src = {f: open(f, encoding="utf-8").read() for f in files}
def exports(code):
    named = set(re.findall(r"export\s+(?:async\s+)?(?:function|const|let|class)\s+([A-Za-z0-9_]+)", code))
    for grp in re.findall(r"export\s*\{([^}]*)\}", code):
        named |= {x.split(" as ")[-1].strip() for x in grp.split(",") if x.strip()}
    return named, bool(re.search(r"export\s+default", code))
problems = []
for f, code in src.items():
    for m in re.finditer(r"import\s+(?:([A-Za-z0-9_]+)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s*['\"]([^'\"]+)['\"]", code):
        default, named, spec = m.groups()
        if not spec.startswith("."): continue
        target = resolve(f, spec)
        if not target: problems.append(f"{f}: cannot resolve '{spec}'"); continue
        if not target.endswith((".js", ".jsx")): continue
        names, has_default = exports(src[target])
        if default and not has_default: problems.append(f"{f}: '{spec}' has no default export")
        for n in [x.split(" as ")[0].strip() for x in (named or "").split(",") if x.strip()]:
            if n not in names: problems.append(f"{f}: '{n}' not exported by {target}")
    # JSX component tags that are not imported or defined
    defined = set(re.findall(r"(?:function|const|class)\s+([A-Z][A-Za-z0-9_]*)", code))
    imported = set()
    for m in re.finditer(r"import\s+(?:([A-Za-z0-9_]+)\s*,?\s*)?(?:\{([^}]*)\})?\s*from", code):
        if m.group(1): imported.add(m.group(1))
        for x in (m.group(2) or "").split(","):
            if x.strip(): imported.add(x.split(" as ")[-1].strip())
    for tag in set(re.findall(r"<([A-Z][A-Za-z0-9_]*)[\s/>.]", code)) | set(re.findall(r"<([A-Z][A-Za-z0-9_]*)\.[A-Za-z]", code)):
        if tag not in defined and tag not in imported and tag != "React":
            problems.append(f"{f}: JSX <{tag}> is not imported or defined")
    # hooks used but not imported from react
    for hook in ("useState", "useEffect", "useRef", "useCallback", "useMemo", "useContext"):
        if re.search(rf"\b{hook}\(", code) and not re.search(rf"\b{hook}\b[^;]*from\s*['\"]react['\"]", code) and f"{hook}" not in "".join(re.findall(r"import\s*\{[^}]*\}\s*from\s*['\"]react['\"]", code)):
            problems.append(f"{f}: {hook} used but not imported from react")
print(f"{len(files)} files checked, {len(problems)} problems")
for p in problems: print(p)
