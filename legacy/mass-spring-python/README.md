# Python example backend

A small reference backend that speaks the [Paperboat protocol](../../../protocol/README.md).
Use it to build and test the web app without the C++ engine. Its domain is one mass on
a spring, with a force source `F1` and a probe `P1` on the mass.

## Layout

```
descriptor.toml   the palette (imports, this domain's blocks) and the starter graph
domain/
  state.py        the mass on its spring (semi-implicit Euler)
  blocks.py       F1 (force source) and P1 (probe)
server.py         fills a paperboat.Backend and serves it: no logic
```

Everything else (the protocol, graph checking, the runs, the toolkit blocks) is the C++
engine, through the Python bindings (`pip install ./python` from the repo root, or
`npm run build:python` while developing), so this folder runs on its own.

## Run

```sh
pip install websockets        # or: pip install -e .
python3 server.py             # ws://localhost:8765
python3 server.py --port 8799
```

## Smoke test

Start a backend, then run:

```sh
python3 ../../../protocol/smoke_test.py --port 8765
```

It knows no domain: it checks the handshake, runs the starter graph the backend sends in
`graph.load` (signals for every monitor node, scene patches, progress up to 1),
checks that a graph with a cycle is rejected, and cancels a run.

The C++ engine must pass this same smoke test, so both backends stay in step with the protocol.
