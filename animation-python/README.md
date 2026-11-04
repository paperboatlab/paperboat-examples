# Animation backend (Python): the Step flow example

A 3D actor (a box with a nose) animated by a **Step flow** on the
[Paperboat protocol](../../../protocol/README.md). Blocks with **step ports** (square,
dark) form a path; the run moves along it one block at a time, like a flowchart or
Scratch, and the Flow page lights up the block it is at.

- **Path blocks** (the toolkit's `step` package, run by the C++ engine): hats Start (once)
  and When (each time `cond` rises, e.g. Key (Space): a new path alongside the others),
  then Wait, If (leaves by `yes` while `cond` is positive), Repeat (leaves by `loop`
  `times` times, then `done`; wire the loop's end back into it).
- **The domain's steps:** Move (`dx`, `dy`, `dz` in the actor's own frame), Rotate
  (degrees about its own `x`, `y`, `z`), Scale (to a size), each over `seconds`. They are
  `paperboat.Timed` steps: each has an optional `curve` input (0 to 1) it follows within
  its time, and a `progress` output. Wire progress → a signal block (Ease, Sine, f(t)…) →
  curve to shape the motion; a steady 0.5 jumps halfway at once, holds, and ends at 1.
- **Signal blocks** work here too: Pose (probe) and the `base`, `signal`, `math` and
  `dashboard` packages (Key, Clock, Threshold, Graph…). They are sampled once per clock step and feed conditions and
  monitors.

The palette and the starter graph come from `descriptor.toml` (it imports `step` and
`base`).
## Layout

```
descriptor.toml   imports and the starter graph (with its groups)
expected.json     what the starter run must produce (npm run golden)
domain/
  state.py        the actor: position, orientation (quaternion), size
  blocks.py       Move, Rotate, Scale (steps), Pose (a probe) and Spin (a signal block)
server.py         fills a paperboat.Backend and serves it: no logic
```

Everything else (the protocol, graph checking, the runs, the toolkit blocks) is the C++
engine, through the Python bindings (`pip install ./python` from the repo root, or
`npm run build:python` while developing), so this folder runs on its own.


**Starter graph: a short story, with groups.**

1. Start → **Walk a square** (a visual group: Repeat ×4 of Move 2 m, Rotate 90°) →
   **Spin** (a *story group*, 2 s: Constant 45 → Spin, a signal block that turns the actor
   while it runs: 90° in all) → **Report** (a story group that runs once: Pose → the final
   heading and x on the Dashboard). A story is one step on the path: its blocks run only
   while the path is there, and what they computed stays for the next story.
2. **Pop on Space** (a visual group): When Key (Space) → pop bigger and back
   (Scale → Scale), any time you press it, alongside the story.
3. **End at 10 s** (a visual group, collapsed: ▸ opens it): Clock → Threshold 10 → When →
   Stop ends the run.

Select blocks and press **Group** or **Story** in the palette to make your own; ▾ collapses
a group into one block that shows only the wires crossing it.
