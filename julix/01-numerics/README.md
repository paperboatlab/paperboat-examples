# 01 Numerics

A first Julix script with Julia's standard library only: a linear system, eigenvalues, and a damped pendulum integrated with Runge-Kutta, in cells you run one at a time. One of the [Julix examples](../README.md), for [Paperboat Julix](https://github.com/paperboatlab/julix).

**Docs:** <https://paperboatlab.org/apps/julix/>

## Run

```sh
paperboat app open julix .
```

Open `main.jl` and run it (F5), or a cell at a time (Ctrl Enter). Without Julix:
`julia --project=. -e 'import Pkg; Pkg.instantiate()'`, then `julia --project=. main.jl`.

## Check

```sh
python3 ../../golden.py .
```

The script writes `out/results.toml`; the check compares it with `golden.json` ([golden tests](../../docs/golden.md)).
