# Simplicial examples

The ten-level tutorial curriculum for [Paperboat Simplicial](https://github.com/paperboatlab/simplicial):
each folder is a station of its own (C++ on the engine, or Python), and each level introduces one
capability, from a first clocked Signal flow to vector wires, custom web stations and an acausal
Modelica reference. They are probes for the framework, not products. Back to the
[repository](../README.md).

| Level | Folder | Port | Language | What it shows |
| --- | --- | --- | --- | --- |
| 01 | `01-smart-thermostat-python/` | 51301 | Python | Signal flow on a clock: bang-bang heating hysteresis, Board plots, Variables |
| 02 | `02-cart-pole-cpp/` | 51302 | C++ | Station object in code: PID balances a cart-pole; Variables formulas |
| 03 | `03-low-poly-island-python/` | 51303 | Python | Evaluated once: procedural terrain, list/array wires, block commenting |
| 04 | `04-cocktail-barista-python/` | 51304 | Python | Step flow: Excel menu, Board Choice, visual groups, subsystem, E-stop key |
| 05 | `05-rover-lander-python/` | 51305 | Python | Custom HTML5 web station: manual pilot vs autonomous lunar landing |
| 06 | `06-robot-pick-place-python/` | 51306 | Python | ABB-style palletizer: analytical IK, quintic trajectories, fork pick-and-place |
| 07 | `07-airfoil-cfd-python/` | 51307 | Python | Lattice-Boltzmann wind tunnel: velocity field, streamlines, lift/drag |
| 08 | `08-air-hockey-tracker-cpp/` | 51308 | C++ | Optional OpenCV toolkit: image wires, HSV→centroid pipeline, air-hockey tracking |
| 09 | `09-modular-synth-cpp/` | 51309 | C++ | Vector wires `[6]`: six-voice synth, per-voice filters, Scope and PCM Speaker |
| 10 | `10-train-pantograph-cpp/` | 51310 | C++/Modelica | Active contact-force regulator, compliant catenary, bypass and arcing |

Ports follow the level number (`station.toml` is the source). Every level has a golden run the
harness checks (`example.toml`, `expected.json`). The design of the curriculum is in [`docs/`](docs/),
its station mockups in [`assets/`](assets/).

## Run one

```sh
paperboat run 09             # build if needed, start, open in Simplicial
```

From a checkout of [simplicial](https://github.com/paperboatlab/simplicial) next to this repository:

```sh
cmake -S 09-modular-synth-cpp -B 09-modular-synth-cpp/build && cmake --build 09-modular-synth-cpp/build
09-modular-synth-cpp/build/paperboat-modular-synth --run    # its starter, headless: protocol messages as JSON lines
```

A Python level's code runs out of process, in a Python runtime `paperboatd` leases; the engine
hosts it (`simplicial-engine` in a checkout's `engine/build/tools/`, or a release's `bin/`):

```sh
cd 01-smart-thermostat-python && simplicial-engine host . --run   # its starter, headless
```

02 needs Simplicial's optional control and optimization toolkits, 08 runs the OpenCV pipeline when
the opencv toolkit is installed (`paperboat toolkit install <name>`), and 07 needs numpy in its
package volume (`paperboat package add python numpy --project 07-airfoil-cfd-python`). Each
level's README walks through it; writing your own station is in Simplicial's docs.
