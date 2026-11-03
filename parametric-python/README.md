# Parametric geometry backend (Python)

A third example backend for the [Paperboat protocol](../../../protocol/README.md), and the
first that is not a simulation. A run evaluates the graph once, Grasshopper style: a
Grid of points goes through a Wave and an Attractor, their sum sets box heights, and
the Boxes block writes the boxes into the 3D scene. Wires carry lists, not scalars.

The web app drives it with no change, the same as the simulation backends.

## Layout

```
descriptor.toml   the palette (imports, this domain's blocks) and the starter graph
domain/
  plant.py        the boxes the Boxes block builds, on a ground plate
  blocks.py       Grid, Wave, Attractor, Add, Scale, Boxes
server.py         fills a paperboat.Backend and serves it: no logic
```

Everything else (the protocol, graph checking, the runs, the toolkit blocks) is the C++
engine, through the Python bindings (`pip install ./python` from the repo root, or
`npm run build:python` while developing), so this folder runs on its own.

## Run

```sh
pip install websockets        # or: pip install -e .
python3 server.py             # ws://localhost:8767
```

## Smoke test

```sh
python3 ../../../protocol/smoke_test.py --port 8767
```

A run finishes in milliseconds, so the cancel check usually sees `done`, which the
smoke test accepts.
