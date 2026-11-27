# 02 Notebook

A script as a notebook: `##` cells that fit a step response, a type that draws itself as an SVG figure, a loop to interrupt and an error to follow back to its line. No packages. One of the [Julix examples](../README.md), for [Paperboat Julix](https://github.com/paperboatlab/julix).

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
