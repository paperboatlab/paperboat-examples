#!/usr/bin/env python3
"""The golden harness: run every example headless and compare its results with the golden files
checked in beside it, within tolerances. Each example is a folder with an `example.toml`.

    python3 golden.py                      # every example (legacy/ is not one)
    python3 golden.py simplicial/09-…      # some of them: folders, or a group such as julix/
    python3 golden.py --update […]         # run and rewrite the golden files from the results
    python3 golden.py --list               # what there is
    python3 golden.py --strict […]         # a check that would be skipped fails (CI, tools installed)

Exit 0 when nothing failed; a pending example and a check whose tools are missing are reported,
not failed. Standard library only (Python 3.11+). The manifest: docs/golden.md.
"""

import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent
# Checkouts a command may name: {simplicial} is the Simplicial app (its engine), from
# $SIMPLICIAL_DIR, else a checkout next to this repository.
PLACES = {
    "repo": str(REPO),
    "simplicial": os.environ.get("SIMPLICIAL_DIR") or str(REPO.parent / "simplicial"),
}


class Skip(Exception):
    """A check that cannot run on this machine: a tool or checkout is missing."""


def fill(words: list[str], cwd: Path) -> list[str]:
    """{repo}, {simplicial} and {dir} (the check's folder, absolute: for a container's mount)."""
    out = [w.format_map(PLACES | {"dir": str(cwd)}) for w in words]
    for name, path in PLACES.items():
        if any(f"{{{name}}}" in w for w in words) and not Path(path).is_dir():
            raise Skip(f"no {name} checkout at {path} (set ${name.upper()}_DIR)")
    return out


def run(cmd: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip()[-600:]
        raise RuntimeError(f"{' '.join(cmd)} exited {proc.returncode}\n{tail}")
    return proc


# ── Reading results ──────────────────────────────────────────────────────────────────────────

def read_simplicial(stdout: str) -> dict:
    """A station's `--run`: protocol messages as JSON lines, ending with run.finished."""
    msgs = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
    if not msgs or msgs[-1].get("type") != "run.finished":
        raise RuntimeError("no run.finished in the output")
    signals = {m["node"]: m["v"] for m in msgs
               if m.get("type") == "signal" and isinstance(m.get("v"), (int, float))}
    logs = [m["text"] for m in msgs if m.get("type") == "log"]
    return {"status": msgs[-1].get("status"), "signals": signals, "logs": logs}


def read_table(path: Path, names: list[str]) -> dict:
    """A CSV with a header row (OpenModelica's _res.csv, a Julix saved table): named columns."""
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"{path.name} has no rows")
    names = names or list(rows[0])
    missing = [n for n in names if n not in rows[0]]
    if missing:
        raise RuntimeError(f"{path.name} has no column {', '.join(missing)}")
    return {n: [float(r[n]) for r in rows] for n in names}


def read_data(path: Path, names: list[str]) -> dict:
    """A JSON or TOML file of named results (a Julix script's saved results, a hub's results.toml)."""
    data = tomllib.loads(path.read_text()) if path.suffix == ".toml" else json.loads(path.read_text())
    return {n: data[n] for n in names} if names else data


# ── Comparing ────────────────────────────────────────────────────────────────────────────────

def close(got, want, atol: float, rtol: float) -> bool:
    if isinstance(want, list):
        return isinstance(got, list) and len(got) == len(want) and all(
            close(g, w, atol, rtol) for g, w in zip(got, want))
    if isinstance(want, (int, float)) and not isinstance(want, bool):
        return isinstance(got, (int, float)) and math.isclose(got, want, rel_tol=rtol, abs_tol=atol)
    return got == want


def compare(got: dict, want: dict, check: dict) -> list[str]:
    atol, rtol, tol = check.get("atol", 1e-9), check.get("rtol", 0.0), check.get("tol", {})
    problems = []
    for name, value in want.items():
        if name not in got:
            problems.append(f"no result {name}")
        elif not close(g := got[name], value, t := tol.get(name, atol), rtol):
            if isinstance(value, list) and isinstance(g, list) and len(g) == len(value):
                i = next(i for i, (a, b) in enumerate(zip(g, value)) if not close(a, b, t, rtol))
                name, g, value = f"{name}[{i}]", g[i], value[i]
            elif isinstance(value, list):
                g, value = f"{len(g) if isinstance(g, list) else 1} values", f"{len(value)}"
            problems.append(f"{name} = {g}, expected {value}")
    return problems


