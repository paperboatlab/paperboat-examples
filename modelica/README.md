# Modelica examples

Standalone Modelica models, opened in [Paperboat Articula](https://github.com/paperboatlab/articula)
and simulated by OpenModelica (`omc`), each with its results checked against a golden file. The
set is ex#46. Back to the [repository](../README.md).

| Example | What it shows | Library |
| --- | --- | --- |
| [01-decay](01-decay/) | One state, one equation | none |
| [02-mass-spring-damper](02-mass-spring-damper/) | Second order as two equations | none |
| [03-tank-loop](03-tank-loop/) | A package of your own: connector, record, function, block | none |
| [04-dc-motor](04-dc-motor/) | Electrical and rotational parts in one model | MSL 4.1.0 |
| [05-double-pendulum](05-double-pendulum/) | MultiBody, drawn in 3D | MSL 4.1.0 |
| [06-speed-control](06-speed-control/) | A limited PI controller in a feedback loop | MSL 4.1.0 |

Each folder is an Articula workspace: the model (`.mo`), a `simulate.mos` that writes
`build/<Model>_res.csv` (Articula has no headless simulate yet, articula#45), the golden file and an
`example.toml` ([golden tests](../docs/golden.md)).

```sh
python3 golden.py modelica/   # needs omc on PATH (or the container shim in docs/golden.md)
```
