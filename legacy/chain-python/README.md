# Chain backend (Python)

A structure and a test of it, on the [Paperboat protocol](../../../protocol/README.md): a
chain of masses, springs and dampers anchored to a wall.

- **The Station page builds the structure, as a graph** (`[station] view = "graph"`).
  Each element (Wall, Mass, Spring, Damper) is a station object; a spring or damper links
  two others through its `a` and `b` slots. Drag from an element's right handle onto a
  slot to link it; edit properties (mass, k, rest length, c) on the Station panel.
- **The Flow page holds the test logic, as stories in sequence:** Start → **Pull test**
  (a story group that runs 6 s: pull mass-2 with 5 N from t = 0.5 s, plot where it goes
  and spring-1's tension) → **Check** (a story that runs once: is spring-1 over its
  4.5 N limit? Threshold → Display). A story's results stay on its outputs for the next
  one; collapse a story (▾) to see it as one step.

The structure settles where it should: two 20 N/m springs in series under 5 N put mass-2
at 2.5 m and spring-1 at 5 N.

## Layout

```
descriptor.toml   imports for the test logic, the starter station (a graph) and test
domain/
  objects.py      Wall, Mass, Spring, Damper: station objects, linked to each other
server.py         fills a paperboat.Backend and serves it: no logic
expected.json     what the starter run must produce (npm run golden)
```

Everything else (the protocol, the station and graph checks, the runs) is the C++ engine,
through the Python bindings.
