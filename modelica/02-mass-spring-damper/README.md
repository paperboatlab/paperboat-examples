# 02 Mass-spring-damper

A second-order system written as two first-order equations: a mass on a spring and a damper, released from rest, oscillates and decays. Plain Modelica, no library.

**Docs:** Articula's manual, <https://paperboatlab.org/apps/articula/>. Back to the [Modelica examples](../README.md).

## Open

```sh
paperboat app open articula modelica/02-mass-spring-damper
```

The folder is the workspace: open `MassSpringDamper` from **Files** and press **Simulate** (`Ctrl R`).

## Check

```sh
python3 golden.py modelica/02-mass-spring-damper   # from the repository root: omc simulate.mos, then compare with golden.json
```

It checks the position `x` and velocity `v` at the experiment's output times (`example.toml`, [golden tests](../../docs/golden.md)).
