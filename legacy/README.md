# Archived examples

The nine backends below predate the numbered tutorial curriculum. They remain here as
reference material, but they are **not** part of the CLI's example list and the golden test
does not run them.

| Folder | What it showed |
| --- | --- |
| `mass-spring-python/` | Signal flow on a clock: a sine pushes a mass on a spring |
| `cart-pole-cpp/` | C++, its own station object in code: PID balances a cart-pole |
| `parametric-python/` | Evaluated once: a grid shaped by a wave and an attractor becomes boxes |
| `runner-python/` | A game with an autopilot (or play it: Space, ↓); its Station is its own web page |
| `animation-python/` | Step flow as a story: walk, spin, report; groups |
| `parts-cpp/` | Image processing with OpenCV: count bolts, nuts and washers in a photo |
| `chain-python/` | A structure built on the Station as a graph, tested from the Flow in stories |
| `supply-python/` | No physics: a supply network on the Station graph, an ordering policy on the Flow |
| `double-pendulum-cpp/` | Payload identification, swing-up and LQR balance with vector ports |

Use the numbered tutorials in the repository root instead; each has an updated README,
`backend.toml`, descriptor and golden result. To run an archived backend explicitly, pass its
path: `./bin/paperboat run paperboat-examples/legacy/parts-cpp`.
