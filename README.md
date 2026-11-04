# Paperboat examples

Example backends for [Paperboat](https://github.com/cyythanapong-netizen/paperboat): each
folder is a project of its own that uses the Paperboat engine (C++) or its Python
bindings, and turns the same domain-free UI into a different app. They exist to prove the
framework: every one must pass the protocol smoke test and its own golden result.

| Folder | Port | What it shows |
| --- | --- | --- |
| `mass-spring-python/` | 8765 | Signal flow on a clock: a sine pushes a mass on a spring |
| `cart-pole-cpp/` | 8766 | C++, its own station object in code: PID balances Cart-poles |
| `parametric-python/` | 8767 | Evaluated once: a grid shaped by a wave and an attractor becomes boxes |
| `runner-python/` | 8768 | A game with an autopilot (or play it: Space, ↓); its Station is its own web page |
| `animation-python/` | 8769 | Step flow as a story: walk (eased), spin, report; groups |
| `parts-cpp/` | 8770 | Image processing with OpenCV: count bolts, nuts and washers in a photo |
| `chain-python/` | 8771 | A structure built on the Station as a graph, tested from the Flow in stories |
| `supply-python/` | 8772 | No physics: a supply network on the Station graph, an ordering policy on the Flow |

## Set up

Clone this repository next to Paperboat:

```
work/
  paperboat/            the framework (engine, Python bindings, UI, protocol)
  paperboat-examples/   this repository
```

```sh
cd paperboat && npm install && npm run build:python   # the UI, and the Python bindings
pip install websockets jsonschema                       # for the tests
```

## Run one

```sh
# Python (the bindings: PYTHONPATH=../paperboat/python, or pip install ../paperboat/python)
PYTHONPATH=../paperboat/python python3 mass-spring-python/server.py

# C++ (finds ../paperboat/engine; or -DPAPERBOAT_ENGINE_DIR=…; parts-cpp needs OpenCV)
cmake -S cart-pole-cpp -B cart-pole-cpp/build && cmake --build cart-pole-cpp/build
cart-pole-cpp/build/paperboat-cart-pole
```

Then, in `../paperboat`, `npm run dev` and open `http://localhost:5173/?backend=ws://localhost:<port>`.
Every backend also runs its starter headless with `--run` (protocol messages as JSON lines).

## Test

```sh
python3 ../paperboat/protocol/golden.py --examples .        # every starter run vs expected.json
python3 ../paperboat/protocol/smoke_test.py --port <port>   # a running backend vs the protocol
```

Writing your own backend: see Paperboat's API reference (`docs/api`, quickstart).

This repository is published from Paperboat's development tree (`examples/backends`).
