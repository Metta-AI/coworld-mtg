"""Small CAOS value/continuation helpers. No worker waits on another worker."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tempfile

ARGS = Path("/cas/args")
ENTRYPOINTS = {'start': ('factory', 'start'), 'acquired': ('factory', 'acquired'), 'vendored': ('factory', 'vendored'), 'baseline-built': ('factory', 'baseline_built'), 'baseline-fitted': ('factory', 'baseline_fitted'), 'discovered': ('factory', 'discovered'), 'planned': ('factory', 'planned'), 'plan-reviewed': ('factory', 'plan_reviewed'), 'implemented': ('factory', 'implemented'), 'candidate-created': ('factory', 'candidate_created'), 'candidate-built': ('factory', 'candidate_built'), 'candidate-fitted': ('factory', 'candidate_fitted'), 'compared': ('factory', 'compared'), 'reviewed': ('factory', 'reviewed'), 'dispatch': ('factory', 'dispatch'), 'acquire': ('mtg', 'acquire'), 'fit': ('mtg', 'fit'), 'discover': ('mtg', 'discover'), 'vendor': ('build', 'vendor'), 'build': ('build', 'compile_target'), 'role': ('agents', 'role'), 'role-done': ('agents', 'role_done'), 'candidate': ('evaluate', 'candidate'), 'compare': ('evaluate', 'compare')}

def command(*args: str) -> str:
    return subprocess.check_output(["caos", *map(str, args)], text=True).strip()

def fetch(path: Path, recursive: bool = False) -> Path:
    command("get", *(["-r"] if recursive else []), str(path))
    return path

def argument(name: str, recursive: bool = False) -> Path:
    return fetch(ARGS / name, recursive)

def text(name: str) -> str:
    return argument(name).read_text().strip()

def load(path: Path):
    return json.loads(fetch(path).read_text())

def value(name: str):
    return load(ARGS / name)

def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def identity(path: Path) -> str:
    return command("hash", str(path))

def scratch(name: str) -> Path:
    return Path(tempfile.mkdtemp(prefix="factory-" + name + "-"))

def store(path: Path, name: str = "value") -> Path:
    dest = Path("/cas") / ("factory-" + name + "-" + os.urandom(6).hex())
    command("put", str(path), str(dest))
    return dest

def json_value(v, name: str = "json") -> Path:
    p = scratch(name) / "value.json"
    p.write_bytes(canonical(v) + b"\n")
    return store(p, name)

def link(source: Path, destination: Path):
    fetch(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(source)

def tree(values: dict[str, Path], name: str = "tree") -> Path:
    out = scratch(name)
    for key, path in values.items():
        if not key or key.startswith("/") or ".." in Path(key).parts: raise ValueError("unsafe tree member")
        link(path, out / key)
    return store(out, name)

def receipt(kind: str, result: dict, inputs: dict[str, Path], *, outputs: dict[str, Path] | None = None) -> Path:
    record = {
        "schema": "coworld/caos-receipt@1", "kind": kind,
        "request": identity(ARGS), "inputs": {k: identity(p) for k, p in sorted(inputs.items())},
        "result": result,
    }
    members = {"receipt.json": json_value(record, kind)}
    members.update({"inputs/" + k: p for k, p in inputs.items()})
    members.update(outputs or {})
    return tree(members, kind)

def emit(path: Path):
    command("forward", str(path), "/cas/out")

def read_receipt(path: Path) -> dict:
    fetch(path)
    v = load(path / "receipt.json")
    if v.get("schema") != "coworld/caos-receipt@1": raise ValueError("unsupported receipt")
    return v

def worker(stage: str, refs: dict[str, Path] | None = None, literals: dict[str, str] | None = None, *, prepare: bool = False) -> str:
    module = ENTRYPOINTS[stage][0]
    modules = ARGS / "modules"
    if module != "factory":
        modules = tree({name: modules / name for name in ("cas.py", "contracts.py", module + ".py")}, "module-closure")
    argv = ["prepare-request" if prepare else "curry", "--base:@=" + str(ARGS / "base"),
            "--worker1:@=" + str(ARGS / "worker1"), "--modules:@=" + str(modules), "--stage=" + stage]
    argv += ["--" + k + ":@=" + str(v) for k, v in (refs or {}).items()]
    argv += ["--" + k + "=" + str(v) for k, v in (literals or {}).items()]
    return command(*argv)

def request_path(stage: str, refs=None, literals=None) -> Path:
    oid = worker(stage, refs, literals, prepare=True)
    path = Path("/cas") / ("factory-request-" + oid)
    if not path.exists(): command("get-hash", oid, str(path))
    return path

def run_then(stage: str, refs: dict[str, Path], callback: str, carry: dict[str, Path], literals=None, *, catch: bool = False):
    req = request_path(stage, refs, literals)
    cb = worker(callback, {**carry, "completed-request": req})
    command("run-request-then", str(req), "--then:hash=" + cb, *(["--catch"] if catch else []))

def fanout(requests: dict[str, Path], callback: str, carry: dict[str, Path], width: int):
    source = tree(requests, "requests")
    mapper = worker("dispatch")
    cb = worker(callback, carry)
    command("map-then", str(source), "--map:hash=" + mapper, "--then:hash=" + cb, "--max-parallel=" + str(width))

def collect_children() -> dict[str, Path]:
    p = argument("children")
    return {child.name: child for child in p.iterdir()}

def copy_value(source: Path, destination: Path):
    fetch(source, True)
    if source.is_dir(): shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

def commit(value: Path, message: str) -> Path:
    p = scratch("commit") / "commit"
    p.write_text("tree " + identity(value) + "\nauthor Coworld Factory <factory@coworld.local> 0 +0000\ncommitter Coworld Factory <factory@coworld.local> 0 +0000\n\n" + message + "\n")
    dest = Path("/cas/factory-commit")
    command("put-commit", str(p), str(dest))
    return dest
