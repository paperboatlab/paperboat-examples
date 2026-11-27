# Julix examples

Standalone [Paperboat Julix](https://github.com/paperboatlab/julix) folders, a set to learn Julix
from in order: scripts and cells, a notebook, JulixPlot figures, and a package from the General
registry (CasADi through CasADiNative.jl) in the folder's own environment. Back to the
[repository](../README.md).

**Docs:** <https://paperboatlab.org/apps/julix/>

| Folder | What it shows | Packages |
| --- | --- | --- |
| [01-numerics](01-numerics/) | a script in cells: linear algebra, a pendulum by Runge-Kutta | standard library |
| [02-notebook](02-notebook/) | a notebook: fit a step response, an SVG figure without a package | standard library |
| [03-julixplot](03-julixplot/) | 2D and 3D axes you pan, zoom and orbit; saving a figure | JulixPlot |
| [04-cart-pole-casadi](04-cart-pole-casadi/) | a cart-pole swing-up by direct collocation, with Ipopt | CasADiNative |

Each folder is a Julix folder (open it with `paperboat app open julix <folder>`) with its
`Project.toml` and `Manifest.toml` (versions pinned), `main.jl`, which writes its results to
`out/results.toml`, the golden file and an `example.toml` ([golden tests](../docs/golden.md)).

## Check

```sh
python3 golden.py julix/
```

Each check instantiates the folder's environment, then runs
`julia --project=. --startup-file=no main.jl` (Julix has no headless run yet).
