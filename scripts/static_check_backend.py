"""Offline sanity check (no dependencies needed). Run from backend/: python ../scripts/static_check_backend.py"""
import ast, builtins, os, re, sys
ROOT = "."
files = [os.path.join(d, f) for d, _, fs in os.walk(ROOT) for f in fs if f.endswith(".py") and "migrations" not in d and "venv" not in d]
trees = {f: ast.parse(open(f, encoding="utf-8").read(), f) for f in files}

def modname(path):
    p = path[2:-3].replace("\\", "/").replace("/", ".")
    return p[:-9] if p.endswith(".__init__") else p
mods = {modname(f): f for f in files}

def top_names(tree):
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for t in ast.walk(n):
                if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store): names.add(t.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: names.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.If, ast.Try, ast.With, ast.For)):
            for t in ast.walk(n):
                if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store): names.add(t.id)
                if isinstance(t, (ast.FunctionDef, ast.ClassDef)): names.add(t.name)
                if isinstance(t, (ast.Import, ast.ImportFrom)):
                    for a in t.names: names.add((a.asname or a.name).split(".")[0])
    return names

tops = {m: top_names(trees[f]) for m, f in mods.items()}
problems = []

# 1. local imports resolve
for f, tree in trees.items():
    me = modname(f)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            if n.level:
                base = me.split(".")[: -n.level] if not f.endswith("__init__.py") else me.split(".")[: len(me.split(".")) - n.level + 1]
                target = ".".join(base + ([n.module] if n.module else []))
            else:
                target = n.module
            if target in mods:
                for a in n.names:
                    if a.name != "*" and a.name not in tops[target] and f"{target}.{a.name}" not in mods:
                        problems.append(f"{f}:{n.lineno}: '{a.name}' not defined in {target}")

# 2. names used but never bound anywhere in the file
BUILTINS = set(dir(builtins)) | {"__file__", "__name__"}
for f, tree in trees.items():
    bound = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): bound.add(n.name)
        if isinstance(n, ast.arg): bound.add(n.arg)
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): bound.add(n.id)
        if isinstance(n, ast.ExceptHandler) and n.name: bound.add(n.name)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: bound.add((a.asname or a.name).split(".")[0])
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in bound and n.id not in BUILTINS:
            problems.append(f"{f}:{n.lineno}: undefined name '{n.id}'")

# 3. urls.py: views.X exists
for f, tree in trees.items():
    if f.endswith("urls.py"):
        app = os.path.dirname(f)[2:]
        vm = f"{app}.views"
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "views" and vm in tops:
                if n.attr not in tops[vm]: problems.append(f"{f}:{n.lineno}: views.{n.attr} missing in {vm}")
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "include" and n.args and isinstance(n.args[0], ast.Constant):
                if n.args[0].value not in mods: problems.append(f"{f}:{n.lineno}: include({n.args[0].value}) not found")

# 4. string FK targets exist
model_classes = {}
for m, f in mods.items():
    if m.endswith(".models"):
        model_classes[m.split(".")[0]] = {c.name for c in trees[f].body if isinstance(c, ast.ClassDef)}
for f, tree in trees.items():
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in ("ForeignKey", "OneToOneField", "ManyToManyField") and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str) and "." in a.value:
                app, cls = a.value.split(".")
                if app not in ("auth",) and cls not in model_classes.get(app, set()):
                    problems.append(f"{f}:{n.lineno}: FK target {a.value} not found")

# 5. INSTALLED_APPS directories
settings = open("config/settings.py", encoding="utf-8").read()
for app in re.findall(r'^\s+"([a-z_]+)",$', settings.split("INSTALLED_APPS")[1].split("]")[0], re.M):
    if not app.startswith("django") and app not in ("rest_framework", "corsheaders") and not os.path.isdir(app):
        problems.append(f"INSTALLED_APPS: {app} directory missing")

print(f"{len(files)} files checked, {len(problems)} problems")
for p in sorted(set(problems)): print(p)
