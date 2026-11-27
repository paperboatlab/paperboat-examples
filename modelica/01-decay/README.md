# 01 First-order decay

The smallest model: one state and one equation, `der(x) = -x/tau`. Plain Modelica, no library.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat app open articula modelica/01-decay
```

The folder is the workspace: open `Decay` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/01-decay   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks `x` against `exp(-t/tau)`, to 1e-4 at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
