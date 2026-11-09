# Paperboat examples

Example backends for [Paperboat](https://github.com/paperboatlab/paperboat): each folder is a
project of its own that uses the Paperboat engine (C++) or its Python bindings, and turns the
same domain-free UI into a different app. They exist to prove the framework: every one must
pass the protocol smoke test and its own golden result.

The repository is now a **ten-level tutorial curriculum**. Each level introduces a distinct
Paperboat capability, from a first clocked Signal flow to vector wires, custom web stations
and an acausal Modelica reference.

| Level | Folder | Port | Language | What it shows |
| --- | --- | --- | --- | --- |
| 01 | `01-smart-thermostat-python/` | 8765 | Python | Signal flow on a clock: bang-bang heating hysteresis, Board plots, Variables |
| 02 | `02-cart-pole-cpp/` | 8766 | C++ | Station object in code: PID balances a cart-pole; Variables formulas |
| 03 | `03-low-poly-island-python/` | 8767 | Python | Evaluated once: procedural terrain, list/array wires, block commenting |
| 04 | `04-cocktail-barista-python/` | 8768 | Python | Step flow: Excel menu, Board Choice, visual groups, subsystem, E-stop key |
| 05 | `05-rover-lander-python/` | 8769 | Python | Custom HTML5 web station: manual pilot vs autonomous lunar landing |
| 06 | `06-robot-pick-place-python/` | 8770 | Python | ABB-style palletizer: analytical IK, quintic trajectories, fork pick-and-place |
| 07 | `07-airfoil-cfd-python/` | 8771 | Python | Lattice-Boltzmann wind tunnel: velocity field, streamlines, lift/drag |
| 08 | `08-air-hockey-tracker-cpp/` | 8772 | C++ | Optional OpenCV toolkit: image wires, HSV→centroid pipeline, air-hockey tracking |
| 09 | `09-modular-synth-cpp/` | 8773 | C++ | Vector wires `[6]`: six-voice synth, per-voice filters, Scope and PCM Speaker |
| 10 | `10-train-pantograph-cpp/` | 8774 | C++/Modelica | Active contact-force regulator, compliant catenary, bypass and arcing |

The nine legacy backends are archived under [`legacy/`](legacy/) for reference; they are not
part of the curriculum, the CLI's example list or the golden run.

## Set up

Clone this repository next to Paperboat:

```
work/
  paperboat/            the framework (engine, Python bindings, UI, protocol)
  paperboat-examples/   this repository
```

```sh
cd paperboat && npm install && npm run build:python   # the UI, and the Python bindings
pip install websockets jsonschema                      # for the tests
```

## Run one

```sh
# Python (the bindings: PYTHONPATH=../paperboat/python, or pip install ../paperboat/python)
PYTHONPATH=../paperboat/python python3 04-cocktail-barista-python/server.py

# C++ (finds ../paperboat/engine; or -DPAPERBOAT_ENGINE_DIR=…)
cmake -S 09-modular-synth-cpp -B 09-modular-synth-cpp/build && cmake --build 09-modular-synth-cpp/build
09-modular-synth-cpp/build/paperboat-modular-synth

# Or let the CLI build and run it
./paperboat/bin/paperboat run 04
```

Then, in `../paperboat`, `npm run dev` and open
`http://localhost:5173/?backend=ws://localhost:<port>`. Every backend also runs its starter
headless with `--run` (protocol messages as JSON lines).

## Test

```sh
python3 ../paperboat/protocol/golden.py --examples .        # every starter run vs expected.json
python3 ../paperboat/protocol/smoke_test.py --port <port>   # a running backend vs the protocol
./paperboat/bin/paperboat check <folder>                    # manifest, catalog, smoke, golden
```

Writing your own backend: see Paperboat's API reference (`docs/api`, quickstart) and the
numbered README next to each backend.

This repository is published from Paperboat's development tree (`examples/backends`).
