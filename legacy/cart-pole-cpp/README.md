# Cart-pole backend (C++)

A cart-pole on the [Paperboat protocol](../../../protocol/README.md), built on the C++
[toolkit](../../../engine/toolkit/README.md). It shows how the pieces split:

| Piece | From |
| --- | --- |
| Catalog (palette, station objects) | [`descriptor.toml`](descriptor.toml) (imports `signal`, `math`, `control` and `dashboard`), via `load_descriptor_file` |
| Sine, gain, sum, PID, key, graph… | toolkit blocks: `catalog.find(type)->make(params)` |
| Cart-poles and their physics | this domain's station object, in [`domain/cart_pole.cpp`](domain/cart_pole.cpp): physics, drawing, linked block; registered with `define_object` |
| Starter station, starter graph | `[station]` and `[graph]` in `descriptor.toml` |
| Protocol, server, graph checking, run loop | `engine/core` (`paperboat::core`) |

It is the reference **simple backend** (GUIDELINES §6.1): `main.cpp` adds the domain's
own station object to the toolkit's registry, loads the descriptor and calls
`paperboat::main()`. The domain's code is one file, [`domain/cart_pole.cpp`](domain/cart_pole.cpp):
a `StationObject` (its state, `step`, `read` and the shapes it draws) registered with
`define_object`, so the descriptor uses it without importing anything. Everything the
example needs lives in this folder; the engine knows nothing of cart-poles.

**Station objects.** The Station page lists the cart-poles. Set their masses, pole
length, force limit and initial conditions (`x0`, `theta0`) there; add more with
**+ Cart-pole**. Each one spawns a linked **Cart-pole** block on the Flow page (force in;
x, v, theta, omega out): wire a controller to it. An unwired one just falls.

The starter graph balances the pole with two PID blocks. Its results match the earlier
Python, TypeScript and Ruby versions of this backend to the last printed digit.

## Build and run

A project of its own: its `CMakeLists.txt` pulls in the engine from
`PAPERBOAT_ENGINE_DIR` (default: this repo's `engine/`) and builds only the libraries it
links. Copy the folder anywhere and point `PAPERBOAT_ENGINE_DIR` at an engine.

```sh
npm run backend:cart-pole            # from the repo root: builds, then serves ws://localhost:8766
# or by hand, from this folder:
cmake -S . -B build                  # add -DPAPERBOAT_ENGINE_DIR=… when copied elsewhere
cmake --build build
build/paperboat-cart-pole --port 8766
python3 ../../../protocol/smoke_test.py --port 8766
```
