# 03 Tank loop

A package of your own, `Basics`: a connector, a record, a function, a block and the models built from them. In `Loop` a pump fills a tank until the tank's head stalls it; `Control` uses the block and the function. No library. Moved from Articula's `examples/authoring`.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat app open articula modelica/03-tank-loop
```

The folder is the workspace: open `Basics` › `Loop` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/03-tank-loop   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks the tank's level and inflow at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
