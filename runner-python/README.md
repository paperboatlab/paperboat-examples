# Runner backend (Python)

A 2D side-scroller on the [Paperboat protocol](../../../protocol/README.md): a runner
jumps over crates and ducks under the occasional bar that slides toward it. The runner and obstacles
live in the backend (setup); the flow decides when to jump or duck (control).

- **Starter graph: autopilot.** Next crate `dx` → Gain (−1) → Threshold (−1.6) → Jump,
  so it jumps when a crate is closer than 1.6 m. The same chain from Next bar → Duck
  ducks, and holds while under the bar (`dx` is negative there).
- **Play it yourself:** delete the wires into Jump and Duck, wire the Space Key → Jump and
  the ArrowDown Key → Duck, press Run, then use Space and Arrow Down. Click a Key block's
  `key` field and press any key to change it. The UI forwards key presses
  as `input` messages.

You can't jump while ducking. Keep running for 20 s to win.

- **Its Station is a web page** (`[station] view = "web"` in the descriptor): the engine
  serves `station/` on the backend's port, and the Station page shows it in place of the
  built-in scene. The page draws the same entities the engine sends (`runner`,
  `obstacle-N`) in its own paper-cut look; it decides nothing. Keys pressed on it still
  reach the Key blocks.

## Layout

```
descriptor.toml   imports, customised templates, the web station and the starter graph
station/          the web station: index.html, runner.js, style.css
expected.json     what the starter run must produce (npm run golden)
domain/
  plant.py        the game: runner, crates and bars
  blocks.py       Runner, Next crate, Next bar (probes); Jump, Duck (sources)
server.py         fills a paperboat.Backend and serves it: no logic
```

Everything else (the protocol, graph checking, the runs, the toolkit blocks) is the C++
engine, through the Python bindings (`pip install ./python` from the repo root, or
`npm run build:python` while developing), so this folder runs on its own.

```sh
pip install websockets
python3 server.py                                   # ws://localhost:8768
python3 ../../../protocol/smoke_test.py --port 8768
```
