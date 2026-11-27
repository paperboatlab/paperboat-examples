# Golden tests

`golden.py` runs every example headless and compares its results with golden files checked in
beside it, within tolerances. An example is any folder with an `example.toml`; `legacy/` holds none.

```sh
python3 golden.py                       # every example
python3 golden.py julix/ hubs/furuta-lab  # a group, or some examples
python3 golden.py --update simplicial/09-modular-synth-cpp   # rewrite its golden files from a run
python3 golden.py --list                # what there is
python3 golden.py --strict simplicial/  # a skip fails too: CI, where the tools are installed
```

Each check prints `ok`, `FAIL`, `skip` (a tool in `requires` or a checkout is missing here) or
`pending` (the example says it is not ready); only `FAIL` fails the run. Python 3.11+, standard
library only.

## example.toml

```toml
kind = "simplicial"            # simplicial | julix | modelica | malachite | hub: its group
app = "simplicial"             # the app it opens in: simplicial | julix | articula | malachite
name = "09 Modular Synth"      # its display name ("Open example: <name>", pb#72)
description = "Vector wires [6]: a six-voice synth"   # one line, plain text
pending = "ex#44: not ported"  # optional: listed as pending, never run

[[check]]                      # one or more; a hub has one per app it uses
name = "starter"               # shown when there are several
dir = "."                      # optional: the folder the commands run in, from the example
requires = ["cmake"]           # optional: executables on PATH, else the check is skipped
build = [["cmake", "-S", ".", "-B", "build"]]  # optional: commands run first, in order
run = ["build/station", "--run"]               # the headless run; must exit 0
timeout = 600                  # optional, seconds, for each command
output = "simplicial"          # how to read the results (below)
file = "build/Model_res.csv"   # csv, json, toml: the file the run writes, from dir
vars = ["time", "x"]           # csv (required in practice), json, toml: which results; default all
golden = "golden.json"         # the golden file, from the example
atol = 1e-9                    # optional: a number matches within atol, or rtol of the larger (math.isclose)
rtol = 0.0
tol = { x = 1e-3 }             # optional: an atol per result
```

`kind`, `app`, `name` and `description` are required, also on a pending example: the platform's
example list reads them (pb#72), and `golden.py --list` prints them. A hub (`kind = "hub"`) opens in
Malachite.

Commands are argument lists, run without a shell. In any word, `{simplicial}`, `{julix}`,
`{articula}` or `{malachite}` is that app's checkout (`$SIMPLICIAL_DIR` and so on, else
`../<app>`; missing: the check is skipped), `{repo}` is this repository and `{dir}` the check's
folder, absolute (to mount it in a container).

| `output` | Results | Golden file |
| --- | --- | --- |
| `simplicial` | The protocol messages a station prints with `--run` (JSON lines ending in `run.finished`): the status, each signal's last number, the log lines | `expected.json`, the file `simplicial check` reads: `{"status", "signals": {node: value \| [value, tolerance]}, "logs": [a substring of a line]}`. `--update` rewrites the values and keeps each tolerance and the logs |
| `csv` | The named columns of a CSV with a header row (OpenModelica's `<Model>_res.csv`), each a list of numbers | JSON, one result per line |
| `json`, `toml` | The named entries of a JSON or TOML file the run writes (a Julix script's results, a hub's `results.toml`), or of what it prints when there is no `file` (a `--json` command) | JSON, one result per line |
| `exit` | Nothing: the check passes when every command exits 0 | none |

A golden file is never edited by hand: run `--update`, read the diff, commit it with the change
that moved it.

## Running each kind headless

- **simplicial:** a station's own `--run` (a C++ station built against `{simplicial}/engine`); a
  saved flow with `{simplicial}/bin/simplicial open <file.psf> --run`. Python and Julia stations run
  through the engine, `simplicial-engine host <dir> --run`, which leases a runtime from `paperboatd`.
- **julix:** Julix has no headless run yet, so a check runs the folder's script with Julia itself,
  `julia --project=. --startup-file=no main.jl` (`requires = ["julia"]`), in the folder's own
  environment (`Project.toml`, `Manifest.toml`), and the script writes its results (TOML is in
  Julia's standard library).
- **modelica:** Articula has no headless simulate yet, so a check runs a `.mos` with `omc`
  (`requires = ["omc"]`): `loadFile`, then `simulate(Model, …, outputFormat = "csv")`, and reads
  `<Model>_res.csv`. Where `omc` is only in a container, put a shim named `omc` on PATH, as CI does
  (`.github/workflows/golden.yml`):
  `exec podman run --rm -v "$PWD:$PWD:Z" -w "$PWD" --tmpfs /tmp -e HOME=/tmp docker.io/openmodelica/openmodelica:v1.27.1-minimal omc "$@"`.
  That image has no Modelica Standard Library: a model that uses it calls
  `installPackage(Modelica)` in its `.mos` first.
- **malachite:** Malachite has no headless check yet: its index (notes, `[[links]]`, backlinks) is
  built only in the server (`server/index.ts`), and `paperboat hub show` reads only hubs already on
  the machine's list. Until a command such as `malachite hub check <folder> --json` exists, a check
  runs `tools/malachite-index.ts`, which builds the index with Malachite's own code and prints each
  note's resolved links and the unresolved ones (`"unresolved": []` in the golden file is the
  check that every link resolves):
  `run = ["node", "{repo}/tools/malachite-index.ts", "{malachite}", "."]`, `requires = ["node"]`,
  `output = "json"`. That it renders has no headless check yet:
  `{malachite}/bin/malachite <folder> --port <n>` serves it, for a browser.
- **hub:** one check per app, each with its `dir` in the hub, plus the malachite check over the
  whole hub.
