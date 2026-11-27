# 04 Cart-Pole Swing-Up

Optimal control with a package from Julia's General registry: a cart-pole swing-up by direct collocation, solved with Ipopt through [CasADiNative.jl](https://github.com/casadi/CasADiNative.jl), installed in this folder's own environment. The first instantiate downloads CasADi's binaries (a few minutes). One of the [Julix examples](../README.md), for [Paperboat Julix](https://github.com/paperboatlab/julix).

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