def compare_simplicial(got: dict, want: dict) -> list[str]:
    """expected.json, the format Simplicial's own `check` reads (simplicial/protocol/golden.py):
    {"status", "signals": {node: value | [value, tolerance]}, "logs": [a substring of a log line]}."""
    problems = []
    if got["status"] != want.get("status", "done"):
        problems.append(f"status {got['status']}, expected {want.get('status', 'done')}")
    for node, w in want.get("signals", {}).items():
        value, tol = (w[0], w[1]) if isinstance(w, list) else (w, 1e-9)
        if node not in got["signals"]:
            problems.append(f"no signal from {node}")
        elif abs(got["signals"][node] - value) > tol:
            problems.append(f"{node} = {got['signals'][node]:.6g}, expected {value:.6g} ± {tol:g}")
    for text in want.get("logs", []):
        if not any(text in line for line in got["logs"]):
            problems.append(f"no log line contains {text!r}")
    return problems


def update_simplicial(got: dict, want: dict) -> dict:
    """The new values, each signal keeping its tolerance; status and log lines stay as written."""
    for node, w in want.get("signals", {}).items():
        if node in got["signals"]:
            v = round(got["signals"][node], 6)
            want["signals"][node] = [v, w[1]] if isinstance(w, list) else v
    return want


def dump(value, indent: str = "") -> str:
    """JSON with one result per line (a list stays on its line), so a diff shows which one moved."""
    if not isinstance(value, dict) or not value:
        return json.dumps(value, ensure_ascii=False)
    inner = indent + "  "
    return "{\n" + ",\n".join(f"{inner}{json.dumps(k)}: {dump(v, inner)}" for k, v in value.items()) + f"\n{indent}}}"


# ── One check ────────────────────────────────────────────────────────────────────────────────

def run_check(example: Path, check: dict, update: bool) -> list[str]:
    for tool in check.get("requires", []):
        if not shutil.which(tool):
            raise Skip(f"needs {tool}")
    cwd = example / check.get("dir", ".")
    timeout = check.get("timeout", 600)
    for step in check.get("build", []):
        run(fill(step, cwd), cwd, timeout)
    proc = run(fill(check["run"], cwd), cwd, timeout)

    kind = check["output"]
    names = check.get("vars", [])
    if kind == "exit":
        return []
    if kind == "simplicial":
        got = read_simplicial(proc.stdout)
    elif kind == "csv":
        got = read_table(cwd / check["file"], names)
    elif kind in ("json", "toml"):
        got = read_data(cwd / check["file"], names)
    else:
        raise RuntimeError(f"unknown output {kind!r} (simplicial, csv, json, toml, exit)")

    golden = example / check["golden"]
    if update:
        if kind == "simplicial":
            got = update_simplicial(got, json.loads(golden.read_text()))
        golden.write_text(dump(got) + "\n")
        return []
    if not golden.exists():
        return [f"no golden file {check['golden']} (run with --update)"]
    want = json.loads(golden.read_text())
    return compare_simplicial(got, want) if kind == "simplicial" else compare(got, want, check)


# ── Examples ─────────────────────────────────────────────────────────────────────────────────

def find(args: list[str]) -> list[Path]:
    roots = [Path(a).resolve() for a in args] or [REPO]
    found = []
    for root in roots:
        if (root / "example.toml").exists():
            found.append(root)
        elif root.is_dir():
            found += [p.parent for p in root.rglob("example.toml")
                      if not {"legacy", "build", "node_modules"} & set(p.relative_to(root).parts)]
        else:
            sys.exit(f"not an example or a folder of them: {root}")
    return sorted(set(found))


def main() -> int:
    args = sys.argv[1:]
    update, listing, strict = "--update" in args, "--list" in args, "--strict" in args
    args = [a for a in args if a not in ("--update", "--list", "--strict")]
    counts = {"ok": 0, "FAIL": 0, "skip": 0, "pending": 0}
    for example in find(args):
        name = example.relative_to(REPO).as_posix() if example.is_relative_to(REPO) else str(example)
        manifest = tomllib.loads((example / "example.toml").read_text())
        if "pending" in manifest:
            counts["pending"] += 1
            print(f"pending {name}: {manifest['pending']}", flush=True)
            continue
        if not manifest.get("check"):
            counts["FAIL"] += 1
            print(f"FAIL    {name}\n        no [[check]] and not pending", flush=True)
        for check in manifest.get("check", []):
            label = f"{name} {check['name']}" if len(manifest["check"]) > 1 else name
            if listing:
                print(f"{manifest['kind']:10} {label}")
                continue
            try:
                problems = run_check(example, check, update)
                status = "FAIL" if problems else "ok"
            except Skip as e:
                status, problems = "skip", [str(e)]
            except (RuntimeError, subprocess.TimeoutExpired, OSError, KeyError, ValueError) as e:
                status, problems = "FAIL", [f"{type(e).__name__}: {e}" if not isinstance(e, RuntimeError) else str(e)]
            if strict and status == "skip":
                status = "FAIL"
            counts[status] += 1
            note = " (golden updated)" if update and status == "ok" else ""
            print(f"{status:7} {label}{note}" + "".join(f"\n        {p}" for p in problems), flush=True)
    if not listing:
        print(", ".join(f"{n} {k}" for k, n in counts.items() if n) or "no examples")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
